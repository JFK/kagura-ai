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
        - All memory is now persistent (stored to disk)
    """
    # Convert k to int
    k_int = to_int(k, default=20, min_val=1, max_val=1000, param_name="k")

    memory = get_memory_manager(user_id, agent_name, enable_rag=True)

    # Use MemoryService for timeline search (v4.4.0+)
    try:
        from kagura.services import MemoryService

        service = MemoryService(memory)
        result = service.search_by_time_range(
            time_range=time_range,
            limit=k_int,
            event_type=event_type,
        )

        return json.dumps(
            {
                "time_range": time_range,
                "event_type": event_type,
                "count": result.count,
                "memories": result.results,
                "metadata": result.metadata,
            },
            indent=2,
            default=str,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def memory_fuzzy_recall(
    user_id: str,
    agent_name: str,
    key_pattern: str,
    similarity_threshold: str | float = 0.6,
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
        - All memory is now persistent (stored to disk)
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

    # Use MemoryService for fuzzy recall (v4.4.0+)
    try:
        from kagura.services import MemoryService

        service = MemoryService(memory)
        result = service.fuzzy_recall(
            key_pattern=key_pattern,
            similarity_threshold=similarity_threshold_f,
            limit=k_int,
        )

        return json.dumps(
            {
                "found": result.count,
                "key_pattern": key_pattern,
                "similarity_threshold": similarity_threshold_f,
                "results": result.results,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})
