"""File change tracking MCP tool.

Tracks file modifications during coding sessions with reasons and context.
"""

from __future__ import annotations

from typing import Literal

from kagura import tool
from kagura.utils.common.mcp_helpers import parse_json_list
from kagura.mcp.tools.coding.common import get_coding_memory


@tool
async def coding_track_file_change(
    user_id: str,
    project_id: str,
    file_path: str,
    action: Literal["create", "edit", "delete", "rename", "refactor", "test"],
    diff: str,
    reason: str,
    related_files: str = "[]",
    line_range: str | None = None,
) -> str:
    """Track file changes with WHY they were made.

    When: After editing files during coding session.
    Records: file_path, action (create/edit/delete/refactor), diff, reason.

    Args:
        user_id: Developer ID
        project_id: Project ID
        file_path: Modified file path
        action: create|edit|delete|rename|refactor|test
        diff: Change summary (concise)
        reason: WHY changed (critical for context)
        related_files: JSON array '["file1.py"]' (optional)
        line_range: "start,end" (optional)

    Returns: Confirmation with change ID
    """
    memory = get_coding_memory(user_id, project_id)

    # Parse related_files from JSON using common helper
    related_files_list = parse_json_list(related_files, param_name="related_files")

    # Parse line_range if provided
    line_range_tuple = None
    if line_range:
        try:
            parts = line_range.split(",")
            if len(parts) == 2:
                line_range_tuple = (int(parts[0]), int(parts[1]))
        except ValueError:
            pass  # Ignore invalid line range

    change_id = await memory.track_file_change(
        file_path=file_path,
        action=action,
        diff=diff,
        reason=reason,
        related_files=related_files_list,
        line_range=line_range_tuple,
    )

    return (
        f"✅ File change tracked: {change_id}\n"
        f"File: {file_path}\n"
        f"Action: {action}\n"
        f"Project: {project_id}\n"
        f"Reason: {reason[:100]}..."
    )


# ==============================================================================
# Issue #720: Renamed file tracking tool
# ==============================================================================


@tool
async def coding_track_change(
    user_id: str,
    project_id: str,
    file_path: str,
    action: str,
    diff: str,
    reason: str,
    line_range: str | None = None,
    related_files: str = "[]",
) -> str:
    """Track file changes with WHY they were made (renamed from coding_track_file_change).

    Records all code modifications with rationale for context preservation.

    Args:
        user_id: Developer ID
        project_id: Project ID
        file_path: Modified file path
        action: Change type (create|edit|delete|rename|refactor|test)
        diff: Change summary (concise description)
        reason: WHY changed (critical for context)
        line_range: Optional "start,end" line numbers
        related_files: JSON array of related files (e.g., '["file1.py"]')

    Returns:
        JSON confirmation with change_id

    Example:
        coding_track_change(
            user_id="kiyota",
            project_id="kagura-ai",
            file_path="src/memory.py",
            action="edit",
            diff="Added BM25 keyword search",
            reason="Implement Issue #720 search tools"
        )

    💡 TIP: Always include the "why" for better context retrieval.
    🌐 Cross-platform: Works across all AI assistants.
    """
    try:
        coding_memory = get_coding_memory(user_id, project_id)

        change_id = coding_memory.track_file_change(
            file_path=file_path,
            action=action,
            diff=diff,
            reason=reason,
            line_range=line_range,
            related_files=parse_json_list(related_files, "related_files", []),
        )

        return json.dumps(
            {
                "status": "success",
                "change_id": change_id,
                "file_path": file_path,
                "action": action,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"error": str(e)})
