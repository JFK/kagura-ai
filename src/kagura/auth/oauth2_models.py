"""OAuth2 Server models for Authlib integration.

Issue #674 - OAuth2 authentication support for ChatGPT MCP integration

Provides SQLAlchemy ORM models for OAuth2 authorization server:
- OAuth2Client: Registered OAuth2 clients (ChatGPT, etc.)
- OAuth2AuthorizationCode: Short-lived authorization codes
- OAuth2Token: Access tokens and refresh tokens

Architecture:
    These models follow Authlib's Flask integration pattern for SQLAlchemy,
    providing the required interface methods for OAuth2 grant flows.

Example:
    >>> from kagura.auth.oauth2_models import OAuth2Client
    >>> client = OAuth2Client(
    ...     client_id="chatgpt-connector",
    ...     client_name="ChatGPT",
    ...     redirect_uris=["https://chat.openai.com/oauth/callback"],
    ... )
    >>> session.add(client)
    >>> session.commit()

References:
    - https://docs.authlib.org/en/latest/flask/2/authorization-server.html
    - RFC 6749: The OAuth 2.0 Authorization Framework
"""

import secrets
import time
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from kagura.auth.models import Base


class OAuth2Client(Base):
    """OAuth2 Client model for registered applications.

    Stores OAuth2 client registration data for applications that want to
    access Kagura AI MCP server (e.g., ChatGPT Connectors).

    Attributes:
        id: Primary key
        client_id: OAuth2 client identifier (unique, public)
        client_secret_hash: SHA256 hash of client secret (confidential)
        client_name: Human-readable name (e.g., "ChatGPT Connector")
        redirect_uris: Allowed redirect URIs (JSON array)
        grant_types: Allowed grant types (JSON array: authorization_code, refresh_token)
        response_types: Allowed response types (JSON array: code)
        scope: Allowed scopes (space-separated: mcp:tools, mcp:memory, etc.)
        token_endpoint_auth_method: Client authentication method (client_secret_post, etc.)
        created_at: Registration timestamp

    Authlib Integration:
        Implements the required interface for Authlib's AuthorizationCodeGrant:
        - get_client_id(): Returns client_id
        - get_default_redirect_uri(): Returns first redirect_uri
        - check_redirect_uri(redirect_uri): Validates redirect_uri
        - has_client_secret(): Returns True if client_secret_hash exists
        - check_client_secret(secret): Validates client secret
        - check_token_endpoint_auth_method(method): Validates auth method
        - check_response_type(response_type): Validates response_type
        - check_grant_type(grant_type): Validates grant_type
    """

    __tablename__ = "oauth_clients"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Client Identity
    client_id = Column(String(48), nullable=False, unique=True, index=True)
    client_secret_hash = Column(String(64), nullable=True)  # SHA256 hash
    client_name = Column(String(100), nullable=False)

    # OAuth2 Configuration
    redirect_uris = Column(JSON, nullable=False)  # ["https://example.com/callback"]
    grant_types = Column(
        JSON, nullable=False, default=["authorization_code", "refresh_token"]
    )
    response_types = Column(JSON, nullable=False, default=["code"])
    scope = Column(
        String(255), nullable=False, default="mcp:tools mcp:memory mcp:coding"
    )
    token_endpoint_auth_method = Column(
        String(50), nullable=False, default="client_secret_post"
    )

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Owner
    owner_id = Column(String(255), nullable=False, index=True)

    # Relationships
    tokens = relationship("OAuth2Token", back_populates="client", cascade="all, delete")

    def __repr__(self) -> str:
        """String representation."""
        return f"<OAuth2Client(client_id='{self.client_id}', name='{self.client_name}')>"

    # ========================================================================
    # Authlib Interface Methods
    # ========================================================================

    def get_client_id(self) -> str:
        """Get client identifier.

        Required by Authlib.

        Returns:
            Client ID string
        """
        return self.client_id

    def get_default_redirect_uri(self) -> str | None:
        """Get default redirect URI.

        Required by Authlib.

        Returns:
            First redirect URI or None
        """
        if self.redirect_uris and len(self.redirect_uris) > 0:
            return self.redirect_uris[0]
        return None

    def check_redirect_uri(self, redirect_uri: str) -> bool:
        """Validate redirect URI.

        Required by Authlib.

        Args:
            redirect_uri: Redirect URI to validate

        Returns:
            True if redirect_uri is in registered redirect_uris
        """
        return redirect_uri in self.redirect_uris

    def has_client_secret(self) -> bool:
        """Check if client has a secret.

        Required by Authlib.

        Returns:
            True if client_secret_hash exists
        """
        return self.client_secret_hash is not None

    def check_client_secret(self, secret: str) -> bool:
        """Validate client secret.

        Required by Authlib.

        Args:
            secret: Client secret to validate

        Returns:
            True if secret matches stored hash
        """
        if not self.client_secret_hash:
            return False

        import hashlib

        secret_hash = hashlib.sha256(secret.encode()).hexdigest()
        return secrets.compare_digest(secret_hash, self.client_secret_hash)

    def check_token_endpoint_auth_method(self, method: str) -> bool:
        """Validate token endpoint authentication method.

        Required by Authlib.

        Args:
            method: Authentication method (e.g., "client_secret_post")

        Returns:
            True if method matches registered method
        """
        return method == self.token_endpoint_auth_method

    def check_response_type(self, response_type: str) -> bool:
        """Validate response type.

        Required by Authlib.

        Args:
            response_type: Response type (e.g., "code")

        Returns:
            True if response_type is in registered response_types
        """
        return response_type in self.response_types

    def check_grant_type(self, grant_type: str) -> bool:
        """Validate grant type.

        Required by Authlib.

        Args:
            grant_type: Grant type (e.g., "authorization_code")

        Returns:
            True if grant_type is in registered grant_types
        """
        return grant_type in self.grant_types

    def get_allowed_scope(self, scope: str) -> str:
        """Get intersection of requested and allowed scopes.

        Required by Authlib.

        Args:
            scope: Requested scope (space-separated)

        Returns:
            Allowed scope (intersection of requested and registered)
        """
        if not scope:
            return self.scope

        requested = set(scope.split())
        allowed = set(self.scope.split())
        return " ".join(requested & allowed)


