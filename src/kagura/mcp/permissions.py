"""Tool permission system for MCP server.

Controls which tools can be accessed remotely vs. locally only.

Issue #720: Simplified to 19 final tools, all remote-capable.
All tools are safe for remote access (API/database operations only,
no filesystem or shell access).
"""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Literal

# Tool permission configuration
# Issue #720: Final 19 tools, all remote-capable
TOOL_PERMISSIONS: dict[str, dict[str, bool]] = {
    # ==============================================================================
    # Memory Tools (8) - All SAFE for remote (database operations only)
    # ==============================================================================
    "memory_store": {"remote": True},
    "memory_delete": {"remote": True},
    "memory_stats": {"remote": True},
    "memory_search_semantic": {"remote": True},  # Issue #720: New
    "memory_search_keyword": {"remote": True},  # Issue #720: New
    "memory_search_timeline": {"remote": True},  # Issue #720: New
    "memory_get_document": {"remote": True},  # Issue #720: New
    "memory_get_neighbors": {"remote": True},  # Issue #720: New
    # ==============================================================================
    # Coding Tools (8: 7 final + 1 utility) - All SAFE for remote (database only)
    # ==============================================================================
    "coding_start_session": {"remote": True},
    "coding_resume_session": {"remote": True},
    "coding_get_status": {"remote": True},  # Issue #720: New
    "coding_end_session": {"remote": True},
    "coding_track_change": {"remote": True},  # Issue #720: New
    "coding_record_item": {"remote": True},  # Issue #720: New
    "coding_search_context": {"remote": True},  # Issue #720: New
    "coding_search_errors": {"remote": True},  # Utility
    # ==============================================================================
    # Search Tools (4) - All SAFE for remote (external API calls only)
    # ==============================================================================
    "brave_web_search": {"remote": True},
    "brave_news_search": {"remote": True},
    "arxiv_search": {"remote": True},
    "youtube_transcript": {"remote": True},  # Issue #720: New
    # ==============================================================================
    # Utility Tools (2) - SAFE for remote (API/database operations)
    # ==============================================================================
    "fact_check_claim": {"remote": True},
    "web_scrape": {"remote": True},
}


def is_tool_allowed(
    tool_name: str,
    context: Literal["local", "remote"] = "local",
) -> bool:
    """Check if a tool is allowed in the given context.

    Args:
        tool_name: Name of the tool to check
        context: Execution context ("local" or "remote")

    Returns:
        True if tool is allowed in this context, False otherwise

    Examples:
        >>> is_tool_allowed("memory_store", "remote")
        True

        >>> is_tool_allowed("memory_store", "local")
        True

        >>> is_tool_allowed("file_read", "remote")
        False

        >>> is_tool_allowed("unknown_tool", "remote")
        True  # Default allow for unlisted tools in local context
    """
    # Local context allows all tools
    if context == "local":
        return True

    # Remote context: check permissions
    # Look for exact match first
    if tool_name in TOOL_PERMISSIONS:
        return TOOL_PERMISSIONS[tool_name].get("remote", False)

    # Try pattern matching (for wildcards like "github_*")
    for pattern, perms in TOOL_PERMISSIONS.items():
        if fnmatch(tool_name, pattern):
            return perms.get("remote", False)

    # Default: disallow unknown tools in remote context (security)
    return False


def filter_tools_by_context(
    tools: list[str],
    context: Literal["local", "remote"] = "local",
) -> list[str]:
    """Filter tool list based on execution context.

    Args:
        tools: List of tool names
        context: Execution context ("local" or "remote")

    Returns:
        Filtered list of allowed tools

    Examples:
        >>> tools = ["memory_store", "file_read", "shell_exec"]
        >>> filter_tools_by_context(tools, "remote")
        ['memory_store']

        >>> filter_tools_by_context(tools, "local")
        ['memory_store', 'file_read', 'shell_exec']
    """
    return [tool for tool in tools if is_tool_allowed(tool, context)]


def get_allowed_tools(
    all_tools: list[str],
    context: Literal["local", "remote"] = "local",
) -> list[str]:
    """Filter tools by permission (alias for filter_tools_by_context).

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
    return filter_tools_by_context(all_tools, context)


def get_tool_permission_summary() -> dict[str, int]:
    """Get summary statistics of tool permissions.

    Returns:
        Dictionary with counts:
        - total: Total registered tools
        - remote_safe: Tools allowed in remote context
        - local_only: Tools restricted to local context

    Example:
        >>> summary = get_tool_permission_summary()
        >>> print(f"Remote-safe: {summary['remote_safe']}/{summary['total']}")
    """
    total = len(TOOL_PERMISSIONS)
    remote_safe = sum(1 for perms in TOOL_PERMISSIONS.values() if perms.get("remote"))
    local_only = total - remote_safe

    return {
        "total": total,
        "remote_safe": remote_safe,
        "local_only": local_only,
    }


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
        >>> get_denied_tools(tools, "local")
        []  # All tools allowed in local context
    """
    return [tool for tool in all_tools if not is_tool_allowed(tool, context)]


def get_tool_permission_info(tool_name: str) -> dict[str, bool | str]:
    """Get permission information for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Dict with permission info: {"remote": bool, "reason": str}

    Examples:
        >>> get_tool_permission_info("memory_store")
        {'remote': True, 'reason': 'Safe for remote access'}
    """
    if tool_name in TOOL_PERMISSIONS:
        remote_allowed = TOOL_PERMISSIONS[tool_name].get("remote", False)
        reason = "Safe for remote access" if remote_allowed else "Restricted for security"
        return {"remote": remote_allowed, "reason": reason}

    # Unknown tool - default deny in remote context
    return {"remote": False, "reason": "Unknown tool (default deny)"}
