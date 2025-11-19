"""Session management MCP tools.

Handles coding session lifecycle: start, resume, status, and end.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from kagura import tool
from kagura.utils.common.mcp_helpers import to_bool
from kagura.mcp.tools.coding.common import get_coding_memory


@tool
async def coding_start_session(
    user_id: str,
    project_id: str,
    description: str,
    tags: str = "[]",
) -> str:
    """Start tracked coding session.

    When: Beginning feature/bugfix/refactor work.
    Auto-tracks: File changes, errors, decisions until coding_end_session().

    Args:
        user_id: Developer ID
        project_id: Project ID
        description: Session goals (what you plan to do)
        tags: JSON array '["feature", "auth"]' (optional)

    Returns: Session ID and confirmation

    💡 Groups related work, generates AI summary on end.
    ⚠️ Error if session already active - end it first!
    """
    memory = get_coding_memory(user_id, project_id)

    # Parse tags
    try:
        tags_list = json.loads(tags)
    except json.JSONDecodeError:
        tags_list = []

    # Use CodingService (v4.4.0+)
    from kagura.services import CodingService

    service = CodingService(memory)
    result = await service.start_session(description=description, tags=tags_list)

    if not result.success:
        return f"❌ Failed to start session: {result.message}"

    return (
        f"✅ Coding session started: {result.session_id}\n"
        f"Project: {project_id}\n"
        f"Description: {description}\n"
        f"Tags: {', '.join(tags_list) if tags_list else 'None'}\n\n"
        f"💡 All file changes, errors, and decisions will be tracked automatically.\n"
        f"Use coding_end_session() when done to generate AI-powered summary."
    )


@tool
async def coding_resume_session(
    user_id: str,
    project_id: str,
    session_id: str,
) -> str:
    """Resume a previously ended coding session.

    Allows you to continue work from where you left off, useful for:
    - Multi-day projects (continue tomorrow)
    - Recovery after interruption (crash, close, etc.)
    - Switching between tasks and coming back
    - Keeping related work in one session

    When you resume a session:
    - All previous activities (files, errors, decisions) are preserved
    - New tracking is appended to the session
    - Final summary includes both old and new work
    - Original start time is preserved, end time is cleared

    Args:
        user_id: User identifier
        project_id: Project identifier
        session_id: ID of the session to resume (from kagura coding sessions)

    Returns:
        Confirmation with session context

    Raises:
        RuntimeError: If another session is already active
        ValueError: If session doesn't exist or is still active

    Examples:
        # List past sessions
        # (Use kagura coding sessions --project kagura-ai)

        # Resume a specific session
        await coding_resume_session(
            user_id="kiyota",
            project_id="kagura-ai",
            session_id="session_abc123"
        )

        # Continue adding activities
        await coding_track_file_change(...)
        await coding_record_decision(...)

        # End when done (includes all activities)
        await coding_end_session(success="true")
    """
    memory = get_coding_memory(user_id, project_id)

    try:
        session_id_returned = await memory.resume_coding_session(session_id)

        # Get session details from working memory
        session_data = memory.recall(f"session:{session_id_returned}")
        if not session_data:
            return f"❌ Failed to load resumed session: {session_id}"

        from kagura.core.memory.coding_memory import CodingSession

        session = CodingSession.model_validate(session_data)

        # Calculate original duration if applicable

        result = f"✅ Session resumed: {session_id_returned}\n\n"
        result += f"**Project:** {project_id}\n"
        result += f"**Description:** {session.description}\n"
        result += f"**Original start:** {session.start_time}\n"
        result += f"**Tags:** {', '.join(session.tags)}\n\n"

        # Show existing activities (fetch from storage)
        file_changes = await memory._get_session_file_changes(session_id)
        errors = await memory._get_session_errors(session_id)
        decisions = await memory._get_session_decisions(session_id)

        result += "**Existing activities:**\n"
        result += f"  • File changes: {len(file_changes)}\n"
        result += f"  • Errors recorded: {len(errors)}\n"
        result += f"  • Decisions made: {len(decisions)}\n\n"

        result += "💡 **Continue where you left off:**\n"
        result += "  • Track new changes: coding_track_file_change()\n"
        result += "  • Record new decisions: coding_record_decision()\n"
        result += "  • Check status: coding_get_current_session_status()\n"
        result += "  • End when done: coding_end_session()\n"

        return result

    except RuntimeError as e:
        return f"❌ Cannot resume session: {e}"
    except ValueError as e:
        return f"❌ Invalid session: {e}"


@tool
async def coding_end_session(
    user_id: str,
    project_id: str,
    summary: str | None = None,
    success: str | bool | None = None,
    save_to_github: str | bool = "false",
    save_to_claude_code_history: str | bool = "true",
) -> str:
    """End session and generate AI summary.

    When: Finishing work session.
    Generates: AI summary of changes, decisions, learnings.

    Args:
        user_id: Developer ID
        project_id: Project ID
        summary: Custom summary (default: AI generates)
        success: "true"|"false" (optional)
        save_to_github: "true"|"false" (default: "false", needs gh CLI + linked issue)
        save_to_claude_code_history: "true"|"false" (default: "true")

    Returns: Summary and statistics

    ⚠️ Cannot be undone! Confirm with user first.
    💡 Auto-saves to Claude Code history for cross-session knowledge.
    """
    memory = get_coding_memory(user_id, project_id)

    # Convert parameters using common helpers
    # Note: success can be None, so handle separately
    if success is None:
        success_bool = None
    else:
        success_bool = to_bool(success, default=False)

    save_to_github_bool = to_bool(save_to_github, default=False)
    save_to_claude_code_history_bool = to_bool(
        save_to_claude_code_history, default=True
    )

    result = await memory.end_coding_session(
        summary=summary,
        success=success_bool,
        save_to_github=save_to_github_bool,
    )

    success_emoji = "✅" if success_bool else ("⚠️" if success_bool is False else "ℹ️")
    duration_str = (
        f"{result['duration_minutes']:.1f} minutes"
        if result["duration_minutes"]
        else "Unknown"
    )

    github_status = ""
    if save_to_github_bool:
        if memory.github_recorder and memory.github_recorder.is_available():
            github_status = (
                f"\n✅ Session summary recorded to GitHub Issue "
                f"#{memory.github_recorder.current_issue_number}"
            )
        else:
            github_status = (
                "\n⚠️ GitHub recording requested but not available "
                "(gh CLI not installed or no issue linked)"
            )

    # Save to Claude Code history if requested
    claude_code_status = ""
    if save_to_claude_code_history_bool:
        try:
            # Prepare session data for Claude Code history
            # Use result data since session just ended
            session_title = result.get("description", "Coding Session")
            files_modified = [str(f) for f in result["files_touched"]]

            # Extract tags from result
            tags = result.get("tags", [])

            # Save using claude_code_save_session logic
            from datetime import datetime

            session_key = (
                f"claude_code_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            session_doc = f"""
