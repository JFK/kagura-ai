"""Built-in MCP tools for Coding Memory operations.

Exposes coding-specialized memory features via MCP for AI coding assistants
like Claude Code, Cursor, and others.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from kagura import tool

if TYPE_CHECKING:
    from kagura.core.memory.coding_memory import CodingMemoryManager


def _get_coding_memory(user_id: str, project_id: str) -> CodingMemoryManager:
    """Get CodingMemoryManager instance (no caching for session synchronization).

    Note: Cache removed in v4.0.9 to fix session synchronization issues.
    Each call creates a fresh instance that loads current session state
    from persistent storage.

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier

    Returns:
        New CodingMemoryManager instance with current session state
    """
    import logging

    logger = logging.getLogger(__name__)

    from kagura.core.memory.coding_memory import CodingMemoryManager

    logger.debug(
        f"_get_coding_memory: Creating CodingMemoryManager for {user_id}:{project_id}"
    )

    # Always create new instance to ensure fresh session state
    return CodingMemoryManager(
        user_id=user_id,
        project_id=project_id,
        enable_rag=True,  # Always enable for semantic search
        enable_graph=True,  # Always enable for relationships
    )


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
    memory = _get_coding_memory(user_id, project_id)

    # Parse related_files from JSON (using helper)
    related_files_list = _parse_json_list(related_files, "related_files")

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
    memory = _get_coding_memory(user_id, project_id)

    # Parse tags from JSON (using helper)
    tags_list = _parse_json_list(tags, "tags")

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
async def coding_record_decision(
    user_id: str,
    project_id: str,
    decision: str,
    rationale: str,
    alternatives: str = "[]",
    impact: str | None = None,
    tags: str = "[]",
    related_files: str = "[]",
    confidence: float = 0.8,
) -> str:
    """Record design and architectural decisions with rationale
    for project context tracking.

    Use this tool to document important technical decisions. This helps:
    1. Future you remember WHY certain choices were made
    2. Other developers understand the reasoning
    3. AI assistants provide context-aware suggestions

    When to use:
    - When choosing between technical approaches
    - When making architectural decisions
    - When selecting libraries/frameworks
    - When establishing coding patterns/standards

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        decision: Brief statement of the decision made (1-2 sentences)
        rationale: Detailed reasoning behind the decision
        alternatives: JSON array of other options considered
            (e.g., '["Option A", "Option B"]')
        impact: Expected impact on the project (optional)
        tags: JSON array of categorization tags (e.g., '["architecture", "security"]')
        related_files: JSON array of files affected by this decision
        confidence: Confidence level in this decision (0.0-1.0, default 0.8)

    Returns:
        Confirmation with decision ID

    Examples:
            rationale=(
                "Stateless auth enables horizontal scaling without "
                "session store. JWTs can be validated without database "
                "lookups, improving performance. Better for planned "
                "mobile app integration."
            ),
            user_id="dev_john",
            project_id="api-service",
            decision="Use JWT tokens for authentication instead of sessions",
            rationale=(
                "Stateless auth enables horizontal scaling without session store. "
                "JWTs can be validated without database lookups, "
                "improving performance. "
                "Better for planned mobile app integration."
            ),
            alternatives='["Session-based auth", "OAuth-only"]',
            impact=(
                "Eliminates need for session storage. "
                "Requires key rotation strategy."
            ),
            tags='["architecture", "authentication", "security"]',
            related_files='["src/auth.py", "src/middleware.py"]',
            confidence=0.9
        )

        # Recording a library choice
        await coding_record_decision(
            user_id="dev_john",
            project_id="api-service",
            decision="Use Pydantic for data validation",
            rationale="Type-safe validation with excellent FastAPI integration. "
                     "Clear error messages and automatic API docs generation.",
            alternatives='["Marshmallow", "Cerberus", "manual validation"]',
            impact="All API models will use Pydantic BaseModel",
            tags='["library", "validation"]',
            confidence=0.95
        )
    """
    memory = _get_coding_memory(user_id, project_id)

    # Parse JSON arrays
    try:
        alternatives_list = json.loads(alternatives)
    except json.JSONDecodeError:
        alternatives_list = []

    try:
        tags_list = json.loads(tags)
    except json.JSONDecodeError:
        tags_list = []

    try:
        related_files_list = json.loads(related_files)
    except json.JSONDecodeError:
        related_files_list = []

    decision_id = await memory.record_decision(
        decision=decision,
        rationale=rationale,
        alternatives=alternatives_list,
        impact=impact,
        tags=tags_list,
        related_files=related_files_list,
        confidence=confidence,
    )

    # Ensure confidence is float for formatting
    confidence_float = float(confidence) if isinstance(confidence, str) else confidence

    return (
        f"✅ Decision recorded: {decision_id}\n"
        f"Decision: {decision}\n"
        f"Confidence: {confidence_float:.0%}\n"
        f"Project: {project_id}\n"
        f"Tags: {', '.join(tags_list) if tags_list else 'None'}"
    )


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
    memory = _get_coding_memory(user_id, project_id)

    # Parse tags
    try:
        tags_list = json.loads(tags)
    except json.JSONDecodeError:
        tags_list = []

    session_id = await memory.start_coding_session(
        description=description,
        tags=tags_list,
    )

    return (
        f"✅ Coding session started: {session_id}\n"
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
    memory = _get_coding_memory(user_id, project_id)

    try:
        session_id_returned = await memory.resume_coding_session(session_id)

        # Get session details from working memory
        session_data = memory.working.get(f"session:{session_id_returned}")
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
async def coding_get_current_session_status(
    user_id: str,
    project_id: str,
) -> str:
    """Get current coding session status and tracked activities.

    Use this tool to check what has been recorded in the current session
    before ending it. Helps you:
    - See what will be included in the session summary
    - Verify important items are tracked
    - Decide if ready to end session

    Returns current session information including:
    - Session metadata (ID, description, duration, tags)
    - Tracked activities count (files, errors, decisions, interactions)
    - Recent activity summary
    - Next steps recommendation

    Args:
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Current session status summary

    Raises:
        Error if no active session

    Examples:
        # Check status before ending
        status = await coding_get_current_session_status(
            user_id="kiyota",
            project_id="kagura-ai"
        )
        # Review the output, then decide:
        # await coding_end_session(...)
    """
    memory = _get_coding_memory(user_id, project_id)

    if not memory.current_session_id:
        return "❌ No active coding session.\n\nStart one with: coding_start_session()"

    # Load current session from working memory
    session_data = memory.working.get(f"session:{memory.current_session_id}")
    if not session_data:
        return "❌ Session data not found in working memory."

    from kagura.core.memory.coding_memory import CodingSession

    session = CodingSession.model_validate(session_data)

    # Calculate duration
    from datetime import datetime, timezone

    # Handle both datetime and string formats
    if isinstance(session.start_time, str):
        start = datetime.fromisoformat(session.start_time)
    else:
        start = session.start_time

    # Ensure timezone-aware comparison
    now = datetime.now(timezone.utc)
    if start.tzinfo is None:
        # Assume UTC if naive
        start = start.replace(tzinfo=timezone.utc)

    duration = (now - start).total_seconds() / 60

    # Count activities (CodingSession doesn't store these, need to fetch from memory)
    # For now, fetch from persistent storage
    file_changes_records = await memory._get_session_file_changes(session.session_id)
    errors_records = await memory._get_session_errors(session.session_id)
    decisions_records = await memory._get_session_decisions(session.session_id)

    file_changes = len(file_changes_records)
    errors = len([e for e in errors_records if not e.solution])
    errors_fixed = len([e for e in errors_records if e.solution])
    decisions = len(decisions_records)
    interactions = 0  # Not yet tracked separately

    # Build status report
    result = "📊 Current Session Status\n\n"
    result += f"**Session ID:** {session.session_id}\n"
    result += f"**Project:** {project_id}\n"
    result += f"**Description:** {session.description}\n"
    result += f"**Duration:** {duration:.1f} minutes (started {session.start_time})\n"
    result += f"**Tags:** {', '.join(session.tags)}\n\n"

    result += "**Tracked Activities:**\n"
    result += f"  • File changes: {file_changes}\n"
    result += f"  • Errors encountered: {errors + errors_fixed}\n"
    result += f"  • Errors fixed: {errors_fixed}\n"
    result += f"  • Decisions recorded: {decisions}\n"
    result += f"  • Interactions tracked: {interactions}\n\n"

    # Recent activity
    if file_changes_records:
        result += "**Recent File Changes (last 3):**\n"
        for change in file_changes_records[-3:]:
            result += f"  • {change.action}: {change.file_path}\n"
        result += "\n"

    if decisions_records:
        result += "**Recent Decisions (last 2):**\n"
        for decision in decisions_records[-2:]:
            result += f"  • {decision.decision[:80]}...\n"
        result += "\n"

    # Recommendations
    result += "**Next Steps:**\n"

    if file_changes == 0:
        result += "  ⚠️  No file changes tracked yet. Use coding_track_file_change()\n"

    if errors > 0:
        result += f"  ⚠️  {errors} unresolved errors. Add solutions before ending.\n"

    result += "  ✅ Ready to end? Confirm with user, then: coding_end_session()\n"

    if file_changes > 0 or decisions > 0:
        result += "  💡 Consider: save_to_github='true' to record to GitHub Issue\n"

    return result


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
    memory = _get_coding_memory(user_id, project_id)

    # Convert parameters to appropriate types (handle both str and bool)
    if success is None:
        success_bool = None
    elif isinstance(success, bool):
        success_bool = success
    else:
        success_bool = success.lower() == "true"

    if isinstance(save_to_github, bool):
        save_to_github_bool = save_to_github
    else:
        save_to_github_bool = save_to_github.lower() == "true"

    if isinstance(save_to_claude_code_history, bool):
        save_to_claude_code_history_bool = save_to_claude_code_history
    else:
        save_to_claude_code_history_bool = save_to_claude_code_history.lower() == "true"

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
            if memory.persistent_rag:
                memory.persistent_rag.store(
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


@tool
async def coding_search_errors(
    user_id: str,
    project_id: str,
    query: str,
    k: int = 5,
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
    memory = _get_coding_memory(user_id, project_id)

    errors = await memory.search_similar_errors(query=query, k=k)

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
    memory = _get_coding_memory(user_id, project_id)

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


@tool
async def coding_analyze_patterns(
    user_id: str,
    project_id: str,
) -> str:
    """Analyze coding patterns and preferences from session history using AI.

    Use this tool to get insights into your coding style and patterns. The AI analyzes:
    - Language preferences (type hints, docstrings, async usage)
    - Library preferences (frameworks, testing tools, etc.)
    - Naming conventions (functions, classes, variables)
    - Code organization (file length, function length, patterns)
    - Testing practices (coverage, style, mock usage)
    - Common error patterns and anti-patterns

    This helps:
    - AI assistants generate code matching your style
    - Identify areas for improvement
    - Maintain consistency across the project
    - Learn from your coding patterns

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier

    Returns:
        Detailed analysis of coding patterns and preferences

    Note:
        Requires sufficient coding history (10+ file changes recommended)
        for reliable pattern extraction.

    Example:
        await coding_analyze_patterns(
            user_id="dev_john",
            project_id="api-service"
        )
    """
    memory = _get_coding_memory(user_id, project_id)

    patterns = await memory.analyze_coding_patterns()

    if patterns.get("confidence") == "low":
        return (
            f"⚠️ Insufficient data for reliable pattern analysis\n"
            f"Project: {project_id}\n\n"
            f"Continue coding and recording changes to build pattern history.\n"
            "Recommended: 10+ file changes for basic analysis, "
            "30+ for detailed insights."
        )

    result = f"🔍 Coding Pattern Analysis: {project_id}\n\n"

    # Language preferences
    if patterns.get("language_preferences"):
        result += "**Language Preferences:**\n"
        for key, value in patterns["language_preferences"].items():
            if isinstance(value, dict) and "confidence" in value:
                result += (
                    f"- {key}: {value.get('style', 'N/A')} "
                    f"(confidence: {value['confidence']})\n"
                )
        result += "\n"

    # Library preferences
    if patterns.get("library_preferences"):
        result += "**Library Preferences:**\n"
        for lib, details in patterns["library_preferences"].items():
            if isinstance(details, dict):
                result += (
                    f"- {lib}: confidence {details.get('confidence', 'unknown')}\n"
                )
        result += "\n"

    # Naming conventions
    if patterns.get("naming_conventions"):
        result += "**Naming Conventions:**\n"
        for element, style in patterns["naming_conventions"].items():
            if isinstance(style, dict):
                result += f"- {element}: {style.get('style', 'N/A')}\n"
        result += "\n"

    # Code organization
    if patterns.get("code_organization"):
        result += "**Code Organization:**\n"
        for aspect, pref in patterns["code_organization"].items():
            if isinstance(pref, dict):
                result += f"- {aspect}: {pref.get('preference', 'N/A')}\n"
        result += "\n"

    # Testing practices
    if patterns.get("testing_practices"):
        result += "**Testing Practices:**\n"
        for practice, level in patterns["testing_practices"].items():
            if isinstance(level, dict):
                result += f"- {practice}: {level.get('level', 'N/A')}\n"
        result += "\n"

    result += (
        "\n💡 This analysis helps AI assistants generate code that matches your style!"
    )

    return result


# Phase 2: Advanced Graph-Based Tools


@tool
async def coding_analyze_file_dependencies(
    user_id: str,
    project_id: str,
    file_path: str,
) -> str:
    """Analyze dependencies for a Python file using AST parsing.

    Automatically parses import statements and builds dependency graph.
    Useful for understanding file relationships and refactoring impact.

    Args:
        user_id: User identifier
        project_id: Project identifier
        file_path: Path to file to analyze

    Returns:
        Dependency analysis with imports, importers, depth, and circular dependencies

    Example:
        await coding_analyze_file_dependencies(
            user_id="dev_john",
            project_id="api-service",
            file_path="src/auth.py"
        )
    """
    memory = _get_coding_memory(user_id, project_id)

    deps = await memory.analyze_file_dependencies(file_path)

    result = f"📊 Dependency Analysis: {file_path}\n\n"

    if deps["imports"]:
        result += f"**Imports ({len(deps['imports'])} files):**\n"
        for imp in deps["imports"]:
            result += f"- {imp}\n"
        result += "\n"
    else:
        result += "**Imports:** None (leaf file)\n\n"

    if deps["imported_by"]:
        result += f"**Imported By ({len(deps['imported_by'])} files):**\n"
        for importer in deps["imported_by"]:
            result += f"- {importer}\n"
        result += "\n"
    else:
        result += "**Imported By:** None (no dependents)\n\n"

    result += f"**Import Depth:** {deps['import_depth']}\n\n"

    if deps["circular_deps"]:
        result += "⚠️  **Circular Dependencies Detected:**\n"
        for cycle in deps["circular_deps"]:
            result += f"- {' → '.join(cycle)}\n"
    else:
        result += "✅ **No Circular Dependencies**\n"

    return result


@tool
async def coding_analyze_refactor_impact(
    user_id: str,
    project_id: str,
    file_path: str,
) -> str:
    """Analyze the impact of refactoring a file.

    Shows which files would be affected and assesses risk level.
    Helps make informed refactoring decisions.

    Args:
        user_id: User identifier
        project_id: Project identifier
        file_path: File to refactor

    Returns:
        Impact analysis with affected files, risk level, and recommendations

    Example:
        await coding_analyze_refactor_impact(
            user_id="dev_john",
            project_id="api-service",
            file_path="src/models/user.py"
        )
    """
    memory = _get_coding_memory(user_id, project_id)

    impact = await memory.analyze_refactor_impact(file_path)

    risk_emoji = {
        "low": "✅",
        "medium": "⚠️ ",
        "high": "🚨",
        "unknown": "❓",
    }

    result = f"🔍 Refactoring Impact Analysis: {file_path}\n\n"
    result += (
        f"**Risk Level:** {risk_emoji[impact['risk_level']]} "
        f"{impact['risk_level'].upper()}\n\n"
    )

    if impact["affected_files"]:
        result += f"**Affected Files ({len(impact['affected_files'])}):**\n"
        for affected in impact["affected_files"][:10]:  # Limit display
            result += f"- {affected}\n"

        if len(impact["affected_files"]) > 10:
            result += f"- ... and {len(impact['affected_files']) - 10} more\n"

        result += "\n"

    result += "**Recommendations:**\n"
    for rec in impact["recommendations"]:
        result += f"{rec}\n"

    return result


@tool
async def coding_suggest_refactor_order(
    user_id: str,
    project_id: str,
    files: str,  # JSON array
) -> str:
    """Suggest safe order to refactor multiple files based on dependencies.

    Uses topological sorting to refactor leaf dependencies first.

    Args:
        user_id: User identifier
        project_id: Project identifier
        files: JSON array of file paths to refactor

    Returns:
        Suggested refactoring order with explanation

    Example:
        await coding_suggest_refactor_order(
            user_id="dev_john",
            project_id="api-service",
            files='["src/main.py", "src/auth.py", "src/models/user.py"]'
        )
    """
    memory = _get_coding_memory(user_id, project_id)

    # Parse files from JSON
    import json

    try:
        files_list = json.loads(files)
    except json.JSONDecodeError:
        return "❌ Error: Invalid JSON array for files parameter"

    order = await memory.suggest_refactor_order(files_list)

    result = "📋 Suggested Refactoring Order:\n\n"

    for i, file in enumerate(order, 1):
        result += f"{i}. {file}\n"

    result += (
        "\n💡 Refactor in this order to minimize breaking changes.\n"
        "Leaf dependencies (files with no internal imports) come first."
    )

    return result


# GitHub Integration Tools (using gh CLI)


@tool
async def coding_link_github_issue(
    user_id: str,
    project_id: str,
    issue_number: int | None = None,
) -> str:
    """Link current coding session to a GitHub issue for context tracking.

    Auto-detects issue number from branch name if not provided
    (e.g., 464-feat-... → #464).
    Fetches issue details via gh CLI and enriches session with title, labels, assignees.

    Requires: gh CLI authenticated (`gh auth login`)

    Args:
        user_id: User identifier
        project_id: Project identifier
        issue_number: GitHub issue number (auto-detect from branch if None)

    Returns:
        Confirmation with issue details

    Raises:
        Error if no active session or gh CLI fails

    Examples:
        # Auto-detect from branch name
        await coding_link_github_issue(
            user_id="dev_john",
            project_id="kagura-ai"
        )

        # Explicit issue number
        await coding_link_github_issue(
            user_id="dev_john",
            project_id="kagura-ai",
            issue_number=464
        )
    """
    from kagura.builtin.git import gh_extract_issue_from_branch

    memory = _get_coding_memory(user_id, project_id)

    # Auto-detect if not provided
    if issue_number is None:
        try:
            issue_number = await gh_extract_issue_from_branch()
        except Exception as e:
            return (
                f"❌ Could not auto-detect issue number: {e}\n\n"
                f"Branch name should start with issue number (e.g., '464-feat-...').\n"
                f"Please provide issue_number explicitly."
            )

        if issue_number is None:
            return (
                "❌ Could not detect issue number from branch name.\n\n"
                "Branch name should follow GitHub convention: "
                "{{issue}}-{{description}}\n"
                "Example: '464-feat-implement-memory'\n\n"
                "Please provide issue_number explicitly or rename your branch."
            )

    # Link to issue
    try:
        result = await memory.link_session_to_github_issue(issue_number)
        return result
    except ValueError as e:
        return (
            f"❌ Failed to link to issue #{issue_number}\n\n"
            f"Error: {e}\n\n"
            f"Make sure:\n"
            f"- gh CLI is installed and authenticated (`gh auth login`)\n"
            f"- Issue #{issue_number} exists in this repository\n"
            f"- You have permission to view the issue"
        )
    except RuntimeError as e:
        return f"❌ {e}"


@tool
async def coding_generate_pr_description(
    user_id: str,
    project_id: str,
) -> str:
    """Generate AI-powered PR description from current session activities.

    Analyzes all tracked changes, decisions, and errors to create a comprehensive
    PR description following best practices.

    Includes:
    - Summary of changes (what and why)
    - Key technical decisions with rationale
    - Files modified and reasons
    - Testing recommendations
    - Related issues (if linked)

    Requires active coding session with tracked activities.

    Args:
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Formatted PR description (markdown)

    Raises:
        Error if no active session

    Examples:
        # Generate PR description for current session
        pr_desc = await coding_generate_pr_description(
            user_id="dev_john",
            project_id="kagura-ai"
        )

        # Use with gh CLI:
        # gh pr create --title "feat: ..." --body "$pr_desc"
    """
    memory = _get_coding_memory(user_id, project_id)

    try:
        pr_desc = await memory.generate_pr_description()

        return (
            "📝 Generated PR Description:\n\n"
            "```markdown\n"
            f"{pr_desc}\n"
            "```\n\n"
            "💡 **Usage:**\n"
            "1. Copy the markdown above\n"
            '2. Use with: `gh pr create --title "..." --body "<paste here>"`\n'
            "3. Or save to file and use: `gh pr create --body-file pr_desc.md`"
        )

    except RuntimeError as e:
        return (
            f"❌ Error: {e}\n\nStart a coding session first with coding_start_session()"
        )


@tool
async def coding_get_issue_context(
    issue_number: int,
) -> str:
    """Get GitHub issue details for coding context.

    Fetches issue title, description, labels, and assignees using gh CLI.
    Useful at session start to understand requirements.

    Requires: gh CLI authenticated (`gh auth login`)

    Args:
        issue_number: GitHub issue number

    Returns:
        Formatted issue details (markdown)

    Examples:
        # Get issue context before starting work
        context = await coding_get_issue_context(464)
        print(context)

        # Then start session with this context
        await coding_start_session(
            description="Work on issue #464",
            tags='["issue-464"]'
        )
    """
    from kagura.builtin.git import gh_issue_get

    try:
        issue = await gh_issue_get(issue_number)

        labels = ", ".join(label["name"] for label in issue.get("labels", []))
        assignees = ", ".join(a["login"] for a in issue.get("assignees", []))

        body_preview = issue.get("body", "")[:500]
        if len(issue.get("body", "")) > 500:
            body_preview += "\n\n... (truncated)"

        return (
            f"# Issue #{issue['number']}: {issue['title']}\n\n"
            f"**URL:** {issue['url']}\n"
            f"**State:** {issue['state']}\n"
            f"**Labels:** {labels or 'None'}\n"
            f"**Assignees:** {assignees or 'None'}\n\n"
            f"## Description\n\n"
            f"{body_preview}"
        )

    except ValueError as e:
        return (
            f"❌ Failed to fetch issue #{issue_number}\n\n"
            f"Error: {e}\n\n"
            f"Make sure:\n"
            f"- gh CLI is installed and authenticated (`gh auth login`)\n"
            f"- Issue #{issue_number} exists\n"
            f"- You have permission to view it"
        )


# Helper Functions


def _parse_json_list(value: str, param_name: str = "parameter") -> list:
    """Parse JSON list parameter from MCP tools.

    Handles JSON parsing with error recovery for MCP tool parameters.

    Args:
        value: JSON string or already-parsed list
        param_name: Parameter name for error messages

    Returns:
        Parsed list (empty list if parsing fails)
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        parsed = json.loads(value) if isinstance(value, str) else value
        if not isinstance(parsed, list):
            logger.warning(
                f"{param_name} is not a list, converting to single-item list"
            )
            return [parsed]
        return parsed
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON for {param_name}: {e}, returning empty list")
        return []


def _parse_json_dict(value: str, param_name: str = "parameter") -> dict:
    """Parse JSON dict parameter from MCP tools.

    Handles JSON parsing with error recovery for MCP tool parameters.

    Args:
        value: JSON string or already-parsed dict
        param_name: Parameter name for error messages

    Returns:
        Parsed dict (empty dict if parsing fails)
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        parsed = json.loads(value) if isinstance(value, str) else value
        if not isinstance(parsed, dict):
            logger.warning(f"{param_name} is not a dict, returning empty dict")
            return {}
        return parsed
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON for {param_name}: {e}, returning empty dict")
        return {}


@tool
async def coding_track_interaction(
    user_id: str,
    project_id: str,
    user_query: str,
    ai_response: str,
    interaction_type: str,
    metadata: str = "{}",
) -> str:
    """Track AI-User interaction with automatic importance classification.

    Records conversations during coding sessions for cross-session context.
    High importance interactions (≥8.0) are automatically recorded to GitHub.

    **When to use:**
    - After important Q&A exchanges
    - When making design decisions through conversation
    - When struggling with a problem and finding solution
    - When discovering important insights
    - During implementation discussions

    Args:
        user_id: User identifier (developer, e.g., "kiyota")
        project_id: Project identifier (e.g., "kagura-ai")
        user_query: User's question or input
        ai_response: AI assistant's response
        interaction_type: Type of interaction:
            - "question": General questions (low importance)
            - "decision": Design/architecture decisions (high importance)
            - "struggle": Problem-solving discussions (high importance)
            - "discovery": New insights or findings (high importance)
            - "implementation": Code implementation discussions (medium)
            - "error_fix": Error resolution discussions (high importance)
        metadata: JSON object with additional context (optional)

    Returns:
        Confirmation with interaction ID

    Examples:
        # Record an error resolution discussion
        await coding_track_interaction(
            user_id="kiyota",
            project_id="kagura-ai",
            user_query="Why does memory_search_hybrid fail with 'str' vs 'int'?",
            ai_response="MCP tools receive params as strings. Convert to float/int.",
            interaction_type="error_fix"
        )

        # Record a design decision
        await coding_track_interaction(
            user_id="kiyota",
            project_id="kagura-ai",
            user_query="Should we use --body or --body-file for GitHub comments?",
            ai_response="Use --body-file for safety and reliability...",
            interaction_type="decision",
            metadata='{"context": "GitHub integration"}'
        )
    """
    import logging

    logger = logging.getLogger(__name__)

    coding_mem = _get_coding_memory(user_id, project_id)

    # Parse metadata
    metadata_dict = _parse_json_dict(metadata, "metadata")

    try:
        interaction_id = await coding_mem.track_interaction(
            user_query=user_query,
            ai_response=ai_response,
            interaction_type=interaction_type,
            metadata=metadata_dict,
        )

        return (
            f"✅ Interaction tracked: {interaction_id}\n"
            f"Type: {interaction_type}\n"
            f"Session: {coding_mem.current_session_id or 'No active session'}\n"
            f"\nNote: Importance will be classified in background. "
            f"High importance (≥8.0) interactions are automatically recorded to GitHub."
        )
    except ValueError as e:
        logger.error(f"Invalid interaction type: {e}")
        return f"❌ Error: {e}"
    except Exception as e:
        logger.error(f"Failed to track interaction: {e}", exc_info=True)
        return f"❌ Failed to track interaction: {e}"


# Source Code RAG Tools (Issue #490)


@tool
async def coding_index_source_code(
    user_id: str,
    project_id: str,
    directory: str,
    file_patterns: str = '["**/*.py"]',
    exclude_patterns: str = '["**/__pycache__/**", "**/test_*.py", "**/.venv/**"]',
    language: str = "python",
) -> str:
    """Index source code files into RAG for semantic code search.

    Scans a directory for source files, parses them (using AST for Python),
    chunks by function/class, and stores in RAG with metadata.

    Use this tool to enable semantic code search across your project.
    Useful for:
    - Understanding large codebases
    - Finding implementation examples
    - Locating where features are implemented
    - Cross-referencing related code

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        directory: Root directory to scan (e.g., "src/", "/path/to/project/src")
        file_patterns: JSON array of glob patterns to include (default: ["**/*.py"])
        exclude_patterns: JSON array of glob patterns to exclude
        language: Programming language (currently only "python" supported)

    Returns:
        Indexing summary with file count, chunks, and stats

    Examples:
        # Index Python source code
        await coding_index_source_code(
            user_id="kiyota",
            project_id="kagura-ai",
            directory="/home/jfk/works/kagura-ai/src"
        )

        # Index with custom patterns
        await coding_index_source_code(
            user_id="kiyota",
            project_id="my-project",
            directory="./src",
            file_patterns='["**/*.py", "**/*.pyx"]',
            exclude_patterns='["**/tests/**", "**/__pycache__/**"]'
        )
    """
    import ast
    import logging
    from pathlib import Path

    logger = logging.getLogger(__name__)

    # Parse patterns
    include_patterns = _parse_json_list(file_patterns, "file_patterns")
    exclude_patterns_list = _parse_json_list(exclude_patterns, "exclude_patterns")

    if language != "python":
        return (
            f"❌ Error: Only 'python' language is currently supported (got: {language})"
        )

    # Get CodingMemoryManager
    memory = _get_coding_memory(user_id, project_id)

    # Scan directory for files
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return f"❌ Error: Directory not found: {directory}"

    logger.info(f"Scanning directory: {dir_path}")

    # Find matching files
    matched_files = []
    for pattern in include_patterns:
        matched_files.extend(dir_path.glob(pattern))

    # Filter exclusions
    filtered_files = []
    for file in matched_files:
        should_exclude = False
        for exclude_pattern in exclude_patterns_list:
            import fnmatch

            if fnmatch.fnmatch(str(file), exclude_pattern):
                should_exclude = True
                break
        if not should_exclude and file.is_file():
            filtered_files.append(file)

    if not filtered_files:
        return f"⚠️ No files found matching patterns in {directory}"

    logger.info(f"Found {len(filtered_files)} files to index")

    # Index each file
    total_chunks = 0
    indexed_files = 0
    errors = []

    for file_path in filtered_files:
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source, filename=str(file_path))

            # Extract chunks (functions, classes, module docstring)
            chunks = _extract_code_chunks(source, tree, file_path)

            # Store each chunk in RAG
            for chunk in chunks:
                content = (
                    f"File: {chunk['file_path']}\n"
                    f"Type: {chunk['type']}\n"
                    f"Name: {chunk['name']}\n"
                    f"Lines: {chunk['line_start']}-{chunk['line_end']}\n\n"
                    f"{chunk['content']}"
                )

                metadata = {
                    "type": "source_code",
                    "file_path": str(chunk["file_path"]),
                    "line_start": chunk["line_start"],
                    "line_end": chunk["line_end"],
                    "chunk_type": chunk["type"],
                    "name": chunk["name"],
                    "language": language,
                }

                # Store in RAG
                memory.store_semantic(content=content, metadata=metadata)
                total_chunks += 1

            indexed_files += 1

        except SyntaxError as e:
            errors.append(f"{file_path.name}: Syntax error at line {e.lineno}")
        except Exception as e:
            errors.append(f"{file_path.name}: {str(e)[:100]}")

    # Build result
    result = "✅ Source Code Indexing Complete\n\n"
    result += f"**Project:** {project_id}\n"
    result += f"**Directory:** {directory}\n"
    result += f"**Files indexed:** {indexed_files}/{len(filtered_files)}\n"
    result += f"**Code chunks:** {total_chunks}\n"
    result += f"**Language:** {language}\n\n"

    if errors:
        result += f"**Errors ({len(errors)}):**\n"
        for error in errors[:5]:
            result += f"- {error}\n"
        if len(errors) > 5:
            result += f"- ... and {len(errors) - 5} more\n"
        result += "\n"

    result += "💡 **Next:** Use coding_search_source_code() to find code semantically"

    return result


def _extract_code_chunks(
    source: str,
    tree: ast.AST,
    file_path: Path,
    overlap_lines: int = 5,
) -> list[dict]:
    """Extract code chunks from AST for indexing with overlap.

    Args:
        source: Source code string
        tree: AST tree
        file_path: Path to source file
        overlap_lines: Number of lines to overlap before/after (default: 5)

    Returns:
        List of chunk dictionaries with overlapping context
    """
    import ast

    chunks = []
    source_lines = source.splitlines()
    total_lines = len(source_lines)

    # Extract imports for context
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

    imports_context = "Imports: " + ", ".join(imports[:10]) if imports else ""

    # Module-level docstring + imports (full file overview)
    if (
        isinstance(tree, ast.Module)
        and hasattr(tree, "body")
        and tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
    ):
        docstring = tree.body[0].value.value
        if isinstance(docstring, str):
            chunks.append(
                {
                    "file_path": str(file_path),
                    "type": "module",
                    "name": file_path.stem,
                    "line_start": 1,
                    "line_end": len(docstring.split("\n")),
                    "content": f"{docstring}\n\n{imports_context}",
                    "imports": imports,
                }
            )

    # Find all top-level classes for context
    classes_info = {}
    if isinstance(tree, ast.Module) and hasattr(tree, "body"):
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes_info[node.name] = {
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node) or "",
                }

    # Functions and classes with overlap
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Function/method
            func_name = node.name
            line_start = node.lineno
            line_end = node.end_lineno or line_start

            # Add overlap context
            overlap_start = max(1, line_start - overlap_lines)
            overlap_end = min(total_lines, line_end + overlap_lines)

            # Extract function with overlap
            func_source_with_overlap = "\n".join(
                source_lines[overlap_start - 1 : overlap_end]
            )

            # Get docstring
            docstring = ast.get_docstring(node) or ""

            # Find parent class if method
            parent_class = None
            for class_name, class_info in classes_info.items():
                if (
                    line_start >= class_info["line_start"]
                    and line_end <= class_info["line_end"]
                ):
                    parent_class = class_name
                    break

            context = f"Function: {func_name}"
            if parent_class:
                context = f"Class: {parent_class}, Method: {func_name}"

            chunks.append(
                {
                    "file_path": str(file_path),
                    "type": "function" if not parent_class else "method",
                    "name": func_name,
                    "line_start": line_start,
                    "line_end": line_end,
                    "content": (
                        f"{context}\n"
                        f"{imports_context}\n\n"
                        f"Code (with {overlap_lines}-line overlap):\n"
                        f"{func_source_with_overlap}\n\n"
                        f"Docstring:\n{docstring}"
                    ),
                    "parent_class": parent_class,
                    "imports": imports,
                }
            )

        elif isinstance(node, ast.ClassDef):
            # Class definition with all methods
            class_name = node.name
            line_start = node.lineno
            line_end = node.end_lineno or line_start

            # Add overlap
            overlap_start = max(1, line_start - overlap_lines)
            overlap_end = min(total_lines, line_end + overlap_lines)

            # Extract class source with overlap
            class_source = "\n".join(source_lines[overlap_start - 1 : overlap_end])

            # Get docstring
            docstring = ast.get_docstring(node) or ""

            # List methods with signatures
            methods = []
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Get method signature
                    args = [a.arg for a in m.args.args]
                    methods.append(f"{m.name}({', '.join(args)})")

            chunks.append(
                {
                    "file_path": str(file_path),
                    "type": "class",
                    "name": class_name,
                    "line_start": line_start,
                    "line_end": line_end,
                    "content": (
                        f"Class: {class_name}\n"
                        f"{imports_context}\n\n"
                        f"Code (with {overlap_lines}-line overlap):\n"
                        f"{class_source}\n\n"
                        f"Docstring:\n{docstring}\n\n"
                        f"Methods ({len(methods)}):\n"
                        + "\n".join(f"- {m}" for m in methods)
                    ),
                    "methods": methods,
                    "imports": imports,
                }
            )

    return chunks


@tool
async def coding_search_source_code(
    user_id: str,
    project_id: str,
    query: str,
    k: int = 5,
    file_filter: str | None = None,
) -> str:
    """Search indexed source code semantically.

    Finds code chunks relevant to the query using semantic search.
    Returns file paths, line ranges, and code snippets.

    Use this tool to:
    - Find implementation examples
    - Locate where a feature is implemented
    - Understand how something works
    - Find related code across the project

    Args:
        user_id: User identifier
        project_id: Project identifier
        query: Search query (e.g., "memory manager implementation", "authentication logic")
        k: Number of results to return (default: 5)
        file_filter: Optional file path filter (e.g., "src/kagura/core/**")

    Returns:
        Search results with file paths, line numbers, and code snippets

    Examples:
        # Find memory implementation
        await coding_search_source_code(
            user_id="kiyota",
            project_id="kagura-ai",
            query="memory manager store implementation"
        )

        # Search in specific directory
        await coding_search_source_code(
            user_id="kiyota",
            project_id="kagura-ai",
            query="RAG search",
            file_filter="src/kagura/core/**"
        )
    """
    memory = _get_coding_memory(user_id, project_id)

    # Perform semantic search using appropriate method
    if memory.persistent_rag and memory.lexical_searcher:
        # Use hybrid search if available
        results = memory.recall_hybrid(
            query=query,
            top_k=k,
            scope="persistent",
        )
    elif memory.persistent_rag:
        # Fallback to RAG-only search
        results = memory.search_memory(
            query=query,
            limit=k,
        )
    else:
        return "❌ RAG not available. Semantic search requires ChromaDB and sentence-transformers."

    if not results:
        return f"⚠️ No results found for query: '{query}'\n\nMake sure you've indexed the source code first with coding_index_source_code()"

    # Filter by file path if specified
    if file_filter:
        import fnmatch

        results = [
            r
            for r in results
            if fnmatch.fnmatch(r.get("metadata", {}).get("file_path", ""), file_filter)
        ]

    if not results:
        return f"⚠️ No results found matching file filter: {file_filter}"

    # Format results
    result = f"🔍 Source Code Search Results: '{query}'\n\n"
    result += f"**Found {len(results)} relevant code chunks:**\n\n"

    for i, res in enumerate(results, 1):
        metadata = res.get("metadata", {})
        if metadata.get("type") != "source_code":
            continue  # Skip non-source-code memories

        file_path = metadata.get("file_path", "unknown")
        line_start = metadata.get("line_start", 0)
        line_end = metadata.get("line_end", 0)
        chunk_type = metadata.get("chunk_type", "unknown")
        name = metadata.get("name", "")
        score = res.get("score", 0.0)

        content_preview = res.get("content", "")[:300]

        result += f"**{i}. {file_path}:{line_start}-{line_end}**\n"
        result += f"   Type: {chunk_type} `{name}`\n"
        result += f"   Score: {score:.3f}\n"
        result += f"   Preview:\n```\n{content_preview}\n```\n\n"

    result += "\n💡 **Tip:** Open files in your editor to see full implementation"

    return result


# Claude Code Integration Tools (Issue #491)


@tool
async def claude_code_save_session(
    user_id: str,
    project_id: str,
    session_title: str,
    work_summary: str,
    files_modified: str = "[]",
    conversation_context: str | None = None,
    tags: str = "[]",
    importance: str = "0.7",
) -> str:
    """Save Claude Code work session to Kagura Memory for future reference.

    Records your Claude Code session with context, making it searchable across sessions.
    Enables knowledge persistence and learning from past work.

    Use this tool:
    - At the end of a significant work session
    - After solving a complex problem
    - When making important decisions
    - To preserve context for future sessions

    Args:
        user_id: User identifier (developer, e.g., "kiyota")
        project_id: Project identifier (e.g., "kagura-ai")
        session_title: Brief title of the work session
        work_summary: Detailed summary of what was accomplished
        files_modified: JSON array of file paths modified (e.g., '["src/auth.py"]')
        conversation_context: Optional conversation snippets or key exchanges
        tags: JSON array of tags (e.g., '["bug-fix", "authentication"]')
        importance: Importance score 0.0-1.0 (default: 0.7)

    Returns:
        Confirmation with session ID

    Examples:
        # Save a debugging session
        await claude_code_save_session(
            user_id="kiyota",
            project_id="kagura-ai",
            session_title="Fix memory search RAG integration",
            work_summary=\"\"\"
            - Investigated Issue #337
            - Fixed memory_search to check both working and RAG
            - Added test coverage
            - All tests passing
            \"\"\",
            files_modified='["src/kagura/mcp/builtin/memory.py", "tests/test_memory.py"]',
            tags='["bug-fix", "memory", "rag", "issue-337"]',
            importance="0.9"
        )

        # Save a feature implementation
        await claude_code_save_session(
            user_id="kiyota",
            project_id="kagura-ai",
            session_title="Implement CLI inspection commands",
            work_summary="Added kagura memory list/search/stats commands for Issue #501",
            files_modified='["src/kagura/cli/memory_cli.py"]',
            tags='["feature", "cli", "issue-501"]'
        )
    """
    from datetime import datetime

    # Parse parameters
    files_list = _parse_json_list(files_modified, "files_modified")
    tags_list = _parse_json_list(tags, "tags")

    try:
        importance_float = float(importance)
    except ValueError:
        importance_float = 0.7

    # Get coding memory
    memory = _get_coding_memory(user_id, project_id)

    # Create session document for RAG
    timestamp = datetime.now().isoformat()
    session_doc = f"""
Claude Code Session: {session_title}
Project: {project_id}
Date: {timestamp}
Files Modified: {", ".join(files_list)}
Tags: {", ".join(tags_list)}

Summary:
{work_summary}
"""

    if conversation_context:
        session_doc += f"\nConversation Context:\n{conversation_context}"

    # Store in memory with metadata
    session_key = f"claude_code_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    metadata = {
        "type": "claude_code_session",
        "project_id": project_id,
        "session_title": session_title,
        "files_modified": files_list,
        "tags": tags_list,
        "timestamp": timestamp,
        "importance": importance_float,
        "platform": "claude_code",
    }

    # Store in persistent memory
    memory.persistent.store(
        key=session_key,
        value=session_doc,
        user_id=user_id,
        metadata=metadata,
    )

    # Also store in RAG for semantic search
    if memory.persistent_rag:
        memory.persistent_rag.store(
            content=session_doc,
            metadata=metadata,
            user_id=user_id,
        )

    # Create graph relationships if session is active
    if memory.current_session_id and memory.graph:
        # Link to current coding session
        memory.graph.add_edge(
            session_key,
            f"coding_session_{memory.current_session_id}",
            rel_type="claude_code_work",
        )

        # Link to modified files
        for file in files_list:
            memory.graph.add_edge(
                session_key,
                f"file_{file}",
                rel_type="modified",
            )

    result = f"✅ Claude Code session saved: {session_key}\n\n"
    result += f"**Project:** {project_id}\n"
    result += f"**Title:** {session_title}\n"
    result += f"**Files:** {len(files_list)} modified\n"
    result += f"**Tags:** {', '.join(tags_list)}\n"
    result += f"**Importance:** {importance_float}\n\n"
    result += f'💡 **Search later with:** claude_code_search_past_work(query="{session_title.split()[0]}")'

    return result


@tool
async def claude_code_search_past_work(
    user_id: str,
    project_id: str,
    query: str,
    k: int = 5,
    file_filter: str | None = None,
    date_range: str | None = None,
) -> str:
    """Search past Claude Code work sessions semantically.

    Find similar problems you've solved, decisions you've made, or work you've done
    in previous Claude Code sessions.

    Use this tool:
    - When starting work on a new issue
    - When encountering a familiar problem
    - To recall how you solved something before
    - To find related work context

    Args:
        user_id: User identifier
        project_id: Project identifier
        query: Search query (e.g., "memory search bug", "authentication implementation")
        k: Number of results to return (default: 5)
        file_filter: Optional file path filter (e.g., "src/kagura/core/**")
        date_range: Optional time filter ("last_7_days", "last_30_days", "last_90_days")

    Returns:
        Past work sessions with summaries, files, and solutions

    Examples:
        # Find similar debugging sessions
        await claude_code_search_past_work(
            user_id="kiyota",
            project_id="kagura-ai",
            query="memory search not returning results"
        )

        # Search recent work only
        await claude_code_search_past_work(
            user_id="kiyota",
            project_id="kagura-ai",
            query="CLI implementation",
            date_range="last_7_days"
        )

        # Search specific directory work
        await claude_code_search_past_work(
            user_id="kiyota",
            project_id="kagura-ai",
            query="RAG integration",
            file_filter="src/kagura/core/memory/**"
        )
    """
    from datetime import datetime, timedelta

    memory = _get_coding_memory(user_id, project_id)

    # Perform semantic search using appropriate method
    if memory.persistent_rag and memory.lexical_searcher:
        # Use hybrid search if available
        results = memory.recall_hybrid(
            query=query,
            top_k=k * 2,  # Get more candidates for filtering
            scope="persistent",
        )
    elif memory.persistent_rag:
        # Fallback to RAG-only search
        results = memory.search_memory(
            query=query,
            limit=k * 2,
        )
    else:
        return "❌ RAG not available. Semantic search requires ChromaDB and sentence-transformers."

    if not results:
        return f"⚠️ No past work sessions found for query: '{query}'\n\nSave sessions with claude_code_save_session() to build history"

    # Filter by type (Claude Code sessions only)
    claude_sessions = [
        r for r in results if r.get("metadata", {}).get("type") == "claude_code_session"
    ]

    # Filter by date range if specified
    if date_range:
        days_map = {
            "last_7_days": 7,
            "last_30_days": 30,
            "last_90_days": 90,
        }
        days = days_map.get(date_range, 30)
        cutoff = datetime.now() - timedelta(days=days)

        claude_sessions = [
            r
            for r in claude_sessions
            if datetime.fromisoformat(
                r.get("metadata", {}).get("timestamp", "2000-01-01")
            )
            > cutoff
        ]

    # Filter by file if specified
    if file_filter:
        import fnmatch

        claude_sessions = [
            r
            for r in claude_sessions
            if any(
                fnmatch.fnmatch(f, file_filter)
                for f in r.get("metadata", {}).get("files_modified", [])
            )
        ]

    if not claude_sessions:
        filters_msg = ""
        if date_range:
            filters_msg += f" (date: {date_range})"
        if file_filter:
            filters_msg += f" (files: {file_filter})"
        return f"⚠️ No Claude Code sessions found{filters_msg}"

    # Limit to k results
    claude_sessions = claude_sessions[:k]

    # Format results
    result = f"🔍 Past Claude Code Work: '{query}'\n\n"
    result += f"**Found {len(claude_sessions)} relevant sessions:**\n\n"

    for i, session in enumerate(claude_sessions, 1):
        metadata = session.get("metadata", {})
        content = session.get("content", "")

        title = metadata.get("session_title", "Untitled")
        timestamp = metadata.get("timestamp", "")
        files = metadata.get("files_modified", [])
        tags = metadata.get("tags", [])
        score = session.get("score", 0.0)

        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_str = timestamp

        # Extract summary from content (with bounds checking)
        summary = ""
        if "Summary:" in content:
            parts = content.split("Summary:")
            if len(parts) > 1:
                summary_parts = parts[1].split("\n\n")
                if summary_parts:
                    summary = summary_parts[0].strip()

        result += f"**{i}. [{date_str}] {title}**\n"
        result += f"   Score: {score:.3f}\n"
        result += f"   Files: {', '.join(files[:3])}"
        if len(files) > 3:
            result += f" (+{len(files) - 3} more)"
        result += "\n"
        result += f"   Tags: {', '.join(tags)}\n"
        result += f"   Summary: {summary[:200]}...\n\n"

    result += "\n💡 **Tip:** Use this context to avoid repeating past work"

    return result
