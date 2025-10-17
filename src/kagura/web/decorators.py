"""Web-enabled decorator for agents."""

import functools
from typing import Awaitable, Callable, Optional, ParamSpec, TypeVar

from kagura.web.search import search

P = ParamSpec("P")
T = TypeVar("T")


async def web_search(query: str, max_results: int = 10) -> str:
    """Search the web for information.

    Args:
        query: Search query
        max_results: Maximum number of results to return (default: 10)

    Returns:
        Formatted search results as a string
    """
    results = await search(query, max_results)

    if not results:
        return f"No results found for: {query}"

    # Format results for LLM consumption
    formatted = [f"Search results for: {query}\n"]
    for i, result in enumerate(results, 1):
        formatted.append(f"{i}. {result.title}")
        formatted.append(f"   URL: {result.url}")
        formatted.append(f"   {result.snippet}")
        formatted.append(f"   Source: {result.source}\n")

    return "\n".join(formatted)


def enable(
    fn: Callable[P, Awaitable[T]] | None = None,
    *,
    search_engine: Optional[str] = None,
) -> (
    Callable[P, Awaitable[T]]
    | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]
):
    """Enable web search capabilities for an agent.

    This decorator should be used in combination with @agent decorator.
    It automatically injects the web_search tool into the agent's available tools.

    Args:
        fn: Function to decorate
        search_engine: Search engine to use ("brave", "duckduckgo", or None for auto)
            Note: Currently ignored - auto-selection based on API key availability

    Returns:
        Decorated function with web search capabilities

    Example:
        @agent(model="gpt-5-mini")
        @web.enable()
        async def research_agent(topic: str) -> str:
            '''Research {{ topic }} using web search.
            Use web_search(query) to search for information.'''
            pass

        result = await research_agent("Python async programming")
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Store web search configuration
        func._web_enabled = True  # type: ignore
        func._web_search_engine = search_engine  # type: ignore
        func._web_search_tool = web_search  # type: ignore

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # The actual web search injection happens in @agent decorator
            # via the tools parameter
            return await func(*args, **kwargs)

        # Copy web metadata to wrapper
        wrapper._web_enabled = True  # type: ignore
        wrapper._web_search_engine = search_engine  # type: ignore
        wrapper._web_search_tool = web_search  # type: ignore

        return wrapper  # type: ignore

    return decorator if fn is None else decorator(fn)


__all__ = ["enable", "web_search"]
