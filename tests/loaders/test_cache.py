"""Tests for LoaderCache."""

import time
from pathlib import Path

import pytest

from kagura.loaders.cache import CacheEntry, CacheStats, LoaderCache
from kagura.loaders.directory import FileContent
from kagura.loaders.file_types import FileType


@pytest.fixture
def temp_files(tmp_path: Path):
    """Create temporary test files."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file3 = tmp_path / "file3.txt"

    file1.write_text("Content 1")
    file2.write_text("Content 2")
    file3.write_text("Content 3")

    return file1, file2, file3


@pytest.fixture
def sample_content(temp_files: tuple[Path, Path, Path]) -> FileContent:
    """Create sample FileContent."""
    file1 = temp_files[0]
    return FileContent(
        path=file1,
        file_type=FileType.TEXT,
        content="Content 1",
        size=9,
    )


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            content="test content",
            file_type=FileType.TEXT,
            size=12,
            cached_at=time.time(),
            mtime=time.time(),
        )

        assert entry.content == "test content"
        assert entry.file_type == FileType.TEXT
        assert entry.size == 12
        assert entry.cached_at > 0
        assert entry.mtime > 0


class TestCacheStats:
    """Tests for CacheStats."""

    def test_stats_default_values(self):
        """Test default statistics values."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=7, misses=3)
        assert stats.hit_rate == 0.7

    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_total_requests(self):
        """Test total requests calculation."""
        stats = CacheStats(hits=10, misses=5)
        assert stats.total_requests == 15


class TestLoaderCacheInit:
    """Tests for LoaderCache initialization."""

    def test_init_default_values(self):
        """Test default initialization."""
        cache = LoaderCache()
        assert cache.max_size_bytes == 100 * 1024 * 1024  # 100 MB
        assert cache.ttl_seconds is None
        assert len(cache._cache) == 0

    def test_init_custom_size(self):
        """Test initialization with custom size."""
        cache = LoaderCache(max_size_mb=50)
        assert cache.max_size_bytes == 50 * 1024 * 1024

    def test_init_with_ttl(self):
        """Test initialization with TTL."""
        cache = LoaderCache(ttl_seconds=3600)
        assert cache.ttl_seconds == 3600


class TestLoaderCacheBasicOperations:
    """Tests for basic cache operations."""

    def test_put_and_get(self, sample_content: FileContent):
        """Test putting and getting content."""
        cache = LoaderCache()
        path = sample_content.path

        cache.put(path, sample_content)
        retrieved = cache.get(path)

        assert retrieved is not None
        assert retrieved.path == sample_content.path
        assert retrieved.content == sample_content.content
        assert retrieved.size == sample_content.size

    def test_get_nonexistent(self, tmp_path: Path):
        """Test getting non-existent entry."""
        cache = LoaderCache()
        nonexistent = tmp_path / "nonexistent.txt"

        result = cache.get(nonexistent)
        assert result is None

    def test_invalidate_existing(self, sample_content: FileContent):
        """Test invalidating existing entry."""
        cache = LoaderCache()
        path = sample_content.path

        cache.put(path, sample_content)
        assert cache.get(path) is not None

        result = cache.invalidate(path)
        assert result is True
        assert cache.get(path) is None

    def test_invalidate_nonexistent(self, tmp_path: Path):
        """Test invalidating non-existent entry."""
        cache = LoaderCache()
        nonexistent = tmp_path / "nonexistent.txt"

        result = cache.invalidate(nonexistent)
        assert result is False

    def test_clear(self, sample_content: FileContent, temp_files):
        """Test clearing all cache entries."""
        cache = LoaderCache()

        # Add multiple entries
        for file_path in temp_files:
            content = FileContent(
                path=file_path,
                file_type=FileType.TEXT,
                content=file_path.read_text(),
                size=len(file_path.read_text()),
            )
            cache.put(file_path, content)

        assert cache.entry_count == 3

        cache.clear()
        assert cache.entry_count == 0


class TestLoaderCacheValidation:
    """Tests for cache validation."""

    def test_get_invalidates_modified_file(
        self, sample_content: FileContent
    ):
        """Test that modified files are invalidated."""
        cache = LoaderCache()
        path = sample_content.path

        # Put original content
        cache.put(path, sample_content)
        assert cache.get(path) is not None

        # Modify file
        time.sleep(0.01)  # Ensure mtime changes
        path.write_text("Modified content")

        # Should be invalidated
        result = cache.get(path)
        assert result is None

    def test_ttl_expiration(self, sample_content: FileContent):
        """Test TTL expiration."""
        cache = LoaderCache(ttl_seconds=0.1)  # 100ms TTL
        path = sample_content.path

        cache.put(path, sample_content)
        assert cache.get(path) is not None

        # Wait for expiration
        time.sleep(0.15)

        # Should be expired
        result = cache.get(path)
        assert result is None

    def test_get_invalidates_deleted_file(
        self, sample_content: FileContent
    ):
        """Test that deleted files are invalidated."""
        cache = LoaderCache()
        path = sample_content.path

        cache.put(path, sample_content)
        assert cache.get(path) is not None

        # Delete file
        path.unlink()

        # Should be invalidated
        result = cache.get(path)
        assert result is None


