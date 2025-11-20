"""Memory timeline and fuzzy recall operations.

Time-based and fuzzy search for memories.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.utils.common.mcp_helpers import to_float_clamped, to_int
from kagura.mcp.tools.memory.common import get_memory_manager



@tool
async def memory_search_timeline(
    user_id: str,
    agent_name: str,
    time_range: str,
    event_type: str | None = None,
    k: int = 20,
) -> str:
    """Search memories by time range (renamed from memory_timeline).

    Filters memories by timestamp, useful for temporal queries like
    "what happened yesterday?" or "last week's decisions".

    Args:
        user_id: Memory owner ID
        agent_name: "global" or "thread_{id}"
        time_range: Time specification:
            - "last_24h", "last_day": Last 24 hours
            - "last_week": Last 7 days
            - "last_month": Last 30 days
            - "YYYY-MM-DD": Specific date
            - "YYYY-MM-DD:YYYY-MM-DD": Date range
        event_type: Optional filter (e.g., "meeting", "decision", "error")
        k: Max results (default: 20, max: 1000)

    Returns:
        JSON with memories from time range, sorted by timestamp (newest first)

    Examples:
        # Yesterday's memories
        memory_search_timeline(user_id="user", agent_name="global", time_range="last_24h")

        # This week's meetings
        memory_search_timeline(..., time_range="last_week", event_type="meeting")

    💡 TIP: Use for "what happened when" queries.
    🌐 Cross-platform: Works across all AI assistants.
    """
    # Validate time_range is a string
    if not isinstance(time_range, str):
        return json.dumps(
            {
                "error": f"time_range must be a string, got {type(time_range).__name__}",
                "valid_formats": [
                    "last_24h",
                    "last_day",
                    "last_week",
                    "last_month",
                    "YYYY-MM-DD",
                    "YYYY-MM-DD:YYYY-MM-DD",
                ],
            }
        )

    k = to_int(k, default=20, min_val=1, max_val=1000, param_name="k")

    memory = get_memory_manager(user_id, agent_name, enable_rag=True)

    try:
        from kagura.services import MemoryService

        service = MemoryService(memory)
        result = service.search_by_time_range(
            time_range=time_range,
            limit=k,
            event_type=event_type,
        )

        return json.dumps(
            {
                "time_range": time_range,
                "event_type": event_type,
                "count": result.count,
                "memories": result.results,
            },
            indent=2,
            ensure_ascii=False,
        )
    except ValueError as e:
        # Invalid time_range format
        return json.dumps(
            {
                "error": str(e),
                "time_range": time_range,
                "valid_formats": [
                    "last_24h",
                    "last_day",
                    "last_week",
                    "last_month",
                    "YYYY-MM-DD",
                    "YYYY-MM-DD:YYYY-MM-DD",
                ],
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e), "time_range": time_range})
