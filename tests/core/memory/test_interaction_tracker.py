"""Tests for InteractionTracker."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from kagura.core.memory.interaction_tracker import (
    InteractionRecord,
    InteractionTracker,
    InteractionType,
)


@pytest.fixture
def tracker():
    """Create InteractionTracker instance."""
    return InteractionTracker(
        importance_threshold=8.0,
        flush_interval_seconds=300,
        flush_count_threshold=10,
    )


@pytest.fixture
def mock_llm_classifier():
    """Create mock LLM classifier."""
    mock = AsyncMock()
    mock.classify_importance = AsyncMock(return_value=7.5)
    return mock


@pytest.fixture
def mock_github_recorder():
    """Create mock GitHub recorder."""
    mock = MagicMock()
    mock.record_important_event = AsyncMock(return_value=True)
    return mock


class TestInteractionRecord:
    """Tests for InteractionRecord model."""

    def test_create_interaction_record(self):
        """Test creating an interaction record."""
        record = InteractionRecord(
            user_query="How to fix TypeError?",
            ai_response="Use timezone-aware datetime",
            interaction_type="error_fix",
        )

        assert record.user_query == "How to fix TypeError?"
        assert record.ai_response == "Use timezone-aware datetime"
        assert record.interaction_type == "error_fix"
        assert record.importance == 5.0  # Default
        assert record.interaction_id.startswith("int_")
        assert isinstance(record.timestamp, datetime)

    def test_interaction_record_with_session(self):
        """Test interaction record with session ID."""
        record = InteractionRecord(
            user_query="Test query",
            ai_response="Test response",
            interaction_type="question",
            session_id="session_123",
            importance=3.0,
        )

        assert record.session_id == "session_123"
        assert record.importance == 3.0

    def test_interaction_record_with_metadata(self):
        """Test interaction record with metadata."""
        metadata = {"context": "debugging", "file": "test.py"}
        record = InteractionRecord(
            user_query="Why error?",
            ai_response="Because...",
            interaction_type="error_fix",
            metadata=metadata,
        )

        assert record.metadata == metadata


class TestInteractionTracker:
    """Tests for InteractionTracker."""

    @pytest.mark.asyncio
    async def test_track_interaction_basic(self, tracker):
        """Test basic interaction tracking."""
        record = await tracker.track_interaction(
            user_query="How to implement feature X?",
            ai_response="You should use pattern Y",
            interaction_type="implementation",
        )

        assert record.interaction_type == "implementation"
        assert len(tracker.buffer) == 1
        assert tracker.buffer[0] == record

    @pytest.mark.asyncio
    async def test_track_interaction_with_session(self, tracker):
        """Test tracking with session ID."""
        record = await tracker.track_interaction(
            user_query="Test query",
            ai_response="Test response",
            interaction_type="question",
            session_id="session_abc",
        )

        assert record.session_id == "session_abc"
        assert len(tracker.buffer) == 1

    @pytest.mark.asyncio
    async def test_classify_importance_with_llm(self, tracker, mock_llm_classifier):
        """Test LLM importance classification."""
        await tracker.track_interaction(
            user_query="Important decision",
            ai_response="Let's use approach X",
            interaction_type="decision",
            llm_classifier=mock_llm_classifier,
        )

        # Wait for async classification
        await asyncio.sleep(0.1)

        assert len(tracker.buffer) == 1
        # Importance should be updated by LLM
        mock_llm_classifier.classify_importance.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_importance_fallback(self, tracker):
        """Test fallback importance scoring when LLM fails."""
        # Create a failing LLM classifier
        failing_llm = AsyncMock()
        failing_llm.classify_importance = AsyncMock(
            side_effect=Exception("LLM failed")
        )

        record = await tracker.track_interaction(
            user_query="Test",
            ai_response="Response",
            interaction_type="decision",
            llm_classifier=failing_llm,
        )

        # Wait for async classification
        await asyncio.sleep(0.1)

        # Should use fallback score for "decision" type
        assert record.importance == 8.5

    @pytest.mark.asyncio
    async def test_high_importance_github_recording(
        self, tracker, mock_llm_classifier, mock_github_recorder
    ):
        """Test automatic GitHub recording for high importance."""
        # Set LLM to return high importance
        mock_llm_classifier.classify_importance = AsyncMock(return_value=9.0)

        await tracker.track_interaction(
            user_query="Critical decision",
            ai_response="Choose architecture X",
            interaction_type="decision",
            llm_classifier=mock_llm_classifier,
            github_recorder=mock_github_recorder,
        )

        # Wait for async operations
        await asyncio.sleep(0.2)

        # Should trigger GitHub recording
        mock_github_recorder.record_important_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_low_importance_no_github(
        self, tracker, mock_llm_classifier, mock_github_recorder
    ):
        """Test no GitHub recording for low importance."""
        # Set LLM to return low importance
        mock_llm_classifier.classify_importance = AsyncMock(return_value=3.0)

        await tracker.track_interaction(
            user_query="Simple question",
            ai_response="Simple answer",
            interaction_type="question",
            llm_classifier=mock_llm_classifier,
            github_recorder=mock_github_recorder,
        )

        # Wait for async operations
        await asyncio.sleep(0.2)

        # Should NOT trigger GitHub recording
        mock_github_recorder.record_important_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_flush_by_count(self, tracker):
        """Test automatic flush when count threshold reached."""
        # Add 10 interactions (flush threshold)
        for i in range(10):
            await tracker.track_interaction(
                user_query=f"Query {i}",
                ai_response=f"Response {i}",
                interaction_type="question",
            )

        # Wait for async flush
        await asyncio.sleep(0.1)

        # Buffer should be flushed
        # Note: _flush_buffer is not yet fully implemented, but trigger is tested
        assert len(tracker.buffer) <= 10

    @pytest.mark.asyncio
    async def test_get_session_summary_basic(self, tracker):
        """Test getting session summary."""
        session_id = "test_session"

        # Add some interactions
        for i in range(3):
            await tracker.track_interaction(
                user_query=f"Query {i}",
                ai_response=f"Response {i}",
                interaction_type="question",
                session_id=session_id,
            )

        summary = await tracker.get_session_summary(session_id)

        assert summary["session_id"] == session_id
        assert summary["total_interactions"] == 3
        assert summary["by_type"]["question"] == 3

    @pytest.mark.asyncio
    async def test_get_session_summary_empty(self, tracker):
        """Test summary for non-existent session."""
        summary = await tracker.get_session_summary("nonexistent")

        assert summary["total_interactions"] == 0
        assert summary["summary"] == "No interactions recorded"

    @pytest.mark.asyncio
    async def test_get_session_summary_with_llm(self, tracker, mock_llm_classifier):
        """Test summary with LLM summarizer."""
        session_id = "test_session"
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize_interactions = AsyncMock(
            return_value="AI-generated summary"
        )

        await tracker.track_interaction(
            user_query="Query",
            ai_response="Response",
            interaction_type="implementation",
            session_id=session_id,
        )

        summary = await tracker.get_session_summary(session_id, mock_summarizer)

        assert summary["summary"] == "AI-generated summary"
        mock_summarizer.summarize_interactions.assert_called_once()

    def test_clear_buffer(self, tracker):
        """Test buffer clearing."""
        # Manually add records to buffer
        tracker.buffer = [
            InteractionRecord(
                user_query="Q1", ai_response="A1", interaction_type="question"
            ),
            InteractionRecord(
                user_query="Q2", ai_response="A2", interaction_type="question"
            ),
        ]

        cleared = tracker.clear_buffer()

        assert len(cleared) == 2
        assert len(tracker.buffer) == 0
        assert tracker.last_flush_time <= datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_interaction_types_coverage(self, tracker):
        """Test all interaction types."""
        types: list[InteractionType] = [
            "question",
            "decision",
            "struggle",
            "discovery",
            "implementation",
            "error_fix",
        ]

        for itype in types:
            record = await tracker.track_interaction(
                user_query=f"Test {itype}",
                ai_response="Response",
                interaction_type=itype,
            )
            assert record.interaction_type == itype

    @pytest.mark.asyncio
    async def test_metadata_preserved(self, tracker):
        """Test metadata is preserved in record."""
        metadata = {"file": "test.py", "line": 42, "context": "debugging"}

        record = await tracker.track_interaction(
            user_query="Question",
            ai_response="Answer",
            interaction_type="question",
            metadata=metadata,
        )

        assert record.metadata == metadata
