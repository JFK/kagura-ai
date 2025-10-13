"""Pytest fixtures for authentication tests"""

import json
from pathlib import Path

import pytest
from google.oauth2.credentials import Credentials


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory for tests

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to temporary .kagura directory
    """
    config_dir = tmp_path / ".kagura"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_credentials() -> Credentials:
    """Create mock Google OAuth2 credentials

    Returns:
        Mock Credentials object
    """
    creds_data = {
        "token": "mock_access_token_12345",
        "refresh_token": "mock_refresh_token_67890",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "mock_client_id.apps.googleusercontent.com",
        "client_secret": "mock_client_secret",
        "scopes": [
            "https://www.googleapis.com/auth/generative-language",
            "openid",
        ],
    }

    return Credentials.from_authorized_user_info(
        creds_data,
        scopes=creds_data["scopes"],
    )


@pytest.fixture
def mock_client_secrets(temp_config_dir: Path) -> Path:
    """Create mock client_secrets.json file

    Args:
        temp_config_dir: Temporary config directory

    Returns:
        Path to mock client_secrets.json
    """
    client_secrets = {
        "installed": {
            "client_id": "mock_client_id.apps.googleusercontent.com",
            "client_secret": "mock_client_secret",
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    secrets_file = temp_config_dir / "client_secrets.json"
    secrets_file.write_text(json.dumps(client_secrets))
    return secrets_file
