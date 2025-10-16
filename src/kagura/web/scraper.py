"""Web scraping functionality with BeautifulSoup."""

import logging
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for web requests."""

    def __init__(self, min_delay: float = 1.0):
        """Initialize rate limiter.

        Args:
            min_delay: Minimum delay between requests in seconds (default: 1.0)
        """
        self.min_delay = min_delay
        self.last_request_time: dict[str, float] = {}

    async def wait(self, domain: str) -> None:
        """Wait if necessary to respect rate limit.

        Args:
            domain: Domain to rate limit
        """
        import asyncio

        current_time = time.time()
        last_time = self.last_request_time.get(domain, 0)
        elapsed = current_time - last_time

        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
            await asyncio.sleep(wait_time)

        self.last_request_time[domain] = time.time()


class RobotsTxtChecker:
    """Check robots.txt compliance."""

    def __init__(self, user_agent: str = "KaguraAI/1.0"):
        """Initialize robots.txt checker.

        Args:
            user_agent: User agent string
        """
        self.user_agent = user_agent
        self._cache: dict[str, bool] = {}

    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if URL can be fetched, False otherwise
        """
        # Extract domain
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Check cache
        cache_key = f"{domain}:{parsed.path}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Try to parse robots.txt
            try:
                from urllib.robotparser import RobotFileParser
            except ImportError:
                logger.warning("urllib.robotparser not available, allowing all URLs")
                return True

            robots_url = f"{domain}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)

            # Fetch robots.txt synchronously (RobotFileParser is sync)
            import asyncio

            await asyncio.get_event_loop().run_in_executor(None, rp.read)

            # Check if URL can be fetched
            can_fetch = rp.can_fetch(self.user_agent, url)
            self._cache[cache_key] = can_fetch

            if not can_fetch:
                logger.warning(f"robots.txt disallows fetching: {url}")

            return can_fetch

        except Exception as e:
            logger.debug(f"Error checking robots.txt for {url}: {e}")
            # On error, allow fetching (fail open)
            return True


class WebScraper:
    """Web scraper with BeautifulSoup.

    Features:
    - HTML fetching with httpx
    - Text extraction with BeautifulSoup
    - CSS selector support
    - robots.txt compliance
    - Rate limiting
    """

    def __init__(
        self,
        user_agent: str = "KaguraAI/1.0",
        respect_robots_txt: bool = True,
        rate_limit_delay: float = 1.0,
    ):
        """Initialize web scraper.

        Args:
            user_agent: User agent string
            respect_robots_txt: Whether to check robots.txt before fetching
            rate_limit_delay: Minimum delay between requests to same domain (seconds)
        """
        self.user_agent = user_agent
        self.respect_robots_txt = respect_robots_txt
        self.rate_limiter = RateLimiter(min_delay=rate_limit_delay)
        self.robots_checker = RobotsTxtChecker(user_agent=user_agent)

    async def fetch(self, url: str, timeout: float = 30.0) -> str:
        """Fetch webpage HTML.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            HTML content as string

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If robots.txt disallows fetching
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "httpx is required for web scraping. "
                "Install with: pip install kagura-ai[web]"
            ) from e

        # Check robots.txt
        if self.respect_robots_txt:
            can_fetch = await self.robots_checker.can_fetch(url)
            if not can_fetch:
                raise ValueError(
                    f"robots.txt disallows fetching this URL: {url}. "
                    "Set respect_robots_txt=False to bypass (not recommended)."
                )

        # Apply rate limiting
        parsed = urlparse(url)
        domain = parsed.netloc
        await self.rate_limiter.wait(domain)

        # Fetch URL
        async with httpx.AsyncClient() as client:
            headers = {"User-Agent": self.user_agent}
            response = await client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            logger.info(f"Fetched {url} ({len(response.text)} chars)")
            return response.text

    async def fetch_text(self, url: str, timeout: float = 30.0) -> str:
        """Fetch webpage and extract text content.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Extracted text content

        Raises:
            httpx.HTTPError: If request fails
            ImportError: If BeautifulSoup not installed
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError as e:
            raise ImportError(
                "BeautifulSoup is required for text extraction. "
                "Install with: pip install kagura-ai[web]"
            ) from e

        html = await self.fetch(url, timeout=timeout)

        # Parse HTML and extract text
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        logger.info(f"Extracted text from {url} ({len(text)} chars)")
        return text

    async def scrape(self, url: str, selector: str, timeout: float = 30.0) -> list[str]:
        """Scrape webpage with CSS selector.

        Args:
            url: URL to scrape
            selector: CSS selector
            timeout: Request timeout in seconds

        Returns:
            List of matching element texts

        Raises:
            httpx.HTTPError: If request fails
            ImportError: If BeautifulSoup not installed
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError as e:
            raise ImportError(
                "BeautifulSoup is required for scraping. "
                "Install with: pip install kagura-ai[web]"
            ) from e

        html = await self.fetch(url, timeout=timeout)

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Select elements
        elements = soup.select(selector)

        # Extract text from each element
        results = [elem.get_text(strip=True) for elem in elements]

        logger.info(
            f"Scraped {len(results)} elements from {url} " f"with selector '{selector}'"
        )
        return results


__all__ = ["WebScraper", "RobotsTxtChecker", "RateLimiter"]
