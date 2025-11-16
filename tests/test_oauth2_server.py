"""Tests for OAuth2 Server implementation.

Issue #674 - OAuth2 authentication support for ChatGPT MCP integration

Tests cover:
- OAuth2 client model
- Authorization code grant
- Refresh token grant
- Token validation
- MCP authentication
"""

import hashlib
import secrets
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from kagura.auth.models import Base
from kagura.auth.oauth2_models import (
    OAuth2AuthorizationCode,
    OAuth2Client,
    OAuth2Token,
)


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def oauth_client(db_session: Session):
    """Create test OAuth2 client."""
    client_secret = "test_secret_123"
    client_secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

    client = OAuth2Client(
        client_id="test-client",
        client_secret_hash=client_secret_hash,
        client_name="Test Client",
        redirect_uris=["https://example.com/callback"],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope="mcp:tools mcp:memory",
        token_endpoint_auth_method="client_secret_post",
    )
    db_session.add(client)
    db_session.commit()

    # Attach plaintext secret for tests
    client._test_secret = client_secret
    return client


class TestOAuth2Client:
    """Tests for OAuth2Client model."""

    def test_get_client_id(self, oauth_client: OAuth2Client):
        """Test get_client_id method."""
        assert oauth_client.get_client_id() == "test-client"

    def test_get_default_redirect_uri(self, oauth_client: OAuth2Client):
        """Test get_default_redirect_uri method."""
        assert oauth_client.get_default_redirect_uri() == "https://example.com/callback"

    def test_check_redirect_uri_valid(self, oauth_client: OAuth2Client):
        """Test redirect URI validation (valid)."""
        assert oauth_client.check_redirect_uri("https://example.com/callback") is True

    def test_check_redirect_uri_invalid(self, oauth_client: OAuth2Client):
        """Test redirect URI validation (invalid)."""
        assert oauth_client.check_redirect_uri("https://evil.com/callback") is False

    def test_has_client_secret(self, oauth_client: OAuth2Client):
        """Test has_client_secret method."""
        assert oauth_client.has_client_secret() is True

    def test_check_client_secret_valid(self, oauth_client: OAuth2Client):
        """Test client secret validation (valid)."""
        assert oauth_client.check_client_secret("test_secret_123") is True

    def test_check_client_secret_invalid(self, oauth_client: OAuth2Client):
        """Test client secret validation (invalid)."""
        assert oauth_client.check_client_secret("wrong_secret") is False

    def test_check_response_type_valid(self, oauth_client: OAuth2Client):
        """Test response type validation (valid)."""
        assert oauth_client.check_response_type("code") is True

    def test_check_response_type_invalid(self, oauth_client: OAuth2Client):
        """Test response type validation (invalid)."""
        assert oauth_client.check_response_type("token") is False

    def test_check_grant_type_valid(self, oauth_client: OAuth2Client):
        """Test grant type validation (valid)."""
        assert oauth_client.check_grant_type("authorization_code") is True
        assert oauth_client.check_grant_type("refresh_token") is True

    def test_check_grant_type_invalid(self, oauth_client: OAuth2Client):
        """Test grant type validation (invalid)."""
        assert oauth_client.check_grant_type("implicit") is False

    def test_get_allowed_scope_subset(self, oauth_client: OAuth2Client):
        """Test scope filtering (requested subset)."""
        allowed = oauth_client.get_allowed_scope("mcp:tools")
        assert allowed == "mcp:tools"

    def test_get_allowed_scope_superset(self, oauth_client: OAuth2Client):
        """Test scope filtering (requested superset)."""
        # Request more than allowed → returns intersection
        allowed = oauth_client.get_allowed_scope("mcp:tools mcp:memory mcp:coding")
        assert set(allowed.split()) == {"mcp:tools", "mcp:memory"}


class TestOAuth2AuthorizationCode:
    """Tests for OAuth2AuthorizationCode model."""

    def test_create_authorization_code(self, db_session: Session, oauth_client: OAuth2Client):
        """Test authorization code creation."""
        code = OAuth2AuthorizationCode(
            code=secrets.token_urlsafe(32),
            client_id=oauth_client.client_id,
            user_id="user123",
            redirect_uri="https://example.com/callback",
            scope="mcp:tools",
            auth_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=600),
        )
        db_session.add(code)
        db_session.commit()

        assert code.id is not None
        assert code.client_id == "test-client"
        assert code.user_id == "user123"

    def test_authorization_code_expiration(self, db_session: Session, oauth_client: OAuth2Client):
        """Test authorization code expiration check."""
        # Expired code
        expired_code = OAuth2AuthorizationCode(
            code="expired_code",
            client_id=oauth_client.client_id,
            user_id="user123",
            redirect_uri="https://example.com/callback",
            scope="mcp:tools",
            auth_time=datetime.utcnow() - timedelta(seconds=700),
            expires_at=datetime.utcnow() - timedelta(seconds=100),  # 100s ago
        )
        db_session.add(expired_code)
        db_session.commit()

        assert expired_code.is_expired() is True

        # Valid code
        valid_code = OAuth2AuthorizationCode(
            code="valid_code",
            client_id=oauth_client.client_id,
            user_id="user123",
            redirect_uri="https://example.com/callback",
            scope="mcp:tools",
            auth_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=600),
        )
        db_session.add(valid_code)
        db_session.commit()

        assert valid_code.is_expired() is False

    def test_pkce_support(self, db_session: Session, oauth_client: OAuth2Client):
        """Test PKCE code challenge storage."""
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()

        code = OAuth2AuthorizationCode(
            code=secrets.token_urlsafe(32),
            client_id=oauth_client.client_id,
            user_id="user123",
            redirect_uri="https://example.com/callback",
            scope="mcp:tools",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            auth_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=600),
        )
        db_session.add(code)
        db_session.commit()

        assert code.get_code_challenge() == code_challenge
        assert code.get_code_challenge_method() == "S256"