Claude Code Session: {session_title}
Project: {project_id}
Date: {datetime.now().isoformat()}
Duration: {duration_str}
Files Modified: {", ".join(files_modified)}
Success: {success_bool}

Summary:
{result["summary"]}

Statistics:
- Files touched: {len(result["files_touched"])}
- Errors encountered: {result["errors_encountered"]}
- Errors fixed: {result["errors_fixed"]}
- Decisions made: {result["decisions_made"]}
"""

            metadata = {
                "type": "claude_code_session",
                "project_id": project_id,
                "session_title": session_title,
                "files_modified": files_modified,
                "tags": tags,
                "timestamp": datetime.now().isoformat(),
                "importance": 0.8 if success_bool else 0.6,
                "platform": "claude_code",
                "session_id": result["session_id"],
            }

            # Store in persistent memory
            mem_key = f"claude_code_{session_key}"
            memory.persistent.store(
                key=mem_key,
                value=session_doc,
                user_id=user_id,
                metadata=metadata,
            )

            # Store in RAG for semantic search
            if memory.rag:
                memory.rag.store(
                    content=session_doc,
                    metadata=metadata,
                    user_id=user_id,
                )

            claude_code_status = (
                f"\n✅ Session saved to Claude Code history: {session_key}"
            )

        except Exception as e:
            claude_code_status = f"\n⚠️ Failed to save to Claude Code history: {e}"

    return (
        f"{success_emoji} Coding session ended: {result['session_id']}\n"
        f"Duration: {duration_str}\n"
        f"Files touched: {len(result['files_touched'])}\n"
        f"Errors: {result['errors_encountered']} encountered, "
        f"{result['errors_fixed']} fixed\n"
        f"Decisions: {result['decisions_made']}\n\n"
        f"📝 Summary:\n{result['summary']}\n\n"
        f"💾 Session data saved for future reference and pattern learning."
        f"{github_status}"
        f"{claude_code_status}"
    )


# ==============================================================================
# Issue #720: Renamed session status tool
# ==============================================================================


@tool
async def coding_get_status(
    user_id: str,
    project_id: str,
) -> str:
    """Get current coding session status (renamed from coding_get_current_session_status).

    Returns active session info including tracked changes, errors, and decisions.

    Args:
        user_id: Developer ID
        project_id: Project identifier

    Returns:
        JSON with session details, tracked activities, and statistics

    Example:
        status = coding_get_status(user_id="kiyota", project_id="kagura-ai")
        # Returns: {"session_id": "...", "duration": "45m", "changes": 5, ...}

    💡 TIP: Use to check session progress and tracked activities.
    🌐 Cross-platform: Works across all AI assistants.
    """
    try:
        coding_memory = get_coding_memory(user_id, project_id)
        status = coding_memory.get_current_session_status()

        if not status:
            return json.dumps(
                {
                    "active": False,
                    "message": "No active session",
                },
                indent=2,
            )

        return json.dumps(status, indent=2, default=str, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})
