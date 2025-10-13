"""LLM integration using LiteLLM"""

import json
import os
from typing import Any, Callable, Literal, Optional

import litellm
from pydantic import BaseModel, Field


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

    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0

    # OAuth2 authentication options
    auth_type: Literal["api_key", "oauth2"] = Field(
        default="api_key",
        description="Authentication type: 'api_key' or 'oauth2'"
    )
    oauth_provider: Optional[str] = Field(
        default=None,
        description="OAuth2 provider (e.g., 'google') when auth_type='oauth2'"
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
) -> str:
    """
    Call LLM with given prompt, handling tool calls if present.

    Supports both API key and OAuth2 authentication based on config.

    Args:
        prompt: The prompt to send
        config: LLM configuration (includes auth settings)
        tool_functions: Optional list of tool functions (Python callables)
        **kwargs: Additional LiteLLM parameters (including 'tools' schema)

    Returns:
        LLM response text

    Raises:
        ValueError: If OAuth2 configuration is invalid
        NotAuthenticatedError: If OAuth2 required but not logged in
    """
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

        # No tool calls, return content
        content = message.content
        return content if content else ""

    # Max iterations reached
    return "Error: Maximum tool call iterations reached"
