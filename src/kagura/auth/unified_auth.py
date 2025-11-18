"""Unified authentication manager for all Kagura interfaces.

Provides a single authentication flow for MCP, API, and CLI by consolidating:
- API Key authentication (Bearer tokens)
- OAuth2 authentication (Google, etc.)
- Session-based authentication (cookies/tokens)
- Anonymous access (development mode)

Priority: API Key > OAuth2 > Session > Anonymous
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Authentication method used for the request."""

    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SESSION = "session"
    ANONYMOUS = "anonymous"


@dataclass
class AuthResult:
    """Result of authentication attempt.

    Attributes:
        user_id: Authenticated user identifier
        method: Authentication method used
        is_authenticated: Whether authentication was successful
        metadata: Additional authentication metadata (e.g., scopes, expiry)
    """

    user_id: str
    method: AuthMethod
    is_authenticated: bool = True
    metadata: dict | None = None

    def __post_init__(self):
        """Set metadata to empty dict if None."""
        if self.metadata is None:
            self.metadata = {}


class UnifiedAuthManager:
    """Single authentication manager for all Kagura interfaces.

    Consolidates API Key, OAuth2, Session, and Anonymous authentication
    into a single, consistent flow with clear priority ordering.

    Priority (highest to lowest):
        1. API Key (Bearer token)
        2. OAuth2 (Google, etc.)
        3. Session (cookie/token)
        4. Anonymous (if allowed)

    Example:
        >>> auth = UnifiedAuthManager()
        >>>
        >>> # Authenticate with API key
        >>> result = await auth.authenticate(
        ...     auth_header="Bearer kagura_abc123...",
        ...     allow_anonymous=False
        ... )
        >>> print(result.user_id)  # "user_123"
        >>> print(result.method)   # AuthMethod.API_KEY
        >>>
        >>> # Authenticate with OAuth2
        >>> result = await auth.authenticate(
        ...     auth_header="Bearer ya29.google_token...",
        ...     allow_anonymous=False
        ... )
        >>> print(result.method)   # AuthMethod.OAUTH2
        >>>
        >>> # Anonymous (development)
        >>> result = await auth.authenticate(allow_anonymous=True)
        >>> print(result.user_id)  # "default_user"
        >>> print(result.method)   # AuthMethod.ANONYMOUS

    Security Notes:
        - API keys are hashed with SHA-256 before storage
        - OAuth2 credentials are encrypted with Fernet (AES-128)
        - Session tokens should be validated against secure storage (Redis)
        - Anonymous access should only be enabled in development

    Args:
        api_key_manager: Optional APIKeyManager instance (default: auto-create)
        oauth2_manager: Optional OAuth2Manager instance (default: None)
        session_store: Optional session storage (Redis, etc.)
    """

    def __init__(
        self,
        api_key_manager: Optional[object] = None,
        oauth2_manager: Optional[object] = None,
        session_store: Optional[object] = None,
    ):
        """Initialize unified authentication manager.

        Args:
            api_key_manager: APIKeyManager instance (default: auto-create)
            oauth2_manager: OAuth2Manager instance (default: None)
            session_store: Session storage backend (default: None)
        """
        self._api_key_manager = api_key_manager
        self.oauth2_manager = oauth2_manager
        self.session_store = session_store

        logger.debug("Initialized UnifiedAuthManager")

    @property
    def api_key_manager(self):
        """Get API key manager (lazy initialization)."""
        if self._api_key_manager is None:
            # Lazy import to avoid circular dependencies
            from kagura.api.auth import get_api_key_manager

            self._api_key_manager = get_api_key_manager()
        return self._api_key_manager

    async def authenticate(
        self,
        auth_header: str | None = None,
        session_token: str | None = None,
        allow_anonymous: bool = False,
    ) -> AuthResult:
        """Authenticate request using available credentials.

        Tries authentication methods in priority order:
        1. API Key (from Authorization: Bearer header)
        2. OAuth2 (from Authorization: Bearer header)
        3. Session (from session_token parameter)
        4. Anonymous (if allow_anonymous=True)

        Args:
            auth_header: Authorization header value (e.g., "Bearer <token>")
            session_token: Session token (cookie or custom header)
            allow_anonymous: Allow anonymous access (default: False)

        Returns:
            AuthResult with user_id and authentication method

        Raises:
            AuthenticationError: If no valid credentials and anonymous not allowed

        Example:
            >>> result = await auth.authenticate(
            ...     auth_header="Bearer kagura_abc123...",
            ...     allow_anonymous=False
            ... )
            >>> print(result.user_id)  # "user_123"
            >>> print(result.method)   # AuthMethod.API_KEY
        """
        # Priority 1: Try API Key authentication
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix

            # Check if it's an API key (kagura_* prefix)
            if token.startswith("kagura_"):
                user_id = await self._verify_api_key(token)
                if user_id:
                    logger.info(f"Authenticated via API key: {user_id}")
                    return AuthResult(
                        user_id=user_id,
                        method=AuthMethod.API_KEY,
                        metadata={"key_prefix": token[:16]},
                    )

            # Priority 2: Try OAuth2 authentication
            user_id = await self._verify_oauth2_token(token)
            if user_id:
                logger.info(f"Authenticated via OAuth2: {user_id}")
                return AuthResult(
                    user_id=user_id,
                    method=AuthMethod.OAUTH2,
                    metadata={"provider": "google"},
                )

        # Priority 3: Try Session authentication
        if session_token:
            user_id = await self._verify_session(session_token)
            if user_id:
                logger.info(f"Authenticated via session: {user_id}")
                return AuthResult(
                    user_id=user_id,
                    method=AuthMethod.SESSION,
                )

        # Priority 4: Anonymous access (if allowed)
        if allow_anonymous:
            logger.debug("Using anonymous authentication (default_user)")
            return AuthResult(
                user_id="default_user",
                method=AuthMethod.ANONYMOUS,
                is_authenticated=False,
            )

        # No valid credentials
        from kagura.auth.exceptions import InvalidCredentialsError

        logger.warning("Authentication failed: No valid credentials provided")
        raise InvalidCredentialsError("No valid credentials provided")

    async def _verify_api_key(self, api_key: str) -> str | None:
        """Verify API key and return user_id.

        Args:
            api_key: Plaintext API key

        Returns:
            user_id if valid, None otherwise
        """
        try:
            user_id = self.api_key_manager.verify_key(api_key)
            if user_id:
                logger.debug(f"API key verified for user: {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            return None

    async def _verify_oauth2_token(self, token: str) -> str | None:
        """Verify OAuth2 token and return user_id.

        Args:
            token: OAuth2 access token

        Returns:
            user_id if valid, None otherwise
        """
        if not self.oauth2_manager:
            return None

        try:
            # Verify token with OAuth2 provider
            # Implementation depends on OAuth2Manager API
            # For now, return None (OAuth2Server not yet implemented)
            logger.debug("OAuth2 verification not yet implemented")
            return None
        except Exception as e:
            logger.error(f"OAuth2 verification failed: {e}")
            return None

    async def _verify_session(self, session_token: str) -> str | None:
        """Verify session token and return user_id.

        Args:
            session_token: Session token (cookie or header)

        Returns:
            user_id if valid, None otherwise
        """
        if not self.session_store:
            return None

        try:
            # Verify session token from storage (Redis, etc.)
            # Implementation depends on session_store API
            # For now, return None
            logger.debug("Session verification not yet implemented")
            return None
        except Exception as e:
            logger.error(f"Session verification failed: {e}")
            return None

    # Delegation methods for API key management

    def create_api_key(
        self,
        name: str,
        user_id: str,
        expires_days: int | None = None,
    ) -> str:
        """Create a new API key.

        Args:
            name: Friendly name for the key
            user_id: User ID that owns this key
            expires_days: Optional expiration in days

        Returns:
            Plaintext API key (only shown once)

        Raises:
            ValueError: If name already exists for user
        """
        return self.api_key_manager.create_key(name, user_id, expires_days)

    def revoke_api_key(self, name: str, user_id: str) -> bool:
        """Revoke an API key.

        Args:
            name: Name of the key to revoke
            user_id: User ID that owns the key

        Returns:
            True if revoked, False if not found
        """
        return self.api_key_manager.revoke_key(name, user_id)

    def list_api_keys(self, user_id: str | None = None) -> list[dict]:
        """List API keys (optionally filtered by user).

        Args:
            user_id: Optional user_id filter

        Returns:
            List of API key metadata dicts
        """
        return self.api_key_manager.list_keys(user_id)


# Global UnifiedAuthManager instance
_unified_auth_manager: UnifiedAuthManager | None = None


def get_unified_auth_manager() -> UnifiedAuthManager:
    """Get or create global UnifiedAuthManager instance.

    Returns:
        UnifiedAuthManager instance
    """
    global _unified_auth_manager

    if _unified_auth_manager is None:
        _unified_auth_manager = UnifiedAuthManager()
        logger.debug("Created global UnifiedAuthManager instance")

    return _unified_auth_manager
