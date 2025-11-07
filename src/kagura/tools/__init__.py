"""
Built-in tools for Kagura AI

Note: All tools have been moved to kagura.mcp.builtin for better MCP integration.
Imports here are provided for backward compatibility only.

Deprecated: This module is deprecated. Use kagura.mcp.builtin instead.
"""
import warnings

# Issue DeprecationWarning for external users
warnings.warn(
    "kagura.tools is deprecated and will be removed in v5.0.0. "
    "Please migrate to kagura.mcp.builtin:\n"
    "  - from kagura.tools import brave_web_search\n"
    "  + from kagura.mcp.builtin.brave_search import brave_web_search\n"
    "  - from kagura.tools import get_youtube_transcript\n"
    "  + from kagura.mcp.builtin.youtube import get_youtube_transcript",
    DeprecationWarning,
    stacklevel=2,
)

# Backward compatibility: All tools moved to MCP builtin
from kagura.mcp.builtin.brave_search import (  # noqa: E402
    brave_news_search,
    brave_web_search,
)
from kagura.mcp.builtin.cache import SearchCache  # noqa: E402
from kagura.mcp.builtin.youtube import (  # noqa: E402
    get_youtube_metadata,
    get_youtube_transcript,
)

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
