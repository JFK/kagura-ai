"""GitHub Issue recorder for external memory integration.

Implements 2-stage recording strategy:
1. Immediate: High importance events → concise GitHub comment (async)
2. Session end: Full LLM summary → comprehensive GitHub comment
"""

import asyncio
import logging
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GitHubRecordConfig(BaseModel):
    """Configuration for GitHub recording.

    Attributes:
        repo: Repository in format "owner/repo" (None = auto-detect)
        auto_detect_issue: Auto-detect issue from branch name
        enabled: Enable GitHub recording (default: True)
    """

    repo: str | None = None
    auto_detect_issue: bool = True
    enabled: bool = True


class GitHubRecorder:
    """Record coding activities to GitHub Issues.

    Two-stage recording:
    - Stage 1: Immediate recording of high importance events (async, non-blocking)
    - Stage 2: Session-end comprehensive summary (blocking, full context)

    Uses `gh` CLI for GitHub API access.

    Attributes:
        config: GitHub recording configuration
        current_issue_number: Current issue number (auto-detected or manual)
    """

    def __init__(self, config: GitHubRecordConfig | None = None) -> None:
        """Initialize GitHub recorder.

        Args:
            config: GitHub recording configuration
        """
        self.config = config or GitHubRecordConfig()
        self.current_issue_number: int | None = None

        if self.config.auto_detect_issue:
            self._auto_detect_issue()

        logger.info(
            f"GitHubRecorder initialized: issue={self.current_issue_number}, "
            f"enabled={self.config.enabled}"
        )

    def _auto_detect_issue(self) -> None:
        """Auto-detect issue number from current git branch.

        Expected branch format: {issue_number}-{description}
        Example: 493-featmemory-unify-coding-memory
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            branch_name = result.stdout.strip()

            # Extract issue number (first number in branch name)
            if branch_name and branch_name[0].isdigit():
                issue_str = branch_name.split("-")[0]
                self.current_issue_number = int(issue_str)
                logger.info(
                    f"Auto-detected issue #{self.current_issue_number} "
                    f"from branch '{branch_name}'"
                )
        except Exception as e:
            logger.debug(f"Could not auto-detect issue number: {e}")

    def set_issue_number(self, issue_number: int) -> None:
        """Manually set target issue number.

        Args:
            issue_number: GitHub issue number
        """
        self.current_issue_number = issue_number
        logger.info(f"Issue number set to #{issue_number}")

    async def record_important_event(
        self,
        interaction_record: Any,
        event_type: str = "discovery",
    ) -> bool:
        """Record high importance event to GitHub (Stage 1: Immediate).

        Non-blocking async operation.

        Args:
            interaction_record: InteractionRecord instance
            event_type: Event type (discovery, decision, error_fix)

        Returns:
            True if successfully recorded
        """
        if not self.config.enabled or not self.current_issue_number:
            logger.debug(
                f"GitHub recording skipped: enabled={self.config.enabled}, "
                f"issue={self.current_issue_number}"
            )
            return False

        try:
            # Generate concise comment
            comment = self._format_immediate_comment(interaction_record, event_type)

            # Post comment via gh CLI (async)
            await self._post_comment(comment)

            logger.info(
                f"Recorded important event to issue "
                f"#{self.current_issue_number}: {event_type}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to record important event to GitHub: {e}")
            return False

    @staticmethod
    def _format_timestamp() -> str:
        """Generate UTC timestamp string.

        Returns:
            Formatted timestamp (YYYY-MM-DD HH:MM UTC)
        """
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def _format_immediate_comment(
        self, interaction_record: Any, event_type: str
    ) -> str:
        """Format concise comment for immediate recording.

        Args:
            interaction_record: InteractionRecord instance
            event_type: Event type

        Returns:
            Markdown-formatted comment
        """
        timestamp = self._format_timestamp()

        # Emoji mapping
        emoji_map = {
            "discovery": "💡",
            "decision": "🎯",
            "error_fix": "🐛",
            "struggle": "🤔",
            "implementation": "⚙️",
        }
        emoji = emoji_map.get(event_type, "📝")

        # Extract key info
        query_preview = interaction_record.user_query[:200]
        response_preview = interaction_record.ai_response[:200]
        q_ellipsis = "..." if len(interaction_record.user_query) > 200 else ""
        r_ellipsis = "..." if len(interaction_record.ai_response) > 200 else ""

        comment = f"""### {emoji} {event_type.replace("_", " ").title()} ({timestamp})

**Query:** {query_preview}{q_ellipsis}

**Response:** {response_preview}{r_ellipsis}

**Importance:** {interaction_record.importance:.1f}/10

