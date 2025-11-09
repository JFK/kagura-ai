"""Memory MCP tools - modular implementation.

This package provides 18 MCP tools for memory management, organized by functionality:

Storage Operations (3 tools):
- memory_store: Store information in agent memory
- memory_recall: Recall information from agent memory
- memory_delete: Delete a memory with audit logging

Search Operations (3 tools):
- memory_search: Search memories by concept/keyword match
- memory_search_ids: Search and return IDs with previews only (low-token)
- memory_fetch: Fetch full content of a specific memory by key

List and Feedback (2 tools):
- memory_list: List all stored memories for debugging and exploration
- memory_feedback: Provide feedback on memory usefulness

Graph Operations (2 tools):
- memory_get_related: Get related nodes from graph memory
- memory_record_interaction: Record AI-User interaction in graph memory

User Pattern (1 tool):
- memory_get_user_pattern: Analyze user's interaction patterns and interests

Stats (1 tool):
- memory_stats: Get memory health report and statistics (read-only)

Timeline (2 tools):
- memory_timeline: Retrieve memories from specific time range
- memory_fuzzy_recall: Recall memories using fuzzy key matching

Tool History (1 tool):
- memory_get_tool_history: Get MCP tool usage history

Chunk Operations (3 tools):
- memory_get_chunk_context: Get neighboring chunks around a specific chunk
- memory_get_full_document: Reconstruct complete document from all chunks
- memory_get_chunk_metadata: Get metadata for chunk(s)

Total: 18 tools
"""

from __future__ import annotations

from kagura.mcp.tools.memory.chunks import (
    memory_get_chunk_context,
    memory_get_chunk_metadata,
    memory_get_full_document,
)
from kagura.mcp.tools.memory.graph import (
    memory_get_related,
    memory_record_interaction,
)
from kagura.mcp.tools.memory.list_and_feedback import (
    memory_feedback,
    memory_list,
)
from kagura.mcp.tools.memory.search import (
    memory_fetch,
    memory_search,
    memory_search_ids,
)
from kagura.mcp.tools.memory.stats import memory_stats
from kagura.mcp.tools.memory.storage import (
    memory_delete,
    memory_recall,
    memory_store,
)
from kagura.mcp.tools.memory.timeline import (
    memory_fuzzy_recall,
    memory_timeline,
)
from kagura.mcp.tools.memory.tool_history import memory_get_tool_history
from kagura.mcp.tools.memory.user_pattern import memory_get_user_pattern

__all__ = [
    # Storage (3)
    "memory_store",
    "memory_recall",
    "memory_delete",
    # Search (3)
    "memory_search",
    "memory_search_ids",
    "memory_fetch",
    # List and Feedback (2)
    "memory_list",
    "memory_feedback",
    # Graph (2)
    "memory_get_related",
    "memory_record_interaction",
    # User Pattern (1)
    "memory_get_user_pattern",
    # Stats (1)
    "memory_stats",
    # Timeline (2)
    "memory_timeline",
    "memory_fuzzy_recall",
    # Tool History (1)
    "memory_get_tool_history",
    # Chunks (3)
    "memory_get_chunk_context",
    "memory_get_full_document",
    "memory_get_chunk_metadata",
]
