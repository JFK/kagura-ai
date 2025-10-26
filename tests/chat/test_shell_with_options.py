"""Tests for shell_exec_with_options."""

from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from kagura.chat.shell_tool import _suggest_alternatives, shell_exec_with_options


class TestSuggestAlternatives:
    """Tests for _suggest_alternatives function."""

    def test_pwd_command_not_found(self):
        """Test alternatives for pwd command not found."""
        alternatives = _suggest_alternatives(
            "pwd", "bash: pwd: command not found", "show current directory"
        )

        assert len(alternatives) >= 2
        assert any("echo $PWD" in alt["command"] for alt in alternatives)
        assert any("ls -la" in alt["command"] for alt in alternatives)

    def test_tree_command_not_found(self):
        """Test alternatives for tree command not found."""
        alternatives = _suggest_alternatives(
            "tree -L 1", "bash: tree: command not found", "show directory tree"
        )

        assert len(alternatives) >= 1
        assert any("ls -R" in alt["command"] for alt in alternatives)

    def test_find_permission_denied(self):
        """Test alternatives for find permission denied."""
        alternatives = _suggest_alternatives(
            "find . -name '*.py'",
            "find: ./some/dir: Permission denied",
            "find Python files",
        )

        assert len(alternatives) >= 1
        assert any("2>/dev/null" in alt["command"] for alt in alternatives)

    def test_no_alternatives_for_unknown_error(self):
        """Test no alternatives for unknown errors."""
        alternatives = _suggest_alternatives(
            "some_weird_command", "unknown error occurred", "do something"
        )

        assert len(alternatives) == 0


@pytest.mark.asyncio
class TestShellExecWithOptions:
    """Tests for shell_exec_with_options function."""

    async def test_auto_select_first_option(self):
        """Test auto-selecting first option."""
        options = [
            {"command": "echo 'test1'", "description": "first option"},
            {"command": "echo 'test2'", "description": "second option"},
        ]

        console = Console(file=StringIO(), force_terminal=True)

        result = await shell_exec_with_options(
            options=options,
            auto_select=1,  # Select first option
            interactive=False,
            console=console,
        )

        assert "test1" in result

    async def test_auto_select_second_option(self):
        """Test auto-selecting second option."""
        options = [
            {"command": "echo 'first'", "description": "first"},
            {"command": "echo 'second'", "description": "second"},
        ]

        console = Console(file=StringIO(), force_terminal=True)

        result = await shell_exec_with_options(
            options=options,
            auto_select=2,  # Select second option
            interactive=False,
            console=console,
        )

        assert "second" in result

    async def test_user_selects_option(self):
        """Test user selecting an option."""
        options = [
            {"command": "echo 'option1'", "description": "first"},
            {"command": "echo 'option2'", "description": "second"},
        ]

        console = Console(file=StringIO(), force_terminal=True)

        # Mock user input: select option 2
        with patch("builtins.input", return_value="2"):
            result = await shell_exec_with_options(
                options=options,
                auto_select=0,  # Ask user
                interactive=False,
                console=console,
            )

        assert "option2" in result

    async def test_user_cancels_selection(self):
        """Test user cancelling selection."""
        options = [
            {"command": "echo 'test'", "description": "test"},
        ]

        console = Console(file=StringIO(), force_terminal=True)

        # Mock user input: cancel
        with patch("builtins.input", return_value="n"):
            result = await shell_exec_with_options(
                options=options,
                auto_select=0,
                interactive=False,
                console=console,
            )

        assert "cancelled" in result.lower()

    async def test_invalid_selection(self):
        """Test invalid selection number."""
        options = [
            {"command": "echo 'test'", "description": "test"},
        ]

        console = Console(file=StringIO(), force_terminal=True)

        # Mock user input: invalid number
        with patch("builtins.input", return_value="99"):
            result = await shell_exec_with_options(
                options=options,
                auto_select=0,
                interactive=False,
                console=console,
            )

        assert "Invalid selection" in result

    async def test_empty_options_list(self):
        """Test with empty options list."""
        console = Console(file=StringIO(), force_terminal=True)

        result = await shell_exec_with_options(
            options=[],
            auto_select=0,
            console=console,
        )

        assert "No command options" in result
