"""Project context MCP tool.

Retrieves comprehensive project context and overview.
"""

from __future__ import annotations

from kagura import tool
from kagura.mcp.tools.coding.common import get_coding_memory


@tool
async def coding_get_project_context(
    user_id: str,
    project_id: str,
    focus: str | None = None,
) -> str:
    """Get comprehensive project context including recent changes,
    patterns, and key decisions.

    Use this tool to get an AI-generated overview of the project state. Useful:
    - At the start of a session to refresh context
    - When returning to a project after time away
    - When you need to explain project decisions
    - When focusing on a specific area

    The context includes:
    - High-level project summary
    - Technology stack
    - Recent changes and activity
    - Key design decisions
    - Identified coding patterns
    - Active issues or blockers

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        focus: Optional focus area (e.g., "authentication", "database", "testing")
            - If provided, context will emphasize this area

    Returns:
        Comprehensive project context summary

    Examples:
        # Get general project context
        await coding_get_project_context(
            user_id="dev_john",
            project_id="api-service"
        )

        # Get focused context on authentication
        await coding_get_project_context(
            user_id="dev_john",
            project_id="api-service",
            focus="authentication"
        )
    """
    memory = get_coding_memory(user_id, project_id)

    context = await memory.get_project_context(focus=focus)

    focus_note = f" (Focus: {focus})" if focus else ""

    result = f"📊 Project Context: {project_id}{focus_note}\n\n"
    result += f"**Summary:**\n{context.summary}\n\n"

    if context.tech_stack:
        result += "**Tech Stack:**\n"
        result += "\n".join(f"- {tech}" for tech in context.tech_stack)
        result += "\n\n"

    if context.architecture_style:
        result += f"**Architecture:** {context.architecture_style}\n\n"

    result += f"**Recent Changes:**\n{context.recent_changes}\n\n"

    if context.key_decisions:
        result += "**Key Decisions:**\n"
        for decision in context.key_decisions[:5]:
            result += f"- {decision}\n"
        result += "\n"

    if context.active_issues:
        result += "**Active Issues:**\n"
        for issue in context.active_issues:
            result += f"- ⚠️ {issue}\n"
        result += "\n"

    if context.coding_patterns:
        result += "**Observed Patterns:**\n"
        for pattern in context.coding_patterns[:3]:
            result += f"- {pattern}\n"

    if context.token_count:
        result += f"\n📏 Context size: ~{context.token_count} tokens"

    return result


# ==============================================================================
# Issue #720: Renamed project context search tool
# ==============================================================================


@tool
async def coding_search_context(
    user_id: str,
    project_id: str,
    query: str,
    focus: str | None = None,
) -> str:
    """Search project coding context (renamed from coding_get_project_context).

    Retrieves comprehensive project context including recent changes,
    decisions, errors, and patterns relevant to the query.

    Args:
        user_id: Developer ID
        project_id: Project ID
        query: Search query (e.g., "authentication", "database", "testing")
        focus: Optional focus area to narrow search

    Returns:
        JSON with relevant context from:
        - Recent file changes
        - Design decisions
        - Error resolutions
        - Code patterns

    Example:
        context = coding_search_context(
            user_id="kiyota",
            project_id="kagura-ai",
            query="memory search implementation"
        )

    💡 TIP: Use to understand project state before making changes.
    🌐 Cross-platform: Works across all AI assistants.
    """
    try:
        coding_memory = get_coding_memory(user_id, project_id)
        context = coding_memory.get_project_context(focus=focus)

        # Filter context by query if provided
        if query:
            # Simple keyword filtering (can be enhanced with semantic search)
            query_lower = query.lower()
            filtered_context = {}

            for key, items in context.items():
                if isinstance(items, list):
                    filtered_items = [
                        item
                        for item in items
                        if query_lower
                        in json.dumps(item, default=str).lower()
                    ]
                    if filtered_items:
                        filtered_context[key] = filtered_items
                elif isinstance(items, dict):
                    if query_lower in json.dumps(items, default=str).lower():
                        filtered_context[key] = items

            context = filtered_context if filtered_context else context

        return json.dumps(
            {
                "project_id": project_id,
                "query": query,
                "focus": focus,
                "context": context,
            },
            indent=2,
            default=str,
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps({"error": str(e), "query": query})
