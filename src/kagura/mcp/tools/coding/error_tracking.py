"""Error tracking MCP tools.

Records and searches coding errors with solutions and context.
"""

from __future__ import annotations

from kagura import tool
from kagura.utils.common.mcp_helpers import parse_json_list, to_int
from kagura.mcp.tools.coding.common import get_coding_memory


@tool
async def coding_record_error(
    user_id: str,
    project_id: str,
    error_type: str,
    message: str,
    stack_trace: str,
    file_path: str,
    line_number: int,
    solution: str | None = None,
    screenshot: str | None = None,
    tags: str = "[]",
) -> str:
    """Record coding errors with stack traces and optional screenshots
    for pattern learning.

    Use this tool to record errors you encounter during development. The system will:
    1. Store error details for future reference
    2. Learn patterns from recurring errors
    3. Suggest solutions based on past resolutions
    4. Analyze screenshots if provided (using Vision AI)

    When to use:
    - When encountering any error during development
    - After resolving an error (include the solution!)
    - When adding error screenshots for better context

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        error_type: Error classification
            (e.g., "TypeError", "SyntaxError", "ImportError")
        message: Full error message text
        stack_trace: Complete stack trace or key frames
        file_path: File where error occurred
        line_number: Line number where error occurred
        solution: How the error was resolved (add this after fixing!)
        screenshot: Optional screenshot path or base64-encoded image
            - Supports: file paths, base64 strings, data URIs
            - Vision AI will extract additional context automatically
        tags: JSON array of custom tags (e.g., '["database", "async"]')

    Returns:
        Confirmation with error ID and any extracted insights from screenshot

    Examples:
        # Recording an error
        await coding_record_error(
            user_id="dev_john",
            project_id="api-service",
            error_type="TypeError",
            message="can't compare offset-naive and offset-aware datetimes",
            stack_trace=(
                'Traceback:\\n  File "auth.py", line 42, '
                "in validate\\n    ..."
            ),
            file_path="src/auth.py",
            line_number=42,
            tags='["datetime", "timezone"]'
        )

        # Recording with solution after fixing
        await coding_record_error(
            user_id="dev_john",
            project_id="api-service",
            error_type="TypeError",
            message="...",
            stack_trace="...",
            file_path="src/auth.py",
            line_number=42,
            solution=("Changed datetime.now() to datetime.now(timezone.utc) "
                      "for consistency"),
            tags='["datetime", "resolved"]'
        )

        # Recording with screenshot
        await coding_record_error(
            user_id="dev_john",
            project_id="api-service",
            error_type="RuntimeError",
            message="Database connection failed",
            stack_trace="...",
            file_path="src/db.py",
            line_number=15,
            screenshot="/path/to/error_screenshot.png"
        )
    """
    memory = get_coding_memory(user_id, project_id)

    # Parse tags from JSON using common helper
    tags_list = parse_json_list(tags, param_name="tags")

    # Convert line_number to int using common helper
    line_number = to_int(line_number, default=0, min_val=0, param_name="line_number")

    error_id = await memory.record_error(
        error_type=error_type,
        message=message,
        stack_trace=stack_trace,
        file_path=file_path,
        line_number=line_number,
        solution=solution,
        screenshot=screenshot,
        tags=tags_list,
    )

    screenshot_note = ""
    if screenshot:
        screenshot_note = (
            "\n📸 Screenshot analysis: Vision AI extracted additional context"
        )

    return (
        f"✅ Error recorded: {error_id}\n"
        f"Type: {error_type}\n"
        f"Location: {file_path}:{line_number}\n"
        f"Status: {'Resolved' if solution else 'Not yet resolved'}\n"
        f"Project: {project_id}{screenshot_note}"
    )


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
