"""Web and search MCP tools - Issue #720 final configuration.

Provides 4 web search tools (3 Brave + 1 YouTube):
- brave_web_search: Web search via Brave Search API
- brave_news_search: News search via Brave Search API
- arxiv_search: Academic paper search (in academic/ package)
- youtube_transcript: YouTube video transcript retrieval

All tools are safe for remote access (external API calls only).
"""

from kagura.mcp.tools.web.brave_search import (
    brave_news_search,
    brave_web_search,
)
from kagura.mcp.tools.web.fact_check import fact_check_claim
from kagura.mcp.tools.web.web import web_scrape
from kagura.mcp.tools.web.youtube import youtube_transcript

__all__ = [
    # Brave Search (2)
    "brave_web_search",
    "brave_news_search",
    # YouTube (1)
    "youtube_transcript",
    # Utilities (kept for compatibility)
    "fact_check_claim",
    "web_scrape",
]
