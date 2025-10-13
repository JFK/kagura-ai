"""Tests for build CLI commands"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from kagura.cli.build_cli import agent_command, build_group
from kagura.meta.spec import AgentSpec


@pytest.fixture
def runner():
    """Create CLI test runner"""
    return CliRunner()


@pytest.fixture
def mock_spec():
    """Create mock AgentSpec"""
    return AgentSpec(
        name="test_agent",
        description="Test agent for CLI",
        input_type="str",
        output_type="str",
        system_prompt="You are a test agent.",
    )


@pytest.fixture
def mock_code():
    """Create mock generated code"""
    return """
from kagura import agent

@agent(model="gpt-4o-mini", temperature=0.7)
async def test_agent(input_data: str) -> str:
    '''Test agent for CLI'''
    return input_data
"""


class TestBuildGroupCommand:
    """Tests for build command group"""

    def test_build_group_help(self, runner):
        """Test build group help message"""
        result = runner.invoke(build_group, ["--help"])
        assert result.exit_code == 0
        assert "Build agents, tools, and workflows" in result.output

    def test_build_agent_help(self, runner):
        """Test build agent help message"""
        result = runner.invoke(build_group, ["agent", "--help"])
        assert result.exit_code == 0
        assert "Build an AI agent from natural language" in result.output
        assert "--description" in result.output
        assert "--output" in result.output
        assert "--model" in result.output


class TestAgentCommandNonInteractive:
    """Tests for agent command in non-interactive mode"""

    @patch("kagura.cli.build_cli.MetaAgent")
    def test_agent_command_non_interactive_basic(
        self, mock_meta_class, runner, tmp_path, mock_spec, mock_code
    ):
        """Test agent command in non-interactive mode"""
        # Setup mocks
        mock_meta = MagicMock()
        mock_meta.parser = MagicMock()
        mock_meta.parser.parse = AsyncMock(return_value=mock_spec)
        mock_meta.generate_from_spec = AsyncMock(return_value=mock_code)
        mock_meta_class.return_value = mock_meta

        # Run command
        output_path = tmp_path / "test_agent.py"
        result = runner.invoke(
            agent_command,
            [
                "--description",
                "Test agent",
                "--output",
                str(output_path),
                "--no-interactive",
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert output_path.exists()
        saved_code = output_path.read_text()
        assert "@agent" in saved_code

    @patch("kagura.cli.build_cli.MetaAgent")
    def test_agent_command_no_description_non_interactive(
        self, mock_meta_class, runner
    ):
        """Test agent command fails without description in non-interactive mode"""
        result = runner.invoke(agent_command, ["--no-interactive"])

        assert result.exit_code == 1
        assert "Error: Description required" in result.output

    @patch("kagura.cli.build_cli.MetaAgent")
    def test_agent_command_custom_model(
        self, mock_meta_class, runner, tmp_path, mock_spec, mock_code
    ):
        """Test agent command with custom model"""
        # Setup mocks
        mock_meta = MagicMock()
        mock_meta.parser = MagicMock()
        mock_meta.parser.parse = AsyncMock(return_value=mock_spec)
        mock_meta.generate_from_spec = AsyncMock(return_value=mock_code)
        mock_meta_class.return_value = mock_meta

        # Run command with custom model
        output_path = tmp_path / "test_agent.py"
        result = runner.invoke(
            agent_command,
            [
                "--description",
                "Test agent",
                "--output",
                str(output_path),
                "--model",
                "gpt-4o",
                "--no-interactive",
            ],
        )

        # Verify model was passed
        assert result.exit_code == 0
        mock_meta_class.assert_called_once()
        call_kwargs = mock_meta_class.call_args.kwargs
        assert call_kwargs.get("model") == "gpt-4o"

    @patch("kagura.cli.build_cli.MetaAgent")
    def test_agent_command_no_validate(
        self, mock_meta_class, runner, tmp_path, mock_spec, mock_code
    ):
        """Test agent command with --no-validate flag"""
        # Setup mocks
        mock_meta = MagicMock()
        mock_meta.parser = MagicMock()
        mock_meta.parser.parse = AsyncMock(return_value=mock_spec)
        mock_meta.generate_from_spec = AsyncMock(return_value=mock_code)
        mock_meta_class.return_value = mock_meta

        # Run command
        output_path = tmp_path / "test_agent.py"
        result = runner.invoke(
            agent_command,
            [
                "--description",
                "Test agent",
                "--output",
                str(output_path),
                "--no-validate",
                "--no-interactive",
            ],
        )

        # Verify validation was disabled
        assert result.exit_code == 0
        mock_meta_class.assert_called_once()
        call_kwargs = mock_meta_class.call_args.kwargs
        assert call_kwargs.get("validate") is False


class TestAgentCommandInteractive:
    """Tests for agent command in interactive mode"""

    @patch("kagura.cli.build_cli.MetaAgent")
    @patch("kagura.cli.build_cli.Confirm.ask")
    @patch("kagura.cli.build_cli.Prompt.ask")
    def test_agent_command_interactive_accept(
        self,
        mock_prompt,
        mock_confirm,
        mock_meta_class,
        runner,
        tmp_path,
        mock_spec,
        mock_code,
    ):
        """Test agent command in interactive mode with user accepting"""
        # Setup mocks
        mock_prompt.side_effect = [
            "Create a test agent",  # Description
            str(tmp_path / "test_agent.py"),  # Output path
        ]
        mock_confirm.return_value = True  # Confirm generation

        mock_meta = MagicMock()
        mock_meta.parser = MagicMock()
        mock_meta.parser.parse = AsyncMock(return_value=mock_spec)
        mock_meta.generate_from_spec = AsyncMock(return_value=mock_code)
        mock_meta_class.return_value = mock_meta

        # Run command (interactive by default)
        result = runner.invoke(agent_command, input="\n\n")

        # Verify
        assert result.exit_code == 0
        assert "Agent created" in result.output

    @patch("kagura.cli.build_cli.MetaAgent")
    @patch("kagura.cli.build_cli.Confirm.ask")
    @patch("kagura.cli.build_cli.Prompt.ask")
    def test_agent_command_interactive_cancel(
        self,
        mock_prompt,
        mock_confirm,
        mock_meta_class,
        runner,
        mock_spec,
    ):
        """Test agent command in interactive mode with user cancelling"""
        # Setup mocks
        mock_prompt.return_value = "Create a test agent"
        mock_confirm.return_value = False  # User cancels

        mock_meta = MagicMock()
        mock_meta.parser = MagicMock()
        mock_meta.parser.parse = AsyncMock(return_value=mock_spec)
        mock_meta_class.return_value = mock_meta

        # Run command
        result = runner.invoke(agent_command, input="\n\n")

        # Verify
        assert "Cancelled" in result.output


class TestAgentCommandErrorHandling:
    """Tests for error handling in agent command"""

    @patch("kagura.cli.build_cli.MetaAgent")
    def test_agent_command_validation_error(
        self, mock_meta_class, runner, tmp_path, mock_spec
    ):
        """Test agent command handles validation errors"""
        from kagura.meta.validator import ValidationError

        # Setup mocks
        mock_meta = MagicMock()
        mock_meta.parser = MagicMock()
        mock_meta.parser.parse = AsyncMock(return_value=mock_spec)
        mock_meta.generate_from_spec = AsyncMock(
            side_effect=ValidationError("Test validation error")
        )
        mock_meta_class.return_value = mock_meta

        # Run command
        output_path = tmp_path / "test_agent.py"
        result = runner.invoke(
            agent_command,
            [
                "--description",
                "Test agent",
                "--output",
                str(output_path),
                "--no-interactive",
            ],
        )

        # Verify
        assert result.exit_code == 1
        assert "Validation failed" in result.output

    @patch("kagura.cli.build_cli.MetaAgent")
    def test_agent_command_generic_error(
        self, mock_meta_class, runner, tmp_path, mock_spec
    ):
        """Test agent command handles generic errors"""
        # Setup mocks
        mock_meta = MagicMock()
        mock_meta.parser = MagicMock()
        mock_meta.parser.parse = AsyncMock(side_effect=Exception("Test error"))
        mock_meta_class.return_value = mock_meta

        # Run command
        output_path = tmp_path / "test_agent.py"
        result = runner.invoke(
            agent_command,
            [
                "--description",
                "Test agent",
                "--output",
                str(output_path),
                "--no-interactive",
            ],
        )

        # Verify
        assert result.exit_code == 1
        assert "Error" in result.output
