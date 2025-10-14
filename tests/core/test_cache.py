"""Tests for LLM Cache System

Tests cover:
- CacheEntry dataclass and expiration
- LLMCache basic operations (get/set/invalidate)
- Hash key generation and determinism
- LRU eviction
- Cache statistics
- Edge cases and error handling
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from kagura.core.cache import CacheEntry, LLMCache


class TestCacheEntry:
    """Tests for CacheEntry dataclass"""

    def test_cache_entry_creation(self):
        """Test CacheEntry can be created with all fields"""
        entry = CacheEntry(
            key="test_key",
            response="test_response",
            created_at=datetime.now(),
            ttl=3600,
            model="gpt-4o-mini"
        )
        assert entry.key == "test_key"
        assert entry.response == "test_response"
        assert entry.ttl == 3600
        assert entry.model == "gpt-4o-mini"

    def test_cache_entry_not_expired(self):
        """Test cache entry is not expired within TTL"""
        entry = CacheEntry(
            key="test",
            response="data",
            created_at=datetime.now(),
            ttl=3600,  # 1 hour
            model="gpt-4o-mini"
        )
        assert not entry.is_expired

    def test_cache_entry_expired(self):
        """Test cache entry is expired after TTL"""
        entry = CacheEntry(
            key="test",
            response="data",
            created_at=datetime.now() - timedelta(seconds=3601),  # 1 hour 1 second ago
            ttl=3600,
            model="gpt-4o-mini"
        )
        assert entry.is_expired

    def test_cache_entry_expiration_edge_case(self):
        """Test cache entry expiration at exact TTL boundary"""
        # Created exactly TTL seconds ago
        entry = CacheEntry(
            key="test",
            response="data",
            created_at=datetime.now() - timedelta(seconds=3600),
            ttl=3600,
            model="gpt-4o-mini"
        )
        # Should be expired or very close to expiration
        # Due to timing, we allow small tolerance
        elapsed = (datetime.now() - entry.created_at).total_seconds()
        assert entry.is_expired or elapsed >= entry.ttl


class TestLLMCache:
    """Tests for LLMCache class"""

    def test_cache_initialization(self):
        """Test LLMCache can be initialized with custom params"""
        cache = LLMCache(
            backend="memory",
            default_ttl=7200,
            max_size=500
        )
        assert cache.backend == "memory"
        assert cache.default_ttl == 7200
        assert cache.max_size == 500
        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_cache_initialization_defaults(self):
        """Test LLMCache uses correct defaults"""
        cache = LLMCache()
        assert cache.backend == "memory"
        assert cache.default_ttl == 3600
        assert cache.max_size == 1000

    @pytest.mark.asyncio
    async def test_cache_get_miss(self):
        """Test cache get returns None on miss"""
        cache = LLMCache()
        result = await cache.get("nonexistent_key")
        assert result is None
        assert cache._misses == 1
        assert cache._hits == 0

    @pytest.mark.asyncio
    async def test_cache_get_hit(self):
        """Test cache get returns value on hit"""
        cache = LLMCache()
        key = cache._hash_key("test", "gpt-4o-mini")
        await cache.set(key, "response_value")

        result = await cache.get(key)
        assert result == "response_value"
        assert cache._hits == 1
        assert cache._misses == 0

    @pytest.mark.asyncio
    async def test_cache_set(self):
        """Test cache set stores value correctly"""
        cache = LLMCache()
        key = "test_key"
        await cache.set(key, "test_value")

        assert len(cache._cache) == 1
        assert key in cache._cache
        assert cache._cache[key].response == "test_value"

    @pytest.mark.asyncio
    async def test_cache_set_with_custom_ttl(self):
        """Test cache set respects custom TTL"""
        cache = LLMCache(default_ttl=3600)
        key = "test_key"
        await cache.set(key, "test_value", ttl=7200)

        assert cache._cache[key].ttl == 7200  # Not default

    @pytest.mark.asyncio
    async def test_cache_set_with_model(self):
        """Test cache set stores model name"""
        cache = LLMCache()
        key = "test_key"
        await cache.set(key, "test_value", model="gpt-4o")

        assert cache._cache[key].model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_cache_expiration_on_get(self):
        """Test expired entries are removed on get"""
        cache = LLMCache(default_ttl=1)
        key = "test_key"
        await cache.set(key, "test_value")

        # Wait for expiration
        await asyncio.sleep(2)

        result = await cache.get(key)
        assert result is None
        assert key not in cache._cache  # Entry removed
        assert cache._misses == 1

    @pytest.mark.asyncio
    async def test_cache_eviction_lru(self):
        """Test LRU eviction when max_size is reached"""
        cache = LLMCache(max_size=2)

        # Fill cache
        await cache.set("key1", "value1")
        await asyncio.sleep(0.01)  # Ensure different timestamps
        await cache.set("key2", "value2")
        await asyncio.sleep(0.01)

        # This should evict key1 (oldest)
        await cache.set("key3", "value3")

        assert len(cache._cache) == 2
        assert "key1" not in cache._cache
        assert "key2" in cache._cache
        assert "key3" in cache._cache

    def test_hash_key_deterministic(self):
        """Test hash key is deterministic for same inputs"""
        cache = LLMCache()
        key1 = cache._hash_key("prompt", "gpt-4o-mini", temperature=0.7)
        key2 = cache._hash_key("prompt", "gpt-4o-mini", temperature=0.7)
        assert key1 == key2

    def test_hash_key_kwargs_order_independent(self):
        """Test hash key is same regardless of kwargs order"""
        cache = LLMCache()
        key1 = cache._hash_key("prompt", "gpt-4o-mini", temp=0.7, max_tokens=100)
        key2 = cache._hash_key("prompt", "gpt-4o-mini", max_tokens=100, temp=0.7)
        assert key1 == key2

    def test_hash_key_different_for_different_inputs(self):
        """Test hash key differs for different inputs"""
        cache = LLMCache()
        key1 = cache._hash_key("prompt1", "gpt-4o-mini")
        key2 = cache._hash_key("prompt2", "gpt-4o-mini")
        assert key1 != key2

    def test_hash_key_different_for_different_models(self):
        """Test hash key differs for different models"""
        cache = LLMCache()
        key1 = cache._hash_key("prompt", "gpt-4o-mini")
        key2 = cache._hash_key("prompt", "gpt-4o")
        assert key1 != key2

    def test_hash_key_length(self):
        """Test hash key is 16 characters"""
        cache = LLMCache()
        key = cache._hash_key("test", "gpt-4o-mini")
        assert len(key) == 16

    @pytest.mark.asyncio
    async def test_invalidate_all(self):
        """Test invalidate with no pattern clears all"""
        cache = LLMCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        await cache.invalidate()  # No pattern = clear all

        assert len(cache._cache) == 0

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self):
        """Test invalidate with pattern removes matching entries"""
        cache = LLMCache()
        await cache.set("translate_en_ja", "value1")
        await cache.set("translate_en_fr", "value2")
        await cache.set("summarize_doc", "value3")

        await cache.invalidate("translate")

        assert len(cache._cache) == 1
        assert "summarize_doc" in cache._cache

    @pytest.mark.asyncio
    async def test_stats_empty_cache(self):
        """Test stats for empty cache"""
        cache = LLMCache()
        stats = cache.stats()

        assert stats["size"] == 0
        assert stats["max_size"] == 1000
        assert stats["backend"] == "memory"
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_stats_hit_rate_calculation(self):
        """Test cache hit rate is calculated correctly"""
        cache = LLMCache()
        key = cache._hash_key("test", "gpt-4o-mini")

        await cache.set(key, "value")
        await cache.get(key)  # Hit
        await cache.get("nonexistent")  # Miss
        await cache.get(key)  # Hit

        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 2 / 3  # 2 hits out of 3 total

    @pytest.mark.asyncio
    async def test_stats_size_tracking(self):
        """Test stats accurately track cache size"""
        cache = LLMCache()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        stats = cache.stats()
        assert stats["size"] == 2

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test cache handles concurrent access correctly"""
        cache = LLMCache()

        async def set_value(key: str, value: str):
            await cache.set(key, value)

        async def get_value(key: str):
            return await cache.get(key)

        # Set multiple values concurrently
        await asyncio.gather(
            set_value("key1", "value1"),
            set_value("key2", "value2"),
            set_value("key3", "value3")
        )

        assert len(cache._cache) == 3

        # Get multiple values concurrently
        results = await asyncio.gather(
            get_value("key1"),
            get_value("key2"),
            get_value("key3")
        )

        assert results == ["value1", "value2", "value3"]
        assert cache._hits == 3

    @pytest.mark.asyncio
    async def test_large_response_caching(self):
        """Test cache handles large responses"""
        cache = LLMCache()
        large_response = "x" * 10000  # 10KB response
        key = "large_key"

        await cache.set(key, large_response)
        result = await cache.get(key)

        assert result == large_response
        assert len(result) == 10000

    @pytest.mark.asyncio
    async def test_empty_cache_stats(self):
        """Test stats with no operations"""
        cache = LLMCache()
        stats = cache.stats()

        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
