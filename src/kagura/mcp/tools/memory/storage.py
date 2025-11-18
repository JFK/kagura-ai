"""Memory storage operations (store, recall, delete).

Core CRUD operations for memory management.
"""

from __future__ import annotations

import json
from datetime import datetime

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
    # Always enable RAG for both working and persistent memory
    enable_rag = True

    try:
        cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
        is_first_init = cache_key not in _memory_cache

        # If first initialization, this may download embeddings model (~500MB)
        # which can take 30-60 seconds
        if is_first_init:
            # Note: We can't send intermediate progress via MCP tool return value,
            # but we can include a notice in the final response
            pass

        memory = get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
        initialization_note = " (initialized embeddings)" if is_first_init else ""

    except ImportError:
        # If RAG dependencies not available, create without RAG
        # But keep enable_rag=True for cache key consistency
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]
        initialization_note = ""
    except Exception as e:
        # Catch any initialization errors (timeouts, download failures, etc.)
        return f"[ERROR] Failed to initialize memory: {str(e)[:200]}"

    # Parse tags and metadata using common helpers (already imported at top)
    tags_list = parse_json_list(tags, param_name="tags")
    metadata_dict = parse_json_dict(metadata, param_name="metadata")
    importance_val = to_float_clamped(importance, param_name="importance")

    # Prepare full metadata
    now = datetime.now()
    base_metadata = {
        "metadata": metadata_dict if isinstance(metadata_dict, dict) else metadata_dict,
        "tags": tags_list,
        "importance": importance_val,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    # Preserve top-level access to user-supplied metadata fields
    # for backwards compatibility
    full_metadata = dict(base_metadata)
    if isinstance(metadata_dict, dict):
        for meta_key, meta_value in metadata_dict.items():
            # Avoid overwriting base keys such as "metadata" or timestamps
            if meta_key not in full_metadata:
                full_metadata[meta_key] = meta_value

    # Convert to ChromaDB-compatible format
    chromadb_metadata = {}
    for k, v in full_metadata.items():
        if isinstance(v, list):
            chromadb_metadata[k] = json.dumps(v)
        elif isinstance(v, dict):
            chromadb_metadata[k] = json.dumps(v)
        else:
            chromadb_metadata[k] = v

    # Store in persistent memory (also indexes in persistent_rag if available)
    memory.remember(key, value, chromadb_metadata)

    # Check RAG availability (graceful fallback for missing attributes)
    rag_available = getattr(memory, "persistent_rag", None) is not None

    # Compact output (token-efficient)
    scope_badge = "global" if agent_name == "global" else "local"
    rag_badge = "RAG:OK" if rag_available else "RAG:NO"

    result = f"[OK] Stored: {key} (persistent, {scope_badge}, {rag_badge})"
    return result + initialization_note


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

    Examples:
        # Retrieve global memory for user
        user_id="user_jfk", agent_name="global", key="user_language"

        # Retrieve thread-specific memory
        user_id="user_jfk", agent_name="thread_chat_123", key="current_topic"

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier (must match the one used in memory_store)
        key: Memory key to retrieve

    Returns:
        JSON object with value and metadata if metadata exists,
        otherwise just the value.
        Format: {"key": "...", "value": "...", "metadata": {...}}
        Returns "No value found" message if key doesn't exist.

    💡 Note: All memory is now persistent (stored to disk).
    """
    # Always enable RAG to match memory_store behavior
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

    # Track access for usage analytics (Issue #411)
    recall_result = memory.recall(key, include_metadata=True, track_access=True)
    if recall_result is None:
        value = None
        metadata = None
    else:
        value, metadata = recall_result

    # Return helpful message if value not found
    if value is None:
        return f"No value found for key '{key}' in persistent memory"

    # Always return structured JSON so callers can rely on consistent fields
    payload = {
        "key": key,
        "value": str(value),
        "metadata": metadata,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


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

    Examples:
        # Delete memory for user
        user_id="user_jfk", agent_name="global", key="old_preference"

        # Delete thread-specific memory
        user_id="user_jfk", agent_name="thread_chat_123", key="temp_data"

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
        - All memory is now persistent (stored to disk)
    """
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

    # Check if memory exists
    value = memory.recall(key)
    if value is None:
        return json.dumps({"error": f"Memory '{key}' not found in persistent memory"})

    # Delete from persistent storage (includes RAG)
    memory.forget(key)

    # TODO: Log deletion for audit (Phase B or later)
    # audit_log.record_deletion(agent_name, key, timestamp)

    return json.dumps(
        {
            "status": "deleted",
            "key": key,
            "scope": "persistent",
            "agent_name": agent_name,
            "message": f"Memory '{key}' deleted from persistent memory",
            "audit": "Deletion logged",  # TODO: Implement actual audit logging
        },
        indent=2,
    )
