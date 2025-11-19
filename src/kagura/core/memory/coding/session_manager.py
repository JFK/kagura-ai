"""Session management module for coding memory.

This module provides coding session lifecycle management with auto-save and
GitHub integration. Extracted from manager.py as part of Phase 3.4.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kagura.core.memory.coding.manager import CodingMemoryManager

from kagura.core.memory.models.coding import CodingSession

logger = logging.getLogger(__name__)


def _detect_active_session(self: CodingMemoryManager) -> str | None:
    """Auto-detect active session from persistent storage.

    Scans persistent storage for sessions with no end_time (active sessions).
    Returns the first active session found, or None.

    Returns:
        Active session ID or None
    """
    try:
        # Search persistent storage for sessions
        key_pattern = f"project:{self.project_id}:session:%"
        sessions = self.persistent.search(
            query=key_pattern, user_id=self.user_id, limit=100
        )

        # Find active session (no end_time)
        for sess in sessions:
            value_str = sess.get("value", "{}")
            try:
                data = (
                    json.loads(value_str)
                    if isinstance(value_str, str)
                    else value_str
                )
                if data.get("end_time") is None:
                    session_id = sess["key"].split(":")[-1]
                    logger.info(f"Auto-detected active session: {session_id}")

                    # Cache session in persistent memory (working memory removed in v4.4.0)
                    self.persistent.store(
                        f"session:{session_id}",
                        json.dumps(data),
                        self.user_id,
                        agent_name="coding_sessions"
                    )

                    # Ensure graph node exists for this session
                    if self.graph:
                        # Check if node exists first
                        if not self.graph.graph.has_node(session_id):
                            self.graph.add_node(
                                node_id=session_id,
                                node_type="memory",
                                data={
                                    "description": data.get("description", ""),
                                    "project_id": self.project_id,
                                    "active": True,
                                },
                            )

                    return session_id
            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.warning(f"Failed to auto-detect active session: {e}")

    return None


async def _auto_save_session_progress(self: CodingMemoryManager) -> None:
    """Auto-save current session progress to Claude Code history.

    Called after each file change to preserve work-in-progress.
    Creates timestamped snapshot for crash recovery.

    Note: Only saves if session has meaningful activity.
    """
    if not self.current_session_id:
        return

    # Get current session data from persistent storage
    session_data_str = self.persistent.recall(
        f"session:{self.current_session_id}", self.user_id, agent_name="coding_sessions"
    )
    if not session_data_str:
        return

    try:
        session_data = json.loads(session_data_str) if isinstance(session_data_str, str) else session_data_str
    except json.JSONDecodeError:
        logger.error(f"Failed to parse session data for {self.current_session_id}")
        return

    # Get current activities
    file_changes = await self._get_session_file_changes(self.current_session_id)
    decisions = await self._get_session_decisions(self.current_session_id)
    errors = await self._get_session_errors(self.current_session_id)

    # Skip if no meaningful activity
    if not file_changes and not decisions and not errors:
        return

    # Create progress snapshot
    snapshot_key = (
        f"claude_code_progress_{self.current_session_id}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    snapshot_doc = f"""
Claude Code Progress Snapshot
Session: {self.current_session_id}
Project: {self.project_id}
Saved: {datetime.now().isoformat()}

Description: {session_data.get("description", "N/A")}
Progress:
- Files modified: {len(file_changes)}
- Decisions made: {len(decisions)}
- Errors encountered: {len(errors)}

