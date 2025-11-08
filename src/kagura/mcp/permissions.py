"""Tool permission system for MCP server.

Controls which tools can be accessed remotely vs. locally only.
"""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Literal

# Tool permission configuration
# Maps tool name patterns to permission settings
TOOL_PERMISSIONS: dict[str, dict[str, bool]] = {
    # Memory tools - SAFE for remote access (database only)
    "memory_store": {"remote": True},
    "memory_recall": {"remote": True},
    "memory_search": {"remote": True},
    "memory_list": {"remote": True},
    "memory_delete": {"remote": True},
    "memory_feedback": {"remote": True},
    "memory_get_related": {"remote": True},
    "memory_record_interaction": {"remote": True},
    "memory_get_user_pattern": {"remote": True},
    # Memory extended tools - SAFE (database only)
    "memory_fetch": {"remote": True},
    "memory_fuzzy_recall": {"remote": True},
    "memory_get_tool_history": {"remote": True},
    "memory_search_ids": {"remote": True},
    "memory_stats": {"remote": True},
    "memory_timeline": {"remote": True},
    "memory_get_chunk_context": {"remote": True},
    "memory_get_chunk_metadata": {"remote": True},
    "memory_get_full_document": {"remote": True},
    # File operations - DANGEROUS (local filesystem access)
    "file_read": {"remote": False},
    "file_write": {"remote": False},
    "dir_list": {"remote": False},
    # Shell execution - DANGEROUS (arbitrary code execution)
    "shell_exec": {"remote": False},
    # Coding memory tools - SAFE (database only)
    "coding_start_session": {"remote": True},
    "coding_end_session": {"remote": True},
    "coding_resume_session": {"remote": True},
    "coding_get_current_session_status": {"remote": True},
    "coding_track_file_change": {"remote": True},
    "coding_record_error": {"remote": True},
    "coding_record_decision": {"remote": True},
    "coding_track_interaction": {"remote": True},
    "coding_search_errors": {"remote": True},
    "coding_search_source_code": {"remote": True},
    "coding_get_project_context": {"remote": True},
    "coding_analyze_patterns": {"remote": True},
    "coding_suggest_refactor_order": {"remote": True},
    "coding_link_github_issue": {"remote": True},
    "coding_generate_pr_description": {"remote": True},
    "coding_get_issue_context": {"remote": True},
    # Coding tools with file access - DANGEROUS (reads server files)
    "coding_index_source_code": {"remote": False},
    "coding_analyze_file_dependencies": {"remote": False},
    "coding_analyze_refactor_impact": {"remote": False},
    # Claude Code memory tools - SAFE (database only)
    "claude_code_save_session": {"remote": True},
    "claude_code_search_past_work": {"remote": True},
    # GitHub operations - API vs gh CLI
    "github_exec": {"remote": False},  # gh CLI wrapper - requires local gh
    "github_issue_view": {"remote": False},  # gh CLI - requires local gh
    "github_issue_list": {"remote": False},  # gh CLI - requires local gh
    "github_issue_create": {"remote": True},  # API-based - safe for remote
    "github_pr_view": {"remote": False},  # gh CLI - requires local gh
    "github_pr_create": {"remote": False},  # gh CLI - requires local gh
    "github_pr_merge": {"remote": False},  # gh CLI - requires local gh
    # GitHub safe wrappers - DANGEROUS (same as regular gh commands)
    "gh_safe_exec": {"remote": False},  # General executor with safety checks
    "gh_pr_create_safe": {"remote": False},  # Write operation with confirmation
    "gh_pr_merge_safe": {"remote": False},  # Write operation with confirmation
    # Media operations - DANGEROUS (local application execution)
    "media_open_audio": {"remote": False},
    "media_open_image": {"remote": False},
    "media_open_video": {"remote": False},
    # Web/API tools - SAFE (external API calls only)
    "web_scrape": {"remote": True},
    "brave_web_search": {"remote": True},
    "brave_news_search": {"remote": True},
    "brave_image_search": {"remote": True},
    "brave_video_search": {"remote": True},
    # YouTube tools - SAFE (API calls only)
    "get_youtube_metadata": {"remote": True},
    "get_youtube_transcript": {"remote": True},
    "youtube_summarize": {"remote": True},
    "youtube_fact_check": {"remote": True},
    # Multimodal tools - SAFE (database storage only)
    "multimodal_index": {"remote": True},
    "multimodal_search": {"remote": True},
    # Meta tools - DANGEROUS (code generation/manipulation)
    "meta_create_agent": {"remote": False},  # Code generation - dangerous
    "meta_fix_code_error": {"remote": False},  # Code generation/execution risk
    # Routing tools - LOCAL ONLY (security)
    "route_query": {"remote": False},  # Local routing logic
    # Academic tools - SAFE (API calls only)
    "arxiv_search": {"remote": True},
    # Telemetry tools - SAFE (read-only metrics)
    "telemetry_stats": {"remote": True},
    "telemetry_cost": {"remote": True},
    # Fact-checking tools - SAFE (API calls only)
    "fact_check_claim": {"remote": True},
}


