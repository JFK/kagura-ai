"""Built-in MCP tools for File and Directory operations

Exposes file/directory operations via MCP for Claude Desktop.
"""

from __future__ import annotations

import json
from pathlib import Path

from kagura import tool


@tool
def file_read(path: str, encoding: str = "utf-8") -> str:
    """Read file content

    Args:
        path: File path
        encoding: File encoding (default: utf-8)

    Returns:
        File content
    """
    try:
        return Path(path).read_text(encoding=encoding)
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def file_write(path: str, content: str, encoding: str = "utf-8") -> str:
    """Write content to file

    Args:
        path: File path
        content: Content to write
        encoding: File encoding (default: utf-8)

    Returns:
        Confirmation message
    """
    try:
        Path(path).write_text(content, encoding=encoding)
        return f"Wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def dir_list(path: str = ".", pattern: str = "*") -> str:
    """List directory contents

    Args:
        path: Directory path (default: current directory)
        pattern: Glob pattern (default: *)

    Returns:
        JSON string of file list
    """
    try:
        files = [str(f.relative_to(path)) for f in Path(path).glob(pattern)]
        return json.dumps(sorted(files), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def shell_exec(command: str) -> str:
    """Execute shell command safely

    Args:
        command: Shell command

    Returns:
        Command output or error message
    """
    try:
        from kagura.core.shell import ShellExecutor

        executor = ShellExecutor()
        result = await executor.exec(command)

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error executing command: {e}"
