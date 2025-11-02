"""Graph Memory API endpoints.

GraphMemory operations for relationship tracking and user pattern analysis:
- POST /api/v1/graph/interactions - Record AI-User interaction
- GET /api/v1/graph/{node_id}/related - Get related nodes
- GET /api/v1/graph/users/{user_id}/pattern - Analyze user pattern

Issue #345: GraphDB integration for AI-User relationship memory
"""

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query

from kagura.api import models
from kagura.api.dependencies import MemoryManagerDep

router = APIRouter()


@router.post(
    "/interactions", response_model=models.InteractionResponse, status_code=201
)
async def record_interaction(
    request: models.InteractionCreate, memory: MemoryManagerDep
) -> dict[str, Any]:
    """Record AI-User interaction in graph memory.

    Stores a conversation turn between user and AI in the knowledge graph,
    enabling pattern analysis and personalization.

    Args:
        request: Interaction creation request
        memory: MemoryManager dependency

    Returns:
        Interaction creation response

    Raises:
        HTTPException: If GraphMemory is not available or recording fails
    """
    # Check if graph is available
    if not memory.graph:
        raise HTTPException(
            status_code=503,
            detail=(
                "GraphMemory not available. Enable graph memory with enable_graph=True."
            ),
        )

    # Record interaction
    try:
        # Merge ai_platform into metadata if provided (backward compatibility)
        meta = request.metadata or {}
        if request.ai_platform:
            meta["ai_platform"] = request.ai_platform

        interaction_id = memory.graph.record_interaction(
            user_id=request.user_id,
            query=request.query,
            response=request.response,
            metadata=meta,
        )

        # Persist graph if persist_path is set
        if memory.graph.persist_path:
            memory.graph.persist()

        return {
            "interaction_id": interaction_id,
            "user_id": request.user_id,
            "ai_platform": request.ai_platform or "unknown",
            "message": "Interaction recorded successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to record interaction: {str(e)}"
        ) from e


@router.get("/{node_id}/related", response_model=models.RelatedNodesResponse)
async def get_related_nodes(
    node_id: Annotated[str, Path(description="Starting node ID")],
    memory: MemoryManagerDep,
    depth: Annotated[int, Query(ge=1, le=5, description="Traversal depth")] = 2,
    rel_type: Annotated[
        str | None,
        Query(
            description=(
                "Filter by relationship type "
                "(related_to, depends_on, learned_from, influences, works_on)"
            )
        ),
    ] = None,
) -> dict[str, Any]:
    """Get related nodes from graph memory.

    Retrieves nodes related to the specified node through graph traversal.
    Useful for discovering connections and relationships between memories,
    users, topics, and interactions.

    Args:
        node_id: Starting node ID
        memory: MemoryManager dependency
        depth: Traversal depth (number of hops)
        rel_type: Filter by relationship type (None = all types)

    Returns:
        Related nodes response

    Raises:
        HTTPException: If GraphMemory is not available
    """
    # Check if graph is available
    if not memory.graph:
        raise HTTPException(
            status_code=503,
            detail=(
                "GraphMemory not available. Enable graph memory with enable_graph=True."
            ),
        )

    # Get related nodes
    try:
        related = memory.graph.get_related(
            node_id=node_id, depth=depth, rel_type=rel_type
        )

        # Convert to GraphNode models
        graph_nodes = [
            models.GraphNode(
                id=node["id"],
                type=node.get("type", "unknown"),
                data={k: v for k, v in node.items() if k not in ("id", "type")},
            )
            for node in related
        ]

        return {
            "node_id": node_id,
            "depth": depth,
            "rel_type": rel_type,
            "related_count": len(graph_nodes),
            "related_nodes": graph_nodes,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get related nodes: {str(e)}"
        ) from e


@router.get("/users/{user_id}/pattern", response_model=models.UserPatternResponse)
async def get_user_pattern(
    user_id: Annotated[str, Path(description="User identifier")],
    memory: MemoryManagerDep,
) -> dict[str, Any]:
    """Analyze user's interaction patterns and interests.

    Analyzes a user's interaction history to discover patterns, interests,
    and preferences. Returns statistics about topics, platforms, and
    interaction frequency.

    Args:
        user_id: User identifier to analyze
        memory: MemoryManager dependency

    Returns:
        User pattern analysis response

    Raises:
        HTTPException: If GraphMemory is not available
    """
    # Check if graph is available
    if not memory.graph:
        raise HTTPException(
            status_code=503,
            detail=(
                "GraphMemory not available. Enable graph memory with enable_graph=True."
            ),
        )

    # Analyze user pattern
    try:
        pattern_data = memory.graph.analyze_user_pattern(user_id)

        return {
            "user_id": user_id,
            "pattern": models.UserPattern(**pattern_data),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze user pattern: {str(e)}"
        ) from e
