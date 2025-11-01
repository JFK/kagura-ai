"""Built-in MCP tools for Coding Memory operations.

Exposes coding-specialized memory features via MCP for AI coding assistants
like Claude Code, Cursor, and others.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal

from kagura import tool

if TYPE_CHECKING:
    from kagura.core.memory.coding_memory import CodingMemoryManager

# Global cache for CodingMemoryManager instances
# Key: f"{user_id}:{project_id}"
_coding_memory_cache: dict[str, CodingMemoryManager] = {}


def _get_coding_memory(user_id: str, project_id: str) -> CodingMemoryManager:
    """Get or create cached CodingMemoryManager instance.

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier

    Returns:
        Cached or new CodingMemoryManager instance
    """
    import logging

    logger = logging.getLogger(__name__)

    from kagura.core.memory.coding_memory import CodingMemoryManager

    cache_key = f"{user_id}:{project_id}"
    logger.debug(f"_get_coding_memory: cache_key={cache_key}")

    if cache_key not in _coding_memory_cache:
        logger.debug(
            f"_get_coding_memory: Creating CodingMemoryManager for {cache_key}"
        )
        _coding_memory_cache[cache_key] = CodingMemoryManager(
            user_id=user_id,
            project_id=project_id,
            enable_rag=True,  # Always enable for semantic search
            enable_graph=True,  # Always enable for relationships
        )
        logger.debug("_get_coding_memory: CodingMemoryManager created")
    else:
        logger.debug("_get_coding_memory: Using cached CodingMemoryManager")

    return _coding_memory_cache[cache_key]


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
    """Track file modifications during coding sessions with context and reasoning.

    Use this tool to record file changes with WHY they were made, not just WHAT changed.
    This enables AI assistants to understand project evolution across sessions.

    When to use:
    - After making significant changes to a file
    - When refactoring code structure
    - When creating new files/modules
    - When decisions affect multiple files

    Args:
        user_id: User identifier (developer, e.g., "dev_john")
        project_id: Project identifier (e.g., "kagura-ai", "my-web-app")
        file_path: Path to modified file (e.g., "src/auth.py")
        action: Type of modification:
            - "create": New file created
            - "edit": Existing file modified
            - "delete": File removed
            - "rename": File renamed/moved
            - "refactor": Code restructured
            - "test": Test file added/modified
        diff: Summary of changes or git-style diff (be concise but informative)
        reason: WHY this change was made (critical for context)
        related_files: JSON array of related file paths (e.g., '["src/middleware.py"]')
        line_range: Optional line range affected (e.g., "42,57" for lines 42-57)

    Returns:
        Confirmation with unique change ID

    Examples:
        # Recording a new feature
        await coding_track_file_change(
            user_id="dev_john",
            project_id="api-service",
            file_path="src/auth.py",
            action="edit",
            diff="+ def validate_token(token: str) -> bool:\\n+     ...",
            reason="Add JWT token validation for new auth middleware",
            related_files='["src/middleware.py", "src/models/user.py"]'
        )

        # Recording a refactor
        await coding_track_file_change(
            user_id="dev_john",
            project_id="api-service",
            file_path="src/utils/helpers.py",
            action="refactor",
            diff="Extracted 3 helper functions into separate module",
            reason="Reduce file size and improve modularity",
            line_range="1,150"
        )
    """
    memory = _get_coding_memory(user_id, project_id)

    # Parse related_files from JSON
    try:
        related_files_list = json.loads(related_files)
    except json.JSONDecodeError:
        related_files_list = []

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
    """Record coding errors with stack traces and optional screenshots for pattern learning.

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
        error_type: Error classification (e.g., "TypeError", "SyntaxError", "ImportError")
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
            stack_trace="Traceback:\\n  File \\"auth.py\\", line 42, in validate\\n    ...",
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
            solution="Changed datetime.now() to datetime.now(timezone.utc) for consistency",
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

    # Parse tags from JSON
    try:
        tags_list = json.loads(tags)
    except json.JSONDecodeError:
        tags_list = []

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
    """Record design and architectural decisions with rationale for project context tracking.

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
        alternatives: JSON array of other options considered (e.g., '["Option A", "Option B"]')
        impact: Expected impact on the project (optional)
        tags: JSON array of categorization tags (e.g., '["architecture", "security"]')
        related_files: JSON array of files affected by this decision
        confidence: Confidence level in this decision (0.0-1.0, default 0.8)

    Returns:
        Confirmation with decision ID

    Examples:
        # Recording an architectural decision
        await coding_record_decision(
            user_id="dev_john",
            project_id="api-service",
            decision="Use JWT tokens for authentication instead of sessions",
            rationale="Stateless auth enables horizontal scaling without session store. "
                     "JWTs can be validated without database lookups, improving performance. "
                     "Better for planned mobile app integration.",
            alternatives='["Session-based auth", "OAuth-only"]',
            impact="Eliminates need for session storage. Requires key rotation strategy.",
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

    return (
        f"✅ Decision recorded: {decision_id}\n"
        f"Decision: {decision}\n"
        f"Confidence: {confidence:.0%}\n"
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
    """Start a tracked coding session to maintain context across related changes.

    Use this tool at the beginning of a coherent work session (e.g., implementing
    a feature, fixing a bug, refactoring a module). The session will automatically
    track all file changes, errors, and decisions until you end it.

    Benefits:
    - Groups related activities together
    - Automatic session summary with AI analysis
    - Better context for future work
    - Pattern learning from session outcomes

    When to use:
    - Starting work on a new feature
    - Beginning a debugging session
    - Starting a refactoring task
    - Any coherent block of work

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        description: Brief description of session goals (what you plan to do)
        tags: JSON array of session tags (e.g., '["feature", "authentication"]')

    Returns:
        Session ID and confirmation

    Raises:
        Error if a session is already active (end it first!)

    Examples:
        # Starting a feature implementation session
        await coding_start_session(
            user_id="dev_john",
            project_id="api-service",
            description="Implement JWT authentication system with RS256 signing",
            tags='["feature", "authentication", "security"]'
        )

        # Starting a debugging session
        await coding_start_session(
            user_id="dev_john",
            project_id="api-service",
            description="Debug database connection timeout issues",
            tags='["bugfix", "database", "performance"]'
        )
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
async def coding_end_session(
    user_id: str,
    project_id: str,
    summary: str | None = None,
    success: bool | None = None,
) -> str:
    """End coding session and generate AI-powered summary of changes, decisions, and learnings.

    Use this tool when finishing a coherent work session. The system will:
    1. Collect all tracked activities (files, errors, decisions)
    2. Generate comprehensive AI summary (if not provided)
    3. Store session data for future reference
    4. Update coding patterns and preferences

    The AI summary includes:
    - Session overview and objectives achieved
    - Key technical decisions and rationale
    - Challenges faced and solutions applied
    - Patterns observed (good and bad practices)
    - Recommendations for future sessions

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        summary: Optional user-provided summary (if None, AI generates it)
        success: Whether session objectives were met (optional)

    Returns:
        Session summary and statistics

    Raises:
        Error if no active session to end

    Examples:
        # End session with AI-generated summary
        await coding_end_session(
            user_id="dev_john",
            project_id="api-service",
            success=True
        )

        # End session with custom summary
        await coding_end_session(
            user_id="dev_john",
            project_id="api-service",
            summary="Completed JWT auth implementation. All tests passing. "
                   "Need to add refresh token mechanism in next session.",
            success=True
        )
    """
    memory = _get_coding_memory(user_id, project_id)

    result = await memory.end_coding_session(
        summary=summary,
        success=success,
    )

    success_emoji = "✅" if success else ("⚠️" if success is False else "ℹ️")
    duration_str = (
        f"{result['duration_minutes']:.1f} minutes"
        if result["duration_minutes"]
        else "Unknown"
    )

    return (
        f"{success_emoji} Coding session ended: {result['session_id']}\n"
        f"Duration: {duration_str}\n"
        f"Files touched: {len(result['files_touched'])}\n"
        f"Errors: {result['errors_encountered']} encountered, {result['errors_fixed']} fixed\n"
        f"Decisions: {result['decisions_made']}\n\n"
        f"📝 Summary:\n{result['summary']}\n\n"
        f"💾 Session data saved for future reference and pattern learning."
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
    """Get comprehensive project context including recent changes, patterns, and key decisions.

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
            f"Recommended: 10+ file changes for basic analysis, 30+ for detailed insights."
        )

    result = f"🔍 Coding Pattern Analysis: {project_id}\n\n"

    # Language preferences
    if patterns.get("language_preferences"):
        result += "**Language Preferences:**\n"
        for key, value in patterns["language_preferences"].items():
            if isinstance(value, dict) and "confidence" in value:
                result += f"- {key}: {value.get('style', 'N/A')} (confidence: {value['confidence']})\n"
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
