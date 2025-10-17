"""Web integration module for Kagura AI.

Provides web search and scraping capabilities.
"""

from kagura.web import decorators as web
from kagura.web.decorators import enable, web_search
from kagura.web.scraper import RateLimiter, RobotsTxtChecker, WebScraper
from kagura.web.search import (
    BraveSearch,
    SearchResult,
    search,
)

__all__ = [
    "BraveSearch",
    "SearchResult",
    "search",
    "web",
    "enable",
    "web_search",
    "WebScraper",
    "RobotsTxtChecker",
    "RateLimiter",
]
