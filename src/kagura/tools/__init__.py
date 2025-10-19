"""
Built-in tools for Kagura AI

Note: YouTube tools have been moved to kagura.mcp.builtin.youtube
for better MCP integration. Imports here are provided for backward compatibility.
"""

# Backward compatibility: YouTube tools moved to MCP builtin
from kagura.mcp.builtin.youtube import get_youtube_metadata, get_youtube_transcript

from .brave_search import brave_news_search, brave_web_search

__all__ = [
    # YouTube (deprecated - use kagura.mcp.builtin.youtube)
    "get_youtube_transcript",
    "get_youtube_metadata",
    # Brave Search
    "brave_web_search",
    "brave_news_search",
]
