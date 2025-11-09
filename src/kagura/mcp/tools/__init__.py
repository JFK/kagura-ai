"""Modular MCP tools for Kagura AI.

Auto-discovery implementation (v4.3.0):
All tools in this package are automatically imported and registered
in the global tool_registry when this module is loaded.

Structure:
- coding/: Coding memory and session management tools (19 tools)
- memory/: Memory operations tools (18 tools)

All tools are decorated with @tool, which automatically registers them
in kagura.core.tool_registry when imported.
"""

# Auto-import all tool modules to trigger @tool registration
from kagura.mcp.tools import coding, memory  # noqa: F401

__all__ = [
    "coding",
    "memory",
]
