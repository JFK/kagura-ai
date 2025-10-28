"""Tests for MCP remote connection CLI commands."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from kagura.cli.mcp import connect, test_remote


class TestMCPConnect:
    """Test 'kagura mcp connect' command."""

    @pytest.fixture
    def temp_config_dir(self, monkeypatch, tmp_path):
        """Use temporary directory for config."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        yield tmp_path

    def test_connect_saves_config(self, temp_config_dir):
        """Test that connect command saves configuration."""
        runner = CliRunner()

        result = runner.invoke(
            connect,
            [
                "--api-base",
                "https://api.example.com",
                "--api-key",
                "test_key_123",
                "--user-id",
                "test_user",
            ],
        )

        # Should succeed
        assert result.exit_code == 0
        assert "configured successfully" in result.output

        # Check config file exists (XDG config dir)
        config_file = temp_config_dir / ".config" / "kagura" / "remote-config.json"
        assert config_file.exists()

        # Check config content
        with open(config_file) as f:
            config = json.load(f)

        assert config["api_base"] == "https://api.example.com"
        assert config["api_key"] == "test_key_123"
        assert config["user_id"] == "test_user"

    def test_connect_without_api_key(self, temp_config_dir):
        """Test connect without API key (optional)."""
        runner = CliRunner()

        result = runner.invoke(
            connect,
            ["--api-base", "https://api.example.com"],
        )

        assert result.exit_code == 0

        # Check config
        config_file = temp_config_dir / ".config" / "kagura" / "remote-config.json"
        with open(config_file) as f:
            config = json.load(f)

        assert config["api_base"] == "https://api.example.com"
        assert config["api_key"] is None
        assert config["user_id"] == "default_user"

    def test_connect_invalid_url(self, temp_config_dir):
        """Test connect with invalid URL."""
        runner = CliRunner()

        result = runner.invoke(
            connect,
            ["--api-base", "invalid-url"],
        )

        # Should fail
        assert result.exit_code != 0
        assert "must start with http" in result.output.lower()

    def test_connect_strips_trailing_slash(self, temp_config_dir):
        """Test that trailing slash is removed from URL."""
        runner = CliRunner()

        result = runner.invoke(
            connect,
            ["--api-base", "https://api.example.com/"],
        )

        assert result.exit_code == 0

        # Check config
        config_file = temp_config_dir / ".config" / "kagura" / "remote-config.json"
        with open(config_file) as f:
            config = json.load(f)

        # Should strip trailing slash
        assert config["api_base"] == "https://api.example.com"


class TestMCPTestRemote:
    """Test 'kagura mcp test-remote' command."""

    @pytest.fixture
    def temp_config_dir(self, monkeypatch, tmp_path):
        """Use temporary directory for config."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        yield tmp_path

    @pytest.fixture
    def mock_config(self, temp_config_dir):
        """Create mock remote config."""
        config_dir = temp_config_dir / ".kagura"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "remote-config.json"

        config = {
            "api_base": "https://api.example.com",
            "api_key": "test_key_123",
            "user_id": "test_user",
        }

        with open(config_file, "w") as f:
            json.dump(config, f)

        return config_file

    def test_test_remote_without_config(self, temp_config_dir):
        """Test test-remote without configuration."""
        runner = CliRunner()

        result = runner.invoke(test_remote)

        # Should fail
        assert result.exit_code != 0
        assert "not configured" in result.output.lower()

    @pytest.mark.skip(reason="Requires mock HTTP server")
    def test_test_remote_with_valid_config(self, mock_config):
        """Test test-remote with valid configuration."""
        # Would require mocking httpx requests
        pytest.skip("Requires HTTP mocking")

    @pytest.mark.skip(reason="Requires mock HTTP server")
    def test_test_remote_connection_failure(self, mock_config):
        """Test test-remote with unreachable server."""
        pytest.skip("Requires HTTP mocking")


class TestMCPRemoteDocumentation:
    """Test that remote commands have proper documentation."""

    def test_connect_help(self):
        """Test that connect command has help text."""
        runner = CliRunner()
        result = runner.invoke(connect, ["--help"])

        assert result.exit_code == 0
        assert "Configure remote MCP connection" in result.output
        assert "--api-base" in result.output
        assert "--api-key" in result.output

    def test_test_remote_help(self):
        """Test that test-remote command has help text."""
        runner = CliRunner()
        result = runner.invoke(test_remote, ["--help"])

        assert result.exit_code == 0
        assert "Test remote MCP connection" in result.output
