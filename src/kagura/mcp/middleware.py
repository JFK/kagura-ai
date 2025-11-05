"""MCP Server middleware for auto-logging tool calls to memory.

Automatically logs MCP tool executions to memory for better context awareness
and result reuse.

Features:
- Non-blocking logging (doesn't fail tool execution)
- Recursion prevention (excludes memory_* tools)
- Configurable via environment variables
- Result truncation (default 500 chars)

Example:
    # Automatic logging when user calls any MCP tool
    result = await brave_web_search(user_id="kiyota", query="Python async")
    # → Automatically logged to persistent memory with key:
    #    "brave_web_search_2025-11-05T16:30:00"

Privacy:
    Opt-out: Set KAGURA_DISABLE_AUTO_LOGGING=true

Related: Issue #400 - Auto-remember MCP tool requests and results
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Excluded tools (prevent recursion)
EXCLUDED_TOOLS = {
    # Memory tools - CRITICAL: Must exclude to prevent infinite loop
    "memory_store",
    "memory_recall",
    "memory_search",
    "memory_delete",
    "memory_feedback",
    "memory_get_tool_history",  # Self-reference
    "memory_stats",
    "memory_list",
    "memory_fuzzy_recall",
    "memory_timeline",
    "memory_search_ids",
    "memory_fetch",
    "memory_search_hybrid",
    "memory_get_related",
    "memory_record_interaction",
    "memory_get_user_pattern",
}


def is_auto_logging_enabled() -> bool:
    """Check if auto-logging is enabled.

    Priority order:
    1. KAGURA_DISABLE_AUTO_LOGGING env var (opt-out, highest priority)
    2. Default: True (enabled)

    Returns:
        True if auto-logging should be enabled

    Example:
        >>> os.environ["KAGURA_DISABLE_AUTO_LOGGING"] = "true"
        >>> is_auto_logging_enabled()
        False
    """
    # Check environment variable (opt-out)
    if os.getenv("KAGURA_DISABLE_AUTO_LOGGING", "").lower() in ("true", "1", "yes"):
        return False

    # Default: enabled
    return True


def should_log_tool(tool_name: str) -> bool:
    """Determine if tool call should be logged.

    Args:
        tool_name: Name of the tool being called

    Returns:
        True if should log, False otherwise

    Reasons to skip:
    - Auto-logging disabled globally
    - Tool in excluded list (memory_* tools)
    - Tool starts with "memory_" prefix (catch-all)

    Example:
        >>> should_log_tool("brave_web_search")
        True
        >>> should_log_tool("memory_store")
        False
    """
    if not is_auto_logging_enabled():
        return False

    # Skip memory tools to avoid recursion (CRITICAL)
    if tool_name in EXCLUDED_TOOLS or tool_name.startswith("memory_"):
        return False

    return True


async def log_tool_call_to_memory(
    user_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    result: str,
) -> None:
    """Auto-log tool call to memory.

    Stores tool execution history for context awareness.

    Args:
        user_id: User identifier
        tool_name: Name of the executed tool
        arguments: Tool arguments (dict)
        result: Tool result (string)

    Note:
        - Non-blocking: Errors are logged but don't fail tool execution
        - Result truncation: Large results truncated to MAX_LENGTH
        - Storage: persistent scope, "mcp_history" agent
        - Tags: ["mcp_history", tool_name] for easy filtering

    Example:
        >>> await log_tool_call_to_memory(
        ...     user_id="kiyota",
        ...     tool_name="brave_web_search",
        ...     arguments={"query": "Python", "count": 5},
        ...     result="1. Python.org\\n2. Python docs..."
        ... )
        # → Stored in persistent memory as:
        # key: "brave_web_search_2025-11-05T16:30:00.123456"
        # value: {"tool": "brave_web_search", "args": {...}, "result": "...", "timestamp": "..."}
    """
    if not should_log_tool(tool_name):
        return

    try:
        # Import here to avoid circular dependency
        from kagura.mcp.builtin.memory import memory_store

        timestamp = datetime.now().isoformat()

        # Truncate large results
        MAX_LENGTH = int(os.getenv("KAGURA_AUTO_LOG_MAX_LENGTH", "500"))
        truncated_result = result[:MAX_LENGTH]
        if len(result) > MAX_LENGTH:
            truncated_result += "... (truncated)"

        # Prepare log entry
        log_entry = {
            "tool": tool_name,
            "args": arguments,
            "result": truncated_result,
            "timestamp": timestamp,
        }

        # Store in persistent memory
        await memory_store(
            user_id=user_id,
            agent_name="mcp_history",
            key=f"{tool_name}_{timestamp}",
            value=json.dumps(log_entry, ensure_ascii=False),
            scope="persistent",
            tags=json.dumps(["mcp_history", tool_name]),
            importance=0.3,  # Low importance (housekeeping data)
        )

        logger.debug(f"Auto-logged tool call: {tool_name}")

    except Exception as e:
        # CRITICAL: Don't fail tool execution if logging fails
        logger.warning(f"Failed to auto-log tool call '{tool_name}': {e}")


__all__ = [
    "is_auto_logging_enabled",
    "should_log_tool",
    "log_tool_call_to_memory",
    "EXCLUDED_TOOLS",
]
