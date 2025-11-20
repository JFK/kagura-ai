"""Memory chunk operations for RAG context retrieval.

Provides tools for accessing document chunks with surrounding context.
"""

from __future__ import annotations

import json
from typing import Optional

from kagura import tool
from kagura.utils.common.mcp_helpers import format_error
from kagura.mcp.tools.memory.common import get_memory_manager



@tool
def memory_get_document(user_id: str, parent_id: str) -> str:
    """Get complete document from chunks (renamed from memory_get_full_document).

    Reconstructs full document when search returns individual chunks.
    Use after semantic search to get complete context.

    Args:
        user_id: Memory owner ID
        parent_id: Parent document ID (from search result metadata)

    Returns:
        JSON with full_content, total_chunks, and metadata

    Example:
        # 1. Search returns chunk
        result = memory_search_semantic(user_id, agent_name, "API docs")
        # 2. Get parent_id from result
        parent_id = result[0]["metadata"]["parent_id"]
        # 3. Reconstruct full document
        doc = memory_get_document(user_id, parent_id)

    💡 TIP: Use when search results are fragmented chunks.
    🌐 Cross-platform: Works across all AI assistants.
    """
    try:
        manager = get_memory_manager(user_id, agent_name="global", enable_rag=True)

        # Get all chunks for this document
        if not (hasattr(manager, "rag") and manager.rag):
            return json.dumps({"error": "RAG not enabled for this user"})

        chunks = manager.rag.get_chunks_by_parent(parent_id)

        if not chunks:
            return json.dumps(
                {"error": f"No chunks found for parent_id: {parent_id}"}
            )

        # Reconstruct full document
        sorted_chunks = sorted(chunks, key=lambda c: c.get("chunk_index", 0))
        full_content = "\n\n".join(c.get("content", "") for c in sorted_chunks)

        return json.dumps(
            {
                "parent_id": parent_id,
                "full_content": full_content,
                "total_chunks": len(sorted_chunks),
                "chunks": sorted_chunks,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps({"error": str(e), "parent_id": parent_id})
