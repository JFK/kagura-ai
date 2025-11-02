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
    # File operations - DANGEROUS (local filesystem access)
    "file_read": {"remote": False},
    "file_write": {"remote": False},
    "dir_list": {"remote": False},
    # Shell execution - DANGEROUS (arbitrary code execution)
    "shell_exec": {"remote": False},
    # GitHub operations - READ operations SAFE, WRITE operations DANGEROUS
    "github_exec": {"remote": False},  # General executor - dangerous
    "github_issue_view": {"remote": True},  # Read-only - safe
    "github_issue_list": {"remote": True},  # Read-only - safe
    "github_pr_view": {"remote": True},  # Read-only - safe
    "github_pr_create": {"remote": False},  # Write operation - dangerous
    "github_pr_merge": {"remote": False},  # Write operation - very dangerous
    # Media operations - DANGEROUS (local application execution)
    "media_open_audio": {"remote": False},
    "media_open_image": {"remote": False},
    "media_open_video": {"remote": False},
    # Web/API tools - SAFE (external API calls only)
    "web_scrape": {"remote": True},
    "brave_web_search": {"remote": True},
    "brave_local_search": {"remote": True},
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
    # Meta/Routing tools - SAFE (in-memory only)
    "meta_create_agent": {"remote": True},
    "route_query": {"remote": True},
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
            if tool_name.startswith("file_"):
                reason = "Local filesystem access"
            elif tool_name == "shell_exec":
                reason = "Shell command execution"
            elif tool_name.startswith("media_open_"):
                reason = "Local application execution"
            else:
                reason = "Restricted for security"
        else:
            reason = "Safe for remote access"

        return {"remote": remote_allowed, "reason": reason}

    # Unknown tool - default deny
    return {"remote": False, "reason": "Unknown tool (default deny)"}
