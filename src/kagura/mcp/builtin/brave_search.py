"""Brave Search integration for Kagura AI."""
# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

import json
import logging
from typing import Any

from kagura import tool
from kagura.config.env import (
    get_brave_search_api_key,
    get_search_cache_enabled,
    get_search_cache_ttl,
)
from kagura.mcp.builtin.cache import SearchCache
from kagura.mcp.builtin.common import setup_external_library_logging

# Setup logger
logger = logging.getLogger(__name__)

# Configure brave_search_python_client logging using common utilities
setup_external_library_logging(
    library_name="brave_search_python_client",
    env_var_name="BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME",
    filename="brave_search_python_client.log",
)

# Global search cache instance
_search_cache: SearchCache | None = None


def _get_cache() -> SearchCache | None:
    """Get or create search cache instance based on environment config

    Returns:
        SearchCache instance if caching is enabled, None otherwise
    """
    global _search_cache

    if not get_search_cache_enabled():
        return None

    if _search_cache is None:
        _search_cache = SearchCache(
            default_ttl=get_search_cache_ttl(),
            max_size=1000,
        )

    return _search_cache


@tool
async def brave_web_search(query: str, count: int = 5) -> str:
    """Search the web using Brave Search API.

    Use this tool when:
    - User asks for current/latest/recent information
    - Information may have changed since knowledge cutoff
    - Real-time data is needed (news, prices, events)
    - Verification of facts is requested
    - User explicitly asks to "search" or "look up" something

    Do NOT use for:
    - General knowledge questions answerable from training data
    - Historical facts that don't change
    - Stable information (definitions, concepts)
    - Mathematical calculations
    - Code generation or debugging

    Automatically handles all languages. Returns formatted text results.
    Results are cached (if enabled) to reduce API calls and improve response times.

    Args:
        query: Search query in any language. Keep it concise (1-6 words recommended)
        count: Number of results to return (default: 5, max: 20)

    Returns:
        Formatted text with search results

    Example:
        # Latest information
        query="Python 3.13 release date", count=3

        # Event search (any language)
        query="熊本 イベント 今週", count=5

        # Price check
        query="Bitcoin price", count=3

    Note:
        Caching can be controlled via environment variables:
        - ENABLE_SEARCH_CACHE: Enable/disable caching (default: true)
        - SEARCH_CACHE_TTL: Cache TTL in seconds (default: 3600)
    """
    # Ensure count is int (LLM might pass as string)
    if isinstance(count, str):
        try:
            count = int(count)
        except ValueError:
            count = 5  # Default fallback

    # Check cache first (if enabled)
    cache = _get_cache()
    if cache:
        logger.debug(f"Cache enabled, checking for query: '{query}' (count={count})")
        cached_result = await cache.get(query, count)
        if cached_result:
            # Cache hit - return instantly
            logger.info(f"Cache HIT for query: '{query}' (count={count})")
            try:
                from rich.console import Console

                console = Console()
                console.print("[green][OK] Cache hit (instant) - No API call needed[/]")
            except ImportError:
                pass

            # Add cache indicator for debugging/transparency
            return f"[CACHED SEARCH RESULT - Retrieved instantly]\n\n{cached_result}"
        else:
            logger.info(f"Cache MISS for query: '{query}' (count={count})")

    # Cache miss or disabled - proceed with API call
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

        result = "\n".join(formatted)

        # Store in cache (if enabled)
        if cache:
            logger.info(f"Caching search result for query: '{query}' (count={count})")
            await cache.set(query, result, count)
            logger.debug(f"Cache stats: {cache.stats()}")

        return result

    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        logger.error(f"Search error for query '{query}': {str(e)}")
        # Don't cache errors
        return error_msg


# Supported country/language combinations for Brave News API
# Based on typical News API limitations (English-speaking countries mainly)
_NEWS_COUNTRY_PRESETS = {
    "US": "en",  # United States - English
    "GB": "en",  # United Kingdom - English
    "CA": "en",  # Canada - English
    "AU": "en",  # Australia - English
    "NZ": "en",  # New Zealand - English
    "IE": "en",  # Ireland - English
    # Limited support for non-English countries
}


