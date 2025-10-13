"""Tests for auth CLI commands"""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from google.oauth2.credentials import Credentials

from kagura.auth import OAuth2Manager
from kagura.auth.exceptions import AuthenticationError
from kagura.cli.auth_cli import auth_group


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create Click CLI test runner"""
    return CliRunner()


class TestAuthLoginCommand:
    """Tests for 'kagura auth login' command"""

    def test_login_success(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
        mock_credentials: Credentials,
    ):
        """Test successful login command"""
        monkeypatch.setenv("HOME", str(tmp_path))

        with patch.object(OAuth2Manager, "login") as mock_login:
            result = cli_runner.invoke(
                auth_group, ["login", "--provider", "google"]
            )

            assert result.exit_code == 0
            assert "successful" in result.output.lower()
            mock_login.assert_called_once()

    def test_login_missing_client_secrets(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch
    ):
        """Test login with missing client_secrets.json"""
        monkeypatch.setenv("HOME", str(tmp_path))

        with patch.object(
            OAuth2Manager,
            "login",
            side_effect=FileNotFoundError("client_secrets.json not found"),
        ):
            result = cli_runner.invoke(
                auth_group, ["login", "--provider", "google"]
            )

            assert result.exit_code != 0
            assert "error" in result.output.lower()

    def test_login_authentication_failed(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch
    ):
        """Test login with authentication failure"""
        monkeypatch.setenv("HOME", str(tmp_path))

        with patch.object(
            OAuth2Manager,
            "login",
            side_effect=AuthenticationError("Authentication failed"),
        ):
            result = cli_runner.invoke(
                auth_group, ["login", "--provider", "google"]
            )

            assert result.exit_code != 0
            assert "failed" in result.output.lower()

    def test_login_default_provider(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch
    ):
        """Test login with default provider"""
        monkeypatch.setenv("HOME", str(tmp_path))

        with patch.object(OAuth2Manager, "login") as mock_login:
            result = cli_runner.invoke(auth_group, ["login"])

            assert result.exit_code == 0
            mock_login.assert_called_once()


class TestAuthLogoutCommand:
    """Tests for 'kagura auth logout' command"""

    def test_logout_success(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
        mock_credentials: Credentials,
    ):
        """Test successful logout command"""
        monkeypatch.setenv("HOME", str(tmp_path))

        # Setup authenticated state
        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        result = cli_runner.invoke(
            auth_group, ["logout", "--provider", "google"]
        )

        assert result.exit_code == 0
        assert "logged out" in result.output.lower()

    def test_logout_not_authenticated(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch
    ):
        """Test logout when not authenticated"""
        monkeypatch.setenv("HOME", str(tmp_path))

        result = cli_runner.invoke(
            auth_group, ["logout", "--provider", "google"]
        )

        assert result.exit_code == 0
        assert "not authenticated" in result.output.lower()

    def test_logout_default_provider(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
        mock_credentials: Credentials,
    ):
        """Test logout with default provider"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        result = cli_runner.invoke(auth_group, ["logout"])

        assert result.exit_code == 0


class TestAuthStatusCommand:
    """Tests for 'kagura auth status' command"""

    def test_status_not_authenticated(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch
    ):
        """Test status when not authenticated"""
        monkeypatch.setenv("HOME", str(tmp_path))

        result = cli_runner.invoke(auth_group, ["status"])

        assert result.exit_code == 0
        assert "not authenticated" in result.output.lower()
        assert "google" in result.output.lower()

    def test_status_authenticated(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
        mock_credentials: Credentials,
    ):
        """Test status when authenticated"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        result = cli_runner.invoke(auth_group, ["status"])

        assert result.exit_code == 0
        assert "authenticated" in result.output.lower()
        assert "google" in result.output.lower()

    def test_status_shows_expiry(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
        mock_credentials: Credentials,
    ):
        """Test status shows token expiry"""
        monkeypatch.setenv("HOME", str(tmp_path))

        auth = OAuth2Manager()
        auth._save_credentials(mock_credentials)

        result = cli_runner.invoke(auth_group, ["status"])

        assert result.exit_code == 0
        # Status table should be displayed
        assert "provider" in result.output.lower() or "google" in result.output.lower()