Recent file changes:
{chr(10).join(f"- {fc.file_path}: {fc.action}" for fc in file_changes[-5:])}
"""

    metadata = {
        "type": "claude_code_progress",
        "session_id": self.current_session_id,
        "project_id": self.project_id,
        "file_count": len(file_changes),
        "decision_count": len(decisions),
        "error_count": len(errors),
        "timestamp": datetime.now().isoformat(),
    }

    # Store snapshot in persistent memory
    self.persistent.store(
        key=snapshot_key,
        value=snapshot_doc,
        user_id=self.user_id,
        metadata=metadata,
    )


async def start_coding_session(
    self: CodingMemoryManager, description: str, tags: list[str] | None = None
) -> str:
    """Start tracked coding session.

    Initiates a new coding session to group related activities.

    Args:
        description: Brief description of session goals
        tags: Session categorization tags

    Returns:
        Session ID

    Raises:
        RuntimeError: If a session is already active

    Example:
        >>> session_id = await coding_mem.start_coding_session(
        ...     description="Implement JWT authentication system",
        ...     tags=["authentication", "security"]
        ... )
    """
    # Use lock to prevent race conditions
    async with self._session_lock:
        if self.current_session_id:
            raise RuntimeError(
                f"❌ A coding session is already active: {self.current_session_id}\n\n"
                "You can only have one active session at a time.\n\n"
                "Options:\n"
                "  1. End current session: coding_end_session()\n"
                "  2. Check session status: coding_get_status()\n\n"
                "💡 TIP: Always end sessions when done to preserve your work history"
            )

        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session = CodingSession(
            session_id=session_id,
            user_id=self.user_id,
            project_id=self.project_id,
            description=description,
            start_time=datetime.utcnow(),
            end_time=None,
            tags=tags or [],
            summary=None,
            success=None,
        )

        # Cache session in persistent memory (working memory removed in v4.4.0)
        self.persistent.store(
            f"session:{session_id}",
            json.dumps(session.model_dump(mode="json")),
            self.user_id,
            agent_name="coding_sessions"
        )

        # Store in persistent memory
        key = self._make_key(f"session:{session_id}")
        self.persistent.store(
            key=key,
            value=session.model_dump(mode="json"),
            user_id=self.user_id,
            agent_name=self.agent_name,
            metadata={
                "type": "coding_session",
                "session_id": session_id,
                "project_id": self.project_id,
                "status": "active",
            },
        )

        # Add to graph
        if self.graph:
            self.graph.add_node(
                node_id=session_id,
                node_type="memory",
                data={
                    "description": description,
                    "project_id": self.project_id,
                    "active": True,
                },
            )

        self.current_session_id = session_id
        logger.info(f"Started coding session: {session_id}")
        return session_id


async def resume_coding_session(self: CodingMemoryManager, session_id: str) -> str:
    """Resume a previously ended coding session.

    Loads the previous session state and sets it as the current active session.
    New activities will be appended to the existing session.

    Args:
        session_id: ID of the session to resume

    Returns:
        Session ID with confirmation message

    Raises:
        RuntimeError: If a session is already active
        ValueError: If session_id doesn't exist or is still active

    Example:
        >>> await coding_mem.resume_coding_session("session_abc123")
    """
    async with self._session_lock:
        if self.current_session_id:
            raise RuntimeError(
                f"Session already active: {self.current_session_id}. "
                "End current session before resuming another."
            )

        # Load session from persistent storage
        key = self._make_key(f"session:{session_id}")
        session_data = self.persistent.recall(key=key, user_id=self.user_id)

        if not session_data:
            raise ValueError(
                f"Session not found: {session_id}. "
                "Check session ID with: kagura coding sessions"
            )

        # Parse session data
        session = CodingSession.model_validate(session_data)

        # Check if session is already ended
        if session.end_time is None:
            raise ValueError(
                f"Session {session_id} is still active. "
                "Cannot resume an active session."
            )

        # Resume session by clearing end_time
        session.end_time = None
        session.success = None

        # Cache resumed session in persistent memory
        self.persistent.store(
            f"session:{session_id}",
            json.dumps(session.model_dump(mode="json")),
            self.user_id,
            agent_name="coding_sessions"
        )

        # Update persistent storage
        self.persistent.store(
            key=key,
            value=session.model_dump(mode="json"),
            user_id=self.user_id,
            agent_name=self.agent_name,
            metadata={
                "type": "coding_session",
                "session_id": session_id,
                "project_id": self.project_id,
                "status": "resumed",
                "resumed": True,
                "resumed_at": datetime.utcnow().isoformat(),
            },
        )

        # Update graph (mark as active again)
        if self.graph and self.graph.graph.has_node(session_id):
            # Update node data directly
            self.graph.graph.nodes[session_id]["active"] = True
            self.graph.graph.nodes[session_id]["resumed"] = True

        self.current_session_id = session_id
        logger.info(f"Resumed coding session: {session_id}")

        return session_id


async def end_coding_session(
    self: CodingMemoryManager,
    summary: str | None = None,
    success: bool | None = None,
    save_to_github: bool = False,
) -> dict[str, Any]:
    """End coding session and generate summary.

    Ends the active session and optionally generates AI-powered summary.
    Can also save session summary to GitHub Issue.

    Args:
        summary: User-provided summary (if None, auto-generate with LLM)
        success: Whether session objectives were met
        save_to_github: Save session summary to GitHub Issue (default: False)

    Returns:
        Dictionary with session data and summary

    Raises:
        RuntimeError: If no active session

    Example:
        >>> result = await coding_mem.end_coding_session(
        ...     success=True
        ... )
        >>> print(result['summary'])
        Implemented JWT auth with RS256 signing...
    """
    if not self.current_session_id:
        raise RuntimeError(
            "❌ No active coding session to end.\n\n"
            "You need to start a session first:\n"
            "  coding_start_session(description='...', project_id='...')\n\n"
            "💡 TIP: Check if a session exists with coding_get_status()"
        )

    session_id = self.current_session_id

    # Retrieve session from persistent storage
    session_data_str = self.persistent.recall(
        f"session:{session_id}", self.user_id, agent_name="coding_sessions"
    )
    if not session_data_str:
        raise RuntimeError(f"Session data not found: {session_id}")

    try:
        session_data = json.loads(session_data_str) if isinstance(session_data_str, str) else session_data_str
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid session data format: {session_id}")

    session = CodingSession(**session_data)
    session.end_time = datetime.utcnow()
    session.success = success

    # Retrieve session activities
    file_changes = await self._get_session_file_changes(session_id)
    errors = await self._get_session_errors(session_id)
    decisions = await self._get_session_decisions(session_id)

    session.files_touched = list({fc.file_path for fc in file_changes})
    session.errors_encountered = len(errors)
    session.errors_fixed = sum(1 for e in errors if e.resolved)
    session.decisions_made = len(decisions)

    # Generate summary if not provided
    if summary is None:
        logger.info("Generating AI-powered session summary...")

        # Estimate cost before generating summary
        context_size = (
            len(str(file_changes)) + len(str(errors)) + len(str(decisions)) + 500
        )
        estimated_tokens = self.coding_analyzer.count_tokens(
            str(session_data)[:context_size]
        )
        estimated_cost = self._estimate_llm_cost(
            input_tokens=estimated_tokens,
            output_tokens=1500,  # Expected summary length
        )

        # Ask approval if cost exceeds threshold
        approved = await self._ask_approval_with_cost(
            operation="Generate AI-powered session summary",
            estimated_cost=estimated_cost,
            details=(
                f"Input: ~{estimated_tokens} tokens, "
                f"Model: {self.coding_analyzer.model}"
            ),
        )

        if not approved:
            summary = (
                f"Session ended. {len(file_changes)} files modified, "
                f"{len(errors)} errors, {len(decisions)} decisions. "
                f"(AI summary skipped)"
            )
            logger.info("Session summary generation cancelled by user")
        else:
            try:
                summary = await self.coding_analyzer.summarize_session(
                    session, file_changes, errors, decisions
                )
                # Track actual cost (would be updated in analyzer)
                logger.info(
                    f"Summary generated. Estimated cost: ${estimated_cost:.2f}"
                )
            except Exception as e:
                logger.error(f"Summary generation failed: {e}")
                summary = (
                    f"Session ended. {len(file_changes)} files modified, "
                    f"{len(errors)} errors, {len(decisions)} decisions."
                )

    session.summary = summary

    # Update stored session
    key = self._make_key(f"session:{session_id}")
    self.persistent.store(
        key=key,
        value=session.model_dump(mode="json"),
        user_id=self.user_id,
        agent_name=self.agent_name,
        metadata={
            "type": "coding_session",
            "session_id": session_id,
            "project_id": self.project_id,
            "status": "completed",
            "success": success,
        },
    )

    # Remove from persistent storage
    self.persistent.forget(f"session:{session_id}", self.user_id, agent_name="coding_sessions")

    # Update graph (delete and re-add with updated data)
    if self.graph:
        if self.graph.graph.has_node(session_id):
            # Get existing data
            node_data = dict(self.graph.graph.nodes[session_id])
            # Update fields
            node_data["active"] = False
            node_data["success"] = success
            # Remove and re-add
            self.graph.graph.remove_node(session_id)
            self.graph.add_node(
                node_id=session_id,
                node_type="memory",
                data=node_data,
            )

    self.current_session_id = None
    logger.info(f"Ended coding session: {session_id}")

    # Save to GitHub if requested
    if save_to_github and self.github_recorder:
        if self.github_recorder.is_available():
            try:
                # Collect interaction summary if available
                interaction_summary = {}
                if self.interaction_tracker:
                    # Only pass analyzer if it exists
                    llm_summarizer = (
                        self.coding_analyzer if self.coding_analyzer else None
                    )
                    interaction_summary = (
                        await self.interaction_tracker.get_session_summary(
                            session_id, llm_summarizer=llm_summarizer
                        )
                    )

                # Prepare summary data
                summary_data = {
                    "total_interactions": interaction_summary.get(
                        "total_interactions", 0
                    ),
                    "by_type": interaction_summary.get("by_type", {}),
                    "file_changes": [
                        {
                            "file_path": fc.file_path,
                            "action": fc.action,
                            "reason": fc.reason,
                        }
                        for fc in file_changes
                    ],
                    "decisions": [
                        {"decision": d.decision, "rationale": d.rationale}
                        for d in decisions
                    ],
                    "errors": [
                        {
                            "error_type": e.error_type,
                            "message": e.message,
                            "solution": e.solution,
                        }
                        for e in errors
                    ],
                }

                # Record to GitHub
                await self.github_recorder.record_session_summary(
                    session_id=session_id,
                    summary_data=summary_data,
                    llm_summary=summary,
                )
                logger.info("Session summary recorded to GitHub Issue")
            except Exception as e:
                logger.error(f"Failed to save session to GitHub: {e}")
        else:
            logger.warning(
                "GitHub recording not available (gh CLI not installed or "
                "no issue number set)"
            )

    return {
        "session_id": session_id,
        "duration_minutes": session.duration_minutes,
        "files_touched": session.files_touched,
        "errors_encountered": session.errors_encountered,
        "errors_fixed": session.errors_fixed,
        "decisions_made": session.decisions_made,
        "summary": summary,
        "success": success,
    }
