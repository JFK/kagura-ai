"""
Interactive shell execution tool for chat session.

Provides user-confirmed shell execution with:
- Rich UI confirmation flow
- Security policy validation
- TTY mode for interactive commands (apt-get, rm -i, etc.)
- Error analysis for auto-correction
- Timeout management
"""

import asyncio
import os
import pty
import select
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from kagura.core.shell import (
    SecurityError,
    ShellExecutor,
    ShellResult,
    UserCancelledError,
)


class InteractiveShellTool:
    """Shell execution tool with interactive confirmation and TTY support.

    Features:
    - User confirmation before execution
    - Security policy validation
    - TTY mode for interactive commands (user can respond to prompts)
    - Error capture for auto-correction
    - Rich UI progress indicators
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        auto_confirm: bool = False,
        timeout: int = 30,
        working_dir: Optional[Path] = None,
    ):
        """Initialize interactive shell tool.

        Args:
            console: Rich console for output (default: create new)
            auto_confirm: Skip confirmation prompts (default: False)
            timeout: Command timeout in seconds (default: 30)
            working_dir: Working directory for command execution
        """
        self.console = console or Console()
        self.auto_confirm = auto_confirm
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()

        # Create shell executor with enhanced security
        self.executor = ShellExecutor(
            timeout=timeout,
            working_dir=self.working_dir,
            require_confirmation=False,  # We handle confirmation ourselves
        )

    async def execute(
        self,
        command: str,
        show_confirmation: bool = True,
        interactive: bool = True,
    ) -> ShellResult:
        """Execute shell command with user confirmation.

        Args:
            command: Shell command to execute
            show_confirmation: Whether to show confirmation prompt
            interactive: Use TTY mode (allows user input during execution)

        Returns:
            ShellResult with execution results

        Raises:
            SecurityError: If command violates security policy
            UserCancelledError: If user cancels execution
            TimeoutError: If command times out
        """
        # Validate security first
        try:
            self.executor.validate_command(command)
        except SecurityError as e:
            # Show blocked message
            self.console.print(
                Panel(
                    f"[red]🛑 BLOCKED: {e}[/red]\n\n"
                    "[yellow]💡 This command could be dangerous.[/yellow]\n"
                    "[dim]Please verify what you're trying to do.[/dim]",
                    title="[bold red]Security Warning[/]",
                    border_style="red",
                )
            )
            raise

        # Show command and ask confirmation
        if show_confirmation and not self.auto_confirm:
            confirmed = await self._ask_confirmation(command)
            if not confirmed:
                raise UserCancelledError("Command execution cancelled by user")

        # Show progress
        self.console.print(f"[dim]⚙️  Executing: [cyan]{command}[/cyan]...[/]")

        # Execute command
        if interactive:
            # Use TTY mode for interactive commands
            result = await self._execute_tty(command)
        else:
            # Use non-interactive mode (capture output)
            result = await self.executor.exec(command)

        # Show completion status
        if result.success:
            self.console.print(
                f"[dim]✓ Command completed (exit code: {result.return_code})[/]"
            )
        else:
            self.console.print(
                f"[yellow]✗ Command failed (exit code: {result.return_code})[/]"
            )

        return result

    async def _execute_tty(self, command: str) -> ShellResult:
        """Execute command in TTY mode (interactive).

        This allows the command to read user input directly (stdin),
        and output is displayed in real-time.

        Args:
            command: Shell command to execute

        Returns:
            ShellResult with execution results

        Raises:
            TimeoutError: If command times out
        """
        # Prepare to capture stdout/stderr
        stdout_data = []
        stderr_data = []

        def read_and_forward(fd: int, output_list: list[str]) -> None:
            """Read from fd and append to output_list."""
            try:
                data = os.read(fd, 1024)
                if data:
                    decoded = data.decode("utf-8", errors="replace")
                    output_list.append(decoded)
                    # Also write to stdout for user to see
                    sys.stdout.write(decoded)
                    sys.stdout.flush()
            except OSError:
                pass

        # Run command with PTY
        def run_with_pty() -> int:
            """Run command in PTY and return exit code."""
            master_fd, slave_fd = pty.openpty()

            try:
                # Fork process
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    cwd=str(self.working_dir),
                    preexec_fn=os.setsid,
                )

                # Close slave in parent
                os.close(slave_fd)

                # Make master non-blocking
                import fcntl

                flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
                fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                # Check if stdin has fileno (not available in pytest)
                stdin_fd = None
                old_stdin_flags = None
                try:
                    stdin_fd = sys.stdin.fileno()
                    old_stdin_flags = fcntl.fcntl(stdin_fd, fcntl.F_GETFL)
                    fcntl.fcntl(
                        stdin_fd, fcntl.F_SETFL, old_stdin_flags | os.O_NONBLOCK
                    )
                except (AttributeError, OSError, IOError):
                    # stdin not available (e.g., in pytest)
                    stdin_fd = None

                try:
                    # I/O loop
                    while process.poll() is None:
                        # Build list of fds to watch
                        watch_fds = [master_fd]
                        if stdin_fd is not None:
                            watch_fds.append(stdin_fd)

                        # Wait for readable fds
                        ready, _, _ = select.select(watch_fds, [], [], 0.1)

                        if master_fd in ready:
                            # Read from command output
                            read_and_forward(master_fd, stdout_data)

                        if stdin_fd is not None and stdin_fd in ready:
                            # Read from user input and forward to command
                            try:
                                user_input = os.read(stdin_fd, 1024)
                                if user_input:
                                    os.write(master_fd, user_input)
                            except OSError:
                                pass

                    # Read remaining output
                    while True:
                        try:
                            ready, _, _ = select.select([master_fd], [], [], 0)
                            if not ready:
                                break
                            read_and_forward(master_fd, stdout_data)
                        except OSError:
                            break

                finally:
                    # Restore stdin flags
                    if stdin_fd is not None and old_stdin_flags is not None:
                        fcntl.fcntl(stdin_fd, fcntl.F_SETFL, old_stdin_flags)

                return process.returncode or 0

            finally:
                os.close(master_fd)

        # Run with timeout
        try:
            return_code = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, run_with_pty),
                timeout=self.timeout,
            )

            return ShellResult(
                return_code=return_code,
                stdout="".join(stdout_data),
                stderr="".join(stderr_data),
                command=command,
            )

        except asyncio.TimeoutError:
            raise TimeoutError(f"Command timed out after {self.timeout}s: {command}")

    async def _ask_confirmation(self, command: str) -> bool:
        """Ask user to confirm command execution.

        Args:
            command: Command to confirm

        Returns:
            True if user confirms, False otherwise
        """
        # Show command in panel
        self.console.print(
            Panel(
                f"[cyan]{command}[/cyan]",
                title="[bold yellow]💡 Suggested Command[/]",
                border_style="yellow",
            )
        )

        # Ask for confirmation
        self.console.print("[yellow]⚠️  Execute this command? [Y/n]:[/] ", end="")

        try:
            # Use asyncio to read input without blocking
            response = await asyncio.get_event_loop().run_in_executor(None, input)

            # Empty response or 'y' → confirm
            # 'n' → cancel
            return response.strip().lower() in ("", "y", "yes")

        except (EOFError, KeyboardInterrupt):
            self.console.print("\n[yellow]Cancelled[/]")
            return False


async def shell_exec_tool(
    command: str,
    auto_confirm: bool = False,
    interactive: bool = True,
    console: Optional[Console] = None,
) -> str:
    """Execute shell command with user confirmation (tool function).

    This is the tool function that can be used directly by agents.

    Args:
        command: Shell command to execute
        auto_confirm: Skip confirmation (default: False)
        interactive: Use TTY mode for interactive commands (default: True)
        console: Rich console for output

    Returns:
        Command output (stdout if success, error message if failed)

    Examples:
        >>> # Non-interactive command
        >>> result = await shell_exec_tool("ls -la", auto_confirm=True)
        ⚙️  Executing: ls -la...
        total 48
        drwxr-xr-x  ...
        ✓ Command completed (exit code: 0)

        >>> # Interactive command (user can respond to prompts)
        >>> result = await shell_exec_tool("rm -i file.txt")
        💡 Suggested Command
        ┌─────────────────┐
        │ rm -i file.txt  │
        └─────────────────┘
        ⚠️  Execute this command? [Y/n]: y
        ⚙️  Executing: rm -i file.txt...
        remove file.txt? y  # ← ユーザーが応答できる
        ✓ Command completed (exit code: 0)
    """
    tool = InteractiveShellTool(
        console=console,
        auto_confirm=auto_confirm,
    )

    try:
        result = await tool.execute(command, interactive=interactive)

        if result.success:
            # Return stdout
            return result.stdout or "(No output)"
        else:
            # Return error with hint for auto-correction
            error_msg = result.stderr or f"Command failed (exit {result.return_code})"
            return (
                f"❌ Command failed:\n{error_msg}\n\n"
                f"💡 Hint: I can analyze this error and suggest a fix."
            )

    except SecurityError as e:
        return f"🛑 Security Error: {e}"

    except UserCancelledError:
        return "⚠️ Command execution cancelled by user"

    except TimeoutError as e:
        return f"⏱️ Timeout: {e}"

    except Exception as e:
        return f"❌ Unexpected error: {e}"
