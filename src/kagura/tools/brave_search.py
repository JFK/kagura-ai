"""Brave Search integration for Kagura AI."""

from __future__ import annotations

import json
from typing import Literal

from kagura import tool
from kagura.config.env import get_brave_search_api_key


@tool
async def brave_web_search(query: str, count: int = 5) -> str:
    """Search the web using Brave Search API.

    Automatically handles all languages. Returns formatted text results.

    Args:
        query: Search query (any language)
        count: Number of results to return (default: 5, max: 20)

    Returns:
        Formatted text with search results

    Example:
        >>> results = await brave_web_search("Python programming", count=3)
        >>> results = await brave_web_search("熊本 イベント", count=5)
    """
    # Use fixed params (US, en) - API auto-detects query language
    country = "US"
    search_lang = "en"
    try:
        from brave_search_python_client import (  # type: ignore[import-untyped]
            BraveSearch,
            WebSearchRequest,
        )
    except ImportError:
        return json.dumps(
            {
                "error": "brave-search-python-client is required",
                "install": "uv add brave-search-python-client",
            },
            indent=2,
        )

    # Check API key
    api_key = get_brave_search_api_key()
    if not api_key:
        return json.dumps(
            {
                "error": "BRAVE_SEARCH_API_KEY environment variable not set",
                "help": "Get API key from https://brave.com/search/api/",
            },
            indent=2,
        )

    try:
        # Create client
        client = BraveSearch(api_key=api_key)

        # Create search request
        request = WebSearchRequest(  # type: ignore[call-arg,arg-type]
            q=query,
            count=min(count, 20),
            country=country,  # type: ignore[arg-type]
            search_lang=search_lang,
        )

        # Execute search
        response = await client.web(request)  # type: ignore[arg-type]

        # Extract results
        results = []
        if hasattr(response, "web") and hasattr(response.web, "results"):
            for item in response.web.results[:count]:  # type: ignore[union-attr]
                results.append(
                    {
                        "title": getattr(item, "title", ""),
                        "url": getattr(item, "url", ""),
                        "description": getattr(item, "description", ""),
                    }
                )

        # Format as readable text instead of JSON
        if not results:
            return f"No results found for: {query}"

        formatted = [f"Search results for: {query}\n"]
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {result['title']}")
            formatted.append(f"   {result['url']}")
            formatted.append(f"   {result['description']}\n")

        # Add instruction to LLM
        formatted.append("---")
        formatted.append(
            "IMPORTANT: These are the web search results. "
            "Use this information to answer the user's question. "
            "Do NOT perform additional searches unless the user explicitly "
            "asks for more or different information."
        )

        return "\n".join(formatted)

    except Exception as e:
        return f"Search failed: {str(e)}"


@tool
async def brave_news_search(
    query: str,
    count: int = 5,
    country: str = "US",
    search_lang: str = "en",
    freshness: Literal["pd", "pw", "pm", "py"] | None = None,
) -> str:
    """Search news using Brave Search API.

    Args:
        query: Search query
        count: Number of results (default: 5, max: 20)
        country: Country code (default: "US", "JP" for Japan)
        search_lang: Search language (default: "en", "ja" for Japanese)
        freshness: Time filter - "pd" (24h), "pw" (week), "pm" (month), "py" (year)

    Returns:
        JSON string with news results

    Example:
        >>> results = await brave_news_search("AI technology", freshness="pw")
    """
    try:
        from brave_search_python_client import (  # type: ignore[import-untyped]
            BraveSearch,
            NewsSearchRequest,
        )
    except ImportError:
        return json.dumps(
            {
                "error": "brave-search-python-client is required",
                "install": "uv add brave-search-python-client",
            },
            indent=2,
        )

    # Check API key
    api_key = get_brave_search_api_key()
    if not api_key:
        return json.dumps(
            {
                "error": "BRAVE_SEARCH_API_KEY environment variable not set",
                "help": "Get API key from https://brave.com/search/api/",
            },
            indent=2,
        )

    try:
        # Create client
        client = BraveSearch(api_key=api_key)

        # Create search request
        kwargs = {
            "q": query,
            "count": min(count, 20),
            "country": country,
            "search_lang": search_lang,
        }
        if freshness:
            kwargs["freshness"] = freshness

        request = NewsSearchRequest(**kwargs)  # type: ignore[arg-type]

        # Execute search
        response = await client.news(request)

        # Extract results
        results = []
        if hasattr(response, "results"):
            for item in response.results[:count]:
                results.append(
                    {
                        "title": getattr(item, "title", ""),
                        "url": getattr(item, "url", ""),
                        "description": getattr(item, "description", ""),
                        "age": getattr(item, "age", ""),
                    }
                )

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"News search failed: {str(e)}"}, indent=2)
