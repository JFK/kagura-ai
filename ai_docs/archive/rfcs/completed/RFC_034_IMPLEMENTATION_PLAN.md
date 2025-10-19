# RFC-034 Implementation Plan: URL Multimodal Analysis + Smart YouTube Search

**RFC**: RFC-034
**Issue**: #280
**Target Version**: v2.7.0
**Duration**: 14-16 hours (2-3 days)
**Priority**: ⭐⭐⭐ High

---

## 📅 Day-by-Day Plan

### Day 1: Core Vision + Gemini SDK (8 hours)

#### Morning (4 hours): Phase 1 - OpenAI Vision URL

**9:00-10:30** (1.5h): `llm_openai.py` - Vision URL support
```python
# src/kagura/core/llm_openai.py

async def call_openai_vision_url(
    image_url: str,
    prompt: str,
    config: LLMConfig
) -> LLMResponse:
    """Analyze image from URL with OpenAI Vision"""
    client = AsyncOpenAI(api_key=config.get_api_key())

    response = await client.chat.completions.create(
        model=config.model,  # gpt-4o or gpt-5
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "detail": "high"  # or "low", "auto"
                    }
                }
            ]
        }],
        max_tokens=config.max_tokens or 4096
    )

    return LLMResponse(
        content=response.choices[0].message.content or "",
        usage={
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        },
        model=config.model,
        duration=...
    )
```

**10:30-12:00** (1.5h): Media detector utility
```python
# src/kagura/utils/media_detector.py (new)

import httpx
from typing import Literal

MediaType = Literal["image", "video", "audio", "text", "unknown"]

def is_image_url(url: str) -> bool:
    """Check if URL is likely an image"""
    image_exts = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic")
    return url.lower().endswith(image_exts)

def is_video_url(url: str) -> bool:
    """Check if URL is likely a video"""
    video_exts = (".mp4", ".mov", ".avi", ".mkv", ".webm")
    return url.lower().endswith(video_exts)

def is_youtube_url(url: str) -> bool:
    """Check if URL is YouTube"""
    return "youtube.com" in url or "youtu.be" in url

async def detect_media_type_from_url(url: str) -> tuple[MediaType, str]:
    """Detect media type from URL

    Returns:
        (media_type, mime_type) e.g. ("image", "image/jpeg")
    """
    # Quick check from extension
    if is_image_url(url):
        ext = url.split(".")[-1].lower()
        mime_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "gif": "image/gif",
            "webp": "image/webp", "heic": "image/heic"
        }
        return ("image", mime_map.get(ext, "image/jpeg"))

    if is_video_url(url):
        return ("video", "video/mp4")

    # HEAD request for Content-Type
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(url, follow_redirects=True, timeout=5.0)
            content_type = response.headers.get("content-type", "").split(";")[0]

            if content_type.startswith("image/"):
                return ("image", content_type)
            elif content_type.startswith("video/"):
                return ("video", content_type)
            elif content_type.startswith("audio/"):
                return ("audio", content_type)
            else:
                return ("text", content_type)
    except:
        return ("unknown", "application/octet-stream")
```

**13:00-14:00** (1h): Chat integration - image URL tool
```python
# src/kagura/chat/session.py

async def _analyze_image_url_tool(
    url: str,
    prompt: str = "Analyze this image in detail."
) -> str:
    """Analyze image from URL using Vision API

    Auto-selects:
    - OpenAI Vision (gpt-4o) for jpg/png/gif (direct URL)
    - Gemini for webp/heic (download required)
    """
    from rich.console import Console
    from kagura.utils.media_detector import detect_media_type_from_url
    from kagura.core.llm import LLMConfig
    from kagura.core.llm_openai import call_openai_vision_url

    console = Console()
    console.print(f"[dim]🌐 Analyzing image from: {url}...[/]")

    media_type, mime_type = await detect_media_type_from_url(url)

    if media_type != "image":
        return f"Error: URL is not an image ({media_type})"

    # Standard formats → OpenAI Vision (fast, no download)
    if mime_type in ["image/jpeg", "image/png", "image/gif"]:
        console.print("[dim]Using OpenAI Vision (direct URL)...[/]")
        config = LLMConfig(model="gpt-4o")
        result = await call_openai_vision_url(url, prompt, config)
        console.print("[dim]✓ Analysis complete[/]")
        return result.content

    # WebP/HEIC → Gemini (download)
    elif mime_type in ["image/webp", "image/heic", "image/heif"]:
        console.print("[dim]Using Gemini (downloading WebP/HEIC)...[/]")
        # TODO: Phase 2 - Gemini SDK
        return "WebP/HEIC analysis coming in Phase 2"

    else:
        return f"Unsupported image format: {mime_type}"
```

