"""Coding memory endpoints.

Coding memory API routes:
- GET /api/v1/coding/doctor - Coding memory health check (Issue #664)
- GET /api/v1/coding/sessions - List coding sessions (Issue #666)
- GET /api/v1/coding/sessions/{session_id} - Get session detail (Issue #666)
"""

import json
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from kagura.api import models
from kagura.api.dependencies import get_current_user
from kagura.api.models_doctor import CodingDoctorResponse, CodingStats
from kagura.core.memory import MemoryManager

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_coding_memory() -> CodingStats:
    """Check coding memory status.

    Returns:
        Coding memory statistics
    """
    try:
        manager = MemoryManager(user_id="system", agent_name="coding-memory")

        # Count sessions - search in persistent storage
        sessions = manager.persistent.search(
            query="%session%",
            user_id="system",
            agent_name="coding-memory",
            limit=1000,
        )

        # Try to identify unique projects
        projects: set[str] = set()
        for session in sessions:
            if "metadata" in session:
                try:
                    import json

                    metadata = json.loads(session.get("metadata", "{}"))
                    if "project_id" in metadata:
                        projects.add(metadata["project_id"])
                except Exception:  # JSON parsing can fail
                    pass

        return CodingStats(
            sessions_count=len(sessions),
            projects_count=len(projects),
        )
    except Exception:  # Ignore errors - operation is non-critical
        return CodingStats(
            sessions_count=0,
            projects_count=0,
        )


@router.get("/doctor", response_model=CodingDoctorResponse)
async def get_coding_doctor(user: dict[str, Any] = Depends(get_current_user)) -> CodingDoctorResponse:
    """Get coding memory health check.

    Returns coding memory diagnostics including:
    - Number of tracked projects
    - Number of recorded sessions

    Args:
        user: Authenticated user (dependency)

    Returns:
        Coding memory health check results

    Example:
        GET /api/v1/coding/doctor
        Response: {
            "stats": {
                "sessions_count": 125,
                "projects_count": 3
            },
            "status": "ok"
        }
    """
    stats = _check_coding_memory()

    return CodingDoctorResponse(
        stats=stats,
        status="ok" if stats.sessions_count > 0 else "info",
    )


# ============================================================================
# Coding Sessions (Issue #666 - Phase 2)
# ============================================================================


