"""
Built-in tools for Kagura AI

Note: All tools have been moved to kagura.mcp.builtin for better MCP integration.
Imports here are provided for backward compatibility only.

Deprecated: This module is deprecated. Use kagura.mcp.builtin instead.
"""
import warnings

# Issue DeprecationWarning for all imports
# Users can suppress internal warnings in their test configurations if needed
warnings.warn(
    "kagura.tools is deprecated and will be removed in v5.0.0. "
    "Please migrate to kagura.mcp.tools:\n"
    "  - from kagura.tools import brave_web_search\n"
    "  + from kagura.mcp.tools.web.brave_search import brave_web_search\n"
    "  - from kagura.tools import get_youtube_transcript\n"
    "  + from kagura.mcp.tools.web.youtube import get_youtube_transcript",
    DeprecationWarning,
    stacklevel=2,
)

# Backward compatibility: All tools moved to MCP tools
from kagura.mcp.tools.web.brave_search import (  # noqa: E402
    brave_news_search,
    brave_web_search,
)
from kagura.mcp.utils.cache import SearchCache  # noqa: E402
from kagura.mcp.tools.web.youtube import (  # noqa: E402
    get_youtube_metadata,
    get_youtube_transcript,
)

__all__ = [
    # YouTube (deprecated - use kagura.mcp.tools.web.youtube)
    "get_youtube_transcript",
    "get_youtube_metadata",
    # Brave Search (deprecated - use kagura.mcp.tools.web.brave_search)
    "brave_web_search",
    "brave_news_search",
    # Cache (deprecated - use kagura.mcp.utils.cache)
    "SearchCache",
]
