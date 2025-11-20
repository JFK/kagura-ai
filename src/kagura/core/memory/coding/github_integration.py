"""GitHub integration module for coding memory.

This module provides GitHub Issue and PR integration for coding sessions.
Extracted from manager.py as part of Phase 3.5.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kagura.core.memory.coding.manager import CodingMemoryManager

logger = logging.getLogger(__name__)


async def link_session_to_github_issue(
    self: CodingMemoryManager, issue_number: int, session_id: str | None = None
) -> str:
    """Link coding session to GitHub issue.

    Fetches issue details via gh CLI and enriches session context.

    Args:
        issue_number: GitHub issue number
        session_id: Session ID (default: current active session)

    Returns:
        Confirmation message with issue details

    Raises:
        RuntimeError: If no active session and session_id not provided
        ValueError: If gh command fails

    Example:
        >>> result = await coding_mem.link_session_to_github_issue(464)
        >>> print(result)
        ✅ Linked session to GitHub issue #464: Implement Coding Memory
    """
    from kagura.builtin.git import gh_issue_get

    # Use current session if not specified
    session_id = session_id or self.current_session_id
    if not session_id:
        raise RuntimeError(
            "No active session to link. "
            "Start a session first with start_coding_session()"
        )

    # Fetch issue details from GitHub
    try:
        issue = await gh_issue_get(issue_number)
    except Exception as e:
        logger.error(f"Failed to fetch GitHub issue #{issue_number}: {e}")
        raise ValueError(
            f"Could not fetch issue #{issue_number}. "
            f"Make sure gh CLI is authenticated (run 'gh auth login')"
        ) from e

    # Prepare issue context
    labels = [label["name"] for label in issue.get("labels", [])]
    assignees = [a["login"] for a in issue.get("assignees", [])]

    issue_context = {
        "github_issue": issue_number,
        "github_title": issue["title"],
        "github_url": issue["url"],
        "github_state": issue["state"],
        "github_labels": labels,
        "github_assignees": assignees,
    }

    # Update session with GitHub context
    session_key = self._make_key(f"session:{session_id}")
    session_data = self.persistent.recall(key=session_key, user_id=self.user_id)

    if session_data:
        session_data["github_context"] = issue_context
        self.persistent.store(
            key=session_key,
            value=session_data,
            user_id=self.user_id,
        )

        # Also update persistent cache if active session
        if session_id == self.current_session_id:
            self.persistent.store(
                f"session:{session_id}",
                json.dumps(session_data),
                self.user_id,
                agent_name="coding_sessions"
            )

    # Add to graph if available
    if self.graph:
        # Create GitHub issue node (using helper)
        issue_node_id = f"gh_issue_{issue_number}"

        self._ensure_graph_node(
            node_id=issue_node_id,
            node_type="github_issue",
            data={
                "issue_number": issue_number,
                "title": issue["title"],
                "url": issue["url"],
                "state": issue["state"],
            },
        )

        # Link session to issue
        self.graph.add_edge(
            src_id=session_id,
            dst_id=issue_node_id,
            rel_type="addresses",
            weight=1.0,
        )

    logger.info(f"Linked session {session_id} to GitHub issue #{issue_number}")

    return (
        f"✅ Linked session to GitHub issue #{issue_number}\n"
        f"Title: {issue['title']}\n"
        f"URL: {issue['url']}\n"
        f"State: {issue['state']}\n"
        f"Labels: {', '.join(labels) if labels else 'None'}"
    )


async def auto_link_github_issue(self: CodingMemoryManager) -> str | None:
    """Auto-detect and link GitHub issue from branch name.

    Extracts issue number from current branch (e.g., 464-feat-... → #464)
    and links to current session.

    Returns:
        Confirmation message if issue detected and linked, None otherwise

    Example:
        >>> # On branch: 464-featmemory-...
        >>> result = await coding_mem.auto_link_github_issue()
        >>> print(result)
        ✅ Linked session to GitHub issue #464: ...
    """
    from kagura.builtin.git import gh_extract_issue_from_branch

    try:
        issue_num = await gh_extract_issue_from_branch()

        if issue_num:
            return await self.link_session_to_github_issue(issue_num)  # type: ignore[misc]
        else:
            logger.info("No issue number detected in branch name")
            return None

    except Exception as e:
        logger.warning(f"Auto-link GitHub issue failed: {e}")
        return None


async def generate_pr_description(self: CodingMemoryManager) -> str:
    """Generate PR description from current session.

    Uses AI to summarize session activities into PR-ready format.

    Returns:
        Markdown-formatted PR description

    Raises:
        RuntimeError: If no active session

    Example:
        >>> pr_desc = await coding_mem.generate_pr_description()
        >>> # Use with: gh pr create --title "..." --body "$(cat <<EOF...)"
    """
    if not self.current_session_id:
        raise RuntimeError(
            "No active session. Start a session to generate PR description."
        )

    # Gather session data from persistent storage
    session_data_str = self.persistent.recall(
        f"session:{self.current_session_id}", self.user_id, agent_name="coding_sessions"
    )
    if not session_data_str:
        raise RuntimeError(f"Session data not found: {self.current_session_id}")

    try:
        session_data = json.loads(session_data_str) if isinstance(session_data_str, str) else session_data_str
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid session data format: {self.current_session_id}")

    file_changes = await self._get_session_file_changes(self.current_session_id)
    decisions = await self._get_session_decisions(self.current_session_id)
    errors = await self._get_session_errors(self.current_session_id)

    # Get GitHub context if available
    github_context = session_data.get("github_context")
    related_issue = github_context.get("github_issue") if github_context else None

    # Generate PR description using LLM
    pr_desc = await self.coding_analyzer.generate_pr_description(
        session_description=session_data.get("description"),
        file_changes=file_changes,
        decisions=decisions,
        errors_fixed=[e for e in errors if e.resolved],
        related_issue=related_issue,
    )

    return pr_desc
