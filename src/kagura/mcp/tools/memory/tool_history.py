"""MCP tool usage history tracking.

Retrieves auto-logged tool calls for context awareness and debugging.
"""

from __future__ import annotations

import json
import logging

from kagura import tool
from kagura.mcp.builtin.common import format_error, to_int
from kagura.mcp.tools.memory.common import get_memory_manager


@tool
async def memory_get_tool_history(
    user_id: str,
    agent_name: str = "mcp_history",
    tool_filter: str | None = None,
    limit: str = "10",
) -> str:
    """Get MCP tool usage history.

    Retrieves auto-logged tool calls for context awareness and debugging.

    🔍 USE WHEN:
    - User asks "What did I search for earlier?"
    - Debugging: "What tools did I call?"
    - Context awareness: AI sees recent tool usage

    Args:
        user_id: User identifier
        agent_name: Agent identifier (default: "mcp_history")
        tool_filter: Filter by specific tool name (e.g., "brave_web_search")
        limit: Number of recent calls (default: "10", max: 100)

    Returns:
        JSON list of recent tool calls

    💡 EXAMPLE:
        memory_get_tool_history(user_id="kiyota", tool_name="brave_web_search")

    📊 RETURNS:
        [{"tool": "brave_web_search", "timestamp": "...", "args": {...}, "result_preview": "..."}]
    """
    limit_int = to_int(limit, default=10, min_val=1, max_val=100, param_name="limit")
    memory = get_memory_manager(user_id, agent_name, enable_rag=False)

    try:
        search_query = f"{tool_filter}_" if tool_filter else "%"
        results = memory.persistent.search(
            query=search_query, user_id=user_id, agent_name=agent_name, limit=limit_int
        )

        history = []
        for mem in results:
            try:
                value_str = mem.get("value", "{}")
                data = (
                    json.loads(value_str) if isinstance(value_str, str) else value_str
                )

                if tool_filter and data.get("tool") != tool_filter:
                    continue

                history.append(
                    {
                        "tool": data.get("tool"),
                        "timestamp": data.get("timestamp"),
                        "args": data.get("args"),
                        "result_preview": data.get("result", "")[:100],
                    }
                )
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logging.getLogger(__name__).warning(
                    f"Failed to parse tool history: {e}"
                )
                continue

        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return json.dumps(history[:limit_int], indent=2, ensure_ascii=False)

    except Exception as e:
        return format_error(
            "Failed to retrieve tool history", details={"error": str(e)}
        )
