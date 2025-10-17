"""Media type detection for URLs

Utilities for detecting media types from URLs, including:
- Image URLs (jpg, png, gif, webp, etc.)
- Video URLs (mp4, mov, etc.)
- YouTube URLs
- Content-Type detection via HTTP HEAD request
"""

from typing import Literal

MediaType = Literal["image", "video", "audio", "text", "unknown"]


def is_image_url(url: str) -> bool:
    """Check if URL points to an image

    Args:
        url: URL to check

    Returns:
        True if URL ends with image extension

    Example:
        >>> is_image_url("https://example.com/photo.jpg")
        True
        >>> is_image_url("https://example.com/page.html")
        False
    """
    image_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".heic",
        ".heif",
    )
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in image_extensions)


def is_video_url(url: str) -> bool:
    """Check if URL points to a video

    Args:
        url: URL to check

    Returns:
        True if URL ends with video extension
    """
    video_extensions = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv")
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in video_extensions)


def is_audio_url(url: str) -> bool:
    """Check if URL points to audio

    Args:
        url: URL to check

    Returns:
        True if URL ends with audio extension
    """
    audio_extensions = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in audio_extensions)


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube video

    Args:
        url: URL to check

    Returns:
        True if URL is YouTube

    Example:
        >>> is_youtube_url("https://youtube.com/watch?v=xxx")
        True
        >>> is_youtube_url("https://youtu.be/xxx")
        True
    """
    return "youtube.com" in url or "youtu.be" in url


async def detect_media_type_from_url(url: str) -> tuple[MediaType, str]:
    """Detect media type from URL

    Checks extension first (fast), then makes HEAD request for Content-Type.

    Args:
        url: URL to check

    Returns:
        Tuple of (media_type, mime_type)
        Example: ("image", "image/jpeg")

    Example:
        >>> media_type, mime = await detect_media_type_from_url(
        ...     "https://example.com/image.webp"
        ... )
        >>> print(media_type)  # "image"
        >>> print(mime)  # "image/webp"
    """
    # Quick extension check (no network)
    if is_image_url(url):
        ext = url.split(".")[-1].split("?")[0].lower()  # Handle query params
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "bmp": "image/bmp",
            "heic": "image/heic",
            "heif": "image/heif",
        }
        return ("image", mime_map.get(ext, "image/jpeg"))

    if is_video_url(url):
        return ("video", "video/mp4")

    if is_audio_url(url):
        return ("audio", "audio/mpeg")

    # Fall back to HEAD request for Content-Type
    try:
        import httpx

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
    except Exception:
        # If HEAD fails, assume text/html
        return ("unknown", "application/octet-stream")


__all__ = [
    "MediaType",
    "is_image_url",
    "is_video_url",
    "is_audio_url",
    "is_youtube_url",
    "detect_media_type_from_url",
]
