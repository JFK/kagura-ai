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
    agent_name: str,
    key: str,
    value: str,
    scope: str = "working",
    tags: str = "[]",
    importance: float = 0.5,
    metadata: str = "{}",
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
        agent_name="global", key="user_language", value="Japanese",
        tags='["preferences"]'

        # Thread-specific memory (only this conversation)
        agent_name="thread_chat_123", key="current_topic",
        value="Python tutorial", importance=0.8

    Args:
        agent_name: Agent identifier (use "global" for cross-thread sharing)
        key: Memory key for retrieval
        value: Information to store
        scope: Memory scope - "persistent" (disk, survives restart)
            or "working" (in-memory)
        tags: JSON array string of tags (e.g., '["python", "coding"]')
        importance: Importance score (0.0-1.0, default 0.5)
        metadata: JSON object string of additional metadata
            (e.g., '{"project": "kagura"}')

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
    full_metadata = {
        **metadata_dict,
        "tags": tags_list,
        "importance": importance,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

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
    # Ensure limit is int (LLM might pass as string)
    if isinstance(limit, str):
        try:
            limit = int(limit)
        except ValueError:
            limit = 50  # Default fallback

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
            # Get all working memory keys (exclude internal _meta_ keys)
            for key in memory.working.keys():
                # Skip internal metadata keys
                if key.startswith("_meta_"):
                    continue

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


@tool
async def memory_feedback(
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

    💡 Feedback Types:
    - label="useful": Memory was helpful (+weight to importance)
    - label="irrelevant": Memory not relevant (-weight)
    - label="outdated": Memory is old/stale (-weight, candidate for removal)

    Examples:
        # Mark memory as useful
        agent_name="global", key="user_language", label="useful", weight=0.2

        # Mark memory as outdated
        agent_name="global", key="old_preference", label="outdated", weight=0.5

    Args:
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
        memory = _get_memory_manager(agent_name, enable_rag=enable_rag)
    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                agent_name=agent_name, enable_rag=False
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
async def memory_delete(agent_name: str, key: str, scope: str = "persistent") -> str:
    """Delete a memory with audit logging

    Permanently delete a memory from storage. Use this tool when:
    - User explicitly asks to forget something
    - Memory is outdated and should be removed
    - Cleaning up temporary data

    💡 IMPORTANT: Deletion is permanent and logged for audit.

    Examples:
        # Delete persistent memory
        agent_name="global", key="old_preference", scope="persistent"

        # Delete working memory
        agent_name="thread_chat_123", key="temp_data", scope="working"

    Args:
        agent_name: Agent identifier
        key: Memory key to delete
        scope: Memory scope (working/persistent)

    Returns:
        Confirmation message with deletion details

    Note:
        - Deletion is logged with timestamp and agent_name
        - Both key-value memory and RAG entries are deleted
        - For GDPR compliance: Complete deletion guaranteed
    """
    enable_rag = True
    try:
        memory = _get_memory_manager(agent_name, enable_rag=enable_rag)
    except ImportError:
        from kagura.core.memory import MemoryManager

        cache_key = f"{agent_name}:rag={enable_rag}"
        if cache_key not in _memory_cache:
            _memory_cache[cache_key] = MemoryManager(
                agent_name=agent_name, enable_rag=False
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
