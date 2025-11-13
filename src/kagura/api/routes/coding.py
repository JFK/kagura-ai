"""Coding memory endpoints.

Coding memory API routes:
- GET /api/v1/coding/doctor - Coding memory health check (Issue #664)
"""

from typing import Any

from fastapi import APIRouter, Depends

from kagura.api.dependencies import get_current_user
from kagura.api.models_doctor import CodingDoctorResponse, CodingStats
from kagura.core.memory import MemoryManager

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
