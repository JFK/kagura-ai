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

# Type for interaction classification
InteractionType = Literal[
    "question", "decision", "struggle", "discovery", "implementation", "error_fix"
]


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
    interaction_type: InteractionType
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
        total_cost: Total LLM cost for importance classification (USD)
        total_tokens: Total tokens used for LLM operations
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
        self.flushed_interactions: list[InteractionRecord] = []  # Preserve flushed data
        self.last_flush_time = datetime.now(timezone.utc)
        self.importance_threshold = importance_threshold
        self.flush_interval_seconds = flush_interval_seconds
        self.flush_count_threshold = flush_count_threshold

        # Cost tracking for LLM operations
        self.total_cost = 0.0
        self.total_tokens = 0

        logger.info(
            f"InteractionTracker initialized: threshold={importance_threshold}, "
            f"flush_interval={flush_interval_seconds}s, "
            f"flush_count={flush_count_threshold}"
        )

    async def track_interaction(
        self,
        user_query: str,
        ai_response: str,
        interaction_type: InteractionType,
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
            # Start classification in background
            asyncio.create_task(
                self._classify_and_record(record, llm_classifier, github_recorder)
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

    async def _classify_and_record(
        self,
        record: InteractionRecord,
        llm_classifier: Any,
        github_recorder: Any | None,
    ) -> None:
        """Classify importance and conditionally record to GitHub.

        This ensures GitHub recording only happens after classification completes.

        Args:
            record: Interaction record to classify
            llm_classifier: LLM classifier instance
            github_recorder: GitHub recorder (optional)
        """
        # Classify importance
        importance = await self._classify_importance(record, llm_classifier)

        logger.debug(f"Importance classified: {record.interaction_id} = {importance}")

        # Record to GitHub if high importance
        if importance >= self.importance_threshold and github_recorder:
            try:
                await github_recorder.record_important_event(record)
                logger.info(
                    f"High importance interaction ({importance}): recorded to GitHub"
                )
            except Exception as e:
                logger.error(f"GitHub recording failed: {e}")

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
        # Type-based heuristics (fallback scores)
        type_scores = {
            "question": 3.0,
            "decision": 8.5,
            "struggle": 7.5,
            "discovery": 8.0,
            "implementation": 6.0,
            "error_fix": 7.0,
        }

        try:
            importance = await llm_classifier.classify_importance(
                user_query=record.user_query,
                ai_response=record.ai_response,
                interaction_type=record.interaction_type,
            )
            record.importance = importance

            # Track cost if available
            if hasattr(llm_classifier, "last_cost"):
                self.total_cost += llm_classifier.last_cost
            if hasattr(llm_classifier, "last_tokens"):
                self.total_tokens += llm_classifier.last_tokens

            return importance
        except Exception as e:
            logger.warning(f"LLM importance classification failed: {e}, using fallback")
            # Fallback to type-based heuristics
            record.importance = type_scores.get(record.interaction_type, 5.0)
            return record.importance

    async def _flush_buffer(
        self, persistent_storage: Any | None = None
    ) -> list[InteractionRecord]:
        """Flush buffered interactions to Persistent Memory.

        Background task, non-blocking.

        IMPORTANT: Flushed interactions are preserved in flushed_interactions list
        to prevent data loss until proper persistent storage integration.

        Args:
            persistent_storage: Storage backend (optional, for future integration)

        Returns:
            List of flushed interactions
        """
        if not self.buffer:
            return []

        # Get interactions to flush
        to_flush = self.buffer.copy()
        self.buffer.clear()
        self.last_flush_time = datetime.now(timezone.utc)

        # Preserve flushed data to prevent loss (critical fix for Copilot P1 issue)
        self.flushed_interactions.extend(to_flush)

        logger.info(
            f"Flushed {len(to_flush)} interactions "
            f"(total preserved: {len(self.flushed_interactions)})"
        )

        # TODO: Integrate with CodingMemoryManager.persistent storage
        # When integrated, write to_flush to persistent storage here

        return to_flush

    async def get_session_summary(
        self, session_id: str, llm_summarizer: Any | None = None
    ) -> dict[str, Any]:
        """Get summary of all interactions in a session.

        Includes both buffered and flushed interactions to prevent data loss.

        Args:
            session_id: Coding session ID
            llm_summarizer: LLM for generating summary (optional)

        Returns:
            Summary dict with statistics and LLM-generated summary
        """
        # Include both buffer and flushed interactions (critical: prevents data loss)
        all_interactions = self.buffer + self.flushed_interactions
        session_interactions = [
            r for r in all_interactions if r.session_id == session_id
        ]

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
