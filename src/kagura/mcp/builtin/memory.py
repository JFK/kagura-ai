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

    Stores data in the specified memory scope. Use this tool when:
    - User explicitly asks to 'remember' or 'save' something
    - Important context needs to be preserved
    - User preferences or settings should be stored

    💡 IMPORTANT: agent_name determines memory sharing behavior:
    - agent_name="global": Shared across ALL chat threads
      (for user preferences, global facts)
    - agent_name="thread_specific": Isolated per thread
      (for conversation-specific context)

    Examples:
        # Global memory (accessible from all threads)
        agent_name="global", key="user_language", value="Japanese"

        # Thread-specific memory (only this conversation)
        agent_name="thread_chat_123", key="current_topic", value="Python tutorial"

    Args:
        agent_name: Agent identifier (use "global" for cross-thread sharing)
        key: Memory key for retrieval
        value: Information to store
        scope: Memory scope - "persistent" (disk, survives restart)
            or "working" (in-memory)

    Returns:
        Confirmation message

    Note:
        Both working and persistent memory data are automatically indexed in RAG
        for semantic search. Use memory_search() to find data stored with this function.
    """
    # Always enable RAG for both working and persistent memory
    enable_rag = True

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
        # Store in persistent memory (also indexes in persistent_rag if available)
        memory.remember(key, value)
    else:
        # Store in working memory
        memory.set_temp(key, value)

        # Also index in working RAG for semantic search (if available)
        if memory.rag:
            try:
                memory.store_semantic(
                    content=f"{key}: {value}",
                    metadata={"type": "working_memory", "key": key}
                )
            except Exception:
                # Silently fail if RAG indexing fails
                pass

    # Check RAG availability based on scope
    rag_available = (
        (scope == "working" and memory.rag is not None) or
        (scope == "persistent" and memory.persistent_rag is not None)
    )
    rag_status = "" if rag_available else " (RAG unavailable)"
    return f"Stored '{key}' in {scope} memory for {agent_name}{rag_status}"


@tool
async def memory_recall(agent_name: str, key: str, scope: str = "working") -> str:
    """Recall information from agent memory

    Retrieve previously stored information. Use this tool when:
    - User asks 'do you remember...'
    - Need to access previously saved context or preferences
    - Continuing a previous conversation or task

    💡 IMPORTANT: Use the SAME agent_name as when storing:
    - agent_name="global": Retrieve globally shared memories
    - agent_name="thread_specific": Retrieve thread-specific memories

    Examples:
        # Retrieve global memory
        agent_name="global", key="user_language"

        # Retrieve thread-specific memory
        agent_name="thread_chat_123", key="current_topic"

    Args:
        agent_name: Agent identifier (must match the one used in memory_store)
        key: Memory key to retrieve
        scope: Memory scope (working/persistent)

    Returns:
        Stored value or "No value found" message
    """
    # Always enable RAG to match memory_store behavior
    enable_rag = True

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
async def memory_search(
    agent_name: str, query: str, k: int = 5, scope: str = "all"
) -> str:
    """Search agent memory using semantic RAG and key-value memory

    Search stored memories using semantic similarity and keyword matching.
    Use this tool when:
    - User asks about topics discussed before but doesn't specify exact key
    - Need to find related memories without exact match
    - Exploring what has been remembered about a topic

    💡 IMPORTANT: Searches are scoped by agent_name:
    - agent_name="global": Search globally shared memories
    - agent_name="thread_specific": Search thread-specific memories

    Examples:
        # Search global memory
        agent_name="global", query="user preferences"

        # Search thread memory
        agent_name="thread_chat_123", query="topics we discussed"

    Args:
        agent_name: Agent identifier (determines which memory space to search)
        query: Search query (semantic and keyword matching)
        k: Number of results from RAG per scope
        scope: Memory scope to search ("working", "persistent", or "all")

    Returns:
        JSON string of search results with combined RAG and key-value matches

    Note:
        Searches data stored via memory_store() in:
        - RAG (semantic search across working/persistent/all)
        - Working memory (key-value, exact/partial key matches)
        Results include "source" and "scope" fields.
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
        # Get RAG results (semantic search) across specified scope
        rag_results = []
        if memory.rag or memory.persistent_rag:
            rag_results = memory.recall_semantic(query, top_k=k, scope=scope)
            # Add source indicator to RAG results
            for result in rag_results:
                result["source"] = "rag"

        # Search working memory for matching keys (only if scope includes working)
        working_results = []
        if scope in ("all", "working"):
            query_lower = query.lower()
            for key in memory.working.keys():
                # Match if query is in key name
                if query_lower in key.lower():
                    value = memory.get_temp(key)
                    working_results.append({
                        "content": f"{key}: {value}",
                        "source": "working_memory",
                        "scope": "working",
                        "key": key,
                        "value": str(value),
                        "match_type": "key_match"
                    })

        # Combine results (working memory first for exact matches, then RAG)
        combined_results = working_results + rag_results

        return json.dumps(combined_results, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def memory_list(
    agent_name: str, scope: str = "persistent", limit: int = 50
) -> str:
    """List all stored memories for debugging and exploration

    List all memories stored for the specified agent. Use this tool when:
    - User asks "what do you remember about me?"
    - Debugging memory issues
    - Exploring what has been stored

    💡 IMPORTANT: Lists memories for specific agent_name:
    - agent_name="global": List globally shared memories
    - agent_name="thread_specific": List thread-specific memories

    Examples:
        # List global memories
        agent_name="global", scope="persistent"

        # List thread-specific working memory
        agent_name="thread_chat_123", scope="working"

    Args:
        agent_name: Agent identifier
        scope: Memory scope (working/persistent)
        limit: Maximum number of entries to return (default: 50)

    Returns:
        JSON list of stored memories with keys, values, and metadata
    """
    # Always enable RAG to match other memory tools
    enable_rag = True

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

    try:
        results = []

        if scope == "persistent":
            # Get all persistent memories for this agent
            memories = memory.persistent.search("%", agent_name, limit=limit)
            for mem in memories:
                results.append(
                    {
                        "key": mem["key"],
                        "value": mem["value"],
                        "scope": "persistent",
                        "created_at": mem.get("created_at"),
                        "updated_at": mem.get("updated_at"),
                        "metadata": mem.get("metadata"),
                    }
                )
        else:  # working
            # Get all working memory keys
            for key in memory.working.keys():
                value = memory.get_temp(key)
                results.append(
                    {
                        "key": key,
                        "value": str(value),
                        "scope": "working",
                        "metadata": None,
                    }
                )

            # Limit results
            results = results[:limit]

        return json.dumps(
            {
                "agent_name": agent_name,
                "scope": scope,
                "count": len(results),
                "memories": results,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"error": str(e)})
