"""Tests for command fixer agent."""

import pytest

from kagura.chat.command_fixer import command_fixer
from kagura.testing.mocking import LLMMock


class TestCommandFixer:
    """Tests for command_fixer agent."""

    @pytest.mark.asyncio
    async def test_command_fixer_exists(self):
        """Test that command_fixer agent exists and is callable."""
        assert callable(command_fixer)
        assert hasattr(command_fixer, "_is_agent")

    @pytest.mark.asyncio
    async def test_pwd_not_found_fix(self):
        """Test fixing 'pwd: command not found' error."""
        with LLMMock("echo $PWD"):
            result = await command_fixer(
                failed_command="pwd",
                error_message="bash: pwd: command not found",
                user_intent="show current directory",
            )

        result_str = str(result)
        assert "echo $PWD" in result_str or "PWD" in result_str

    @pytest.mark.asyncio
    async def test_tree_not_found_fix(self):
        """Test fixing 'tree: command not found' error."""
        with LLMMock("ls -R"):
            result = await command_fixer(
                failed_command="tree -L 1",
                error_message="bash: tree: command not found",
                user_intent="show directory tree",
            )

        result_str = str(result)
        assert "ls -R" in result_str or "ls" in result_str

    @pytest.mark.asyncio
    async def test_permission_denied_fix(self):
        """Test fixing permission denied errors."""
        with LLMMock("find . -name '*.py' 2>/dev/null"):
            result = await command_fixer(
                failed_command="find . -name '*.py'",
                error_message="find: ./somedir: Permission denied",
                user_intent="find Python files",
            )

        result_str = str(result)
        assert "2>/dev/null" in result_str or "find" in result_str

    @pytest.mark.asyncio
    async def test_syntax_error_fix(self):
        """Test fixing syntax errors."""
        with LLMMock("ls -la"):
            result = await command_fixer(
                failed_command="ls -laa",
                error_message="ls: invalid option -- 'a'",
                user_intent="list files in detail",
            )

        result_str = str(result).strip()
        assert result_str  # Should return something

    @pytest.mark.asyncio
    async def test_returns_single_command(self):
        """Test that fixer returns only a single command."""
        with LLMMock("echo $PWD"):
            result = await command_fixer(
                failed_command="pwd",
                error_message="command not found",
                user_intent="show directory",
            )

        # Should not contain explanations or multiple lines
        result_str = str(result).strip()
        lines = result_str.split("\n")
        assert len(lines) <= 2  # Allow for minor formatting
