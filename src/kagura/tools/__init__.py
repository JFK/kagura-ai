"""
Built-in tools for Kagura AI

Note: All tools have been moved to kagura.mcp.builtin for better MCP integration.
Imports here are provided for backward compatibility only.

Deprecated: This module is deprecated. Use kagura.mcp.builtin instead.
"""

# Backward compatibility: All tools moved to MCP builtin
from kagura.mcp.builtin.brave_search import brave_news_search, brave_web_search
from kagura.mcp.builtin.cache import SearchCache
from kagura.mcp.builtin.youtube import get_youtube_metadata, get_youtube_transcript

__all__ = [
    # YouTube (deprecated - use kagura.mcp.builtin.youtube)
    "get_youtube_transcript",
    "get_youtube_metadata",
    # Brave Search (deprecated - use kagura.mcp.builtin.brave_search)
    "brave_web_search",
    "brave_news_search",
    # Cache (deprecated - use kagura.mcp.builtin.cache)
    "SearchCache",
]
