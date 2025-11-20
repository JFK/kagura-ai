"""Coding service - Business logic for coding session management.

Simplified implementation for Phase 1. Delegates to CodingMemoryManager.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kagura.services.base import BaseService


@dataclass
class SessionResult:
    """Result of a coding session operation."""

    session_id: str | None
    success: bool
    message: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CodingService(BaseService):
    """Business logic for coding session management.

    Simplified implementation that delegates to CodingMemoryManager.
    Future: Extract more business logic from CodingMemoryManager.

    Example:
        >>> from kagura.core.memory.coding_memory import CodingMemoryManager
        >>> coding_memory = CodingMemoryManager("user_123", "kagura-ai")
        >>> service = CodingService(coding_memory)
        >>>
        >>> result = await service.start_session(
        ...     description="Implement new feature",
        ...     tags=["feature", "api"]
        ... )
        >>> print(result.session_id)
    """

    def __init__(self, coding_memory_manager):
        """Initialize coding service.

        Args:
            coding_memory_manager: CodingMemoryManager instance
        """
        super().__init__()
        self.coding_memory = coding_memory_manager

    async def start_session(
        self,
        description: str,
        tags: list[str] | None = None,
    ) -> SessionResult:
        """Start a new coding session.

        Args:
            description: Session description
            tags: Optional tags

        Returns:
            SessionResult with session_id
        """
        self.validate_required(description, "description")

        try:
            # Delegate to CodingMemoryManager (method: start_coding_session)
            session_id = await self.coding_memory.start_coding_session(
                description=description, tags=tags or []
            )

            return SessionResult(
                session_id=session_id,
                success=True,
                message="Session started successfully",
            )
        except Exception as e:
            self.logger.error(f"Failed to start session: {e}")
            return SessionResult(
                session_id=None,
                success=False,
                message=f"Failed to start session: {str(e)}",
            )

    async def end_session(
        self, success: bool = True, summary: str | None = None
    ) -> SessionResult:
        """End current coding session.

        Args:
            success: Whether session was successful
            summary: Optional summary

        Returns:
            SessionResult
        """
        try:
            result = await self.coding_memory.end_session(
                success=success, summary=summary
            )

            return SessionResult(
                session_id=result.get("session_id"),
                success=True,
                message="Session ended successfully",
                metadata=result,
            )
        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")
            return SessionResult(
                session_id=None,
                success=False,
                message=f"Failed to end session: {str(e)}",
            )

    async def track_file_change(
        self,
        file_path: str,
        action: str,
        diff: str,
        reason: str,
    ) -> SessionResult:
        """Track a file change.

        Args:
            file_path: File path
            action: Action type (edit, create, delete, etc.)
            diff: Change summary
            reason: Reason for change

        Returns:
            SessionResult
        """
        self.validate_required(file_path, "file_path")
        self.validate_required(action, "action")

        try:
            await self.coding_memory.track_file_change(
                file_path=file_path, action=action, diff=diff, reason=reason
            )

            return SessionResult(
                session_id=None,
                success=True,
                message="File change tracked",
            )
        except Exception as e:
            self.logger.error(f"Failed to track file change: {e}")
            return SessionResult(
                session_id=None,
                success=False,
                message=f"Failed to track: {str(e)}",
            )
