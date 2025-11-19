"""
YouTube integration tools for Kagura AI (MCP Built-in)

This module provides YouTube video analysis capabilities via MCP.
"""

import json
import logging
import re
from typing import Any

from kagura import tool
from kagura.mcp.utils.common import get_library_cache_dir

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



async def youtube_transcript(video_url: str, lang: str = "en") -> str:
    """Get YouTube video transcript (renamed from get_youtube_transcript).

    Retrieves full transcript text for video analysis or summarization.

    Args:
        video_url: YouTube URL (full or youtu.be short link)
        lang: Language code (default: "en", use "ja" for Japanese)

    Returns:
        Full transcript text or error message

    Examples:
        # English transcript
        transcript = youtube_transcript(
            "https://www.youtube.com/watch?v=VIDEO_ID"
        )

        # Japanese transcript
        transcript = youtube_transcript(
            "https://youtu.be/VIDEO_ID",
            lang="ja"
        )

    💡 TIP: Use with LLM to summarize or analyze video content.
    🌐 Cross-platform: Works across all AI assistants.
    """
    try:
        from youtube_transcript_api import (  # type: ignore[import-untyped]
            NoTranscriptFound,
            TranscriptsDisabled,
            YouTubeTranscriptApi,
        )
    except ImportError:
        return json.dumps(
            {
                "error": "Missing dependency: youtube-transcript-api",
                "help": "Install with: pip install youtube-transcript-api",
            }
        )

    try:
        video_id = extract_video_id(video_url)

        if not video_id:
            return json.dumps({"error": "Invalid YouTube URL", "url": video_url})

        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])

        # Combine all text
        full_text = "\n".join(item["text"] for item in transcript_list)

        return json.dumps(
            {
                "video_id": video_id,
                "language": lang,
                "transcript": full_text,
                "segments": len(transcript_list),
            },
            indent=2,
            ensure_ascii=False,
        )

    except NoTranscriptFound:
        return json.dumps(
            {
                "error": f"No transcript found for language: {lang}",
                "video_id": video_id,
                "help": "Try a different language code (en, ja, es, etc.)",
            }
        )
    except TranscriptsDisabled:
        return json.dumps(
            {
                "error": "Transcripts are disabled for this video",
                "video_id": video_id,
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e), "video_url": video_url})
