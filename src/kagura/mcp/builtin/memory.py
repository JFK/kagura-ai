# ruff: noqa: F822
"""Built-in MCP tools for Memory operations.

.. deprecated:: 4.3.0
    This module has been reorganized into ``kagura.mcp.tools.memory``.
    Import from ``kagura.mcp.tools.memory`` instead.
    This compatibility facade will be removed in v4.5.0.

Exposes Kagura's memory management features via MCP.

All tools have been moved to modular files in ``src/kagura/mcp/tools/memory/``:
- storage.py: Core CRUD operations (store, recall, delete)
- search.py: Search operations (search, search_ids, fetch)
- list_and_feedback.py: List and feedback operations
- graph.py: Graph relationships and interactions
- user_pattern.py: User pattern analysis
- stats.py: Memory health and statistics
- timeline.py: Timeline and fuzzy search
- tool_history.py: MCP tool usage history
- chunks.py: RAG chunk operations

Note: Tools are dynamically imported via __getattr__, so static linters
cannot detect them. This is intentional for backward compatibility.
"""

from __future__ import annotations

import warnings


def __getattr__(name: str):
    """Lazy import with deprecation warning for backward compatibility.

    This allows old imports to still work while showing deprecation warnings.
    Tools are imported on-demand to avoid circular import issues.
    """
    warnings.warn(
        f"kagura.mcp.builtin.memory.{name} is deprecated and will be removed in v4.5.0. "
        "Use kagura.mcp.tools.memory instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Lazy import from new location
    from kagura.mcp.tools import memory as memory_tools

    if hasattr(memory_tools, name):
        return getattr(memory_tools, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # Storage
    "memory_store",
    "memory_recall",
    "memory_delete",
    # Search
    "memory_search",
    "memory_search_ids",
    "memory_fetch",
    # List & Feedback
    "memory_list",
    "memory_feedback",
    # Graph
    "memory_get_related",
    "memory_record_interaction",
    # User Pattern
    "memory_get_user_pattern",
    # Stats
    "memory_stats",
    # Timeline
    "memory_timeline",
    "memory_fuzzy_recall",
    # Tool History
    "memory_get_tool_history",
    # Chunks
    "memory_get_chunk_context",
    "memory_get_full_document",
    "memory_get_chunk_metadata",
]
