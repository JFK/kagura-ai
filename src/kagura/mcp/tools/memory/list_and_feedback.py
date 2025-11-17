"""Memory listing and feedback operations.

List memories and provide feedback for importance scoring.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from kagura import tool
from kagura.mcp.builtin.common import format_error, to_float_clamped, to_int
from kagura.mcp.tools.memory.common import _memory_cache, get_memory_manager


def _datetime_handler(obj: Any) -> str:
    """JSON serialization handler for datetime objects.

    Args:
        obj: Object to serialize

    Returns:
        ISO format string for datetime objects

    Raises:
        TypeError: For unsupported types
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@tool
async def memory_list(
    user_id: str, agent_name: str, scope: str = "persistent", limit: int = 10
) -> str:
    """List all stored memories for debugging and exploration

    List all memories stored for the specified user and agent. Use this tool when:
    - User asks "what do you remember about me?"
    - Debugging memory issues
    - Exploring what has been stored

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns these memories (lists only this user's data)
    - agent_name: WHERE to list from ("global" = all threads, "thread_X" = specific)

    🌐 CROSS-PLATFORM: Lists are scoped by user_id, showing only
        memories owned by this user across all AI platforms.

    Examples:
        # List global memories for user
        user_id="user_jfk", agent_name="global", scope="persistent"

        # List thread-specific working memory
        user_id="user_jfk", agent_name="thread_chat_123", scope="working"

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        scope: Memory scope (working/persistent)
        limit: Maximum number of entries to return
            (default: 10, reduced from 50 for token efficiency)

    Returns:
        JSON list of stored memories with keys, values, and metadata
    """
    # Convert limit to int using common helper
    limit = to_int(limit, default=50, min_val=1, max_val=1000, param_name="limit")

    # Always enable RAG to match other memory tools
    enable_rag = True

    try:
        memory = get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
    except ImportError:
        # If RAG dependencies not available, get from cache with consistent key
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    try:
        results = []

        if scope == "persistent":
            # Get all persistent memories for this user and agent
            memories = memory.persistent.search("%", user_id, agent_name, limit=limit)
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
            # Get all working memory keys (exclude internal _meta_ keys)
            for key in memory.working.keys():
                # Skip internal metadata keys
                if key.startswith("_meta_"):
                    continue

                value = memory.working.get(key)
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
            default=_datetime_handler,
        )

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def memory_feedback(
    user_id: str,
    agent_name: str,
    key: str,
    label: str,
    weight: float = 1.0,
    scope: str = "persistent",
) -> str:
    """Provide feedback on memory usefulness

    Provide feedback to improve memory quality and importance scoring.
    Use this tool when:
    - A memory was helpful in answering a question
    - A memory is outdated or no longer relevant
    - A memory should be prioritized or deprioritized

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns this memory (feedback applies to user's memory)
    - agent_name: WHERE the memory is stored

    💡 Feedback Types:
    - label="useful": Memory was helpful (+weight to importance)
    - label="irrelevant": Memory not relevant (-weight)
    - label="outdated": Memory is old/stale (-weight, candidate for removal)

    Examples:
        # Mark memory as useful for user
        user_id="user_jfk", agent_name="global", key="user_language",
        label="useful", weight=0.2

        # Mark memory as outdated
        user_id="user_jfk", agent_name="global", key="old_preference",
        label="outdated", weight=0.5

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        key: Memory key to provide feedback on
        label: Feedback type ("useful", "irrelevant", "outdated")
        weight: Feedback strength (0.0-1.0, default 1.0)
        scope: Memory scope (working/persistent)

    Returns:
        Confirmation message with updated importance score

    Note:
        Importance scoring uses Hebbian-like learning:
        - Useful memories: importance increases
        - Irrelevant/outdated: importance decreases
        - Future: Will influence recall ranking
    """
    # Validate inputs
    if label not in ("useful", "irrelevant", "outdated"):
        return format_error(
            f"Invalid label: {label}",
            help_text="Use: useful, irrelevant, or outdated",
        )

    # Convert weight to float using common helper
    weight = to_float_clamped(
        weight, min_val=0.0, max_val=1.0, default=1.0, param_name="weight"
    )

    enable_rag = True
    try:
        memory = get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    # Get current memory
    if scope == "persistent":
        value = memory.recall(key)
        if value is None:
            return json.dumps({"error": f"Memory '{key}' not found in {scope} memory"})

        # Get metadata from persistent storage
        mem_list = memory.search_memory(f"%{key}%", limit=1)
        if not mem_list:
            return json.dumps({"error": f"Metadata for '{key}' not found"})

        mem_data = mem_list[0]
        metadata_dict = mem_data.get("metadata", {})

        # Decode metadata if JSON strings
        import json as json_lib

        if isinstance(metadata_dict.get("tags"), str):
            try:
                metadata_dict["tags"] = json_lib.loads(metadata_dict["tags"])
            except json_lib.JSONDecodeError:
                pass
        if isinstance(metadata_dict.get("importance"), str):
            try:
                metadata_dict["importance"] = float(metadata_dict["importance"])
            except (ValueError, TypeError):
                metadata_dict["importance"] = 0.5

        current_importance = metadata_dict.get("importance", 0.5)

        # Update importance based on feedback
        if label == "useful":
            new_importance = min(1.0, current_importance + weight * 0.1)
        else:  # irrelevant or outdated
            new_importance = max(0.0, current_importance - weight * 0.1)

        metadata_dict["importance"] = new_importance

        # Convert back to ChromaDB-compatible format
        chromadb_metadata = {}
        for k, v in metadata_dict.items():
            if isinstance(v, list):
                chromadb_metadata[k] = json_lib.dumps(v)
            elif isinstance(v, dict):
                chromadb_metadata[k] = json_lib.dumps(v)
            else:
                chromadb_metadata[k] = v

        # Update memory (delete and recreate)
        memory.forget(key)
        memory.remember(key, value, chromadb_metadata)

        return json.dumps(
            {
                "status": "success",
                "key": key,
                "label": label,
                "weight": weight,
                "importance": {
                    "previous": current_importance,
                    "current": new_importance,
                    "delta": new_importance - current_importance,
                },
            },
            indent=2,
        )
    else:
        # Working memory feedback - update metadata
        value = memory.get_temp(key)
        if value is None:
            return json.dumps({"error": f"Memory '{key}' not found in {scope} memory"})

        metadata_dict = memory.get_temp(f"_meta_{key}", {})
        current_importance = metadata_dict.get("importance", 0.5)

        # Update importance
        if label == "useful":
            new_importance = min(1.0, current_importance + weight * 0.1)
        else:
            new_importance = max(0.0, current_importance - weight * 0.1)

        metadata_dict["importance"] = new_importance
        memory.set_temp(f"_meta_{key}", metadata_dict)

        return json.dumps(
            {
                "status": "success",
                "key": key,
                "label": label,
                "weight": weight,
                "importance": {
                    "previous": current_importance,
                    "current": new_importance,
                    "delta": new_importance - current_importance,
                },
            },
            indent=2,
        )
