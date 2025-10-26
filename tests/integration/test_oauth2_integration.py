"""OAuth2 Integration Tests

These tests require actual Google OAuth2 credentials and are skipped in CI.

Prerequisites:
    1. Google Cloud Project with Generative Language API enabled
    2. OAuth 2.0 Client ID (Desktop application)
    3. client_secrets.json saved to ~/.kagura/

Run with:
    pytest -m integration tests/integration/test_oauth2_integration.py -v
"""

from pathlib import Path

import pytest


def has_oauth_credentials() -> bool:
    """Check if OAuth2 credentials are available for testing"""
    client_secrets = Path.home() / ".kagura" / "client_secrets.json"
    return client_secrets.exists()


@pytest.mark.integration
@pytest.mark.skipif(
    not has_oauth_credentials(),
    reason="OAuth2 credentials not available (client_secrets.json missing)",
)
class TestOAuth2Integration:
    """Integration tests for OAuth2 authentication with real Google API"""

    def test_oauth2_manager_initialization(self):
        """Test OAuth2Manager initializes correctly"""
        from kagura.auth import OAuth2Manager

        auth = OAuth2Manager(provider="google")

        assert auth.provider == "google"
        assert auth.config_dir.exists()
        assert auth.config_dir == Path.home() / ".kagura"

    def test_client_secrets_exists(self):
        """Test client_secrets.json exists and is readable"""
        client_secrets = Path.home() / ".kagura" / "client_secrets.json"

        assert client_secrets.exists(), (
            "client_secrets.json not found. "
            "Please download from Google Cloud Console."
        )

        # Check file is readable
        import json

        with open(client_secrets) as f:
            data = json.load(f)

        # Verify it's an OAuth client secrets file
        assert (
            "installed" in data or "web" in data
        ), "Invalid client_secrets.json format"

    def test_authentication_status(self):
        """Test authentication status check"""
        from kagura.auth import OAuth2Manager

        auth = OAuth2Manager(provider="google")

        # Just check that is_authenticated() returns a boolean
        is_authenticated = auth.is_authenticated()
        assert isinstance(is_authenticated, bool)

        if is_authenticated:
            # If authenticated, we should be able to get credentials
            creds = auth.get_credentials()
            assert creds is not None
            assert hasattr(creds, "token")

    def test_get_token_when_authenticated(self):
        """Test token retrieval when authenticated"""
        from kagura.auth import OAuth2Manager

        auth = OAuth2Manager(provider="google")

        if not auth.is_authenticated():
            pytest.skip("Not authenticated. Run: kagura auth login --provider google")

        # Should not raise
        token = auth.get_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_credentials_encryption(self):
        """Test that credentials are encrypted on disk"""
        from kagura.auth import OAuth2Manager

        auth = OAuth2Manager(provider="google")

        if not auth.is_authenticated():
            pytest.skip("Not authenticated. Run: kagura auth login --provider google")

        # Credentials file should exist
        assert auth.creds_file.exists()

        # File should be encrypted (not readable as JSON)
        import json

        with open(auth.creds_file, "rb") as f:
            content = f.read()

        # Should not be valid JSON (because it's encrypted)
        with pytest.raises((json.JSONDecodeError, UnicodeDecodeError)):
            json.loads(content)

        # But encryption key should exist
        assert auth.key_file.exists()

    def test_file_permissions(self):
        """Test that credential files have correct permissions"""
        from kagura.auth import OAuth2Manager

        auth = OAuth2Manager(provider="google")

        if not auth.is_authenticated():
            pytest.skip("Not authenticated. Run: kagura auth login --provider google")

        import os
        import stat

        # Check credentials file permissions (should be 0600)
        creds_stat = os.stat(auth.creds_file)
        creds_perms = stat.S_IMODE(creds_stat.st_mode)
        assert creds_perms == 0o600, (
            f"Credentials file has wrong permissions: {oct(creds_perms)} "
            f"(expected 0o600)"
        )

        # Check key file permissions (should be 0600)
        key_stat = os.stat(auth.key_file)
        key_perms = stat.S_IMODE(key_stat.st_mode)
        assert key_perms == 0o600, (
            f"Key file has wrong permissions: {oct(key_perms)} " f"(expected 0o600)"
        )


@pytest.mark.integration
@pytest.mark.skipif(
    not has_oauth_credentials(), reason="OAuth2 credentials not available"
)
@pytest.mark.asyncio
class TestLLMOAuth2Integration:
    """Integration tests for LLM calls with OAuth2"""

    async def test_call_llm_with_oauth2(self):
        """Test actual LLM call using OAuth2 authentication"""
        from kagura.auth import OAuth2Manager
        from kagura.core.llm import LLMConfig, call_llm

        # Check authentication
        auth = OAuth2Manager(provider="google")
        if not auth.is_authenticated():
            pytest.skip("Not authenticated. Run: kagura auth login --provider google")

        # Create OAuth2 config
        config = LLMConfig(
            model="gemini/gemini-1.5-flash",
            auth_type="oauth2",
            oauth_provider="google",
            temperature=0.7,
            max_tokens=50,
        )

        # Call LLM
        response = await call_llm("What is 2+2? Answer in one word.", config)

        # Verify response
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        # Response should mention "4" or "four" (case insensitive)
        assert (
            "4" in response or "four" in response.lower()
        ), f"Expected response to mention '4' or 'four', got: {response}"

    async def test_oauth2_token_used_in_llm_call(self, monkeypatch):
        """Test that OAuth2 token is actually used in LLM call"""
        from unittest.mock import MagicMock, patch

        from kagura.auth import OAuth2Manager
        from kagura.core.llm import LLMConfig, call_llm

        # Check authentication
        auth = OAuth2Manager(provider="google")
        if not auth.is_authenticated():
            pytest.skip("Not authenticated. Run: kagura auth login --provider google")

        # Get real token
        real_token = auth.get_token()

        # Mock litellm to capture the API key used
        captured_kwargs = {}

        async def mock_acompletion(*args, **kwargs):
            captured_kwargs.update(kwargs)
            # Return mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Four"
            mock_response.choices[0].message.tool_calls = None
            return mock_response

        with patch("kagura.core.llm.litellm.acompletion", side_effect=mock_acompletion):
            config = LLMConfig(
                model="gemini/gemini-1.5-flash",
                auth_type="oauth2",
                oauth_provider="google",
            )

            await call_llm("What is 2+2?", config)

        # Verify OAuth2 token was used
        assert "api_key" in captured_kwargs
        assert captured_kwargs["api_key"] == real_token


# Note: Login/Logout tests are not included because they require
# interactive browser authentication and would interfere with CI.
# Use scripts/test_oauth2.py for manual testing of login/logout.
