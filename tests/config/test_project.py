"""Tests for project configuration and auto-detection."""

import subprocess
from unittest.mock import MagicMock, patch

from kagura.config.project import (
    detect_git_repo_name,
    get_default_project,
    get_default_user,
    get_reranking_enabled,
    load_pyproject_config,
)


class TestDetectGitRepoName:
    """Test git repository name detection."""

    def test_detect_from_https_url(self):
        """Detect repo name from HTTPS URL."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/JFK/kagura-ai.git\n"

        with patch("subprocess.run", return_value=mock_result):
            assert detect_git_repo_name() == "kagura-ai"

    def test_detect_from_https_url_no_git_suffix(self):
        """Detect repo name from HTTPS URL without .git."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/JFK/kagura-ai\n"

        with patch("subprocess.run", return_value=mock_result):
            assert detect_git_repo_name() == "kagura-ai"

    def test_detect_from_ssh_url(self):
        """Detect repo name from SSH URL."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git@github.com:JFK/kagura-ai.git\n"

        with patch("subprocess.run", return_value=mock_result):
            assert detect_git_repo_name() == "kagura-ai"

    def test_detect_from_directory_name(self):
        """Fallback to directory name if remote fails."""
        # First call (remote) fails, second call (toplevel) succeeds
        mock_results = [
            MagicMock(returncode=1, stdout=""),  # remote get-url fails
            MagicMock(returncode=0, stdout="/home/user/projects/my-app\n"),  # toplevel succeeds
        ]

        with patch("subprocess.run", side_effect=mock_results):
            assert detect_git_repo_name() == "my-app"

    def test_no_git_repo(self):
        """Return None when not in git repository."""
        mock_result = MagicMock()
        mock_result.returncode = 128  # Not a git repository

        with patch("subprocess.run", return_value=mock_result):
            assert detect_git_repo_name() is None

    def test_timeout_handling(self):
        """Handle subprocess timeout gracefully."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 1)):
            assert detect_git_repo_name() is None


