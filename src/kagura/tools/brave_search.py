"""Brave Search integration for Kagura AI."""

from __future__ import annotations

import json
from typing import Literal

from kagura import tool
from kagura.config.env import get_brave_search_api_key


@tool
async def brave_web_search(
    query: str,
    count: int = 5,
    country: str = "US",
    search_lang: str = "en",
) -> str:
    """Search the web using Brave Search API.

    Args:
        query: Search query
        count: Number of results to return (default: 5, max: 20)
        country: Country code for results (default: "US", "JP" for Japan)
        search_lang: Search language (default: "en", "ja" for Japanese)

    Returns:
        JSON string with search results containing:
        - title: Result title
        - url: Result URL
        - description: Result snippet

    Example:
        >>> results = await brave_web_search("Python programming", count=3)
        >>> import json
        >>> data = json.loads(results)
        >>> print(data[0]["title"])
    """
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

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"}, indent=2)


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
