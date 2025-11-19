"""Coding MCP tools - Issue #720 final configuration.

Provides 7 coding session management tools with clear responsibility separation:
- MCP Server: Pure tool provider (no decision-making)
- LLM Client: Decision maker (chooses strategies, analyzes patterns, generates descriptions)

Session Management (4 tools):
- coding_start_session: Start tracked coding session
- coding_resume_session: Resume previous session
- coding_get_status: Get current session status
- coding_end_session: End session with AI summary

Recording Operations (2 tools):
- coding_track_change: Track file changes with rationale
- coding_record_item: Record errors, decisions, or notes (type-based)

Search Operations (1 tool):
- coding_search_context: Search project coding context

Total: 7 tools (reduced from 19+ in v4.3.0)

Removed tools (now LLM responsibilities):
- coding_analyze_patterns → LLM analyzes from search results
- coding_generate_pr_description → LLM generates from session data
- coding_suggest_refactor_order → LLM decides from dependency analysis
"""

from kagura.mcp.tools.coding.error_tracking import (
    coding_record_item,
    coding_search_errors,
)
from kagura.mcp.tools.coding.file_tracking import coding_track_change
from kagura.mcp.tools.coding.project_context import coding_search_context
from kagura.mcp.tools.coding.session import (
    coding_end_session,
    coding_get_status,
    coding_resume_session,
    coding_start_session,
)

__all__ = [
    # Session management (4)
    "coding_start_session",
    "coding_resume_session",
    "coding_get_status",
    "coding_end_session",
    # Recording (2)
    "coding_track_change",
    "coding_record_item",
    # Search (1)
    "coding_search_context",
    # Utility (kept for compatibility)
    "coding_search_errors",
]
