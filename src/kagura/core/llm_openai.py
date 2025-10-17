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
        }

        # gpt-5 series only supports temperature=1.0 (default)
        # o1 series also has temperature restrictions
        is_gpt5 = config.model.startswith("gpt-5")
        is_o1 = config.model.startswith("o1-")

        if not (is_gpt5 or is_o1):
            # Only add temperature for models that support it
            api_params["temperature"] = config.temperature

        # Add optional parameters
        if config.max_tokens:
            api_params["max_tokens"] = config.max_tokens

        # Add top_p if not default (OpenAI default is 1.0)
        # Skip for gpt-5 and o1 series
        if config.top_p != 1.0 and not (is_gpt5 or is_o1):
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


async def call_openai_vision_url(
    image_url: str,
    prompt: str,
    config: LLMConfig,
) -> LLMResponse:
    """Analyze image from URL using OpenAI Vision API

    Directly passes URL to OpenAI (no download needed).

    Args:
        image_url: Direct image URL (jpg, png, gif, webp)
        prompt: Analysis prompt
        config: LLM config (should use gpt-4o, gpt-5, or vision-capable model)

    Returns:
        LLMResponse with image analysis

    Raises:
        ImportError: If openai package not installed
        ValueError: If API key not set
        openai.OpenAIError: If API request fails

    Note:
        OpenAI Vision API supports direct URLs (no download needed).
        Supported formats: JPEG, PNG, GIF, WebP
    """
    # Import OpenAI SDK
    try:
        from openai import AsyncOpenAI
    except ImportError as e:
        raise ImportError(
            "openai package is required for Vision API. "
            "Install with: pip install openai"
        ) from e

    # Track timing
    import time

    start_time = time.time()

    # Initialize OpenAI client
    api_key = config.get_api_key()
    client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    # Build Vision API request
    # Note: gpt-5 doesn't support temperature, use default
    api_params: dict[str, Any] = {
        "model": config.model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "high",  # high/low/auto
                        },
                    },
                ],
            }
        ],
    }

    # Add max_tokens if specified
    if config.max_tokens:
        api_params["max_tokens"] = config.max_tokens
    else:
        # Default higher limit for vision tasks
        api_params["max_tokens"] = 4096

    # Add temperature for non-gpt-5 models
    is_gpt5 = config.model.startswith("gpt-5")
    is_o1 = config.model.startswith("o1-")
    if not (is_gpt5 or is_o1):
        api_params["temperature"] = config.temperature

    # Call OpenAI Vision API
    response = await client.chat.completions.create(**api_params)

    # Extract result
    content = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens or 0,
        "completion_tokens": response.usage.completion_tokens or 0,
        "total_tokens": response.usage.total_tokens or 0,
    }

    duration = time.time() - start_time

    return LLMResponse(
        content=content, usage=usage, model=config.model, duration=duration
    )


__all__ = ["call_openai_direct", "call_openai_vision_url"]
