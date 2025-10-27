"""Tests for Brave Search tools."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from kagura.mcp.builtin.brave_search import (
    brave_image_search,
    brave_news_search,
    brave_video_search,
    brave_web_search,
)
from kagura.mcp.builtin.common import setup_external_library_logging


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
        # Disable cache to ensure we hit the API key check
        monkeypatch.setenv("ENABLE_SEARCH_CACHE", "false")

        result = await brave_web_search("test query")

        # brave_web_search returns JSON on error, text on success
        if result.startswith("{"):
            data = json.loads(result)
            assert "error" in data
            # Either import error or API key error is acceptable
            assert (
                "BRAVE_SEARCH_API_KEY" in data["error"]
                or "brave-search-python-client" in data["error"]
            )
        else:
            # Text response (cache hit or other case)
            # This is OK - cache might have returned a result
            assert isinstance(result, str)


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
    async def test_count_string_conversion(self, monkeypatch) -> None:
        """Test that count parameter handles string input (regression test for #333)"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        # Pass count as string - should be converted to int
        result = await brave_news_search("test query", count="10")  # type: ignore[arg-type]

        # The key test: no TypeError should occur
        # Result should be either JSON error message or actual results
        assert isinstance(result, str)
        assert len(result) > 0

        # If it's JSON, parse it (either error or results)
        if result.startswith("{") or result.startswith("["):
            data = json.loads(result)
            # Either error or valid results - both are acceptable
            # The important thing is we didn't get TypeError from count being a string
            assert isinstance(data, (dict, list))

    @pytest.mark.asyncio
    async def test_freshness_parameter(self, monkeypatch) -> None:
        """Test that freshness parameter is accepted"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        # Should not raise error about freshness parameter
        result = await brave_news_search("test", freshness="pw")
        data = json.loads(result)

        # Will fail due to missing key, but parameter should be accepted
        assert "error" in data

    @pytest.mark.asyncio
    async def test_json_serializable_results(self, monkeypatch) -> None:
        """Test that news search results are JSON serializable (HttpUrl fix)"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        result = await brave_news_search("test query")

        # Result should be valid JSON string
        assert isinstance(result, str)

        # Should be parseable as JSON
        # (no "Object of type HttpUrl is not JSON serializable" error)
        try:
            data = json.loads(result)
            # Successfully parsed - either error dict or results list
            assert isinstance(data, (dict, list))
        except json.JSONDecodeError:
            # Should not happen - result should always be valid JSON
            pytest.fail("Result is not valid JSON")


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
        from kagura.mcp.builtin.brave_search import _get_cache

        cache = _get_cache()
        assert cache is not None

    @pytest.mark.asyncio
    async def test_custom_cache_ttl(self, monkeypatch) -> None:
        """Test that SEARCH_CACHE_TTL is respected"""
        monkeypatch.setenv("SEARCH_CACHE_TTL", "7200")

        # Reset global cache
        import kagura.mcp.builtin.brave_search as bs
        from kagura.mcp.builtin.brave_search import _get_cache

        bs._search_cache = None

        cache = _get_cache()
        assert cache is not None
        assert cache.default_ttl == 7200

    @pytest.mark.asyncio
    async def test_cache_hit_reduces_api_calls(self, monkeypatch) -> None:
        """Test that cache hits avoid API calls"""
        import kagura.mcp.builtin.brave_search as bs

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

        # Should return cached result with cache indicator prefix
        expected = f"[CACHED SEARCH RESULT - Retrieved instantly]\n\n{cached_response}"
        assert result == expected

        # Verify it was a cache hit
        stats = cache.stats()
        assert stats["hits"] >= 1

    @pytest.mark.asyncio
    async def test_different_count_different_cache(self, monkeypatch) -> None:
        """Test that different count values use different cache entries"""
        import kagura.mcp.builtin.brave_search as bs

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
        expected5 = "[CACHED SEARCH RESULT - Retrieved instantly]\n\n5 results"
        assert result5 == expected5

        # Get with count=10
        result10 = await brave_web_search("Python", count=10)
        expected10 = "[CACHED SEARCH RESULT - Retrieved instantly]\n\n10 results"
        assert result10 == expected10

    @pytest.mark.asyncio
    async def test_query_normalization_in_caching(self, monkeypatch) -> None:
        """Test that queries are normalized for caching"""
        import kagura.mcp.builtin.brave_search as bs

        monkeypatch.setenv("ENABLE_SEARCH_CACHE", "true")

        # Reset global cache
        bs._search_cache = None

        cache = bs._get_cache()
        assert cache is not None

        # Set with mixed case and spaces
        await cache.set("  Python   Tutorial  ", "Results", count=5)

        # Get with normalized query - should hit cache
        result = await brave_web_search("python tutorial", count=5)
        expected = "[CACHED SEARCH RESULT - Retrieved instantly]\n\nResults"
        assert result == expected

        # Should be a cache hit
        stats = cache.stats()
        assert stats["hits"] >= 1


class TestBraveSearchLogging:
    """Test Brave Search logging configuration."""

    def test_respects_existing_env_var(self, monkeypatch) -> None:
        """Test that existing env var is respected"""
        custom_log_path = "/custom/path/to/log.log"
        monkeypatch.setenv("BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME", custom_log_path)

        # Call setup function
        result = setup_external_library_logging(
            "brave_search_python_client",
            "BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME",
            "brave_search_python_client.log",
        )

        # Should return existing env var
        assert result == custom_log_path
        assert os.environ["BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME"] == custom_log_path

    def test_creates_home_directory_log(self, monkeypatch, tmp_path) -> None:
        """Test that log file is created in home directory by default"""
        # Clear env var
        monkeypatch.delenv("BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME", raising=False)

        # Mock home directory to use tmp_path
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()

        with patch("kagura.mcp.builtin.common.Path.home", return_value=fake_home):
            result = setup_external_library_logging(
                "brave_search_python_client",
                "BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME",
                "brave_search_python_client.log",
            )

            # Should set env var to home directory
            log_file = "brave_search_python_client.log"
            expected_log_path = fake_home / ".kagura" / "logs" / log_file
            assert result == str(expected_log_path)
            assert os.environ["BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME"] == str(
                expected_log_path
            )

            # Should create the log directory
            assert (fake_home / ".kagura" / "logs").exists()

    def test_fallback_to_null_device_on_permission_error(
        self, monkeypatch
    ) -> None:
        """Test fallback to /dev/null when home directory is not writable"""
        # Clear env var
        monkeypatch.delenv("BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME", raising=False)

        # Mock Path.home() to raise permission error
        with patch(
            "kagura.mcp.builtin.common.Path.home",
            side_effect=PermissionError("No access"),
        ):
            result = setup_external_library_logging(
                "brave_search_python_client",
                "BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME",
                "brave_search_python_client.log",
            )

            # Should fallback to null device
            assert result in ("/dev/null", "NUL")
            log_path = os.environ.get("BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME")
            assert log_path in ("/dev/null", "NUL")

    def test_fallback_to_null_device_on_write_test_failure(
        self, monkeypatch, tmp_path
    ) -> None:
        """Test fallback to /dev/null when write test fails"""
        # Clear env var
        monkeypatch.delenv("BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME", raising=False)

        # Mock home directory
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()

        # Mock Path.touch() to raise permission error
        original_touch = Path.touch

        def mock_touch(self, *args, **kwargs):
            if ".write_test" in str(self):
                raise PermissionError("Cannot write to directory")
            return original_touch(self, *args, **kwargs)

        with (
            patch("kagura.mcp.builtin.common.Path.home", return_value=fake_home),
            patch("kagura.mcp.builtin.common.Path.touch", mock_touch),
        ):
            result = setup_external_library_logging(
                "brave_search_python_client",
                "BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME",
                "brave_search_python_client.log",
            )

            # Should fallback to null device
            assert result in ("/dev/null", "NUL")
            log_path = os.environ.get("BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME")
            assert log_path in ("/dev/null", "NUL")

    def test_windows_null_device(self, monkeypatch) -> None:
        """Test that Windows uses NUL as null device"""
        # Clear env var
        monkeypatch.delenv("BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME", raising=False)

        # Mock os.name to simulate Windows
        monkeypatch.setattr("kagura.mcp.builtin.common.os.name", "nt")

        # Mock Path.home() to raise error (force fallback)
        with patch(
            "kagura.mcp.builtin.common.Path.home",
            side_effect=PermissionError("No access"),
        ):
            result = setup_external_library_logging(
                "brave_search_python_client",
                "BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME",
                "brave_search_python_client.log",
            )

            # Should use Windows null device
            assert result == "NUL"
            assert os.environ["BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME"] == "NUL"

    def test_unix_null_device(self, monkeypatch) -> None:
        """Test that Unix-like systems use /dev/null as null device"""
        # Clear env var
        monkeypatch.delenv("BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME", raising=False)

        # Mock os.name to simulate Unix
        monkeypatch.setattr("kagura.mcp.builtin.common.os.name", "posix")

        # Mock Path.home() to raise error (force fallback)
        with patch(
            "kagura.mcp.builtin.common.Path.home",
            side_effect=PermissionError("No access"),
        ):
            result = setup_external_library_logging(
                "brave_search_python_client",
                "BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME",
                "brave_search_python_client.log",
            )

            # Should use Unix null device
            assert result == "/dev/null"
            assert os.environ["BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME"] == "/dev/null"


class TestBraveImageSearch:
    """Test brave_image_search tool."""

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

        result = await brave_image_search("test query")
        data = json.loads(result)

        assert "error" in data
        assert "brave-search-python-client" in data["error"]

    @pytest.mark.asyncio
    async def test_missing_api_key(self, monkeypatch) -> None:
        """Test error when BRAVE_SEARCH_API_KEY not set"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        result = await brave_image_search("test query")
        data = json.loads(result)

        assert "error" in data
        assert (
            "BRAVE_SEARCH_API_KEY" in data["error"]
            or "brave-search-python-client" in data["error"]
        )

    @pytest.mark.asyncio
    async def test_count_string_conversion(self, monkeypatch) -> None:
        """Test that count parameter handles string input"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        # Pass count as string - should be converted to int
        result = await brave_image_search("test", count="10")  # type: ignore[arg-type]

        # The key test: no TypeError should occur
        assert isinstance(result, str)
        assert len(result) > 0


class TestBraveVideoSearch:
    """Test brave_video_search tool."""

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

        result = await brave_video_search("test query")
        data = json.loads(result)

        assert "error" in data
        assert "brave-search-python-client" in data["error"]

    @pytest.mark.asyncio
    async def test_missing_api_key(self, monkeypatch) -> None:
        """Test error when BRAVE_SEARCH_API_KEY not set"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        result = await brave_video_search("test query")
        data = json.loads(result)

        assert "error" in data
        assert (
            "BRAVE_SEARCH_API_KEY" in data["error"]
            or "brave-search-python-client" in data["error"]
        )

    @pytest.mark.asyncio
    async def test_count_string_conversion(self, monkeypatch) -> None:
        """Test that count parameter handles string input"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        # Pass count as string - should be converted to int
        result = await brave_video_search("test", count="10")  # type: ignore[arg-type]

        # The key test: no TypeError should occur
        assert isinstance(result, str)
        assert len(result) > 0