class TestLoadPyprojectConfig:
    """Test pyproject.toml configuration loading."""

    def test_load_existing_config(self, tmp_path, monkeypatch):
        """Load configuration from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.kagura]
project = "test-project"
user = "testuser"
enable_reranking = true
""")

        monkeypatch.chdir(tmp_path)

        config = load_pyproject_config()
        assert config["project"] == "test-project"
        assert config["user"] == "testuser"
        assert config["enable_reranking"] is True

    def test_no_pyproject_file(self, tmp_path, monkeypatch):
        """Return empty dict when pyproject.toml doesn't exist."""
        monkeypatch.chdir(tmp_path)

        config = load_pyproject_config()
        assert config == {}

    def test_no_tool_kagura_section(self, tmp_path, monkeypatch):
        """Return empty dict when [tool.kagura] section is missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test"
""")

        monkeypatch.chdir(tmp_path)

        config = load_pyproject_config()
        assert config == {}

    def test_invalid_toml(self, tmp_path, monkeypatch):
        """Return empty dict when pyproject.toml is invalid."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("invalid toml [[[")

        monkeypatch.chdir(tmp_path)

        config = load_pyproject_config()
        assert config == {}


class TestGetDefaultProject:
    """Test default project resolution with priority cascade."""

    def test_env_var_highest_priority(self, monkeypatch):
        """Environment variable has highest priority."""
        monkeypatch.setenv("KAGURA_DEFAULT_PROJECT", "env-project")

        with patch("kagura.config.project.load_pyproject_config", return_value={"project": "pyproject-project"}):
            with patch("kagura.config.project.detect_git_repo_name", return_value="git-project"):
                assert get_default_project() == "env-project"

    def test_pyproject_second_priority(self, monkeypatch):
        """pyproject.toml has second priority."""
        monkeypatch.delenv("KAGURA_DEFAULT_PROJECT", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={"project": "pyproject-project"}):
            with patch("kagura.config.project.detect_git_repo_name", return_value="git-project"):
                assert get_default_project() == "pyproject-project"

    def test_git_detection_third_priority(self, monkeypatch):
        """Git detection has third priority."""
        monkeypatch.delenv("KAGURA_DEFAULT_PROJECT", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={}):
            with patch("kagura.config.project.detect_git_repo_name", return_value="git-project"):
                assert get_default_project() == "git-project"

    def test_no_detection(self, monkeypatch):
        """Return None when nothing is detected."""
        monkeypatch.delenv("KAGURA_DEFAULT_PROJECT", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={}):
            with patch("kagura.config.project.detect_git_repo_name", return_value=None):
                assert get_default_project() is None


class TestGetDefaultUser:
    """Test default user resolution."""

    def test_env_var_highest_priority(self, monkeypatch):
        """Environment variable has highest priority."""
        monkeypatch.setenv("KAGURA_DEFAULT_USER", "env-user")

        with patch("kagura.config.project.load_pyproject_config", return_value={"user": "pyproject-user"}):
            assert get_default_user() == "env-user"

    def test_pyproject_second_priority(self, monkeypatch):
        """pyproject.toml has second priority."""
        monkeypatch.delenv("KAGURA_DEFAULT_USER", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={"user": "pyproject-user"}):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="git-user\n")
                assert get_default_user() == "pyproject-user"

    def test_git_user_third_priority(self, monkeypatch):
        """Git user.name has third priority."""
        monkeypatch.delenv("KAGURA_DEFAULT_USER", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={}):
            mock_result = MagicMock(returncode=0, stdout="git-user\n")
            with patch("subprocess.run", return_value=mock_result):
                assert get_default_user() == "git-user"

    def test_no_detection(self, monkeypatch):
        """Return None when nothing is detected."""
        monkeypatch.delenv("KAGURA_DEFAULT_USER", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={}):
            mock_result = MagicMock(returncode=1, stdout="")
            with patch("subprocess.run", return_value=mock_result):
                assert get_default_user() is None


class TestGetRerankingEnabled:
    """Test reranking enabled flag resolution."""

    def test_env_var_true(self, monkeypatch):
        """Environment variable 'true' enables reranking."""
        monkeypatch.setenv("KAGURA_ENABLE_RERANKING", "true")

        with patch("kagura.config.project.load_pyproject_config", return_value={"enable_reranking": False}):
            assert get_reranking_enabled() is True

    def test_env_var_variants(self, monkeypatch):
        """Test various true values."""
        for value in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            monkeypatch.setenv("KAGURA_ENABLE_RERANKING", value)
            assert get_reranking_enabled() is True, f"Failed for value: {value}"

    def test_env_var_false(self, monkeypatch):
        """Environment variable 'false' disables reranking."""
        monkeypatch.setenv("KAGURA_ENABLE_RERANKING", "false")

        with patch("kagura.config.project.load_pyproject_config", return_value={"enable_reranking": True}):
            assert get_reranking_enabled() is False

    def test_pyproject_second_priority(self, monkeypatch):
        """pyproject.toml has second priority."""
        monkeypatch.delenv("KAGURA_ENABLE_RERANKING", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={"enable_reranking": True}):
            assert get_reranking_enabled() is True

    def test_auto_enable_when_cached(self, monkeypatch):
        """Auto-enable when model is cached."""
        monkeypatch.delenv("KAGURA_ENABLE_RERANKING", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={}):
            with patch("kagura.config.project.is_reranking_model_cached", return_value=True):
                assert get_reranking_enabled() is True

    def test_default_false_when_not_cached(self, monkeypatch):
        """Default to False when model is not cached."""
        monkeypatch.delenv("KAGURA_ENABLE_RERANKING", raising=False)

        with patch("kagura.config.project.load_pyproject_config", return_value={}):
            with patch("kagura.config.project.is_reranking_model_cached", return_value=False):
                assert get_reranking_enabled() is False
