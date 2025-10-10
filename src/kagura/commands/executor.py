"""Command execution for custom commands.

Executes commands with inline command substitution and template rendering.
"""

import re
import subprocess
from typing import Any, Optional

from jinja2 import Template

from .command import Command
from .hooks import HookRegistry, HookType, get_registry


class InlineCommandExecutor:
    """Execute inline commands in templates.

    Inline commands use the syntax !`command` and are replaced with the
    command's output during template rendering.

    Example:
        Template: "Current directory: !`pwd`"
        Rendered: "Current directory: /home/user/project"
    """

    def __init__(
        self, timeout: int = 10, hook_registry: Optional[HookRegistry] = None
    ) -> None:
        """Initialize inline command executor.

        Args:
            timeout: Timeout in seconds for command execution (default: 10)
            hook_registry: Hook registry for pre/post execution hooks
        """
        self.timeout = timeout
        self.hook_registry = hook_registry or get_registry()
        self._pattern = re.compile(r"!`([^`]+)`")

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

        # Execute pre-tool-use hooks
        tool_input = {"command": command, "tool": "bash"}
        hook_results = self.hook_registry.execute_hooks(
            HookType.PRE_TOOL_USE, "bash", tool_input
        )

        # Check if any hook blocked execution
        for result in hook_results:
            if result.is_blocked():
                return f"[Blocked: {result.message}]"
            # Apply modifications if any
            if result.modified_input:
                command = result.modified_input.get("command", command)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            output = (
                result.stdout.strip()
                if result.returncode == 0
                else f"[Error: {result.stderr.strip()}]"
            )

            # Execute post-tool-use hooks
            post_input = {
                "command": command,
                "tool": "bash",
                "output": output,
                "returncode": result.returncode,
            }
            self.hook_registry.execute_hooks(HookType.POST_TOOL_USE, "bash", post_input)

            return output

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
        self,
        inline_timeout: int = 10,
        enable_inline: bool = True,
        hook_registry: Optional[HookRegistry] = None,
    ) -> None:
        """Initialize command executor.

        Args:
            inline_timeout: Timeout for inline command execution
            enable_inline: Enable inline command execution (default: True)
            hook_registry: Hook registry for pre/post execution hooks
        """
        self.enable_inline = enable_inline
        self.hook_registry = hook_registry or get_registry()
        self.inline_executor = InlineCommandExecutor(
            timeout=inline_timeout, hook_registry=self.hook_registry
        )

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

        # Execute validation hooks
        validation_input = {
            "command_name": command.name,
            "parameters": params,
            "template": command.template,
        }
        hook_results = self.hook_registry.execute_hooks(
            HookType.VALIDATION, command.name, validation_input
        )

        # Check if any hook blocked execution
        for result in hook_results:
            if result.is_blocked():
                raise ValueError(f"Validation failed: {result.message}")
            # Apply parameter modifications if any
            if result.modified_input and "parameters" in result.modified_input:
                params = result.modified_input["parameters"]

        # Validate parameters (built-in validation)
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
