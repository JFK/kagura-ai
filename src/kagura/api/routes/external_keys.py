"""External API Keys management endpoints.

Issues #690, #692 - Secure management of external service API keys.

Provides REST API for managing encrypted external API keys (OpenAI, Anthropic,
Google, Brave, Cohere, Voyage, Jina, etc.).

Security:
- Admin-only access (role=admin required)
- Fernet symmetric encryption (API_KEY_SECRET)
- Masked values in responses (never expose plaintext)
- Audit trail (updated_by)

Endpoints:
- GET /external-api-keys - List all keys (masked)
- POST /external-api-keys - Create new key
- PUT /external-api-keys/{key_name} - Update existing key
- DELETE /external-api-keys/{key_name} - Delete key
- POST /external-api-keys/import - Import from .env.cloud
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from kagura.auth.models import User
from kagura.config.external_api_key_manager import ExternalAPIKeyManager
from kagura.utils.encryption import get_encryptor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external-api-keys", tags=["external-api-keys"])


# ============================================================================
# Dependency: Admin User Only
# ============================================================================


async def get_current_admin_user(request: Request) -> dict:
    """Get current user and verify admin role.

    Args:
        request: FastAPI request

    Returns:
        User session data dict

    Raises:
        HTTPException: If not authenticated or not admin
    """
    from kagura.api.dependencies import get_current_user

    user = get_current_user(request)

    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user


AdminUser = Annotated[User, Depends(get_current_admin_user)]


# ============================================================================
# Request/Response Models
# ============================================================================


class ExternalAPIKeyCreate(BaseModel):
    """Request to create external API key."""

    key_name: str = Field(..., min_length=1, max_length=100, description="Key identifier (e.g., OPENAI_API_KEY)")
    provider: str = Field(..., min_length=1, max_length=50, description="Provider (openai, anthropic, etc.)")
    value: str = Field(..., min_length=1, description="Plaintext API key value")


class ExternalAPIKeyUpdate(BaseModel):
    """Request to update external API key."""

    value: str = Field(..., min_length=1, description="New plaintext API key value")


class ExternalAPIKeyResponse(BaseModel):
    """Response with masked API key."""

    id: int
    key_name: str
    provider: str
    masked_value: str
    created_at: str
    updated_at: str
    updated_by: str | None

    class Config:
        from_attributes = True


class ImportResult(BaseModel):
    """Result of .env.cloud import operation."""

    created: list[str] = Field(description="Keys successfully created")
    skipped: list[str] = Field(description="Keys already exist")
    failed: list[tuple[str, str]] = Field(description="Keys that failed with error message")


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=list[ExternalAPIKeyResponse])
async def list_external_api_keys(
    admin: AdminUser,
    provider: str | None = None,
) -> list[ExternalAPIKeyResponse]:
    """List all external API keys (with masked values).

    Args:
        admin: Admin user (dependency)
        provider: Optional provider filter

    Returns:
        List of external API keys with masked values

    Example:
        GET /api/v1/external-api-keys
        GET /api/v1/external-api-keys?provider=openai
    """
    try:
        encryptor = get_encryptor()
        manager = ExternalAPIKeyManager(encryptor)

        keys = manager.list_keys(provider=provider)

        return [ExternalAPIKeyResponse(**key) for key in keys]

    except Exception as e:
        logger.error(f"Failed to list external API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}",
        )


@router.post("", response_model=ExternalAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_external_api_key(
    data: ExternalAPIKeyCreate,
    admin: AdminUser,
) -> ExternalAPIKeyResponse:
    """Create a new external API key.

    Args:
        data: Key creation data
        admin: Admin user (dependency)

    Returns:
        Created key with masked value

    Example:
        POST /api/v1/external-api-keys
        {
            "key_name": "OPENAI_API_KEY",
            "provider": "openai",
            "value": "sk-proj-abc123..."
        }
    """
    try:
        encryptor = get_encryptor()
        manager = ExternalAPIKeyManager(encryptor)

        user_email = admin.get("email", "unknown")

        key = manager.create_key(
            key_name=data.key_name,
            provider=data.provider,
            value=data.value,
            updated_by=user_email,
        )

        # Return masked response
        plaintext = manager.get_decrypted_value(data.key_name)
        masked = encryptor.mask_value(plaintext)

        return ExternalAPIKeyResponse(
            id=key.id,
            key_name=key.key_name,
            provider=key.provider,
            masked_value=masked,
            created_at=key.created_at.isoformat(),
            updated_at=key.updated_at.isoformat(),
            updated_by=key.updated_by,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create external API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        )


@router.put("/{key_name}", response_model=ExternalAPIKeyResponse)
async def update_external_api_key(
    key_name: str,
    data: ExternalAPIKeyUpdate,
    admin: AdminUser,
) -> ExternalAPIKeyResponse:
    """Update an existing external API key.

    Args:
        key_name: Key identifier
        data: Update data with new value
        admin: Admin user (dependency)

    Returns:
        Updated key with masked value

    Example:
        PUT /api/v1/external-api-keys/OPENAI_API_KEY
        {
            "value": "sk-proj-new..."
        }
    """
    try:
        encryptor = get_encryptor()
        manager = ExternalAPIKeyManager(encryptor)

        user_email = admin.get("email", "unknown")

        key = manager.update_key(
            key_name=key_name,
            value=data.value,
            updated_by=user_email,
        )

        # Return masked response
        plaintext = manager.get_decrypted_value(key_name)
        masked = encryptor.mask_value(plaintext)

        return ExternalAPIKeyResponse(
            id=key.id,
            key_name=key.key_name,
            provider=key.provider,
            masked_value=masked,
            created_at=key.created_at.isoformat(),
            updated_at=key.updated_at.isoformat(),
            updated_by=key.updated_by,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to update external API key '{key_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key: {str(e)}",
        )


@router.delete("/{key_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_external_api_key(
    key_name: str,
    admin: AdminUser,
) -> None:
    """Delete an external API key.

    Args:
        key_name: Key identifier
        admin: Admin user (dependency)

    Example:
        DELETE /api/v1/external-api-keys/OLD_API_KEY
    """
    try:
        encryptor = get_encryptor()
        manager = ExternalAPIKeyManager(encryptor)

        manager.delete_key(key_name)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to delete external API key '{key_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}",
        )


@router.post("/import", response_model=ImportResult)
async def import_external_api_keys_from_env(
    admin: AdminUser,
) -> ImportResult:
    """Import API keys from .env.cloud file.

    Reads API keys from .env.cloud and stores encrypted in database.
    Skips keys that already exist. Typically run once on first setup.

    Args:
        admin: Admin user (dependency)

    Returns:
        Import results (created, skipped, failed)

    Example:
        POST /api/v1/external-api-keys/import
        Response: {
            "created": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
            "skipped": ["GOOGLE_API_KEY"],
            "failed": []
        }
    """
    try:
        import os

        encryptor = get_encryptor()
        manager = ExternalAPIKeyManager(encryptor)
        user_email = admin.get("email", "unknown")

        # Read from .env.cloud
        # Known API key environment variables
        key_names = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "BRAVE_SEARCH_API_KEY",
            "COHERE_API_KEY",
            "VOYAGE_API_KEY",
            "JINA_API_KEY",
        ]

        env_values = {}
        for key_name in key_names:
            value = os.getenv(key_name)
            if value:
                env_values[key_name] = value

        if not env_values:
            logger.warning("No API keys found in environment variables")
            return ImportResult(created=[], skipped=[], failed=[])

        # Import to database
        results = manager.import_from_env(env_values, updated_by=user_email)

        return ImportResult(**results)

    except Exception as e:
        logger.error(f"Failed to import external API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}",
        )