#### Afternoon (4 hours): Phase 2 - Gemini SDK Direct

**14:00-16:00** (2h): Gemini backend implementation
```python
# src/kagura/core/llm_gemini.py (new file, ~250 lines)

"""Google Gemini SDK direct backend for multimodal URLs

Supports:
- Image URLs (download → analyze)
- Video URLs (download → analyze)
- Audio URLs (download → transcribe)
- WebP, HEIC full support
"""

import httpx
import tempfile
from pathlib import Path
from typing import Any
from google import generativeai as genai

from .llm import LLMConfig, LLMResponse

async def call_gemini_direct(
    prompt: str,
    config: LLMConfig,
    media_url: str | None = None,
    media_type: str | None = None,
    **kwargs: Any
) -> LLMResponse:
    """Call Gemini API directly (bypass LiteLLM)

    Args:
        prompt: Text prompt
        config: LLM config (model should be gemini/*)
        media_url: Optional media URL to download and analyze
        media_type: MIME type (e.g., "image/webp")

    Returns:
        LLMResponse with analysis
    """
    # Configure Gemini
    api_key = config.get_api_key()
    if not api_key:
        # Try environment
        from kagura.config.env import get_google_api_key
        api_key = get_google_api_key()

    genai.configure(api_key=api_key)

    # Remove gemini/ prefix for actual model name
    model_name = config.model.replace("gemini/", "")
    model = genai.GenerativeModel(model_name)

    # Build content
    content_parts = [prompt]

    # Download and add media if URL provided
    if media_url:
        media_data = await _download_media(media_url)
        content_parts.append({
            "mime_type": media_type or "image/jpeg",
            "data": media_data
        })

    # Generate
    import time
    start = time.time()

    response = await model.generate_content_async(content_parts)

    duration = time.time() - start

    return LLMResponse(
        content=response.text,
        usage={
            "prompt_tokens": 0,  # Gemini doesn't expose token counts
            "completion_tokens": 0,
            "total_tokens": 0
        },
        model=config.model,
        duration=duration
    )

async def _download_media(url: str) -> bytes:
    """Download media from URL

    Returns:
        Media bytes

    Raises:
        httpx.HTTPError: If download fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60.0)
        response.raise_for_status()
        return response.content

__all__ = ["call_gemini_direct"]
```

**16:00-18:00** (2h): Router integration + Chat tool update
```python
# src/kagura/core/llm.py

def _should_use_gemini_direct(model: str) -> bool:
    """Check if should use Gemini SDK directly"""
    return model.startswith("gemini/")

async def call_llm(prompt, config, **kwargs):
    # Triple routing
    if _should_use_openai_direct(config.model):
        return await call_openai_direct(...)
    elif _should_use_gemini_direct(config.model):  # NEW
        from .llm_gemini import call_gemini_direct
        return await call_gemini_direct(prompt, config, **kwargs)
    else:
        return await _call_litellm(...)
```

**Chat tool update**:
```python
# src/kagura/chat/session.py

# Update _analyze_image_url_tool to support WebP via Gemini
elif mime_type in ["image/webp", "image/heic", "image/heif"]:
    console.print("[dim]Using Gemini SDK (WebP/HEIC)...[/]")
    from kagura.core.llm import LLMConfig
    from kagura.core.llm_gemini import call_gemini_direct

    config = LLMConfig(model="gemini/gemini-2.0-flash")
    result = await call_gemini_direct(
        prompt,
        config,
        media_url=url,
        media_type=mime_type
    )
    console.print("[dim]✓ Analysis complete[/]")
    return result.content
```

