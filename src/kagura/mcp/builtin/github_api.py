"""GitHub REST API tools for remote MCP access.

These tools use GitHub REST API directly (not gh CLI), making them safe
for remote access via MCP servers.
"""

from typing import Any

from kagura import tool
from kagura.config.env import get_github_token


async def _get_github_repo_info() -> tuple[str, str] | str:
    """Get owner/repo from git remote.

    Returns:
        Tuple of (owner, repo) on success, error message string on failure
    """
    from pathlib import Path

    from kagura.core.shell import ShellExecutor

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
async def github_issue_view_api(issue_number: int) -> str:
    """Get GitHub issue details using REST API.

    Safe for remote access - uses GitHub REST API.

    Args:
        issue_number: Issue number

    Returns:
        Issue details as formatted text

    Example:
        github_issue_view_api(348)
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

    # Make API request
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers)

            if response.status_code == 200:
                issue_data = response.json()

                # Format nicely for display
                output = f"# Issue #{issue_number}: {issue_data.get('title', 'N/A')}\n\n"
                output += f"**State:** {issue_data.get('state', 'N/A')}\n"
                output += f"**Author:** {issue_data.get('user', {}).get('login', 'N/A')}\n"

                labels = issue_data.get("labels", [])
                if labels:
                    label_names = [label.get("name", "") for label in labels]
                    output += f"**Labels:** {', '.join(label_names)}\n"

                output += f"\n## Description\n\n{issue_data.get('body', 'No description')}\n"

                return output
            else:
                error_msg = response.text
                return f"Error fetching issue (HTTP {response.status_code}): {error_msg}"

    except Exception as e:
        return f"Error making API request: {e}"


@tool
async def github_issue_list_api(state: str = "open", limit: int = 30) -> str:
    """List GitHub issues using REST API.

    Safe for remote access - uses GitHub REST API.

    Args:
        state: Issue state (open, closed, all)
        limit: Maximum issues to return

    Returns:
        Formatted issue list

    Example:
        github_issue_list_api("open", 10)
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

    # Make API request
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {"state": state, "per_page": limit}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers, params=params)

            if response.status_code == 200:
                issues = response.json()

                if not issues:
                    return f"No {state} issues found."

                output = f"# {state.capitalize()} Issues ({len(issues)})\n\n"

                for issue in issues:
                    labels = issue.get("labels", [])
                    label_str = (
                        ", ".join(label.get("name", "") for label in labels)
                        if labels
                        else ""
                    )

                    output += (
                        f"- **#{issue.get('number')}** {issue.get('title', 'N/A')}"
                    )
                    if label_str:
                        output += f" [{label_str}]"
                    output += f" ({issue.get('state', 'N/A')})\n"

                return output
            else:
                error_msg = response.text
                return f"Error fetching issues (HTTP {response.status_code}): {error_msg}"

    except Exception as e:
        return f"Error making API request: {e}"


@tool
async def github_pr_view_api(pr_number: int) -> str:
    """Get GitHub PR details using REST API.

    Safe for remote access - uses GitHub REST API.

    Args:
        pr_number: PR number

    Returns:
        PR details as formatted text

    Example:
        github_pr_view_api(465)
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

    # Make API request
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers)

            if response.status_code == 200:
                pr_data = response.json()

                # Format nicely
                output = f"# PR #{pr_number}: {pr_data.get('title', 'N/A')}\n\n"
                output += f"**State:** {pr_data.get('state', 'N/A')}\n"
                output += f"**Author:** {pr_data.get('user', {}).get('login', 'N/A')}\n"
                output += f"**Mergeable:** {pr_data.get('mergeable', 'N/A')}\n"
                output += (
                    f"**Base:** {pr_data.get('base', {}).get('ref', 'N/A')} ← "
                    f"**Head:** {pr_data.get('head', {}).get('ref', 'N/A')}\n"
                )

                output += f"\n## Description\n\n{pr_data.get('body', 'No description')}\n"

                return output
            else:
                error_msg = response.text
                return f"Error fetching PR (HTTP {response.status_code}): {error_msg}"

    except Exception as e:
        return f"Error making API request: {e}"


@tool
async def github_pr_create_api(
    title: str,
    head: str,
    base: str = "main",
    body: str = "",
    draft: bool = True,
) -> str:
    """Create GitHub PR using REST API.

    Safe for remote access - uses GitHub REST API.

    Args:
        title: PR title (required)
        head: Branch name to merge from (required)
        base: Branch name to merge into (default: main)
        body: PR description (optional)
        draft: Create as draft PR (default: True)

    Returns:
        Created PR details (number, URL, etc.)

    Example:
        github_pr_create_api("feat: Add feature", "feature-branch", body="Description")
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
    payload: dict[str, Any] = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
        "draft": draft,
    }

    # Make API request
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers)

            if response.status_code == 201:
                pr_data = response.json()
                pr_number = pr_data["number"]
                pr_url = pr_data["html_url"]

                output = f"✓ Created PR #{pr_number}\n"
                output += f"URL: {pr_url}\n"
                output += f"Title: {title}\n"
                output += f"Base: {base} ← Head: {head}\n"
                output += f"Draft: {draft}\n"

                return output
            else:
                error_msg = response.text
                return f"Error creating PR (HTTP {response.status_code}): {error_msg}"

    except Exception as e:
        return f"Error making API request: {e}"


@tool
async def github_pr_merge_api(
    pr_number: int,
    merge_method: str = "squash",
    commit_title: str | None = None,
    commit_message: str | None = None,
) -> str:
    """Merge GitHub PR using REST API.

    Safe for remote access - uses GitHub REST API.

    IMPORTANT: This performs the actual merge. Use with caution.

    Args:
        pr_number: PR number to merge (required)
        merge_method: Merge method (squash, merge, rebase) (default: squash)
        commit_title: Optional custom commit title
        commit_message: Optional custom commit message

    Returns:
        Merge result

    Example:
        github_pr_merge_api(465, merge_method="squash")
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
    payload: dict[str, Any] = {"merge_method": merge_method}

    if commit_title:
        payload["commit_title"] = commit_title

    if commit_message:
        payload["commit_message"] = commit_message

    # Make API request
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/merge"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(api_url, json=payload, headers=headers)

            if response.status_code == 200:
                merge_data = response.json()

                output = f"✓ Merged PR #{pr_number}\n"
                output += f"SHA: {merge_data.get('sha', 'N/A')}\n"
                output += f"Merged: {merge_data.get('merged', False)}\n"
                output += f"Message: {merge_data.get('message', 'N/A')}\n"

                return output
            else:
                error_msg = response.text
                return f"Error merging PR (HTTP {response.status_code}): {error_msg}"

    except Exception as e:
        return f"Error making API request: {e}"
