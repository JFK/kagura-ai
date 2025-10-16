"""Directory scanner for multimodal content.

Scans directories recursively, detects file types, and loads content
in parallel using asyncio.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kagura.loaders.file_types import FileType, detect_file_type, is_multimodal_file
from kagura.loaders.gemini import GeminiLoader


@dataclass
class FileInfo:
    """Information about a scanned file."""

    path: Path
    file_type: FileType
    size: int
    is_multimodal: bool


@dataclass
class FileContent:
    """Loaded file content with metadata."""

    path: Path
    file_type: FileType
    content: str
    size: int


class DirectoryScanner:
    """Scan directory for multimodal content.

    Recursively scans directories, detects file types, and loads content
    in parallel using GeminiLoader for multimodal files.

    Example:
        >>> scanner = DirectoryScanner(
        ...     directory=Path("./docs"),
        ...     gemini=GeminiLoader()
        ... )
        >>> files = await scanner.scan()
        >>> print(f"Found {len(files)} files")
        >>> contents = await scanner.load_all(max_concurrent=5)
    """

    def __init__(
        self,
        directory: Path,
        gemini: Optional[GeminiLoader] = None,
        respect_gitignore: bool = True,
    ):
        """Initialize directory scanner.

        Args:
            directory: Directory to scan
            gemini: GeminiLoader instance for multimodal files
            respect_gitignore: Whether to respect .gitignore/.kaguraignore
        """
        self.directory = Path(directory)
        self.gemini = gemini
        self.respect_gitignore = respect_gitignore
        self._ignore_patterns: set[str] = set()

        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory}")

        if not self.directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.directory}")

        # Load ignore patterns
        if self.respect_gitignore:
            self._load_ignore_patterns()

    def _load_ignore_patterns(self) -> None:
        """Load patterns from .gitignore and .kaguraignore."""
        ignore_files = [
            self.directory / ".gitignore",
            self.directory / ".kaguraignore",
        ]

        for ignore_file in ignore_files:
            if ignore_file.exists():
                with open(ignore_file) as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith("#"):
                            self._ignore_patterns.add(line)

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored.

        Args:
            path: Path to check

        Returns:
            True if path should be ignored
        """
        if not self.respect_gitignore:
            return False

        # Always ignore hidden files/directories (starting with .)
        if any(part.startswith(".") for part in path.parts):
            return True

        # Check against ignore patterns
        rel_path = path.relative_to(self.directory)
        rel_path_str = str(rel_path)

        for pattern in self._ignore_patterns:
            # Simple pattern matching (not full gitignore spec)
            if pattern.endswith("/"):
                # Directory pattern
                if rel_path_str.startswith(pattern.rstrip("/")):
                    return True
            elif "*" in pattern:
                # Wildcard pattern - simple implementation
                if pattern.replace("*", "") in rel_path_str:
                    return True
            else:
                # Exact match or substring
                if pattern in rel_path_str or rel_path_str.startswith(pattern):
                    return True

        return False

    async def scan(self) -> list[FileInfo]:
        """Scan directory recursively for files.

        Returns:
            List of FileInfo objects for all discovered files

        Example:
            >>> files = await scanner.scan()
            >>> print(f"Found {len(files)} files")
            >>> multimodal = [f for f in files if f.is_multimodal]
            >>> print(f"{len(multimodal)} multimodal files")
        """
        files: list[FileInfo] = []

        for path in self.directory.rglob("*"):
            # Skip directories
            if path.is_dir():
                continue

            # Skip ignored files
            if self._should_ignore(path):
                continue

            # Detect file type
            file_type = detect_file_type(path)

            # Create FileInfo
            file_info = FileInfo(
                path=path,
                file_type=file_type,
                size=path.stat().st_size,
                is_multimodal=is_multimodal_file(path),
            )

            files.append(file_info)

        return files

    async def load_file(
        self, path: Path, prompt: Optional[str] = None, language: str = "en"
    ) -> FileContent:
        """Load single file with appropriate loader.

        Args:
            path: Path to file
            prompt: Optional custom prompt for multimodal files
            language: Language for responses (en/ja)

        Returns:
            FileContent with loaded content

        Raises:
            ValueError: If file type is not supported or gemini is None
                       for multimodal files
        """
        file_type = detect_file_type(path)

        # Handle text files
        if file_type == FileType.TEXT:
            content = path.read_text(encoding="utf-8")
            return FileContent(
                path=path, file_type=file_type, content=content, size=len(content)
            )

        # Handle multimodal files
        if is_multimodal_file(path):
            if self.gemini is None:
                raise ValueError(
                    f"GeminiLoader required for multimodal file: {path}. "
                    "Pass gemini parameter to DirectoryScanner."
                )

            content = await self.gemini.process_file(path, prompt, language)
            return FileContent(
                path=path, file_type=file_type, content=content, size=len(content)
            )

        # Unsupported file type
        raise ValueError(f"Unsupported file type: {file_type} for {path}")

    async def load_all(
        self, max_concurrent: int = 5, language: str = "en"
    ) -> list[FileContent]:
        """Load all files in parallel.

        Args:
            max_concurrent: Maximum number of concurrent file loads
            language: Language for responses (en/ja)

        Returns:
            List of FileContent for all loaded files

        Example:
            >>> contents = await scanner.load_all(max_concurrent=3)
            >>> for content in contents:
            ...     print(f"{content.path}: {len(content.content)} chars")
        """
        # Scan directory
        files = await self.scan()

        # Filter to supported file types (text + multimodal)
        supported_files = [
            f for f in files if f.file_type == FileType.TEXT or f.is_multimodal
        ]

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def load_with_semaphore(file_info: FileInfo) -> FileContent:
            async with semaphore:
                return await self.load_file(file_info.path, language=language)

        # Load all files in parallel
        tasks = [load_with_semaphore(f) for f in supported_files]
        contents = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful loads
        successful_contents = [c for c in contents if isinstance(c, FileContent)]

        return successful_contents


__all__ = ["DirectoryScanner", "FileInfo", "FileContent"]