class OAuth2AuthorizationCode(Base):
    """OAuth2 Authorization Code model.

    Stores short-lived authorization codes issued during OAuth2 flow.
    Codes are single-use and expire after 10 minutes (RFC 6749 recommendation).

    Attributes:
        id: Primary key
        code: Authorization code (unique, random)
        client_id: Client that requested the code
        user_id: User who authorized (OAuth2 sub)
        redirect_uri: Redirect URI used in authorization request
        scope: Granted scope (space-separated)
        code_challenge: PKCE code challenge (optional, for public clients)
        code_challenge_method: PKCE method ("S256" or "plain")
        auth_time: Authorization timestamp (when user consented)
        expires_at: Expiration timestamp (auth_time + 600s)

    Authlib Integration:
        Implements the required interface for Authlib's AuthorizationCodeGrant:
        - get_redirect_uri(): Returns redirect_uri
        - get_scope(): Returns scope
        - get_auth_time(): Returns auth_time
        - get_code_challenge(): Returns code_challenge
        - get_code_challenge_method(): Returns code_challenge_method
        - is_expired(): Checks if code is expired
    """

    __tablename__ = "oauth_authorization_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Authorization Code Data
    code = Column(String(120), nullable=False, unique=True, index=True)
    client_id = Column(String(48), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)

    # OAuth2 Flow Data
    redirect_uri = Column(String(512), nullable=False)
    scope = Column(String(255), nullable=True)

    # PKCE Support (RFC 7636)
    code_challenge = Column(String(128), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)

    # Timestamps
    auth_time = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False, index=True)

    # Indexes
    __table_args__ = (Index("idx_client_user", "client_id", "user_id"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<OAuth2AuthorizationCode(code='{self.code[:8]}...', client='{self.client_id}')>"

    # ========================================================================
    # Authlib Interface Methods
    # ========================================================================

    def get_redirect_uri(self) -> str:
        """Get redirect URI.

        Required by Authlib.

        Returns:
            Redirect URI string
        """
        return self.redirect_uri

    def get_scope(self) -> str | None:
        """Get granted scope.

        Required by Authlib.

        Returns:
            Scope string or None
        """
        return self.scope

    def get_auth_time(self) -> int:
        """Get authorization timestamp.

        Required by Authlib.

        Returns:
            Unix timestamp (seconds since epoch)
        """
        return int(self.auth_time.timestamp())

    def get_code_challenge(self) -> str | None:
        """Get PKCE code challenge.

        Required by Authlib (PKCE extension).

        Returns:
            Code challenge string or None
        """
        return self.code_challenge

    def get_code_challenge_method(self) -> str | None:
        """Get PKCE code challenge method.

        Required by Authlib (PKCE extension).

        Returns:
            Method ("S256" or "plain") or None
        """
        return self.code_challenge_method

    def is_expired(self) -> bool:
        """Check if authorization code is expired.

        Required by Authlib.

        Returns:
            True if code is expired (current time > expires_at)
        """
        return datetime.utcnow() > self.expires_at


class OAuth2Token(Base):
    """OAuth2 Access Token model.

    Stores access tokens and refresh tokens issued to clients.

    Attributes:
        id: Primary key
        client_id: Client that owns the token
        user_id: User who authorized (OAuth2 sub)
        token_type: Token type (always "Bearer")
        access_token: Access token value (unique, random)
        refresh_token: Refresh token value (optional, unique, random)
        scope: Granted scope (space-separated)
        revoked: Revocation status (False = active)
        issued_at: Token issuance timestamp
        access_token_revoked_at: Access token revocation timestamp (NULL = active)
        refresh_token_revoked_at: Refresh token revocation timestamp (NULL = active)
        expires_in: Access token lifetime in seconds (default: 3600)

    Authlib Integration:
        Implements the required interface for Authlib's AuthorizationServer:
        - get_client_id(): Returns client_id
        - get_scope(): Returns scope
        - get_expires_in(): Returns expires_in
        - is_expired(): Checks if access token is expired
        - is_revoked(): Checks if access token is revoked
        - is_refresh_token_active(): Checks if refresh token is valid
    """

    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Token Owner
    client_id = Column(
        String(48), ForeignKey("oauth_clients.client_id"), nullable=False, index=True
    )
    user_id = Column(String(255), nullable=False, index=True)

    # Token Data
    token_type = Column(String(20), nullable=False, default="Bearer")
    access_token = Column(String(255), nullable=False, unique=True, index=True)
    refresh_token = Column(String(255), nullable=True, unique=True, index=True)
    scope = Column(String(255), nullable=True)

    # Status
    revoked = Column(Boolean, nullable=False, default=False, index=True)

    # Timestamps
    issued_at = Column(DateTime, nullable=False, server_default=func.now())
    access_token_revoked_at = Column(DateTime, nullable=True)
    refresh_token_revoked_at = Column(DateTime, nullable=True)

    # Expiration
    expires_in = Column(Integer, nullable=False, default=3600)  # 1 hour

    # Relationships
    client = relationship("OAuth2Client", back_populates="tokens")

    # Indexes
    __table_args__ = (Index("idx_client_user", "client_id", "user_id"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<OAuth2Token(access_token='{self.access_token[:8]}...', client='{self.client_id}')>"

    # ========================================================================
    # Authlib Interface Methods
    # ========================================================================

    def get_client_id(self) -> str:
        """Get client identifier.

        Required by Authlib.

        Returns:
            Client ID string
        """
        return self.client_id

    def get_scope(self) -> str | None:
        """Get granted scope.

        Required by Authlib.

        Returns:
            Scope string or None
        """
        return self.scope

    def get_expires_in(self) -> int:
        """Get access token lifetime.

        Required by Authlib.

        Returns:
            Lifetime in seconds
        """
        return self.expires_in

    def get_expires_at(self) -> int:
        """Get access token expiration timestamp.

        Required by Authlib.

        Returns:
            Unix timestamp (seconds since epoch)
        """
        return int(self.issued_at.timestamp()) + self.expires_in

    def is_expired(self) -> bool:
        """Check if access token is expired.

        Required by Authlib.

        Returns:
            True if token is expired (current time > issued_at + expires_in)
        """
        return time.time() > self.get_expires_at()

    def is_revoked(self) -> bool:
        """Check if access token is revoked.

        Required by Authlib.

        Returns:
            True if access_token_revoked_at is set or revoked flag is True
        """
        return self.revoked or self.access_token_revoked_at is not None

    def is_refresh_token_active(self) -> bool:
        """Check if refresh token is valid.

        Required by Authlib (for refresh token grant).

        Returns:
            True if refresh token exists and is not revoked
        """
        if not self.refresh_token:
            return False
        if self.refresh_token_revoked_at is not None:
            return False
        return True
