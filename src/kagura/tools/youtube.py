"""
YouTube integration tools for Kagura AI
"""

import json
import re
from typing import Any

from kagura import tool


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
        Video transcript text

    Example:
        >>> transcript = await get_youtube_transcript(
        ...     "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ...     lang="en"
        ... )
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except ImportError:
        return (
            "Error: youtube-transcript-api is required.\n"
            "Install with: pip install youtube-transcript-api"
        )

    try:
        # Extract video ID
        video_id = extract_video_id(video_url)

        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=[lang]
        )

        # Combine text segments
        text = " ".join([segment["text"] for segment in transcript_list])

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
        # Configure yt-dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            # Extract relevant metadata
            metadata: dict[str, Any] = {
                "title": info.get("title"),
                "channel": info.get("uploader") or info.get("channel"),
                "duration_seconds": info.get("duration"),
                "view_count": info.get("view_count"),
                "upload_date": info.get("upload_date"),
                "description": info.get("description", "")[:500],  # First 500 chars
                "tags": info.get("tags", [])[:10],  # First 10 tags
            }

            return json.dumps(metadata, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Failed to get metadata: {str(e)}"}, indent=2)
