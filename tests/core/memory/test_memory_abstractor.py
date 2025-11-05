"""Tests for MemoryAbstractor."""

from unittest.mock import AsyncMock

import pytest

from kagura.core.memory.interaction_tracker import InteractionRecord
from kagura.core.memory.memory_abstractor import (
    AbstractedMemory,
    AbstractionLevel,
    MemoryAbstractor,
)


@pytest.fixture
def abstractor():
    """Create MemoryAbstractor instance."""
    return MemoryAbstractor(
        level1_model="gpt-5-mini", level2_model="gpt-5", enable_level2=True
    )


@pytest.fixture
def abstractor_level1_only():
    """Create MemoryAbstractor with level 2 disabled."""
    return MemoryAbstractor(enable_level2=False)


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    mock = AsyncMock()
    return mock


class TestAbstractionLevel:
    """Tests for AbstractionLevel enum."""

    def test_abstraction_levels(self):
        """Test abstraction level constants."""
        assert AbstractionLevel.LEVEL_0_RAW == "raw"
        assert AbstractionLevel.LEVEL_1_SUMMARY == "summary"
        assert AbstractionLevel.LEVEL_2_CONCEPT == "concept"


class TestAbstractedMemory:
    """Tests for AbstractedMemory model."""

    def test_create_abstracted_memory_basic(self):
        """Test creating basic abstracted memory."""
        memory = AbstractedMemory(
            original_id="record_123",
            abstraction_level="summary",
            summary="Short summary",
            keywords=["keyword1", "keyword2"],
        )

        assert memory.original_id == "record_123"
        assert memory.abstraction_level == "summary"
        assert memory.summary == "Short summary"
        assert len(memory.keywords) == 2

    def test_abstracted_memory_with_concepts(self):
        """Test abstracted memory with level 2 data."""
        memory = AbstractedMemory(
            original_id="context_456",
            abstraction_level="concept",
            summary="High-level summary",
            keywords=["async", "python"],
            concepts=["concurrent programming", "event loop"],
            patterns=["use asyncio.gather for parallel tasks"],
            reference="https://github.com/owner/repo/issues/123",
        )

        assert memory.abstraction_level == "concept"
        assert len(memory.concepts) == 2
        assert len(memory.patterns) == 1
        assert memory.reference.startswith("https://")


