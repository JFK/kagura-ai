"""Type stubs for coding memory module.

This .pyi file provides type information for dynamically added mixin methods
so that pyright/mypy can properly type-check code using CodingMemoryManager.
"""

from typing import Any

from kagura.core.memory.coding.manager import (
    CodingMemoryManager as _CodingMemoryManagerBase,
)
from kagura.core.memory.coding.manager import UserCancelledError as UserCancelledError
from kagura.core.memory.models.coding import (
    CodingPattern as CodingPattern,
    CodingSession as CodingSession,
    DesignDecision as DesignDecision,
    ErrorRecord as ErrorRecord,
    FileChangeRecord as FileChangeRecord,
    ProjectContext as ProjectContext,
)

# Augment CodingMemoryManager with mixin methods
class CodingMemoryManager(_CodingMemoryManagerBase):
    # file_tracker.py
    async def track_file_change(
        self,
        file_path: str,
        change_type: str,
        reason: str | None = None,
        old_path: str | None = None,
    ) -> str: ...

    # error_recorder.py
    async def record_error(
        self,
        error_type: str,
        message: str,
        stack_trace: str | None = None,
        file_path: str | None = None,
        line_number: int | None = None,
        solution: str | None = None,
        tags: list[str] | None = None,
    ) -> str: ...
    async def search_similar_errors(
        self, error_type: str, context: str | None = None, limit: int = 5
    ) -> list[dict[str, Any]]: ...

    # decision_recorder.py
    async def record_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: list[str] | None = None,
        impact: str | None = None,
        tags: list[str] | None = None,
        related_files: list[str] | None = None,
        confidence: float = 0.8,
    ) -> str: ...
    async def get_decision_implementation_status(
        self, decision_id: str
    ) -> dict[str, Any]: ...

    # analyzers.py
    async def get_project_context(
        self, focus: str | None = None
    ) -> ProjectContext: ...
    async def analyze_coding_patterns(self) -> dict[str, Any]: ...
    async def track_interaction(
        self,
        user_query: str,
        ai_response: str,
        interaction_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> str: ...
    async def analyze_file_dependencies(
        self, file_path: str
    ) -> dict[str, Any]: ...
    async def analyze_refactor_impact(self, file_path: str) -> dict[str, Any]: ...
    async def suggest_refactor_order(
        self, files: list[str]
    ) -> dict[str, Any]: ...
    async def get_error_solution_suggestions(
        self, error_record_id: str
    ) -> dict[str, Any]: ...

    # session_manager.py
    async def start_coding_session(
        self,
        description: str,
        tags: list[str] | None = None,
        github_issue: str | None = None,
    ) -> str: ...
    async def resume_coding_session(
        self, session_id: str | None = None
    ) -> str: ...
    async def end_coding_session(
        self,
        success: bool = True,
        summary: str | None = None,
        save_to_github: bool = False,
    ) -> dict[str, Any]: ...
    async def get_current_session_status(self) -> dict[str, Any]: ...
    def _detect_active_session(self) -> str | None: ...
    async def _auto_save_session_progress(self) -> None: ...

    # github_integration.py
    async def link_session_to_github_issue(
        self, issue_number: int, repo: str | None = None
    ) -> dict[str, Any]: ...
    async def generate_pr_description(
        self, session_id: str, target_branch: str = "main"
    ) -> dict[str, Any]: ...

__all__ = [
    "CodingMemoryManager",
    "UserCancelledError",
    "CodingSession",
    "FileChangeRecord",
    "ErrorRecord",
    "DesignDecision",
    "ProjectContext",
    "CodingPattern",
]
