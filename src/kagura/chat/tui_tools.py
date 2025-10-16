"""
Tool wrappers for TUI mode (no interactive confirmation prompts).

Since TUI uses Application event loop, we can't use input() for confirmations.
These wrappers use auto-confirm mode and display commands before execution.
"""

from rich.console import Console

from kagura.chat.shell_tool import shell_exec_tool


async def _shell_exec_tool_tui(command: str, user_intent: str = "") -> str:
    """Execute shell command in TUI mode (auto-confirm).

    Args:
        command: Shell command to execute
        user_intent: What the user is trying to accomplish

    Returns:
        Command output or error message

    Note:
        This version uses auto_confirm=True because TUI can't handle input()
        prompts. The command is shown to the user before execution via
        append_output().
    """
    console = Console()

    # Show command that will be executed
    console.print(f"[yellow]💡 Executing:[/] [cyan]{command}[/cyan]")

    # Execute with auto-confirm (no interactive prompt)
    return await shell_exec_tool(
        command=command,
        auto_confirm=True,  # TUI can't handle input() prompts
        interactive=False,  # TUI can't handle TTY mode
        enable_auto_retry=True,  # Still enable auto-retry
        user_intent=user_intent or command,
        console=console,
    )
