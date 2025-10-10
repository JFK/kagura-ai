"""Tests for DirectoryScanner."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from kagura.loaders.directory import DirectoryScanner, FileContent
from kagura.loaders.file_types import FileType


@pytest.fixture
def temp_dir(tmp_path: Path):
    """Create temporary directory with test files."""
    # Create directory structure
    (tmp_path / "docs").mkdir()
    (tmp_path / "images").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "ignored").mkdir()

    # Create text files
    (tmp_path / "README.md").write_text("# README")
    (tmp_path / "docs" / "guide.txt").write_text("Guide content")
    (tmp_path / "code.py").write_text("print('hello')")

    # Create image files
    (tmp_path / "images" / "photo.png").write_bytes(b"fake png data")
    (tmp_path / "images" / "icon.jpg").write_bytes(b"fake jpg data")

    # Create hidden and ignored files
    (tmp_path / ".hidden" / "secret.txt").write_text("secret")
    (tmp_path / "ignored" / "temp.txt").write_text("temp")

    # Create .gitignore
    (tmp_path / ".gitignore").write_text("ignored/\n*.log\n")

    return tmp_path


@pytest.fixture
def mock_gemini():
    """Create mock GeminiLoader."""
    gemini = Mock()
    gemini.process_file = AsyncMock(return_value="Mocked Gemini response")
    return gemini


class TestDirectoryScannerInit:
    """Tests for DirectoryScanner initialization."""

    def test_init_basic(self, temp_dir: Path):
        """Test basic initialization."""
        scanner = DirectoryScanner(directory=temp_dir)
        assert scanner.directory == temp_dir
        assert scanner.gemini is None
        assert scanner.respect_gitignore is True

    def test_init_with_gemini(self, temp_dir: Path, mock_gemini):
        """Test initialization with GeminiLoader."""
        scanner = DirectoryScanner(directory=temp_dir, gemini=mock_gemini)
        assert scanner.gemini is mock_gemini

    def test_init_without_gitignore(self, temp_dir: Path):
        """Test initialization without gitignore support."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=False)
        assert scanner.respect_gitignore is False
        assert len(scanner._ignore_patterns) == 0

    def test_init_nonexistent_directory(self, tmp_path: Path):
        """Test initialization with nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            DirectoryScanner(directory=nonexistent)

    def test_init_file_path(self, temp_dir: Path):
        """Test initialization with file path instead of directory."""
        file_path = temp_dir / "README.md"
        with pytest.raises(NotADirectoryError, match="Not a directory"):
            DirectoryScanner(directory=file_path)


class TestDirectoryScannerIgnorePatterns:
    """Tests for ignore pattern handling."""

    def test_load_gitignore_patterns(self, temp_dir: Path):
        """Test loading patterns from .gitignore."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)
        assert "ignored/" in scanner._ignore_patterns
        assert "*.log" in scanner._ignore_patterns

    def test_load_kaguraignore_patterns(self, temp_dir: Path):
        """Test loading patterns from .kaguraignore."""
        (temp_dir / ".kaguraignore").write_text("cache/\n*.tmp\n")
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)
        assert "cache/" in scanner._ignore_patterns
        assert "*.tmp" in scanner._ignore_patterns

    def test_should_ignore_hidden_files(self, temp_dir: Path):
        """Test that hidden files are ignored."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)
        hidden_file = temp_dir / ".hidden" / "secret.txt"
        assert scanner._should_ignore(hidden_file) is True

    def test_should_ignore_directory_pattern(self, temp_dir: Path):
        """Test directory pattern matching."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)
        ignored_file = temp_dir / "ignored" / "temp.txt"
        assert scanner._should_ignore(ignored_file) is True

    def test_should_ignore_wildcard_pattern(self, temp_dir: Path):
        """Test wildcard pattern matching."""
        (temp_dir / "debug.log").write_text("log data")
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)
        log_file = temp_dir / "debug.log"
        assert scanner._should_ignore(log_file) is True

    def test_should_not_ignore_normal_files(self, temp_dir: Path):
        """Test that normal files are not ignored."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)
        normal_file = temp_dir / "README.md"
        assert scanner._should_ignore(normal_file) is False


class TestDirectoryScannerScan:
    """Tests for directory scanning."""

    @pytest.mark.asyncio
    async def test_scan_basic(self, temp_dir: Path):
        """Test basic directory scanning."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=False)
        files = await scanner.scan()

        # Should find all files including hidden
        assert len(files) > 0
        paths = [f.path.name for f in files]
        assert "README.md" in paths
        assert "guide.txt" in paths

    @pytest.mark.asyncio
    async def test_scan_with_gitignore(self, temp_dir: Path):
        """Test scanning with gitignore patterns."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)
        files = await scanner.scan()

        # Hidden and ignored files should not be included
        paths = [f.path.name for f in files]
        assert "secret.txt" not in paths  # hidden
        assert "temp.txt" not in paths  # ignored

        # Normal files should be included
        assert "README.md" in paths
        assert "guide.txt" in paths

    @pytest.mark.asyncio
    async def test_scan_detects_file_types(self, temp_dir: Path):
        """Test that file types are correctly detected."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=False)
        files = await scanner.scan()

        # Check file types
        file_dict = {f.path.name: f for f in files}

        assert file_dict["README.md"].file_type == FileType.TEXT
        assert file_dict["code.py"].file_type == FileType.TEXT
        assert file_dict["photo.png"].file_type == FileType.IMAGE
        assert file_dict["icon.jpg"].file_type == FileType.IMAGE

    @pytest.mark.asyncio
    async def test_scan_marks_multimodal(self, temp_dir: Path):
        """Test that multimodal files are marked correctly."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=False)
        files = await scanner.scan()

        file_dict = {f.path.name: f for f in files}

        # Images are multimodal
        assert file_dict["photo.png"].is_multimodal is True
        assert file_dict["icon.jpg"].is_multimodal is True

        # Text files are not multimodal
        assert file_dict["README.md"].is_multimodal is False
        assert file_dict["code.py"].is_multimodal is False


class TestDirectoryScannerLoadFile:
    """Tests for loading individual files."""

    @pytest.mark.asyncio
    async def test_load_text_file(self, temp_dir: Path):
        """Test loading text file."""
        scanner = DirectoryScanner(directory=temp_dir)
        file_path = temp_dir / "README.md"

        content = await scanner.load_file(file_path)

        assert isinstance(content, FileContent)
        assert content.path == file_path
        assert content.file_type == FileType.TEXT
        assert content.content == "# README"
        assert content.size == len("# README")

    @pytest.mark.asyncio
    async def test_load_multimodal_without_gemini(self, temp_dir: Path):
        """Test loading multimodal file without GeminiLoader raises error."""
        scanner = DirectoryScanner(directory=temp_dir)
        image_path = temp_dir / "images" / "photo.png"

        with pytest.raises(ValueError, match="GeminiLoader required"):
            await scanner.load_file(image_path)

    @pytest.mark.asyncio
    async def test_load_multimodal_with_gemini(
        self, temp_dir: Path, mock_gemini
    ):
        """Test loading multimodal file with GeminiLoader."""
        scanner = DirectoryScanner(directory=temp_dir, gemini=mock_gemini)
        image_path = temp_dir / "images" / "photo.png"

        content = await scanner.load_file(image_path)

        assert isinstance(content, FileContent)
        assert content.path == image_path
        assert content.file_type == FileType.IMAGE
        assert content.content == "Mocked Gemini response"

        # Verify gemini was called
        mock_gemini.process_file.assert_called_once_with(
            image_path, None, "en"
        )

    @pytest.mark.asyncio
    async def test_load_file_with_language(
        self, temp_dir: Path, mock_gemini
    ):
        """Test loading file with custom language."""
        scanner = DirectoryScanner(directory=temp_dir, gemini=mock_gemini)
        image_path = temp_dir / "images" / "photo.png"

        await scanner.load_file(image_path, language="ja")

        # Verify language was passed to gemini
        mock_gemini.process_file.assert_called_once_with(
            image_path, None, "ja"
        )


class TestDirectoryScannerLoadAll:
    """Tests for parallel file loading."""

    @pytest.mark.asyncio
    async def test_load_all_text_files(self, temp_dir: Path):
        """Test loading all text files."""
        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)
        contents = await scanner.load_all()

        # Should load all text files
        assert len(contents) > 0
        paths = [c.path.name for c in contents]
        assert "README.md" in paths
        assert "guide.txt" in paths
        assert "code.py" in paths

    @pytest.mark.asyncio
    async def test_load_all_with_gemini(self, temp_dir: Path, mock_gemini):
        """Test loading all files including multimodal."""
        scanner = DirectoryScanner(
            directory=temp_dir, gemini=mock_gemini, respect_gitignore=True
        )
        contents = await scanner.load_all()

        # Should load both text and multimodal files
        paths = [c.path.name for c in contents]
        assert "README.md" in paths  # text
        assert "photo.png" in paths  # multimodal

        # Gemini should be called for multimodal files
        assert mock_gemini.process_file.call_count >= 2  # 2 images

    @pytest.mark.asyncio
    async def test_load_all_concurrency_limit(
        self, temp_dir: Path, mock_gemini
    ):
        """Test that concurrency limit is respected."""
        scanner = DirectoryScanner(
            directory=temp_dir, gemini=mock_gemini, respect_gitignore=True
        )

        # Track concurrent calls
        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        original_process_file = mock_gemini.process_file

        async def tracked_process_file(*args, **kwargs):
            nonlocal max_concurrent, current_concurrent
            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            await asyncio.sleep(0.01)  # Simulate work
            async with lock:
                current_concurrent -= 1
            return await original_process_file(*args, **kwargs)

        mock_gemini.process_file = tracked_process_file

        await scanner.load_all(max_concurrent=2)

        # Should not exceed limit
        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_load_all_handles_exceptions(self, temp_dir: Path):
        """Test that load_all handles exceptions gracefully."""
        # Create a file that will fail to load
        bad_file = temp_dir / "bad.txt"
        bad_file.write_text("content")

        scanner = DirectoryScanner(directory=temp_dir, respect_gitignore=True)

        # Mock load_file to raise exception for bad.txt
        original_load_file = scanner.load_file

        async def load_file_with_error(path, *args, **kwargs):
            if path.name == "bad.txt":
                raise ValueError("Simulated error")
            return await original_load_file(path, *args, **kwargs)

        scanner.load_file = load_file_with_error  # type: ignore

        # Should not raise, but return successful loads only
        contents = await scanner.load_all()

        # Should have some successful loads
        assert len(contents) > 0
        # bad.txt should not be in results
        paths = [c.path.name for c in contents]
        assert "bad.txt" not in paths