def is_tool_allowed(
    tool_name: str,
    context: Literal["local", "remote"] = "local",
) -> bool:
    """Check if a tool is allowed in the given context.

    Args:
        tool_name: Name of the tool (e.g., "memory_store", "file_read")
        context: Execution context ("local" or "remote")

    Returns:
        True if tool is allowed, False otherwise

    Examples:
        >>> is_tool_allowed("memory_store", "remote")
        True
        >>> is_tool_allowed("file_read", "remote")
        False
        >>> is_tool_allowed("file_read", "local")
        True
    """
    # Local context allows all tools
    if context == "local":
        return True

    # Remote context - check permissions
    # Try exact match first
    if tool_name in TOOL_PERMISSIONS:
        return TOOL_PERMISSIONS[tool_name].get("remote", False)

    # Try pattern matching (for future wildcard support)
    for pattern, permissions in TOOL_PERMISSIONS.items():
        if fnmatch(tool_name, pattern):
            return permissions.get("remote", False)

    # Default: deny remote access for unknown tools (fail-safe)
    return False


def get_allowed_tools(
    all_tools: list[str],
    context: Literal["local", "remote"] = "local",
) -> list[str]:
    """Filter tools by permission.

    Args:
        all_tools: List of all available tool names
        context: Execution context ("local" or "remote")

    Returns:
        List of allowed tool names

    Examples:
        >>> tools = ["memory_store", "file_read", "brave_web_search"]
        >>> get_allowed_tools(tools, "remote")
        ['memory_store', 'brave_web_search']
        >>> get_allowed_tools(tools, "local")
        ['memory_store', 'file_read', 'brave_web_search']
    """
    return [tool for tool in all_tools if is_tool_allowed(tool, context)]


def get_denied_tools(
    all_tools: list[str],
    context: Literal["local", "remote"] = "remote",
) -> list[str]:
    """Get list of tools that are denied in the given context.

    Args:
        all_tools: List of all available tool names
        context: Execution context ("local" or "remote")

    Returns:
        List of denied tool names

    Examples:
        >>> tools = ["memory_store", "file_read", "brave_web_search"]
        >>> get_denied_tools(tools, "remote")
        ['file_read']
    """
    return [tool for tool in all_tools if not is_tool_allowed(tool, context)]


def get_tool_permission_info(tool_name: str) -> dict[str, bool | str]:
    """Get permission information for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Dict with permission info: {"remote": bool, "reason": str}

    Examples:
        >>> get_tool_permission_info("file_read")
        {'remote': False, 'reason': 'Local filesystem access'}
    """
    # Check if in permissions
    if tool_name in TOOL_PERMISSIONS:
        remote_allowed = TOOL_PERMISSIONS[tool_name].get("remote", False)

        # Determine reason
        if not remote_allowed:
            if tool_name.startswith("file_") or tool_name == "dir_list":
                reason = "Local filesystem access"
            elif tool_name == "shell_exec":
                reason = "Shell command execution"
            elif tool_name.startswith("media_open_"):
                reason = "Local application execution"
            elif tool_name.startswith("coding_") and (
                "index" in tool_name
                or "dependencies" in tool_name
                or "refactor_impact" in tool_name
            ):
                reason = "Server filesystem access (reads local files)"
            elif tool_name == "meta_fix_code_error":
                reason = "Code generation/execution risk"
            elif tool_name == "meta_create_agent":
                reason = "Code generation risk"
            elif tool_name.startswith("github_"):
                reason = "GitHub write operations"
            else:
                reason = "Restricted for security"
        else:
            reason = "Safe for remote access"

        return {"remote": remote_allowed, "reason": reason}

    # Unknown tool - default deny
    return {"remote": False, "reason": "Unknown tool (default deny)"}
