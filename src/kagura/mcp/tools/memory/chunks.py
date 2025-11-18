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
def memory_get_chunk_context(
    user_id: str,
    parent_id: str,
    chunk_index: str,
    context_size: str = "1",
) -> str:
    """Get neighboring chunks around a specific chunk for additional context.

    Use when a search result returns a chunk and you need surrounding context.

    Args:
        user_id: User identifier (memory owner)
        parent_id: Parent document ID (from search result metadata.parent_id)
        chunk_index: Target chunk index (from search result metadata.chunk_index)
        context_size: Number of chunks before/after to retrieve (default: "1")

    Returns:
        JSON array of chunks with content and metadata, sorted by position

    Example:
        # Search returns chunk 5, need context
        result = memory_search(user_id, agent_name, query)
        parent_id = result["metadata"]["parent_id"]
        chunk_idx = result["metadata"]["chunk_index"]
        context = memory_get_chunk_context(user_id, parent_id, chunk_idx, "1")
        # Returns chunks 4, 5, 6
    """
    try:
        manager = get_memory_manager(user_id, agent_name="global", enable_rag=True)

        # Validate parameters
        try:
            chunk_idx_int = int(chunk_index)
            context_size_int = int(context_size)
        except ValueError:
            return format_error(
                "Invalid parameter type",
                details={
                    "chunk_index": "Must be integer",
                    "context_size": "Must be integer",
                },
            )

        # Validate non-negativity
        if chunk_idx_int < 0 or context_size_int < 0:
            return format_error(
                "Invalid parameter value",
                details={
                    "chunk_index": "Must be non-negative",
                    "context_size": "Must be non-negative",
                },
            )

        # Get chunk context
        chunks = manager.get_chunk_context(
            parent_id=parent_id,
            chunk_index=chunk_idx_int,
            context_size=context_size_int,
        )

        if not chunks:
            return json.dumps(
                {
                    "chunks": [],
                    "message": "No chunks found for this document",
                    "parent_id": parent_id,
                },
                indent=2,
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "chunks": chunks,
                "parent_id": parent_id,
                "total_returned": len(chunks),
            },
            indent=2,
            ensure_ascii=False,
        )

    except ValueError as e:
        return format_error("RAG not enabled", details={"error": str(e)})
    except Exception as e:
        return format_error(
            "Failed to get chunk context", details={"error": str(e)}
        )


@tool
def memory_get_full_document(user_id: str, parent_id: str) -> str:
    """Reconstruct complete document from all chunks.

    Use when you need the full document instead of individual chunks.

    Args:
        user_id: User identifier (memory owner)
        parent_id: Parent document ID (from search result metadata.parent_id)

    Returns:
        JSON with full_content (reconstructed text), chunks array, and statistics

    Example:
        # Search returns a chunk, reconstruct full document
        result = memory_search(user_id, agent_name, query)
        parent_id = result["metadata"]["parent_id"]
        doc = memory_get_full_document(user_id, parent_id)
        # Returns: {"full_content": "...", "total_chunks": 12}
    """
    try:
        manager = get_memory_manager(user_id, agent_name="global", enable_rag=True)

        # Get full document
        doc = manager.get_full_document(parent_id=parent_id)

        if "error" in doc:
            return json.dumps(
                {"error": doc["error"], "parent_id": parent_id},
                indent=2,
                ensure_ascii=False,
            )

        # Return without full chunk array (too verbose)
        return json.dumps(
            {
                "full_content": doc["full_content"],
                "parent_id": doc["parent_id"],
                "total_chunks": doc["total_chunks"],
            },
            indent=2,
            ensure_ascii=False,
        )

    except ValueError as e:
        return format_error("RAG not enabled", details={"error": str(e)})
    except Exception as e:
        return format_error(
            "Failed to get full document", details={"error": str(e)}
        )


@tool
def memory_get_chunk_metadata(
    user_id: str,
    parent_id: str,
    chunk_index: str = "",
) -> str:
    """Get metadata for chunk(s) to make informed decisions about context retrieval.

    Use to check chunk count, position, or metadata before fetching full content.

    Args:
        user_id: User identifier (memory owner)
        parent_id: Parent document ID
        chunk_index: Optional chunk index (empty string = all chunks)

    Returns:
        JSON with metadata for specific chunk or all chunks

    Example:
        # Check total chunks before deciding to fetch all
        meta = memory_get_chunk_metadata(user_id, parent_id, "")
        if len(meta) > 20:
            # Too many chunks, get specific context only
            context = memory_get_chunk_context(user_id, parent_id, "5", "2")
        else:
            # Small doc, get full content
            doc = memory_get_full_document(user_id, parent_id)
    """
    try:
        manager = get_memory_manager(user_id, agent_name="global", enable_rag=True)

        # Parse chunk_index
        chunk_idx: Optional[int] = None
        if chunk_index:
            try:
                chunk_idx = int(chunk_index)
            except ValueError:
                return format_error(
                    "Invalid chunk_index",
                    details={"chunk_index": "Must be integer or empty string"},
                )

        # Get metadata
        metadata = manager.get_chunk_metadata(
            parent_id=parent_id, chunk_index=chunk_idx
        )

        return json.dumps(metadata, indent=2, ensure_ascii=False)

    except ValueError as e:
        return format_error("RAG not enabled", details={"error": str(e)})
    except Exception as e:
        return format_error(
            "Failed to get chunk metadata", details={"error": str(e)}
        )
