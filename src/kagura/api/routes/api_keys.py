"""API Key management routes.

Provides CRUD operations for API keys with role-based access control.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from kagura.api.dependencies import AdminUser
from kagura.auth.api_key_manager import APIKeyManagerSQL, get_api_key_manager_sql
from kagura.core.memory.api_key_stats import (
    APIKeyStatsTracker,
    get_stats_tracker,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config/api-keys", tags=["API Keys"])


# ============================================================================
# Pydantic Models
# ============================================================================


class APIKeyCreate(BaseModel):
    """Request model for creating an API key."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Friendly name for the API key"
    )
    expires_days: Optional[int] = Field(
        None,
        ge=1,
        le=3650,
        description="Expiration in days (30, 90, 365, or None for no expiration)",
    )


class DailyStats(BaseModel):
    """Daily usage statistics."""

    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    count: int = Field(..., ge=0, description="Number of requests on this date")


class APIKeyStats(BaseModel):
    """API key usage statistics."""

    total_requests: int = Field(..., ge=0, description="Total requests in period")
    daily_stats: list[DailyStats] = Field(..., description="Daily breakdown")
    period_start: str = Field(..., description="Start date of statistics period")
    period_end: str = Field(..., description="End date of statistics period")


class APIKeyResponse(BaseModel):
    """Response model for API key metadata."""

    id: int = Field(..., description="Database ID")
    key_prefix: str = Field(..., description="First 16 characters of key (for display)")
    name: str = Field(..., description="Friendly name")
    user_id: str = Field(..., description="Owner user ID")
    created_at: str = Field(..., description="Creation timestamp")
    last_used_at: Optional[str] = Field(None, description="Last usage timestamp")
    revoked_at: Optional[str] = Field(None, description="Revocation timestamp")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    status: Literal["active", "revoked", "expired"] = Field(
        ..., description="Current status"
    )


class APIKeyCreateResponse(APIKeyResponse):
    """Response model for API key creation (includes plaintext key)."""

    api_key: str = Field(
        ...,
        description="Plaintext API key (ONLY shown once - must be saved by client)",
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _determine_status(
    revoked_at: Optional[str], expires_at: Optional[str]
) -> Literal["active", "revoked", "expired"]:
    """Determine API key status.

    Args:
        revoked_at: Revocation timestamp (ISO format)
        expires_at: Expiration timestamp (ISO format)

    Returns:
        Status string: "active", "revoked", or "expired"
    """
    if revoked_at:
        return "revoked"

    if expires_at:
        expires_dt = datetime.fromisoformat(expires_at)
        if datetime.now() > expires_dt:
            return "expired"

    return "active"


def _format_key_response(key_data: dict[str, Any]) -> APIKeyResponse:
    """Format database row into APIKeyResponse.

    Args:
        key_data: Database row as dictionary

    Returns:
        Formatted APIKeyResponse model
    """
    status = _determine_status(key_data["revoked_at"], key_data["expires_at"])

    return APIKeyResponse(
        id=key_data["id"],
        key_prefix=key_data["key_prefix"],
        name=key_data["name"],
        user_id=key_data["user_id"],
        created_at=key_data["created_at"],
        last_used_at=key_data.get("last_used_at"),
        revoked_at=key_data.get("revoked_at"),
        expires_at=key_data.get("expires_at"),
        status=status,
    )


# ============================================================================
# Routes
# ============================================================================


@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(
    user: AdminUser,
    manager: APIKeyManagerSQL = Depends(get_api_key_manager_sql),
) -> list[APIKeyResponse]:
    """List all API keys (Admin only).

    Args:
        user: Authenticated admin user
        manager: API Key manager instance

    Returns:
        List of API key metadata

    Raises:
        HTTPException: 403 if not admin
    """
    try:
        keys = manager.list_keys(user_id=None)  # List all keys for admins
        return [_format_key_response(key) for key in keys]
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys",
        ) from e


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    user: AdminUser,
    manager: APIKeyManagerSQL = Depends(get_api_key_manager_sql),
) -> APIKeyCreateResponse:
    """Create a new API key (Admin only).

    Args:
        data: API key creation request
        user: Authenticated admin user
        manager: API Key manager instance

    Returns:
        API key metadata with plaintext key (ONLY shown once)

    Raises:
        HTTPException: 400 if name already exists, 403 if not admin
    """
    try:
        # Create key (use 'sub' from OAuth2 session as user_id)
        user_id = user.get("user_id") or user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in session",
            )

        api_key = manager.create_key(
            name=data.name, user_id=user_id, expires_days=data.expires_days
        )

        # Retrieve metadata
        keys = manager.list_keys(user_id=user_id)
        created_key = next((k for k in keys if k["name"] == data.name), None)

        if not created_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created key",
            )

        # Format response with plaintext key
        response_data = _format_key_response(created_key)

        return APIKeyCreateResponse(**response_data.model_dump(), api_key=api_key)

    except ValueError as e:
        # Name already exists
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        ) from e


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    user: AdminUser,
    manager: APIKeyManagerSQL = Depends(get_api_key_manager_sql),
    stats_tracker: APIKeyStatsTracker = Depends(get_stats_tracker),
) -> None:
    """Permanently delete an API key (Admin only).

    WARNING: This is a hard delete that removes the key from the database.
    For soft delete that preserves audit history, use POST /{key_id}/revoke instead.

    Args:
        key_id: Database ID of the key to delete
        user: Authenticated admin user
        manager: API Key manager instance
        stats_tracker: Stats tracker instance

    Raises:
        HTTPException: 404 if key not found, 403 if not admin
    """
    try:
        # Retrieve key to get name
        keys = manager.list_keys(user_id=None)
        target_key = next((k for k in keys if k["id"] == key_id), None)

        if not target_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        # Hard delete key
        success = manager.delete_key(name=target_key["name"], user_id=target_key["user_id"])

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )

        # Delete statistics as well (hard delete removes all traces)
        try:
            key_hash = target_key["key_hash"]
            stats_tracker.delete_stats(key_hash)
        except Exception as e:
            logger.warning(f"Failed to delete API key stats: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key",
        ) from e


