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
# Must import submodules explicitly to execute @tool decorators
from kagura.mcp.tools import academic, coding, memory, observability, web  # noqa: F401

# Force import of all tool functions to trigger @tool registration
from kagura.mcp.tools.academic import *  # noqa: F403, F401
from kagura.mcp.tools.coding import *  # noqa: F403, F401
from kagura.mcp.tools.memory import *  # noqa: F403, F401
from kagura.mcp.tools.observability import *  # noqa: F403, F401
from kagura.mcp.tools.web import *  # noqa: F403, F401

__all__ = [
    "academic",
    "coding",
    "memory",
    "observability",
    "web",
]
