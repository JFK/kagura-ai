"""File type detection for multimodal content."""

from enum import Enum
from pathlib import Path


class FileType(Enum):
    """Supported file types for multimodal processing."""

    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"
    TEXT = "text"
    DATA = "data"
    UNKNOWN = "unknown"


# File extension mappings
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}
PDF_EXTENSIONS = {".pdf"}
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".html",
    ".css",
    ".scss",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".vim",
    ".lua",
    ".rs",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".sql",
    ".r",
    ".R",
}
DATA_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet", ".json", ".jsonl"}


def detect_file_type(path: Path) -> FileType:
    """Detect file type from file extension.

    Args:
        path: Path to the file

    Returns:
        FileType enum value

    Examples:
        >>> detect_file_type(Path("image.png"))
        FileType.IMAGE
        >>> detect_file_type(Path("audio.mp3"))
        FileType.AUDIO
        >>> detect_file_type(Path("document.pdf"))
        FileType.PDF
    """
    if not isinstance(path, Path):
        path = Path(path)

    ext = path.suffix.lower()

    if ext in IMAGE_EXTENSIONS:
        return FileType.IMAGE
    elif ext in AUDIO_EXTENSIONS:
        return FileType.AUDIO
    elif ext in VIDEO_EXTENSIONS:
        return FileType.VIDEO
    elif ext in PDF_EXTENSIONS:
        return FileType.PDF
    elif ext in TEXT_EXTENSIONS:
        return FileType.TEXT
    elif ext in DATA_EXTENSIONS:
        return FileType.DATA
    else:
        return FileType.UNKNOWN


def is_multimodal_file(path: Path) -> bool:
    """Check if file requires multimodal processing (Gemini API).

    Args:
        path: Path to the file

    Returns:
        True if file is image, audio, video, or PDF
    """
    file_type = detect_file_type(path)
    return file_type in {FileType.IMAGE, FileType.AUDIO, FileType.VIDEO, FileType.PDF}


def get_supported_extensions() -> dict[FileType, set[str]]:
    """Get all supported file extensions grouped by type.

    Returns:
        Dictionary mapping FileType to set of extensions
    """
    return {
        FileType.IMAGE: IMAGE_EXTENSIONS,
        FileType.AUDIO: AUDIO_EXTENSIONS,
        FileType.VIDEO: VIDEO_EXTENSIONS,
        FileType.PDF: PDF_EXTENSIONS,
        FileType.TEXT: TEXT_EXTENSIONS,
        FileType.DATA: DATA_EXTENSIONS,
    }
