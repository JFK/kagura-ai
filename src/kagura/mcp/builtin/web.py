"""Built-in MCP tools for Web operations

Exposes Kagura's web search and scraping features via MCP.
"""

from __future__ import annotations

import json

from kagura import tool


@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Brave Search API

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        JSON string of search results
    """
    try:
        from kagura.web import search

        results = await search(query, max_results=max_results)
        return json.dumps(results, indent=2)
    except ImportError:
        return json.dumps(
            {
                "error": "Web search requires 'web' extra. "
                "Install with: pip install kagura-ai[web]"
            }
        )


@tool
async def web_scrape(url: str, selector: str = "body") -> str:
    """Scrape web page content

    Args:
        url: URL to scrape
        selector: CSS selector (default: body)

    Returns:
        Page text content or error message
    """
    try:
        from kagura.web import WebScraper

        scraper = WebScraper()
        results = await scraper.scrape(url, selector=selector)
        return "\n".join(results)
    except ImportError:
        return (
            "Error: Web scraping requires 'web' extra. "
            "Install with: pip install kagura-ai[web]"
        )
