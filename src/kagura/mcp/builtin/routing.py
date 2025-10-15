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
        from kagura.routing import LLMRouter  # noqa: F401

        # Note: Requires agents to be registered
        # This is a simplified version for MCP
        return f"Router initialized: {router_type}"
    except ImportError:
        return (
            "Error: Routing requires 'ai' extra. "
            "Install with: pip install kagura-ai[ai]"
        )
