"""Memory search operations (semantic search, ID search, fetch).

Provides multiple search strategies for memory retrieval.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.utils.common.mcp_helpers import to_int
from kagura.mcp.tools.memory.common import _memory_cache, get_memory_manager



@tool
async def memory_search_semantic(
    user_id: str,
    agent_name: str,
    query: str,
    k: int = 5,
) -> str:
    """Search memories using semantic similarity (RAG/vector search).

    Finds memories by meaning, not exact keywords.
    Best for conceptual queries like "authentication issues" or "recent bugs".

    Args:
        user_id: Memory owner ID
        agent_name: "global" (cross-platform) or "thread_{id}" (conversation-specific)
        query: Search query (natural language, e.g., "API authentication problems")
        k: Number of results (default: 5, max: 100)

    Returns:
        JSON array of results with content, score, and metadata

    Example:
        Query: "machine learning projects"
        Finds: entries about ML, AI, neural networks (semantic match)

    💡 TIP: Use this when you want conceptually similar results.
    🌐 Cross-platform: Works across all AI assistants (Claude, ChatGPT, etc.)
    """
    k = to_int(k, default=5, min_val=1, max_val=100, param_name="k")

    try:
        memory = get_memory_manager(user_id, agent_name, enable_rag=True)
    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag=True"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=True
            )
        memory = _memory_cache[cache_key]

    try:
        from kagura.services import MemoryService

        service = MemoryService(memory)
        result = service.search_memory(query=query, limit=k)

        return json.dumps(result.results, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


@tool
async def memory_search_keyword(
    user_id: str,
    agent_name: str,
    query: str,
    k: int = 5,
) -> str:
    """Search memories using keyword matching (BM25 algorithm).

    Finds memories by exact keyword matches.
    Best for specific terms like "PostgreSQL" or "Issue #123".

    Args:
        user_id: Memory owner ID
        agent_name: "global" (cross-platform) or "thread_{id}" (conversation-specific)
        query: Search keywords (e.g., "PostgreSQL connection timeout")
        k: Number of results (default: 5, max: 100)

    Returns:
        JSON array of results with content, score, and metadata

    Example:
        Query: "PostgreSQL"
        Finds: entries containing exactly "PostgreSQL" (keyword match)

    💡 TIP: Use this when searching for specific terms or names.
    🌐 Cross-platform: Works across all AI assistants.
    """
    k = to_int(k, default=5, min_val=1, max_val=100, param_name="k")

    try:
        memory = get_memory_manager(user_id, agent_name, enable_rag=False)
    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag=False"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    try:
        # Use BM25 search from MemoryManager
        from kagura.core.memory.bm25_search import BM25Search

        # Build corpus from persistent memory
        corpus = []
        if hasattr(memory, "persistent") and memory.persistent:
            # Use fetch_all() with required parameters (not get_all())
            all_memories_list = memory.persistent.fetch_all(
                user_id=user_id,
                agent_name=agent_name
            )
            for mem in all_memories_list:
                corpus.append(
                    {
                        "key": mem.get("key", ""),
                        "content": str(mem.get("value", mem.get("content", ""))),
                        "agent_name": agent_name,
                    }
                )

        if not corpus:
            return json.dumps([], indent=2)

        # Initialize BM25 and search
        bm25 = BM25Search(k1=1.2, b=0.4)
        bm25.build_index(corpus)  # Correct method name: build_index, not fit
        results = bm25.search(query, k=k)  # Correct parameter name: k, not top_k

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "key": result["key"],
                    "content": result["content"],
                    "score": result.get("bm25_score", 0.0),  # BM25 uses 'bm25_score' key
                    "agent_name": result.get("agent_name", agent_name),
                }
            )

        return json.dumps(formatted_results, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e), "query": query})
