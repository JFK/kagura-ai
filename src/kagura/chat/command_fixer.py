"""
Command Fixer Agent - Analyzes failed commands and suggests fixes.

Part of RFC-033 Week 2: Auto-correction for shell commands.
"""

from kagura import agent


@agent(model="gpt-5-mini", temperature=0.3)
async def command_fixer(
    failed_command: str,
    error_message: str,
    user_intent: str,
) -> str:
    """Analyze failed shell command and suggest a working fix.

    Failed command: {{ failed_command }}
    Error message: {{ error_message }}
    User's intent: {{ user_intent }}

    Analyze the error and provide a SINGLE corrected command that will work.

    Common fixes:
    - Command not found → suggest alternative command
      - pwd not found → echo $PWD
      - tree not found → ls -R or find
    - Permission denied → add 2>/dev/null to ignore errors
    - Syntax error → fix command syntax
    - File not found → check path or suggest alternative

    IMPORTANT:
    - Return ONLY the fixed command, nothing else
    - No explanation, no markdown, just the command
    - Make sure the command is safe and will likely work
    - Prefer simpler, more portable commands

    Examples:
    User intent: show current directory
    Failed: pwd (command not found)
    Fixed: echo $PWD

    User intent: find Python files
    Failed: find . -name "*.py" (Permission denied)
    Fixed: find . -name "*.py" 2>/dev/null

    User intent: show directory tree
    Failed: tree -L 1 (command not found)
    Fixed: ls -R

    Now fix this command:
    """
    ...
