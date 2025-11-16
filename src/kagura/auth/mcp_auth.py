"""Authentication helpers for MCP Transport.

Issue #674 - OAuth2 authentication support for ChatGPT MCP integration

Provides unified authentication for MCP over HTTP/SSE:
- OAuth2 Bearer tokens (from ChatGPT, etc.)
- API Key Bearer tokens (from Claude Code, etc.)
- Fallback to default_user for local development

Architecture:
    This module decouples authentication logic from transport layer,
    making it easier to test and maintain.

Usage:
    >>> from kagura.auth.mcp_auth import authenticate_mcp_request
    >>>
    >>> user_id = await authenticate_mcp_request(
    ...     authorization_header="Bearer oauth_abc123..."
    ... )
    >>> # Returns user_id or raises HTTPException
"""

import logging

from fastapi import HTTPException, status

from kagura.auth.api_key_manager import get_api_key_manager_sql
from kagura.auth.models import get_session
from kagura.auth.oauth2_models import OAuth2Token

logger = logging.getLogger(__name__)


async def authenticate_mcp_request(
    authorization_header: str | bytes | None,
    allow_anonymous: bool = True,
) -> str:
    """Authenticate MCP request using Bearer token.

    Supports both OAuth2 tokens and API keys.

    Authentication Priority:
        1. OAuth2 Bearer token (from oauth_tokens table)
        2. API Key Bearer token (from api_keys table)
        3. default_user (if allow_anonymous=True)

    Args:
        authorization_header: Authorization header value (e.g., "Bearer xyz...")
        allow_anonymous: Allow anonymous access with default_user (default: True)

    Returns:
        user_id: Authenticated user ID

    Raises:
        HTTPException: If authentication fails (401 Unauthorized)

    Example:
        >>> user_id = await authenticate_mcp_request("Bearer oauth_abc123...")
        >>> # Returns: "user_12345"
    """
    # No auth header → anonymous (if allowed)
    if not authorization_header:
        if allow_anonymous:
            logger.info("No authorization header, using default_user")
            return "default_user"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Parse Authorization header
    if isinstance(authorization_header, bytes):
        auth_str = authorization_header.decode("utf-8")
    else:
        auth_str = authorization_header

    if not auth_str.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer {token}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_str[7:]  # Remove "Bearer " prefix
    logger.debug(f"Authenticating token: {token[:20]}...")

    # Try OAuth2 token first (priority for ChatGPT integration)
    user_id = await _verify_oauth2_token(token)
    if user_id:
        logger.info(f"Authenticated via OAuth2 token: user={user_id}")
        return user_id

    # Fallback to API Key
    user_id = _verify_api_key(token)
    if user_id:
        logger.info(f"Authenticated via API Key: user={user_id}")
        return user_id

    # Authentication failed
    logger.warning(f"Authentication failed: invalid token (prefix: {token[:20]}...)")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired Bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _verify_oauth2_token(token: str) -> str | None:
    """Verify OAuth2 access token.

    Args:
        token: Access token value

    Returns:
        user_id if token is valid, None otherwise
    """
    db_session = get_session()
    try:
        # Query token from database
        oauth_token = (
            db_session.query(OAuth2Token)
            .filter_by(access_token=token)
            .first()
        )

        if not oauth_token:
            logger.debug("OAuth2 token not found in database")
            return None

        # Check if token is revoked
        if oauth_token.is_revoked():
            logger.warning(f"OAuth2 token revoked: user={oauth_token.user_id}")
            return None

        # Check if token is expired
        if oauth_token.is_expired():
            logger.warning(f"OAuth2 token expired: user={oauth_token.user_id}")
            return None

        # Valid token → return user_id
        logger.debug(
            f"OAuth2 token validated: user={oauth_token.user_id}, "
            f"client={oauth_token.client_id}"
        )
        return oauth_token.user_id

    except Exception as e:
        logger.error(f"OAuth2 token verification error: {e}")
        return None
    finally:
        db_session.close()


def _verify_api_key(api_key: str) -> str | None:
    """Verify API key.

    Args:
        api_key: API key value

    Returns:
        user_id if key is valid, None otherwise
    """
    try:
        manager = get_api_key_manager_sql()
        user_id = manager.verify_key(api_key)

        if user_id:
            logger.debug(f"API key validated: user={user_id}")
            return user_id
        else:
            logger.debug("API key not found or invalid")
            return None

    except Exception as e:
        logger.error(f"API key verification error: {e}")
        return None
