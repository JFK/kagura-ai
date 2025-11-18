"""Essential MCP tools (non-migrated).

Contains tools that have not yet been migrated to mcp/tools/:
- academic.py: arXiv paper search
- brave_search.py: Web search via Brave API
- youtube.py: YouTube tools
- cache.py: Search caching (used by brave_search)
- common.py: Helper functions

Status: Active (migration planned for future release)
"""

# Auto-register tools
from kagura.mcp.builtin import academic, brave_search, youtube  # noqa: F401

__all__ = ["academic", "brave_search", "youtube"]