class TestLoaderCacheStatistics:
    """Tests for cache statistics."""

    def test_cache_hit(self, sample_content: FileContent):
        """Test cache hit tracking."""
        cache = LoaderCache()
        path = sample_content.path

        cache.put(path, sample_content)
        cache.get(path)

        stats = cache.stats()
        assert stats.hits == 1
        assert stats.misses == 0

    def test_cache_miss(self, tmp_path: Path):
        """Test cache miss tracking."""
        cache = LoaderCache()
        nonexistent = tmp_path / "nonexistent.txt"

        cache.get(nonexistent)

        stats = cache.stats()
        assert stats.hits == 0
        assert stats.misses == 1

    def test_mixed_hits_and_misses(
        self, sample_content: FileContent, tmp_path: Path
    ):
        """Test mixed hits and misses."""
        cache = LoaderCache()
        path = sample_content.path

        cache.put(path, sample_content)

        # 2 hits
        cache.get(path)
        cache.get(path)

        # 3 misses
        cache.get(tmp_path / "miss1.txt")
        cache.get(tmp_path / "miss2.txt")
        cache.get(tmp_path / "miss3.txt")

        stats = cache.stats()
        assert stats.hits == 2
        assert stats.misses == 3
        assert stats.hit_rate == 0.4

    def test_reset_stats(self, sample_content: FileContent):
        """Test resetting statistics."""
        cache = LoaderCache()
        path = sample_content.path

        cache.put(path, sample_content)
        cache.get(path)

        assert cache.stats().hits == 1

        cache.reset_stats()

        stats = cache.stats()
        assert stats.hits == 0
        assert stats.misses == 0


class TestLoaderCacheEviction:
    """Tests for cache eviction."""

    def test_eviction_when_size_exceeded(self, temp_files):
        """Test that oldest entries are evicted when size is exceeded."""
        # Small cache (200 bytes) - fits 2 entries but not 3
        cache = LoaderCache(max_size_mb=200 / (1024 * 1024))

        file1, file2, file3 = temp_files

        # Add entries (each ~100 bytes)
        for i, file_path in enumerate(temp_files):
            content = FileContent(
                path=file_path,
                file_type=FileType.TEXT,
                content=f"Content {i+1}" * 10,  # ~100 bytes each
                size=len(f"Content {i+1}" * 10),
            )
            cache.put(file_path, content)
            time.sleep(0.01)  # Ensure different cached_at times

        # First entry should be evicted (oldest)
        assert cache.get(file1) is None
        # Last two should remain
        assert cache.get(file2) is not None
        assert cache.get(file3) is not None

        # Check eviction stats
        stats = cache.stats()
        assert stats.evictions > 0

    def test_no_eviction_under_limit(self, temp_files):
        """Test that no eviction occurs under size limit."""
        cache = LoaderCache(max_size_mb=100)  # Large cache

        for file_path in temp_files:
            content = FileContent(
                path=file_path,
                file_type=FileType.TEXT,
                content=file_path.read_text(),
                size=len(file_path.read_text()),
            )
            cache.put(file_path, content)

        # All entries should be present
        for file_path in temp_files:
            assert cache.get(file_path) is not None

        # No evictions
        assert cache.stats().evictions == 0


class TestLoaderCacheProperties:
    """Tests for cache properties."""

    def test_size_bytes(self, sample_content: FileContent):
        """Test size_bytes property."""
        cache = LoaderCache()
        cache.put(sample_content.path, sample_content)

        assert cache.size_bytes == sample_content.size

    def test_size_mb(self, sample_content: FileContent):
        """Test size_mb property."""
        cache = LoaderCache()
        cache.put(sample_content.path, sample_content)

        expected_mb = sample_content.size / (1024 * 1024)
        assert abs(cache.size_mb - expected_mb) < 0.001

    def test_entry_count(self, temp_files):
        """Test entry_count property."""
        cache = LoaderCache()

        assert cache.entry_count == 0

        for file_path in temp_files:
            content = FileContent(
                path=file_path,
                file_type=FileType.TEXT,
                content=file_path.read_text(),
                size=len(file_path.read_text()),
            )
            cache.put(file_path, content)

        assert cache.entry_count == 3
