"""Search & Recall endpoints.

Semantic search and recall API routes:
- POST /api/v1/search - Full-text + semantic search
- POST /api/v1/recall - Semantic recall (similarity-based)
"""

import json
from typing import Any

from fastapi import APIRouter

from kagura.api import models
from kagura.api.dependencies import MemoryManagerDep

router = APIRouter()


def _decode_metadata(metadata_dict: dict[str, Any]) -> dict[str, Any]:
    """Decode JSON strings in metadata (ChromaDB compatibility).

    Args:
        metadata_dict: Metadata with potential JSON strings

    Returns:
        Decoded metadata with lists/dicts restored
    """
    decoded = {}
    for k, v in metadata_dict.items():
        if isinstance(v, str) and (v.startswith("[") or v.startswith("{")):
            try:
                decoded[k] = json.loads(v)
            except json.JSONDecodeError:
                decoded[k] = v
        else:
            decoded[k] = v
    return decoded


@router.post("/search", response_model=models.SearchResponse)
async def search_memories(
    request: models.SearchRequest, memory: MemoryManagerDep
) -> dict[str, Any]:
    """Search memories with full-text + semantic search.

    Args:
        request: Search request
        memory: MemoryManager dependency

    Returns:
        Search results with relevance scores
    """
    # Use persistent memory search (SQL LIKE)
    # TODO: Add full-text search support or use RAG
    search_pattern = f"%{request.query}%"
    results_list = memory.search_memory(search_pattern, limit=request.limit)

    # Filter by scope if specified
    if request.scope != "all":
        # Note: search_memory only searches persistent memory
        # For working memory, would need to implement search
        if request.scope != "persistent":
            results_list = []

    # Filter by tags if specified
    if request.filter_tags:
        filtered_results = []
        for mem in results_list:
            metadata_dict = mem.get("metadata", {})
            mem_tags = set(metadata_dict.get("tags", []))
            if all(tag in mem_tags for tag in request.filter_tags):
                filtered_results.append(mem)
        results_list = filtered_results

    # Convert to API response format
    search_results = []
    for mem in results_list:
        metadata_dict = mem.get("metadata", {})

        # Decode metadata (ChromaDB compatibility)
        metadata_dict = _decode_metadata(metadata_dict)

        tags = metadata_dict.get("tags", [])

        # Remove internal fields
        user_metadata = {
            k: v
            for k, v in metadata_dict.items()
            if k not in ("tags", "importance", "created_at", "updated_at")
        }

        search_results.append(
            {
                "key": mem["key"],
                "value": mem["value"],
                "scope": "persistent",  # search_memory only searches persistent
                "tags": tags,
                "score": 1.0,  # TODO: Calculate actual relevance score
                "metadata": user_metadata,
            }
        )

    return {
        "results": search_results,
        "total": len(search_results),
        "query": request.query,
    }


@router.post("/recall", response_model=models.RecallResponse)
async def recall_memories(
    request: models.RecallRequest, memory: MemoryManagerDep
) -> dict[str, Any]:
    """Recall memories by semantic similarity.

    Uses vector embeddings to find semantically similar memories.

    Args:
        request: Recall request
        memory: MemoryManager dependency

    Returns:
        Recall results with similarity scores
    """
    # Use semantic search (RAG)
    try:
        rag_results = memory.recall_semantic(
            query=request.query, top_k=request.k, scope=request.scope
        )
    except ValueError:
        # RAG not enabled
        return {
            "results": [],
            "query": request.query,
            "k": request.k,
        }

    # Convert to API response format
    recall_results = []
    for result in rag_results:
        # Get metadata from result
        metadata_dict = result.get("metadata", {})

        # Decode metadata (ChromaDB compatibility)
        metadata_dict = _decode_metadata(metadata_dict)

        key = metadata_dict.get("key", "unknown")
        tags = metadata_dict.get("tags", [])
        scope = result.get("scope", "persistent")

        # Remove internal fields
        user_metadata = {
            k: v
            for k, v in metadata_dict.items()
            if k
            not in ("tags", "importance", "created_at", "updated_at", "type", "key")
        }

        # Calculate similarity from distance (ChromaDB uses cosine distance)
        # Distance range: 0 (identical) to 2 (opposite)
        # Similarity: 1 (identical) to 0 (opposite)
        distance = result.get("distance", 0.0)
        similarity = 1.0 - (distance / 2.0)
        similarity = max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

        recall_results.append(
            {
                "key": key,
                "value": result.get("content", ""),
                "scope": scope,
                "similarity": similarity,
                "tags": tags,
                "metadata": user_metadata,
            }
        )

    return {
        "results": recall_results,
        "query": request.query,
        "k": request.k,
    }