class TestOAuth2Token:
    """Tests for OAuth2Token model."""

    def test_create_token(self, db_session: Session, oauth_client: OAuth2Client):
        """Test token creation."""
        token = OAuth2Token(
            client_id=oauth_client.client_id,
            user_id="user123",
            token_type="Bearer",
            access_token=secrets.token_urlsafe(64),
            refresh_token=secrets.token_urlsafe(64),
            scope="mcp:tools mcp:memory",
            expires_in=3600,
            revoked=False,
        )
        db_session.add(token)
        db_session.commit()

        assert token.id is not None
        assert token.client_id == "test-client"
        assert token.user_id == "user123"
        assert token.get_expires_in() == 3600

    def test_token_expiration(self, db_session: Session, oauth_client: OAuth2Client):
        """Test token expiration check."""
        # Create expired token (issued 2 hours ago, expires in 1 hour)
        expired_token = OAuth2Token(
            client_id=oauth_client.client_id,
            user_id="user123",
            token_type="Bearer",
            access_token="expired_token",
            scope="mcp:tools",
            expires_in=3600,  # 1 hour
            revoked=False,
            issued_at=datetime.utcnow() - timedelta(hours=2),  # 2 hours ago
        )
        db_session.add(expired_token)
        db_session.commit()

        assert expired_token.is_expired() is True

        # Create valid token (issued now, expires in 1 hour)
        valid_token = OAuth2Token(
            client_id=oauth_client.client_id,
            user_id="user123",
            token_type="Bearer",
            access_token="valid_token",
            scope="mcp:tools",
            expires_in=3600,
            revoked=False,
        )
        db_session.add(valid_token)
        db_session.commit()

        assert valid_token.is_expired() is False

    def test_token_revocation(self, db_session: Session, oauth_client: OAuth2Client):
        """Test token revocation."""
        token = OAuth2Token(
            client_id=oauth_client.client_id,
            user_id="user123",
            token_type="Bearer",
            access_token=secrets.token_urlsafe(64),
            scope="mcp:tools",
            expires_in=3600,
            revoked=False,
        )
        db_session.add(token)
        db_session.commit()

        # Initially not revoked
        assert token.is_revoked() is False

        # Revoke token
        token.access_token_revoked_at = datetime.utcnow()
        db_session.commit()

        assert token.is_revoked() is True

    def test_refresh_token_validation(self, db_session: Session, oauth_client: OAuth2Client):
        """Test refresh token validation."""
        # Token with active refresh token
        token = OAuth2Token(
            client_id=oauth_client.client_id,
            user_id="user123",
            token_type="Bearer",
            access_token=secrets.token_urlsafe(64),
            refresh_token=secrets.token_urlsafe(64),
            scope="mcp:tools",
            expires_in=3600,
            revoked=False,
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_refresh_token_active() is True

        # Revoke refresh token
        token.refresh_token_revoked_at = datetime.utcnow()
        db_session.commit()

        assert token.is_refresh_token_active() is False

        # Token without refresh token
        token_no_refresh = OAuth2Token(
            client_id=oauth_client.client_id,
            user_id="user123",
            token_type="Bearer",
            access_token=secrets.token_urlsafe(64),
            refresh_token=None,  # No refresh token
            scope="mcp:tools",
            expires_in=3600,
            revoked=False,
        )
        db_session.add(token_no_refresh)
        db_session.commit()

        assert token_no_refresh.is_refresh_token_active() is False


@pytest.mark.asyncio
async def test_mcp_oauth2_authentication():
    """Test MCP authentication with OAuth2 token.

    This is a basic integration test for the authentication flow.
    Full integration tests require FastAPI test client.
    """
    from kagura.auth.mcp_auth import _verify_oauth2_token

    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    # Initialize database session
    from kagura.auth.models import init_db
    init_db("sqlite:///:memory:")

    # Create test client and token
    session = SessionLocal()
    client = OAuth2Client(
        client_id="test-mcp-client",
        client_name="Test MCP Client",
        redirect_uris=["https://example.com/callback"],
        scope="mcp:tools",
    )
    session.add(client)
    session.commit()

    token_value = secrets.token_urlsafe(64)
    token = OAuth2Token(
        client_id=client.client_id,
        user_id="test_user_123",
        token_type="Bearer",
        access_token=token_value,
        scope="mcp:tools",
        expires_in=3600,
        revoked=False,
    )
    session.add(token)
    session.commit()
    session.close()

    # Test token verification
    user_id = await _verify_oauth2_token(token_value)
    assert user_id == "test_user_123"

    # Test invalid token
    invalid_user_id = await _verify_oauth2_token("invalid_token")
    assert invalid_user_id is None
