# RFC-034: URL-Based Multimodal Analysis

**Status**: Draft
**Created**: 2025-10-17
**Author**: Claude Code + JFK
**Priority**: ⭐⭐⭐ High

---

## 📋 Problem Statement

### Current Limitation

Users cannot directly analyze images/videos from URLs in `kagura chat`:

```
[You] > analyze https://example.com/image.jpg

🌐 Fetching URL...
[AI] > I fetched the URL but couldn't parse as image (got binary data)
```

**Workaround**: Manual download → re-upload → analyze

**Impact**: Poor UX, multi-step process

### Root Cause

1. `_url_fetch_tool` only extracts text (uses WebScraper)
2. No image URL detection
3. No temporary file management for downloaded media
4. Gemini API doesn't support direct URLs (requires download)

---

## 🎯 Proposed Solution

### Vision

**Seamless URL media analysis**:
```
[You] > analyze https://example.com/diagram.jpg

🌐 Downloading image...
🔍 Analyzing with Vision API...

[AI] > This diagram shows a system architecture with...
```

### Architecture: Triple Backend System

**Hybrid Backend Evolution**:
```
Current (v2.6.x):
- OpenAI SDK: gpt-*, o1-*
- LiteLLM: claude-*, gemini/*, etc.

Proposed (v2.7.0):
- OpenAI SDK: gpt-*, o1-* (+ Vision for image URLs) ← NEW
- Gemini SDK: gemini/* (direct, for URL multimodal) ← NEW
- LiteLLM: claude-*, etc.
```

**Benefits**:
- ✅ Best-of-breed: OpenAI Vision (image URLs), Gemini (WebP/video/audio)
- ✅ Direct SDK access (faster, more features)
- ✅ Unified interface (transparent to users)

---

## 🏗️ Implementation Plan

### Phase 1: OpenAI Vision URL Support (3 hours)

#### 1.1 Core Implementation

**File**: `src/kagura/core/llm_openai.py`

```python
async def call_openai_vision_url(
    image_url: str,
    prompt: str,
    config: LLMConfig
) -> LLMResponse:
    """Analyze image from URL using OpenAI Vision API

    Args:
        image_url: Direct image URL (jpg, png, gif, webp)
        prompt: Analysis prompt
        config: LLM config (should use gpt-4o or gpt-5)

    Returns:
        Analysis result
    """
    client = AsyncOpenAI(api_key=config.get_api_key())

    response = await client.chat.completions.create(
        model=config.model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }]
    )

    return LLMResponse(
        content=response.choices[0].message.content,
        usage={...},
        model=config.model,
        duration=...
    )
```

#### 1.2 URL Detection

**File**: `src/kagura/utils/media_detector.py` (new)

```python
def is_image_url(url: str) -> bool:
    """Check if URL points to an image"""
    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
    return any(url.lower().endswith(ext) for ext in image_exts)

async def detect_media_type_from_url(url: str) -> str:
    """Detect media type from URL (HEAD request)

    Returns: "image/jpeg", "video/mp4", "text/html", etc.
    """
    import httpx

    # Try extension first (fast)
    if url.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif url.endswith(".png"):
        return "image/png"
    elif url.endswith(".webp"):
        return "image/webp"

    # HEAD request for Content-Type
    async with httpx.AsyncClient() as client:
        response = await client.head(url, follow_redirects=True)
        return response.headers.get("content-type", "text/html").split(";")[0]
```

#### 1.3 Chat Integration

**File**: `src/kagura/chat/session.py`

```python
async def _analyze_image_url_tool(url: str, prompt: str = "Analyze this image in detail.") -> str:
    """Analyze image from URL using Vision API

    Auto-selects:
    - OpenAI Vision (gpt-4o) for standard formats
    - Gemini for WebP/HEIC
    """
    from kagura.utils.media_detector import detect_media_type_from_url
    from kagura.core.llm import LLMConfig
    from kagura.core.llm_openai import call_openai_vision_url

    console = Console()
    console.print(f"[dim]🌐 Analyzing image from URL: {url}...[/]")

    media_type = await detect_media_type_from_url(url)

    if media_type in ["image/jpeg", "image/png", "image/gif"]:
        # Use OpenAI Vision (direct URL)
        config = LLMConfig(model="gpt-4o")
        result = await call_openai_vision_url(url, prompt, config)
        console.print("[dim]✓ Analysis complete (OpenAI Vision)[/]")
        return result.content
    else:
        # WebP/HEIC → Gemini (download required)
        # TODO: Phase 2
        return "WebP/HEIC not yet supported (Phase 2)"
```

**Update tools list**:
```python
tools=[
    ...
    _analyze_image_url_tool,  # NEW
    _url_fetch_tool,  # Existing (webpage text)
    ...
]
```