---

### Day 2: YouTube Integration + Testing (6-8 hours)

#### Morning (4 hours): Phase 6 - Smart YouTube Search

**9:00-10:30** (1.5h): YouTube detection + parallel fetching
```python
# src/kagura/chat/session.py

def _extract_youtube_urls(search_results_json: str) -> list[str]:
    """Extract YouTube URLs from Brave Search results"""
    import json

    try:
        results = json.loads(search_results_json)
    except:
        return []

    youtube_urls = []
    for result in results:
        url = result.get("url", "")
        if "youtube.com/watch" in url or "youtu.be/" in url:
            youtube_urls.append(url)

    return youtube_urls

async def _fetch_youtube_enhanced_data(url: str) -> dict:
    """Fetch YouTube metadata + transcript (safe)

    Returns:
        {"url": str, "title": str, "transcript": str | None, "duration": str}
    """
    from kagura.tools.youtube import get_youtube_metadata, get_youtube_transcript

    try:
        # Always fetch metadata
        metadata_str = await get_youtube_metadata(url)
        metadata = json.loads(metadata_str)

        # Try transcript (may fail)
        transcript = None
        try:
            transcript = await get_youtube_transcript(url, lang="en")
            # Truncate to reasonable length
            if len(transcript) > 2000:
                transcript = transcript[:2000] + "... (truncated)"
        except:
            pass  # Transcript not available

        return {
            "url": url,
            "title": metadata.get("title", "Unknown"),
            "duration": metadata.get("duration", ""),
            "transcript": transcript
        }
    except Exception as e:
        return {"url": url, "error": str(e)}
```

**10:30-12:00** (1.5h): Enhanced Brave Search tool
```python
# src/kagura/chat/session.py

async def _brave_search_tool(
    query: str,
    count: int = 5,
    enhance_youtube: bool = True
) -> str:
    """Search web with optional YouTube enhancement

    If enhance_youtube=True and YouTube videos found:
    - Automatically fetches transcripts (parallel)
    - Merges into search results
    - Provides richer context to LLM
    """
    from rich.console import Console
    from kagura.tools.brave_search import brave_web_search
    import json
    import asyncio

    console = Console()
    console.print(f"[dim]🔍 Brave Search: {query}...[/]")

    # Basic search
    results_json = await brave_web_search(query, count=count)

    # YouTube enhancement disabled or no results
    if not enhance_youtube:
        console.print("[dim]✓ Search completed[/]")
        return results_json

    # Extract YouTube URLs
    youtube_urls = _extract_youtube_urls(results_json)

    if not youtube_urls:
        console.print("[dim]✓ Search completed (no YouTube)[/]")
        return results_json

    # Fetch YouTube data (parallel)
    console.print(
        f"[dim]📺 Found {len(youtube_urls)} YouTube videos, "
        f"fetching transcripts...[/]"
    )

    youtube_tasks = [
        _fetch_youtube_enhanced_data(url)
        for url in youtube_urls[:3]  # Top 3 only
    ]

    # Wait max 30 seconds
    youtube_data = await asyncio.wait_for(
        asyncio.gather(*youtube_tasks, return_exceptions=True),
        timeout=30.0
    )

    # Merge transcripts into results
    results = json.loads(results_json)
    youtube_map = {data["url"]: data for data in youtube_data if isinstance(data, dict)}

    for result in results:
        url = result.get("url", "")
        if url in youtube_map:
            yt_data = youtube_map[url]
            if yt_data.get("transcript"):
                result["youtube_transcript_preview"] = yt_data["transcript"][:300]
                result["youtube_has_full_transcript"] = True
                result["youtube_duration"] = yt_data.get("duration", "")

    enhanced_json = json.dumps(results, ensure_ascii=False, indent=2)

    transcripts_count = sum(
        1 for data in youtube_data
        if isinstance(data, dict) and data.get("transcript")
    )
    console.print(f"[dim]✓ Search completed ({transcripts_count} transcripts fetched)[/]")

    return enhanced_json
```

