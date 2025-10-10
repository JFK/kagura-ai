"""Caching system for loaded file content.

Provides in-memory caching with TTL and size limits to optimize
repeated file loading operations.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kagura.loaders.directory import FileContent
from kagura.loaders.file_types import FileType


@dataclass
class CacheEntry:
    """Cache entry with metadata.

    Attributes:
        content: File content string
        file_type: Type of file
        size: Content size in bytes
        cached_at: Unix timestamp when cached
        mtime: File modification time at caching
    """

    content: str
    file_type: FileType
    size: int
    cached_at: float
    mtime: float


@dataclass
class CacheStats:
    """Cache statistics for monitoring performance.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        evictions: Number of evicted entries
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            Hit rate as float between 0.0 and 1.0
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def total_requests(self) -> int:
        """Total number of cache requests.

        Returns:
            Sum of hits and misses
        """
        return self.hits + self.misses


class LoaderCache:
    """In-memory cache for file content with TTL and size limits.

    Provides automatic cache invalidation based on file modification time,
    TTL expiration, and LRU eviction when size limits are exceeded.

    Example:
        >>> cache = LoaderCache(max_size_mb=50, ttl_seconds=3600)
        >>> content = FileContent(path=Path("test.txt"), ...)
        >>> cache.put(Path("test.txt"), content)
        >>> cached = cache.get(Path("test.txt"))
        >>> print(f"Hit rate: {cache.stats().hit_rate:.2%}")
    """

    def __init__(
        self,
        max_size_mb: int = 100,
        ttl_seconds: Optional[float] = None,
    ):
        """Initialize cache with size and TTL limits.

        Args:
            max_size_mb: Maximum cache size in megabytes (default: 100)
            ttl_seconds: Time to live in seconds (None = no expiration)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        self._cache: dict[Path, CacheEntry] = {}
        self._stats = CacheStats()

    def get(self, path: Path) -> Optional[FileContent]:
        """Get cached content if valid.

        Args:
            path: Path to file

        Returns:
            FileContent if cached and valid, None otherwise
        """
        # Check if in cache
        if path not in self._cache:
            self._stats.misses += 1
            return None

        entry = self._cache[path]

        # Validate entry
        if not self._is_valid(entry, path):
            # Remove invalid entry
            del self._cache[path]
            self._stats.misses += 1
            return None

        # Cache hit
        self._stats.hits += 1
        return FileContent(
            path=path,
            file_type=entry.file_type,
            content=entry.content,
            size=entry.size,
        )

    def put(self, path: Path, content: FileContent) -> None:
        """Store content in cache.

        Automatically evicts oldest entries if size limit is exceeded.

        Args:
            path: Path to file
            content: FileContent to cache
        """
        # Get file modification time
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            # File doesn't exist, don't cache
            return

        # Create cache entry
        entry = CacheEntry(
            content=content.content,
            file_type=content.file_type,
            size=content.size,
            cached_at=time.time(),
            mtime=mtime,
        )

        # Evict if needed
        self._evict_if_needed(entry.size)

        # Store in cache
        self._cache[path] = entry

    def invalidate(self, path: Path) -> bool:
        """Remove entry from cache.

        Args:
            path: Path to file

        Returns:
            True if entry was removed, False if not in cache
        """
        if path in self._cache:
            del self._cache[path]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats object with current statistics
        """
        return self._stats

    def reset_stats(self) -> None:
        """Reset cache statistics to zero."""
        self._stats = CacheStats()

    @property
    def size_bytes(self) -> int:
        """Current cache size in bytes.

        Returns:
            Total size of cached content in bytes
        """
        return sum(entry.size for entry in self._cache.values())

    @property
    def size_mb(self) -> float:
        """Current cache size in megabytes.

        Returns:
            Total size of cached content in MB
        """
        return self.size_bytes / (1024 * 1024)

    @property
    def entry_count(self) -> int:
        """Number of cached entries.

        Returns:
            Count of entries in cache
        """
        return len(self._cache)

    def _is_valid(self, entry: CacheEntry, path: Path) -> bool:
        """Check if cache entry is still valid.

        Args:
            entry: Cache entry to validate
            path: Path to file

        Returns:
            True if entry is valid, False otherwise
        """
        # Check TTL
        if self.ttl_seconds is not None:
            age = time.time() - entry.cached_at
            if age > self.ttl_seconds:
                return False

        # Check file modification time
        try:
            current_mtime = path.stat().st_mtime
            if current_mtime > entry.mtime:
                return False
        except FileNotFoundError:
            # File no longer exists
            return False

        return True

    def _evict_if_needed(self, new_size: int) -> None:
        """Evict oldest entries if size limit would be exceeded.

        Uses LRU (Least Recently Used) strategy based on cached_at time.

        Args:
            new_size: Size of new entry to be added
        """
        current_size = self.size_bytes

        # Check if we need to evict
        if current_size + new_size <= self.max_size_bytes:
            return

        # Sort by cached_at (oldest first)
        entries = sorted(self._cache.items(), key=lambda x: x[1].cached_at)

        # Evict until we have space
        for path, entry in entries:
            if current_size + new_size <= self.max_size_bytes:
                break

            del self._cache[path]
            current_size -= entry.size
            self._stats.evictions += 1


__all__ = ["LoaderCache", "CacheEntry", "CacheStats"]
