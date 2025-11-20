"""Built-in MCP tools for Web operations

Exposes Kagura's web scraping features via MCP.

Note: For web search, use brave_web_search from brave_search.py
"""

from __future__ import annotations

from kagura import tool


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
