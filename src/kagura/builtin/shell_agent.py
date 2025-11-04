"""Shell command agent with safety controls.

Provides safe shell command execution with automatic danger detection
and confirmation prompts.
"""

import logging
from pathlib import Path

from kagura import agent
from kagura.core.shell import ShellExecutor
from kagura.core.shell_safety import DangerLevel, check_command_safety

logger = logging.getLogger(__name__)


@agent
async def shell_safe_exec(
    command: str,
    working_dir: str = ".",
    auto_confirm: bool = False,
    enable_llm_check: bool = False,
) -> str:
    """Execute shell command with automatic safety checking.

    Analyzes command for potential dangers before execution.
    Requires auto_confirm=True for dangerous operations.

    Args:
        command: Shell command to execute
        working_dir: Working directory (default: current directory)
        auto_confirm: Skip safety confirmation (use for verified commands)
        enable_llm_check: Enable LLM-based analysis (slower, optional)

    Returns:
        Command output or safety warning

    Examples:
        >>> # Safe command (executes immediately)
        >>> await shell_safe_exec("ls -la")
        >>> await shell_safe_exec("git status")

        >>> # With working directory
        >>> await shell_safe_exec("pytest", working_dir="/home/project/tests")

        >>> # Dangerous command (requires confirmation)
        >>> await shell_safe_exec("rm -rf build")  # Returns warning
        >>> await shell_safe_exec("rm -rf build", auto_confirm=True)  # Executes
    """
    # Safety check
    safety = await check_command_safety(
        command, enable_llm=enable_llm_check, context={"working_dir": working_dir}
    )

    # Handle based on danger level
    if safety.level == DangerLevel.HIGH:
        if not auto_confirm:
            warning = (
                f"🚨 CRITICAL DANGER DETECTED\n"
                f"Command: {command}\n"
                f"Working Directory: {working_dir}\n\n"
                f"Reason: {safety.reasoning}\n"
                f"Risks:\n"
            )
            for risk in safety.risks:
                warning += f"  • {risk}\n"

            if safety.safe_alternative:
                warning += f"\n💡 Safer alternative:\n  {safety.safe_alternative}\n"

            warning += (
                "\n❌ Execution BLOCKED. "
                "Use auto_confirm=True to override (not recommended)."
            )
            return warning

        logger.warning(
            f"Executing HIGH danger command with override: {command} in {working_dir}"
        )

    elif safety.level == DangerLevel.MEDIUM:
        if not auto_confirm:
            warning = (
                f"⚠️ WARNING: Potentially dangerous operation\n"
                f"Command: {command}\n"
                f"Working Directory: {working_dir}\n\n"
                f"Reason: {safety.reasoning}\n"
                f"Risks: {', '.join(safety.risks)}\n"
            )

            if safety.safe_alternative:
                warning += f"\n💡 Consider: {safety.safe_alternative}\n"

            warning += "\nTo proceed, call with auto_confirm=True"
            return warning

        logger.info(f"Executing MEDIUM danger command with confirmation: {command}")

    elif safety.level == DangerLevel.LOW:
        logger.debug(f"Executing LOW danger command: {command}")

    # Execute command
    try:
        executor = ShellExecutor(working_dir=Path(working_dir))
        result = await executor.exec(command)

        if result.return_code != 0:
            error_msg = (
                f"❌ Command failed (exit code {result.return_code})\n"
                f"Command: {command}\n"
                f"Error: {result.stderr}"
            )
            logger.error(error_msg)
            return error_msg

        output = result.stdout if result.stdout else result.stderr
        logger.debug(f"Command executed successfully: {command}")
        return output

    except Exception as e:
        logger.error(f"Shell execution error: {e}", exc_info=True)
        return f"❌ Execution error: {e}"


@agent
async def cd_and_exec(path: str, command: str, auto_confirm: bool = False) -> str:
    """Change directory and execute command (convenience wrapper).

    Args:
        path: Directory path
        command: Command to execute in that directory
        auto_confirm: Skip safety confirmation

    Returns:
        Command output

    Example:
        >>> await cd_and_exec("/home/project", "ls -la")
        >>> await cd_and_exec("/home/project", "git status")
    """
    return await shell_safe_exec(command, working_dir=path, auto_confirm=auto_confirm)
