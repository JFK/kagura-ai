"""Memory search operations (semantic search, ID search, fetch).

Provides multiple search strategies for memory retrieval.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.utils.common.mcp_helpers import to_int
from kagura.mcp.tools.memory.common import _memory_cache, get_memory_manager
from kagura.mcp.tools.memory.storage import memory_recall


@tool
async def memory_search(
    user_id: str,
    agent_name: str,
    query: str,
    k: int = 3,
    mode: str = "full",
) -> str:
    """Search memories by concept/keyword match.

    When: User recalls topic but not exact key.
    Uses: Semantic (RAG) + keyword matching.

    Args:
        user_id: Memory owner ID
        agent_name: "global" or "thread_{id}"
        query: Search query (natural language)
        k: Number of results (default: 3)
        mode: "summary" (compact) or "full" (JSON, default)

    Returns: Search results

    💡 TIP: Searches by meaning, not exact words.
    🌐 Cross-platform: Searches user's data across all AI tools.
    """
    # Convert k to int
    k = to_int(k, default=5, min_val=1, max_val=100, param_name="k")

    # Get MemoryManager
    try:
        memory = get_memory_manager(user_id, agent_name, enable_rag=True)
    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag=True"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    # Use MemoryService for search (v4.4.0+)
    try:
        from kagura.services import MemoryService

        service = MemoryService(memory)
        result = service.search_memory(query=query, limit=k)

        combined_results = result.results

        # Format output based on mode
        if mode == "summary":
            if not combined_results:
                return "No results found."

            lines = []
            for i, res in enumerate(combined_results[:k], 1):
                content = res.get("content", res.get("value", ""))
                preview = content[:100] + "..." if len(content) > 100 else content
                lines.append(f"{i}. {preview}")

            return "\n".join(lines)
        else:
            # Full JSON format
            return json.dumps(combined_results, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def memory_search_ids(
    user_id: str,
    agent_name: str,
    query: str,
    k: int = 10,
    scope: str = "all",
) -> str:
    """Search memory and return IDs with previews only (low-token)

    Returns compact search results with IDs and short previews instead of
    full content. Use this for:
    - Initial exploration of search results
    - When you need to see many results without consuming too many tokens
    - Two-step workflow: search IDs first, fetch full content later

    💡 WORKFLOW:
    1. Use memory_search_ids() to see available results (low tokens)
    2. Ask user which one they want
    3. Use memory_fetch() to get full content of selected item

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        query: Search query
        k: Number of results to return (default: 10)
        scope: Memory scope to search ("working", "persistent", or "all")

    Returns:
        JSON array of result objects with id, key, preview (50 chars), and score

        Example:
            [{"id": "result_0", "key": "project_plan",
              "preview": "The Q3 roadmap...", "score": 0.95}]

    Note:
        Use memory_fetch(key="project_plan") to get full content.
        The "id" field is for display only; use "key" for fetching.
    """
    # Convert k to int using common helper
    k = to_int(k, default=10, min_val=1, max_val=100, param_name="k")

    try:
        memory = get_memory_manager(user_id, agent_name, enable_rag=True)
    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag=True"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    try:
        # Get search results
        rag_results = []
        if memory.rag or memory.persistent_rag:
            rag_results = memory.recall_semantic(query, top_k=k, scope=scope)

        working_results = []
        if scope in ("all", "working"):
            query_lower = query.lower()
            for key in []:
                if key.startswith("_meta_"):
                    continue
                if query_lower in key.lower():
                    value = memory.get_temp(key)
                    working_results.append(
                        {
                            "key": key,
                            "value": str(value),
                            "scope": "working",
                            "source": "working_memory",
                        }
                    )

        # Combine results
        combined = working_results + rag_results

        # Format as compact ID-based results
        compact_results = []
        for i, result in enumerate(combined[:k]):
            content = result.get("content", result.get("value", ""))
            preview = content[:50] + "..." if len(content) > 50 else content

            # Generate simple ID (index-based for display)
            result_id = f"result_{i}"

            # Convert distance to score (consistent with memory_search)
            distance = result.get("distance")
            score = max(0.0, min(1.0, 1 - distance)) if distance is not None else None

            compact_results.append(
                {
                    "id": result_id,
                    "key": result.get("key", ""),
                    "preview": preview,
                    "score": score,
                    "scope": result.get("scope", ""),
                    "source": result.get("source", ""),
                }
            )

        return json.dumps(compact_results, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def memory_fetch(
    user_id: str,
    agent_name: str,
    key: str,
    scope: str = "persistent",
) -> str:
    """Fetch full content of a specific memory by key

    Retrieves complete memory content after using memory_search_ids() to browse.

    💡 WORKFLOW:
    1. memory_search_ids("project") → See previews
    2. memory_fetch(key="project_plan") → Get full content

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        key: Memory key to fetch (from search_ids results)
        scope: Memory scope ("working" or "persistent")

    Returns:
        Full memory value as string, or error message if not found

    Note:
        This is essentially an alias for memory_recall() but with clearer
        purpose in the two-step search workflow.
    """
    # Delegate to memory_recall
    return await memory_recall(user_id, agent_name, key, scope)
