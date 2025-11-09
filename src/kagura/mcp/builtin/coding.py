# ruff: noqa: F822
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

Note: Tools are dynamically imported via __getattr__, so static linters
cannot detect them. This is intentional for backward compatibility.
"""

from __future__ import annotations

import warnings

# Eager import all tools to trigger @tool registration
# This must happen at module load time, not lazily via __getattr__
from kagura.mcp.tools.coding import *  # noqa: F403, F401


def __getattr__(name: str):
    """Backward compatibility shim with deprecation warning.

    Tools are already imported above, so this only triggers deprecation warning.
    """
    warnings.warn(
        f"kagura.mcp.builtin.coding.{name} is deprecated and will be removed in v4.5.0. "
        "Use kagura.mcp.tools.coding instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Return from globals (already imported above)
    if name in globals():
        return globals()[name]

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
