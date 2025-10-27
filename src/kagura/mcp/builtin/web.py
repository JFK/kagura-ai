"""Built-in MCP tools for Web operations

Exposes Kagura's web search and scraping features via MCP.
"""

from __future__ import annotations

from kagura import tool


@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Brave Search API

    NOTE: This is an alias for brave_web_search for backward compatibility.
    brave_web_search has better features (caching, detailed docs).

    Args:
        query: Search query
        max_results: Maximum number of results (maps to count parameter)

    Returns:
        JSON string of search results

    Recommendation: Use brave_web_search directly for:
    - Search result caching
    - Better parameter names
    - More detailed documentation
    """
    # Delegate to brave_web_search (better implementation)
    from kagura.mcp.builtin.brave_search import brave_web_search

    return await brave_web_search(query=query, count=max_results)


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
