"""Tests for web MCP tools."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from kagura.mcp.builtin.web import web_scrape, web_search


class TestWebSearch:
    """Test web_search MCP tool."""

    @pytest.mark.asyncio
    async def test_web_search_success(self) -> None:
        """Test web_search returns valid JSON when search succeeds."""
        # Mock brave_web_search (web_search is now an alias)
        mock_result = json.dumps(
            [
                {
                    "title": "Python Tutorial",
                    "url": "https://example.com/python",
                    "snippet": "Learn Python programming",
                    "source": "brave",
                },
                {
                    "title": "FastAPI Guide",
                    "url": "https://example.com/fastapi",
                    "snippet": "Modern web framework",
                    "source": "brave",
                },
            ]
        )

        # Mock brave_web_search since web_search delegates to it
        with patch(
            "kagura.mcp.builtin.brave_search.brave_web_search",
            new_callable=AsyncMock,
        ) as mock_brave:
            mock_brave.return_value = mock_result

            result = await web_search("python tutorial", max_results=2)

            # Verify result is valid JSON
            parsed = json.loads(result)
            assert isinstance(parsed, list)
            assert len(parsed) == 2

            # Verify first result structure
            assert parsed[0]["title"] == "Python Tutorial"
            assert parsed[0]["url"] == "https://example.com/python"
            assert parsed[0]["snippet"] == "Learn Python programming"
            assert parsed[0]["source"] == "brave"

            # Verify brave_web_search was called correctly
            mock_brave.assert_called_once_with(query="python tutorial", count=2)

    @pytest.mark.asyncio
    async def test_web_search_empty_results(self) -> None:
        """Test web_search handles empty results."""
        # Mock brave_web_search returning empty list
        mock_result = json.dumps([])

        with patch(
            "kagura.mcp.builtin.brave_search.brave_web_search",
            new_callable=AsyncMock,
        ) as mock_brave:
            mock_brave.return_value = mock_result

            result = await web_search("nonexistent query")

            # Verify result is valid JSON
            parsed = json.loads(result)
            assert isinstance(parsed, list)
            assert len(parsed) == 0

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ImportError testing is complex with dynamic imports")
    async def test_web_search_import_error(self) -> None:
        """Test web_search handles ImportError gracefully.

        Note: This test is skipped because mocking ImportError in a way that
        doesn't break other imports (like Pydantic) is complex. The error
        handling path is tested manually.
        """
        pass

    @pytest.mark.asyncio
    async def test_web_search_japanese_characters(self) -> None:
        """Test web_search handles Japanese characters correctly."""
        # Mock brave_web_search with Japanese content
        mock_result = json.dumps(
            [
                {
                    "title": "Pythonチュートリアル",
                    "url": "https://example.jp/python",
                    "snippet": "Python プログラミングを学ぶ",
                    "source": "brave",
                }
            ],
            ensure_ascii=False,
        )

        with patch(
            "kagura.mcp.builtin.brave_search.brave_web_search",
            new_callable=AsyncMock,
        ) as mock_brave:
            mock_brave.return_value = mock_result

            result = await web_search("Python 日本語")

            # Verify result is valid JSON with Japanese characters
            parsed = json.loads(result)
            assert parsed[0]["title"] == "Pythonチュートリアル"
            assert parsed[0]["snippet"] == "Python プログラミングを学ぶ"

            # Verify the result string contains Japanese characters (not escaped)
            assert "Pythonチュートリアル" in result


class TestWebScrape:
    """Test web_scrape MCP tool."""

    @pytest.mark.asyncio
    async def test_web_scrape_success(self) -> None:
        """Test web_scrape returns content when scraping succeeds."""
        from kagura.web import WebScraper

        mock_scraper = AsyncMock(spec=WebScraper)
        mock_scraper.scrape.return_value = [
            "Heading 1",
            "Paragraph text",
            "Another paragraph",
        ]

        with patch("kagura.web.WebScraper", return_value=mock_scraper):
            result = await web_scrape("https://example.com", selector="article")

            # Verify result is newline-separated text
            assert "Heading 1" in result
            assert "Paragraph text" in result
            assert "Another paragraph" in result

            # Verify scraper was called correctly
            mock_scraper.scrape.assert_called_once_with(
                "https://example.com", selector="article"
            )

    @pytest.mark.asyncio
    async def test_web_scrape_default_selector(self) -> None:
        """Test web_scrape uses default selector 'body'."""
        from kagura.web import WebScraper

        mock_scraper = AsyncMock(spec=WebScraper)
        mock_scraper.scrape.return_value = ["Content"]

        with patch("kagura.web.WebScraper", return_value=mock_scraper):
            await web_scrape("https://example.com")

            # Verify default selector 'body' was used
            mock_scraper.scrape.assert_called_once_with(
                "https://example.com", selector="body"
            )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ImportError testing is complex with dynamic imports")
    async def test_web_scrape_import_error(self) -> None:
        """Test web_scrape handles ImportError gracefully.

        Note: This test is skipped because mocking ImportError in a way that
        doesn't break other imports (like Pydantic) is complex. The error
        handling path is tested manually.
        """
        pass
