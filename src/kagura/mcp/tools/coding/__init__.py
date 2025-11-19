"""Coding MCP tools - modular organization.

Reorganized in v4.3.0 from monolithic mcp/builtin/coding.py into focused modules:
- session.py: Session lifecycle (start, resume, status, end)
- file_tracking.py: File change tracking
- error_tracking.py: Error recording and search
- decision.py: Design decision recording
- project_context.py: Project context retrieval
- patterns.py: Pattern analysis
- dependencies.py: Dependency analysis and refactoring
- github_integration.py: GitHub issue/PR integration
- interaction.py: AI-User interaction tracking
- source_indexing.py: Source code RAG indexing and search

All tools are re-exported from this module for convenience.
"""

# Re-export all tools for easy importing
from kagura.mcp.tools.coding.decision import coding_record_decision
from kagura.mcp.tools.coding.dependencies import (
    coding_analyze_file_dependencies,
    coding_analyze_refactor_impact,
    coding_suggest_refactor_order,
)
from kagura.mcp.tools.coding.error_tracking import (
    coding_record_error,
    coding_record_item,  # Issue #720: New (unified error+decision)
    coding_search_errors,
)
from kagura.mcp.tools.coding.file_tracking import (
    coding_track_change,  # Issue #720: New (renamed)
    coding_track_file_change,
)
from kagura.mcp.tools.coding.github_integration import (
    coding_generate_pr_description,
    coding_get_issue_context,
    coding_link_github_issue,
)
from kagura.mcp.tools.coding.interaction import coding_track_interaction
from kagura.mcp.tools.coding.patterns import coding_analyze_patterns
from kagura.mcp.tools.coding.project_context import (
    coding_get_project_context,
    coding_search_context,  # Issue #720: New (renamed)
)
from kagura.mcp.tools.coding.session import (
    coding_end_session,
    coding_get_current_session_status,
    coding_get_status,  # Issue #720: New (renamed)
    coding_resume_session,
    coding_start_session,
)
from kagura.mcp.tools.coding.source_indexing import (
    coding_index_source_code,
    coding_search_source_code,
)

__all__ = [
    # Session management (4 + 1 new = 5)
    "coding_start_session",
    "coding_resume_session",
    "coding_get_current_session_status",
    "coding_get_status",  # Issue #720: New
    "coding_end_session",
    # File tracking (1 + 1 new = 2)
    "coding_track_file_change",
    "coding_track_change",  # Issue #720: New
    # Error tracking (2 + 1 new = 3)
    "coding_record_error",
    "coding_record_item",  # Issue #720: New (unified)
    "coding_search_errors",
    # Decision recording (1)
    "coding_record_decision",
    # Context & patterns (2 + 1 new = 3)
    "coding_get_project_context",
    "coding_search_context",  # Issue #720: New
    "coding_analyze_patterns",
    # Dependencies (3)
    "coding_analyze_file_dependencies",
    "coding_analyze_refactor_impact",
    "coding_suggest_refactor_order",
    # GitHub integration (3)
    "coding_link_github_issue",
    "coding_generate_pr_description",
    "coding_get_issue_context",
    # Interaction (1)
    "coding_track_interaction",
    # Source indexing (2)
    "coding_index_source_code",
    "coding_search_source_code",
]
