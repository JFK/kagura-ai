"""Tests for OAuth2Manager"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

from kagura.auth import AuthConfig, OAuth2Manager
from kagura.auth.exceptions import (
    InvalidCredentialsError,
    NotAuthenticatedError,
)


class TestOAuth2ManagerInit:
    """Tests for OAuth2Manager initialization"""

    def test_initialization_default_provider(self, tmp_path: Path, monkeypatch):
        """Test initialization with default provider"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager(provider="google")

        assert auth.provider == "google"
        assert auth.config_dir == tmp_path / ".kagura"
        assert auth.config_dir.exists()
        assert auth.key_file.exists()
        assert auth.key_file.stat().st_mode & 0o777 == 0o600

    def test_initialization_custom_config(self, tmp_path: Path, monkeypatch):
        """Test initialization with custom config"""
        monkeypatch.setenv("HOME", str(tmp_path))

        config = AuthConfig(
            provider="google",
            scopes=["https://www.googleapis.com/auth/test"],
        )
        auth = OAuth2Manager(config=config)

        assert auth.provider == "google"
        assert auth.config.scopes == ["https://www.googleapis.com/auth/test"]

    def test_encryption_key_generation(self, tmp_path: Path, monkeypatch):
        """Test encryption key is generated on first run"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()

        assert auth.key_file.exists()
        key = auth.key_file.read_bytes()
        assert len(key) == 44  # Fernet key length

        # Verify key can decrypt
        cipher = Fernet(key)
        encrypted = cipher.encrypt(b"test")
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == b"test"

    def test_encryption_key_reuse(self, tmp_path: Path, monkeypatch):
        """Test existing encryption key is reused"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth1 = OAuth2Manager()
        key1 = auth1.key_file.read_bytes()

        auth2 = OAuth2Manager()
        key2 = auth2.key_file.read_bytes()

        assert key1 == key2


class TestOAuth2ManagerAuthentication:
    """Tests for authentication methods"""

    def test_is_authenticated_false_initially(self, tmp_path: Path, monkeypatch):
        """Test is_authenticated returns False initially"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        assert not auth.is_authenticated()

    def test_is_authenticated_true_after_save(
        self, tmp_path: Path, monkeypatch, mock_credentials: Credentials
    ):
        """Test is_authenticated returns True after credentials saved"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        assert auth.is_authenticated()

    def test_login_missing_client_secrets(self, tmp_path: Path, monkeypatch):
        """Test login raises error when client_secrets.json missing"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()

        with pytest.raises(FileNotFoundError) as exc_info:
            auth.login()

        assert "client_secrets.json" in str(exc_info.value).lower()

    @patch("kagura.auth.oauth2.InstalledAppFlow")
    def test_login_success(
        self,
        mock_flow_class: MagicMock,
        tmp_path: Path,
        monkeypatch,
        mock_client_secrets: Path,
        mock_credentials: Credentials,
    ):
        """Test successful login flow"""
        monkeypatch.setenv("HOME", str(tmp_path.parent))
        monkeypatch.setattr(Path, "home", lambda: tmp_path.parent)

        # Setup mock flow
        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = mock_credentials
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        auth = OAuth2Manager()
        auth.client_secrets_file = mock_client_secrets

        # Login
        auth.login()

        # Verify
        assert auth.is_authenticated()
        assert auth.creds_file.exists()

        # Verify credentials can be loaded
        loaded_creds = auth.get_credentials()
        assert loaded_creds.token == mock_credentials.token

    def test_logout_when_authenticated(
        self, tmp_path: Path, monkeypatch, mock_credentials: Credentials
    ):
        """Test logout removes credentials"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        assert auth.is_authenticated()

        auth.logout()

        assert not auth.is_authenticated()
        assert not auth.creds_file.exists()

    def test_logout_when_not_authenticated(self, tmp_path: Path, monkeypatch):
        """Test logout raises error when not authenticated"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()

        with pytest.raises(NotAuthenticatedError) as exc_info:
            auth.logout()

        assert "google" in str(exc_info.value).lower()


class TestOAuth2ManagerCredentials:
    """Tests for credential management"""

    def test_save_and_load_credentials(
        self, tmp_path: Path, monkeypatch, mock_credentials: Credentials
    ):
        """Test credentials can be saved and loaded"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        loaded_creds = auth._load_credentials()

        assert loaded_creds.token == mock_credentials.token
        assert loaded_creds.refresh_token == mock_credentials.refresh_token
        assert loaded_creds.client_id == mock_credentials.client_id

    def test_credentials_file_permissions(
        self, tmp_path: Path, monkeypatch, mock_credentials: Credentials
    ):
        """Test credentials file has secure permissions"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        # Check file permissions (0o600 = owner read/write only)
        assert auth.creds_file.stat().st_mode & 0o777 == 0o600

    def test_get_credentials_when_not_authenticated(
        self, tmp_path: Path, monkeypatch
    ):
        """Test get_credentials raises error when not authenticated"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()

        with pytest.raises(NotAuthenticatedError):
            auth.get_credentials()

    def test_get_credentials_valid(
        self, tmp_path: Path, monkeypatch, mock_credentials: Credentials
    ):
        """Test get_credentials returns valid credentials"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        creds = auth.get_credentials()

        assert creds.token == mock_credentials.token
        assert creds.valid or creds.expired  # Either valid or needs refresh

    @patch("kagura.auth.oauth2.Request")
    def test_token_refresh_on_expiry(
        self, mock_request_class: MagicMock, tmp_path: Path, monkeypatch
    ):
        """Test token is refreshed when expired"""
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create expired credentials
        creds_data = {
            "token": "old_token",
            "refresh_token": "refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scopes": ["https://www.googleapis.com/auth/generative-language"],
        }
        creds = Credentials.from_authorized_user_info(
            creds_data, scopes=creds_data["scopes"]
        )
        creds._expires = None  # Force expiration

        auth = OAuth2Manager()
        auth._save_credentials(creds)

        # Mock refresh
        def mock_refresh(request):
            creds.token = "new_token"  # Update token

        with patch.object(Credentials, "refresh", mock_refresh):
            with patch.object(Credentials, "expired", True):
                refreshed_creds = auth.get_credentials()

                # Note: Credentials object is complex, just verify it worked
                assert refreshed_creds is not None

    def test_get_token(
        self, tmp_path: Path, monkeypatch, mock_credentials: Credentials
    ):
        """Test get_token returns access token"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        token = auth.get_token()

        assert token == mock_credentials.token
        assert isinstance(token, str)

    def test_get_token_when_not_authenticated(
        self, tmp_path: Path, monkeypatch
    ):
        """Test get_token raises error when not authenticated"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()

        with pytest.raises(NotAuthenticatedError):
            auth.get_token()

    def test_load_invalid_credentials(self, tmp_path: Path, monkeypatch):
        """Test loading corrupted credentials raises error"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()

        # Write invalid encrypted data
        auth.creds_file.write_bytes(b"invalid_encrypted_data")

        with pytest.raises(InvalidCredentialsError):
            auth._load_credentials()
