"""Built-in MCP tools for Observability

Exposes telemetry and cost tracking via MCP.
"""

from __future__ import annotations

import json

from kagura import tool


@tool
def telemetry_stats(agent_name: str | None = None) -> str:
    """Get telemetry statistics

    Args:
        agent_name: Filter by agent name (optional)

    Returns:
        JSON string of statistics
    """
    try:
        from kagura.observability import EventStore

        store = EventStore()
        stats = store.get_summary_stats(agent_name=agent_name)

        return json.dumps(stats, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def telemetry_cost(agent_name: str | None = None, limit: int = 100) -> str:
    """Get cost summary

    Args:
        agent_name: Filter by agent name (optional)
        limit: Number of executions to analyze

    Returns:
        JSON string of cost breakdown
    """
    try:
        from kagura.observability import EventStore

        store = EventStore()
        executions = store.get_executions(agent_name=agent_name, limit=limit)

        # Calculate costs
        total_cost = sum(
            e.get("metrics", {}).get("total_cost", 0.0) for e in executions
        )

        return json.dumps(
            {"total_cost": total_cost, "executions": len(executions)}, indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)})
