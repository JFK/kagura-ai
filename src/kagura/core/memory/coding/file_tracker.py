"""File change tracking module for coding memory.

This module provides file modification tracking with context for cross-session
understanding. Extracted from manager.py as part of Phase 3.2 refactoring.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kagura.core.memory.coding.manager import CodingMemoryManager

from kagura.core.memory.models.coding import FileChangeRecord

logger = logging.getLogger(__name__)


async def track_file_change(
    self: CodingMemoryManager,
    file_path: str,
    action: Literal["create", "edit", "delete", "rename", "refactor", "test"],
    diff: str,
    reason: str,
    related_files: list[str] | None = None,
    line_range: tuple[int, int] | None = None,
    implements_decision_id: str | None = None,
) -> str:
    """Track file modification with context.

    Records file changes with reasoning for cross-session understanding.

    Args:
        file_path: Path to modified file
        action: Type of modification
        diff: Git-style diff or summary of changes
        reason: Why this change was made
        related_files: Other affected/related files
        line_range: Lines affected (start, end)
        implements_decision_id: ID of design decision this change implements
            (Phase 2)

    Returns:
        Unique ID for this file change record

    Example:
        >>> change_id = await coding_mem.track_file_change(
        ...     file_path="src/auth.py",
        ...     action="edit",
        ...     diff="+ def validate_token(token: str) -> bool:",
        ...     reason="Add token validation for JWT auth",
        ...     related_files=["src/middleware.py"]
        ... )
    """
    record = FileChangeRecord(
        file_path=file_path,
        action=action,
        diff=diff,
        reason=reason,
        related_files=related_files or [],
        session_id=self.current_session_id,
        line_range=line_range,
    )

    # Generate unique ID
    change_id = f"change_{uuid.uuid4().hex[:12]}"

    # Store in persistent memory (user_id scoped)
    key = self._make_key(f"file_change:{change_id}")
    self.persistent.store(
        key=key, value=record.model_dump(mode="json"), user_id=self.user_id
    )

    # Add to RAG if available for semantic search
    if self.rag:
        content_text = (
            f"File: {file_path}\n"
            f"Action: {action}\n"
            f"Reason: {reason}\n"
            f"Diff: {diff[:500]}"
        )
        self.rag.store(
            content=content_text,
            user_id=self.user_id,
            metadata={
                "type": "file_change",
                "file_path": file_path,
                "action": action,
                "project_id": self.project_id,
                "session_id": self.current_session_id or "",
                "change_id": change_id,  # Entity ID for retrieval
            },
            agent_name=self.agent_name,
        )

    # Add to graph if available
    if self.graph:
        # Node for file change
        self.graph.add_node(
            node_id=change_id,
            node_type="memory",
            data={
                "file_path": file_path,
                "action": action,
                "reason": reason,
                "project_id": self.project_id,
            },
        )

        # Link to related files
        for related_file in related_files or []:
            related_key = self._make_key(f"file:{related_file}")
            # Ensure related file node exists (using helper)
            self._ensure_graph_node(
                node_id=related_key,
                node_type="memory",
                data={"file_path": related_file},
            )
            self.graph.add_edge(
                src_id=change_id,
                dst_id=related_key,
                rel_type="affects",
                weight=0.8,
            )

        # Link to current session if active
        if self.current_session_id:
            self.graph.add_edge(
                src_id=self.current_session_id,
                dst_id=change_id,
                rel_type="includes",
                weight=1.0,
            )

        # Link to decision if implementing one (Phase 2)
        if implements_decision_id:
            if self.graph.graph.has_node(implements_decision_id):
                self.graph.add_edge(
                    src_id=change_id,
                    dst_id=implements_decision_id,
                    rel_type="implements",
                    weight=1.0,
                )
                logger.info(
                    f"Linked file change {change_id} "
                    f"to decision {implements_decision_id}"
                )

    logger.info(f"Tracked file change: {change_id} ({file_path})")

    # Auto-save session progress after each file change (v4.0.9)
    if self.current_session_id:
        await self._auto_save_session_progress()  # type: ignore[attr-defined]

    return change_id
