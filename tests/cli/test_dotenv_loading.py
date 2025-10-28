"""Tests for .env file auto-loading in CLI (Issue #444)."""

import os

from click.testing import CliRunner

from kagura.cli.main import cli


class TestDotenvLoading:
    """Test that .env files are automatically loaded by CLI."""

    def test_dotenv_loaded_in_cli(self, tmp_path, monkeypatch):
        """Test that CLI automatically loads .env file."""
        # Create .env file with OPENAI_API_KEY
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=sk-test123456789\n")

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Clear any existing OPENAI_API_KEY from environment
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        # Also need to mock XDG dirs for config doctor
        monkeypatch.setenv("KAGURA_DATA_DIR", str(tmp_path / "data"))

        # Run config doctor (should load .env and detect key)
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "doctor"])

        # load_dotenv() is called, so OPENAI_API_KEY should be loaded
        # Config doctor should NOT complain about missing keys
        assert "Missing required variables" not in result.output and \
               "OPENAI_API_KEY" not in result.output

    def test_dotenv_not_required(self, tmp_path, monkeypatch):
        """Test that CLI works without .env file."""
        # Change to temp directory (no .env file)
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        # Should still work without .env
        assert result.exit_code == 0

    def test_system_env_takes_precedence(self, tmp_path, monkeypatch):
        """Test that system environment variables override .env."""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_OVERRIDE=from_dotenv\n")

        # Set system environment variable (should take precedence)
        monkeypatch.setenv("TEST_OVERRIDE", "from_system")

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0

        # System env should take precedence (dotenv default behavior)
        assert os.getenv("TEST_OVERRIDE") == "from_system"

    def test_config_doctor_with_dotenv(self, tmp_path, monkeypatch):
        """Test that config doctor recognizes keys from .env."""
        # Create .env with API key
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=sk-test123456789\n")

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Clear any existing OPENAI_API_KEY
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "doctor"])

        # Should detect the API key from .env
        # Should NOT show "Missing required variables" error
        assert "At least one of: OPENAI_API_KEY" not in result.output
        # May still show connection test failure (no real API),
        # but key should be detected
        assert result.exit_code in [0, 1]  # 1 if connection test fails
