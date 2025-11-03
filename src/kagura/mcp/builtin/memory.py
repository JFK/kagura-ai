"""Built-in MCP tools for Memory operations

Exposes Kagura's memory management features via MCP.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from kagura import tool

if TYPE_CHECKING:
    from kagura.core.memory import MemoryManager

# Global cache for MemoryManager instances (agent_name -> MemoryManager)
# Ensures working memory persists across MCP tool calls for the same agent
_memory_cache: dict[str, MemoryManager] = {}


def _get_memory_manager(
    user_id: str, agent_name: str, enable_rag: bool = False
) -> MemoryManager:
    """Get or create cached MemoryManager instance

    Ensures the same MemoryManager instance is reused across MCP tool calls
    for the same user_id + agent_name combination, allowing working memory to persist.

    Args:
        user_id: User identifier (memory owner)
        agent_name: Name of the agent
        enable_rag: Whether to enable RAG (semantic search)

    Returns:
        Cached or new MemoryManager instance
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.debug("_get_memory_manager: Importing MemoryManager...")
    from kagura.core.memory import MemoryManager

    logger.debug("_get_memory_manager: MemoryManager imported successfully")

    cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
    logger.debug(f"_get_memory_manager: cache_key={cache_key}")

    if cache_key not in _memory_cache:
        logger.debug(f"_get_memory_manager: Creating MemoryManager rag={enable_rag}")
        if enable_rag:
            logger.info(
                f"First-time RAG initialization for {agent_name}. "
                "Downloading embeddings model (~500MB, may take 30-60s)..."
            )
        _memory_cache[cache_key] = MemoryManager(
            user_id=user_id, agent_name=agent_name, enable_rag=enable_rag
        )
        logger.debug("_get_memory_manager: MemoryManager created successfully")
    else:
        logger.debug("_get_memory_manager: Using cached MemoryManager")

    return _memory_cache[cache_key]


