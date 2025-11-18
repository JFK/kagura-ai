"""Memory storage operations (store, recall, delete).

Core CRUD operations for memory management.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.mcp.builtin.common import (
    parse_json_dict,
    parse_json_list,
    to_float_clamped,
)
from kagura.mcp.tools.memory.common import _memory_cache, get_memory_manager


@tool
async def memory_store(
    user_id: str,
    key: str,
    value: str,
    agent_name: str = "global",
    tags: str = "[]",
    importance: float = 0.5,
    metadata: str = "{}",
) -> str:
    """Store information in agent memory.

    When: User asks to remember/save something.
    Defaults: agent_name="global" (v4.0.10)

    Args:
        user_id: Memory owner ID
        key: Memory key
        value: Info to store
        agent_name: "global" (all conversations) or "thread_{id}" (this conversation only)
        tags: JSON array '["tag1"]' (optional)
        importance: 0.0-1.0 (default: 0.5)
        metadata: JSON object (optional)

    Returns: Confirmation with storage scope

    💡 Note: All memory is now persistent (stored to disk).
    🌐 Cross-platform: Memories shared across Claude, ChatGPT, Gemini via user_id.
    """
    # Get MemoryManager (with caching for performance)
    enable_rag = True
    try:
        cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
        is_first_init = cache_key not in _memory_cache

        memory = get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
        initialization_note = " (initialized embeddings)" if is_first_init else ""

    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]
        initialization_note = ""
    except Exception as e:
        return f"[ERROR] Failed to initialize memory: {str(e)[:200]}"

    # Parse parameters
    tags_list = parse_json_list(tags, param_name="tags")
    metadata_dict = parse_json_dict(metadata, param_name="metadata")
    importance_val = to_float_clamped(importance, param_name="importance")

    # Use MemoryService for business logic (v4.4.0+)
    try:
        from kagura.services import MemoryService

        service = MemoryService(memory)
        result = service.store_memory(
            key=key,
            value=value,
            tags=tags_list,
            importance=importance_val,
            metadata=metadata_dict,
        )

        if not result.success:
            return f"[ERROR] {result.message}"

        # Check RAG availability
        rag_available = getattr(memory, "persistent_rag", None) is not None
        scope_badge = "global" if agent_name == "global" else "local"
        rag_badge = "RAG:OK" if rag_available else "RAG:NO"

        return f"[OK] Stored: {key} (persistent, {scope_badge}, {rag_badge}){initialization_note}"

    except Exception as e:
        return f"[ERROR] Storage failed: {str(e)[:200]}"


@tool
async def memory_recall(user_id: str, agent_name: str, key: str) -> str:
    """Recall information from agent memory

    Retrieve previously stored information. Use this tool when:
    - User asks 'do you remember...'
    - Need to access previously saved context or preferences
    - Continuing a previous conversation or task

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns this memory (e.g., "user_jfk", email, username)
    - agent_name: WHERE to retrieve from ("global" = all threads, "thread_X" = specific)

    🌐 CROSS-PLATFORM: All memories are tied to user_id, enabling
        true Universal Memory across Claude, ChatGPT, Gemini, etc.

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier (must match the one used in memory_store)
        key: Memory key to retrieve

    Returns:
        JSON object with value and metadata
        Format: {"key": "...", "value": "...", "metadata": {...}}

    💡 Note: All memory is now persistent (stored to disk).
    """
    # Get MemoryManager
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

    # Use MemoryService for business logic (v4.4.0+)
    try:
        from kagura.services import MemoryService

        service = MemoryService(memory)
        result = service.recall_memory(key)

        if not result.success:
            return f"No value found for key '{key}' in persistent memory"

        # Return structured JSON
        payload = {
            "key": key,
            "value": result.metadata.get("value", ""),
            "metadata": result.metadata,
        }

        return json.dumps(payload, ensure_ascii=False, indent=2, default=str)

    except Exception as e:
        return f"[ERROR] Recall failed: {str(e)[:200]}"


@tool
async def memory_delete(user_id: str, agent_name: str, key: str) -> str:
    """Delete a memory with audit logging

    Permanently delete a memory from storage. Use this tool when:
    - User explicitly asks to forget something
    - Memory is outdated and should be removed
    - Cleaning up data

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns this memory (deletion scoped to user)
    - agent_name: WHERE the memory is stored

    💡 IMPORTANT: Deletion is permanent and logged for audit.

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        key: Memory key to delete

    Returns:
        Confirmation message with deletion details

    Note:
        - Deletion is logged with timestamp and user_id
        - Both key-value memory and RAG entries are deleted
        - For GDPR compliance: Complete deletion guaranteed
    """
    # Get MemoryManager
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

    # Use MemoryService for business logic (v4.4.0+)
    try:
        from kagura.services import MemoryService

        service = MemoryService(memory)
        result = service.delete_memory(key)

        if not result.success:
            return json.dumps({"error": result.message})

        return json.dumps(
            {
                "status": "deleted",
                "key": key,
                "scope": "persistent",
                "agent_name": agent_name,
                "message": result.message,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"error": f"Deletion failed: {str(e)[:200]}"})
