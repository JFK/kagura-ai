"""Tests for command executors."""

import pytest

from kagura.commands import Command, CommandExecutor, InlineCommandExecutor


class TestInlineCommandExecutor:
    """Tests for InlineCommandExecutor."""

    def test_simple_command(self):
        """Test executing a simple inline command."""
        executor = InlineCommandExecutor()

        template = "Current user: !`whoami`"
        result = executor.execute(template)

        assert "Current user:" in result
        assert result != template  # Should be replaced
        assert "!`" not in result  # No inline command syntax

    def test_multiple_commands(self):
        """Test executing multiple inline commands."""
        executor = InlineCommandExecutor()

        template = "User: !`whoami`, PWD: !`pwd`"
        result = executor.execute(template)

        assert "User:" in result
        assert "PWD:" in result
        assert "!`" not in result

    def test_command_with_output(self):
        """Test command that produces output."""
        executor = InlineCommandExecutor()

        template = "Echo: !`echo hello`"
        result = executor.execute(template)

        assert "Echo: hello" in result

    def test_failed_command(self):
        """Test handling of failed command."""
        executor = InlineCommandExecutor()

        # Command that will fail
        template = "Fail: !`false`"
        result = executor.execute(template)

        assert "Fail:" in result
        assert "[Error" in result or result == "Fail: "

    def test_nonexistent_command(self):
        """Test handling of nonexistent command."""
        executor = InlineCommandExecutor()

        template = "Missing: !`nonexistent_command_12345`"
        result = executor.execute(template)

        assert "Missing:" in result
        assert "[Error" in result

    def test_timeout(self):
        """Test command timeout."""
        executor = InlineCommandExecutor(timeout=1)

        # Command that sleeps longer than timeout
        template = "Sleep: !`sleep 5`"
        result = executor.execute(template)

        assert "Sleep:" in result
        assert "timed out" in result.lower()

    def test_no_commands(self):
        """Test template with no inline commands."""
        executor = InlineCommandExecutor()

        template = "Just plain text"
        result = executor.execute(template)

        assert result == template

    def test_empty_command(self):
        """Test empty inline command."""
        executor = InlineCommandExecutor()

        template = "Empty: !``"
        result = executor.execute(template)

        # Should execute empty command (which does nothing)
        assert "Empty:" in result

    def test_command_with_pipes(self):
        """Test command with pipes."""
        executor = InlineCommandExecutor()

        template = "Files: !`echo hello | wc -w`"
        result = executor.execute(template)

        assert "Files:" in result
        assert "1" in result  # "hello" is 1 word

    def test_multiline_output(self):
        """Test command with multiline output."""
        executor = InlineCommandExecutor()

        template = "Lines: !`echo -e 'line1\\nline2\\nline3'`"
        result = executor.execute(template)

        assert "Lines:" in result
        assert "line1" in result


class TestCommandExecutor:
    """Tests for CommandExecutor."""

    def test_simple_render(self):
        """Test simple command rendering without inline commands."""
        command = Command(
            name="test",
            description="Test",
            template="Hello {{ name }}!",
            parameters={"name": "string"},
        )

        executor = CommandExecutor()
        result = executor.render(command, {"name": "World"})

        assert result == "Hello World!"

    def test_render_with_inline_commands(self):
        """Test rendering with inline commands."""
        command = Command(
            name="test",
            description="Test",
            template="User: {{ user }}, PWD: !`pwd`",
            parameters={"user": "string"},
        )

        executor = CommandExecutor()
        result = executor.render(command, {"user": "Alice"})

        assert "User: Alice" in result
        assert "PWD:" in result
        assert "!`" not in result

    def test_render_no_parameters(self):
        """Test rendering without parameters."""
        command = Command(
            name="test",
            description="Test",
            template="Static content",
        )

        executor = CommandExecutor()
        result = executor.render(command)

        assert result == "Static content"

    def test_missing_required_parameter(self):
        """Test error when required parameter is missing."""
        command = Command(
            name="test",
            description="Test",
            template="Hello {{ name }}!",
            parameters={"name": "string"},
        )

        executor = CommandExecutor()

        with pytest.raises(ValueError, match="Required parameter"):
            executor.render(command, {})

    def test_execute_alias(self):
        """Test that execute() is an alias for render()."""
        command = Command(
            name="test",
            description="Test",
            template="Hello!",
        )

        executor = CommandExecutor()
        result1 = executor.render(command)
        result2 = executor.execute(command)

        assert result1 == result2

    def test_disable_inline_commands(self):
        """Test disabling inline command execution."""
        command = Command(
            name="test",
            description="Test",
            template="PWD: !`pwd`",
        )

        executor = CommandExecutor(enable_inline=False)
        result = executor.render(command)

        # Inline command should not be executed
        assert "!`pwd`" in result

    def test_complex_template(self):
        """Test complex template with both parameters and inline commands."""
        command = Command(
            name="test",
            description="Test",
            template="""# Analysis for {{ filename }}

User is {{ user }}

## Processing

Count: {{ count }}
""",
            parameters={"filename": "string", "user": "string", "count": "int"},
        )

        executor = CommandExecutor(enable_inline=False)  # Disable inline for simplicity
        result = executor.render(
            command,
            {"filename": "test.txt", "user": "Alice", "count": 3}
        )

        assert "# Analysis for test.txt" in result
        assert "User is Alice" in result
        assert "Count: 3" in result

    def test_custom_timeout(self):
        """Test custom timeout for inline commands."""
        command = Command(
            name="test",
            description="Test",
            template="Result: !`sleep 2 && echo done`",
        )

        # Short timeout - should fail
        executor = CommandExecutor(inline_timeout=1)
        result = executor.render(command)
        assert "timed out" in result.lower()

        # Longer timeout - should succeed
        executor = CommandExecutor(inline_timeout=5)
        result = executor.render(command)
        assert "done" in result

    def test_jinja2_features(self):
        """Test that Jinja2 features work correctly."""
        command = Command(
            name="test",
            description="Test",
            template="""
{% if verbose %}
Verbose mode enabled
{% else %}
Quiet mode
{% endif %}

Files: {% for file in files %}{{ file }} {% endfor %}
""",
            parameters={"verbose": "bool", "files": "list"},
        )

        executor = CommandExecutor(enable_inline=False)
        result = executor.render(
            command,
            {"verbose": True, "files": ["a.txt", "b.txt", "c.txt"]}
        )

        assert "Verbose mode enabled" in result
        assert "a.txt" in result
        assert "b.txt" in result
        assert "c.txt" in result
