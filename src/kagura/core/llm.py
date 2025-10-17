"""LLM integration using LiteLLM"""

import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional

import litellm
from pydantic import BaseModel, Field

from .cache import LLMCache


@dataclass
class LLMResponse:
    """LLM response with metadata

    Attributes:
        content: Response text
        usage: Token usage dict (prompt_tokens, completion_tokens, total_tokens)
        model: Model name
        duration: Response time in seconds
    """

    content: str
    usage: dict[str, int]
    model: str
    duration: float

    def __str__(self) -> str:
        """Return content as string for backward compatibility"""
        return self.content

    def __eq__(self, other: object) -> bool:
        """Support comparison with strings for backward compatibility"""
        if isinstance(other, str):
            return self.content == other
        return super().__eq__(other)


# Global cache instance
_llm_cache = LLMCache(backend="memory", default_ttl=3600)


class LLMConfig(BaseModel):
    """LLM configuration

    Supports both API key and OAuth2 authentication for Google models.

    Example with API key:
        >>> config = LLMConfig(model="gemini/gemini-1.5-flash")
        >>> # Uses GOOGLE_API_KEY environment variable

    Example with OAuth2:
        >>> config = LLMConfig(
        ...     model="gemini/gemini-1.5-flash",
        ...     auth_type="oauth2",
        ...     oauth_provider="google"
        ... )
        >>> # Uses OAuth2Manager to get token automatically
    """

    model: str = "gpt-5-mini"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0

    # OAuth2 authentication options
    auth_type: Literal["api_key", "oauth2"] = Field(
        default="api_key", description="Authentication type: 'api_key' or 'oauth2'"
    )
    oauth_provider: Optional[str] = Field(
        default=None,
        description="OAuth2 provider (e.g., 'google') when auth_type='oauth2'",
    )

    # Cache configuration
    enable_cache: bool = Field(
        default=True,
        description="Enable LLM response caching for faster responses and lower costs",
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache time-to-live in seconds (default: 3600 = 1 hour)",
    )
    cache_backend: Literal["memory", "redis"] = Field(
        default="memory", description="Cache backend: 'memory' (default) or 'redis'"
    )

    def get_api_key(self) -> Optional[str]:
        """Get API key or OAuth2 token based on auth_type

        Returns:
            API key or OAuth2 access token

        Raises:
            ValueError: If OAuth2 is requested but auth module not installed
            NotAuthenticatedError: If OAuth2 auth required but not logged in
        """
        if self.auth_type == "api_key":
            # Use environment variable (standard LiteLLM behavior)
            return None  # LiteLLM will use env vars

        # OAuth2 authentication
        if self.auth_type == "oauth2":
            if self.oauth_provider is None:
                raise ValueError(
                    "oauth_provider must be specified when auth_type='oauth2'"
                )

            try:
                from kagura.auth import OAuth2Manager
            except ImportError as e:
                raise ValueError(
                    "OAuth2 authentication requires the 'oauth' extra. "
                    "Install with: pip install kagura-ai[oauth]"
                ) from e

            # Get token from OAuth2Manager
            auth = OAuth2Manager(provider=self.oauth_provider)
            return auth.get_token()

        return None