class TestMemoryAbstractor:
    """Tests for MemoryAbstractor."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        abstractor = MemoryAbstractor()

        assert abstractor.level1_model == "gpt-5-mini"
        assert abstractor.level2_model == "gpt-5"
        assert abstractor.enable_level2 is True

    def test_init_custom_models(self):
        """Test initialization with custom models."""
        abstractor = MemoryAbstractor(
            level1_model="gemini-2.0-flash-exp",
            level2_model="claude-sonnet-4-5",
            enable_level2=False,
        )

        assert abstractor.level1_model == "gemini-2.0-flash-exp"
        assert abstractor.level2_model == "claude-sonnet-4-5"
        assert abstractor.enable_level2 is False

    @pytest.mark.asyncio
    async def test_abstract_external_record_without_llm(self, abstractor):
        """Test external record abstraction without LLM (fallback)."""
        result = await abstractor.abstract_external_record(
            record_id="gh_comment_123",
            raw_content="User asked about datetime timezone issues. "
            "Tried multiple approaches. Finally solved with UTC.",
            reference="https://github.com/org/repo/issues/42#comment-123",
        )

        assert result.original_id == "gh_comment_123"
        assert result.abstraction_level == "summary"
        assert len(result.summary) > 0
        assert len(result.keywords) > 0
        assert result.reference == "https://github.com/org/repo/issues/42#comment-123"

    @pytest.mark.asyncio
    async def test_abstract_external_record_with_llm(self, abstractor, mock_llm_client):
        """Test external record abstraction with LLM."""
        # Mock LLM response
        mock_llm_client.generate = AsyncMock(
            return_value='{"summary": "Datetime timezone fix", '
            '"keywords": ["datetime", "timezone", "UTC"]}'
        )

        result = await abstractor.abstract_external_record(
            record_id="gh_comment_456",
            raw_content="Long content here...",
            reference="https://example.com",
            llm_client=mock_llm_client,
        )

        assert result.original_id == "gh_comment_456"
        assert result.summary == "Datetime timezone fix"
        assert "datetime" in result.keywords
        assert result.reference == "https://example.com"
        mock_llm_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_abstract_external_record_llm_failure(
        self, abstractor, mock_llm_client
    ):
        """Test fallback when LLM fails."""
        mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM error"))

        result = await abstractor.abstract_external_record(
            record_id="record_789",
            raw_content="Content here",
            llm_client=mock_llm_client,
        )

        # Should fallback to simple extraction
        assert result.abstraction_level == "summary"
        assert len(result.summary) > 0

    def test_fallback_level1_basic(self, abstractor):
        """Test level 1 fallback abstraction."""
        result = abstractor._fallback_level1(
            "rec_001", "Short content with important keywords like Python async", None
        )

        assert result.original_id == "rec_001"
        assert result.abstraction_level == "summary"
        assert "Short content" in result.summary
        assert len(result.keywords) > 0

    def test_fallback_level1_long_content(self, abstractor):
        """Test fallback with long content (truncation)."""
        long_content = "A" * 500
        result = abstractor._fallback_level1("rec_002", long_content, None)

        assert len(result.summary) <= 203  # 200 + "..."
        assert result.summary.endswith("...")

    @pytest.mark.asyncio
    async def test_abstract_context_level2_disabled(self, abstractor_level1_only):
        """Test context abstraction with level 2 disabled."""
        interactions = [
            InteractionRecord(
                user_query="Q1", ai_response="A1", interaction_type="question"
            ),
            InteractionRecord(
                user_query="Q2", ai_response="A2", interaction_type="decision"
            ),
        ]

        result = await abstractor_level1_only.abstract_context(
            "session_123", interactions
        )

        assert result.abstraction_level == "summary"
        assert "2 interactions" in result.summary
        assert result.metadata.get("downgraded_from_level2") is True

    @pytest.mark.asyncio
    async def test_abstract_context_with_llm(self, abstractor, mock_llm_client):
        """Test context abstraction with LLM (level 2)."""
        mock_llm_client.generate = AsyncMock(
            return_value='{"summary": "Session summary", '
            '"keywords": ["async", "python"], '
            '"concepts": ["concurrency"], '
            '"patterns": ["use asyncio"]}'
        )

        interactions = [
            InteractionRecord(
                user_query="How to use asyncio?",
                ai_response="Use asyncio.gather...",
                interaction_type="implementation",
            )
        ]

        result = await abstractor.abstract_context(
            "session_456", interactions, llm_client=mock_llm_client
        )

        assert result.abstraction_level == "concept"
        assert result.summary == "Session summary"
        assert "async" in result.keywords
        assert "concurrency" in result.concepts
        assert len(result.patterns) > 0
        assert result.metadata["interaction_count"] == 1

    @pytest.mark.asyncio
    async def test_abstract_context_llm_failure_fallback(
        self, abstractor, mock_llm_client
    ):
        """Test fallback when level 2 LLM fails."""
        mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM failed"))

        interactions = [
            InteractionRecord(
                user_query="Test", ai_response="Response", interaction_type="question"
            )
        ]

        result = await abstractor.abstract_context(
            "session_789", interactions, llm_client=mock_llm_client
        )

        # Should downgrade to level 1
        assert result.abstraction_level == "summary"
        assert "1 interaction" in result.summary  # Singular for count=1

    @pytest.mark.asyncio
    async def test_downgrade_to_level1_multiple_types(self, abstractor):
        """Test level 1 downgrade with multiple interaction types."""
        interactions = [
            InteractionRecord(
                user_query="Q1", ai_response="A1", interaction_type="question"
            ),
            InteractionRecord(
                user_query="Q2", ai_response="A2", interaction_type="question"
            ),
            InteractionRecord(
                user_query="Q3", ai_response="A3", interaction_type="decision"
            ),
            InteractionRecord(
                user_query="Q4", ai_response="A4", interaction_type="error_fix"
            ),
        ]

        result = await abstractor._downgrade_to_level1("ctx_001", interactions)

        assert "4 interactions" in result.summary
        assert "question" in result.keywords
        assert "decision" in result.keywords
        assert "error_fix" in result.keywords
