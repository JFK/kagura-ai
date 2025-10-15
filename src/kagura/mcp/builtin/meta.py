"""Built-in MCP tools for Meta Agent

Exposes agent generation capabilities via MCP.
"""

from __future__ import annotations

from kagura import tool


@tool
async def meta_create_agent(description: str) -> str:
    """Create agent from natural language description

    Args:
        description: Agent description

    Returns:
        Generated agent code or error message
    """
    try:
        from kagura.meta import MetaAgent

        meta = MetaAgent()
        spec = await meta.create_spec(description)
        code = meta.generate_code(spec)

        return code
    except Exception as e:
        return f"Error creating agent: {e}"
