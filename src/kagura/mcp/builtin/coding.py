"""Built-in MCP tools for Coding Memory operations.

.. deprecated:: 4.3.0
    This module has been reorganized into ``kagura.mcp.tools.coding``.
    Import from ``kagura.mcp.tools.coding`` instead.
    This compatibility facade will be removed in v4.5.0.

Exposes coding-specialized memory features via MCP for AI coding assistants
like Claude Code, Cursor, and others.

All tools have been moved to modular files in ``src/kagura/mcp/tools/coding/``:
- session.py: Session lifecycle management
- file_tracking.py: File change tracking
- error_tracking.py: Error recording and search
- decision.py: Design decision recording
- project_context.py: Project context retrieval
- patterns.py: Pattern analysis
- dependencies.py: Dependency analysis
- github_integration.py: GitHub integration
- interaction.py: Interaction tracking
- source_indexing.py: Source code indexing
"""

from __future__ import annotations

import warnings

# Deprecation warning
warnings.warn(
    "kagura.mcp.builtin.coding is deprecated and will be removed in v4.5.0. "
    "Use kagura.mcp.tools.coding instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all tools from new modular structure for backward compatibility
from kagura.mcp.tools.coding import (  # noqa: F401
    coding_analyze_file_dependencies,
    coding_analyze_patterns,
    coding_analyze_refactor_impact,
    coding_end_session,
    coding_generate_pr_description,
    coding_get_current_session_status,
    coding_get_issue_context,
    coding_get_project_context,
    coding_index_source_code,
    coding_link_github_issue,
    coding_record_decision,
    coding_record_error,
    coding_resume_session,
    coding_search_errors,
    coding_search_source_code,
    coding_start_session,
    coding_suggest_refactor_order,
    coding_track_file_change,
    coding_track_interaction,
)

__all__ = [
    # Session management
    "coding_start_session",
    "coding_resume_session",
    "coding_get_current_session_status",
    "coding_end_session",
    # File tracking
    "coding_track_file_change",
    # Error tracking
    "coding_record_error",
    "coding_search_errors",
    # Decision recording
    "coding_record_decision",
    # Context & patterns
    "coding_get_project_context",
    "coding_analyze_patterns",
    # Dependencies
    "coding_analyze_file_dependencies",
    "coding_analyze_refactor_impact",
    "coding_suggest_refactor_order",
    # GitHub integration
    "coding_link_github_issue",
    "coding_generate_pr_description",
    "coding_get_issue_context",
    # Interaction
    "coding_track_interaction",
    # Source indexing
    "coding_index_source_code",
    "coding_search_source_code",
]
