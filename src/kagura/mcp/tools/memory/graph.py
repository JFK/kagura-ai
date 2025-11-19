"""Graph memory operations (relationships, interactions).

Provides graph-based memory operations for discovering connections.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.utils.common.mcp_helpers import format_error, parse_json_dict, to_int
from kagura.mcp.tools.memory.common import get_memory_manager


@tool
async def memory_get_related(
    user_id: str,
    agent_name: str,
    node_id: str,
    depth: str | int = 2,
    rel_type: str | None = None,
) -> str:
    """Get related nodes from graph memory

    Retrieves nodes related to the specified node through graph traversal.
    Useful for discovering connections and relationships between memories,
    users, topics, and interactions.

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns this graph data (searches user's graph)
    - agent_name: WHERE to search ("global" = all threads, "thread_X" = specific)

    🔍 USE WHEN:
    - Discovering connections between memories
    - Finding related topics or users
    - Exploring knowledge graph relationships
    - Building context from related information

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier (use "global" for cross-thread sharing)
        node_id: Starting node ID to find related nodes from
        depth: Traversal depth (number of hops, default: 2)
        rel_type: Filter by relationship type (related_to, depends_on,
            learned_from, influences, works_on). None = all types

    Returns:
        JSON string with related nodes list

    💡 EXAMPLE:
        # Find memories related to "python_tips" for user
        memory_get_related(user_id="user_jfk", agent_name="global",
                          node_id="mem_python_tips", depth=2)

        # Find topics a user has interacted with
        memory_get_related(user_id="user_jfk", agent_name="global",
                          node_id="user_001", depth=1, rel_type="learned_from")

    📊 RETURNS:
        {
          "node_id": "starting_node",
          "depth": 2,
          "rel_type": "related_to" or null,
          "related_count": 5,
          "related_nodes": [...]
        }

    Note:
        Requires enable_graph=True in MemoryManager (enabled by default).
        Returns empty list if GraphMemory is not available.
    """
    enable_rag = True
    memory = get_memory_manager(user_id, agent_name, enable_rag=enable_rag)

    # Check if graph is available
    if not memory.graph:
        return format_error(
            "GraphMemory not available",
            details={"message": "Graph memory is disabled or NetworkX not installed"},
        )

    # Convert depth to int using common helper
    depth_int = to_int(depth, default=2, min_val=1, max_val=10, param_name="depth")

    # Get related nodes
    try:
        related = memory.graph.get_related(
            node_id=node_id, depth=depth_int, rel_type=rel_type
        )

        return json.dumps(
            {
                "node_id": node_id,
                "depth": depth,
                "rel_type": rel_type,
                "related_count": len(related),
                "related_nodes": related,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to get related nodes: {str(e)}"}, indent=2)


@tool
async def memory_record_interaction(
    agent_name: str,
    user_id: str,
    query: str,
    response: str,
    ai_platform: str = "",
    metadata: str = "{}",
) -> str:
    """Record AI-User interaction in graph memory

    Stores a conversation turn between user and AI in the knowledge graph,
    enabling pattern analysis and personalization. Use this to build a
    history of interactions for learning user preferences and habits.

    🔍 USE WHEN:
    - Recording conversation turns for pattern analysis
    - Building user interaction history
    - Enabling cross-platform memory (same user, different AI tools)
    - Tracking topic discussions over time

    💡 v4.0 Universal Memory: ai_platform is OPTIONAL
        Focus on "what" was discussed, not "where"
        Platform tracking is optional for statistics

    💡 TIP: Include "topic" in metadata to enable topic analysis
        metadata='{"topic": "python", "project": "kagura"}'

    This allows memory_get_user_pattern to discover discussed topics and
    build a knowledge graph of user interests.

    Args:
        agent_name: Agent identifier (use "global" for cross-thread sharing)
        user_id: User identifier (e.g., "user_001", email, username)
        query: User's query/message
        response: AI's response
        ai_platform: (Optional) AI platform name (e.g., "claude", "chatgpt", "gemini")
            Leave empty for platform-agnostic memory
        metadata: JSON object string with additional data
            (e.g., '{"project": "kagura", "topic": "python", "session_id": "sess_123"}')

    Returns:
        JSON string with interaction ID and confirmation

    💡 EXAMPLE:
        # Platform-agnostic memory (recommended)
        memory_record_interaction(
            agent_name="global",
            user_id="user_jfk",
            query="How to use FastAPI?",
            response="FastAPI is a modern web framework...",
            metadata='{"topic": "python", "project": "kagura"}'
        )

        # With platform tracking (optional)
        memory_record_interaction(
            agent_name="global",
            user_id="user_jfk",
            query="...",
            response="...",
            ai_platform="claude",
            metadata='{"topic": "python"}'
        )

    📊 RETURNS:
        {
          "interaction_id": "interaction_abc123",
          "user_id": "user_jfk",
          "message": "Interaction recorded successfully"
        }

    Note:
        Requires enable_graph=True in MemoryManager (enabled by default).
        The interaction is linked to the user node and can be analyzed later.
    """
    enable_rag = True
    memory = get_memory_manager(user_id, agent_name, enable_rag=enable_rag)

    # Check if graph is available
    if not memory.graph:
        return format_error(
            "GraphMemory not available",
            details={"message": "Graph memory is disabled or NetworkX not installed"},
        )

    # Parse metadata using common helper
    metadata_dict = parse_json_dict(metadata, param_name="metadata")

    # Merge ai_platform into metadata if provided (backward compatibility)
    if ai_platform:
        metadata_dict["ai_platform"] = ai_platform

    # Record interaction (ai_platform now in metadata)
    try:
        interaction_id = memory.graph.record_interaction(
            user_id=user_id,
            query=query,
            response=response,
            metadata=metadata_dict,
        )

        # Persist graph if persist_path is set
        if memory.graph.persist_path:
            memory.graph.persist()

        # Get platform for response (backward compat)
        platform = ai_platform or metadata_dict.get("ai_platform", "unknown")

        return json.dumps(
            {
                "status": "recorded",
                "interaction_id": interaction_id,
                "user_id": user_id,
                "ai_platform": platform,
                "message": "Interaction recorded successfully",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to record interaction: {str(e)}"}, indent=2
        )


# ==============================================================================
# Issue #720: Renamed graph navigation tool
# ==============================================================================


@tool
async def memory_get_neighbors(
    user_id: str,
    agent_name: str,
    node_id: str,
    depth: int = 2,
    rel_type: str | None = None,
) -> str:
    """Get related nodes from graph memory (renamed from memory_get_related).

    Traverses knowledge graph to discover connections between memories.
    Useful for exploring relationships and building context.

    Args:
        user_id: Memory owner ID
        agent_name: "global" (all threads) or "thread_{id}" (specific conversation)
        node_id: Starting node ID
        depth: Traversal depth (default: 2, max: 5 hops)
        rel_type: Filter by relationship type:
            - "related_to": General association
            - "depends_on": Dependency relationship
            - "learned_from": Knowledge source
            - "influences": Impact relationship
            - None: All types

    Returns:
        JSON with related nodes, relationships, and traversal path

    Example:
        # Find memories related to "API authentication"
        neighbors = memory_get_neighbors(
            user_id="user",
            agent_name="global",
            node_id="api_auth_node",
            depth=2
        )

    💡 TIP: Use for discovering hidden connections in knowledge graph.
    🌐 Cross-platform: Works across all AI assistants.
    """
    from kagura.utils.common.mcp_helpers import to_int

    depth = to_int(depth, default=2, min_val=1, max_val=5, param_name="depth")

    try:
        memory = get_memory_manager(user_id, agent_name, enable_rag=False)

        # Get graph memory
        if not hasattr(memory, "graph") or memory.graph is None:
            return json.dumps(
                {
                    "error": "Graph memory not enabled",
                    "help": "Enable graph memory in configuration",
                }
            )

        # Get related nodes
        related = memory.graph.get_related_nodes(
            node_id=node_id,
            depth=depth,
            rel_type=rel_type,
        )

        return json.dumps(
            {
                "node_id": node_id,
                "depth": depth,
                "rel_type": rel_type,
                "found": len(related),
                "related_nodes": related,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps({"error": str(e), "node_id": node_id})
