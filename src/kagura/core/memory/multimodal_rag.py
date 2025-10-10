"""Multimodal RAG with directory scanning and ChromaDB integration.

Extends MemoryRAG to support automatic indexing of multimodal content
(images, audio, video, PDFs) from directories.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from kagura.core.memory.rag import MemoryRAG
from kagura.loaders.cache import LoaderCache
from kagura.loaders.directory import DirectoryScanner
from kagura.loaders.file_types import FileType

# Try to import GeminiLoader
try:
    from kagura.loaders.gemini import GEMINI_AVAILABLE, GeminiLoader

    MULTIMODAL_AVAILABLE = GEMINI_AVAILABLE
except ImportError:
    MULTIMODAL_AVAILABLE = False
    if not TYPE_CHECKING:
        GeminiLoader = None  # type: ignore

logger = logging.getLogger(__name__)


class MultimodalRAG(MemoryRAG):
    """Multimodal RAG with directory scanning.

    Extends MemoryRAG to automatically scan directories, process multimodal
    content (images, audio, video, PDFs) using Gemini, and index them in
    ChromaDB for semantic search.

    Example:
        >>> # Initialize with directory
        >>> rag = MultimodalRAG(
        ...     directory=Path("./project"),
        ...     collection_name="project_docs"
        ... )
        >>> # Build index from directory content
        >>> await rag.build_index()
        >>> # Query across all content types
        >>> results = rag.query("How does authentication work?")
        >>> print(results[0]["content"])
    """

    def __init__(
        self,
        directory: Path,
        collection_name: str = "multimodal_memory",
        persist_dir: Optional[Path] = None,
        gemini_api_key: Optional[str] = None,
        enable_cache: bool = True,
        cache_size_mb: int = 100,
        respect_gitignore: bool = True,
    ):
        """Initialize MultimodalRAG.

        Args:
            directory: Directory to scan for content
            collection_name: ChromaDB collection name
            persist_dir: Directory for ChromaDB storage
            gemini_api_key: Gemini API key (optional, uses env var if None)
            enable_cache: Enable file content caching
            cache_size_mb: Cache size limit in megabytes
            respect_gitignore: Respect .gitignore/.kaguraignore patterns

        Raises:
            ImportError: If Gemini or ChromaDB not available
            FileNotFoundError: If directory doesn't exist
        """
        # Initialize parent RAG
        super().__init__(collection_name=collection_name, persist_dir=persist_dir)

        if not MULTIMODAL_AVAILABLE:
            raise ImportError(
                "Multimodal support requires google-generativeai. "
                "Install with: pip install kagura-ai[multimodal]"
            )

        self.directory = Path(directory)
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory}")

        # Initialize Gemini loader
        self.gemini = GeminiLoader(api_key=gemini_api_key)

        # Initialize directory scanner
        self.scanner = DirectoryScanner(
            directory=self.directory,
            gemini=self.gemini,
            respect_gitignore=respect_gitignore,
        )

        # Initialize cache
        self.cache: Optional[LoaderCache] = None
        if enable_cache:
            self.cache = LoaderCache(max_size_mb=cache_size_mb)

        self._indexed_files: set[Path] = set()

    async def build_index(
        self,
        max_concurrent: int = 3,
        language: str = "en",
        force_rebuild: bool = False,
    ) -> dict[str, Any]:
        """Build vector index from directory content.

        Scans directory, processes all supported files (text + multimodal),
        and adds them to ChromaDB for semantic search.

        Args:
            max_concurrent: Maximum concurrent file processing
            language: Language for Gemini responses (en/ja)
            force_rebuild: Force rebuild even if files already indexed

        Returns:
            Statistics dictionary with:
            - total_files: Total files processed
            - text_files: Number of text files
            - multimodal_files: Number of multimodal files
            - failed_files: Number of failed files
            - cache_hit_rate: Cache hit rate (if enabled)

        Example:
            >>> stats = await rag.build_index(max_concurrent=5)
            >>> print(f"Indexed {stats['total_files']} files")
        """
        logger.info(f"Building index from {self.directory}")

        # Clear existing index if force rebuild
        if force_rebuild:
            logger.info("Force rebuild: clearing existing index")
            self.delete_all()
            self._indexed_files.clear()

        # Scan and load all files
        contents = await self.scanner.load_all(
            max_concurrent=max_concurrent, language=language
        )

        # Statistics
        stats = {
            "total_files": 0,
            "text_files": 0,
            "multimodal_files": 0,
            "failed_files": 0,
            "cache_hit_rate": 0.0,
        }

        # Index each file
        for content in contents:
            # Skip if already indexed (unless force rebuild)
            if not force_rebuild and content.path in self._indexed_files:
                continue

            try:
                # Create metadata
                metadata = {
                    "file_path": str(content.path),
                    "file_type": content.file_type.value,
                    "file_size": content.size,
                }

                # Store in ChromaDB
                self.store(
                    content=content.content,
                    metadata=metadata,
                )

                # Mark as indexed
                self._indexed_files.add(content.path)

                # Update statistics
                stats["total_files"] += 1
                if content.file_type == FileType.TEXT:
                    stats["text_files"] += 1
                else:
                    stats["multimodal_files"] += 1

                # Cache the content
                if self.cache:
                    self.cache.put(content.path, content)

            except Exception as e:
                logger.error(f"Failed to index {content.path}: {e}")
                stats["failed_files"] += 1

        # Add cache statistics
        if self.cache:
            stats["cache_hit_rate"] = self.cache.stats().hit_rate

        logger.info(
            f"Index built: {stats['total_files']} files "
            f"({stats['text_files']} text, {stats['multimodal_files']} multimodal)"
        )

        return stats

    async def incremental_update(
        self, max_concurrent: int = 3, language: str = "en"
    ) -> dict[str, Any]:
        """Incrementally update index with new/modified files.

        Only processes files that haven't been indexed or have been modified
        since last indexing.

        Args:
            max_concurrent: Maximum concurrent file processing
            language: Language for Gemini responses

        Returns:
            Statistics dictionary (same as build_index)

        Example:
            >>> stats = await rag.incremental_update()
            >>> print(f"Updated {stats['total_files']} files")
        """
        logger.info("Performing incremental update")

        # Scan directory
        file_infos = await self.scanner.scan()

        # Find new/modified files
        files_to_process = []
        for file_info in file_infos:
            # Skip if already indexed and not modified
            if file_info.path in self._indexed_files:
                # Check cache validity (will detect modifications)
                if self.cache and self.cache.get(file_info.path):
                    continue  # File cached and not modified
            files_to_process.append(file_info.path)

        if not files_to_process:
            logger.info("No files to update")
            return {
                "total_files": 0,
                "text_files": 0,
                "multimodal_files": 0,
                "failed_files": 0,
            }

        # Load only new/modified files
        logger.info(f"Processing {len(files_to_process)} new/modified files")
        # TODO: Implement selective loading in DirectoryScanner
        # For now, rebuild entire index
        return await self.build_index(
            max_concurrent=max_concurrent, language=language, force_rebuild=False
        )

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        file_type: Optional[FileType] = None,
    ) -> list[dict[str, Any]]:
        """Semantic search across multimodal content.

        Args:
            query_text: Search query
            n_results: Number of results to return
            file_type: Optional file type filter

        Returns:
            List of result dictionaries with content, distance, and metadata

        Example:
            >>> # Search all content
            >>> results = rag.query("authentication flow")
            >>> # Search only images
            >>> results = rag.query("diagram", file_type=FileType.IMAGE)
        """
        # Use parent recall method
        results = self.recall(query=query_text, top_k=n_results)

        # Filter by file type if specified
        if file_type:
            results = [
                r
                for r in results
                if r.get("metadata", {}).get("file_type") == file_type.value
            ]

        return results

    def get_indexed_files(self) -> list[Path]:
        """Get list of indexed file paths.

        Returns:
            List of indexed file paths
        """
        return list(self._indexed_files)

    def clear_cache(self) -> None:
        """Clear file content cache."""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MultimodalRAG(directory={self.directory}, "
            f"indexed_files={len(self._indexed_files)}, "
            f"collection={self.collection.name})"
        )


__all__ = ["MultimodalRAG"]
