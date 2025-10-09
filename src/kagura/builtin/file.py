"""Built-in file agents for file operations."""

from kagura.core.shell import ShellExecutor

# File-operations-only executor for security
_executor = ShellExecutor(allowed_commands=["find", "grep", "ls", "cat"])


async def file_search(
    pattern: str,
    directory: str = ".",
    file_type: str = "*",
) -> list[str]:
    """Search for files matching pattern.

    Args:
        pattern: File name pattern to search for
        directory: Directory to search in (default: current directory)
        file_type: File extension filter (e.g., "*.py", "*.txt")

    Returns:
        List of matching file paths

    Examples:
        >>> files = await file_search("test", directory="./tests", file_type="*.py")
        >>> files = await file_search("config", file_type="*.json")
    """
    # Build find command
    cmd = f'find {directory} -name "{file_type}" -type f'

    # Add grep filter if pattern is not "*"
    if pattern != "*":
        cmd += f' | grep "{pattern}"'

    result = await _executor.exec(cmd)

    if not result.stdout.strip():
        return []

    return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]


async def grep_content(pattern: str, files: list[str]) -> dict[str, list[str]]:
    """Search for content in files.

    Args:
        pattern: Text pattern to search for
        files: List of file paths to search in

    Returns:
        Dictionary mapping file paths to matching lines

    Example:
        >>> results = await grep_content("TODO", ["src/main.py", "src/utils.py"])
        >>> for file, lines in results.items():
        ...     print(f"{file}: {len(lines)} matches")
    """
    results: dict[str, list[str]] = {}

    for file in files:
        # Use grep with line numbers
        cmd = f'grep -n "{pattern}" {file}'

        try:
            result = await _executor.exec(cmd)

            if result.stdout.strip():
                lines = [
                    line.strip()
                    for line in result.stdout.strip().split("\n")
                    if line.strip()
                ]
                if lines:
                    results[file] = lines
        except Exception:
            # grep returns non-zero exit code if no matches found
            # This is expected, so we skip this file
            continue

    return results
