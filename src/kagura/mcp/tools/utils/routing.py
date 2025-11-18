"""Built-in MCP tools for Agent Routing

Exposes intelligent routing capabilities via MCP.
"""

from __future__ import annotations

from kagura import tool


@tool
async def route_query(query: str, router_type: str = "llm") -> str:
    """Route query to appropriate agent (placeholder)

    Args:
        query: User query
        router_type: Router type (llm/keyword/semantic)

    Returns:
        Selected agent name or error
    """
    try:
        # Note: This is a placeholder - routing requires agents to be registered
        # Real implementation would need AgentRouter with registered agents
        return f"Router type '{router_type}' - requires agent registration"
    except Exception as e:
        return f"Error: {e}"
