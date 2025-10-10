"""Web integration module for Kagura AI.

Provides web search and scraping capabilities.
"""

from kagura.web.search import (
    BraveSearch,
    DuckDuckGoSearch,
    SearchResult,
    search,
)

__all__ = [
    "BraveSearch",
    "DuckDuckGoSearch",
    "SearchResult",
    "search",
]