async def call_llm(
    prompt: str,
    config: LLMConfig,
    tool_functions: Optional[list[Callable]] = None,
    **kwargs: Any,
) -> str | LLMResponse:
    """
    Call LLM with given prompt, handling tool calls if present.

    Supports both API key and OAuth2 authentication based on config.
    Automatically caches responses for faster access and cost reduction.

    Args:
        prompt: The prompt to send
        config: LLM configuration (includes auth and cache settings)
        tool_functions: Optional list of tool functions (Python callables)
        **kwargs: Additional LiteLLM parameters (including 'tools' schema)

    Returns:
        LLM response text

    Raises:
        ValueError: If OAuth2 configuration is invalid
        NotAuthenticatedError: If OAuth2 required but not logged in

    Note:
        - Caching is only used when tool_functions is None (no tool calls)
        - Cache key includes prompt, model, and all kwargs for uniqueness
        - Use config.enable_cache=False to disable caching
    """
    # Check cache first (only if no tools and cache enabled)
    if config.enable_cache and not tool_functions:
        cache_key = _llm_cache._hash_key(
            prompt,
            config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            **kwargs,
        )
        cached_response = await _llm_cache.get(cache_key)
        if cached_response is not None:
            return cached_response

    # Track timing
    start_time = time.time()

    # Track total usage across all LLM calls (for tool iterations)
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # Build messages list
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

    # Create tool name -> function mapping from Python callables
    tool_map: dict[str, Callable] = {}
    if tool_functions:
        tool_map = {tool.__name__: tool for tool in tool_functions}

    # Maximum iterations to prevent infinite loops
    max_iterations = 5
    iterations = 0

    # Get API key/token based on auth_type
    api_key = config.get_api_key()

    while iterations < max_iterations:
        iterations += 1

        # Filter out parameters already set in config to avoid duplication
        filtered_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ("model", "temperature", "max_tokens", "top_p", "api_key")
        }

        # Add API key if OAuth2 authentication is used
        if api_key:
            filtered_kwargs["api_key"] = api_key

        # Call LLM (filtered kwargs may contain 'tools' for OpenAI schema)
        response = await litellm.acompletion(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            **filtered_kwargs,
        )

        # Track usage (safely handle different response types)
        usage = getattr(response, "usage", None)
        if usage:
            total_usage["prompt_tokens"] += getattr(usage, "prompt_tokens", 0)
            total_usage["completion_tokens"] += getattr(usage, "completion_tokens", 0)
            total_usage["total_tokens"] += getattr(usage, "total_tokens", 0)

        message = response.choices[0].message  # type: ignore

        # Check if LLM wants to call tools
        tool_calls = getattr(message, "tool_calls", None)

        if tool_calls:
            # Add assistant message with tool calls to conversation
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args_str = tool_call.function.arguments

                # Parse arguments
                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}

                # Execute tool
                if tool_name in tool_map:
                    tool_func = tool_map[tool_name]
                    try:
                        # Call tool (handle both sync and async)
                        import inspect

                        if inspect.iscoroutinefunction(tool_func):
                            tool_result = await tool_func(**tool_args)
                        else:
                            tool_result = tool_func(**tool_args)

                        result_content = str(tool_result)
                    except Exception as e:
                        result_content = f"Error executing {tool_name}: {str(e)}"
                else:
                    result_content = f"Tool {tool_name} not found"

                # Add tool result to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": result_content,
                    }
                )

            # Continue loop to get final response
            continue

        # No tool calls, return content with metadata
        content = message.content or ""
        duration = time.time() - start_time

        # Cache the response (only if no tools were used)
        if config.enable_cache and not tool_functions:
            await _llm_cache.set(
                cache_key, content, ttl=config.cache_ttl, model=config.model
            )

        # Return LLMResponse with metadata
        return LLMResponse(
            content=content, usage=total_usage, model=config.model, duration=duration
        )

    # Max iterations reached
    duration = time.time() - start_time
    return LLMResponse(
        content="Error: Maximum tool call iterations reached",
        usage=total_usage,
        model=config.model,
        duration=duration,
    )


def get_llm_cache() -> LLMCache:
    """Get global LLM cache instance for inspection or invalidation

    Returns:
        Global LLMCache instance

    Example:
        >>> cache = get_llm_cache()
        >>> stats = cache.stats()
        >>> print(f"Hit rate: {stats['hit_rate']:.1%}")
        Hit rate: 85.3%

        >>> # Invalidate cache for specific model
        >>> await cache.invalidate("gpt-4o")
    """
    return _llm_cache


def set_llm_cache(cache: LLMCache) -> None:
    """Set custom LLM cache instance

    Args:
        cache: Custom LLMCache instance (e.g., with Redis backend)

    Example:
        >>> from kagura.core.cache import LLMCache
        >>> custom_cache = LLMCache(max_size=5000, default_ttl=7200)
        >>> set_llm_cache(custom_cache)
    """
    global _llm_cache
    _llm_cache = cache


__all__ = ["LLMConfig", "LLMResponse", "call_llm", "get_llm_cache", "set_llm_cache"]
