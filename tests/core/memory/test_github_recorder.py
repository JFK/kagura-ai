"""Tests for GitHubRecorder."""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kagura.core.memory.github_recorder import (
    GitHubRecordConfig,
    GitHubRecorder,
)
from kagura.core.memory.interaction_tracker import InteractionRecord


@pytest.fixture
def recorder():
    """Create GitHubRecorder with auto-detect disabled."""
    config = GitHubRecordConfig(auto_detect_issue=False, enabled=True)
    return GitHubRecorder(config=config)


@pytest.fixture
def recorder_with_issue():
    """Create GitHubRecorder with issue number set."""
    config = GitHubRecordConfig(auto_detect_issue=False, enabled=True)
    recorder = GitHubRecorder(config=config)
    recorder.set_issue_number(493)
    return recorder


@pytest.fixture
def sample_interaction():
    """Create sample interaction record."""
    return InteractionRecord(
        user_query="How to fix memory leak?",
        ai_response="Use context managers and weak references...",
        interaction_type="error_fix",
        importance=8.5,
    )


class TestGitHubRecordConfig:
    """Tests for GitHubRecordConfig."""

    def test_config_defaults(self):
        """Test default configuration."""
        config = GitHubRecordConfig()

        assert config.repo is None
        assert config.auto_detect_issue is True
        assert config.enabled is True

    def test_config_custom(self):
        """Test custom configuration."""
        config = GitHubRecordConfig(
            repo="owner/repo", auto_detect_issue=False, enabled=False
        )

        assert config.repo == "owner/repo"
        assert config.auto_detect_issue is False
        assert config.enabled is False


class TestGitHubRecorder:
    """Tests for GitHubRecorder."""

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = GitHubRecordConfig(enabled=False, auto_detect_issue=False)
        recorder = GitHubRecorder(config=config)

        assert recorder.config.enabled is False
        assert recorder.current_issue_number is None

    @patch("subprocess.run")
    def test_auto_detect_issue_success(self, mock_run):
        """Test successful issue auto-detection from branch."""
        mock_run.return_value = MagicMock(
            stdout="493-featmemory-unify-coding-memory\n", returncode=0
        )

        config = GitHubRecordConfig(auto_detect_issue=True)
        recorder = GitHubRecorder(config=config)

        assert recorder.current_issue_number == 493

    @patch("subprocess.run")
    def test_auto_detect_issue_no_number(self, mock_run):
        """Test auto-detection when branch has no issue number."""
        mock_run.return_value = MagicMock(stdout="main\n", returncode=0)

        config = GitHubRecordConfig(auto_detect_issue=True)
        recorder = GitHubRecorder(config=config)

        assert recorder.current_issue_number is None

    @patch("subprocess.run")
    def test_auto_detect_issue_failure(self, mock_run):
        """Test auto-detection failure handling."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        config = GitHubRecordConfig(auto_detect_issue=True)
        recorder = GitHubRecorder(config=config)

        # Should not crash
        assert recorder.current_issue_number is None

    def test_set_issue_number(self, recorder):
        """Test manual issue number setting."""
        recorder.set_issue_number(123)

        assert recorder.current_issue_number == 123

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        timestamp = GitHubRecorder._format_timestamp()

        assert "UTC" in timestamp
        assert len(timestamp.split("-")) == 3  # YYYY-MM-DD format

    def test_format_immediate_comment(self, recorder_with_issue, sample_interaction):
        """Test immediate comment formatting."""
        comment = recorder_with_issue._format_immediate_comment(
            sample_interaction, "error_fix"
        )

        assert "🐛 Error Fix" in comment
        assert "How to fix memory leak?" in comment
        assert "Use context managers" in comment
        assert "8.5/10" in comment
        assert "Auto-recorded by Kagura" in comment

    def test_format_immediate_comment_truncation(self, recorder_with_issue):
        """Test long content truncation in immediate comment."""
        long_interaction = InteractionRecord(
            user_query="Q" * 300,
            ai_response="A" * 300,
            interaction_type="question",
            importance=5.0,
        )

        comment = recorder_with_issue._format_immediate_comment(
            long_interaction, "question"
        )

        # Should contain ellipsis for truncated content
        assert "..." in comment

    @pytest.mark.asyncio
    async def test_record_important_event_disabled(self, sample_interaction):
        """Test recording when GitHub is disabled."""
        config = GitHubRecordConfig(enabled=False)
        recorder = GitHubRecorder(config=config)

        result = await recorder.record_important_event(sample_interaction)

        assert result is False

    @pytest.mark.asyncio
    async def test_record_important_event_no_issue(
        self, recorder, sample_interaction
    ):
        """Test recording when no issue number is set."""
        result = await recorder.record_important_event(sample_interaction)

        assert result is False

    @pytest.mark.asyncio
    @patch("asyncio.get_event_loop")
    async def test_record_important_event_success(
        self, mock_loop, recorder_with_issue, sample_interaction
    ):
        """Test successful important event recording."""
        # Mock executor
        mock_executor = AsyncMock(return_value=None)
        mock_loop.return_value.run_in_executor = mock_executor

        result = await recorder_with_issue.record_important_event(sample_interaction)

        assert result is True
        mock_executor.assert_called_once()

    def test_format_session_comment_full(self, recorder_with_issue):
        """Test full session comment formatting."""
        summary_data = {
            "total_interactions": 15,
            "by_type": {"decision": 5, "implementation": 8, "error_fix": 2},
            "file_changes": [
                {"file_path": "src/auth.py", "action": "edit", "reason": "Add JWT"},
                {"file_path": "src/db.py", "action": "refactor", "reason": "Optimize"},
            ],
            "decisions": [
                {"decision": "Use FastAPI", "rationale": "Better async support"}
            ],
            "errors": [
                {
                    "error_type": "TypeError",
                    "message": "str vs int",
                    "solution": "Convert types",
                }
            ],
        }

        comment = recorder_with_issue._format_session_comment(
            "session_xyz", summary_data, "AI summary here"
        )

        assert "Claude Code Session Summary" in comment
        assert "session_xyz" in comment
        assert "15" in comment  # total_interactions
        assert "decision: 5" in comment
        assert "src/auth.py" in comment
        assert "Use FastAPI" in comment
        assert "TypeError" in comment
        assert "AI summary here" in comment

    @patch("subprocess.run")
    def test_is_available_no_gh_cli(self, mock_run, recorder_with_issue):
        """Test availability check when gh CLI not installed."""
        mock_run.side_effect = FileNotFoundError()

        assert recorder_with_issue.is_available() is False

    @patch("subprocess.run")
    def test_is_available_gh_fails(self, mock_run, recorder_with_issue):
        """Test availability when gh command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        assert recorder_with_issue.is_available() is False

    @patch("subprocess.run")
    def test_is_available_success(self, mock_run, recorder_with_issue):
        """Test availability when everything is set up."""
        mock_run.return_value = MagicMock(returncode=0)

        assert recorder_with_issue.is_available() is True

    def test_is_available_no_issue_number(self, recorder):
        """Test availability when no issue number set."""
        assert recorder.is_available() is False

    def test_is_available_disabled(self):
        """Test availability when GitHub recording disabled."""
        config = GitHubRecordConfig(enabled=False)
        recorder = GitHubRecorder(config=config)
        recorder.set_issue_number(123)

        assert recorder.is_available() is False
