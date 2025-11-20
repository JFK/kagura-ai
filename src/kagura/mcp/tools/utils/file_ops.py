"""Built-in MCP tools for File and Directory operations

Exposes file/directory operations via MCP for Claude Desktop.
"""

from __future__ import annotations

import json
from pathlib import Path

from kagura import tool


@tool
def file_read(path: str, encoding: str = "utf-8") -> str:
    """Read the content of a text file from the local filesystem.

    Use this tool when:
    - User mentions a specific file by name
    - Need to analyze or process existing file content
    - User asks to 'read', 'check', 'open', or 'show' a file
    - Reviewing configuration files or logs
    - Examining code or documentation

    Do NOT use for:
    - Creating new files (use file_write)
    - Searching for files (use dir_list first)
    - Binary files (images, videos, etc.)

    Args:
        path: File path (absolute or relative to working directory)
        encoding: File encoding (default: utf-8, use 'utf-16', 'latin-1' if needed)

    Returns:
        File content as string

    Example:
        # Read configuration
        path="config.json"

        # Read with specific encoding
        path="data.csv", encoding="utf-8"

        # Read from absolute path
        path="/home/user/notes.txt"
    """
    try:
        return Path(path).read_text(encoding=encoding)
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def file_write(path: str, content: str, encoding: str = "utf-8") -> str:
    """Write or save content to a file on the local filesystem.

    Use this tool when:
    - User asks to save, write, or create a file
    - Generated content (code, text, data) needs to be persisted
    - User wants to export results to a file
    - Creating configuration or script files
    - Saving analysis results

    Do NOT use for:
    - Reading files (use file_read)
    - Appending to files (overwrites existing content)

    Args:
        path: File path (creates new file or overwrites existing)
        content: Content to write to the file
        encoding: File encoding (default: utf-8)

    Returns:
        Confirmation message with character count

    Example:
        # Save generated code
        path="script.py", content="print('Hello')"

        # Create configuration
        path="config.json", content='{"key": "value"}'

        # Save to absolute path
        path="/home/user/output.txt", content="Analysis results..."
    """
    try:
        Path(path).write_text(content, encoding=encoding)
        return f"Wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def dir_list(path: str = ".", pattern: str = "*") -> str:
    """List files and directories in a specified path.

    Use this tool when:
    - User asks 'what files are in...'
    - Need to explore directory structure
    - Looking for files matching a pattern
    - User wants to see available files before reading
    - Checking if a file exists

    Supports glob patterns for filtering (e.g., '*.txt', '*.py', '**/*.json').

    Args:
        path: Directory path (default: "." for current directory)
        pattern: Glob pattern to filter files:
            - "*" (all files in directory)
            - "*.txt" (all .txt files)
            - "*.{py,js}" (all .py and .js files)
            - "**/*.md" (all .md files recursively)

    Returns:
        JSON array of relative file paths (sorted alphabetically)

    Example:
        # List all files in current directory
        path=".", pattern="*"

        # List Python files
        path="src", pattern="*.py"

        # List all markdown files recursively
        path="docs", pattern="**/*.md"

        # List specific pattern
        path="/home/user/projects", pattern="*.{json,yaml}"
    """
    try:
        files = [str(f.relative_to(path)) for f in Path(path).glob(pattern)]
        return json.dumps(sorted(files), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def shell_exec(
    command: str,
    working_dir: str = ".",
    force: bool = False,
    return_code: bool = False,
) -> str:
    """Generate Python code for shell command (does NOT execute directly).

    Returns implementation code instead of executing. Allows review before running.

    Args:
        command: Shell command to show implementation for
        working_dir: Working directory context
        force: Whether safety checks would be skipped (for documentation)
        return_code: If True, return executable code; if False, return explanation

    Returns:
        Python implementation code or safety explanation

    Examples:
        # Get explanation
        shell_exec("gh issue view 348")

        # Get executable code
        shell_exec("ls -la", return_code=True)
    """
    from kagura.core.shell_safety import check_command_safety

    safety = await check_command_safety(command)

    if return_code:
        # Return executable Python code
        return f"""import subprocess
result = subprocess.run(
    {repr(command)},
    shell=True,
    cwd={repr(working_dir)},
    capture_output=True,
    text=True
)
print(result.stdout if result.returncode == 0 else result.stderr)
"""

    # Return explanation with safety analysis
    explanation = f"""# Command: {command}
# Working Dir: {working_dir}
# Safety: {safety.level.value}

{safety.reasoning}

## Python Implementation
```python
import subprocess
result = subprocess.run({repr(command)}, shell=True, cwd={repr(working_dir)},
                       capture_output=True, text=True)
print(result.stdout if result.returncode == 0 else result.stderr)
```
"""

    if safety.risks:
        explanation += "\n## Risks\n" + "\n".join(f"- {r}" for r in safety.risks)

    if safety.safe_alternative:
        explanation += f"\n\n## Safer: {safety.safe_alternative}"

    return explanation
