"""Audit log API endpoints.

Issue #653 - PostgreSQL backend for roles and audit logs

Provides Admin-only API for querying security audit logs:
- Configuration changes
- Role assignments
- API key operations
- System restarts

All endpoints require ADMIN role.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from kagura.api.dependencies import AdminUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


# ============================================================================
# Models
# ============================================================================


class AuditLogEntry(BaseModel):
    """Audit log entry."""

    id: int
    user_email: str
    user_id: str
    action: str
    resource: str
    old_value_hash: Optional[str] = None
    new_value_hash: Optional[str] = None
    user_metadata: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: str  # ISO 8601 timestamp


class AuditLogResponse(BaseModel):
    """Audit log query response."""

    logs: list[AuditLogEntry]
    total: int
    limit: int
    offset: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=AuditLogResponse)
async def get_audit_logs(
    admin_user: AdminUser,
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Get audit logs.

    Requires ADMIN role. Returns security audit trail with filters.

    Args:
        admin_user: Authenticated admin user
        action: Filter by action (config_update, role_assign, etc.)
        resource: Filter by resource (OPENAI_API_KEY, user:email, etc.)
        user_email: Filter by user who performed action
        limit: Maximum number of results (default: 100, max: 1000)
        offset: Pagination offset

    Returns:
        List of audit log entries

    Example:
        GET /api/v1/audit?action=config_update&limit=50
        Response: {
            "logs": [
                {
                    "id": 123,
                    "user_email": "admin@example.com",
                    "action": "config_update",
                    "resource": "OPENAI_API_KEY",
                    "old_value_hash": "abc123...",
                    "new_value_hash": "def456...",
                    "created_at": "2025-11-11T10:00:00Z"
                },
                ...
            ],
            "total": 150,
            "limit": 50,
            "offset": 0
        }
    """
    try:
        from kagura.auth.models import AuditLog, get_session

        session = get_session()
        try:
            # Build query with filters
            query = session.query(AuditLog)

            if action:
                query = query.filter(AuditLog.action == action)
            if resource:
                query = query.filter(AuditLog.resource == resource)
            if user_email:
                query = query.filter(AuditLog.user_email == user_email)

            # Get total count before pagination
            total = query.count()

            # Apply pagination and ordering
            logs = (
                query.order_by(AuditLog.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            # Convert to response model
            entries = [
                AuditLogEntry(
                    id=log.id,
                    user_email=log.user_email,
                    user_id=log.user_id,
                    action=log.action,
                    resource=log.resource,
                    old_value_hash=log.old_value_hash,
                    new_value_hash=log.new_value_hash,
                    user_metadata=log.user_metadata,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    created_at=log.created_at.isoformat() if log.created_at else "",
                )
                for log in logs
            ]

            return AuditLogResponse(
                logs=entries, total=total, limit=limit, offset=offset
            )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to query audit logs: {e}")
        # Return empty result on error
        return AuditLogResponse(logs=[], total=0, limit=limit, offset=offset)
