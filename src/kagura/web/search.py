"""Web search functionality with Brave and DuckDuckGo."""

import logging
from dataclasses import dataclass
from typing import Optional

from kagura.config.env import get_brave_search_api_key

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Web search result."""

    title: str
    url: str
    snippet: str
    source: str


class BraveSearch:
    """Brave Search API client.

    Requires BRAVE_SEARCH_API_KEY environment variable.
    Get API key at: https://brave.com/search/api/
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Brave Search client.

        Args:
            api_key: Brave API key (uses BRAVE_SEARCH_API_KEY env var if None)

        Raises:
            ValueError: If API key not provided
        """
        self.api_key = api_key or get_brave_search_api_key()
        if not self.api_key:
            raise ValueError(
                "Brave API key required. Set BRAVE_SEARCH_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.base_url = "https://api.search.brave.com/res/v1"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search the web using Brave Search API.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "httpx is required for web search. "
                "Install with: pip install kagura-ai[web]"
            ) from e

        async with httpx.AsyncClient() as client:
            # api_key is guaranteed to be str here (checked in __init__)
            headers: dict[str, str] = {"X-Subscription-Token": self.api_key}  # type: ignore[dict-item]
            response = await client.get(
                f"{self.base_url}/web/search",
                headers=headers,
                params={"q": query, "count": max_results},
                timeout=30.0,
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("web", {}).get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                        source="brave",
                    )
                )

            logger.info(f"Brave Search: Found {len(results)} results for '{query}'")
            return results


class DuckDuckGoSearch:
    """DuckDuckGo search (no API key required).

    Uses duckduckgo-search library.
    """

    def __init__(self):
        """Initialize DuckDuckGo Search client."""
        pass

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search the web using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results

        Raises:
            ImportError: If duckduckgo-search not installed
        """
        try:
            from duckduckgo_search import DDGS
        except ImportError as e:
            raise ImportError(
                "duckduckgo-search is required for DuckDuckGo search. "
                "Install with: pip install kagura-ai[web]"
            ) from e

        results = []

        # DuckDuckGo search is synchronous, run in executor
        import asyncio

        def _sync_search():
            with DDGS() as ddgs:
                search_results = []
                try:
                    for r in ddgs.text(query, max_results=max_results):
                        search_results.append(
                            SearchResult(
                                title=r.get("title", ""),
                                url=r.get("href", ""),
                                snippet=r.get("body", ""),
                                source="duckduckgo",
                            )
                        )
                except Exception as e:
                    logger.error(f"DuckDuckGo search error: {e}")
                return search_results

        results = await asyncio.get_event_loop().run_in_executor(None, _sync_search)

        logger.info(f"DuckDuckGo: Found {len(results)} results for '{query}'")
        return results


async def search(query: str, max_results: int = 10) -> list[SearchResult]:
    """Search the web (auto-select engine).

    Automatically selects search engine based on available API keys:
    1. Brave Search (if BRAVE_SEARCH_API_KEY is set)
    2. DuckDuckGo (fallback, no API key needed)

    Args:
        query: Search query
        max_results: Maximum number of results to return

    Returns:
        List of search results

    Example:
        >>> results = await search("Python tutorial", max_results=5)
        >>> for r in results:
        ...     print(f"{r.title}: {r.url}")
    """
    if get_brave_search_api_key():
        logger.info("Using Brave Search")
        engine = BraveSearch()
    else:
        logger.info("Using DuckDuckGo (no API key required)")
        engine = DuckDuckGoSearch()

    return await engine.search(query, max_results)


__all__ = ["SearchResult", "BraveSearch", "DuckDuckGoSearch", "search"]
