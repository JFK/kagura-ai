"""Tests for unified authentication manager."""

from __future__ import annotations

import pytest

from kagura.auth.exceptions import InvalidCredentialsError
from kagura.auth.unified_auth import AuthMethod, AuthResult, UnifiedAuthManager


class MockAPIKeyManager:
    """Mock API Key manager for testing."""

    def __init__(self):
        self.keys = {
            "kagura_valid_key_123": "user_123",
            "kagura_admin_key_456": "admin_user",
        }

    def verify_key(self, api_key: str) -> str | None:
        """Mock API key verification."""
        return self.keys.get(api_key)

    def create_key(self, name: str, user_id: str, expires_days: int | None = None) -> str:
        """Mock API key creation."""
        new_key = f"kagura_mock_{name}"
        self.keys[new_key] = user_id
        return new_key

    def revoke_key(self, name: str, user_id: str) -> bool:
        """Mock API key revocation."""
        return True

    def list_keys(self, user_id: str | None = None) -> list[dict]:
        """Mock API key listing."""
        return [
            {
                "name": "test_key",
                "user_id": user_id or "user_123",
                "key_prefix": "kagura_test",
            }
        ]


class MockOAuth2Manager:
    """Mock OAuth2 manager for testing."""

    def __init__(self):
        self.tokens = {
            "ya29.google_token_abc": "google_user_123",
        }

    async def verify_token(self, token: str) -> str | None:
        """Mock OAuth2 token verification."""
        return self.tokens.get(token)


class MockSessionStore:
    """Mock session store for testing."""

    def __init__(self):
        self.sessions = {
            "session_abc123": "session_user_123",
        }

    async def get(self, session_token: str) -> str | None:
        """Mock session lookup."""
        return self.sessions.get(session_token)


@pytest.fixture
def mock_api_key_manager():
    """Create mock API key manager."""
    return MockAPIKeyManager()


@pytest.fixture
def mock_oauth2_manager():
    """Create mock OAuth2 manager."""
    return MockOAuth2Manager()


@pytest.fixture
def mock_session_store():
    """Create mock session store."""
    return MockSessionStore()


@pytest.fixture
def auth_manager(mock_api_key_manager, mock_oauth2_manager, mock_session_store):
    """Create UnifiedAuthManager with mocks."""
    return UnifiedAuthManager(
        api_key_manager=mock_api_key_manager,
        oauth2_manager=mock_oauth2_manager,
        session_store=mock_session_store,
    )


class TestUnifiedAuthManager:
    """Test suite for UnifiedAuthManager."""

    @pytest.mark.asyncio
    async def test_api_key_authentication_success(self, auth_manager):
        """Test successful API key authentication."""
        result = await auth_manager.authenticate(
            auth_header="Bearer kagura_valid_key_123",
            allow_anonymous=False,
        )

        assert result.user_id == "user_123"
        assert result.method == AuthMethod.API_KEY
        assert result.is_authenticated is True
        assert "key_prefix" in result.metadata

    @pytest.mark.asyncio
    async def test_api_key_authentication_invalid(self, auth_manager):
        """Test API key authentication with invalid key."""
        with pytest.raises(InvalidCredentialsError):
            await auth_manager.authenticate(
                auth_header="Bearer kagura_invalid_key",
                allow_anonymous=False,
            )

    @pytest.mark.asyncio
    async def test_anonymous_authentication(self, auth_manager):
        """Test anonymous authentication when allowed."""
        result = await auth_manager.authenticate(allow_anonymous=True)

        assert result.user_id == "default_user"
        assert result.method == AuthMethod.ANONYMOUS
        assert result.is_authenticated is False

    @pytest.mark.asyncio
    async def test_anonymous_authentication_not_allowed(self, auth_manager):
        """Test anonymous authentication when not allowed."""
        with pytest.raises(InvalidCredentialsError):
            await auth_manager.authenticate(allow_anonymous=False)

    @pytest.mark.asyncio
    async def test_authentication_priority_api_key_first(self, auth_manager):
        """Test that API key has highest priority."""
        # Provide both API key and session token
        result = await auth_manager.authenticate(
            auth_header="Bearer kagura_valid_key_123",
            session_token="session_abc123",
            allow_anonymous=True,
        )

        # API key should be used (highest priority)
        assert result.method == AuthMethod.API_KEY
        assert result.user_id == "user_123"

    @pytest.mark.asyncio
    async def test_bearer_token_without_prefix(self, auth_manager):
        """Test authentication with Bearer token (no 'Bearer ' prefix)."""
        # Missing "Bearer " prefix
        with pytest.raises(InvalidCredentialsError):
            await auth_manager.authenticate(
                auth_header="kagura_valid_key_123",
                allow_anonymous=False,
            )

    @pytest.mark.asyncio
    async def test_create_api_key(self, auth_manager):
        """Test API key creation delegation."""
        api_key = auth_manager.create_api_key(
            name="test_key",
            user_id="user_123",
            expires_days=30,
        )

        assert api_key.startswith("kagura_mock_")
        assert "test_key" in api_key

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, auth_manager):
        """Test API key revocation delegation."""
        result = auth_manager.revoke_api_key(
            name="test_key",
            user_id="user_123",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_list_api_keys(self, auth_manager):
        """Test API key listing delegation."""
        keys = auth_manager.list_api_keys(user_id="user_123")

        assert isinstance(keys, list)
        assert len(keys) > 0
        assert keys[0]["user_id"] == "user_123"

    @pytest.mark.asyncio
    async def test_multiple_authentication_methods(self, auth_manager):
        """Test fallback to next authentication method."""
        # Invalid API key, but valid session
        # (This test requires session verification to be implemented)
        result = await auth_manager.authenticate(
            auth_header="Bearer kagura_invalid",
            session_token="session_abc123",
            allow_anonymous=True,
        )

        # Should fall back to anonymous since session verification
        # is not yet implemented
        assert result.method == AuthMethod.ANONYMOUS

    def test_auth_result_dataclass(self):
        """Test AuthResult dataclass."""
        result = AuthResult(
            user_id="test_user",
            method=AuthMethod.API_KEY,
        )

        assert result.user_id == "test_user"
        assert result.method == AuthMethod.API_KEY
        assert result.is_authenticated is True
        assert result.metadata == {}

    def test_auth_result_with_metadata(self):
        """Test AuthResult with metadata."""
        result = AuthResult(
            user_id="test_user",
            method=AuthMethod.OAUTH2,
            metadata={"provider": "google", "scopes": ["email"]},
        )

        assert result.metadata["provider"] == "google"
        assert "scopes" in result.metadata
