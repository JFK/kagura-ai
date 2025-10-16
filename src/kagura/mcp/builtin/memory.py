"""Built-in MCP tools for Memory operations

Exposes Kagura's memory management features via MCP.
"""

from __future__ import annotations

import json

from kagura import tool


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
    from kagura.core.memory import MemoryManager

    memory = MemoryManager(agent_name=agent_name)

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
    from kagura.core.memory import MemoryManager

    memory = MemoryManager(agent_name=agent_name)

    if scope == "persistent":
        value = memory.recall(key)
    else:
        value = memory.get_temp(key)

    return str(value) if value else ""


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
    try:
        from kagura.core.memory import MemoryManager

        memory = MemoryManager(agent_name=agent_name, enable_rag=True)
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
