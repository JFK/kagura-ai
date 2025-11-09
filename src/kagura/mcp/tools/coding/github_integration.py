"""GitHub integration MCP tools.

Links coding sessions to GitHub issues and generates PR descriptions.
"""

from __future__ import annotations

from kagura import tool
from kagura.mcp.builtin.common import to_int
from kagura.mcp.tools.coding.common import get_coding_memory


@tool
async def coding_link_github_issue(
    user_id: str,
    project_id: str,
    issue_number: str | int | None = None,
) -> str:
    """Link current coding session to a GitHub issue for context tracking.

    Auto-detects issue number from branch name if not provided
    (e.g., 464-feat-... → #464).
    Fetches issue details via gh CLI and enriches session with title, labels, assignees.

    Requires: gh CLI authenticated (`gh auth login`)

    Args:
        user_id: User identifier
        project_id: Project identifier
        issue_number: GitHub issue number (auto-detect from branch if None)

    Returns:
        Confirmation with issue details

    Raises:
        Error if no active session or gh CLI fails

    Examples:
        # Auto-detect from branch name
        await coding_link_github_issue(
            user_id="dev_john",
            project_id="kagura-ai"
        )

        # Explicit issue number
        await coding_link_github_issue(
            user_id="dev_john",
            project_id="kagura-ai",
            issue_number=464
        )
    """
    from kagura.builtin.git import gh_extract_issue_from_branch

    memory = get_coding_memory(user_id, project_id)

    # Convert issue_number to int if provided
    if issue_number is not None:
        issue_number = to_int(
            issue_number, default=0, min_val=1, param_name="issue_number"
        )
        if issue_number == 0:
            issue_number = None  # Invalid number, treat as None

    # Auto-detect if not provided
    if issue_number is None:
        try:
            issue_number = await gh_extract_issue_from_branch()
        except Exception as e:
            return (
                f"❌ Could not auto-detect issue number: {e}\n\n"
                f"Branch name should start with issue number (e.g., '464-feat-...').\n"
                f"Please provide issue_number explicitly."
            )

        if issue_number is None:
            return (
                "❌ Could not detect issue number from branch name.\n\n"
                "Branch name should follow GitHub convention: "
                "{{issue}}-{{description}}\n"
                "Example: '464-feat-implement-memory'\n\n"
                "Please provide issue_number explicitly or rename your branch."
            )

    # Link to issue
    try:
        result = await memory.link_session_to_github_issue(issue_number)
        return result
    except ValueError as e:
        return (
            f"❌ Failed to link to issue #{issue_number}\n\n"
            f"Error: {e}\n\n"
            f"Make sure:\n"
            f"- gh CLI is installed and authenticated (`gh auth login`)\n"
            f"- Issue #{issue_number} exists in this repository\n"
            f"- You have permission to view the issue"
        )
    except RuntimeError as e:
        return f"❌ {e}"


@tool
async def coding_generate_pr_description(
    user_id: str,
    project_id: str,
) -> str:
    """Generate AI-powered PR description from current session activities.

    Analyzes all tracked changes, decisions, and errors to create a comprehensive
    PR description following best practices.

    Includes:
    - Summary of changes (what and why)
    - Key technical decisions with rationale
    - Files modified and reasons
    - Testing recommendations
    - Related issues (if linked)

    Requires active coding session with tracked activities.

    Args:
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Formatted PR description (markdown)

    Raises:
        Error if no active session

    Examples:
        # Generate PR description for current session
        pr_desc = await coding_generate_pr_description(
            user_id="dev_john",
            project_id="kagura-ai"
        )

        # Use with gh CLI:
        # gh pr create --title "feat: ..." --body "$pr_desc"
    """
    memory = get_coding_memory(user_id, project_id)

    try:
        pr_desc = await memory.generate_pr_description()

        return (
            "📝 Generated PR Description:\n\n"
            "```markdown\n"
            f"{pr_desc}\n"
            "```\n\n"
            "💡 **Usage:**\n"
            "1. Copy the markdown above\n"
            '2. Use with: `gh pr create --title "..." --body "<paste here>"`\n'
            "3. Or save to file and use: `gh pr create --body-file pr_desc.md`"
        )

    except RuntimeError as e:
        return (
            f"❌ Error: {e}\n\nStart a coding session first with coding_start_session()"
        )


@tool
async def coding_get_issue_context(
    issue_number: str | int,
) -> str:
    """Get GitHub issue details for coding context.

    Fetches issue title, description, labels, and assignees using gh CLI.
    Useful at session start to understand requirements.

    Requires: gh CLI authenticated (`gh auth login`)

    Args:
        issue_number: GitHub issue number

    Returns:
        Formatted issue details (markdown)

    Examples:
        # Get issue context before starting work
        context = await coding_get_issue_context(464)
        print(context)

        # Then start session with this context
        await coding_start_session(
            description="Work on issue #464",
            tags='["issue-464"]'
        )
    """
    from kagura.builtin.git import gh_issue_get

    # Convert issue_number to int using common helper
    issue_number_int = to_int(
        issue_number, default=0, min_val=1, param_name="issue_number"
    )
    if issue_number_int == 0:
        return "❌ Error: Invalid issue number. Must be a positive integer."

    try:
        issue = await gh_issue_get(issue_number_int)

        labels = ", ".join(label["name"] for label in issue.get("labels", []))
        assignees = ", ".join(a["login"] for a in issue.get("assignees", []))

        body_preview = issue.get("body", "")[:500]
        if len(issue.get("body", "")) > 500:
            body_preview += "\n\n... (truncated)"

        return (
            f"# Issue #{issue['number']}: {issue['title']}\n\n"
            f"**URL:** {issue['url']}\n"
            f"**State:** {issue['state']}\n"
            f"**Labels:** {labels or 'None'}\n"
            f"**Assignees:** {assignees or 'None'}\n\n"
            f"## Description\n\n"
            f"{body_preview}"
        )

    except ValueError as e:
        return (
            f"❌ Failed to fetch issue #{issue_number}\n\n"
            f"Error: {e}\n\n"
            f"Make sure:\n"
            f"- gh CLI is installed and authenticated (`gh auth login`)\n"
            f"- Issue #{issue_number} exists\n"
            f"- You have permission to view it"
        )
