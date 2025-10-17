"""OpenAI SDK direct backend for gpt-* models

This module provides direct OpenAI API integration for better compatibility
with latest OpenAI models (gpt-5, gpt-4o, o1, etc.) without relying on LiteLLM.

Benefits:
- Immediate access to latest OpenAI features
- Better parameter compatibility (no drop_params needed)
- More control over OpenAI-specific optimizations
- Reduced dependency on LiteLLM updates
"""

import json
import time
from typing import Any, Callable, Optional

from .llm import LLMConfig, LLMResponse


async def call_openai_direct(
    prompt: str,
    config: LLMConfig,
    tool_functions: Optional[list[Callable]] = None,
    **kwargs: Any,
) -> LLMResponse:
    """Call OpenAI API directly using official SDK

    Args:
        prompt: The prompt to send
        config: LLM configuration
        tool_functions: Optional list of tool functions (Python callables)
        **kwargs: Additional OpenAI parameters (including 'tools' schema)

    Returns:
        LLMResponse with content, usage, model, and duration

    Raises:
        ImportError: If openai package not installed
        ValueError: If API key not set
        openai.OpenAIError: If API request fails

    Note:
        This function handles tool calling automatically with multi-turn
        conversation loop (max 5 iterations).
    """
    # Import OpenAI SDK
    try:
        from openai import AsyncOpenAI
    except ImportError as e:
        raise ImportError(
            "openai package is required for direct OpenAI SDK backend. "
            "Install with: pip install openai"
        ) from e

    # Track timing
    start_time = time.time()

    # Track total usage across all LLM calls (for tool iterations)
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # Initialize OpenAI client
    # Uses OPENAI_API_KEY environment variable by default
    api_key = config.get_api_key()
    client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    # Build messages list
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

    # Create tool name -> function mapping from Python callables
    tool_map: dict[str, Callable] = {}
    if tool_functions:
        tool_map = {tool.__name__: tool for tool in tool_functions}

    # Maximum iterations to prevent infinite loops
    max_iterations = 5
    iterations = 0

    while iterations < max_iterations:
        iterations += 1

        # Build OpenAI API call parameters
        api_params: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
        }

        # Add optional parameters
        if config.max_tokens:
            api_params["max_tokens"] = config.max_tokens

        # Add top_p if not default (OpenAI default is 1.0)
        if config.top_p != 1.0:
            api_params["top_p"] = config.top_p

        # Add tools schema if provided in kwargs
        if "tools" in kwargs:
            api_params["tools"] = kwargs["tools"]

        # Add any other OpenAI-specific parameters from kwargs
        openai_params = [
            "response_format",
            "seed",
            "stop",
            "presence_penalty",
            "frequency_penalty",
        ]
        for key in openai_params:
            if key in kwargs:
                api_params[key] = kwargs[key]

        # Call OpenAI API
        response = await client.chat.completions.create(**api_params)

        # Track usage
        if response.usage:
            total_usage["prompt_tokens"] += response.usage.prompt_tokens or 0
            total_usage["completion_tokens"] += response.usage.completion_tokens or 0
            total_usage["total_tokens"] += response.usage.total_tokens or 0

        message = response.choices[0].message

        # Check if LLM wants to call tools
        tool_calls = message.tool_calls

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


__all__ = ["call_openai_direct"]
