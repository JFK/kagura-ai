"""Built-in MCP tools for Memory operations

Exposes Kagura's memory management features via MCP.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from kagura import tool

if TYPE_CHECKING:
    from kagura.core.memory import MemoryManager

# Global cache for MemoryManager instances (agent_name -> MemoryManager)
# Ensures working memory persists across MCP tool calls for the same agent
_memory_cache: dict[str, MemoryManager] = {}


def _get_memory_manager(agent_name: str, enable_rag: bool = False) -> MemoryManager:
    """Get or create cached MemoryManager instance

    Ensures the same MemoryManager instance is reused across MCP tool calls
    for the same agent_name, allowing working memory to persist.

    Args:
        agent_name: Name of the agent
        enable_rag: Whether to enable RAG (semantic search)

    Returns:
        Cached or new MemoryManager instance
    """
    from kagura.core.memory import MemoryManager

    cache_key = f"{agent_name}:rag={enable_rag}"

    if cache_key not in _memory_cache:
        _memory_cache[cache_key] = MemoryManager(
            agent_name=agent_name, enable_rag=enable_rag
        )

    return _memory_cache[cache_key]


@tool
async def memory_store(
    agent_name: str, key: str, value: str, scope: str = "working"
) -> str:
    """Store information in agent memory

    Stores data in the specified memory scope. When storing in working memory,
    the data is also automatically indexed in RAG (vector DB) for semantic search,
    making it discoverable via memory_search().

    Args:
        agent_name: Name of the agent
        key: Memory key
        value: Information to store
        scope: Memory scope (working/persistent)

    Returns:
        Confirmation message

    Note:
        Working memory data is automatically indexed in RAG for semantic search.
        Use memory_search() to find data stored with this function.
    """
    # Enable RAG for working memory to support semantic search
    enable_rag = scope == "working"

    try:
        memory = _get_memory_manager(agent_name, enable_rag=enable_rag)
    except ImportError:
        # If RAG dependencies not available, create without RAG
        # But keep enable_rag=True for cache key consistency
        from kagura.core.memory import MemoryManager
        cache_key = f"{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    if scope == "persistent":
        memory.remember(key, value)
    else:
        # Store in working memory
        memory.set_temp(key, value)

        # Also index in RAG for semantic search (if available)
        if memory.rag:
            try:
                memory.store_semantic(
                    content=f"{key}: {value}",
                    metadata={"type": "working_memory", "key": key}
                )
            except Exception:
                # Silently fail if RAG indexing fails
                pass

    rag_status = " (RAG unavailable)" if not memory.rag else ""
    return f"Stored '{key}' in {scope} memory for {agent_name}{rag_status}"


@tool
async def memory_recall(agent_name: str, key: str, scope: str = "working") -> str:
    """Recall information from agent memory

    Args:
        agent_name: Name of the agent
        key: Memory key
        scope: Memory scope (working/persistent)

    Returns:
        Stored value or empty string
    """
    # Use same enable_rag logic as memory_store to ensure cache hit
    enable_rag = scope == "working"

    try:
        memory = _get_memory_manager(agent_name, enable_rag=enable_rag)
    except ImportError:
        # If RAG dependencies not available, get from cache with consistent key
        from kagura.core.memory import MemoryManager
        cache_key = f"{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    if scope == "persistent":
        value = memory.recall(key)
    else:
        value = memory.get_temp(key)

    # Return helpful message if value not found
    if value is None:
        return f"No value found for key '{key}' in {scope} memory"

    return str(value)


@tool
async def memory_search(agent_name: str, query: str, k: int = 5) -> str:
    """Search agent memory using semantic RAG and working memory

    Searches both RAG (vector DB) for semantic matches and working memory
    for exact or partial key matches. Results from both sources are combined
    and returned in a unified format.

    Args:
        agent_name: Name of the agent
        query: Search query
        k: Number of results from RAG (working memory results are added separately)

    Returns:
        JSON string of search results with combined RAG and working memory matches

    Note:
        This searches data stored via memory_store() in both RAG (semantic)
        and working memory (key-value). Results include a "source" field
        indicating where the data came from.
    """
    # Ensure k is int (LLM might pass as string)
    if isinstance(k, str):
        try:
            k = int(k)
        except ValueError:
            k = 5  # Default fallback

    try:
        # Use cached MemoryManager with RAG enabled
        memory = _get_memory_manager(agent_name, enable_rag=True)
    except ImportError:
        # If RAG dependencies not available, get from cache with consistent key
        from kagura.core.memory import MemoryManager
        cache_key = f"{agent_name}:rag=True"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    try:
        # Get RAG results (semantic search) if available
        rag_results = []
        if memory.rag:
            rag_results = memory.recall_semantic(query, top_k=k)
            # Add source indicator to RAG results
            for result in rag_results:
                result["source"] = "rag"

        # Search working memory for matching keys
        working_results = []
        query_lower = query.lower()
        for key in memory.working.keys():
            # Match if query is in key name
            if query_lower in key.lower():
                value = memory.get_temp(key)
                working_results.append({
                    "content": f"{key}: {value}",
                    "source": "working_memory",
                    "key": key,
                    "value": str(value),
                    "match_type": "key_match"
                })

        # Combine results (working memory first for exact matches, then RAG)
        combined_results = working_results + rag_results

        return json.dumps(combined_results, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
