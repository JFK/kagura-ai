"""Command execution for custom commands.

Executes commands with inline command substitution and template rendering.
"""

import re
import subprocess
from typing import Any, Optional

from jinja2 import Template

from .command import Command


class InlineCommandExecutor:
    """Execute inline commands in templates.

    Inline commands use the syntax !`command` and are replaced with the
    command's output during template rendering.

    Example:
        Template: "Current directory: !`pwd`"
        Rendered: "Current directory: /home/user/project"
    """

    def __init__(self, timeout: int = 10) -> None:
        """Initialize inline command executor.

        Args:
            timeout: Timeout in seconds for command execution (default: 10)
        """
        self.timeout = timeout
        self._pattern = re.compile(r'!`([^`]+)`')

    def execute(self, template: str) -> str:
        """Execute all inline commands in template.

        Args:
            template: Template string containing inline commands

        Returns:
            Template with inline commands replaced by their output

        Example:
            >>> executor = InlineCommandExecutor()
            >>> result = executor.execute("Time: !`date`")
            >>> "Time:" in result
            True
        """
        return self._pattern.sub(self._execute_command, template)

    def _execute_command(self, match: re.Match) -> str:
        """Execute a single inline command.

        Args:
            match: Regex match object containing the command

        Returns:
            Command output or error message
        """
        command = match.group(1)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Command failed, return stderr
                return f"[Error: {result.stderr.strip()}]"

        except subprocess.TimeoutExpired:
            return f"[Error: Command timed out after {self.timeout}s]"
        except Exception as e:
            return f"[Error: {str(e)}]"


class CommandExecutor:
    """Execute custom commands with template rendering.

    Combines inline command execution and Jinja2 template rendering
    to produce the final command prompt.
    """

    def __init__(
        self, inline_timeout: int = 10, enable_inline: bool = True
    ) -> None:
        """Initialize command executor.

        Args:
            inline_timeout: Timeout for inline command execution
            enable_inline: Enable inline command execution (default: True)
        """
        self.enable_inline = enable_inline
        self.inline_executor = InlineCommandExecutor(timeout=inline_timeout)

    def render(
        self, command: Command, parameters: Optional[dict[str, Any]] = None
    ) -> str:
        """Render command template with parameters and inline commands.

        Args:
            command: Command to render
            parameters: Template parameters (default: {})

        Returns:
            Rendered template string

        Raises:
            ValueError: If required parameters are missing

        Example:
            >>> cmd = Command(
            ...     name="test",
            ...     description="Test",
            ...     template="Hello {{ name }}!",
            ...     parameters={"name": "string"}
            ... )
            >>> executor = CommandExecutor()
            >>> executor.render(cmd, {"name": "Alice"})
            'Hello Alice!'
        """
        params = parameters or {}

        # Validate parameters
        if command.parameters:
            command.validate_parameters(params)

        # Step 1: Execute inline commands
        template_str = command.template
        if self.enable_inline:
            template_str = self.inline_executor.execute(template_str)

        # Step 2: Render Jinja2 template with parameters
        template = Template(template_str)
        rendered = template.render(**params)

        return rendered

    def execute(
        self, command: Command, parameters: Optional[dict[str, Any]] = None
    ) -> str:
        """Execute command and return rendered result.

        This is an alias for render() for consistency with the executor pattern.

        Args:
            command: Command to execute
            parameters: Template parameters

        Returns:
            Rendered template string
        """
        return self.render(command, parameters)