@tool
async def brave_news_search(
    query: str,
    count: int = 5,
    country: str = "US",
    search_lang: str = "en",
    freshness: str | None = None,
) -> str:
    """Search recent news articles using Brave Search API.

    Use this tool specifically for:
    - Breaking news and current events
    - Recent developments in specific topics
    - Time-sensitive information from news sources
    - User explicitly asks for "news" or "latest news"

    ⚠️ IMPORTANT: News API primarily supports English-speaking countries
    - For non-English news, use brave_web_search or web_search instead
    - Supported countries: US, GB, CA, AU, NZ, IE (English only)
    - For Japanese/other language news → use brave_web_search

    Args:
        query: Search query for news articles
        count: Number of results (default: 5, max: 20)
        country: Country code (default: "US")
            Supported: US, GB, CA, AU, NZ, IE
            For other countries, automatically falls back to US
        search_lang: Search language (default: "en")
            Currently only "en" is well-supported for news
        freshness: Time filter (optional):
            - "pd" (past day / 24 hours)
            - "pw" (past week)
            - "pm" (past month)
            - "py" (past year)
            - None (all time)

    Returns:
        JSON string with news results

    Examples:
        # Breaking US news (recommended)
        query="AI regulation", freshness="pd"

        # UK news
        query="tech industry", country="GB"

        # For Japanese news, use brave_web_search instead:
        brave_web_search(query="AI ニュース")
    """
    # Ensure count is int (LLM might pass as string)
    if isinstance(count, str):
        try:
            count = int(count)
        except ValueError:
            count = 5  # Default fallback

    # Validate and auto-correct country/language combination
    if country not in _NEWS_COUNTRY_PRESETS:
        logger.info(
            f"News API: Country '{country}' → Using 'US' (English news). "
            f"Supported countries: {list(_NEWS_COUNTRY_PRESETS.keys())}. "
            f"Tip: For non-English news, use brave_web_search() instead."
        )
        country = "US"
        search_lang = "en"
    else:
        # Use preset language for country
        search_lang = _NEWS_COUNTRY_PRESETS[country]

    # Validate freshness parameter
    valid_freshness = ["pd", "pw", "pm", "py"]
    if freshness and freshness not in valid_freshness:
        logger.warning(f"Invalid freshness value '{freshness}', using None (all time)")
        freshness = None

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
                # Clean thumbnail if present but empty
                thumbnail = getattr(item, "thumbnail", None)
                thumbnail_data = None
                if thumbnail:
                    # Handle empty thumbnail src (422 error cause)
                    thumb_src = str(getattr(thumbnail, "src", ""))
                    if thumb_src:  # Only include if not empty
                        thumbnail_data = {
                            "src": thumb_src,
                            "width": getattr(thumbnail, "width", None),
                            "height": getattr(thumbnail, "height", None),
                        }

                result_item: dict[str, Any] = {
                    "title": str(getattr(item, "title", "")),
                    "url": str(getattr(item, "url", "")),  # Convert HttpUrl to str
                    "description": str(getattr(item, "description", "")),
                    "age": str(getattr(item, "age", "")),
                }

                # Only add thumbnail if it has valid data
                if thumbnail_data:
                    result_item["thumbnail"] = thumbnail_data

                results.append(result_item)

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        error_msg = str(e)

        # Provide helpful error messages
        if "422" in error_msg or "Unprocessable" in error_msg:
            return json.dumps(
                {
                    "error": "News search API error (422)",
                    "details": error_msg,
                    "suggestions": [
                        "Try with country='US' and search_lang='en'",
                        "Some country/language combinations may not be supported",
                        "For Japanese news, try web_search instead",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )

        return json.dumps(
            {"error": f"News search failed: {error_msg}"},
            ensure_ascii=False,
            indent=2,
        )


@tool
async def brave_image_search(
    query: str,
    count: int = 10,
    safesearch: str = "moderate",
) -> str:
    """Search for images using Brave Search API.

    Use this tool when:
    - User asks for images, photos, or pictures
    - Visual content is needed
    - User explicitly requests image search
    - Need illustrations or examples

    Args:
        query: Search query for images
        count: Number of results (default: 10, max: 200)
        safesearch: Safe search filtering:
            - "off": No filtering
            - "moderate": Filter explicit content (default)
            - "strict": Strict filtering

    Returns:
        JSON string with image results including URLs, thumbnails, titles

    Examples:
        # Search for images
        query="python programming", count=10

        # Strict filtering
        query="nature photos", safesearch="strict"
    """
    # Ensure count is int
    if isinstance(count, str):
        try:
            count = int(count)
        except ValueError:
            count = 10

    # Validate safesearch
    valid_safesearch = ["off", "moderate", "strict"]
    if safesearch not in valid_safesearch:
        safesearch = "moderate"

    try:
        from brave_search_python_client import (  # type: ignore[import-untyped]
            BraveSearch,
            ImageSearchRequest,
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
        request = ImageSearchRequest(  # type: ignore[call-arg,misc]
            q=query,
            count=min(count, 200),
            safesearch=safesearch,  # type: ignore[arg-type]
        )

        # Execute search
        response = await client.images(request)  # type: ignore[arg-type]

        # Extract results
        results = []
        if hasattr(response, "results"):
            for item in response.results[:count]:  # type: ignore[union-attr]
                results.append(
                    {
                        "title": str(getattr(item, "title", "")),
                        "url": str(getattr(item, "url", "")),
                        "thumbnail": str(getattr(item, "thumbnail", "")),
                        "source": str(getattr(item, "source", "")),
                    }
                )

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps(
            {"error": f"Image search failed: {str(e)}"},
            ensure_ascii=False,
            indent=2,
        )


@tool
async def brave_video_search(
    query: str,
    count: int = 10,
    safesearch: str = "moderate",
) -> str:
    """Search for videos using Brave Search API.

    Use this tool when:
    - User asks for videos or video content
    - Need tutorial or demonstration videos
    - User explicitly requests video search
    - Looking for visual explanations

    Args:
        query: Search query for videos
        count: Number of results (default: 10, max: 50)
        safesearch: Safe search filtering:
            - "off": No filtering
            - "moderate": Filter explicit content (default)
            - "strict": Strict filtering

    Returns:
        JSON string with video results including URLs, thumbnails, titles, duration

    Examples:
        # Search for videos
        query="python tutorial", count=10

        # Educational content
        query="machine learning basics", safesearch="strict"
    """
    # Ensure count is int
    if isinstance(count, str):
        try:
            count = int(count)
        except ValueError:
            count = 10

    # Validate safesearch
    valid_safesearch = ["off", "moderate", "strict"]
    if safesearch not in valid_safesearch:
        safesearch = "moderate"

    try:
        from brave_search_python_client import (  # type: ignore[import-untyped]
            BraveSearch,
            VideoSearchRequest,
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
        request = VideoSearchRequest(  # type: ignore[call-arg,misc]
            q=query,
            count=min(count, 50),
            safesearch=safesearch,  # type: ignore[arg-type]
        )

        # Execute search
        response = await client.videos(request)  # type: ignore[arg-type]

        # Extract results
        results = []
        if hasattr(response, "results"):
            for item in response.results[:count]:  # type: ignore[union-attr]
                results.append(
                    {
                        "title": str(getattr(item, "title", "")),
                        "url": str(getattr(item, "url", "")),
                        "thumbnail": str(getattr(item, "thumbnail", "")),
                        "duration": str(getattr(item, "duration", "")),
                        "creator": str(getattr(item, "creator", "")),
                        "view_count": str(getattr(item, "view_count", "")),
                    }
                )

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps(
            {"error": f"Video search failed: {str(e)}"},
            ensure_ascii=False,
            indent=2,
        )
