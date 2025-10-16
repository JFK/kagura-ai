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
        sys.stdout.flush()  # Ensure prompt is displayed

        try:
            # Use asyncio with timeout to read input
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, input),
                timeout=60.0,  # 60 seconds for user to respond
            )

            # Empty response or 'y' → confirm
            # 'n' → cancel
            result = response.strip().lower() in ("", "y", "yes")
            return result

        except asyncio.TimeoutError:
            self.console.print("\n[yellow]⏱️  Confirmation timeout (auto-cancel)[/]")
            return False

        except (EOFError, KeyboardInterrupt):
            self.console.print("\n[yellow]Cancelled[/]")
            return False

        except Exception as e:
            self.console.print(f"\n[red]Error reading confirmation: {e}[/]")
            return False


async def shell_exec_with_options(
    options: list[dict[str, str]],
    auto_select: int = 0,
    interactive: bool = True,
    console: Optional[Console] = None,
) -> str:
    """Execute shell command from multiple options with user selection.

    Args:
        options: List of command options, each with "command" and "description"
        auto_select: Auto-select option (0 = ask user, 1-N = select that option)
        interactive: Use TTY mode for interactive commands
        console: Rich console for output

    Returns:
        Command output or error message

    Examples:
        >>> options = [
        ...     {"command": "pwd", "description": "current directory path"},
        ...     {"command": "ls -la", "description": "detailed file listing"},
        ...     {"command": "tree -L 1", "description": "visual tree view"},
        ... ]
        >>> result = await shell_exec_with_options(options)
        💡 Suggested commands:
          1. pwd          (current directory path)
          2. ls -la       (detailed file listing)
          3. tree -L 1    (visual tree view)

        ⚠️  Execute which command? [1/2/3/n]: 1
        ⚙️  Executing: pwd...
        ✓ Success
    """
    console = console or Console()

    # Validate options
    if not options or len(options) == 0:
        return "❌ Error: No command options provided"

    # Show options
    option_lines = []
    for i, opt in enumerate(options):
        desc = opt.get('description', 'no description')
        option_lines.append(
            f"  [cyan]{i+1}. {opt['command']:20}[/cyan] [dim]({desc})[/dim]"
        )

    console.print(
        Panel(
            "\n".join(option_lines),
            title="[bold yellow]💡 Suggested Commands[/]",
            border_style="yellow",
        )
    )

    # Ask user to select (unless auto_select is set)
    if auto_select > 0:
        if auto_select > len(options):
            return f"❌ Error: Invalid auto_select ({auto_select} > {len(options)})"
        selected_idx = auto_select - 1
    else:
        # Ask user
        console.print(
            f"[yellow]⚠️  Execute which command? [1-{len(options)}/n]:[/] ",
            end=""
        )
        sys.stdout.flush()

        try:
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, input),
                timeout=60.0,
            )

            # Parse response
            response = response.strip().lower()
            if response == 'n' or response == 'no':
                return "⚠️ Command execution cancelled by user"

            # Try to parse as number
            try:
                selected_idx = int(response) - 1
                if selected_idx < 0 or selected_idx >= len(options):
                    return (
                        f"❌ Error: Invalid selection "
                        f"(must be 1-{len(options)} or 'n')"
                    )
            except ValueError:
                # Default to first option if empty or invalid
                if response == '' or response == 'y' or response == 'yes':
                    selected_idx = 0
                else:
                    return (
                        f"❌ Error: Invalid input '{response}' "
                        f"(expected 1-{len(options)} or 'n')"
                    )

        except asyncio.TimeoutError:
            console.print("\n[yellow]⏱️  Selection timeout (auto-cancel)[/]")
            return "⚠️ Selection timeout"

        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Cancelled[/]")
            return "⚠️ Command execution cancelled by user"

        except Exception as e:
            return f"❌ Error reading selection: {e}"

    # Execute selected command
    selected_option = options[selected_idx]
    selected_command = selected_option["command"]

    console.print(
        f"\n[dim]Selected: [cyan]{selected_idx + 1}. {selected_command}[/cyan][/]"
    )

    # Execute using shell_exec_tool (without confirmation, already confirmed)
    return await shell_exec_tool(
        command=selected_command,
        auto_confirm=True,  # Already confirmed via selection
        interactive=interactive,
        console=console,
    )


