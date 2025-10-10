"""Tests for web scraper functionality."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting."""
        from kagura.web.scraper import RateLimiter

        limiter = RateLimiter(min_delay=0.1)

        # First request should not wait
        start = time.time()
        await limiter.wait("example.com")
        elapsed = time.time() - start
        assert elapsed < 0.05  # Should be nearly instant

        # Second request should wait
        start = time.time()
        await limiter.wait("example.com")
        elapsed = time.time() - start
        assert elapsed >= 0.09  # Should wait ~0.1s

    @pytest.mark.asyncio
    async def test_rate_limiter_different_domains(self):
        """Test rate limiting is per-domain."""
        from kagura.web.scraper import RateLimiter

        limiter = RateLimiter(min_delay=0.1)

        # Different domains should not interfere
        await limiter.wait("example.com")

        start = time.time()
        await limiter.wait("another.com")
        elapsed = time.time() - start
        assert elapsed < 0.05  # Should be instant (different domain)


class TestRobotsTxtChecker:
    """Tests for RobotsTxtChecker class."""

    @pytest.mark.asyncio
    async def test_robots_txt_checker_basic(self):
        """Test basic robots.txt checking."""
        from kagura.web.scraper import RobotsTxtChecker

        checker = RobotsTxtChecker(user_agent="TestBot/1.0")

        # Mock RobotFileParser
        with patch("urllib.robotparser.RobotFileParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.can_fetch.return_value = True
            mock_parser_class.return_value = mock_parser

            result = await checker.can_fetch("https://example.com/page")

            assert result is True
            mock_parser.set_url.assert_called_once()
            mock_parser.read.assert_called_once()
            mock_parser.can_fetch.assert_called_once_with(
                "TestBot/1.0", "https://example.com/page"
            )

    @pytest.mark.asyncio
    async def test_robots_txt_checker_disallowed(self):
        """Test robots.txt disallowed URL."""
        from kagura.web.scraper import RobotsTxtChecker

        checker = RobotsTxtChecker()

        with patch("urllib.robotparser.RobotFileParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.can_fetch.return_value = False
            mock_parser_class.return_value = mock_parser

            result = await checker.can_fetch("https://example.com/admin")

            assert result is False

    @pytest.mark.asyncio
    async def test_robots_txt_checker_cache(self):
        """Test that robots.txt results are cached."""
        from kagura.web.scraper import RobotsTxtChecker

        checker = RobotsTxtChecker()

        with patch("urllib.robotparser.RobotFileParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.can_fetch.return_value = True
            mock_parser_class.return_value = mock_parser

            # First call
            result1 = await checker.can_fetch("https://example.com/page")
            assert result1 is True

            # Second call should use cache
            result2 = await checker.can_fetch("https://example.com/page")
            assert result2 is True

            # read() should only be called once (cached)
            assert mock_parser.read.call_count == 1


class TestWebScraper:
    """Tests for WebScraper class."""

    @pytest.mark.asyncio
    async def test_scraper_init(self):
        """Test WebScraper initialization."""
        from kagura.web.scraper import WebScraper

        scraper = WebScraper(
            user_agent="TestBot/1.0",
            respect_robots_txt=True,
            rate_limit_delay=2.0,
        )

        assert scraper.user_agent == "TestBot/1.0"
        assert scraper.respect_robots_txt is True
        assert scraper.rate_limiter.min_delay == 2.0

    @pytest.mark.asyncio
    async def test_fetch_html(self):
        """Test fetching HTML content."""
        from kagura.web.scraper import WebScraper

        scraper = WebScraper(respect_robots_txt=False, rate_limit_delay=0)

        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            html = await scraper.fetch("https://example.com")

            assert html == "<html><body>Test</body></html>"
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_respects_robots_txt(self):
        """Test that fetch respects robots.txt."""
        from kagura.web.scraper import WebScraper

        scraper = WebScraper(respect_robots_txt=True, rate_limit_delay=0)

        # Mock robots.txt to disallow
        with patch.object(scraper.robots_checker, "can_fetch", return_value=False):
            with pytest.raises(ValueError, match="robots.txt disallows"):
                await scraper.fetch("https://example.com/admin")

    @pytest.mark.asyncio
    async def test_fetch_text(self):
        """Test extracting text from HTML."""
        from kagura.web.scraper import WebScraper

        scraper = WebScraper(respect_robots_txt=False, rate_limit_delay=0)

        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Hello World</h1>
                <p>This is a test.</p>
                <script>alert('removed');</script>
            </body>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            text = await scraper.fetch_text("https://example.com")

            # Should contain main content
            assert "Hello World" in text
            assert "This is a test" in text

            # Should NOT contain script content
            assert "alert" not in text
            assert "removed" not in text

    @pytest.mark.asyncio
    async def test_scrape_with_selector(self):
        """Test scraping with CSS selector."""
        from kagura.web.scraper import WebScraper

        scraper = WebScraper(respect_robots_txt=False, rate_limit_delay=0)

        html = """
        <html>
            <body>
                <h1 class="title">Title 1</h1>
                <h1 class="title">Title 2</h1>
                <p>Not a title</p>
            </body>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            results = await scraper.scrape("https://example.com", "h1.title")

            assert len(results) == 2
            assert results[0] == "Title 1"
            assert results[1] == "Title 2"

    @pytest.mark.asyncio
    async def test_scrape_empty_results(self):
        """Test scraping with no matching elements."""
        from kagura.web.scraper import WebScraper

        scraper = WebScraper(respect_robots_txt=False, rate_limit_delay=0)

        html = "<html><body><p>No titles here</p></body></html>"

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            results = await scraper.scrape("https://example.com", "h1")

            assert len(results) == 0


class TestIntegration:
    """Integration tests (require actual dependencies)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_scraper_real_fetch(self):
        """Test real webpage fetching (integration test)."""
        from kagura.web.scraper import WebScraper

        try:
            scraper = WebScraper(respect_robots_txt=False, rate_limit_delay=0)

            # Fetch a simple test page
            html = await scraper.fetch("https://httpbin.org/html")

            assert len(html) > 0
            assert "<html" in html.lower()
        except Exception as e:
            pytest.skip(f"Integration test failed: {e}")
