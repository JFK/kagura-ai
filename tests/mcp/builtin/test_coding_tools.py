"""Tests for coding MCP tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kagura.mcp.builtin.coding import (
    coding_analyze_patterns,
    coding_end_session,
    coding_get_project_context,
    coding_record_decision,
    coding_record_error,
    coding_search_errors,
    coding_start_session,
    coding_track_file_change,
    coding_track_interaction,
)


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock LLM response"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    return mock_response


class TestCodingTrackFileChange:
    """Test coding_track_file_change MCP tool."""

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    async def test_track_basic_file_change(self, mock_acompletion, mock_llm_response):
        """Test tracking a basic file change."""
        mock_acompletion.return_value = mock_llm_response

        result = await coding_track_file_change(
            user_id="test_user",
            project_id="test_project",
            file_path="src/auth.py",
            action="edit",
            diff="+ def validate_token(): ...",
            reason="Add token validation",
        )

        assert "✅ File change tracked" in result
        assert "src/auth.py" in result
        assert "edit" in result

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    async def test_track_with_related_files(self, mock_acompletion, mock_llm_response):
        """Test tracking with related files."""
        mock_acompletion.return_value = mock_llm_response

        result = await coding_track_file_change(
            user_id="test_user",
            project_id="test_project",
            file_path="src/auth.py",
            action="refactor",
            diff="Extracted validation logic",
            reason="Improve modularity",
            related_files='["src/middleware.py", "src/models/user.py"]',
        )

        assert "✅ File change tracked" in result
        assert "refactor" in result


class TestCodingRecordError:
    """Test coding_record_error MCP tool."""

    @pytest.mark.asyncio
    @patch("kagura.llm.vision.acompletion")
    async def test_record_basic_error(self, mock_acompletion, mock_llm_response):
        """Test recording a basic error."""
        mock_acompletion.return_value = mock_llm_response

        result = await coding_record_error(
            user_id="test_user",
            project_id="test_project",
            error_type="TypeError",
            message="can't compare offset-naive and offset-aware datetimes",
            stack_trace="Traceback:\n  File 'auth.py', line 42...",
            file_path="src/auth.py",
            line_number=42,
        )

        assert "✅ Error recorded" in result
        assert "TypeError" in result
        assert "src/auth.py:42" in result

    @pytest.mark.asyncio
    @patch("kagura.llm.vision.acompletion")
    async def test_record_error_with_solution(
        self, mock_acompletion, mock_llm_response
    ):
        """Test recording error with solution."""
        mock_acompletion.return_value = mock_llm_response

        result = await coding_record_error(
            user_id="test_user",
            project_id="test_project",
            error_type="TypeError",
            message="Error message",
            stack_trace="Stack trace",
            file_path="src/auth.py",
            line_number=42,
            solution="Use datetime.now(timezone.utc)",
            tags='["datetime", "timezone"]',
        )

        assert "✅ Error recorded" in result
        assert "Resolved" in result


class TestCodingRecordDecision:
    """Test coding_record_decision MCP tool."""

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    async def test_record_decision(self, mock_acompletion, mock_llm_response):
        """Test recording a design decision."""
        mock_acompletion.return_value = mock_llm_response

        result = await coding_record_decision(
            user_id="test_user",
            project_id="test_project",
            decision="Use JWT tokens for authentication",
            rationale="Stateless auth enables horizontal scaling",
            alternatives='["Session-based auth", "OAuth only"]',
            impact="No session storage needed",
            tags='["architecture", "security"]',
        )

        assert "✅ Decision recorded" in result
        assert "Use JWT tokens" in result
        assert "80%" in result  # Default confidence 0.8 = 80%


class TestCodingSession:
    """Test coding session MCP tools."""

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    async def test_start_session(self, mock_acompletion, mock_llm_response):
        """Test starting a coding session."""
        mock_acompletion.return_value = mock_llm_response

        result = await coding_start_session(
            user_id="test_user_session",
            project_id="test_project_session",
            description="Implement authentication",
            tags='["feature", "auth"]',
        )

        assert "✅ Coding session started" in result
        assert "session_" in result
        assert "Implement authentication" in result

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    async def test_end_session(self, mock_acompletion, mock_llm_response):
        """Test ending a coding session."""
        mock_acompletion.return_value = mock_llm_response

        # First start a session
        start_result = await coding_start_session(
            user_id="test_user_session2",
            project_id="test_project_session2",
            description="Test session",
        )

        # Extract session_id from result
        # Format: "✅ Coding session started: session_xxxxx"
        assert "session_" in start_result

        # End session with manual summary (to avoid LLM call in tests)
        end_result = await coding_end_session(
            user_id="test_user_session2",
            project_id="test_project_session2",
            summary="Test session completed",
            success=True,
        )

        assert "✅ Coding session ended" in end_result or "ℹ️" in end_result


class TestCodingSearchErrors:
    """Test coding_search_errors MCP tool."""

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test searching when no errors exist."""
        result = await coding_search_errors(
            user_id="test_user_search",
            project_id="test_project_search",
            query="NonexistentError that will not match",
            k=5,
        )

        assert "🔍" in result
        # Either "No similar errors" or results shown


class TestCodingGetProjectContext:
    """Test coding_get_project_context MCP tool."""

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    async def test_get_context(self, mock_acompletion, mock_llm_response):
        """Test getting project context."""
        mock_acompletion.return_value = mock_llm_response

        result = await coding_get_project_context(
            user_id="test_user_context",
            project_id="test_project_context",
        )

        assert "📊 Project Context" in result
        assert "test_project_context" in result


