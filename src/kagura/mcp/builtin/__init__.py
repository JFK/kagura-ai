"""Built-in MCP tools for Kagura features

These tools expose Kagura's advanced features (Memory, Routing, Multimodal,
Web) via MCP for single-config Claude Desktop integration.
"""

# Auto-import all builtin tools
from . import (
    brave_search,  # noqa: F401
    cache,  # noqa: F401
    fact_check,  # noqa: F401
    file_ops,  # noqa: F401
    media,  # noqa: F401
    memory,  # noqa: F401
    meta,  # noqa: F401
    observability,  # noqa: F401
    routing,  # noqa: F401
    web,  # noqa: F401
    youtube,  # noqa: F401
)

# Multimodal is optional (requires 'web' extra)
try:
    from . import multimodal  # noqa: F401
except ImportError:
    pass

__all__ = [
    "memory",
    "routing",
    "multimodal",
    "web",
    "file_ops",
    "observability",
    "meta",
    "youtube",
    "media",
    "fact_check",
    "brave_search",
    "cache",
]
