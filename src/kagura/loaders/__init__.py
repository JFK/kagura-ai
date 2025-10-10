"""Loaders for multimodal content.

This module provides loaders for various file types including:
- Images (PNG, JPG, JPEG, GIF, WEBP)
- Audio (MP3, WAV, M4A)
- Video (MP4, MOV, AVI)
- PDF documents
"""

from kagura.loaders.file_types import FileType, detect_file_type

__all__ = [
    "FileType",
    "detect_file_type",
]

# Conditional import for GeminiLoader (requires google-generativeai)
try:
    from kagura.loaders.gemini import GeminiLoader

    __all__.append("GeminiLoader")
except ImportError:
    pass