@router.get("/sessions", response_model=models.SessionListResponse)
async def list_coding_sessions(
    user: dict[str, Any] = Depends(get_current_user),
    project_id: Annotated[str | None, Query(description="Filter by project ID")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    offset: Annotated[int, Query(ge=0, description="Offset")] = 0,
) -> models.SessionListResponse:
    """List coding sessions.

    Returns list of coding sessions with summary information.

    Args:
        user: Authenticated user (dependency)
        project_id: Optional project filter
        limit: Number of sessions to return
        offset: Offset for pagination

    Returns:
        Session list with pagination info

    Example:
        GET /api/v1/coding/sessions?project_id=kagura-ai&limit=10
        Response: {
            "sessions": [
                {
                    "id": "abc123",
                    "project_id": "kagura-ai",
                    "description": "Fix Issue #510",
                    "start_time": "2025-11-12T10:00:00Z",
                    "end_time": "2025-11-12T12:15:00Z",
                    "duration_seconds": 8100,
                    "file_changes_count": 5,
                    "decisions_count": 2,
                    "errors_count": 1,
                    "github_issue": 510,
                    "success": true
                },
                ...
            ],
            "total": 42,
            "page": 1,
            "page_size": 20
        }
    """
    try:
        manager = MemoryManager(user_id="system", agent_name="coding-memory")

        # Build search query
        if project_id:
            query = f"project:{project_id}:session:%"
        else:
            query = "%session%"

        # Search sessions in persistent storage
        all_sessions_raw = manager.persistent.search(
            query=query,
            user_id="system",
            agent_name="coding-memory",
            limit=1000,  # Get all, then paginate
        )

        # Parse sessions
        sessions: list[models.SessionSummary] = []
        for sess_raw in all_sessions_raw:
            try:
                # Parse session data
                value_str = sess_raw.get("value", "{}")
                sess_data = (
                    json.loads(value_str) if isinstance(value_str, str) else value_str
                )

                # Extract session ID from key (format: "project:xxx:session:yyy")
                key = sess_raw.get("key", "")
                session_id = key.split(":")[-1] if ":" in key else key

                # Parse timestamps
                start_time = sess_data.get("start_time")
                end_time = sess_data.get("end_time")

                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time)

                # Calculate duration
                duration = None
                if end_time and start_time:
                    duration = int((end_time - start_time).total_seconds())

                # Count activities
                file_changes_count = len(sess_data.get("file_changes", []))
                decisions_count = len(sess_data.get("decisions", []))
                errors_count = len(sess_data.get("errors", []))

                # Extract GitHub issue
                github_issue = sess_data.get("github_issue")

                sessions.append(
                    models.SessionSummary(
                        id=session_id,
                        project_id=sess_data.get("project_id", "unknown"),
                        description=sess_data.get("description", ""),
                        start_time=start_time or datetime.now(),
                        end_time=end_time,
                        duration_seconds=duration,
                        file_changes_count=file_changes_count,
                        decisions_count=decisions_count,
                        errors_count=errors_count,
                        github_issue=github_issue,
                        success=sess_data.get("success"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse session {sess_raw.get('key')}: {e}")
                continue

        # Sort by start_time descending (newest first)
        sessions.sort(key=lambda s: s.start_time, reverse=True)

        # Pagination
        total = len(sessions)
        page = (offset // limit) + 1
        sessions_page = sessions[offset : offset + limit]

        return models.SessionListResponse(
            sessions=sessions_page,
            total=total,
            page=page,
            page_size=limit,
        )

    except Exception as e:
        logger.error(f"Failed to list coding sessions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=models.SessionDetailResponse)
async def get_session_detail(
    session_id: Annotated[str, Path(description="Session ID")],
    user: dict[str, Any] = Depends(get_current_user),
) -> models.SessionDetailResponse:
    """Get coding session detail.

    Returns full session details including file changes, decisions, and errors.

    Args:
        session_id: Session ID
        user: Authenticated user (dependency)

    Returns:
        Complete session details

    Raises:
        HTTPException(404): Session not found

    Example:
        GET /api/v1/coding/sessions/abc123
        Response: {
            "session": {
                "id": "abc123",
                "project_id": "kagura-ai",
                ...
            },
            "file_changes": [
                {
                    "file_path": "src/memory.py",
                    "action": "edit",
                    "diff": "Fix #510",
                    "reason": "Add None check"
                },
                ...
            ],
            "decisions": [...],
            "errors": [...]
        }
    """
    try:
        manager = MemoryManager(user_id="system", agent_name="coding-memory")

        # Search for session
        sessions = manager.persistent.search(
            query=f"%session:{session_id}",
            user_id="system",
            agent_name="coding-memory",
            limit=1,
        )

        if not sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        sess_raw = sessions[0]
        value_str = sess_raw.get("value", "{}")
        sess_data = json.loads(value_str) if isinstance(value_str, str) else value_str

        # Parse session summary
        start_time = sess_data.get("start_time")
        end_time = sess_data.get("end_time")

        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)

        duration = None
        if end_time and start_time:
            duration = int((end_time - start_time).total_seconds())

        session_summary = models.SessionSummary(
            id=session_id,
            project_id=sess_data.get("project_id", "unknown"),
            description=sess_data.get("description", ""),
            start_time=start_time or datetime.now(),
            end_time=end_time,
            duration_seconds=duration,
            file_changes_count=len(sess_data.get("file_changes", [])),
            decisions_count=len(sess_data.get("decisions", [])),
            errors_count=len(sess_data.get("errors", [])),
            github_issue=sess_data.get("github_issue"),
            success=sess_data.get("success"),
        )

        # Parse file changes
        file_changes = [
            models.FileChange(
                file_path=fc.get("file_path", ""),
                action=fc.get("action", "edit"),
                diff=fc.get("diff"),
                reason=fc.get("reason"),
                line_range=fc.get("line_range"),
            )
            for fc in sess_data.get("file_changes", [])
        ]

        # Parse decisions
        decisions = [
            models.Decision(
                decision=d.get("decision", ""),
                rationale=d.get("rationale", ""),
                alternatives=d.get("alternatives", []),
                impact=d.get("impact"),
                tags=d.get("tags", []),
            )
            for d in sess_data.get("decisions", [])
        ]

        # Parse errors
        errors = [
            models.ErrorRecord(
                error_type=e.get("error_type", "Unknown"),
                message=e.get("message", ""),
                file_path=e.get("file_path"),
                line_number=e.get("line_number"),
                solution=e.get("solution"),
            )
            for e in sess_data.get("errors", [])
        ]

        return models.SessionDetailResponse(
            session=session_summary,
            file_changes=file_changes,
            decisions=decisions,
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session detail: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session detail: {str(e)}"
        )
