"""Tests for SearchCache."""

import asyncio

import pytest

from kagura.mcp.builtin.cache import SearchCache


class TestSearchCache:
    """Test SearchCache functionality."""

    @pytest.mark.asyncio
    async def test_basic_caching(self) -> None:
        """Test basic cache set and get operations"""
        cache = SearchCache(default_ttl=3600)

        # Set a value
        await cache.set("Python tutorial", "Search results for Python", count=5)

        # Get it back
        result = await cache.get("Python tutorial", count=5)
        assert result == "Search results for Python"

        # Stats should show 1 hit, 0 misses
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        assert stats["size"] == 1

    @pytest.mark.asyncio
    async def test_cache_miss(self) -> None:
        """Test cache miss behavior"""
        cache = SearchCache()

        # Get non-existent value
        result = await cache.get("nonexistent query", count=5)
        assert result is None

        # Stats should show 0 hits, 1 miss
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_query_normalization(self) -> None:
        """Test that queries are normalized for consistent caching"""
        cache = SearchCache()

        # Set with mixed case and extra spaces
        await cache.set("  Python   Tutorial  ", "Results", count=5)

        # Get with different formatting - should hit cache
        result = await cache.get("python tutorial", count=5)
        assert result == "Results"

        # Should be a cache hit
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    @pytest.mark.asyncio
    async def test_count_affects_cache_key(self) -> None:
        """Test that different count values create different cache entries"""
        cache = SearchCache()

        # Set with count=5
        await cache.set("Python", "5 results", count=5)

        # Set with count=10 (different cache key)
        await cache.set("Python", "10 results", count=10)

        # Getting with count=5 should return first result
        result5 = await cache.get("Python", count=5)
        assert result5 == "5 results"

        # Getting with count=10 should return second result
        result10 = await cache.get("Python", count=10)
        assert result10 == "10 results"

        # Should have 2 entries
        stats = cache.stats()
        assert stats["size"] == 2

    @pytest.mark.asyncio
    async def test_ttl_expiration(self) -> None:
        """Test that cache entries expire after TTL"""
        cache = SearchCache(default_ttl=1)  # 1 second TTL

        # Set a value
        await cache.set("Python", "Results", count=5)

        # Immediately get it - should hit
        result = await cache.get("Python", count=5)
        assert result == "Results"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired now
        result = await cache.get("Python", count=5)
        assert result is None

        # Should be removed from cache
        stats = cache.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_lru_eviction(self) -> None:
        """Test LRU eviction when cache reaches max_size"""
        cache = SearchCache(max_size=2)

        # Add 2 entries
        await cache.set("query1", "result1", count=5)
        await cache.set("query2", "result2", count=5)

        # Cache should have 2 entries
        assert cache.stats()["size"] == 2

        # Add 3rd entry - should evict oldest (query1)
        await cache.set("query3", "result3", count=5)

        # query1 should be evicted
        assert await cache.get("query1", count=5) is None

        # query2 and query3 should still be there
        assert await cache.get("query2", count=5) == "result2"
        assert await cache.get("query3", count=5) == "result3"

        # Size should still be 2
        assert cache.stats()["size"] == 2

    @pytest.mark.asyncio
    async def test_invalidate_all(self) -> None:
        """Test invalidating all cache entries"""
        cache = SearchCache()

        # Add some entries
        await cache.set("Python tutorial", "results1", count=5)
        await cache.set("Java tutorial", "results2", count=5)

        # Invalidate all
        await cache.invalidate()

        # Cache should be empty
        stats = cache.stats()
        assert stats["size"] == 0

        # Entries should be gone
        assert await cache.get("Python tutorial", count=5) is None
        assert await cache.get("Java tutorial", count=5) is None

    @pytest.mark.asyncio
    async def test_invalidate_by_pattern(self) -> None:
        """Test invalidating cache entries by pattern"""
        cache = SearchCache()

        # Add entries
        await cache.set("Python tutorial", "results1", count=5)
        await cache.set("Python basics", "results2", count=5)
        await cache.set("Java tutorial", "results3", count=5)

        # Invalidate entries containing "python"
        await cache.invalidate("python")

        # Python entries should be gone
        assert await cache.get("Python tutorial", count=5) is None
        assert await cache.get("Python basics", count=5) is None

        # Java entry should still be there
        assert await cache.get("Java tutorial", count=5) == "results3"

        # Size should be 1
        assert cache.stats()["size"] == 1

    @pytest.mark.asyncio
    async def test_custom_ttl(self) -> None:
        """Test setting custom TTL per entry"""
        cache = SearchCache(default_ttl=3600)

        # Set with custom short TTL
        await cache.set("Python", "Results", count=5, ttl=1)

        # Immediately get it - should hit
        result = await cache.get("Python", count=5)
        assert result == "Results"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        result = await cache.get("Python", count=5)
        assert result is None

    @pytest.mark.asyncio
    async def test_hit_rate_calculation(self) -> None:
        """Test cache hit rate calculation"""
        cache = SearchCache()

        # Set a value
        await cache.set("Python", "Results", count=5)

        # 1 hit
        await cache.get("Python", count=5)

        # 1 miss
        await cache.get("nonexistent", count=5)

        # Hit rate should be 0.5 (1 hit out of 2 total)
        stats = cache.stats()
        assert stats["hit_rate"] == 0.5

        # Another hit
        await cache.get("Python", count=5)

        # Hit rate should be 0.666... (2 hits out of 3 total)
        stats = cache.stats()
        assert abs(stats["hit_rate"] - 2 / 3) < 0.01

    @pytest.mark.asyncio
    async def test_normalize_query_edge_cases(self) -> None:
        """Test query normalization edge cases"""
        cache = SearchCache()

        # Test various normalizations
        test_cases = [
            ("  Python  ", "python"),
            ("PYTHON", "python"),
            ("Python   Tutorial", "python tutorial"),
            ("  PYTHON   TUTORIAL  ", "python tutorial"),
        ]

        for input_query, expected_normalized in test_cases:
            normalized = cache._normalize_query(input_query)
            assert normalized == expected_normalized