async def shell_exec_tool(
    command: str,
    auto_confirm: bool = False,
    interactive: bool = True,
    console: Optional[Console] = None,
    enable_auto_retry: bool = False,
    user_intent: Optional[str] = None,
) -> str:
    """Execute shell command with user confirmation (tool function).

    This is the tool function that can be used directly by agents.

    Args:
        command: Shell command to execute
        auto_confirm: Skip confirmation (default: False)
        interactive: Use TTY mode for interactive commands (default: True)
        console: Rich console for output
        enable_auto_retry: Enable automatic retry with alternatives on failure
        user_intent: Original user intent (for better error analysis)

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
    console = console or Console()

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
            # Command failed
            error_msg = result.stderr or f"Command failed (exit {result.return_code})"

            # If auto_retry is enabled, use LLM to fix command
            if enable_auto_retry and user_intent:
                console.print("\n[yellow]💡 Analyzing error...[/]")

                try:
                    from kagura.chat.command_fixer import command_fixer

                    # Use LLM to generate fixed command
                    fixed_command = await command_fixer(
                        failed_command=command,
                        error_message=error_msg,
                        user_intent=user_intent,
                    )

                    fixed_command = fixed_command.strip()

                    if fixed_command and fixed_command != command:
                        console.print(
                            f"[yellow]💡 Suggested fix:[/] [cyan]{fixed_command}[/cyan]"
                        )
                        console.print(
                            "[yellow]⚠️  Try fixed command? [Y/n]:[/] ",
                            end=""
                        )
                        sys.stdout.flush()

                        try:
                            response = await asyncio.wait_for(
                                asyncio.get_event_loop().run_in_executor(None, input),
                                timeout=60.0,
                            )

                            if response.strip().lower() in ("", "y", "yes"):
                                # Retry with fixed command (no retry to prevent loop)
                                return await shell_exec_tool(
                                    command=fixed_command,
                                    auto_confirm=True,  # Already confirmed
                                    interactive=interactive,
                                    console=console,
                                    enable_auto_retry=False,  # Prevent infinite retry
                                )

                        except (asyncio.TimeoutError, EOFError, KeyboardInterrupt):
                            pass  # Fall through to error message

                except Exception as e:
                    console.print(f"[dim]Error analyzing command: {e}[/]")

            # No retry or no alternatives
            return (
                f"❌ Command failed:\n{error_msg}\n\n"
                f"💡 Hint: Try a different approach or ask for help."
            )

    except SecurityError as e:
        return f"🛑 Security Error: {e}"

    except UserCancelledError:
        return "⚠️ Command execution cancelled by user"

    except TimeoutError as e:
        return f"⏱️ Timeout: {e}"

    except Exception as e:
        return f"❌ Unexpected error: {e}"


def _suggest_alternatives(
    failed_command: str,
    error_message: str,
    user_intent: str,
) -> list[dict[str, str]]:
    """Suggest alternative commands based on error.

    Args:
        failed_command: The command that failed
        error_message: Error message from failed command
        user_intent: What the user was trying to do

    Returns:
        List of alternative command options

    Examples:
        >>> _suggest_alternatives("pwd", "command not found", "show directory")
        [
            {"command": "echo $PWD", "description": "using env variable"},
            {"command": "ls -la", "description": "show directory contents"},
        ]
    """
    alternatives = []

    # Simple rule-based alternatives (Week 2 will add LLM-based analysis)

    # "command not found" errors
    if "not found" in error_message.lower() or "no such file" in error_message.lower():
        # Common command not found → suggest alternatives
        if "pwd" in failed_command:
            alternatives.append({
                "command": "echo $PWD",
                "description": "using environment variable"
            })
            alternatives.append({
                "command": "ls -la",
                "description": "show directory contents instead"
            })

        elif "tree" in failed_command:
            alternatives.append({
                "command": "ls -R",
                "description": "recursive listing (tree alternative)"
            })
            alternatives.append({
                "command": "find . -type d",
                "description": "find all directories"
            })

    # "Permission denied" errors
    elif "permission denied" in error_message.lower():
        # Suggest adding 2>/dev/null or alternative approach
        if failed_command.startswith("find"):
            alternatives.append({
                "command": f"{failed_command} 2>/dev/null",
                "description": "ignore permission errors"
            })

    return alternatives