class TestCodingAnalyzePatterns:
    """Test coding_analyze_patterns MCP tool."""

    @pytest.mark.asyncio
    async def test_analyze_insufficient_data(self):
        """Test pattern analysis with insufficient data."""
        result = await coding_analyze_patterns(
            user_id="test_user_patterns",
            project_id="test_project_patterns",
        )

        # Should show insufficient data message
        assert "⚠️" in result or "🔍" in result


class TestCodingTrackInteraction:
    """Test coding_track_interaction MCP tool."""

    @pytest.mark.asyncio
    async def test_track_interaction_basic(self):
        """Test basic interaction tracking."""
        result = await coding_track_interaction(
            user_id="test_user_int",
            project_id="test_project_int",
            user_query="How to fix this bug?",
            ai_response="Try using async/await pattern",
            interaction_type="question",
        )

        assert "✅ Interaction tracked" in result
        assert "question" in result
        assert "int_" in result  # interaction ID

    @pytest.mark.asyncio
    async def test_track_interaction_with_metadata(self):
        """Test tracking with metadata."""
        result = await coding_track_interaction(
            user_id="test_user_int2",
            project_id="test_project_int2",
            user_query="Should we use FastAPI?",
            ai_response="Yes, FastAPI is better for async",
            interaction_type="decision",
            metadata='{"context": "architecture", "file": "api.py"}',
        )

        assert "✅ Interaction tracked" in result
        assert "decision" in result

    @pytest.mark.asyncio
    async def test_track_interaction_invalid_type(self):
        """Test tracking with invalid interaction type."""
        result = await coding_track_interaction(
            user_id="test_user_int3",
            project_id="test_project_int3",
            user_query="Test",
            ai_response="Response",
            interaction_type="invalid_type",
        )

        assert "❌" in result
        assert "Error" in result or "Invalid" in result

    @pytest.mark.asyncio
    async def test_track_interaction_all_types(self):
        """Test all valid interaction types."""
        types = [
            "question",
            "decision",
            "struggle",
            "discovery",
            "implementation",
            "error_fix",
        ]

        for itype in types:
            result = await coding_track_interaction(
                user_id=f"test_user_{itype}",
                project_id=f"test_project_{itype}",
                user_query=f"Test {itype} query",
                ai_response=f"Test {itype} response",
                interaction_type=itype,
            )

            assert "✅ Interaction tracked" in result
            assert itype in result

    @pytest.mark.asyncio
    async def test_track_interaction_within_session(self):
        """Test interaction tracking within active session."""
        # Start a session first
        session_result = await coding_start_session(
            user_id="test_user_session_int",
            project_id="test_project_session_int",
            description="Test session for interactions",
        )
        assert "✅ Coding session started" in session_result

        # Track interaction
        result = await coding_track_interaction(
            user_id="test_user_session_int",
            project_id="test_project_session_int",
            user_query="Test query in session",
            ai_response="Test response",
            interaction_type="implementation",
        )

        assert "✅ Interaction tracked" in result
        assert "session_" in result  # Should mention session ID

        # Clean up
        await coding_end_session(
            user_id="test_user_session_int",
            project_id="test_project_session_int",
        )


class TestCodingEndSessionExtended:
    """Test extended coding_end_session with GitHub integration."""

    @pytest.mark.asyncio
    async def test_end_session_with_github_disabled(self):
        """Test ending session without GitHub save."""
        # Start session
        await coding_start_session(
            user_id="test_user_end1",
            project_id="test_project_end1",
            description="Test session",
        )

        # End without GitHub
        result = await coding_end_session(
            user_id="test_user_end1",
            project_id="test_project_end1",
            success="true",
            save_to_github="false",
        )

        assert "✅ Coding session ended" in result or "ℹ️" in result
        assert "session_" in result
        # Should NOT mention GitHub
        assert "GitHub" not in result or "not available" in result

    @pytest.mark.asyncio
    async def test_end_session_with_github_enabled(self):
        """Test GitHub save enabled (may succeed or warn)."""
        # Start session
        await coding_start_session(
            user_id="test_user_end2",
            project_id="test_project_end2",
            description="Test session",
        )

        # End with GitHub enabled
        result = await coding_end_session(
            user_id="test_user_end2",
            project_id="test_project_end2",
            success="true",
            save_to_github="true",
        )

        assert "Coding session ended" in result
        # Either succeeds or warns (depends on gh CLI availability)
        # Just check it doesn't crash

    @pytest.mark.asyncio
    async def test_end_session_success_param_parsing(self):
        """Test success parameter parsing (string to bool)."""
        # Start session
        await coding_start_session(
            user_id="test_user_end3",
            project_id="test_project_end3",
            description="Test",
        )

        # Test with "true"
        result_true = await coding_end_session(
            user_id="test_user_end3",
            project_id="test_project_end3",
            success="true",
        )
        assert "✅" in result_true

        # Start another session for "false" test
        await coding_start_session(
            user_id="test_user_end4",
            project_id="test_project_end4",
            description="Test",
        )

        # Test with "false"
        result_false = await coding_end_session(
            user_id="test_user_end4",
            project_id="test_project_end4",
            success="false",
        )
        assert "⚠️" in result_false
