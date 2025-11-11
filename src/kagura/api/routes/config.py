"""Configuration management API endpoints.

Issue #650 - Web UI for Environment Variable Configuration

Provides Admin-only API for managing .env.cloud configuration:
- GET /api/v1/config - Read all config (sensitive values masked)
- GET /api/v1/config/categories - Get config organized by category
- PUT /api/v1/config/{key} - Update single config value
- POST /api/v1/config/batch - Batch update multiple values
- POST /api/v1/config/validate - Validate config before saving

All endpoints require ADMIN role.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from kagura.api.dependencies import AdminUser
from kagura.config.env_manager import get_env_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ConfigValue(BaseModel):
    """Single configuration value."""

    key: str = Field(..., description="Environment variable name")
    value: str = Field(..., description="Value (masked if sensitive)")
    is_sensitive: bool = Field(..., description="Whether value is sensitive")
    category: Optional[str] = Field(None, description="Config category")


class ConfigResponse(BaseModel):
    """Configuration read response."""

    config: dict[str, str] = Field(..., description="All environment variables")
    categories: dict[str, list[str]] = Field(..., description="Category mapping")
    masked: bool = Field(..., description="Whether sensitive values are masked")


class ConfigUpdateRequest(BaseModel):
    """Single config update request."""

    value: str = Field(..., description="New value")


class BatchConfigUpdateRequest(BaseModel):
    """Batch config update request."""

    updates: dict[str, str] = Field(..., description="Key-value pairs to update")


class ConfigValidateRequest(BaseModel):
    """Config validation request."""

    key: str = Field(..., description="Config key")
    value: str = Field(..., description="Value to validate")


class ConfigValidateResponse(BaseModel):
    """Config validation response."""

    valid: bool = Field(..., description="Whether value is valid")
    error: Optional[str] = Field(None, description="Error message if invalid")


class RestartRequiredResponse(BaseModel):
    """Response indicating restart is required."""

    success: bool = Field(..., description="Update successful")
    restart_required: bool = Field(
        default=True, description="Application restart required"
    )
    message: str = Field(..., description="User-facing message")


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=ConfigResponse)
async def get_config(
    admin_user: AdminUser,
    mask_sensitive: bool = True,
):
    """Get all configuration values.

    Requires ADMIN role. Sensitive values (API keys, secrets) are masked by default.

    Args:
        admin_user: Authenticated admin user (from require_admin dependency)
        mask_sensitive: If True, mask sensitive values (default: True)

    Returns:
        All environment variables with category mapping

    Example:
        GET /api/v1/config
        Response: {
            "config": {
                "OPENAI_API_KEY": "sk-proj-***",
                "LOG_LEVEL": "info",
                ...
            },
            "categories": {
                "llm_api_keys": ["OPENAI_API_KEY", ...],
                ...
            },
            "masked": true
        }
    """
    env_manager = get_env_manager()
    config = env_manager.read_config(mask_sensitive=mask_sensitive)
    categories = env_manager.get_categories()

    return ConfigResponse(config=config, categories=categories, masked=mask_sensitive)


@router.get("/categories", response_model=dict[str, list[str]])
async def get_config_categories(admin_user: AdminUser):
    """Get configuration categories for UI organization.

    Requires ADMIN role.

    Returns:
        Dictionary mapping category names to list of keys

    Example:
        GET /api/v1/config/categories
        Response: {
            "llm_api_keys": ["OPENAI_API_KEY", "GOOGLE_API_KEY"],
            "oauth2": ["GOOGLE_CLIENT_ID", ...],
            ...
        }
    """
    env_manager = get_env_manager()
    return env_manager.get_categories()


@router.put("/{key}", response_model=RestartRequiredResponse)
async def update_config(
    key: str,
    request_body: ConfigUpdateRequest,
    admin_user: AdminUser,
    request: Request,
):
    """Update single configuration value.

    Requires ADMIN role. Changes are written to .env.cloud file.
    Application restart is required to apply changes.

    Args:
        key: Environment variable name
        request_body: New value
        admin_user: Authenticated admin user
        request: FastAPI request (for audit metadata)

    Returns:
        Success response with restart_required flag

    Raises:
        HTTPException(400): Invalid key or value

    Example:
        PUT /api/v1/config/OPENAI_API_KEY
        Body: {"value": "sk-proj-newkey"}
        Response: {
            "success": true,
            "restart_required": true,
            "message": "Configuration updated. Restart required."
        }
    """
    env_manager = get_env_manager()

    # Validate
    is_valid, error = env_manager.validate_config(key, request_body.value)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Audit metadata
    audit_metadata = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }

    # Update
    try:
        env_manager.update_config(
            key=key,
            value=request_body.value,
            user_email=admin_user["email"],
            audit_metadata=audit_metadata,
        )
    except Exception as e:
        logger.error(f"Config update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

    return RestartRequiredResponse(
        success=True,
        restart_required=True,
        message=f"Configuration '{key}' updated successfully. Application restart required to apply changes.",
    )


@router.post("/batch", response_model=RestartRequiredResponse)
async def batch_update_config(
    request_body: BatchConfigUpdateRequest,
    admin_user: AdminUser,
    request: Request,
):
    """Batch update multiple configuration values.

    Requires ADMIN role.

    Args:
        request_body: Dictionary of key-value pairs
        admin_user: Authenticated admin user
        request: FastAPI request

    Returns:
        Success response

    Example:
        POST /api/v1/config/batch
        Body: {
            "updates": {
                "OPENAI_API_KEY": "sk-proj-new",
                "LOG_LEVEL": "debug"
            }
        }
    """
    env_manager = get_env_manager()

    # Validate all values first
    for key, value in request_body.updates.items():
        is_valid, error = env_manager.validate_config(key, value)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"{key}: {error}")

    # Audit metadata
    audit_metadata = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }

    # Apply updates
    try:
        env_manager.batch_update_config(
            updates=request_body.updates,
            user_email=admin_user["email"],
            audit_metadata=audit_metadata,
        )
    except Exception as e:
        logger.error(f"Batch config update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

    return RestartRequiredResponse(
        success=True,
        restart_required=True,
        message=f"{len(request_body.updates)} configuration values updated. Application restart required.",
    )


@router.post("/validate", response_model=ConfigValidateResponse)
async def validate_config(
    request_body: ConfigValidateRequest,
    admin_user: AdminUser,
):
    """Validate configuration value before saving.

    Requires ADMIN role. Allows frontend to validate values before submission.

    Args:
        request_body: Key and value to validate
        admin_user: Authenticated admin user

    Returns:
        Validation result

    Example:
        POST /api/v1/config/validate
        Body: {"key": "OPENAI_API_KEY", "value": "invalid"}
        Response: {
            "valid": false,
            "error": "OpenAI API key must start with 'sk-' or 'sk-proj-'"
        }
    """
    env_manager = get_env_manager()
    is_valid, error = env_manager.validate_config(request_body.key, request_body.value)

    return ConfigValidateResponse(valid=is_valid, error=error)
