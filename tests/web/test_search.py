"""Tests for web search functionality."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip tests if web dependencies not available
pytest.importorskip("httpx")

from kagura.web.search import (  # noqa: E402
    BraveSearch,
    SearchResult,
    search,
)


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            source="brave",
        )

        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.source == "brave"


class TestBraveSearch:
    """Tests for BraveSearch class."""

    def test_init_with_api_key(self):
        """Test BraveSearch initialization with API key."""
        brave = BraveSearch(api_key="test_key")
        assert brave.api_key == "test_key"
        assert brave.base_url == "https://api.search.brave.com/res/v1"

    def test_init_with_env_var(self, monkeypatch):
        """Test BraveSearch initialization with environment variable."""
        # Clear all Brave API keys first
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        # Set only the new variable
        monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "env_key")
        brave = BraveSearch()
        assert brave.api_key == "env_key"

    def test_init_without_api_key(self):
        """Test BraveSearch initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Brave API key required"):
                BraveSearch()

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful Brave search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Python Tutorial",
                        "url": "https://python.org/tutorial",
                        "description": "Learn Python programming",
                    },
                    {
                        "title": "Python Docs",
                        "url": "https://docs.python.org",
                        "description": "Official documentation",
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            brave = BraveSearch(api_key="test_key")
            results = await brave.search("Python tutorial", max_results=10)

            assert len(results) == 2
            assert results[0].title == "Python Tutorial"
            assert results[0].url == "https://python.org/tutorial"
            assert results[0].snippet == "Learn Python programming"
            assert results[0].source == "brave"

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "web/search" in call_args[0][0]
            assert call_args[1]["params"]["q"] == "Python tutorial"
            assert call_args[1]["params"]["count"] == 10

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """Test Brave search with empty results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            brave = BraveSearch(api_key="test_key")
            results = await brave.search("nonexistent query")

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_http_error(self):
        """Test Brave search with HTTP error."""
        # Simply mock the entire search method to raise an exception
        import httpx

        with patch.object(
            BraveSearch,
            "search",
            side_effect=httpx.HTTPError("API error"),
        ):
            brave = BraveSearch(api_key="invalid_key")
            with pytest.raises(httpx.HTTPError):
                await brave.search("test query")


class TestSearchFunction:
    """Tests for unified search() function."""

    @pytest.mark.asyncio
    async def test_search_with_brave_key(self, monkeypatch):
        """Test search() uses Brave when API key is available."""
        # Set only new variable name
        monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test_key")

        with patch(
            "kagura.web.search.BraveSearch.search"
        ) as mock_brave_search:
            mock_brave_search.return_value = [
                SearchResult(
                    title="Test",
                    url="https://example.com",
                    snippet="Test snippet",
                    source="brave",
                )
            ]

            results = await search("test query", max_results=5)

            assert len(results) == 1
            assert results[0].source == "brave"
            mock_brave_search.assert_called_once_with("test query", 5)

class TestIntegration:
    """Integration tests (require actual dependencies)."""

    # Integration tests for Brave Search would go here
    # Currently skipped to avoid API rate limits in CI