**13:00-14:30** (1.5h): Update chat agent prompt
```python
# src/kagura/chat/session.py - chat_agent docstring

    Web & Content:
    - brave_search(query, count=5): Search web with automatic YouTube enhancement
      - If YouTube videos found, transcripts are auto-fetched (parallel)
      - Results include transcript previews
      - Use this for research - you'll get richer context automatically
    - analyze_image_url(url, prompt): Analyze image from URL (jpg/png/gif/webp)
      - Direct URL analysis (no download needed for standard formats)
      - WebP/HEIC supported
    - url_fetch(url): Fetch webpage text content

    Automatic tool usage guidelines:
    - Image URLs → use analyze_image_url (supports jpg/png/gif/webp/heic)
    - Web research → use brave_search (auto-fetches YouTube transcripts)
    - YouTube links → brave_search will handle automatically
    - General URLs → use url_fetch (for text content)
```

#### Afternoon (4 hours): Phase 2 Continuation + Testing

**14:30-16:30** (2h): Gemini backend completion + tests
```python
# tests/core/test_llm_gemini.py (new, ~300 lines)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from kagura.core.llm import LLMConfig, _should_use_gemini_direct
from kagura.core.llm_gemini import call_gemini_direct

class TestGeminiBackendRouting:
    """Tests for Gemini backend detection"""

    def test_should_use_gemini_direct():
        assert _should_use_gemini_direct("gemini/gemini-2.0-flash") is True
        assert _should_use_gemini_direct("gemini/gemini-1.5-pro") is True
        assert _should_use_gemini_direct("gpt-5-mini") is False
        assert _should_use_gemini_direct("claude-3-5-sonnet") is False

class TestGeminiDirectCalling:
    """Tests for Gemini SDK direct calling"""

    @pytest.mark.asyncio
    async def test_call_gemini_text_only():
        """Test Gemini text-only call"""
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Gemini response"
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_model_class.return_value = mock_model

            config = LLMConfig(model="gemini/gemini-2.0-flash")
            result = await call_gemini_direct("test prompt", config)

            assert result.content == "Gemini response"
            assert result.model == "gemini/gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_call_gemini_with_image_url():
        """Test Gemini with image URL (downloads)"""
        # Mock httpx download
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = b"fake image data"
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock Gemini
            with patch("google.generativeai.GenerativeModel") as mock_model_class:
                mock_model = MagicMock()
                mock_gen_response = MagicMock()
                mock_gen_response.text = "Image analysis result"
                mock_model.generate_content_async = AsyncMock(
                    return_value=mock_gen_response
                )
                mock_model_class.return_value = mock_model

                config = LLMConfig(model="gemini/gemini-2.0-flash")
                result = await call_gemini_direct(
                    "Describe image",
                    config,
                    media_url="https://example.com/image.webp",
                    media_type="image/webp"
                )

                assert result.content == "Image analysis result"
                # Verify download was called
                mock_client.get.assert_called_once()
```

**16:30-18:00** (1.5h): Media detector tests
```python
# tests/utils/test_media_detector.py (new, ~150 lines)

import pytest
from kagura.utils.media_detector import (
    is_image_url,
    is_video_url,
    is_youtube_url,
    detect_media_type_from_url
)

class TestURLDetection:
    def test_is_image_url():
        assert is_image_url("https://example.com/photo.jpg") is True
        assert is_image_url("https://example.com/image.webp") is True
        assert is_image_url("https://example.com/page.html") is False

    def test_is_youtube_url():
        assert is_youtube_url("https://youtube.com/watch?v=xxx") is True
        assert is_youtube_url("https://youtu.be/xxx") is True
        assert is_youtube_url("https://vimeo.com/xxx") is False

    @pytest.mark.asyncio
    async def test_detect_from_extension():
        media_type, mime = await detect_media_type_from_url(
            "https://example.com/image.webp"
        )
        assert media_type == "image"
        assert mime == "image/webp"
```

---

### Day 3: Testing + Documentation (2-3 hours)

