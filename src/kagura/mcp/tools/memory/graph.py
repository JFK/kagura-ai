"""Graph memory operations (relationships, interactions).

Provides graph-based memory operations for discovering connections.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.utils.common.mcp_helpers import format_error, parse_json_dict, to_int
from kagura.mcp.tools.memory.common import get_memory_manager



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
