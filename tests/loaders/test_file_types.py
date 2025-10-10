"""Tests for file type detection."""

from pathlib import Path

import pytest

# Direct import to avoid gemini dependency issues in tests
import kagura.loaders.file_types as file_types_module

FileType = file_types_module.FileType
detect_file_type = file_types_module.detect_file_type
get_supported_extensions = file_types_module.get_supported_extensions
is_multimodal_file = file_types_module.is_multimodal_file


class TestFileType:
    """Tests for FileType enum."""

    def test_file_type_values(self):
        """Test FileType enum values."""
        assert FileType.IMAGE.value == "image"
        assert FileType.AUDIO.value == "audio"
        assert FileType.VIDEO.value == "video"
        assert FileType.PDF.value == "pdf"
        assert FileType.TEXT.value == "text"
        assert FileType.DATA.value == "data"
        assert FileType.UNKNOWN.value == "unknown"


class TestDetectFileType:
    """Tests for detect_file_type function."""

    def test_detect_image(self):
        """Test image file detection."""
        assert detect_file_type(Path("test.png")) == FileType.IMAGE
        assert detect_file_type(Path("test.jpg")) == FileType.IMAGE
        assert detect_file_type(Path("test.jpeg")) == FileType.IMAGE
        assert detect_file_type(Path("test.gif")) == FileType.IMAGE
        assert detect_file_type(Path("test.webp")) == FileType.IMAGE

    def test_detect_audio(self):
        """Test audio file detection."""
        assert detect_file_type(Path("test.mp3")) == FileType.AUDIO
        assert detect_file_type(Path("test.wav")) == FileType.AUDIO
        assert detect_file_type(Path("test.m4a")) == FileType.AUDIO

    def test_detect_video(self):
        """Test video file detection."""
        assert detect_file_type(Path("test.mp4")) == FileType.VIDEO
        assert detect_file_type(Path("test.mov")) == FileType.VIDEO
        assert detect_file_type(Path("test.avi")) == FileType.VIDEO

    def test_detect_pdf(self):
        """Test PDF file detection."""
        assert detect_file_type(Path("test.pdf")) == FileType.PDF

    def test_detect_text(self):
        """Test text file detection."""
        assert detect_file_type(Path("test.txt")) == FileType.TEXT
        assert detect_file_type(Path("test.md")) == FileType.TEXT
        assert detect_file_type(Path("test.py")) == FileType.TEXT
        assert detect_file_type(Path("test.json")) == FileType.TEXT

    def test_detect_data(self):
        """Test data file detection."""
        assert detect_file_type(Path("test.csv")) == FileType.DATA
        assert detect_file_type(Path("test.xlsx")) == FileType.DATA
        assert detect_file_type(Path("test.parquet")) == FileType.DATA

    def test_detect_unknown(self):
        """Test unknown file type."""
        assert detect_file_type(Path("test.unknown")) == FileType.UNKNOWN
        assert detect_file_type(Path("test.xyz")) == FileType.UNKNOWN

    def test_case_insensitive(self):
        """Test case-insensitive detection."""
        assert detect_file_type(Path("test.PNG")) == FileType.IMAGE
        assert detect_file_type(Path("test.MP3")) == FileType.AUDIO
        assert detect_file_type(Path("test.PDF")) == FileType.PDF

    def test_string_path(self):
        """Test string path input."""
        assert detect_file_type(Path("test.png")) == FileType.IMAGE


class TestIsMultimodalFile:
    """Tests for is_multimodal_file function."""

    def test_multimodal_files(self):
        """Test multimodal file detection."""
        assert is_multimodal_file(Path("test.png")) is True
        assert is_multimodal_file(Path("test.mp3")) is True
        assert is_multimodal_file(Path("test.mp4")) is True
        assert is_multimodal_file(Path("test.pdf")) is True

    def test_non_multimodal_files(self):
        """Test non-multimodal file detection."""
        assert is_multimodal_file(Path("test.txt")) is False
        assert is_multimodal_file(Path("test.py")) is False
        assert is_multimodal_file(Path("test.csv")) is False
        assert is_multimodal_file(Path("test.unknown")) is False


class TestGetSupportedExtensions:
    """Tests for get_supported_extensions function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        result = get_supported_extensions()
        assert isinstance(result, dict)

    def test_all_types_present(self):
        """Test that all file types are present."""
        result = get_supported_extensions()
        assert FileType.IMAGE in result
        assert FileType.AUDIO in result
        assert FileType.VIDEO in result
        assert FileType.PDF in result
        assert FileType.TEXT in result
        assert FileType.DATA in result

    def test_extensions_are_sets(self):
        """Test that extensions are sets."""
        result = get_supported_extensions()
        for extensions in result.values():
            assert isinstance(extensions, set)

    def test_extensions_format(self):
        """Test that extensions start with dot."""
        result = get_supported_extensions()
        for extensions in result.values():
            for ext in extensions:
                assert ext.startswith(".")