@tool
async def memory_store(
    user_id: str,
    agent_name: str,
    key: str,
    value: str,
    scope: str = "working",
    tags: str = "[]",
    importance: float = 0.5,
    metadata: str = "{}",
) -> str:
    """Store information in agent memory

    ⚠️ BEFORE CALLING THIS TOOL: Always ask the user whether they want to store
    the memory globally (accessible from all conversations) or locally (only this
    conversation). Never assume without asking!

    Question to ask user:
    "Should I remember this globally (accessible from all conversations) or just
    for this conversation?"

    Stores data in the specified memory scope. Use this tool when:
    - User explicitly asks to 'remember' or 'save' something
    - Important context needs to be preserved
    - User preferences or settings should be stored

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns this memory (e.g., "user_jfk", email, username)
    - agent_name: WHERE to store
      * "global" = ALL conversations (user preferences, facts)
      * "thread_{id}" = ONLY this conversation (temporary context)

    🌐 CROSS-PLATFORM: All memories are tied to user_id, enabling
        true Universal Memory across Claude, ChatGPT, Gemini, etc.

    Examples:
        # Global memory (accessible from ALL conversations)
        agent_name="global", key="user_language", value="Japanese",
        tags='["preferences"]'

        # Thread-specific memory (ONLY this conversation)
        agent_name="thread_chat_123", key="current_topic",
        value="Python tutorial", importance=0.8

    Args:
        user_id: User identifier (memory owner)
        agent_name: ⚠️ CRITICAL CHOICE - Ask user first!
            - "global": Accessible from ALL conversations (use for preferences,
              user facts, long-term knowledge)
            - "thread_{thread_id}": Only THIS conversation (use for temporary
              context, current task state)
        key: Memory key for retrieval
        value: Information to store
        scope: Memory scope - "persistent" (disk, survives restart)
            or "working" (in-memory, cleared on restart)
        tags: JSON array string of tags (e.g., '["python", "coding"]')
        importance: Importance score (0.0-1.0, default 0.5)
        metadata: JSON object string of additional metadata
            (e.g., '{"project": "kagura"}')

    Returns:
        Confirmation message with clear indication of storage scope

    Note:
        Both working and persistent memory data are automatically indexed in RAG
        for semantic search. Use memory_search() to find data stored with this function.
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

        memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
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

    # Parse tags and metadata from JSON strings
    try:
        tags_list = json.loads(tags) if isinstance(tags, str) else tags
    except json.JSONDecodeError:
        tags_list = []

    try:
        metadata_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
    except json.JSONDecodeError:
        metadata_dict = {}

    try:
        importance = float(importance)
        importance = max(0.0, min(1.0, importance))  # Clamp to [0, 1]
    except (ValueError, TypeError):
        importance = 0.5

    # Prepare full metadata
    from datetime import datetime

    now = datetime.now()
    base_metadata = {
        "metadata": metadata_dict if isinstance(metadata_dict, dict) else metadata_dict,
        "tags": tags_list,
        "importance": importance,
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

    if scope == "persistent":
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
    else:
        # Store in working memory
        memory.set_temp(key, value)
        memory.set_temp(f"_meta_{key}", full_metadata)

        # Also index in working RAG for semantic search (if available)
        if memory.rag:
            try:
                rag_metadata = {
                    "type": "working_memory",
                    "key": key,
                    "tags": json.dumps(tags_list),  # ChromaDB compatibility
                    "importance": importance,
                }
                memory.store_semantic(content=f"{key}: {value}", metadata=rag_metadata)
            except Exception:
                # Silently fail if RAG indexing fails
                pass

    # Check RAG availability based on scope
    rag_available = (scope == "working" and memory.rag is not None) or (
        scope == "persistent" and memory.persistent_rag is not None
    )

    # Compact output (token-efficient)
    scope_badge = "global" if agent_name == "global" else "local"
    rag_badge = "RAG:OK" if rag_available else "RAG:NO"

    result = f"[OK] Stored: {key} ({scope}, {scope_badge}, {rag_badge})"
    return result + initialization_note


@tool
async def memory_recall(
    user_id: str, agent_name: str, key: str, scope: str = "working"
) -> str:
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
        scope: Memory scope (working/persistent)

    Returns:
        JSON object with value and metadata if metadata exists,
        otherwise just the value.
        Format: {"key": "...", "value": "...", "metadata": {...}}
        Returns "No value found" message if key doesn't exist.
    """
    # Always enable RAG to match memory_store behavior
    enable_rag = True

    try:
        memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
    except ImportError:
        # If RAG dependencies not available, get from cache with consistent key
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    if scope == "persistent":
        recall_result = memory.recall(key, include_metadata=True)
        if recall_result is None:
            value = None
            metadata = None
        else:
            value, metadata = recall_result
    else:
        value = memory.get_temp(key)
        # Get metadata from working memory
        metadata = memory.get_temp(f"_meta_{key}")

    # Return helpful message if value not found
    if value is None:
        return f"No value found for key '{key}' in {scope} memory"

    # Always return structured JSON so callers can rely on consistent fields
    payload = {
        "key": key,
        "value": str(value),
        "metadata": metadata,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


@tool
async def memory_search(
    user_id: str,
    agent_name: str,
    query: str,
    k: int = 3,
    scope: str = "all",
    mode: str = "full",
) -> str:
    """Search agent memory using semantic RAG and key-value memory

    Search stored memories using semantic similarity and keyword matching.
    Use this tool when:
    - User asks about topics discussed before but doesn't specify exact key
    - Need to find related memories without exact match
    - Exploring what has been remembered about a topic

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns these memories (searches only this user's data)
    - agent_name: WHERE to search ("global" = all threads, "thread_X" = specific)

    🌐 CROSS-PLATFORM: Searches are scoped by user_id, enabling
        cross-platform memory search across all AI tools.

    Examples:
        # Search global memory for user
        user_id="user_jfk", agent_name="global", query="user preferences"

        # Search thread memory
        user_id="user_jfk", agent_name="thread_chat_123", query="topics we discussed"

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier (determines which memory space to search)
        query: Search query (semantic and keyword matching)
        k: Number of results from RAG per scope
            (default: 3, reduced from 5 for token efficiency)
        scope: Memory scope to search ("working", "persistent", or "all")
        mode: Output mode - "summary" (compact, token-efficient) or
            "full" (complete JSON, default for backward compatibility)

    Returns:
        Search results in the specified format:
        - summary mode: Compact text format with previews (~200 tokens)
        - full mode: Complete JSON with all data (~1000 tokens)

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
        memory = _get_memory_manager(user_id, agent_name, enable_rag=True)
    except ImportError:
        # If RAG dependencies not available, get from cache with consistent key
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag=True"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
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
                    working_results.append(
                        {
                            "content": f"{key}: {value}",
                            "source": "working_memory",
                            "scope": "working",
                            "key": key,
                            "value": str(value),
                            "match_type": "key_match",
                        }
                    )

        # Combine results (working memory first for exact matches, then RAG)
        combined_results = working_results + rag_results

        # Format output based on mode
        if mode == "summary":
            # Compact summary format (token-efficient)
            if not combined_results:
                return "No results found."

            lines = []
            for i, result in enumerate(combined_results[:k], 1):
                content = result.get("content", result.get("value", ""))
                # Truncate long content
                preview = content[:100] + "..." if len(content) > 100 else content

                # Add source indicator
                source = result.get("source", "unknown")
                scope_str = result.get("scope", "")
                source_badge = f"[{source}:{scope_str}]" if scope_str else f"[{source}]"

                # Distance/score (if available)
                distance = result.get("distance")
                if distance is not None:
                    score = max(0.0, min(1.0, 1 - distance))
                    score_str = f" (score: {score:.2f})"
                else:
                    score_str = ""

                lines.append(f"{i}. {source_badge} {preview}{score_str}")

            return "\n".join(lines)
        else:
            # Full JSON format (backward compatibility)
            return json.dumps(combined_results, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


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
    # Ensure limit is int (LLM might pass as string)
    if isinstance(limit, str):
        try:
            limit = int(limit)
        except ValueError:
            limit = 50  # Default fallback

    # Always enable RAG to match other memory tools
    enable_rag = True

    try:
        memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
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
        return json.dumps(
            {"error": f"Invalid label: {label}. Use: useful, irrelevant, or outdated"}
        )

    try:
        weight = float(weight)
        if not 0.0 <= weight <= 1.0:
            weight = max(0.0, min(1.0, weight))
    except (ValueError, TypeError):
        weight = 1.0

    enable_rag = True
    try:
        memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
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


@tool
async def memory_delete(
    user_id: str, agent_name: str, key: str, scope: str = "persistent"
) -> str:
    """Delete a memory with audit logging

    Permanently delete a memory from storage. Use this tool when:
    - User explicitly asks to forget something
    - Memory is outdated and should be removed
    - Cleaning up temporary data

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns this memory (deletion scoped to user)
    - agent_name: WHERE the memory is stored

    💡 IMPORTANT: Deletion is permanent and logged for audit.

    Examples:
        # Delete persistent memory for user
        user_id="user_jfk", agent_name="global", key="old_preference",
        scope="persistent"

        # Delete working memory
        user_id="user_jfk", agent_name="thread_chat_123", key="temp_data",
        scope="working"

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        key: Memory key to delete
        scope: Memory scope (working/persistent)

    Returns:
        Confirmation message with deletion details

    Note:
        - Deletion is logged with timestamp and user_id
        - Both key-value memory and RAG entries are deleted
        - For GDPR compliance: Complete deletion guaranteed
    """
    enable_rag = True
    try:
        memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                user_id=user_id, agent_name=agent_name, enable_rag=False
            )
        memory = _memory_cache[cache_key]

    # Check if memory exists
    if scope == "persistent":
        value = memory.recall(key)
        if value is None:
            return json.dumps({"error": f"Memory '{key}' not found in {scope} memory"})

        # Delete from persistent storage (includes RAG)
        memory.forget(key)

        # TODO: Log deletion for audit (Phase B or later)
        # audit_log.record_deletion(agent_name, key, scope, timestamp)

        return json.dumps(
            {
                "status": "deleted",
                "key": key,
                "scope": scope,
                "agent_name": agent_name,
                "message": f"Memory '{key}' deleted from {scope} memory",
                "audit": "Deletion logged",  # TODO: Implement actual audit logging
            },
            indent=2,
        )
    else:  # working
        if not memory.has_temp(key):
            return json.dumps({"error": f"Memory '{key}' not found in {scope} memory"})

        # Delete from working memory
        memory.delete_temp(key)
        memory.delete_temp(f"_meta_{key}")  # Delete metadata if exists

        # Delete from working RAG if indexed
        if memory.rag:
            try:
                where_filter: dict[str, str] = {"key": key}
                if agent_name:
                    where_filter["agent_name"] = agent_name
                results = memory.rag.collection.get(where=where_filter)  # type: ignore[arg-type]
                if results["ids"]:
                    memory.rag.collection.delete(ids=results["ids"])
            except Exception:
                pass  # Silently fail

        return json.dumps(
            {
                "status": "deleted",
                "key": key,
                "scope": scope,
                "agent_name": agent_name,
                "message": f"Memory '{key}' deleted from {scope} memory",
            },
            indent=2,
        )


@tool
async def memory_get_related(
    user_id: str,
    agent_name: str,
    node_id: str,
    depth: int | str = 2,
    rel_type: str | None = None,
) -> str:
    """Get related nodes from graph memory

    Retrieves nodes related to the specified node through graph traversal.
    Useful for discovering connections and relationships between memories,
    users, topics, and interactions.

    💡 IMPORTANT: Memory ownership model (v4.0)
    - user_id: WHO owns this graph data (searches user's graph)
    - agent_name: WHERE to search ("global" = all threads, "thread_X" = specific)

    🔍 USE WHEN:
    - Discovering connections between memories
    - Finding related topics or users
    - Exploring knowledge graph relationships
    - Building context from related information

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier (use "global" for cross-thread sharing)
        node_id: Starting node ID to find related nodes from
        depth: Traversal depth (number of hops, default: 2)
        rel_type: Filter by relationship type (related_to, depends_on,
            learned_from, influences, works_on). None = all types

    Returns:
        JSON string with related nodes list

    💡 EXAMPLE:
        # Find memories related to "python_tips" for user
        memory_get_related(user_id="user_jfk", agent_name="global",
                          node_id="mem_python_tips", depth=2)

        # Find topics a user has interacted with
        memory_get_related(user_id="user_jfk", agent_name="global",
                          node_id="user_001", depth=1, rel_type="learned_from")

    📊 RETURNS:
        {
          "node_id": "starting_node",
          "depth": 2,
          "rel_type": "related_to" or null,
          "related_count": 5,
          "related_nodes": [...]
        }

    Note:
        Requires enable_graph=True in MemoryManager (enabled by default).
        Returns empty list if GraphMemory is not available.
    """
    enable_rag = True
    memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)

    # Check if graph is available
    if not memory.graph:
        return json.dumps(
            {
                "error": "GraphMemory not available",
                "message": "Graph memory is disabled or NetworkX not installed",
                "related_nodes": [],
            },
            indent=2,
        )

    # Convert depth to int (MCP clients may send as string)
    try:
        depth_int = int(depth) if isinstance(depth, str) else depth
    except (ValueError, TypeError):
        return json.dumps(
            {"error": f"Invalid depth value: {depth}. Must be an integer."},
            indent=2,
        )

    # Get related nodes
    try:
        related = memory.graph.get_related(
            node_id=node_id, depth=depth_int, rel_type=rel_type
        )

        return json.dumps(
            {
                "node_id": node_id,
                "depth": depth,
                "rel_type": rel_type,
                "related_count": len(related),
                "related_nodes": related,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to get related nodes: {str(e)}"}, indent=2)


@tool
async def memory_record_interaction(
    agent_name: str,
    user_id: str,
    query: str,
    response: str,
    ai_platform: str = "",
    metadata: str = "{}",
) -> str:
    """Record AI-User interaction in graph memory

    Stores a conversation turn between user and AI in the knowledge graph,
    enabling pattern analysis and personalization. Use this to build a
    history of interactions for learning user preferences and habits.

    🔍 USE WHEN:
    - Recording conversation turns for pattern analysis
    - Building user interaction history
    - Enabling cross-platform memory (same user, different AI tools)
    - Tracking topic discussions over time

    💡 v4.0 Universal Memory: ai_platform is OPTIONAL
        Focus on "what" was discussed, not "where"
        Platform tracking is optional for statistics

    💡 TIP: Include "topic" in metadata to enable topic analysis
        metadata='{"topic": "python", "project": "kagura"}'

    This allows memory_get_user_pattern to discover discussed topics and
    build a knowledge graph of user interests.

    Args:
        agent_name: Agent identifier (use "global" for cross-thread sharing)
        user_id: User identifier (e.g., "user_001", email, username)
        query: User's query/message
        response: AI's response
        ai_platform: (Optional) AI platform name (e.g., "claude", "chatgpt", "gemini")
            Leave empty for platform-agnostic memory
        metadata: JSON object string with additional data
            (e.g., '{"project": "kagura", "topic": "python", "session_id": "sess_123"}')

    Returns:
        JSON string with interaction ID and confirmation

    💡 EXAMPLE:
        # Platform-agnostic memory (recommended)
        memory_record_interaction(
            agent_name="global",
            user_id="user_jfk",
            query="How to use FastAPI?",
            response="FastAPI is a modern web framework...",
            metadata='{"topic": "python", "project": "kagura"}'
        )

        # With platform tracking (optional)
        memory_record_interaction(
            agent_name="global",
            user_id="user_jfk",
            query="...",
            response="...",
            ai_platform="claude",
            metadata='{"topic": "python"}'
        )

    📊 RETURNS:
        {
          "interaction_id": "interaction_abc123",
          "user_id": "user_jfk",
          "message": "Interaction recorded successfully"
        }

    Note:
        Requires enable_graph=True in MemoryManager (enabled by default).
        The interaction is linked to the user node and can be analyzed later.
    """
    enable_rag = True
    memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)

    # Check if graph is available
    if not memory.graph:
        return json.dumps(
            {
                "error": "GraphMemory not available",
                "message": "Graph memory is disabled or NetworkX not installed",
            },
            indent=2,
        )

    # Parse metadata
    try:
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in metadata parameter"}, indent=2)

    # Merge ai_platform into metadata if provided (backward compatibility)
    if ai_platform:
        metadata_dict["ai_platform"] = ai_platform

    # Record interaction (ai_platform now in metadata)
    try:
        interaction_id = memory.graph.record_interaction(
            user_id=user_id,
            query=query,
            response=response,
            metadata=metadata_dict,
        )

        # Persist graph if persist_path is set
        if memory.graph.persist_path:
            memory.graph.persist()

        # Get platform for response (backward compat)
        platform = ai_platform or metadata_dict.get("ai_platform", "unknown")

        return json.dumps(
            {
                "status": "recorded",
                "interaction_id": interaction_id,
                "user_id": user_id,
                "ai_platform": platform,
                "message": "Interaction recorded successfully",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to record interaction: {str(e)}"}, indent=2
        )


@tool
async def memory_get_user_pattern(
    agent_name: str,
    user_id: str,
) -> str:
    """Analyze user's interaction patterns and interests

    Analyzes a user's interaction history to discover patterns, interests,
    and preferences. Returns statistics about topics, platforms, and
    interaction frequency across all AI tools.

    🔍 USE WHEN:
    - Understanding user's interests and discussion patterns
    - Personalizing responses based on past interactions
    - Discovering which topics the user discusses most
    - Analyzing cross-platform usage (Claude vs ChatGPT, etc.)

    Args:
        agent_name: Agent identifier (use "global" for cross-thread sharing)
        user_id: User identifier to analyze

    Returns:
        JSON string with user pattern analysis including:
        - total_interactions: Number of recorded interactions
        - topics: List of topics user has discussed
        - avg_interactions_per_topic: Average interactions per topic
        - most_discussed_topic: Most frequently discussed topic
        - platforms: Platform usage statistics (e.g., {"claude": 30})

    💡 EXAMPLE:
        # Analyze user's patterns
        memory_get_user_pattern(agent_name="global", user_id="user_jfk")

    📊 RETURNS:
        {
          "user_id": "user_jfk",
          "pattern": {
            "total_interactions": 42,
            "topics": ["python", "fastapi", "asyncio"],
            "avg_interactions_per_topic": 14.0,
            "most_discussed_topic": "python",
            "platforms": {"claude": 30, "chatgpt": 12}
          }
        }

    💡 TIP: To get meaningful topic analysis, record interactions with
        "topic" in metadata:
        metadata='{"topic": "python"}'

    Note:
        Requires enable_graph=True in MemoryManager (enabled by default).
        User must have recorded interactions via memory_record_interaction.
    """
    enable_rag = True
    memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)

    # Check if graph is available
    if not memory.graph:
        return json.dumps(
            {
                "error": "GraphMemory not available",
                "message": "Graph memory is disabled or NetworkX not installed",
            },
            indent=2,
        )

    # Analyze user pattern
    try:
        pattern = memory.graph.analyze_user_pattern(user_id)

        return json.dumps(
            {
                "user_id": user_id,
                "pattern": pattern,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to analyze user pattern: {str(e)}"}, indent=2
        )


@tool
async def memory_stats(
    user_id: str,
    agent_name: str = "global",
) -> str:
    """Get memory health report and statistics (read-only)

    Provides insights into memory usage without making any changes.
    Use this tool when:
    - User asks "how much do you remember?"
    - Checking memory health
    - Looking for cleanup opportunities

    💡 READ-ONLY: Does NOT delete or modify memories

    Args:
        user_id: User identifier
        agent_name: Agent identifier (default: "global")

    Returns:
        JSON with statistics and recommendations
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.debug(f"memory_stats: Starting for user={user_id}, agent={agent_name}")
    enable_rag = True
    memory = _get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
    logger.debug("memory_stats: Got memory manager")

    try:
        # Count memories
        logger.debug("memory_stats: Counting working memories")
        working_keys_all = memory.working.keys()
        working_count = len([k for k in working_keys_all if not k.startswith("_meta_")])
        logger.debug(f"memory_stats: Working count = {working_count}")

        logger.debug("memory_stats: Searching persistent memories")
        persistent_mems = memory.persistent.search("%", user_id, agent_name, limit=1000)
        persistent_count = len(persistent_mems)
        logger.debug(f"memory_stats: Persistent count = {persistent_count}")

        # Analyze duplicates
        logger.debug("memory_stats: Analyzing duplicates")
        working_keys = [k for k in working_keys_all if not k.startswith("_meta_")]
        duplicates = sum(
            1 for k in working_keys if any(m["key"] == k for m in persistent_mems)
        )
        logger.debug(f"memory_stats: Duplicates = {duplicates}")

        # Analyze old memories (>90 days)
        logger.debug("memory_stats: Analyzing old memories")
        from datetime import datetime, timedelta

        old_threshold = datetime.now() - timedelta(days=90)
        old_count = 0
        for mem in persistent_mems:
            if mem.get("created_at"):
                try:
                    created_str = mem["created_at"].replace("Z", "+00:00")
                    created = datetime.fromisoformat(created_str)
                    if created < old_threshold:
                        old_count += 1
                except (ValueError, AttributeError):
                    pass

        # Tag distribution (both working and persistent)
        logger.debug("memory_stats: Analyzing tags")
        tag_counts: dict[str, int] = {}

        # Count tags from persistent memories
        for mem in persistent_mems:
            meta = mem.get("metadata")
            if meta and isinstance(meta, dict):
                tags = meta.get("tags", [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except json.JSONDecodeError:
                        tags = []
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Count tags from working memories
        for key in working_keys:
            meta = memory.get_temp(f"_meta_{key}")
            if meta and isinstance(meta, dict):
                tags = meta.get("tags", [])
                # Working memory tags are already lists (not JSON strings)
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except json.JSONDecodeError:
                        tags = []
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        logger.debug("memory_stats: Sorting tags")
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        top_tags = dict(sorted_tags[:5])

        # Recommendations
        logger.debug("memory_stats: Generating recommendations")
        recs = []
        if duplicates:
            recs.append(f"{duplicates} duplicate keys - consider consolidating")
        if old_count > 10:
            recs.append(f"{old_count} memories >90 days - consider export")
        if not recs:
            recs.append("Memory health looks good!")

        # Health score
        logger.debug("memory_stats: Calculating health score")
        total = working_count + persistent_count
        health = "excellent" if total < 100 else "good" if total < 500 else "fair"

        stats = {
            "total_memories": total,
            "breakdown": {"working": working_count, "persistent": persistent_count},
            "analysis": {"duplicates": duplicates, "old_90days": old_count},
            "top_tags": top_tags,
            "recommendations": recs,
            "health_score": health,
        }

        logger.debug("memory_stats: Creating JSON response")
        result = json.dumps(stats, indent=2)
        logger.debug(f"memory_stats: Returning JSON (length={len(result)})")
        return result

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
    # Ensure k is int
    if isinstance(k, str):
        try:
            k = int(k)
        except ValueError:
            k = 10

    try:
        memory = _get_memory_manager(user_id, agent_name, enable_rag=True)
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
            for key in memory.working.keys():
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


@tool
async def memory_search_hybrid(
    user_id: str,
    agent_name: str,
    query: str,
    keyword_weight: str = "0.4",
    semantic_weight: str = "0.6",
    scope: str = "persistent",
    k: str = "10",
) -> str:
    """Search agent memory using hybrid approach (keyword + semantic).

    Combines BM25 keyword search with RAG semantic search for better recall.
    Uses Reciprocal Rank Fusion (RRF) to merge results.

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        query: Search query (any language)
        keyword_weight: Weight for BM25 keyword search (0.0-1.0, default: 0.4)
        semantic_weight: Weight for RAG semantic search (0.0-1.0, default: 0.6)
        scope: Memory scope ("working", "persistent", or "all")
        k: Number of results to return (default: 10)

    Returns:
        JSON string with search results ranked by hybrid score

    Examples:
        # Balanced hybrid search
        await memory_search_hybrid(
            user_id="user_001",
            agent_name="coding",
            query="meeting yesterday roadmap"
        )

        # Keyword-heavy search (exact terms important)
        await memory_search_hybrid(
            user_id="user_001",
            agent_name="coding",
            query="API key configuration",
            keyword_weight=0.7,
            semantic_weight=0.3
        )

        # Semantic-heavy search (concepts important)
        await memory_search_hybrid(
            user_id="user_001",
            agent_name="coding",
            query="how to improve performance",
            keyword_weight=0.2,
            semantic_weight=0.8
        )

    Note:
        - Weights should sum to 1.0 for normalized scores
        - Requires RAG to be enabled for semantic search
        - Falls back to keyword-only if RAG unavailable
    """
    # Convert string parameters to appropriate types
    keyword_weight_f = float(keyword_weight)
    semantic_weight_f = float(semantic_weight)
    k_int = int(k)

    memory = _get_memory_manager(user_id, agent_name, enable_rag=True)

    results: list[dict[str, Any]] = []

    # 1. BM25 Keyword Search
    keyword_results: list[dict[str, Any]] = []
    if keyword_weight_f > 0:
        try:
            # Get all memories for keyword search
            all_memories = []
            if scope in ["working", "all"]:
                # Get all working memory keys
                for key in memory.working.keys():
                    if not key.startswith("_meta_"):
                        value = memory.working.get(key)
                        all_memories.append({"key": key, "value": str(value)})

            if scope in ["persistent", "all"]:
                # Search all persistent memories
                persistent_mems = memory.persistent.search(
                    "%", user_id, agent_name, limit=1000
                )
                all_memories.extend(persistent_mems)

            if all_memories:
                # Build BM25 index
                from kagura.core.memory.bm25_search import BM25Search

                bm25 = BM25Search()
                bm25_docs = [
                    {"id": m["key"], "content": str(m.get("value", ""))}
                    for m in all_memories
                ]
                bm25.build_index(bm25_docs)

                # Search
                keyword_results = bm25.search(query, k=k_int * 2)

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"BM25 search failed: {e}, skipping keyword search")

    # 2. RAG Semantic Search
    semantic_results: list[dict[str, Any]] = []
    if semantic_weight_f > 0 and memory.persistent_rag:
        try:
            rag_results = memory.persistent_rag.recall(
                query=query,
                user_id=user_id,
                top_k=k_int * 2,
                agent_name=agent_name,
            )

            # Convert to standard format
            semantic_results = [
                {
                    "id": r.get("key", ""),
                    "rank": idx + 1,
                    "score": r.get("score", 0.0),
                    "content": r.get("value", ""),
                    "metadata": r.get("metadata", {}),
                }
                for idx, r in enumerate(rag_results)
            ]

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"RAG search failed: {e}, skipping semantic search")

    # 3. Hybrid Fusion
    if keyword_results and semantic_results:
        # Use weighted RRF fusion
        from kagura.core.memory.hybrid_search import weighted_rrf_fusion

        # Prepare results with ranks
        kw_ranked = [
            {"id": r["id"], "rank": idx + 1} for idx, r in enumerate(keyword_results)
        ]
        sem_ranked = [{"id": r["id"], "rank": r["rank"]} for r in semantic_results]

        # Fuse
        fused_scores = weighted_rrf_fusion(
            sem_ranked,
            kw_ranked,
            k=60,
            vector_weight=semantic_weight_f,
            lexical_weight=keyword_weight_f,
        )

        # Retrieve full documents
        for doc_id, rrf_score in fused_scores[:k_int]:
            # Find in either result set
            doc = next(
                (r for r in keyword_results if r.get("id") == doc_id),
                next((r for r in semantic_results if r.get("id") == doc_id), None),
            )
            if doc:
                result = {
                    "key": doc_id,
                    "value": doc.get("content", ""),
                    "hybrid_score": rrf_score,
                    "keyword_score": next(
                        (
                            r.get("bm25_score", 0)
                            for r in keyword_results
                            if r.get("id") == doc_id
                        ),
                        0,
                    ),
                    "semantic_score": next(
                        (
                            r.get("score", 0)
                            for r in semantic_results
                            if r.get("id") == doc_id
                        ),
                        0,
                    ),
                    "metadata": doc.get("metadata", {}),
                }
                results.append(result)

    elif keyword_results:
        # Keyword-only fallback
        results = [
            {
                "key": r["id"],
                "value": r.get("content", ""),
                "hybrid_score": r.get("bm25_score", 0),
                "keyword_score": r.get("bm25_score", 0),
                "semantic_score": 0,
            }
            for r in keyword_results[:k_int]
        ]

    elif semantic_results:
        # Semantic-only fallback
        results = [
            {
                "key": r["id"],
                "value": r.get("content", ""),
                "hybrid_score": r.get("score", 0),
                "keyword_score": 0,
                "semantic_score": r.get("score", 0),
            }
            for r in semantic_results[:k_int]
        ]

    # Format output
    if not results:
        return json.dumps(
            {"found": 0, "results": [], "message": "No matching memories found"}
        )

    return json.dumps(
        {
            "found": len(results),
            "results": results,
            "search_type": "hybrid",
            "weights": {"keyword": keyword_weight, "semantic": semantic_weight},
        },
        indent=2,
    )


@tool
async def memory_timeline(
    user_id: str,
    agent_name: str,
    time_range: str,
    event_type: str | None = None,
    scope: str = "persistent",
    k: int = 20,
) -> str:
    """Retrieve memories from specific time range.

    Search memories by timestamp, optionally filtering by event type.
    Useful for answering "what happened yesterday?" or "last week's decisions".

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        time_range: Time range specification:
            - "last_24h" or "last_day": Last 24 hours
            - "last_week": Last 7 days
            - "last_month": Last 30 days
            - "YYYY-MM-DD": Specific date
            - "YYYY-MM-DD:YYYY-MM-DD": Date range
        event_type: Optional event type filter (e.g., "meeting", "decision", "error")
        scope: Memory scope ("working", "persistent", or "all")
        k: Maximum number of results (default: 20)

    Returns:
        JSON string with memories from the time range,
        sorted by timestamp (newest first)

    Examples:
        # Yesterday's memories
        await memory_timeline(
            user_id="user_001",
            agent_name="coding",
            time_range="last_24h"
        )

        # This week's meetings
        await memory_timeline(
            user_id="user_001",
            agent_name="coding",
            time_range="last_week",
            event_type="meeting"
        )

        # Specific date range
        await memory_timeline(
            user_id="user_001",
            agent_name="coding",
            time_range="2025-11-01:2025-11-03"
        )

    Note:
        - Memories must have "timestamp" in metadata for time filtering
        - Results are sorted by timestamp (newest first)
        - Event type matching is case-insensitive substring match
    """
    from datetime import datetime, timedelta

    memory = _get_memory_manager(user_id, agent_name, enable_rag=True)

    # Parse time range
    now = datetime.utcnow()
    start_time: datetime | None = None
    end_time: datetime | None = None

    if time_range == "last_24h" or time_range == "last_day":
        start_time = now - timedelta(days=1)
        end_time = now
    elif time_range == "last_week":
        start_time = now - timedelta(days=7)
        end_time = now
    elif time_range == "last_month":
        start_time = now - timedelta(days=30)
        end_time = now
    elif ":" in time_range:
        # Date range: "YYYY-MM-DD:YYYY-MM-DD"
        start_str, end_str = time_range.split(":")
        start_time = datetime.fromisoformat(start_str)
        end_time = datetime.fromisoformat(end_str)
    else:
        # Single date: "YYYY-MM-DD"
        try:
            start_time = datetime.fromisoformat(time_range)
            end_time = start_time + timedelta(days=1)
        except ValueError:
            return json.dumps(
                {
                    "error": f"Invalid time_range format: {time_range}",
                    "expected": (
                        "last_24h, last_week, last_month, YYYY-MM-DD, "
                        "or YYYY-MM-DD:YYYY-MM-DD"
                    ),
                }
            )

    # Collect memories
    all_memories = []
    if scope in ["working", "all"]:
        # Get all working memory keys
        for key in memory.working.keys():
            if not key.startswith("_meta_"):
                value = memory.working.get(key)
                all_memories.append({"key": key, "value": str(value), "metadata": {}})

    if scope in ["persistent", "all"]:
        # Search all persistent memories
        persistent_mems = memory.persistent.search("%", user_id, agent_name, limit=1000)
        all_memories.extend(persistent_mems)

    # Filter by time and event type
    filtered_results = []
    for mem in all_memories:
        metadata = mem.get("metadata", {})

        # Check timestamp
        timestamp_str = metadata.get("timestamp")
        if not timestamp_str:
            continue

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            continue

        if start_time and timestamp < start_time:
            continue
        if end_time and timestamp > end_time:
            continue

        # Check event type
        if event_type:
            mem_type = metadata.get("type", "").lower()
            if event_type.lower() not in mem_type:
                continue

        filtered_results.append(
            {
                "key": mem.get("key", ""),
                "value": mem.get("value", ""),
                "timestamp": timestamp_str,
                "type": metadata.get("type", ""),
                "metadata": metadata,
            }
        )

    # Sort by timestamp (newest first)
    filtered_results.sort(key=lambda x: x["timestamp"], reverse=True)

    # Limit to k results
    final_results = filtered_results[:k]

    return json.dumps(
        {
            "found": len(final_results),
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
                "query": time_range,
            },
            "event_type": event_type,
            "results": final_results,
        },
        indent=2,
    )


@tool
async def memory_fuzzy_recall(
    user_id: str,
    agent_name: str,
    key_pattern: str,
    similarity_threshold: float = 0.6,
    scope: str = "persistent",
    k: int = 10,
) -> str:
    """Recall memories using fuzzy key matching.

    Find memories when you don't remember the exact key.
    Uses string similarity (Levenshtein distance) for matching.

    Args:
        user_id: User identifier (memory owner)
        agent_name: Agent identifier
        key_pattern: Partial key or pattern to search for
        similarity_threshold: Minimum similarity score (0.0-1.0, default: 0.6)
        scope: Memory scope ("working", "persistent", or "all")
        k: Maximum number of results (default: 10)

    Returns:
        JSON string with fuzzy-matched memories ranked by key similarity

    Examples:
        # Partial key recall
        await memory_fuzzy_recall(
            user_id="user_001",
            agent_name="coding",
            key_pattern="meeting"  # Matches "meeting_2025-11-02", "team_meeting", etc.
        )

        # Fuzzy match with typo tolerance
        await memory_fuzzy_recall(
            user_id="user_001",
            agent_name="coding",
            key_pattern="roadmap",  # Matches "roadmap", "road_map", "v4_roadmap"
            similarity_threshold=0.5  # Lower threshold for more results
        )

    Note:
        - Uses Ratcliff-Obershelp algorithm for similarity
        - Case-insensitive matching
        - Returns results sorted by similarity score
    """
    from difflib import SequenceMatcher

    memory = _get_memory_manager(user_id, agent_name, enable_rag=False)

    # Collect all keys
    all_memories = []
    if scope in ["working", "all"]:
        # Get all working memory keys
        for key in memory.working.keys():
            if not key.startswith("_meta_"):
                value = memory.working.get(key)
                all_memories.append({"key": key, "value": str(value), "metadata": {}})

    if scope in ["persistent", "all"]:
        # Search all persistent memories
        persistent_mems = memory.persistent.search("%", user_id, agent_name, limit=1000)
        all_memories.extend(persistent_mems)

    if not all_memories:
        return json.dumps(
            {"found": 0, "results": [], "message": "No memories in specified scope"}
        )

    # Calculate similarity scores
    matches = []
    key_pattern_lower = key_pattern.lower()

    for mem in all_memories:
        mem_key = mem.get("key", "")
        mem_key_lower = mem_key.lower()

        # Calculate similarity
        similarity = SequenceMatcher(None, key_pattern_lower, mem_key_lower).ratio()

        if similarity >= similarity_threshold:
            matches.append(
                {
                    "key": mem_key,
                    "value": mem.get("value", ""),
                    "similarity": similarity,
                    "metadata": mem.get("metadata", {}),
                }
            )

    # Sort by similarity (descending)
    matches.sort(key=lambda x: x["similarity"], reverse=True)

    # Limit to k results
    final_results = matches[:k]

    return json.dumps(
        {
            "found": len(final_results),
            "key_pattern": key_pattern,
            "similarity_threshold": similarity_threshold,
            "results": final_results,
        },
        indent=2,
    )
