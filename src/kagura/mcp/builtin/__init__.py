"""Built-in MCP tools for Kagura features

These tools expose Kagura's advanced features (Memory, Routing, Multimodal,
Web) via MCP for single-config Claude Desktop integration.
"""

# Auto-import all builtin tools
from . import (
    academic,  # noqa: F401
    brave_search,  # noqa: F401
    cache,  # noqa: F401
    coding,  # noqa: F401
    fact_check,  # noqa: F401
    file_ops,  # noqa: F401
    github,  # noqa: F401
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
    "academic",
    "brave_search",
    "cache",
    "coding",
    "fact_check",
    "file_ops",
    "github",
    "media",
    "memory",
    "meta",
    "multimodal",
    "observability",
    "routing",
    "web",
    "youtube",
]