---
🤖 Auto-recorded by Kagura (importance: {interaction_record.importance:.1f}/10)
"""
        return comment

    async def record_session_summary(
        self,
        session_id: str,
        summary_data: dict[str, Any],
        llm_summary: str | None = None,
    ) -> bool:
        """Record comprehensive session summary to GitHub (Stage 2: Session end).

        Blocking operation (intended for session end).

        Args:
            session_id: Coding session ID
            summary_data: Session statistics and data
            llm_summary: LLM-generated summary (optional)

        Returns:
            True if successfully recorded
        """
        if not self.config.enabled or not self.current_issue_number:
            logger.debug("GitHub session summary recording skipped")
            return False

        try:
            # Generate comprehensive comment
            comment = self._format_session_comment(
                session_id, summary_data, llm_summary
            )

            # Post comment via gh CLI
            await self._post_comment(comment)

            logger.info(
                f"Recorded session summary to issue "
                f"#{self.current_issue_number}: {session_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to record session summary to GitHub: {e}")
            return False

    def _format_session_comment(
        self,
        session_id: str,
        summary_data: dict[str, Any],
        llm_summary: str | None,
    ) -> str:
        """Format comprehensive session summary comment.

        Args:
            session_id: Coding session ID
            summary_data: Session statistics
            llm_summary: LLM-generated summary

        Returns:
            Markdown-formatted comment
        """
        timestamp = self._format_timestamp()

        # Extract data
        total_interactions = summary_data.get("total_interactions", 0)
        by_type = summary_data.get("by_type", {})
        changes = summary_data.get("file_changes", [])
        decisions = summary_data.get("decisions", [])
        errors = summary_data.get("errors", [])

        comment = f"""## 🤖 Claude Code Session Summary

**Session ID:** `{session_id}`
**End Time:** {timestamp}
**Total Interactions:** {total_interactions}

### 📊 Activity Breakdown
"""

        # Interaction types
        if by_type:
            comment += "\n**Interactions by type:**\n"
            for itype, count in by_type.items():
                comment += f"- {itype}: {count}\n"

        # File changes
        if changes:
            comment += f"\n### 📝 File Changes ({len(changes)})\n"
            for change in changes[:10]:  # Limit to 10
                fp = change.get("file_path")
                action = change.get("action")
                reason = change.get("reason", "")[:80]
                comment += f"- `{fp}`: {action} - {reason}...\n"
            if len(changes) > 10:
                comment += f"\n_... and {len(changes) - 10} more changes_\n"

        # Decisions
        if decisions:
            comment += f"\n### 🎯 Design Decisions ({len(decisions)})\n"
            for decision in decisions[:5]:  # Limit to 5
                comment += f"- **{decision.get('decision', 'N/A')[:100]}**\n"
                comment += (
                    f"  - Rationale: {decision.get('rationale', 'N/A')[:150]}...\n"
                )
            if len(decisions) > 5:
                comment += f"\n_... and {len(decisions) - 5} more decisions_\n"

        # Errors
        if errors:
            comment += f"\n### 🐛 Errors Fixed ({len(errors)})\n"
            for error in errors[:5]:  # Limit to 5
                comment += (
                    f"- `{error.get('error_type')}`: {error.get('message')[:80]}...\n"
                )
                if error.get("solution"):
                    comment += f"  - Solution: {error.get('solution')[:100]}...\n"

        # LLM summary
        if llm_summary:
            comment += f"\n### 🧠 AI Summary\n\n{llm_summary}\n"

        comment += """
---
🤖 Auto-generated by Kagura Coding Memory
https://github.com/JFK/kagura-ai
"""

        return comment

    async def _post_comment(self, comment: str) -> None:
        """Post comment to GitHub issue via gh CLI.

        Uses --body-file for safety and reliability with complex content.
        This avoids special character escaping issues and command-line length limits.

        Args:
            comment: Markdown comment text

        Raises:
            subprocess.CalledProcessError: If gh command fails
            ValueError: If no issue number is set
        """
        if not self.current_issue_number:
            raise ValueError("No issue number set")

        # Create temporary markdown file with unique name
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / f"kagura_comment_{uuid.uuid4().hex[:8]}.md"

        try:
            # Write content to temp file
            temp_file.write_text(comment, encoding="utf-8")
            logger.debug(f"Created temp comment file: {temp_file}")

            # Use --body-file instead of --body
            cmd = [
                "gh",
                "issue",
                "comment",
                str(self.current_issue_number),
                "--body-file",
                str(temp_file),
            ]

            if self.config.repo:
                cmd.extend(["--repo", self.config.repo])

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, check=True, capture_output=True, text=True),
            )
            logger.debug(f"Successfully posted comment from {temp_file}")

        finally:
            # Always cleanup temp file
            if temp_file.exists():
                temp_file.unlink()
                logger.debug(f"Cleaned up temp file: {temp_file}")

    def is_available(self) -> bool:
        """Check if GitHub recording is available.

        Returns:
            True if gh CLI is installed and issue number is set
        """
        if not self.config.enabled:
            return False

        # Check gh CLI availability
        try:
            subprocess.run(
                ["gh", "--version"], capture_output=True, check=True, timeout=5
            )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            logger.warning("gh CLI not available")
            return False

        # Check issue number
        if not self.current_issue_number:
            logger.debug("No GitHub issue number set")
            return False

        return True
