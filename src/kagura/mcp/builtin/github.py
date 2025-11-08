"""GitHub MCP tools for Claude Desktop integration.

These tools provide GitHub operations via MCP (Model Context Protocol),
allowing Claude Desktop to interact with GitHub safely.

All tools use the underlying GitHub agents with safety controls.
"""

import logging
import os
from pathlib import Path
from typing import Any

from kagura import tool
from kagura.builtin.github_agent import (
    gh_pr_create_safe,
    gh_pr_merge_safe,
    gh_safe_exec,
)
from kagura.core.shell import ShellExecutor

logger = logging.getLogger(__name__)


# Helper functions for GitHub REST API
async def _get_github_repo_info() -> tuple[str, str] | str:
    """Get owner/repo from git remote.

    Returns:
        Tuple of (owner, repo) on success, error message string on failure
    """
    try:
        executor = ShellExecutor(allowed_commands=["git"], working_dir=Path("."))
        remote_result = await executor.exec("git remote get-url origin")

        if remote_result.return_code != 0:
            return "Error: Not in a git repository or no origin remote"

        # Parse owner/repo from remote URL
        # Format: git@github.com:owner/repo.git or https://github.com/owner/repo.git
        remote_url = remote_result.stdout.strip()
        if "github.com" not in remote_url:
            return "Error: Not a GitHub repository"

        if remote_url.startswith("git@"):
            # git@github.com:owner/repo.git
            repo_path = remote_url.split(":")[1].replace(".git", "")
        else:
            # https://github.com/owner/repo.git
            repo_path = remote_url.split("github.com/")[1].replace(".git", "")

        owner, repo = repo_path.split("/")
        return (owner, repo)

    except Exception as e:
        return f"Error parsing repository info: {e}"


