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

    Args:
        agent_name: Name of the agent
        key: Memory key
        value: Information to store
        scope: Memory scope (working/persistent)

    Returns:
        Confirmation message
    """
    # Use cached MemoryManager to ensure working memory persists
    memory = _get_memory_manager(agent_name)

    if scope == "persistent":
        memory.remember(key, value)
    else:
        memory.set_temp(key, value)

    return f"Stored '{key}' in {scope} memory for {agent_name}"


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
    # Use cached MemoryManager to ensure working memory persists
    memory = _get_memory_manager(agent_name)

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
    """Search agent memory using semantic RAG

    Args:
        agent_name: Name of the agent
        query: Search query
        k: Number of results

    Returns:
        JSON string of search results
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
        results = memory.recall_semantic(query, top_k=k)

        return json.dumps(results, indent=2)
    except ImportError:
        return json.dumps(
            {
                "error": "MemoryRAG requires 'ai' extra. "
                "Install with: pip install kagura-ai[ai]"
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})
