"""Integration tests for LLM cache with call_llm()

Tests cover:
- Cache hit/miss behavior with call_llm()
- LLMConfig cache settings
- get_llm_cache() / set_llm_cache()
- Cache invalidation
- Cache stats tracking
- Tool functions disable caching
"""

import pytest

from kagura.core.cache import LLMCache
from kagura.core.llm import LLMConfig, call_llm, get_llm_cache, set_llm_cache


@pytest.fixture
def mock_llm_response():
    """Mock LLM response object"""

    class MockMessage:
        def __init__(self, content: str):
            self.content = content
            self.tool_calls = None

    class MockChoice:
        def __init__(self, content: str):
            self.message = MockMessage(content)

    class MockResponse:
        def __init__(self, content: str):
            self.choices = [MockChoice(content)]

    async def mock_completion(*args, **kwargs):
        # Extract prompt from messages
        messages = kwargs.get("messages", [])
        if messages:
            prompt = messages[0].get("content", "")
            # Simple mapping
            responses = {
                "test prompt": "test response",
                "another prompt": "another response",
                "cached prompt": "cached response",
            }
            return MockResponse(responses.get(prompt, "default response"))
        return MockResponse("default response")

    return mock_completion


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset global cache before each test"""
    # Create fresh cache
    fresh_cache = LLMCache(max_size=1000, default_ttl=3600)
    set_llm_cache(fresh_cache)
    yield
    # Clean up after test
    fresh_cache = LLMCache(max_size=1000, default_ttl=3600)
    set_llm_cache(fresh_cache)


# Note: Cache tests now use claude models to test LiteLLM backend
# (OpenAI direct backend doesn't implement caching yet)


class TestLLMCacheIntegration:
    """Tests for call_llm() caching integration"""

    @pytest.mark.asyncio
    async def test_call_llm_cache_miss(self, mock_llm_response, monkeypatch):
        """Test call_llm() cache miss (first call)"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022", enable_cache=True)
        result = await call_llm("test prompt", config)

        assert result == "test response"

        # Check cache stats
        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    @pytest.mark.asyncio
    async def test_call_llm_cache_hit(self, mock_llm_response, monkeypatch):
        """Test call_llm() cache hit (second call)"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022", enable_cache=True)

        # First call (cache miss)
        result1 = await call_llm("cached prompt", config)
        assert result1 == "cached response"

        # Second call (cache hit)
        result2 = await call_llm("cached prompt", config)
        assert result2 == "cached response"

        # Check cache stats
        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_call_llm_cache_disabled(self, mock_llm_response, monkeypatch):
        """Test caching can be disabled via config"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022", enable_cache=False)

        # Two calls with same prompt
        result1 = await call_llm("test prompt", config)
        result2 = await call_llm("test prompt", config)

        assert result1 == "test response"
        assert result2 == "test response"

        # Cache should not have been used
        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0  # Never checked cache

    @pytest.mark.asyncio
    async def test_call_llm_custom_ttl(self, mock_llm_response, monkeypatch):
        """Test custom cache TTL is respected"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(
            model="claude-3-5-sonnet-20241022",
            enable_cache=True,
            cache_ttl=7200,  # 2 hours
        )

        await call_llm("test prompt", config)

        # Check TTL in cache
        cache = get_llm_cache()
        # Get the cached entry (internal access for testing)
        for entry in cache._cache.values():
            assert entry.ttl == 7200

    @pytest.mark.asyncio
    async def test_get_llm_cache(self):
        """Test get_llm_cache() returns global instance"""
        cache = get_llm_cache()
        assert isinstance(cache, LLMCache)
        assert cache.backend == "memory"

    @pytest.mark.asyncio
    async def test_set_llm_cache(self):
        """Test set_llm_cache() replaces global instance"""
        custom_cache = LLMCache(max_size=500, default_ttl=1800)
        set_llm_cache(custom_cache)

        cache = get_llm_cache()
        assert cache.max_size == 500
        assert cache.default_ttl == 1800

    @pytest.mark.asyncio
    async def test_cache_with_different_kwargs(self, mock_llm_response, monkeypatch):
        """Test different kwargs create different cache keys"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config1 = LLMConfig(model="claude-3-5-sonnet-20241022", temperature=0.7)
        config2 = LLMConfig(model="claude-3-5-sonnet-20241022", temperature=0.9)

        await call_llm("test prompt", config1)
        await call_llm("test prompt", config2)

        # Both should be cache misses (different temperatures)
        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0
        assert stats["size"] == 2  # Two separate cache entries

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, mock_llm_response, monkeypatch):
        """Test cache can be invalidated"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022")

        # Cache a response
        result1 = await call_llm("test prompt", config)
        assert result1 == "test response"

        # Invalidate cache
        cache = get_llm_cache()
        await cache.invalidate()

        # Next call should be cache miss
        result2 = await call_llm("test prompt", config)
        assert result2 == "test response"

        stats = cache.stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0

    @pytest.mark.asyncio
    async def test_llm_config_cache_defaults(self):
        """Test LLMConfig has correct cache defaults"""
        config = LLMConfig()

        assert config.enable_cache is True
        assert config.cache_ttl == 3600
        assert config.cache_backend == "memory"

    @pytest.mark.asyncio
    async def test_cache_across_multiple_calls(self, mock_llm_response, monkeypatch):
        """Test cache works across multiple different calls"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022")

        # Call 3 different prompts
        await call_llm("test prompt", config)
        await call_llm("another prompt", config)
        await call_llm("cached prompt", config)

        # Repeat calls (should hit cache)
        await call_llm("test prompt", config)
        await call_llm("another prompt", config)

        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["size"] == 3  # 3 unique prompts
        assert stats["hits"] == 2  # 2 repeated calls
        assert stats["misses"] == 3  # 3 initial calls
        assert stats["hit_rate"] == 2 / 5

    @pytest.mark.asyncio
    async def test_cache_stats_tracking(self, mock_llm_response, monkeypatch):
        """Test cache stats are accurately tracked"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022")

        # 1 miss
        await call_llm("test prompt", config)
        # 1 hit
        await call_llm("test prompt", config)
        # 1 hit
        await call_llm("test prompt", config)
        # 1 miss
        await call_llm("another prompt", config)

        cache = get_llm_cache()
        stats = cache.stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.5
        assert stats["size"] == 2


class TestToolFunctionsCaching:
    """Tests for caching behavior with tool functions"""

    @pytest.mark.asyncio
    async def test_tool_functions_disable_caching(self, mock_llm_response, monkeypatch):
        """Test tool functions disable caching"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        def dummy_tool():
            return "tool result"

        config = LLMConfig(model="claude-3-5-sonnet-20241022", enable_cache=True)

        # Call with tool function
        await call_llm("test prompt", config, tool_functions=[dummy_tool])

        # Cache should not have been used
        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0

    @pytest.mark.asyncio
    async def test_cache_works_without_tools(self, mock_llm_response, monkeypatch):
        """Test caching works when no tools are provided"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022")

        # First call (no tools)
        result1 = await call_llm("test prompt", config, tool_functions=None)
        # Second call (no tools, should hit cache)
        result2 = await call_llm("test prompt", config, tool_functions=None)

        assert result1 == result2

        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1


class TestCacheKeyGeneration:
    """Tests for cache key generation"""

    @pytest.mark.asyncio
    async def test_different_models_different_cache_keys(
        self, mock_llm_response, monkeypatch
    ):
        """Test different models create different cache keys"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config1 = LLMConfig(model="claude-3-5-sonnet-20241022")
        config2 = LLMConfig(model="claude-3-opus-20240229")

        await call_llm("test prompt", config1)
        await call_llm("test prompt", config2)

        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["size"] == 2  # Different models = different keys

    @pytest.mark.asyncio
    async def test_same_prompt_same_model_same_key(
        self, mock_llm_response, monkeypatch
    ):
        """Test same prompt + model creates same cache key"""
        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_llm_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022", temperature=0.7)

        await call_llm("test prompt", config)
        await call_llm("test prompt", config)

        cache = get_llm_cache()
        stats = cache.stats()
        assert stats["size"] == 1  # Same key reused
        assert stats["hits"] == 1  # Second call hit cache
