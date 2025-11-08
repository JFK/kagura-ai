"""GitHub MCP tools for Claude Desktop integration.

These tools provide GitHub operations via MCP (Model Context Protocol),
allowing Claude Desktop to interact with GitHub safely.

All tools use the underlying GitHub agents with safety controls.
"""

import logging
from pathlib import Path
from typing import Any

from kagura import tool
from kagura.config.env import get_github_token
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
    github_token = get_github_token()
    if not github_token:
        return "Error: GITHUB_TOKEN environment variable not set"

    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }


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