---

### Phase 2: Gemini SDK Direct (3 hours)

#### 2.1 Gemini Backend

**File**: `src/kagura/core/llm_gemini.py` (new, ~250 lines)

```python
\"\"\"Google Gemini SDK direct backend for multimodal\"\"\"

import httpx
import tempfile
from pathlib import Path
from google import generativeai as genai

async def call_gemini_direct(
    prompt: str,
    config: LLMConfig,
    media_url: str | None = None,
    media_type: str | None = None,
    **kwargs
) -> LLMResponse:
    \"\"\"Call Gemini API directly (bypassing LiteLLM)

    Supports:
    - Text-only
    - Image URL (download → analyze)
    - Video URL (download → analyze)
    - Audio URL (download → transcribe)
    \"\"\"
    # Configure
    genai.configure(api_key=config.get_api_key())
    model = genai.GenerativeModel(config.model.replace("gemini/", ""))

    content_parts = [prompt]

    # Download media if URL provided
    if media_url:
        media_data = await _download_media(media_url)
        content_parts.append({
            "mime_type": media_type,
            "data": media_data
        })

    # Generate
    response = await model.generate_content_async(content_parts)

    return LLMResponse(
        content=response.text,
        usage={...},
        model=config.model,
        duration=...
    )

async def _download_media(url: str) -> bytes:
    \"\"\"Download media from URL\"\"\"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60.0)
        response.raise_for_status()
        return response.content
```

#### 2.2 Router Update

**File**: `src/kagura/core/llm.py`

```python
def _should_use_gemini_direct(model: str) -> bool:
    \"\"\"Check if should use Gemini SDK directly\"\"\"
    return model.startswith("gemini/")

async def call_llm(prompt, config, **kwargs):
    if _should_use_openai_direct(config.model):
        return await call_openai_direct(...)
    elif _should_use_gemini_direct(config.model):  # NEW
        return await call_gemini_direct(...)
    else:
        return await _call_litellm(...)
```

---

### Phase 3: WebP Support Validation (1 hour)

**Verification**:
- ✅ `file_types.py` already includes `.webp`
- ✅ Gemini API supports WebP
- ✅ OpenAI Vision supports WebP

**Action**: Add integration test for WebP

---

### Phase 4: Testing (2 hours)

**New files**:
1. `tests/core/test_llm_gemini.py` (~300 lines)
2. `tests/utils/test_media_detector.py` (~150 lines)
3. `tests/chat/test_url_media_analysis.py` (~200 lines)

**Test coverage**:
- [ ] OpenAI Vision URL calling
- [ ] Gemini SDK direct calling
- [ ] Media type detection
- [ ] Temp file cleanup
- [ ] Error handling (404, invalid format)
- [ ] WebP support
- [ ] Integration test

---

### Phase 5: Documentation (1 hour)

**Updates**:
- `docs/en/tutorials/13-multimodal-rag.md` - URL examples
- `docs/en/guides/chat-multimodal.md` - Image URL usage
- `README.md` - Feature highlight

---

## 📊 Comparison: OpenAI vs Gemini for URLs

| Feature | OpenAI Vision | Gemini SDK |
|---------|---------------|------------|
| **Direct URL** | ✅ Yes | ❌ No (download) |
| **WebP** | ✅ Yes | ✅ Yes |
| **HEIC/HEIF** | ❌ No | ✅ Yes |
| **Video URL** | ❌ No | ✅ Yes (download) |
| **Audio URL** | ❌ No | ✅ Yes (download) |
| **Complexity** | Low | Medium |
| **Speed** | Fast (no download) | Slower (download) |

**Best Strategy**: **Hybrid**
- Image (jpg/png/gif) → OpenAI Vision (fast, no download)
- WebP/HEIC/video/audio → Gemini SDK (download required)

---

---

## 🎯 Phase 6: Smart Web Search with YouTube Integration (NEW) ⭐

### Problem

**Current**: Brave Search返す結果にYouTube動画が含まれることがある

```
[You] > Search for Python tutorial

🔍 Brave Search: Python tutorial...
Results:
1. Python Official Docs (text)
2. YouTube: Python Tutorial for Beginners (video) ← 字幕取得すればより良い
3. Real Python Article (text)
```

**Limitation**: YouTube URLを見つけても、自動で字幕取得しない

### Proposed: Intelligent Search Result Processing

**Auto-enhance YouTube results**:

