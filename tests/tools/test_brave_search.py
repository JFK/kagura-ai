"""Tests for Brave Search tools."""

import json

import pytest

from kagura.tools.brave_search import brave_news_search, brave_web_search


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
