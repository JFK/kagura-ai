"""Built-in shell agent for secure command execution."""

from pathlib import Path

from kagura.core.shell import ShellExecutor


async def shell(command: str, working_dir: str = ".") -> str:
    """Execute a shell command safely.

    This agent executes shell commands with security controls:
    - Whitelist validation (only allowed commands)
    - Blacklist filtering (dangerous commands blocked)
    - Timeout management (30s default)
    - Working directory isolation

    Args:
        command: The shell command to execute
        working_dir: Working directory (default: current directory)

    Returns:
        Command output (stdout if success, stderr if failed)

    Raises:
        RuntimeError: If command execution fails
        SecurityError: If command violates security policy

    Examples:
        >>> await shell("ls -la")
        >>> await shell("git status")
        >>> await shell("pytest tests/", working_dir="./myproject")
    """
    executor = ShellExecutor(working_dir=Path(working_dir))
    result = await executor.exec(command)

    if not result.success:
        raise RuntimeError(
            f"Command failed (exit {result.return_code}): {result.stderr}"
        )

    return result.stdout
