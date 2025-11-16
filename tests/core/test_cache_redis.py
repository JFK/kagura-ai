"""Tests for LLM Cache with Redis backend.

Issue #554 - Cloud-Native Infrastructure Migration (Phase 2)
"""

import os

import pytest

from kagura.core.cache import LLMCache


class TestLLMCacheMemoryBackend:
    """Test LLMCache with in-memory backend (default)."""

    @pytest.mark.asyncio
    async def test_memory_backend_default(self):
        """Test default in-memory backend."""
        cache = LLMCache()

        assert cache.backend == "memory"

        # Basic operations
        key = cache._hash_key("test", "gpt-4")
        await cache.set(key, "response")

        result = await cache.get(key)
        assert result == "response"

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics."""
        cache = LLMCache()

        key = cache._hash_key("test", "gpt-4")

        # Miss
        await cache.get(key)

        # Set and hit
        await cache.set(key, "response")
        await cache.get(key)

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["backend"] == "memory"


@pytest.mark.skipif(
    not os.getenv("TEST_REDIS_URL"),
    reason="TEST_REDIS_URL not set (Redis tests require Redis server)",
)
class TestLLMCacheRedisBackend:
    """Test LLMCache with Redis backend.

    Note: Requires TEST_REDIS_URL environment variable.

    Example:
        export TEST_REDIS_URL=redis://localhost:6379/1
        pytest tests/core/test_cache_redis.py::TestLLMCacheRedisBackend
    """

    @pytest.fixture
    def redis_url(self):
        """Get test Redis URL from environment."""
        return os.getenv("TEST_REDIS_URL")

    @pytest.fixture
    async def cache(self, redis_url):
        """Create LLMCache with Redis backend."""
        cache = LLMCache(backend="redis", redis_url=redis_url)

        yield cache

        # Cleanup: Clear test cache keys
        try:
            keys = cache._redis.keys("llm_cache:*")
            if keys:
                cache._redis.delete(*keys)
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_redis_backend_initialization(self, cache):
        """Test Redis backend initialization."""
        assert cache.backend == "redis"
        assert cache._redis is not None

        # Test connection
        cache._redis.ping()

    @pytest.mark.asyncio
    async def test_redis_set_and_get(self, cache):
        """Test basic set and get operations."""
        key = cache._hash_key("test", "gpt-4")

        # Set
        await cache.set(key, "test_response")

        # Get
        result = await cache.get(key)
        assert result == "test_response"

    @pytest.mark.asyncio
    async def test_redis_ttl_expiration(self, cache):
        """Test TTL-based expiration."""
        key = cache._hash_key("test_ttl", "gpt-4")

        # Set with short TTL
        await cache.set(key, "response", ttl=1)

        # Should exist immediately
        result = await cache.get(key)
        assert result == "response"

        # Wait for expiration
        import asyncio

        await asyncio.sleep(2)

        # Should be expired
        result = await cache.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_invalidate_all(self, cache):
        """Test invalidating all cache entries."""
        # Add multiple entries
        for i in range(5):
            key = cache._hash_key(f"test_{i}", "gpt-4")
            await cache.set(key, f"response_{i}")

        # Invalidate all
        await cache.invalidate()

        # All should be gone
        for i in range(5):
            key = cache._hash_key(f"test_{i}", "gpt-4")
            result = await cache.get(key)
            assert result is None

    @pytest.mark.asyncio
    async def test_redis_invalidate_pattern(self, cache):
        """Test invalidating cache entries by pattern."""
        # Add entries with different patterns
        await cache.set(cache._hash_key("translate_en", "gpt-4"), "resp1")
        await cache.set(cache._hash_key("translate_ja", "gpt-4"), "resp2")
        await cache.set(cache._hash_key("summarize", "gpt-4"), "resp3")

        # Invalidate translate_* pattern
        await cache.invalidate("translate")

        # translate entries should be gone
        assert await cache.get(cache._hash_key("translate_en", "gpt-4")) is None
        assert await cache.get(cache._hash_key("translate_ja", "gpt-4")) is None

        # summarize should remain
        assert await cache.get(cache._hash_key("summarize", "gpt-4")) == "resp3"

    @pytest.mark.asyncio
    async def test_redis_stats(self, cache):
        """Test cache statistics with Redis backend."""
        key = cache._hash_key("test", "gpt-4")

        # Miss
        await cache.get(key)

        # Set and hit
        await cache.set(key, "response")
        await cache.get(key)

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["backend"] == "redis"
        assert "total_redis_keys" in stats

    @pytest.mark.asyncio
    async def test_redis_singleton_pattern(self, redis_url):
        """Test that multiple cache instances share same Redis client."""
        cache1 = LLMCache(backend="redis", redis_url=redis_url)
        cache2 = LLMCache(backend="redis", redis_url=redis_url)

        # Should share same Redis client
        assert cache1._redis is cache2._redis

        # Operations on cache1 should be visible in cache2
        key = cache1._hash_key("shared_test", "gpt-4")
        await cache1.set(key, "shared_response")

        result = await cache2.get(key)
        assert result == "shared_response"

        # Cleanup
        await cache1.invalidate()

    @pytest.mark.asyncio
    async def test_environment_variable_redis(self, redis_url, monkeypatch):
        """Test CACHE_BACKEND environment variable."""
        monkeypatch.setenv("CACHE_BACKEND", "redis")
        monkeypatch.setenv("REDIS_URL", redis_url)

        cache = LLMCache()

        assert cache.backend == "redis"
        assert cache._redis is not None

        # Cleanup
        await cache.invalidate()
