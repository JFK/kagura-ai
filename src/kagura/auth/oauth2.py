"""OAuth2 authentication manager for Google services"""

import json
import logging
from pathlib import Path

from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from kagura.auth.config import AuthConfig
from kagura.auth.exceptions import (
    InvalidCredentialsError,
    NotAuthenticatedError,
    TokenRefreshError,
)

logger = logging.getLogger(__name__)


class OAuth2Manager:
    """OAuth2 authentication manager for Google services

    Handles OAuth2 authentication flow, token management, and secure credential storage.

    Args:
        provider: OAuth2 provider name (default: "google")
        config: Optional AuthConfig instance

    Example:
        >>> auth = OAuth2Manager(provider="google")
        >>> auth.login()  # Opens browser for authentication
        >>> creds = auth.get_credentials()  # Returns valid credentials
        >>> token = auth.get_token()  # Returns access token

    Security:
        - Credentials are encrypted using Fernet (AES-128)
        - Encryption key stored separately with 0o600 permissions
        - Credentials file has 0o600 permissions
        - Automatic token refresh when expired
    """

    SCOPES = {
        "google": [
            "https://www.googleapis.com/auth/generative-language",
            "openid",
        ]
    }

    def __init__(self, provider: str = "google", config: AuthConfig | None = None):
        """Initialize OAuth2 manager

        Args:
            provider: OAuth2 provider name
            config: Optional authentication configuration
        """
        self.provider = provider
        self.config = config or AuthConfig(provider=provider)

        # Setup configuration directory
        self.config_dir = Path.home() / ".kagura"
        self.config_dir.mkdir(exist_ok=True)

        # File paths
        self.creds_file = self.config_dir / "credentials.json.enc"
        self.key_file = self.config_dir / ".key"
        self.client_secrets_file = (
            self.config.client_secrets_path or self.config_dir / "client_secrets.json"
        )

        # Setup encryption
        self._setup_encryption()

        logger.debug(
            f"Initialized OAuth2Manager for {provider} "
            f"(config_dir: {self.config_dir})"
        )

    def _setup_encryption(self) -> None:
        """Setup encryption key for credential storage"""
        if not self.key_file.exists():
            logger.info("Generating new encryption key")
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)
            logger.debug(f"Encryption key saved to {self.key_file}")

        self.cipher = Fernet(self.key_file.read_bytes())

    def login(self) -> None:
        """Launch browser for OAuth2 authentication

        Raises:
            FileNotFoundError: If client_secrets.json not found
            InvalidCredentialsError: If authentication fails
        """
        if not self.client_secrets_file.exists():
            raise FileNotFoundError(
                f"Client secrets file not found: {self.client_secrets_file}\n\n"
                "Please download client_secrets.json from Google Cloud Console:\n"
                "1. Go to https://console.cloud.google.com/apis/credentials\n"
                "2. Create OAuth 2.0 Client ID (Desktop application)\n"
                "3. Download JSON and save as: {self.client_secrets_file}"
            )

        try:
            logger.info(f"Starting OAuth2 flow for {self.provider}")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.client_secrets_file),
                self.config.scopes or self.SCOPES[self.provider],
            )

            # Run local server for OAuth2 callback
            creds_result = flow.run_local_server(port=0)

            # Ensure we have OAuth2 Credentials (not ExternalAccountCredentials)
            if not isinstance(creds_result, Credentials):
                raise InvalidCredentialsError(
                    "Received unexpected credential type from OAuth2 flow"
                )

            # Save encrypted credentials
            self._save_credentials(creds_result)

            logger.info("Authentication successful")
            print("✓ Authentication successful!")
            print(f"✓ Credentials saved to: {self.creds_file}")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise InvalidCredentialsError(f"Authentication failed: {e}") from e

    def logout(self) -> None:
        """Remove stored credentials

        Raises:
            NotAuthenticatedError: If not authenticated
        """
        if not self.is_authenticated():
            raise NotAuthenticatedError(self.provider)

        logger.info(f"Logging out from {self.provider}")
        self.creds_file.unlink()
        print(f"✓ Logged out from {self.provider}")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated

        Returns:
            True if valid credentials exist
        """
        return self.creds_file.exists()

    def get_credentials(self) -> Credentials:
        """Get valid credentials with automatic refresh

        Returns:
            Valid Google OAuth2 credentials

        Raises:
            NotAuthenticatedError: If not authenticated
            TokenRefreshError: If token refresh fails
        """
        if not self.is_authenticated():
            raise NotAuthenticatedError(self.provider)

        # Load credentials
        creds = self._load_credentials()

        # Refresh if expired
        if hasattr(creds, "expired") and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired token")
                creds.refresh(Request())
                self._save_credentials(creds)
                logger.debug("Token refreshed successfully")
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                raise TokenRefreshError(self.provider, reason=str(e)) from e

        return creds

    def get_token(self) -> str:
        """Get access token for API calls

        Returns:
            Access token string

        Raises:
            NotAuthenticatedError: If not authenticated
            TokenRefreshError: If token refresh fails
        """
        creds = self.get_credentials()
        if not creds.token:
            raise InvalidCredentialsError("No access token available")
        return creds.token

    def _save_credentials(self, creds: Credentials) -> None:
        """Encrypt and save credentials

        Args:
            creds: Google OAuth2 credentials to save
        """
        # Prepare credentials data for encryption
        creds_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }

        # Save expiry as ISO format string with timezone
        if creds.expiry:
            # Ensure expiry has timezone info before saving
            from datetime import timezone

            expiry_to_save = creds.expiry
            if expiry_to_save.tzinfo is None:
                # If naive, assume UTC
                expiry_to_save = expiry_to_save.replace(tzinfo=timezone.utc)
            creds_data["expiry"] = expiry_to_save.isoformat()
        else:
            creds_data["expiry"] = None

        # Encrypt credentials
        encrypted = self.cipher.encrypt(json.dumps(creds_data).encode())

        # Save with secure permissions
        self.creds_file.write_bytes(encrypted)
        self.creds_file.chmod(0o600)

        logger.debug(f"Credentials saved to {self.creds_file}")

    def _load_credentials(self) -> Credentials:
        """Decrypt and load credentials

        Returns:
            Google OAuth2 credentials

        Raises:
            InvalidCredentialsError: If decryption fails
        """
        try:
            # Decrypt credentials
            encrypted = self.creds_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            creds_data = json.loads(decrypted)

            # Extract expiry separately (not part of from_authorized_user_info)
            expiry_str = creds_data.pop("expiry", None)

            # Reconstruct Credentials object
            creds = Credentials.from_authorized_user_info(
                creds_data, self.config.scopes or self.SCOPES[self.provider]
            )

            # Restore expiry if it exists
            if expiry_str:
                from datetime import datetime, timezone

                # Parse ISO format datetime (preserves timezone from string)
                expiry_dt = datetime.fromisoformat(expiry_str)
                # IMPORTANT: Google auth library's _helpers.utcnow() is timezone-NAIVE
                # We must store expiry as naive UTC datetime to match
                if expiry_dt.tzinfo is not None:
                    # Convert to UTC and make naive
                    expiry_dt = expiry_dt.astimezone(timezone.utc).replace(tzinfo=None)
                # Now expiry_dt is naive UTC datetime, matching Google's expectations
                creds.expiry = expiry_dt

            return creds

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            raise InvalidCredentialsError(f"Failed to decrypt credentials: {e}") from e