@router.post("/{key_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    user: AdminUser,
    manager: APIKeyManagerSQL = Depends(get_api_key_manager_sql),
) -> None:
    """Revoke an API key (Admin only).

    Soft delete - marks the key as revoked but keeps it in database for audit trail.
    The key will no longer be usable but statistics and history are preserved.

    Args:
        key_id: Database ID of the key to revoke
        user: Authenticated admin user
        manager: API Key manager instance

    Raises:
        HTTPException: 404 if key not found, 403 if not admin
    """
    try:
        # Retrieve key to get name
        keys = manager.list_keys(user_id=None)
        target_key = next((k for k in keys if k["id"] == key_id), None)

        if not target_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        # Revoke key (soft delete)
        success = manager.revoke_key(name=target_key["name"], user_id=target_key["user_id"])

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or already revoked",
            )

        # Keep statistics for audit purposes (soft delete)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key",
        ) from e


@router.get("/{key_id}/stats", response_model=APIKeyStats)
async def get_api_key_stats(
    key_id: int,
    user: AdminUser,
    manager: APIKeyManagerSQL = Depends(get_api_key_manager_sql),
    stats_tracker: APIKeyStatsTracker = Depends(get_stats_tracker),
    days: int = 30,
) -> APIKeyStats:
    """Get usage statistics for an API key (Admin only).

    Args:
        key_id: Database ID of the key
        days: Number of days to retrieve (1-90, default: 30)
        user: Authenticated admin user
        manager: API Key manager instance
        stats_tracker: Stats tracker instance

    Returns:
        Usage statistics

    Raises:
        HTTPException: 404 if key not found, 400 if invalid days, 403 if not admin
    """
    if days < 1 or days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days parameter must be between 1 and 90",
        )

    try:
        # Retrieve key
        keys = manager.list_keys(user_id=None)
        target_key = next((k for k in keys if k["id"] == key_id), None)

        if not target_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        # Get key_hash from database (now available with SQLAlchemy)
        key_hash = target_key["key_hash"]

        # Check if stats tracker is healthy (Redis available)
        try:
            if not stats_tracker.health_check():
                logger.warning("Redis not available, returning empty stats")
                # Return empty stats with proper structure
                from datetime import date, timedelta
                end_date = date.today()
                start_date = end_date - timedelta(days=days - 1)

                return APIKeyStats(
                    total_requests=0,
                    daily_stats=[],
                    period_start=start_date.isoformat(),
                    period_end=end_date.isoformat(),
                )
        except Exception as e:
            logger.warning(f"Health check failed: {e}, proceeding with stats retrieval")

        # Retrieve statistics from Redis
        stats_data = stats_tracker.get_stats(key_hash, days=days)

        # Format daily stats
        daily_stats = [
            DailyStats(date=day["date"], count=day["count"])
            for day in stats_data["daily_stats"]
        ]

        return APIKeyStats(
            total_requests=stats_data["total_requests"],
            daily_stats=daily_stats,
            period_start=stats_data["period_start"],
            period_end=stats_data["period_end"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve API key stats for key_id={key_id}: {e}")
        # Return empty stats on error instead of 500 error
        # This allows the UI to show "No data available" instead of error message
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        return APIKeyStats(
            total_requests=0,
            daily_stats=[],
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
        )
