"""Memory MCP tools - Issue #720 final configuration.

Provides 8 memory management tools with clear responsibility separation:
- MCP Server: Pure tool provider (no decision-making)
- LLM Client: Decision maker (chooses which tools to use, when, and how)

Storage Operations (3 tools):
- memory_store: Store information in agent memory
- memory_delete: Delete a memory with audit logging
- memory_stats: Get memory health report and statistics

Search Operations (3 tools):
- memory_search_semantic: Semantic similarity search (RAG/vector)
- memory_search_keyword: Keyword matching (BM25 algorithm)
- memory_search_timeline: Time-range filtering

RAG Extensions (2 tools):
- memory_get_document: Reconstruct complete document from chunks
- memory_get_neighbors: Graph traversal for related nodes

Total: 8 tools (reduced from 18+ in v4.3.0)
"""

from __future__ import annotations

# Final 8 memory tools (Issue #720)
from kagura.mcp.tools.memory.chunks import memory_get_document
from kagura.mcp.tools.memory.graph import memory_get_neighbors
from kagura.mcp.tools.memory.search import (
    memory_search_keyword,
    memory_search_semantic,
)
from kagura.mcp.tools.memory.stats import memory_stats
from kagura.mcp.tools.memory.storage import (
    memory_delete,
    memory_store,
)
from kagura.mcp.tools.memory.timeline import memory_search_timeline

__all__ = [
    # Storage (3)
    "memory_store",
    "memory_delete",
    # Stats (1)
    "memory_stats",
    # Search (3)
    "memory_search_semantic",
    "memory_search_keyword",
    "memory_search_timeline",
    # RAG Extensions (2)
    "memory_get_document",
    "memory_get_neighbors",
]
