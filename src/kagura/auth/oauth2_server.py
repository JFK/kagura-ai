"""OAuth2 Authorization Server implementation using Authlib.

Issue #674 - OAuth2 authentication support for ChatGPT MCP integration

Provides OAuth2 authorization server functionality with:
- Authorization Code Grant (RFC 6749 Section 4.1)
- Refresh Token Grant (RFC 6749 Section 6)
- PKCE Extension (RFC 7636 - for public clients)

Architecture:
    Built on Authlib's Flask-style integration pattern, adapted for FastAPI.
    Supports both confidential clients (ChatGPT Desktop) and public clients
    (ChatGPT Mobile with PKCE).

Usage:
    >>> from kagura.auth.oauth2_server import create_authorization_server
    >>> from kagura.auth.models import get_session
    >>>
    >>> session = get_session()
    >>> server = create_authorization_server(session)
    >>>
    >>> # In FastAPI routes:
    >>> @app.get("/oauth/authorize")
    >>> async def authorize():
    ...     return server.create_authorization_response(request)

References:
    - https://docs.authlib.org/en/latest/flask/2/authorization-server.html
    - RFC 6749: The OAuth 2.0 Authorization Framework
    - RFC 7636: Proof Key for Code Exchange (PKCE)
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from authlib.oauth2 import OAuth2Request
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7636 import CodeChallenge
from sqlalchemy.orm import Session

from kagura.auth.oauth2_models import (
    OAuth2AuthorizationCode,
    OAuth2Client,
    OAuth2Token,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Query Functions (Required by Authlib)
# ============================================================================


def query_client(session: Session, client_id: str) -> OAuth2Client | None:
    """Query OAuth2 client by client_id.

    Required by Authlib.

    Args:
        session: SQLAlchemy session
        client_id: Client identifier

    Returns:
        OAuth2Client or None
    """
    return session.query(OAuth2Client).filter_by(client_id=client_id).first()


def save_token(token: dict[str, Any], request: OAuth2Request, session: Session) -> None:
    """Save access token to database.

    Required by Authlib.

    Args:
        token: Token data from Authlib
        request: OAuth2 request object
        session: SQLAlchemy session
    """
    # Extract client and user from request
    client_id = request.client.client_id
    user_id = request.user.user_id if hasattr(request, "user") else None

    # For refresh token grant, user comes from existing token
    if not user_id and hasattr(request, "credential"):
        user_id = request.credential.user_id

    if not user_id:
        logger.error("Cannot save token: user_id not found in request")
        raise ValueError("User ID required for token issuance")

    # Create new token record
    oauth_token = OAuth2Token(
        client_id=client_id,
        user_id=user_id,
        token_type=token.get("token_type", "Bearer"),
        access_token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        scope=token.get("scope", ""),
        expires_in=token.get("expires_in", 3600),
        revoked=False,
    )

    session.add(oauth_token)
    session.commit()

    logger.info(
        f"Token saved: client={client_id}, user={user_id}, "
        f"expires_in={token.get('expires_in', 3600)}s"
    )


# ============================================================================
# Authorization Code Grant
# ============================================================================


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    """Authorization Code Grant implementation.

    Implements RFC 6749 Section 4.1 (Authorization Code Grant) with
    PKCE extension support (RFC 7636).

    Flow:
        1. Client requests authorization: GET /oauth/authorize
        2. User consents
        3. Server issues authorization code
        4. Client exchanges code for token: POST /oauth/token
        5. Server validates code and issues access token

    Security:
        - Authorization codes expire after 10 minutes
        - Codes are single-use (deleted after exchange)
        - PKCE supported for public clients
    """

    TOKEN_ENDPOINT_AUTH_METHODS = [
        "client_secret_basic",
        "client_secret_post",
        "none",  # For PKCE public clients
    ]

    def save_authorization_code(
        self, code: str, request: OAuth2Request
    ) -> OAuth2AuthorizationCode:
        """Save authorization code to database.

        Called by Authlib after user authorization.

        Args:
            code: Generated authorization code
            request: OAuth2 request object

        Returns:
            Saved OAuth2AuthorizationCode instance
        """
        # Extract data from request
        client_id = request.client.client_id
        user_id = request.user.user_id if hasattr(request, "user") else None
        redirect_uri = request.redirect_uri
        scope = request.scope

        # PKCE support
        code_challenge = request.data.get("code_challenge")
        code_challenge_method = request.data.get("code_challenge_method")

        if not user_id:
            logger.error("Cannot save authorization code: user_id not found")
            raise ValueError("User ID required for authorization")

        # Create authorization code record (expires in 10 minutes)
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            auth_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=600),  # 10 min
        )

        self.server.db_session.add(auth_code)
        self.server.db_session.commit()

        logger.info(
            f"Authorization code saved: client={client_id}, user={user_id}, "
            f"pkce={bool(code_challenge)}"
        )

        return auth_code

    def query_authorization_code(
        self, code: str, client: OAuth2Client
    ) -> OAuth2AuthorizationCode | None:
        """Query authorization code from database.

        Called by Authlib during token exchange.

        Args:
            code: Authorization code
            client: OAuth2Client instance

        Returns:
            OAuth2AuthorizationCode or None
        """
        auth_code = (
            self.server.db_session.query(OAuth2AuthorizationCode)
            .filter_by(code=code, client_id=client.client_id)
            .first()
        )

        # Check expiration
        if auth_code and auth_code.is_expired():
            logger.warning(
                f"Authorization code expired: code={code[:8]}..., "
                f"client={client.client_id}"
            )
            return None

        return auth_code

    def delete_authorization_code(self, authorization_code: OAuth2AuthorizationCode) -> None:
        """Delete authorization code after use.

        Called by Authlib after successful token exchange.
        Codes are single-use only.

        Args:
            authorization_code: OAuth2AuthorizationCode instance to delete
        """
        self.server.db_session.delete(authorization_code)
        self.server.db_session.commit()

        logger.info(
            f"Authorization code deleted: code={authorization_code.code[:8]}..., "
            f"client={authorization_code.client_id}"
        )

    def authenticate_user(self, authorization_code: OAuth2AuthorizationCode) -> Any:
        """Get user from authorization code.

        Called by Authlib to attach user to token request.

        Args:
            authorization_code: OAuth2AuthorizationCode instance

        Returns:
            User object (must have user_id attribute)
        """
        # Return a minimal user object
        # In a real implementation, you might fetch from users table
        class UserStub:
            def __init__(self, user_id: str):
                self.user_id = user_id

        return UserStub(user_id=authorization_code.user_id)


# ============================================================================
# Refresh Token Grant
# ============================================================================


class RefreshTokenGrant(grants.RefreshTokenGrant):
    """Refresh Token Grant implementation.

    Implements RFC 6749 Section 6 (Refreshing an Access Token).

    Flow:
        1. Client sends refresh token: POST /oauth/token
        2. Server validates refresh token
        3. Server issues new access token (and optionally new refresh token)

    Security:
        - Refresh tokens can be revoked independently
        - Refresh tokens are long-lived (no automatic expiration)
    """

    TOKEN_ENDPOINT_AUTH_METHODS = [
        "client_secret_basic",
        "client_secret_post",
        "none",
    ]

    def authenticate_refresh_token(self, refresh_token: str) -> OAuth2Token | None:
        """Query and validate refresh token.

        Called by Authlib during refresh token grant.

        Args:
            refresh_token: Refresh token value

        Returns:
            OAuth2Token or None
        """
        token = (
            self.server.db_session.query(OAuth2Token)
            .filter_by(refresh_token=refresh_token)
            .first()
        )

        # Validate token
        if token and token.is_refresh_token_active():
            return token

        if token:
            logger.warning(
                f"Refresh token invalid: token={refresh_token[:8]}..., "
                f"revoked={token.refresh_token_revoked_at is not None}"
            )

        return None

    def authenticate_user(self, credential: OAuth2Token) -> Any:
        """Get user from refresh token.

        Called by Authlib to attach user to token request.

        Args:
            credential: OAuth2Token instance

        Returns:
            User object (must have user_id attribute)
        """
        class UserStub:
            def __init__(self, user_id: str):
                self.user_id = user_id

        return UserStub(user_id=credential.user_id)

    def revoke_old_credential(self, credential: OAuth2Token) -> None:
        """Revoke old access token.

        Called by Authlib after issuing new token.
        Optionally revoke old token to enforce single active token per refresh.

        Args:
            credential: Old OAuth2Token instance
        """
        # Mark old access token as revoked
        credential.access_token_revoked_at = datetime.utcnow()
        self.server.db_session.commit()

        logger.info(
            f"Old access token revoked: client={credential.client_id}, "
            f"user={credential.user_id}"
        )


# ============================================================================
# Authorization Server Factory
# ============================================================================


class OAuth2AuthorizationServer:
    """OAuth2 Authorization Server wrapper.

    Encapsulates Authlib's AuthorizationServer with SQLAlchemy session management.
    """

    def __init__(self, session: Session):
        """Initialize OAuth2 server.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.db_session = session

        # Import here to avoid circular dependency
        from authlib.oauth2 import AuthorizationServer

        # Create query_client function
        def query_client_func(client_id: str) -> OAuth2Client | None:
            return query_client(session, client_id)

        # Create save_token function
        def save_token_func(token: dict, request: OAuth2Request) -> None:
            save_token(token, request, session)

        # Create Authlib server
        self.server = AuthorizationServer(
            query_client=query_client_func,
            save_token=save_token_func,
        )

        # Register grants
        self._register_grants()

    def _register_grants(self) -> None:
        """Register grant types with the server."""
        # Authorization Code Grant with PKCE
        self.server.register_grant(
            AuthorizationCodeGrant,
            [CodeChallenge(required=False)],  # PKCE optional
        )

        # Refresh Token Grant
        self.server.register_grant(RefreshTokenGrant)

        logger.info(
            "OAuth2 server initialized: grants=[authorization_code, refresh_token], "
            "pkce=optional"
        )

    def create_authorization_response(self, request: Any, grant_user: Any) -> Any:
        """Create authorization response.

        Args:
            request: OAuth2 request (FastAPI Request or OAuth2Request)
            grant_user: User object granting authorization

        Returns:
            Authorization response (redirect or error)
        """
        return self.server.create_authorization_response(request, grant_user=grant_user)

    def create_token_response(self, request: Any) -> Any:
        """Create token response.

        Args:
            request: OAuth2 request (FastAPI Request or OAuth2Request)

        Returns:
            Token response (JSON with access_token)
        """
        return self.server.create_token_response(request)

    def validate_consent_request(self, request: Any) -> Any:
        """Validate authorization request for consent screen.

        Args:
            request: OAuth2 request

        Returns:
            Grant object for rendering consent screen
        """
        return self.server.validate_consent_request(request)


def create_authorization_server(session: Session) -> OAuth2AuthorizationServer:
    """Factory function to create OAuth2 authorization server.

    Args:
        session: SQLAlchemy session

    Returns:
        Configured OAuth2AuthorizationServer instance

    Example:
        >>> from kagura.auth.models import get_session
        >>> session = get_session()
        >>> server = create_authorization_server(session)
    """
    return OAuth2AuthorizationServer(session)
