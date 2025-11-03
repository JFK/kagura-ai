"""GitHub CLI Agent with safety controls.

This module provides safe GitHub operations via the `gh` CLI,
with automatic safety analysis and confirmation prompts.

All operations use the CommandSafetyAnalyzer for protection against
dangerous commands.
"""

import logging
from pathlib import Path

from kagura import tool
from kagura.core.shell import ShellExecutor
from kagura.core.shell_safety import DangerLevel, check_command_safety

logger = logging.getLogger(__name__)


@tool
async def gh_safe_exec(
    command: str,
    working_dir: str = ".",
    auto_confirm: bool = False,
    enable_llm_check: bool = False,
) -> str:
    """Execute gh command with automatic safety checking.

    This agent analyzes the command for safety before execution.
    Dangerous commands require auto_confirm=True.

    Args:
        command: GitHub CLI command (with or without 'gh' prefix)
        working_dir: Working directory for command execution
        auto_confirm: Skip safety confirmation (use for confirmed commands)
        enable_llm_check: Enable LLM-based safety analysis (slower, smarter)

    Returns:
        Command output or safety warning

    Raises:
        ValueError: If command validation fails

    Examples:
        >>> # Safe command (executes immediately)
        >>> await gh_safe_exec("gh issue view 348")
        >>> await gh_safe_exec("issue view 348")  # 'gh' prefix optional

        >>> # Dangerous command (requires confirmation)
        >>> await gh_safe_exec("gh pr merge 465")  # Returns warning
        >>> await gh_safe_exec("gh pr merge 465", auto_confirm=True)  # Executes
    """
    # Normalize command (add 'gh' prefix if missing)
    if not command.strip().startswith("gh "):
        command = f"gh {command}"

    # Safety check
    safety = await check_command_safety(
        command, enable_llm=enable_llm_check, context={"tool": "gh"}
    )

    # Handle based on danger level
    if safety.level == DangerLevel.HIGH:
        if not auto_confirm:
            warning = (
                f"🚨 CRITICAL DANGER DETECTED\n"
                f"Command: {command}\n\n"
                f"Reason: {safety.reasoning}\n"
                f"Risks:\n"
            )
            for risk in safety.risks:
                warning += f"  • {risk}\n"

            if safety.safe_alternative:
                warning += f"\nSafer alternative:\n  {safety.safe_alternative}\n"

            warning += "\n❌ Execution blocked. Use auto_confirm=True to override."
            return warning

        logger.warning(f"Executing HIGH danger command with confirmation: {command}")

    elif safety.level == DangerLevel.MEDIUM:
        if not auto_confirm:
            warning = (
                f"⚠️ WARNING: Potentially dangerous operation\n"
                f"Command: {command}\n\n"
                f"Reason: {safety.reasoning}\n"
                f"Risks: {', '.join(safety.risks)}\n\n"
                f"Use auto_confirm=True to proceed."
            )
            return warning

        logger.info(f"Executing MEDIUM danger command with confirmation: {command}")

    # Execute command
    try:
        executor = ShellExecutor(allowed_commands=["gh"], working_dir=Path(working_dir))
        result = await executor.exec(command)

        if result.return_code != 0:
            return f"❌ Command failed (exit {result.return_code}):\n{result.stderr}"

        return result.stdout if result.stdout else result.stderr

    except Exception as e:
        logger.error(f"Failed to execute gh command: {e}", exc_info=True)
        return f"❌ Execution error: {e}"


@tool
async def gh_pr_create_safe(
    title: str,
    body: str,
    base: str = "main",
    draft: bool = True,
    auto_confirm: bool = False,
) -> str:
    """Create GitHub PR with safety confirmation.

    Uses temporary markdown file for PR body to avoid escaping issues.

    Args:
        title: PR title
        body: PR description (markdown)
        base: Base branch (default: main)
        draft: Create as draft (default: True, safer)
        auto_confirm: Skip confirmation prompt

    Returns:
        PR creation result or confirmation prompt

    Example:
        >>> result = await gh_pr_create_safe(
        ...     title="feat: Add feature",
        ...     body="Description",
        ...     draft=True
        ... )
    """
    import tempfile
    import uuid
    from pathlib import Path

    # Create temporary file for PR body
    temp_dir = Path(tempfile.gettempdir())
    temp_file = temp_dir / f"kagura_pr_body_{uuid.uuid4().hex[:8]}.md"

    try:
        # Write body to temp file
        temp_file.write_text(body, encoding="utf-8")

        # Build command with --body-file
        draft_flag = "--draft" if draft else ""
        cmd = (
            f'gh pr create --title "{title}" --body-file {temp_file} '
            f"--base {base} {draft_flag}"
        ).strip()

        result = await gh_safe_exec(cmd, auto_confirm=auto_confirm)
        return result

    finally:
        # Always cleanup temp file
        if temp_file.exists():
            temp_file.unlink()


@tool
async def gh_pr_merge_safe(
    pr_number: int,
    squash: bool = True,
    delete_branch: bool = True,
    auto_confirm: bool = False,
) -> str:
    """Merge GitHub PR with safety confirmation.

    Args:
        pr_number: PR number to merge
        squash: Use squash merge (default: True)
        delete_branch: Delete branch after merge (default: True)
        auto_confirm: Skip confirmation (DANGEROUS)

    Returns:
        Merge result or confirmation prompt

    Example:
        >>> # First call - get confirmation prompt
        >>> result = await gh_pr_merge_safe(465)
        >>> # Second call - execute with confirmation
        >>> result = await gh_pr_merge_safe(465, auto_confirm=True)
    """
    merge_method = "--squash" if squash else "--merge"
    delete_flag = "--delete-branch" if delete_branch else ""
    cmd = f"gh pr merge {pr_number} {merge_method} {delete_flag}".strip()

    return await gh_safe_exec(cmd, auto_confirm=auto_confirm)
