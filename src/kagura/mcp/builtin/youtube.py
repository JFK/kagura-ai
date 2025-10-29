"""
YouTube integration tools for Kagura AI (MCP Built-in)

This module provides YouTube video analysis capabilities via MCP.
"""

import json
import logging
import re
from typing import Any

from kagura import tool
from kagura.mcp.builtin.common import get_library_cache_dir

# Setup logger
logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str:
    """
    Extract video ID from YouTube URL.

    Args:
        url: YouTube URL

    Returns:
        Video ID

    Raises:
        ValueError: If video ID cannot be extracted
    """
    # Match various YouTube URL formats
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)",
        r"youtube\.com\/embed\/([^&\n?#]+)",
        r"youtube\.com\/v\/([^&\n?#]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")


@tool
async def get_youtube_transcript(video_url: str, lang: str = "en") -> str:
    """
    Get YouTube video transcript.

    Args:
        video_url: YouTube video URL
        lang: Language code (default: en, ja for Japanese)

    Returns:
        Video transcript text or helpful error message

    Example:
        >>> transcript = await get_youtube_transcript(
        ...     "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ...     lang="en"
        ... )
    """
    try:
        from youtube_transcript_api import (  # type: ignore[import-untyped]
            NoTranscriptFound,
            TranscriptsDisabled,
            YouTubeTranscriptApi,
        )
    except ImportError:
        return (
            "Error: youtube-transcript-api is required.\n"
            "Install with: pip install youtube-transcript-api"
        )

    try:
        # Extract video ID
        video_id = extract_video_id(video_url)

        # Create API instance (required for v0.6+)
        api = YouTubeTranscriptApi()

        # Try to get transcript in requested language
        # If not available, try auto-generated or other available languages
        try:
            transcript = api.fetch(video_id, languages=[lang])  # type: ignore[attr-defined]
        except NoTranscriptFound:  # type: ignore[misc]
            # Try to get any available transcript
            try:
                transcript = api.fetch(video_id)  # type: ignore[attr-defined]
            except (NoTranscriptFound, TranscriptsDisabled):  # type: ignore[misc]
                # No transcript available at all
                return (
                    "Transcript not available: "
                    "This video does not have subtitles.\n\n"
                    "Tip: You can still get video information using "
                    "get_youtube_metadata, or use web_search for additional context."
                )

        # Combine text segments (v0.6+ uses .text attribute)
        text = " ".join([segment.text for segment in transcript])  # type: ignore[attr-defined]

        return text

    except Exception as e:
        return f"Error getting transcript: {str(e)}"


