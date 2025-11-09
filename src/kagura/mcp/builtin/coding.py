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


def __getattr__(name: str):
    """Lazy import with deprecation warning for backward compatibility.

    This allows old imports to still work while showing deprecation warnings.
    Tools are imported on-demand to avoid circular import issues.
    """
    warnings.warn(
        f"kagura.mcp.builtin.coding.{name} is deprecated and will be removed in v4.5.0. "
        "Use kagura.mcp.tools.coding instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Lazy import from new location
    from kagura.mcp.tools import coding as coding_tools

    if hasattr(coding_tools, name):
        return getattr(coding_tools, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

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