**9:00-11:00** (2h): Integration tests
```python
# tests/chat/test_url_media_analysis.py (new, ~200 lines)

@pytest.mark.asyncio
async def test_analyze_image_url_openai():
    """Test image URL with OpenAI Vision"""
    with patch("kagura.core.llm_openai.call_openai_vision_url") as mock:
        mock.return_value = LLMResponse(
            content="Image shows a diagram",
            usage={...},
            model="gpt-4o",
            duration=1.0
        )

        result = await _analyze_image_url_tool(
            "https://example.com/diagram.jpg"
        )

        assert "diagram" in result.lower()

@pytest.mark.asyncio
async def test_brave_search_with_youtube_enhancement():
    """Test Brave Search auto-fetches YouTube transcripts"""
    # Mock search results with YouTube
    search_results = json.dumps([
        {"url": "https://python.org", "title": "Python Docs"},
        {"url": "https://youtube.com/watch?v=123", "title": "Python Tutorial"}
    ])

    with patch("kagura.tools.brave_search.brave_web_search") as mock_search:
        mock_search.return_value = search_results

        with patch("kagura.tools.youtube.get_youtube_transcript") as mock_transcript:
            mock_transcript.return_value = "Tutorial transcript here..."

            result = await _brave_search_tool("Python tutorial")

            # Should include transcript
            assert "transcript" in result.lower()
```

**11:00-12:00** (1h): Documentation
- Update `docs/en/guides/chat-multimodal.md`
- Update `docs/en/guides/web-integration.md`
- Add examples to README

---

## 📊 Success Criteria

### Functional
- ✅ `analyze <image-url>` works (jpg/png/gif/webp)
- ✅ WebP URLs supported (Gemini SDK)
- ✅ Video/Audio URLs supported (Gemini SDK)
- ✅ **Brave Search auto-fetches YouTube transcripts** ← NEW
- ✅ **Parallel YouTube processing** ← NEW
- ✅ Auto-format detection
- ✅ Temp file cleanup (Gemini)

### Quality
- ✅ 40+ new tests
- ✅ Pyright 0 errors
- ✅ Coverage 90%+
- ✅ No memory leaks

### Performance
- ✅ OpenAI Vision: <2 seconds (no download)
- ✅ Gemini WebP: <5 seconds (download)
- ✅ YouTube transcripts: <10 seconds (parallel, top 3)

### UX
- ✅ Single command
- ✅ **Auto-enhanced search results** ← NEW
- ✅ Progress indicators
- ✅ Helpful errors

---

## 📋 Checklist

### Phase 1: OpenAI Vision
- [ ] `llm_openai.py`: Add `call_openai_vision_url()`
- [ ] `media_detector.py`: URL detection utilities
- [ ] `session.py`: `_analyze_image_url_tool`
- [ ] Tests: OpenAI Vision URL tests

### Phase 2: Gemini SDK
- [ ] `llm_gemini.py`: Full Gemini backend (~250 lines)
- [ ] `llm.py`: Triple routing
- [ ] `session.py`: WebP/HEIC support
- [ ] Tests: Gemini SDK tests

### Phase 6: YouTube Integration
- [ ] `session.py`: `_extract_youtube_urls()`
- [ ] `session.py`: `_fetch_youtube_enhanced_data()`
- [ ] `session.py`: Enhanced `_brave_search_tool`
- [ ] Tests: YouTube enhancement tests

### Testing
- [ ] Unit tests: 40+ tests
- [ ] Integration tests
- [ ] Manual testing (kagura chat)

### Documentation
- [ ] Update multimodal guide
- [ ] Update web integration guide
- [ ] Add README examples

---

## 🚀 Execution Plan

1. **Merge Issue #275 first** (Hybrid LLM backend)
2. Create branch from Issue #280
3. Implement Phase 1-2-6 (Day 1-2)
4. Testing (Day 3)
5. Create PR
6. Merge → v2.7.0

---

**Note**: This implementation builds on Issue #275 (Hybrid backend),
extending it from dual (OpenAI + LiteLLM) to triple (OpenAI + Gemini + LiteLLM).