@tool
async def get_youtube_metadata(video_url: str) -> str:
    """
    Get YouTube video metadata.

    Args:
        video_url: YouTube video URL

    Returns:
        JSON string with video metadata (title, author, duration, views, etc.)

    Example:
        >>> metadata = await get_youtube_metadata(
        ...     "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ... )
        >>> print(metadata)
    """
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        return json.dumps(
            {
                "error": "yt-dlp is required",
                "install": "pip install yt-dlp",
            },
            indent=2,
        )

    try:
        # Configure yt-dlp with proper cache directory
        cache_dir = get_library_cache_dir("yt-dlp")
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "cachedir": cache_dir,  # Use Kagura's cache directory
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            # Extract relevant metadata
            if info is None:
                return json.dumps(
                    {"error": "Failed to extract video information"}, indent=2
                )

            metadata: dict[str, Any] = {
                "title": info.get("title"),
                "channel": info.get("uploader") or info.get("channel"),
                "duration_seconds": info.get("duration"),
                "view_count": info.get("view_count"),
                "upload_date": info.get("upload_date"),
                "description": info.get("description", "")[:500],  # First 500 chars
                "tags": info.get("tags", [])[:10],  # First 10 tags
                "url": video_url,  # Include original URL for Markdown link
            }

            return json.dumps(metadata, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Failed to get metadata: {str(e)}"}, indent=2)


@tool
async def youtube_summarize(video_url: str, lang: str = "en") -> str:
    """Generate a summary of a YouTube video's content using its transcript.

    Use this tool when:
    - User provides a YouTube URL and asks for summary
    - User asks 'what is this video about'
    - Need to understand video content without watching
    - User wants key points from a long video
    - Reviewing educational or informational content

    Do NOT use for:
    - Videos without transcripts (will fail)
    - Live streams (transcripts may be incomplete)
    - Music videos or content without meaningful speech

    Automatically fetches transcript and creates structured summary.

    Args:
        video_url: YouTube video URL (full URL or youtu.be short link)
        lang: Language code for transcript:
            - "en" (English, default)
            - "ja" (Japanese)
            - "es" (Spanish)
            - "fr" (French)
            - etc.

    Returns:
        Markdown-formatted summary with:
        - Main topic/theme
        - Key points (2-3 bullet points)
        - Overall takeaway

    Example:
        # Summarize English video
        video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Summarize Japanese video
        video_url="https://youtu.be/abcdefg", lang="ja"

        # Educational content
        video_url="https://www.youtube.com/watch?v=xyz123"
    """
    # Get transcript
    transcript = await get_youtube_transcript(video_url, lang)

    if transcript.startswith("Error") or "Transcript not available" in transcript:
        return transcript

    # Get metadata for context
    metadata_json = await get_youtube_metadata(video_url)
    try:
        metadata = json.loads(metadata_json)
        title = metadata.get("title", "Unknown")
        channel = metadata.get("channel", "Unknown")
    except Exception:
        title = "Unknown"
        channel = "Unknown"

    # Use LLM to summarize
    try:
        from kagura.core.llm import LLMConfig, call_llm

        config = LLMConfig(model="gpt-4o-mini", temperature=0.3)

        prompt = f"""Summarize this YouTube video transcript concisely (3-5 sentences).

Video: {title}
Channel: {channel}
URL: {video_url}

Transcript:
{transcript[:3000]}  # Limit to first 3000 chars

Provide:
1. Main topic/theme
2. Key points (2-3 bullet points)
3. Overall takeaway

Format as Markdown with the video title as a link: [{title}]({video_url})
"""

        response = await call_llm(prompt, config)
        return str(response)

    except Exception as e:
        return (
            f"Error summarizing video: {str(e)}\n\n"
            "Transcript available but summary failed."
        )


@tool
async def youtube_fact_check(video_url: str, claim: str, lang: str = "en") -> str:
    """Verify a specific claim made in a YouTube video against web sources.

    Use this tool when:
    - User questions the accuracy of information in a video
    - A video makes a specific factual claim that needs verification
    - User explicitly asks to fact-check video content
    - Checking controversial or disputed statements in videos
    - User asks "is what they said in the video true?"

    Do NOT use for:
    - Summarizing videos (use youtube_summarize)
    - Checking opinions or subjective content
    - Videos without transcripts

    Extracts transcript and uses web search to verify the claim.

    Args:
        video_url: YouTube video URL
        claim: Specific claim to fact-check (be precise and quote if possible)
        lang: Language code for transcript (default: "en", use "ja" for Japanese)

    Returns:
        Fact-check result with verdict, evidence, and confidence

    Example:
        >>> result = await youtube_fact_check(
        ...     "https://www.youtube.com/watch?v=XXX",
        ...     "The Earth is flat"
        ... )
    """
    # Get transcript
    transcript = await get_youtube_transcript(video_url, lang)

    if transcript.startswith("Error") or "Transcript not available" in transcript:
        return f"Cannot fact-check: {transcript}"

    # Get metadata
    metadata_json = await get_youtube_metadata(video_url)
    try:
        metadata = json.loads(metadata_json)
        title = metadata.get("title", "Unknown")
    except Exception:
        title = "Unknown"

    # Use web search to fact-check
    try:
        from kagura.core.llm import LLMConfig, call_llm
        from kagura.tools import brave_web_search

        # Search for evidence
        search_results = await brave_web_search(claim, count=5)

        # Use LLM to analyze
        config = LLMConfig(model="gpt-4o-mini", temperature=0.2)

        prompt = f"""Fact-check this claim from a YouTube video.

Video: [{title}]({video_url})
Claim: "{claim}"

Video transcript excerpt:
{transcript[:2000]}

Web search results:
{search_results}

Analyze and provide:
1. **Verdict**: TRUE / FALSE / MIXED / UNVERIFIED
2. **Confidence**: 0-100%
3. **Evidence**: Key supporting/contradicting facts
4. **Summary**: Brief explanation (2-3 sentences)

Format as Markdown.
"""

        response = await call_llm(prompt, config)
        return str(response)

    except Exception as e:
        return f"Error fact-checking claim: {str(e)}"
