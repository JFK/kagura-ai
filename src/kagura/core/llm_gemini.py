"""Google Gemini SDK direct backend for multimodal

Provides direct Gemini API integration for better WebP/HEIC support
and multimodal URL processing without relying on LiteLLM.

Benefits:
- WebP/HEIC full support
- Direct URL processing (download → analyze)
- File API for caching/reuse
- Latest Gemini features immediately
"""

import time
from typing import Any

from .llm import LLMConfig, LLMResponse


async def call_gemini_direct(
    prompt: str,
    config: LLMConfig,
    media_url: str | None = None,
    media_type: str | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """Call Gemini API directly using official SDK

    Args:
        prompt: Text prompt
        config: LLM configuration (model should be gemini/*)
        media_url: Optional media URL to download and analyze
        media_type: MIME type (e.g., "image/webp", "video/mp4")
        **kwargs: Additional Gemini parameters

    Returns:
        LLMResponse with content and metadata

    Raises:
        ImportError: If google-generativeai not installed
        ValueError: If API key not set
        Exception: If API request fails

    Note:
        This function downloads media from URLs (unlike OpenAI Vision
        which accepts URLs directly). Use for WebP, HEIC, video, audio.
    """
    # Import Gemini SDK
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise ImportError(
            "google-generativeai is required for Gemini SDK backend. "
            "Install with: pip install kagura-ai[web]"
        ) from e

    # Track timing
    start_time = time.time()

    # Get API key
    api_key = config.get_api_key()
    if not api_key:
        # Try environment
        from kagura.config.env import get_google_api_key

        api_key = get_google_api_key()

    if not api_key:
        raise ValueError(
            "Google API key required. "
            "Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
        )

    # Configure Gemini
    genai.configure(api_key=api_key)

    # Remove gemini/ prefix for actual model name
    model_name = config.model.replace("gemini/", "")
    model = genai.GenerativeModel(model_name)

    # Build content parts
    content_parts: list[Any] = [prompt]

    # Download and add media if URL provided
    if media_url:
        media_data = await _download_media(media_url)
        content_parts.append(
            {"mime_type": media_type or "image/jpeg", "data": media_data}
        )

    # Generate content
    response = await model.generate_content_async(content_parts)

    duration = time.time() - start_time

    # Gemini doesn't expose token counts in the same way
    # Estimate based on text length (rough approximation)
    text_length = len(response.text)
    estimated_tokens = text_length // 4  # Rough estimate

    return LLMResponse(
        content=response.text,
        usage={
            "prompt_tokens": estimated_tokens // 2,
            "completion_tokens": estimated_tokens // 2,
            "total_tokens": estimated_tokens,
        },
        model=config.model,
        duration=duration,
    )


async def _download_media(url: str) -> bytes:
    """Download media from URL

    Args:
        url: Media URL to download

    Returns:
        Media bytes

    Raises:
        httpx.HTTPError: If download fails

    Note:
        Uses httpx for async download with 60s timeout.
    """
    try:
        import httpx
    except ImportError as e:
        raise ImportError(
            "httpx is required for media download. "
            "Install with: pip install kagura-ai[web]"
        ) from e

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60.0, follow_redirects=True)
        response.raise_for_status()
        return response.content


__all__ = ["call_gemini_direct"]
