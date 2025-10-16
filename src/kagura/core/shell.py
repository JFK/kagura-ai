"""Secure shell command executor for Kagura AI.

This module provides a secure execution environment for shell commands,
with whitelist/blacklist validation, timeout management, and sandbox support.
"""

import asyncio
import shlex
import subprocess
from pathlib import Path
from typing import Optional


class ShellExecutor:
    """Secure shell command executor with security controls."""

    def __init__(
        self,
        allowed_commands: Optional[list[str]] = None,
        blocked_commands: Optional[dict[str, str]] = None,
        working_dir: Optional[Path] = None,
        timeout: int = 30,
        require_confirmation: bool = False,
    ):
        """Initialize ShellExecutor.

        Args:
            allowed_commands: Whitelist of allowed commands (None = use defaults)
            blocked_commands: Blacklist of blocked commands (None = use defaults)
            working_dir: Working directory for command execution
            timeout: Command timeout in seconds
            require_confirmation: Whether to require user confirmation
        """
        self.allowed_commands = allowed_commands or self._default_allowed()
        self.blocked_commands = blocked_commands or self._default_blocked()
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout
        self.require_confirmation = require_confirmation

    @staticmethod
    def _default_allowed() -> list[str]:
        """Get default whitelist of allowed commands."""
        return [
            # Git
            "git",
            # File operations
            "ls",
            "cat",
            "find",
            "grep",
            "mkdir",
            "rm",
            "cp",
            "mv",
            "pwd",
            "wc",
            "sort",
            "uniq",
            # Package managers
            "npm",
            "pip",
            "uv",
            "poetry",
            "yarn",
            "pnpm",
            # Build tools
            "make",
            "cmake",
            "cargo",
            "go",
            # Testing
            "pytest",
            "jest",
            "vitest",
            # GitHub CLI
            "gh",
            # Network tools
            "curl",
            "wget",
            # Others
            "echo",
            "which",
        ]

    @staticmethod
    def _default_blocked() -> dict[str, str]:
        """Get blacklist of dangerous commands.

        Returns:
            Dict mapping command/pattern to match type:
            - "exact": Match command name only (first word)
            - "pattern": Match pattern anywhere in command string
        """
        return {
            # Exact command name matches
            "sudo": "exact",
            "su": "exact",
            "passwd": "exact",
            "shutdown": "exact",
            "reboot": "exact",
            "dd": "exact",
            "mkfs": "exact",
            "fdisk": "exact",
            "parted": "exact",
            "eval": "exact",
            "exec": "exact",
            "source": "exact",
            # Pattern matches (dangerous command sequences)
            "rm -rf /": "pattern",
            "| sh": "pattern",  # Piping to shell is dangerous
            "| bash": "pattern",  # Piping to bash is dangerous
        }

    def validate_command(self, command: str) -> bool:
        """Validate command against security policies.

        Args:
            command: Shell command to validate

        Returns:
            True if command is valid

        Raises:
            SecurityError: If command violates security policy
        """
        parts = shlex.split(command)
        if not parts:
            raise SecurityError("Empty command")

        cmd = parts[0]

        # Check blacklist first (higher priority)
        for blocked_cmd, match_type in self.blocked_commands.items():
            if match_type == "exact":
                # Check command name only (first word after parsing)
                if cmd == blocked_cmd:
                    raise SecurityError(f"Blocked command: {blocked_cmd}")
            elif match_type == "pattern":
                # Check pattern anywhere in command string (exact substring match)
                if blocked_cmd in command:
                    raise SecurityError(f"Blocked command pattern: {blocked_cmd}")

        # Check whitelist
        if self.allowed_commands:
            if cmd not in self.allowed_commands:
                raise SecurityError(f"Command not allowed: {cmd}")

        return True

    async def exec(
        self,
        command: str,
        env: Optional[dict[str, str]] = None,
        capture_output: bool = True,
    ) -> "ShellResult":
        """Execute shell command securely.

        Args:
            command: Shell command to execute
            env: Environment variables (optional)
            capture_output: Whether to capture stdout/stderr

        Returns:
            ShellResult containing execution results

        Raises:
            SecurityError: If command violates security policy
            TimeoutError: If command exceeds timeout
            UserCancelledError: If user cancels execution
        """
        # Validate command
        self.validate_command(command)

        # Ask for confirmation if required
        if self.require_confirmation:
            confirmed = await self._ask_confirmation(command)
            if not confirmed:
                raise UserCancelledError("Command execution cancelled by user")

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                cwd=str(self.working_dir),
                env=env,
            )

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )

            return ShellResult(
                return_code=process.returncode or 0,
                stdout=stdout.decode("utf-8") if stdout else "",
                stderr=stderr.decode("utf-8") if stderr else "",
                command=command,
            )

        except asyncio.TimeoutError:
            # Kill process on timeout
            if process:
                process.kill()
                await process.wait()
            raise TimeoutError(f"Command timed out after {self.timeout}s: {command}")

    async def _ask_confirmation(self, command: str) -> bool:
        """Ask user confirmation for command execution.

        Args:
            command: Command to confirm

        Returns:
            True if user confirms, False otherwise
        """
        # TODO: Integrate with CLI/UI for better confirmation flow
        print(f"Execute command: {command}? [y/N] ", end="", flush=True)
        try:
            response = input()
            return response.lower() == "y"
        except (EOFError, KeyboardInterrupt):
            return False


class ShellResult:
    """Result of shell command execution."""

    def __init__(
        self, return_code: int, stdout: str, stderr: str, command: str
    ) -> None:
        """Initialize ShellResult.

        Args:
            return_code: Process exit code
            stdout: Standard output
            stderr: Standard error
            command: Executed command
        """
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        self.command = command

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.return_code == 0

    def __str__(self) -> str:
        """Get string representation (stdout if success, stderr otherwise)."""
        return self.stdout if self.success else self.stderr

    def __repr__(self) -> str:
        """Get detailed representation."""
        status = "success" if self.success else f"failed (code={self.return_code})"
        return f"ShellResult({status}, command='{self.command}')"


class SecurityError(Exception):
    """Raised when command violates security policy."""

    pass


class UserCancelledError(Exception):
    """Raised when user cancels command execution."""

    pass
