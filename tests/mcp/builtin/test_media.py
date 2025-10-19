"""Tests for Media display tools."""

import platform
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kagura.mcp.builtin.media import (
    media_open_audio,
    media_open_image,
    media_open_video,
)


class TestMediaOpenImage:
    """Test media_open_image tool."""

    def test_image_file_not_found(self) -> None:
        """Test error when image file does not exist"""
        result = media_open_image("/nonexistent/image.png")

        assert "Error" in result
        assert "not found" in result.lower()

    def test_image_open_success(self, tmp_path: Path) -> None:
        """Test successfully opening an image file"""
        # Create a temporary test file
        test_image = tmp_path / "test.png"
        test_image.write_text("test image content")

        with patch("subprocess.run") as mock_run:
            result = media_open_image(str(test_image))

            # Should succeed
            assert "Successfully opened image" in result
            assert str(test_image) in result

            # Should have called subprocess.run
            assert mock_run.called

    def test_image_open_macos(self, tmp_path: Path, monkeypatch) -> None:
        """Test that macOS uses 'open' command"""
        test_image = tmp_path / "test.png"
        test_image.write_text("test")

        monkeypatch.setattr(platform, "system", lambda: "Darwin")

        with patch("subprocess.run") as mock_run:
            media_open_image(str(test_image))

            # Verify 'open' was called
            args = mock_run.call_args[0][0]
            assert args[0] == "open"
            assert str(test_image) in args

    def test_image_open_linux(self, tmp_path: Path, monkeypatch) -> None:
        """Test that Linux uses 'xdg-open' command"""
        test_image = tmp_path / "test.png"
        test_image.write_text("test")

        monkeypatch.setattr(platform, "system", lambda: "Linux")

        with patch("subprocess.run") as mock_run:
            media_open_image(str(test_image))

            # Verify 'xdg-open' was called
            args = mock_run.call_args[0][0]
            assert args[0] == "xdg-open"


class TestMediaOpenVideo:
    """Test media_open_video tool."""

    def test_video_file_not_found(self) -> None:
        """Test error when video file does not exist"""
        result = media_open_video("/nonexistent/video.mp4")

        assert "Error" in result
        assert "not found" in result.lower()

    def test_video_open_success(self, tmp_path: Path) -> None:
        """Test successfully opening a video file"""
        test_video = tmp_path / "test.mp4"
        test_video.write_text("test video content")

        with patch("subprocess.run") as mock_run:
            result = media_open_video(str(test_video))

            assert "Successfully opened video" in result
            assert str(test_video) in result
            assert mock_run.called


class TestMediaOpenAudio:
    """Test media_open_audio tool."""

    def test_audio_file_not_found(self) -> None:
        """Test error when audio file does not exist"""
        result = media_open_audio("/nonexistent/audio.mp3")

        assert "Error" in result
        assert "not found" in result.lower()

    def test_audio_open_success(self, tmp_path: Path) -> None:
        """Test successfully opening an audio file"""
        test_audio = tmp_path / "test.mp3"
        test_audio.write_text("test audio content")

        with patch("subprocess.run") as mock_run:
            result = media_open_audio(str(test_audio))

            assert "Successfully opened audio" in result
            assert str(test_audio) in result
            assert mock_run.called


class TestCrossPlatform:
    """Test cross-platform compatibility."""

    def test_windows_uses_startfile(self, tmp_path: Path, monkeypatch) -> None:
        """Test that Windows uses os.startfile"""
        test_file = tmp_path / "test.png"
        test_file.write_text("test")

        monkeypatch.setattr(platform, "system", lambda: "Windows")

        # Mock os.startfile
        mock_startfile = MagicMock()
        with patch("os.startfile", mock_startfile, create=True):
            media_open_image(str(test_file))

            # Verify os.startfile was called
            assert mock_startfile.called
            assert str(test_file) in str(mock_startfile.call_args)
