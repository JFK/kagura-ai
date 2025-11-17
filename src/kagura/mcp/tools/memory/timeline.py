"""Memory timeline and fuzzy recall operations.

Time-based and fuzzy search for memories.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from kagura import tool
from kagura.mcp.builtin.common import to_float_clamped, to_int
from kagura.mcp.tools.memory.common import get_memory_manager


@tool
async def memory_timeline(
    user_id: str,
    agent_name: str,
    time_range: str,
    event_type: str | None = None,
    scope: str = "persistent",
    k: str | int = 20,
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
    # Convert k to int using common helper
    k_int = to_int(k, default=20, min_val=1, max_val=1000, param_name="k")

    memory = get_memory_manager(user_id, agent_name, enable_rag=True)

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
        metadata = mem.get("metadata") or {}

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

    # Limit to k_int results
    final_results = filtered_results[:k_int]

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
    similarity_threshold: str | float = 0.6,
    scope: str = "persistent",
    k: str | int = 10,
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
    # Convert parameters using common helpers
    similarity_threshold_f = to_float_clamped(
        similarity_threshold,
        min_val=0.0,
        max_val=1.0,
        default=0.6,
        param_name="similarity_threshold",
    )
    k_int = to_int(k, default=10, min_val=1, max_val=1000, param_name="k")

    memory = get_memory_manager(user_id, agent_name, enable_rag=False)

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

        if similarity >= similarity_threshold_f:
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

    # Limit to k_int results
    final_results = matches[:k_int]

    return json.dumps(
        {
            "found": len(final_results),
            "key_pattern": key_pattern,
            "similarity_threshold": similarity_threshold_f,
            "results": final_results,
        },
        indent=2,
    )
