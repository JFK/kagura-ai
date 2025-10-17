"""Streaming support for LLM responses

This module provides streaming LLM responses for improved user experience:
- First token arrives in <500ms (vs 2-5s for full response)
- Real-time progress feedback
- Better perceived latency

Example:
    >>> from kagura.core.streaming import call_llm_stream
    >>> from kagura import LLMConfig
    >>>
    >>> config = LLMConfig(model="gpt-5-mini")
    >>> async for chunk in call_llm_stream("Write a story", config):
    ...     print(chunk, end="", flush=True)
    Once upon a time...

Note:
    Streaming responses are NOT cached (non-deterministic, real-time).
"""

from typing import Any, AsyncIterator

import litellm

from .llm import LLMConfig


async def call_llm_stream(
    prompt: str, config: LLMConfig, **kwargs: Any
) -> AsyncIterator[str]:
    """Stream LLM response token by token

    Streams LLM responses in real-time, yielding tokens as they arrive.
    This provides better UX for long-running generations by showing
    progress immediately.

    Args:
        prompt: The prompt to send to the LLM
        config: LLM configuration (model, temperature, auth, etc.)
        **kwargs: Additional litellm parameters

    Yields:
        Response tokens/chunks as they arrive from the LLM

    Raises:
        ValueError: If OAuth2 configuration is invalid
        Exception: If LLM API call fails

    Example:
        >>> config = LLMConfig(model="gpt-5-mini", temperature=0.7)
        >>>
        >>> async for chunk in call_llm_stream("Explain quantum computing", config):
        ...     print(chunk, end="", flush=True)
        Quantum computing is a type of computation that...

    Performance:
        - First token: <500ms (immediate feedback)
        - Total time: Same as non-streaming (2-5s)
        - Perceived latency: Much better (progressive display)

    Note:
        - Streaming responses are NOT cached (real-time, non-deterministic)
        - OAuth2 authentication supported (same as call_llm)
        - Tool calling not supported in streaming mode
    """
    # Build messages list
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

    # Get API key/token (OAuth2 support)
    api_key = config.get_api_key()

    # Prepare kwargs for litellm
    llm_kwargs = dict(kwargs)
    if api_key:
        llm_kwargs["api_key"] = api_key

    # Call litellm with streaming enabled
    response = await litellm.acompletion(
        model=config.model,
        messages=messages,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        top_p=config.top_p,
        stream=True,  # Enable streaming
        **llm_kwargs,
    )

    # Yield chunks as they arrive
    async for chunk in response:  # type: ignore
        # Extract content from chunk
        if hasattr(chunk, "choices") and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, "delta"):
                delta = choice.delta
                if hasattr(delta, "content") and delta.content:
                    yield delta.content


async def stream_to_string(stream: AsyncIterator[str]) -> str:
    """Collect streaming chunks into a single string

    Utility function to convert streaming response to complete string.
    Useful for testing or when you need the full response.

    Args:
        stream: AsyncIterator of response chunks

    Returns:
        Complete response as a single string

    Example:
        >>> stream = call_llm_stream("Hello", config)
        >>> full_response = await stream_to_string(stream)
        >>> print(full_response)
        Hello! How can I help you today?
    """
    chunks: list[str] = []
    async for chunk in stream:
        chunks.append(chunk)
    return "".join(chunks)
