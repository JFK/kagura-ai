"""
Tool wrappers and agent for TUI mode with yes/no dialogs.

Uses prompt_toolkit's yes_no_dialog for confirmations instead of input().
"""

from prompt_toolkit.shortcuts import yes_no_dialog
from rich.console import Console

from kagura import agent
from kagura.chat.shell_tool import InteractiveShellTool
from kagura.core.memory import MemoryManager
from kagura.core.shell import SecurityError, ShellResult

# Import all other tools from session
from .session import (
    _brave_search_tool,
    _execute_python_tool,
    _file_read_tool,
    _file_search_tool,
    _file_write_tool,
    _url_fetch_tool,
    _web_search_tool,
    _youtube_metadata_tool,
    _youtube_transcript_tool,
)


async def shell_exec_tool_tui(command: str, user_intent: str = "") -> str:
    """Execute shell command in TUI mode with dialog confirmation.

    Args:
        command: Shell command to execute
        user_intent: What the user is trying to accomplish

    Returns:
        Command output or error message

    Note:
        Uses yes_no_dialog() instead of input() for TUI compatibility.
    """
    console = Console()

    # Create shell tool
    tool = InteractiveShellTool(console=console, auto_confirm=True)

    # Validate security first
    try:
        tool.executor.validate_command(command)
    except SecurityError as e:
        return f"🛑 Security Error: {e}"

    # Show confirmation dialog
    confirmed = yes_no_dialog(
        title="Execute Shell Command?",
        text=f"Command: {command}\n\nExecute this command?",
    ).run()

    if not confirmed:
        return "⚠️ Command execution cancelled by user"

    # Execute command
    try:
        result: ShellResult = await tool.execute(
            command,
            show_confirmation=False,  # Already confirmed via dialog
            interactive=False,  # TUI mode doesn't support TTY
        )

        if result.success:
            return result.stdout or "(No output)"
        else:
            error_msg = result.stderr or f"Command failed (exit {result.return_code})"

            # Auto-retry with LLM analysis
            if user_intent:
                console.print("\n[yellow]💡 Analyzing error...[/]")

                try:
                    from kagura.chat.command_fixer import command_fixer

                    # Get fixed command from LLM
                    fixed_command = await command_fixer(
                        failed_command=command,
                        error_message=error_msg,
                        user_intent=user_intent,
                    )

                    fixed_command = str(fixed_command).strip()

                    if fixed_command and fixed_command != command:
                        # Ask to retry with fixed command
                        retry_confirmed = yes_no_dialog(
                            title="Try Fixed Command?",
                            text=f"Original: {command}\nFailed: {error_msg}\n\nSuggested fix: {fixed_command}\n\nTry this instead?",
                        ).run()

                        if retry_confirmed:
                            # Retry (no auto-retry to prevent loops)
                            return await shell_exec_tool_tui(fixed_command, user_intent="")

                except Exception as e:
                    console.print(f"[dim]Error analyzing: {e}[/]")

            # No retry or retry declined
            return f"❌ Command failed:\n{error_msg}"

    except Exception as e:
        return f"❌ Error: {e}"


# TUI-specific chat agent (same as chat_agent but with TUI shell tool)
@agent(
    model="gpt-4o-mini",
    temperature=0.7,
    enable_memory=False,
    tools=[
        # File operations
        _file_read_tool,
        _file_write_tool,
        _file_search_tool,
        # Code execution
        _execute_python_tool,
        # Shell execution (TUI version with yes/no dialogs)
        shell_exec_tool_tui,
        # Web & Content
        _brave_search_tool,
        _web_search_tool,
        _url_fetch_tool,
        # YouTube
        _youtube_transcript_tool,
        _youtube_metadata_tool,
    ],
)
async def chat_agent_tui(user_input: str, memory: MemoryManager) -> str:
    """
    TUI-compatible chat agent with dialog-based shell confirmations.

    This is identical to chat_agent except it uses shell_exec_tool_tui
    which shows yes/no dialogs instead of input() prompts.

    User: {{ user_input }}

    [Same tool documentation as chat_agent...]
    """
    ...
