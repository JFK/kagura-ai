"""Built-in Git agents for repository operations."""

from kagura.core.shell import ShellExecutor

# Git-only executor for security
_executor = ShellExecutor(allowed_commands=["git", "gh"])


async def git_commit(
    message: str,
    files: list[str] | None = None,
    all: bool = False,
) -> str:
    """Create a git commit.

    Args:
        message: Commit message
        files: Specific files to commit (optional)
        all: Commit all changes (git commit -a)

    Returns:
        Git commit output

    Examples:
        >>> await git_commit("feat: add new feature", files=["src/main.py"])
        >>> await git_commit("fix: bug fix", all=True)
    """
    results = []

    # Add files
    if files:
        for file in files:
            result = await _executor.exec(f"git add {file}")
            results.append(result.stdout)
    elif all:
        result = await _executor.exec("git add -A")
        results.append(result.stdout)

    # Commit
    # Escape double quotes in message
    escaped_message = message.replace('"', '\\"')
    result = await _executor.exec(f'git commit -m "{escaped_message}"')
    results.append(result.stdout)

    return "\n".join(filter(None, results))


async def git_push(remote: str = "origin", branch: str | None = None) -> str:
    """Push commits to remote repository.

    Args:
        remote: Remote name (default: origin)
        branch: Branch name (default: current branch)

    Returns:
        Git push output

    Examples:
        >>> await git_push()
        >>> await git_push(remote="origin", branch="main")
    """
    if branch:
        cmd = f"git push {remote} {branch}"
    else:
        cmd = f"git push {remote}"

    result = await _executor.exec(cmd)
    return result.stdout


async def git_status() -> str:
    """Get git repository status.

    Returns:
        Git status output

    Example:
        >>> status = await git_status()
        >>> print(status)
    """
    result = await _executor.exec("git status")
    return result.stdout


async def git_create_pr(
    title: str,
    body: str,
    base: str = "main",
) -> str:
    """Create a pull request using GitHub CLI.

    Requires: GitHub CLI (gh) installed and authenticated

    Args:
        title: PR title
        body: PR description
        base: Base branch (default: main)

    Returns:
        PR URL

    Example:
        >>> pr_url = await git_create_pr(
        ...     title="feat: new feature",
        ...     body="This PR adds a new feature"
        ... )
    """
    # Escape quotes in title and body
    escaped_title = title.replace('"', '\\"')
    escaped_body = body.replace('"', '\\"')

    cmd = (
        f'gh pr create --title "{escaped_title}" --body "{escaped_body}" --base {base}'
    )
    result = await _executor.exec(cmd)
    return result.stdout
