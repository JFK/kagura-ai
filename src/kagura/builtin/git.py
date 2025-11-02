"""Built-in Git agents for repository operations."""

import json
import re

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


async def gh_issue_get(issue_number: int) -> dict:
    """Get GitHub issue details as structured data.

    Uses gh CLI with JSON output for easy parsing.

    Args:
        issue_number: GitHub issue number

    Returns:
        Dictionary with issue data (number, title, body, url, state, labels, assignees)

    Raises:
        ValueError: If issue number is invalid or gh command fails

    Example:
        >>> issue = await gh_issue_get(464)
        >>> print(issue['title'])
        'feat(memory): Implement Coding-Specialized Memory System'
        >>> print(issue['url'])
        'https://github.com/owner/repo/issues/464'
    """
    # Validate input
    if not isinstance(issue_number, int) or issue_number < 1:
        raise ValueError(f"Invalid issue number: {issue_number}")

    # Execute gh command with JSON output
    cmd = (
        f"gh issue view {issue_number} "
        f"--json number,title,body,url,state,labels,assignees"
    )
    result = await _executor.exec(cmd)

    if not result.success:
        raise ValueError(f"Failed to fetch issue #{issue_number}: {result.stderr}")

    # Parse JSON response
    return json.loads(result.stdout)


async def gh_pr_get(pr_number: int | None = None) -> dict:
    """Get GitHub PR details as structured data.

    Uses gh CLI with JSON output. If pr_number is None, gets PR for current branch.

    Args:
        pr_number: PR number (if None, uses current branch)

    Returns:
        Dictionary with PR data (number, title, body, url, state, isDraft, headRefName)

    Raises:
        ValueError: If gh command fails

    Example:
        >>> pr = await gh_pr_get()  # Current branch
        >>> pr = await gh_pr_get(465)  # Specific PR
        >>> print(pr['title'])
        >>> print(pr['state'])  # OPEN, CLOSED, MERGED
    """
    # Build command
    if pr_number is not None:
        if not isinstance(pr_number, int) or pr_number < 1:
            raise ValueError(f"Invalid PR number: {pr_number}")
        cmd = (
            f"gh pr view {pr_number} "
            f"--json number,title,body,url,state,isDraft,headRefName"
        )
    else:
        # Get PR for current branch
        cmd = "gh pr view --json number,title,body,url,state,isDraft,headRefName"

    result = await _executor.exec(cmd)

    if not result.success:
        raise ValueError(f"Failed to fetch PR: {result.stderr}")

    return json.loads(result.stdout)


async def git_current_branch() -> str:
    """Get current git branch name.

    Returns:
        Branch name (e.g., 'main', '464-feat-implement...')

    Raises:
        ValueError: If not in a git repository

    Example:
        >>> branch = await git_current_branch()
        >>> print(branch)
        '464-featmemory-implement-coding-specialized-memory-system-phase-1-core'
    """
    result = await _executor.exec("git rev-parse --abbrev-ref HEAD")

    if not result.success:
        raise ValueError(f"Failed to get current branch: {result.stderr}")

    return result.stdout.strip()


async def git_current_commit() -> str:
    """Get current git commit hash.

    Returns:
        Full commit hash (40 characters)

    Raises:
        ValueError: If not in a git repository

    Example:
        >>> commit = await git_current_commit()
        >>> print(commit)
        'a1b2c3d4e5f6...'
    """
    result = await _executor.exec("git rev-parse HEAD")

    if not result.success:
        raise ValueError(f"Failed to get current commit: {result.stderr}")

    return result.stdout.strip()


async def gh_extract_issue_from_branch(branch_name: str | None = None) -> int | None:
    """Extract GitHub issue number from branch name.

    Follows GitHub convention: {issue_number}-{description}
    Example: "464-feat-implement..." → 464

    Args:
        branch_name: Branch name (if None, uses current branch)

    Returns:
        Issue number or None if not found

    Example:
        >>> issue_num = await gh_extract_issue_from_branch()
        >>> print(issue_num)
        464
        >>> issue_num = await gh_extract_issue_from_branch("123-bugfix")
        >>> print(issue_num)
        123
        >>> issue_num = await gh_extract_issue_from_branch("main")
        >>> print(issue_num)
        None
    """
    # Get current branch if not provided
    if branch_name is None:
        branch_name = await git_current_branch()

    # Extract issue number using regex
    # Pattern: starts with digits followed by dash
    match = re.match(r"^(\d+)-", branch_name)

    return int(match.group(1)) if match else None
