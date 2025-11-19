"""Project context MCP tool.

Retrieves comprehensive project context and overview.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.mcp.tools.coding.common import get_coding_memory



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