```python
async def _brave_search_with_youtube_tool(query: str, count: int = 5) -> str:
    """Search web and auto-process YouTube results"""

    # 1. Brave Search
    results = await brave_web_search(query, count)

    # 2. Detect YouTube URLs
    youtube_urls = _extract_youtube_urls(results)

    # 3. Fetch transcripts (parallel)
    if youtube_urls:
        console.print(f"[dim]📺 Found {len(youtube_urls)} YouTube videos, fetching transcripts...[/]")

        transcripts = await asyncio.gather(*[
            _get_youtube_transcript_safe(url)
            for url in youtube_urls[:3]  # Limit to top 3
        ])

        # 4. Enhance results with transcript snippets
        enhanced_results = _merge_youtube_transcripts(results, transcripts)
        return enhanced_results

    return results

async def _get_youtube_transcript_safe(url: str) -> dict:
    """Get YouTube transcript (returns empty if unavailable)"""
    try:
        transcript = await get_youtube_transcript(url)
        return {"url": url, "transcript": transcript[:500]}  # First 500 chars
    except:
        return {"url": url, "transcript": None}
```

**Example Output**:
```
Search results:
1. Python Official Docs
   https://python.org/tutorial

2. YouTube: Python Tutorial for Beginners (23:45)
   https://youtube.com/watch?v=xxx
   📺 Transcript preview: "In this tutorial we'll cover variables, functions..."
   [Full transcript available - 5000 words]

3. Real Python Article
   https://realpython.com/...
```

### Benefits

- ✅ **自動YouTube検出**: 検索結果から自動抽出
- ✅ **並列処理**: 複数動画の字幕を同時取得
- ✅ **LLMに渡す情報が豊富**: テキスト+字幕で高品質な回答
- ✅ **ユーザー操作不要**: 完全自動

### Implementation

**File**: `src/kagura/chat/session.py`

```python
# Replace _brave_search_tool with enhanced version
async def _brave_search_tool(query: str, count: int = 5, enable_youtube: bool = True) -> str:
    """Search web with optional YouTube transcript enhancement"""

    if not enable_youtube:
        # Simple search (existing)
        return await brave_web_search(query, count)

    # Enhanced search with YouTube
    results_json = await brave_web_search(query, count)
    results = json.loads(results_json)

    # Extract YouTube URLs
    youtube_entries = [
        r for r in results
        if "youtube.com" in r.get("url", "") or "youtu.be" in r.get("url", "")
    ]

    if not youtube_entries:
        return results_json  # No YouTube, return as-is

    console.print(f"[dim]📺 Fetching transcripts for {len(youtube_entries)} videos...[/]")

    # Fetch transcripts (parallel, with timeout)
    tasks = [
        _fetch_youtube_data(entry["url"])
        for entry in youtube_entries[:3]  # Top 3 only
    ]
    youtube_data = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge transcripts into results
    for entry, data in zip(youtube_entries, youtube_data):
        if isinstance(data, dict) and data.get("transcript"):
            entry["transcript_preview"] = data["transcript"][:300]
            entry["has_full_transcript"] = True

    return json.dumps(results, ensure_ascii=False, indent=2)

async def _fetch_youtube_data(url: str) -> dict:
    """Fetch YouTube metadata + transcript"""
    try:
        # Metadata
        metadata = await get_youtube_metadata(url)
        # Transcript (may fail)
        try:
            transcript = await get_youtube_transcript(url)
        except:
            transcript = None

        return {
            "url": url,
            "metadata": metadata,
            "transcript": transcript
        }
    except Exception as e:
        return {"url": url, "error": str(e)}
```

---

## 🎯 Updated Success Criteria

### Functional
- ✅ `analyze <image-url>` works instantly
- ✅ WebP URLs supported
- ✅ Video/Audio URLs supported (Gemini)
- ✅ **YouTube検索結果の自動処理** ← NEW
- ✅ **並列字幕取得** ← NEW
- ✅ Auto-format detection
- ✅ Temp file cleanup

### Quality
- ✅ 40+ new tests
- ✅ Pyright 0 errors
- ✅ No memory leaks (temp files)

### UX
- ✅ Single command (no manual steps)
- ✅ **YouTube動画の文脈も自動取得** ← NEW
- ✅ Clear progress indicators
- ✅ Helpful error messages

---

## 📅 Updated Timeline

**Total**: 14-16 hours (2-3 days)

- Phase 1 (OpenAI Vision): 3 hours
- Phase 2 (Gemini SDK): 3 hours
- Phase 3 (WebP validation): 1 hour
- **Phase 6 (YouTube Integration): 3 hours** ← NEW
- Phase 4 (Testing): 3 hours (増加)
- Phase 5 (Documentation): 1 hour

**Target Version**: v2.7.0

---

## 🚀 Next Steps

1. Create GitHub Issue from this RFC
2. Create implementation plan (5 phases)
3. Implement after Issue #275 merge
