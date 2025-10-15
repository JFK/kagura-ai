"""
Tests for YouTube tools
"""

import pytest

from kagura.tools.youtube import extract_video_id, get_youtube_metadata, get_youtube_transcript


class TestExtractVideoId:
    """Test suite for extract_video_id"""

    def test_extract_from_watch_url(self) -> None:
        """Test extracting video ID from standard watch URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_from_short_url(self) -> None:
        """Test extracting video ID from short youtu.be URL"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_from_embed_url(self) -> None:
        """Test extracting video ID from embed URL"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_with_parameters(self) -> None:
        """Test extracting video ID from URL with parameters"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_invalid_url(self) -> None:
        """Test that invalid URL raises ValueError"""
        with pytest.raises(ValueError, match="Could not extract video ID"):
            extract_video_id("https://example.com/video")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_youtube_transcript_missing_library() -> None:
    """Test transcript tool when youtube-transcript-api is not installed"""
    # This test verifies graceful error handling
    # In CI without the library, should return error message
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = await get_youtube_transcript(url)

    # Should either succeed or return error message
    assert isinstance(result, str)
    # If library is missing, should have error message
    if "Error" in result:
        assert "youtube-transcript-api" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_youtube_metadata_missing_library() -> None:
    """Test metadata tool when yt-dlp is not installed"""
    # This test verifies graceful error handling
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = await get_youtube_metadata(url)

    # Should return JSON string
    assert isinstance(result, str)
    assert "{" in result  # JSON format

    # If library is missing, should have error message
    if "error" in result.lower():
        assert "yt-dlp" in result


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    True,
    reason="Requires youtube-transcript-api and network access",
)
async def test_get_youtube_transcript_real() -> None:
    """Test getting real YouTube transcript"""
    # Real test (skipped by default, requires network)
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = await get_youtube_transcript(url, lang="en")

    assert isinstance(result, str)
    assert len(result) > 0
    assert "Error" not in result


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    True,
    reason="Requires yt-dlp and network access",
)
async def test_get_youtube_metadata_real() -> None:
    """Test getting real YouTube metadata"""
    # Real test (skipped by default, requires network)
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = await get_youtube_metadata(url)

    assert isinstance(result, str)
    assert "title" in result.lower()
    assert "error" not in result.lower()
