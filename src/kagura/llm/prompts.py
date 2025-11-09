"""Carefully crafted prompts for coding context analysis.

This module contains high-quality prompt templates following best practices:
- Few-shot learning with examples
- Chain-of-thought reasoning
- Structured output formats (JSON/YAML)
- Clear role definitions
- Explicit constraints

All prompts are designed for maximum reliability and consistency.
"""

from typing import Any

from kagura.llm.prompt_loader import load_template, render_template

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def format_duration(minutes: float) -> str:
    """Format duration in human-readable form.

    Args:
        minutes: Duration in minutes

    Returns:
        Human-readable duration string

    Examples:
        >>> format_duration(45.5)
        '45 minutes'
        >>> format_duration(90)
        '1.5 hours'
        >>> format_duration(150)
        '2.5 hours'
    """
    if minutes < 60:
        return f"{minutes:.0f} minutes"
    hours = minutes / 60
    return f"{hours:.1f} hours"


def build_session_summary_prompt(session_data: dict[str, Any]) -> dict[str, str]:
    """Build session summary prompt from session data.

    Args:
        session_data: Dictionary containing session information

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    duration_minutes = session_data.get("duration_minutes", 0)
    duration_human = format_duration(duration_minutes)

    files_list = "\n".join(f"- {f}" for f in session_data.get("files_touched", []))
    errors_list = "\n\n".join(
        f"**Error {i + 1}:** {e.get('message', 'Unknown')}\n"
        f"File: {e.get('file_path', 'Unknown')}\n"
        f"Solution: {e.get('solution', 'Not yet resolved')}"
        for i, e in enumerate(session_data.get("errors", []))
    )
    decisions_list = "\n\n".join(
        f"**Decision {i + 1}:** {d.get('decision', 'Unknown')}\n"
        f"Rationale: {d.get('rationale', 'Not specified')}"
        for i, d in enumerate(session_data.get("decisions", []))
    )

    system_prompt = load_template("coding/session_summary_system.j2")
    user_prompt = render_template(
        "coding/session_summary_user.j2",
        duration_minutes=duration_minutes,
        duration_human=duration_human,
        project_id=session_data.get("project_id", "Unknown"),
        description=session_data.get("description", "No description"),
        file_count=len(session_data.get("files_touched", [])),
        files_list=files_list or "No files modified",
        error_count=len(session_data.get("errors", [])),
        fixed_count=sum(1 for e in session_data.get("errors", []) if e.get("resolved")),
        errors_list=errors_list or "No errors encountered",
        decision_count=len(session_data.get("decisions", [])),
        decisions_list=decisions_list or "No decisions recorded",
        session_id=session_data.get("session_id", "unknown"),
    )

    return {"system": system_prompt, "user": user_prompt}


def build_error_pattern_prompt(errors: list[dict[str, Any]]) -> dict[str, str]:
    """Build error pattern analysis prompt.

    Args:
        errors: List of error records

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    error_history = "\n\n".join(
        f"### Error #{i + 1}\n"
        f"**Type:** {e.get('error_type', 'Unknown')}\n"
        f"**Message:** {e.get('message', 'N/A')}\n"
        f"**Location:** {e.get('file_path', 'unknown')}:{e.get('line_number', 0)}\n"
        f"**Timestamp:** {e.get('timestamp', 'Unknown')}\n"
        f"**Resolved:** {'Yes' if e.get('resolved') else 'No'}\n"
        f"**Solution:** {e.get('solution', 'Not yet resolved')}"
        for i, e in enumerate(errors)
    )

    system_prompt = load_template("coding/error_pattern_system.j2")
    user_prompt = render_template("coding/error_pattern_user.j2", error_history=error_history)

    return {"system": system_prompt, "user": user_prompt}


def build_solution_prompt(
    current_error: dict[str, Any], similar_errors: list[dict[str, Any]]
) -> dict[str, str]:
    """Build solution suggestion prompt.

    Args:
        current_error: The current error needing resolution
        similar_errors: Past similar errors with solutions

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    screenshot_section = ""
    if current_error.get("screenshot_path") or current_error.get("screenshot_base64"):
        screenshot_section = (
            "**Screenshot:** Available (analyze for additional context)\n"
        )

    similar_errors_text = (
        "\n\n".join(
            f"### Past Error #{i + 1} (Similarity: {e.get('similarity', 0):.1%})\n"
            f"**Type:** {e.get('error_type', 'Unknown')}\n"
            f"**Message:** {e.get('message', 'N/A')}\n"
            f"**Solution Applied:** {e.get('solution', 'No solution recorded')}\n"
            f"**Outcome:** {'Successful' if e.get('resolved') else 'Unresolved'}"
            for i, e in enumerate(similar_errors)
        )
        or "No similar past errors found"
    )

    system_prompt = load_template("coding/solution_suggestion_system.j2")
    user_prompt = render_template(
        "coding/solution_suggestion_user.j2",
        error_type=current_error.get("error_type", "Unknown"),
        error_message=current_error.get("message", "No message"),
        file_path=current_error.get("file_path", "unknown"),
        line_number=current_error.get("line_number", 0),
        stack_trace=current_error.get("stack_trace", "No stack trace available"),
        screenshot_section=screenshot_section,
        similar_errors=similar_errors_text,
    )

    return {"system": system_prompt, "user": user_prompt}


def build_preference_extraction_prompt(
    file_changes: list[dict[str, Any]], decisions: list[dict[str, Any]]
) -> dict[str, str]:
    """Build coding preference extraction prompt.

    Args:
        file_changes: List of file change records
        decisions: List of design decisions

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    changes_text = "\n\n".join(
        f"### Change #{i + 1}\n"
        f"**File:** {c.get('file_path', 'unknown')}\n"
        f"**Action:** {c.get('action', 'unknown')}\n"
        f"**Reason:** {c.get('reason', 'Not specified')}\n"
        f"**Diff Summary:** {c.get('diff', 'N/A')[:200]}..."
        for i, c in enumerate(file_changes[:30])  # Limit to 30 most recent
    )

    decisions_text = "\n\n".join(
        f"### Decision #{i + 1}\n"
        f"**Decision:** {d.get('decision', 'Unknown')}\n"
        f"**Rationale:** {d.get('rationale', 'Not specified')}\n"
        f"**Alternatives:** {', '.join(d.get('alternatives', ['None']))}"
        for i, d in enumerate(decisions[:20])  # Limit to 20 most recent
    )

    system_prompt = load_template("coding/preference_extraction_system.j2")
    user_prompt = render_template(
        "coding/preference_extraction_user.j2",
        change_count=len(file_changes),
        file_changes=changes_text,
        decision_count=len(decisions),
        design_decisions=decisions_text,
    )

    return {"system": system_prompt, "user": user_prompt}


def build_context_compression_prompt(
    full_context: str,
    target_tokens: int,
    original_tokens: int,
    preserve_topics: list[str],
) -> dict[str, str]:
    """Build context compression prompt.

    Args:
        full_context: The full context to compress
        target_tokens: Target token count
        original_tokens: Original token count
        preserve_topics: Topics that must be preserved

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    preserve_text = "\n".join(f"- {topic}" for topic in preserve_topics)

    system_prompt = load_template("coding/context_compression_system.j2")
    user_prompt = render_template(
        "coding/context_compression_user.j2",
        target_tokens=target_tokens,
        original_tokens=original_tokens,
        full_context=full_context,
        preserve_topics=preserve_text or "- All critical information",
    )

    return {"system": system_prompt, "user": user_prompt}
