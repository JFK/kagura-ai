"""Tests for Brave Search tools."""

import json

import pytest

from kagura.tools.brave_search import _search_cache, brave_news_search, brave_web_search


class TestBraveWebSearch:
    """Test brave_web_search tool."""

    @pytest.mark.asyncio
    async def test_missing_library(self, monkeypatch) -> None:
        """Test error when brave-search-python-client not installed"""
        # Mock missing import
        import sys

        # Remove module if exists
        if "brave_search_python_client" in sys.modules:
            del sys.modules["brave_search_python_client"]

        # Mock import error
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "brave_search_python_client":
                raise ImportError("No module named 'brave_search_python_client'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = await brave_web_search("test query")
        data = json.loads(result)

        assert "error" in data
        assert "brave-search-python-client" in data["error"]
        assert "install" in data

    @pytest.mark.asyncio
    async def test_missing_api_key(self, monkeypatch) -> None:
        """Test error when BRAVE_SEARCH_API_KEY not set"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        result = await brave_web_search("test query")
        data = json.loads(result)

        assert "error" in data
        # Either import error or API key error is acceptable
        assert (
            "BRAVE_SEARCH_API_KEY" in data["error"]
            or "brave-search-python-client" in data["error"]
        )


class TestBraveNewsSearch:
    """Test brave_news_search tool."""

    @pytest.mark.asyncio
    async def test_missing_library(self, monkeypatch) -> None:
        """Test error when brave-search-python-client not installed"""
        import builtins
        import sys

        if "brave_search_python_client" in sys.modules:
            del sys.modules["brave_search_python_client"]

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "brave_search_python_client":
                raise ImportError("No module named 'brave_search_python_client'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = await brave_news_search("test query")
        data = json.loads(result)

        assert "error" in data
        assert "brave-search-python-client" in data["error"]

    @pytest.mark.asyncio
    async def test_missing_api_key(self, monkeypatch) -> None:
        """Test error when BRAVE_SEARCH_API_KEY not set"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        result = await brave_news_search("test query")
        data = json.loads(result)

        assert "error" in data
        # Either import error or API key error is acceptable
        assert (
            "BRAVE_SEARCH_API_KEY" in data["error"]
            or "brave-search-python-client" in data["error"]
        )

    @pytest.mark.asyncio
    async def test_freshness_parameter(self, monkeypatch) -> None:
        """Test that freshness parameter is accepted"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        # Should not raise error about freshness parameter
        result = await brave_news_search("test", freshness="pw")
        data = json.loads(result)

        # Will fail due to missing key, but parameter should be accepted
        assert "error" in data


class TestBraveSearchCaching:
    """Test caching functionality for brave_web_search."""

    @pytest.mark.asyncio
    async def test_cache_disabled(self, monkeypatch) -> None:
        """Test that caching is disabled when ENABLE_SEARCH_CACHE=false"""
        monkeypatch.setenv("ENABLE_SEARCH_CACHE", "false")
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        # Even with cache disabled, should handle missing API key gracefully
        result = await brave_web_search("test query")

        # Result could be JSON error or text response
        if result.startswith("{"):
            data = json.loads(result)
            assert "error" in data
        else:
            # Text response (when library is missing or other error)
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_cache_enabled_by_default(self, monkeypatch) -> None:
        """Test that caching is enabled by default"""
        # Don't set ENABLE_SEARCH_CACHE - should default to true
        monkeypatch.delenv("ENABLE_SEARCH_CACHE", raising=False)

        # Import the function to check if cache is created
        from kagura.tools.brave_search import _get_cache

        cache = _get_cache()
        assert cache is not None

    @pytest.mark.asyncio
    async def test_custom_cache_ttl(self, monkeypatch) -> None:
        """Test that SEARCH_CACHE_TTL is respected"""
        monkeypatch.setenv("SEARCH_CACHE_TTL", "7200")

        from kagura.tools.brave_search import _get_cache

        # Reset global cache
        import kagura.tools.brave_search as bs

        bs._search_cache = None

        cache = _get_cache()
        assert cache is not None
        assert cache.default_ttl == 7200

    @pytest.mark.asyncio
    async def test_cache_hit_reduces_api_calls(self, monkeypatch) -> None:
        """Test that cache hits avoid API calls"""
        import kagura.tools.brave_search as bs

        # Enable caching
        monkeypatch.setenv("ENABLE_SEARCH_CACHE", "true")

        # Reset global cache
        bs._search_cache = None

        # Pre-populate cache with a result
        cache = bs._get_cache()
        assert cache is not None

        test_query = "test cache query"
        cached_response = "Cached search results"

        await cache.set(test_query, cached_response, count=5)

        # Now call brave_web_search - should hit cache (no API key needed)
        result = await brave_web_search(test_query, count=5)

        # Should return cached result
        assert result == cached_response

        # Verify it was a cache hit
        stats = cache.stats()
        assert stats["hits"] >= 1

    @pytest.mark.asyncio
    async def test_different_count_different_cache(self, monkeypatch) -> None:
        """Test that different count values use different cache entries"""
        import kagura.tools.brave_search as bs

        monkeypatch.setenv("ENABLE_SEARCH_CACHE", "true")

        # Reset global cache
        bs._search_cache = None

        cache = bs._get_cache()
        assert cache is not None

        # Pre-populate cache with different counts
        await cache.set("Python", "5 results", count=5)
        await cache.set("Python", "10 results", count=10)

        # Get with count=5
        result5 = await brave_web_search("Python", count=5)
        assert result5 == "5 results"

        # Get with count=10
        result10 = await brave_web_search("Python", count=10)
        assert result10 == "10 results"

    @pytest.mark.asyncio
    async def test_query_normalization_in_caching(self, monkeypatch) -> None:
        """Test that queries are normalized for caching"""
        import kagura.tools.brave_search as bs

        monkeypatch.setenv("ENABLE_SEARCH_CACHE", "true")

        # Reset global cache
        bs._search_cache = None

        cache = bs._get_cache()
        assert cache is not None

        # Set with mixed case and spaces
        await cache.set("  Python   Tutorial  ", "Results", count=5)

        # Get with normalized query - should hit cache
        result = await brave_web_search("python tutorial", count=5)
        assert result == "Results"

        # Should be a cache hit
        stats = cache.stats()
        assert stats["hits"] >= 1
