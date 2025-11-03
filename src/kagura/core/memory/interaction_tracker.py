"""Interaction tracker for AI-User conversation recording.

Implements hybrid buffering strategy with LLM importance classification:
- Immediate: Working Memory buffering
- High importance (>= 8.0): Async GitHub recording
- Periodic flush: Persistent Memory (10 interactions or 5 minutes)
- Session end: LLM summary + GitHub full comment
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class InteractionType(str):
    """Interaction type classification."""

    QUESTION = "question"  # Low importance
    DECISION = "decision"  # High importance
    STRUGGLE = "struggle"  # High importance
    DISCOVERY = "discovery"  # High importance
    IMPLEMENTATION = "implementation"  # Medium importance
    ERROR_FIX = "error_fix"  # High importance


class InteractionRecord(BaseModel):
    """Record of a single AI-User interaction.

    Attributes:
        interaction_id: Unique identifier
        user_query: User's input/question
        ai_response: AI's response
        interaction_type: Classification of interaction
        timestamp: When this interaction occurred
        importance: LLM-classified importance (0.0-10.0)
        session_id: Associated coding session ID
        metadata: Additional context
    """

    interaction_id: str = Field(default_factory=lambda: f"int_{uuid.uuid4().hex[:12]}")
    user_query: str
    ai_response: str
    interaction_type: Literal[
        "question", "decision", "struggle", "discovery", "implementation", "error_fix"
    ]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    importance: float = 5.0  # 0.0-10.0
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionTracker:
    """Track and manage AI-User interactions with hybrid buffering.

    Strategy:
    - Immediate: Buffer all interactions in Working Memory
    - High importance (>= 8.0): Async record to GitHub (non-blocking)
    - Periodic: Flush to Persistent Memory (10 interactions or 5 minutes)
    - Session end: Full summary + GitHub comment

    Attributes:
        buffer: In-memory buffer for current interactions
        last_flush_time: When buffer was last flushed
        importance_threshold: Threshold for immediate GitHub recording (default: 8.0)
        flush_interval_seconds: Seconds between automatic flushes (default: 300)
        flush_count_threshold: Number of interactions before auto-flush (default: 10)
    """

    def __init__(
        self,
        importance_threshold: float = 8.0,
        flush_interval_seconds: int = 300,
        flush_count_threshold: int = 10,
    ) -> None:
        """Initialize interaction tracker.

        Args:
            importance_threshold: Minimum importance for immediate GitHub record
            flush_interval_seconds: Seconds between automatic flushes
            flush_count_threshold: Interactions count before auto-flush
        """
        self.buffer: list[InteractionRecord] = []
        self.last_flush_time = datetime.now(timezone.utc)
        self.importance_threshold = importance_threshold
        self.flush_interval_seconds = flush_interval_seconds
        self.flush_count_threshold = flush_count_threshold

        logger.info(
            f"InteractionTracker initialized: threshold={importance_threshold}, "
            f"flush_interval={flush_interval_seconds}s, "
            f"flush_count={flush_count_threshold}"
        )

    async def track_interaction(
        self,
        user_query: str,
        ai_response: str,
        interaction_type: Literal[
            "question",
            "decision",
            "struggle",
            "discovery",
            "implementation",
            "error_fix",
        ],
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        llm_classifier: Any | None = None,
        github_recorder: Any | None = None,
    ) -> InteractionRecord:
        """Track a single interaction with hybrid buffering.

        Args:
            user_query: User's input
            ai_response: AI's response
            interaction_type: Type of interaction
            session_id: Associated coding session ID
            metadata: Additional context
            llm_classifier: LLM for importance classification (optional)
            github_recorder: GitHub recorder for immediate recording (optional)

        Returns:
            Created interaction record

        Example:
            >>> record = await tracker.track_interaction(
            ...     user_query="How do I fix this TypeError?",
            ...     ai_response="Use timezone-aware datetime...",
            ...     interaction_type="error_fix"
            ... )
        """
        # Create interaction record
        record = InteractionRecord(
            user_query=user_query,
            ai_response=ai_response,
            interaction_type=interaction_type,
            session_id=session_id,
            metadata=metadata or {},
        )

        # 1. Buffer immediately (non-blocking)
        self.buffer.append(record)
        logger.debug(
            f"Buffered interaction {record.interaction_id}: {interaction_type}"
        )

        # 2. LLM importance classification (async, non-blocking)
        if llm_classifier:
            importance_task = asyncio.create_task(
                self._classify_importance(record, llm_classifier)
            )
            # Don't await - runs in background
            importance_task.add_done_callback(
                lambda t: logger.debug(
                    f"Importance classified: {record.interaction_id} = "
                    f"{record.importance}"
                )
            )

        # 3. High importance → immediate GitHub record (async, non-blocking)
        if record.importance >= self.importance_threshold and github_recorder:
            asyncio.create_task(github_recorder.record_important_event(record))
            logger.info(
                f"High importance interaction ({record.importance}): "
                f"async GitHub recording triggered"
            )

        # 4. Check flush conditions
        should_flush = (
            len(self.buffer) >= self.flush_count_threshold
            or (datetime.now(timezone.utc) - self.last_flush_time).total_seconds()
            >= self.flush_interval_seconds
        )

        if should_flush:
            # Flush in background (non-blocking)
            asyncio.create_task(self._flush_buffer())

        return record

    async def _classify_importance(
        self, record: InteractionRecord, llm_classifier: Any
    ) -> float:
        """Classify interaction importance using LLM.

        Args:
            record: Interaction record to classify
            llm_classifier: LLM classifier instance

        Returns:
            Importance score (0.0-10.0)
        """
        try:
            importance = await llm_classifier.classify_importance(
                user_query=record.user_query,
                ai_response=record.ai_response,
                interaction_type=record.interaction_type,
            )
            record.importance = importance
            return importance
        except Exception as e:
            logger.warning(f"LLM importance classification failed: {e}")
            # Fallback to type-based heuristics
            type_scores = {
                "question": 3.0,
                "decision": 8.5,
                "struggle": 7.5,
                "discovery": 8.0,
                "implementation": 6.0,
                "error_fix": 7.0,
            }
            record.importance = type_scores.get(record.interaction_type, 5.0)
            return record.importance

    async def _flush_buffer(self) -> None:
        """Flush buffered interactions to Persistent Memory.

        Background task, non-blocking.
        """
        if not self.buffer:
            return

        # Get interactions to flush
        to_flush = self.buffer.copy()
        self.buffer.clear()
        self.last_flush_time = datetime.now(timezone.utc)

        logger.info(f"Flushing {len(to_flush)} interactions to Persistent Memory")

        # TODO: Actual flush to Persistent Memory
        # This will be implemented when integrating with CodingMemoryManager

    async def get_session_summary(
        self, session_id: str, llm_summarizer: Any | None = None
    ) -> dict[str, Any]:
        """Get summary of all interactions in a session.

        Args:
            session_id: Coding session ID
            llm_summarizer: LLM for generating summary (optional)

        Returns:
            Summary dict with statistics and LLM-generated summary
        """
        session_interactions = [r for r in self.buffer if r.session_id == session_id]

        if not session_interactions:
            return {
                "session_id": session_id,
                "total_interactions": 0,
                "summary": "No interactions recorded",
            }

        # Calculate statistics
        stats = {
            "session_id": session_id,
            "total_interactions": len(session_interactions),
            "by_type": {},
            "avg_importance": sum(r.importance for r in session_interactions)
            / len(session_interactions),
            "high_importance_count": len(
                [r for r in session_interactions if r.importance >= 8.0]
            ),
        }

        # Count by type
        for interaction in session_interactions:
            itype = interaction.interaction_type
            stats["by_type"][itype] = stats["by_type"].get(itype, 0) + 1

        # LLM-generated summary
        if llm_summarizer:
            try:
                llm_summary = await llm_summarizer.summarize_interactions(
                    session_interactions
                )
                stats["summary"] = llm_summary
            except Exception as e:
                logger.warning(f"LLM summary generation failed: {e}")
                stats["summary"] = "Summary generation failed"

        return stats

    def clear_buffer(self) -> list[InteractionRecord]:
        """Clear and return current buffer.

        Returns:
            List of buffered interaction records
        """
        buffer_copy = self.buffer.copy()
        self.buffer.clear()
        self.last_flush_time = datetime.now(timezone.utc)
        return buffer_copy