def _get_github_headers() -> dict[str, str] | str:
    """Get GitHub API headers with authentication.

    Returns:
        Headers dict on success, error message string on failure
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return "Error: GITHUB_TOKEN environment variable not set"

    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }


@tool
async def github_exec(gh_command: str, force: bool = False) -> str:
    """Execute GitHub CLI command with safety checks.

    This is a general-purpose GitHub command executor for MCP clients.
    Dangerous commands require force=True.

    Args:
        gh_command: GitHub CLI command (with or without 'gh' prefix)
        force: Skip safety confirmation (default: False)

    Returns:
        Command output or safety warning

    Examples:
        github_exec("issue view 348")
        github_exec("pr list --state open")
        github_exec("pr merge 465", force=True)
    """
    result = await gh_safe_exec(gh_command, auto_confirm=force)
    return result


@tool
async def github_issue_view(issue_number: int) -> str:
    """Get GitHub issue details.

    Safe, read-only operation.

    Args:
        issue_number: Issue number

    Returns:
        Issue details as formatted text

    Example:
        github_issue_view(348)
    """

    # Execute gh command directly (bypassing agent to avoid LLM call)
    import json
    from pathlib import Path

    from kagura.core.shell import ShellExecutor

    cmd = f"gh issue view {issue_number} --json number,title,body,state,labels,comments"

    try:
        executor = ShellExecutor(allowed_commands=["gh"], working_dir=Path("."))
        exec_result = await executor.exec(cmd)

        if exec_result.return_code != 0:
            return f"Error: {exec_result.stderr}"

        issue_data = json.loads(exec_result.stdout)
    except json.JSONDecodeError:
        return f"Error: Failed to parse issue data\n{exec_result.stdout}"
    except Exception as e:
        return f"Error: {e}"

    # Format nicely for display
    output = f"# Issue #{issue_number}: {issue_data.get('title', 'N/A')}\n\n"
    output += f"**State:** {issue_data.get('state', 'N/A')}\n"

    labels = issue_data.get("labels", [])
    if labels:
        label_names = [label.get("name", "") for label in labels]
        output += f"**Labels:** {', '.join(label_names)}\n"

    output += f"\n## Description\n\n{issue_data.get('body', 'No description')}\n"

    comments = issue_data.get("comments", [])
    if comments:
        output += f"\n## Comments ({len(comments)})\n\n"
        for comment in comments[:3]:  # Show first 3
            output += f"- {comment.get('body', '')[:100]}...\n"

    return output


@tool
async def github_pr_view(pr_number: int | None = None) -> str:
    """Get GitHub PR details.

    Safe, read-only operation.

    Args:
        pr_number: PR number (None = auto-detect from current branch)

    Returns:
        PR details as formatted text

    Example:
        github_pr_view(465)
        github_pr_view()  # Auto-detect from branch
    """
    # Execute gh command directly
    import json
    from pathlib import Path

    from kagura.core.shell import ShellExecutor

    if pr_number:
        cmd = f"gh pr view {pr_number} --json number,title,body,state,commits,files"
    else:
        cmd = "gh pr view --json number,title,body,state,commits,files"

    try:
        executor = ShellExecutor(allowed_commands=["gh"], working_dir=Path("."))
        exec_result = await executor.exec(cmd)

        if exec_result.return_code != 0:
            return f"Error: {exec_result.stderr}"

        pr_data = json.loads(exec_result.stdout)
    except json.JSONDecodeError:
        return f"Error: Failed to parse PR data\n{exec_result.stdout}"
    except Exception as e:
        return f"Error: {e}"

    if "error" in pr_data:
        return f"Error: {pr_data['error']}"

    # Format nicely
    pr_num = pr_data.get("number", pr_number or "N/A")
    output = f"# PR #{pr_num}: {pr_data.get('title', 'N/A')}\n\n"
    output += f"**State:** {pr_data.get('state', 'N/A')}\n"

    commits = pr_data.get("commits", [])
    if commits:
        output += f"**Commits:** {len(commits)}\n"

    files = pr_data.get("files", [])
    if files:
        output += f"**Files Changed:** {len(files)}\n"

    output += f"\n## Description\n\n{pr_data.get('body', 'No description')}\n"

    return output


@tool
async def github_issue_list(state: str = "open", limit: int = 30) -> str:
    """List GitHub issues.

    Safe, read-only operation.

    Args:
        state: Issue state (open, closed, all)
        limit: Maximum issues to return

    Returns:
        Formatted issue list

    Example:
        github_issue_list("open", 10)
    """
    # Execute gh command directly
    import json
    from pathlib import Path

    from kagura.core.shell import ShellExecutor

    cmd = (
        f"gh issue list --state {state} --limit {limit} "
        f"--json number,title,state,labels"
    )

    try:
        executor = ShellExecutor(allowed_commands=["gh"], working_dir=Path("."))
        exec_result = await executor.exec(cmd)

        if exec_result.return_code != 0:
            return f"Error: {exec_result.stderr}"

        issues = json.loads(exec_result.stdout)
    except json.JSONDecodeError:
        return f"Error: Failed to parse issues\n{exec_result.stdout}"
    except Exception as e:
        return f"Error: {e}"

    if not issues:
        return f"No {state} issues found."

    output = f"# {state.capitalize()} Issues ({len(issues)})\n\n"

    for issue in issues:
        labels = issue.get("labels", [])
        label_str = (
            ", ".join(label.get("name", "") for label in labels) if labels else ""
        )

        output += f"- **#{issue.get('number')}** {issue.get('title', 'N/A')}"
        if label_str:
            output += f" [{label_str}]"
        output += f" ({issue.get('state', 'N/A')})\n"

    return output


@tool
async def github_pr_create(
    title: str, body: str, draft: bool = True, force: bool = False
) -> str:
    """Create GitHub PR.

    Requires force=True for confirmation.

    Args:
        title: PR title
        body: PR description
        draft: Create as draft (default: True, safer)
        force: Confirm creation (default: False)

    Returns:
        PR creation result or confirmation prompt

    Example:
        github_pr_create("feat: Add feature", "Description", draft=True, force=True)
    """
    result = await gh_pr_create_safe(title, body, draft=draft, auto_confirm=force)
    return result


@tool
async def github_issue_create(
    title: str,
    body: str = "",
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
) -> str:
    """Create GitHub issue using REST API.

    Safe for remote access - uses GitHub API with token authentication.

    Args:
        title: Issue title (required)
        body: Issue body/description (optional)
        labels: List of label names to apply (optional)
        assignees: List of GitHub usernames to assign (optional)

    Returns:
        Created issue details (number, URL, etc.)

    Example:
        github_issue_create("Bug: Memory leak", "Description here", labels=["bug"])
        github_issue_create("feat: New feature", assignees=["username"])
    """
    try:
        import httpx
    except ImportError:
        return "Error: httpx not installed. Install with: pip install kagura-ai[web]"

    # Get repository info
    repo_info = await _get_github_repo_info()
    if isinstance(repo_info, str):
        return repo_info
    owner, repo = repo_info

    # Get headers
    headers = _get_github_headers()
    if isinstance(headers, str):
        return headers

    # Build request payload
    payload: dict[str, Any] = {"title": title, "body": body}

    if labels:
        payload["labels"] = labels

    if assignees:
        payload["assignees"] = assignees

    # Make API request
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers)

            if response.status_code == 201:
                issue_data = response.json()
                issue_number = issue_data["number"]
                issue_url = issue_data["html_url"]

                output = f"✓ Created issue #{issue_number}\n"
                output += f"URL: {issue_url}\n"
                output += f"Title: {title}\n"

                if labels:
                    output += f"Labels: {', '.join(labels)}\n"

                if assignees:
                    output += f"Assignees: {', '.join(assignees)}\n"

                return output
            else:
                error_msg = response.text
                return f"Error creating issue (HTTP {response.status_code}): {error_msg}"

    except Exception as e:
        return f"Error making API request: {e}"


@tool
async def github_pr_merge(
    pr_number: int, squash: bool = True, force: bool = False
) -> str:
    """Merge GitHub PR.

    DANGEROUS: Requires force=True for confirmation.

    Args:
        pr_number: PR number to merge
        squash: Use squash merge (default: True)
        force: Confirm merge (default: False) - REQUIRED

    Returns:
        Merge result or confirmation prompt

    Example:
        github_pr_merge(465)  # Returns warning
        github_pr_merge(465, force=True)  # Executes merge
    """
    result = await gh_pr_merge_safe(pr_number, squash=squash, auto_confirm=force)
    return result
