"""Tests for chat session tools (file operations, code execution, etc.)"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kagura.chat.session import (
    _execute_python_tool,
    _file_read_tool,
    _file_search_tool,
    _file_write_tool,
    _url_fetch_tool,
    _video_extract_audio_tool,
    _youtube_metadata_tool,
    _youtube_transcript_tool,
)


class TestFileOperations:
    """Test file operation tools"""

    @pytest.mark.asyncio
    async def test_file_read_text(self, tmp_path: Path):
        """Test reading text files"""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!\nLine 2")

        # Read the file
        result = await _file_read_tool(str(test_file))

        assert "Error" not in result
        assert "Hello, World!" in result
        assert "Line 2" in result

    @pytest.mark.asyncio
    async def test_file_read_nonexistent(self):
        """Test reading nonexistent file"""
        result = await _file_read_tool("/nonexistent/file.txt")

        assert "Error" in result
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_file_write(self, tmp_path: Path):
        """Test writing files"""
        test_file = tmp_path / "output.txt"
        content = "Test content\nLine 2"

        # Write the file
        result = await _file_write_tool(str(test_file), content)

        assert "Error" not in result
        assert "Success" in result
        assert test_file.exists()
        assert test_file.read_text() == content

    @pytest.mark.asyncio
    async def test_file_write_with_backup(self, tmp_path: Path):
        """Test writing files creates backup"""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Original content")

        # Write new content
        result = await _file_write_tool(str(test_file), "New content")

        assert "Error" not in result
        assert "Backup created" in result or "Success" in result
        assert test_file.read_text() == "New content"

        # Backup should exist
        backup = tmp_path / "existing.txt.backup"
        assert backup.exists()
        assert backup.read_text() == "Original content"

    @pytest.mark.asyncio
    async def test_file_search(self, tmp_path: Path):
        """Test file search"""
        # Create test files
        (tmp_path / "file1.py").write_text("# Python file 1")
        (tmp_path / "file2.py").write_text("# Python file 2")
        (tmp_path / "file.txt").write_text("Text file")

        # Search for Python files
        result = await _file_search_tool("*.py", str(tmp_path))

        assert "Error" not in result
        assert "file1.py" in result
        assert "file2.py" in result
        assert "file.txt" not in result


class TestCodeExecution:
    """Test code execution tool"""

    @pytest.mark.asyncio
    async def test_execute_simple_code(self):
        """Test executing simple Python code"""
        code = "result = 2 + 2"

        result = await _execute_python_tool(code)

        assert "Error" not in result
        assert "Result: 4" in result

    @pytest.mark.asyncio
    async def test_execute_with_print(self):
        """Test executing code with print"""
        code = "print('Hello from Python')"

        result = await _execute_python_tool(code)

        assert "Error" not in result
        assert "Hello from Python" in result

    @pytest.mark.asyncio
    async def test_execute_invalid_code(self):
        """Test executing invalid Python code"""
        code = "this is not valid python"

        result = await _execute_python_tool(code)

        assert "Error" in result or "SyntaxError" in result


class TestWebTools:
    """Test web and content tools"""

    @pytest.mark.asyncio
    async def test_url_fetch(self):
        """Test URL fetch tool"""
        # Mock WebScraper
        mock_scraper = MagicMock()
        mock_scraper.fetch_text = AsyncMock(return_value="Page content here")

        with patch("kagura.web.WebScraper", return_value=mock_scraper):
            result = await _url_fetch_tool("https://example.com")

            assert "Error" not in result
            assert "Page content" in result


class TestYouTubeTools:
    """Test YouTube tools"""

    @pytest.mark.asyncio
    async def test_youtube_transcript(self):
        """Test YouTube transcript tool"""
        # Mock at the import location (session.py imports from kagura.tools)
        with patch(
            "kagura.tools.get_youtube_transcript",
            new=AsyncMock(return_value="Transcript text here"),
        ):
            result = await _youtube_transcript_tool("https://youtube.com/watch?v=test")

            assert "Error" not in result
            assert "Transcript text" in result

    @pytest.mark.asyncio
    async def test_youtube_metadata(self):
        """Test YouTube metadata tool"""
        # Mock at the import location (session.py imports from kagura.tools)
        metadata = '{"title": "Test Video", "author": "Test Channel"}'
        with patch(
            "kagura.tools.get_youtube_metadata",
            new=AsyncMock(return_value=metadata),
        ):
            result = await _youtube_metadata_tool("https://youtube.com/watch?v=test")

            assert "Error" not in result
            assert "Test Video" in result


class TestVideoProcessing:
    """Test video processing tools"""

    @pytest.mark.asyncio
    async def test_video_extract_audio_ffmpeg_not_found(self, tmp_path: Path):
        """Test video audio extraction when ffmpeg is not available"""
        # Create a dummy video file
        test_video = tmp_path / "test.mp4"
        test_video.write_text("dummy video")

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
            result = await _video_extract_audio_tool(str(test_video))

            assert "Error" in result
            assert "ffmpeg not found" in result
