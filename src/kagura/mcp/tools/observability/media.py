"""
Media display tools for Kagura AI (MCP Built-in)

Cross-platform tools to open images, videos, and audio files
using OS-specific default applications.
"""

import platform
import subprocess
from pathlib import Path

from kagura import tool


def _open_with_os_app(file_path: str) -> None:
    """Open file with OS default application.

    Args:
        file_path: Path to the file to open

    Raises:
        FileNotFoundError: If file does not exist
        subprocess.CalledProcessError: If command fails
    """
    # Verify file exists
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get OS and execute appropriate command
    system = platform.system()

    if system == "Darwin":  # macOS
        subprocess.run(["open", str(path)], check=True)
    elif system == "Windows":
        # Use os.startfile on Windows (more reliable than subprocess)
        import os

        os.startfile(str(path))  # type: ignore[attr-defined]
    else:  # Linux and others
        subprocess.run(["xdg-open", str(path)], check=True)


@tool
def media_open_image(path: str) -> str:
    """Open an image file with the OS default application.

    Supports cross-platform operation (Windows/macOS/Linux).

    Args:
        path: Path to the image file (absolute or relative)

    Returns:
        Success message or error description

    Example:
        >>> result = media_open_image("/path/to/image.png")
        >>> print(result)
        "Successfully opened image: /path/to/image.png"
    """
    try:
        _open_with_os_app(path)
        return f"Successfully opened image: {path}"
    except FileNotFoundError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Failed to open image: {str(e)}"


@tool
def media_open_video(path: str) -> str:
    """Open a video file with the OS default application.

    Supports cross-platform operation (Windows/macOS/Linux).

    Args:
        path: Path to the video file (absolute or relative)

    Returns:
        Success message or error description

    Example:
        >>> result = media_open_video("/path/to/video.mp4")
        >>> print(result)
        "Successfully opened video: /path/to/video.mp4"
    """
    try:
        _open_with_os_app(path)
        return f"Successfully opened video: {path}"
    except FileNotFoundError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Failed to open video: {str(e)}"


@tool
def media_open_audio(path: str) -> str:
    """Open an audio file with the OS default application.

    Attempts console playback if possible, otherwise falls back
    to OS default application.

    Supports cross-platform operation (Windows/macOS/Linux).

    Args:
        path: Path to the audio file (absolute or relative)

    Returns:
        Success message or error description

    Example:
        >>> result = media_open_audio("/path/to/audio.mp3")
        >>> print(result)
        "Successfully opened audio: /path/to/audio.mp3"
    """
    try:
        # For now, use OS default app
        # TODO (v3.1): Implement console playback (pydub, playsound, etc.) as optional
        # This would require optional dependencies: pip install kagura-ai[audio]
        # Implementation: Use pydub + simpleaudio for cross-platform audio playback
        _open_with_os_app(path)
        return f"Successfully opened audio: {path}"
    except FileNotFoundError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Failed to open audio: {str(e)}"
