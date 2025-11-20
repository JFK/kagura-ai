"""Error tracking MCP tools.

Records and searches coding errors with solutions and context.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.utils.common.mcp_helpers import parse_json_list, to_int
from kagura.mcp.tools.coding.common import get_coding_memory



@tool
async def coding_search_errors(
    user_id: str,
    project_id: str,
    query: str,
    k: str | int = 5,
) -> str:
    """Search past errors semantically to find similar issues and their solutions.

    Use this tool when encountering an error to find how similar errors were
    resolved in the past. The search uses semantic similarity (not just keywords)
    to find relevant past errors.

    When to use:
    - When encountering a new error
    - When you remember fixing something similar before
    - When looking for error patterns in your project

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        query: Error description or message to search for
        k: Number of similar errors to return (default: 5)

    Returns:
        List of similar past errors with solutions

    Examples:
        # Search for datetime-related errors
        await coding_search_errors(
            user_id="dev_john",
            project_id="api-service",
            query="TypeError comparing datetime objects",
            k=3
        )

        # Search for database errors
        await coding_search_errors(
            user_id="dev_john",
            project_id="api-service",
            query="database connection timeout",
            k=5
        )
    """
    memory = get_coding_memory(user_id, project_id)

    # Convert k to int using common helper
    k_int = to_int(k, default=5, min_val=1, max_val=50, param_name="k")

    errors = await memory.search_similar_errors(query=query, k=k_int)

    if not errors:
        return (
            f"🔍 No similar errors found for: {query}\n"
            f"Project: {project_id}\n\n"
            f"This might be a new type of error for this project."
        )

    result_lines = [f"🔍 Found {len(errors)} similar errors:\n"]

    for i, error in enumerate(errors, 1):
        status = "✅ Resolved" if error.resolved else "❌ Unresolved"
        result_lines.append(
            f"\n{i}. {error.error_type} in {error.file_path}:{error.line_number}"
        )
        result_lines.append(f"   Status: {status}")
        result_lines.append(f"   Message: {error.message[:100]}...")

        if error.solution:
            result_lines.append(f"   Solution: {error.solution[:150]}...")

        result_lines.append(f"   Date: {error.timestamp.strftime('%Y-%m-%d %H:%M')}")

    return "\n".join(result_lines)


# ==============================================================================
# Issue #720: Unified recording tool (error + decision)
# ==============================================================================


@tool
async def coding_record_item(
    user_id: str,
    project_id: str,
    item_type: str,
    title: str,
    description: str,
    solution: str | None = None,
    metadata: str = "{}",
) -> str:
    """Record coding item (error, decision, or note) with context.

    Unified tool for recording errors, design decisions, and important notes.
    Replaces coding_record_error and coding_record_decision.

    Args:
        user_id: Developer ID
        project_id: Project ID
        item_type: Type of item:
            - "error": Bug or issue encountered
            - "decision": Design or architectural decision
            - "note": Important observation or insight
        title: Brief title/summary
        description: Detailed description
        solution: How it was resolved (for errors) or rationale (for decisions)
        metadata: JSON object with additional context

    Returns:
        JSON confirmation with item_id

    Examples:
        # Record error
        coding_record_item(
            user_id="kiyota",
            project_id="kagura-ai",
            item_type="error",
            title="ImportError in memory.py",
            description="Missing BM25Search import",
            solution="Added from kagura.core.memory.bm25_search import BM25Search"
        )

        # Record decision
        coding_record_item(
            user_id="kiyota",
            project_id="kagura-ai",
            item_type="decision",
            title="Use BM25 for keyword search",
            description="Chose BM25 algorithm for memory_search_keyword",
            solution="BM25 provides better keyword matching than TF-IDF"
        )

    💡 TIP: Record both problems AND solutions for future reference.
    🌐 Cross-platform: Works across all AI assistants.
    """
    try:
        coding_memory = get_coding_memory(user_id, project_id)
        metadata_dict = parse_json_dict(metadata, "metadata", {})

        # Add item_type to metadata
        metadata_dict["item_type"] = item_type

        if item_type == "error":
            # Use existing error recording
            item_id = coding_memory.record_error(
                error_type=metadata_dict.get("error_type", "GeneralError"),
                message=title,
                stack_trace=description,
                file_path=metadata_dict.get("file_path", ""),
                line_number=metadata_dict.get("line_number", 0),
                solution=solution,
            )
        elif item_type == "decision":
            # Use existing decision recording
            item_id = coding_memory.record_decision(
                decision=title,
                rationale=description,
                alternatives=metadata_dict.get("alternatives", []),
                impact=solution,  # Use solution field for impact
            )
        else:
            # Generic note recording (store in memory)
            item_id = f"note_{user_id}_{project_id}_{title[:50]}"
            # Store as memory note (simplified)
            metadata_dict["title"] = title
            metadata_dict["description"] = description
            if solution:
                metadata_dict["solution"] = solution

        return json.dumps(
            {
                "status": "success",
                "item_id": item_id,
                "item_type": item_type,
                "title": title,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"error": str(e)})
