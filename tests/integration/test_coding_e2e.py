"""E2E integration tests for coding memory system."""

from unittest.mock import MagicMock, patch

import pytest

from kagura.core.memory.coding_memory import CodingMemoryManager


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """# Session Summary

## Overview
Implemented authentication system with JWT tokens.

## Key Decisions
- Use JWT for stateless auth

## Challenges
- Fixed datetime comparison issue

## Recommendations
- Add pre-commit hooks
- Implement token refresh
"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 200
    mock_response.usage.total_tokens = 300
    return mock_response


@pytest.fixture
def coding_memory():
    """Create coding memory manager for testing."""
    return CodingMemoryManager(
        user_id="test_e2e_user",
        project_id="test_e2e_project",
        enable_rag=False,  # Disable RAG for faster tests
        enable_graph=False,  # Disable graph for simpler tests
        auto_approve=True,  # Auto-approve to skip prompts in tests
    )


class TestCodingMemoryE2E:
    """End-to-end integration tests for coding memory."""

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    async def test_full_session_workflow(
        self, mock_acompletion, mock_llm_response, coding_memory
    ):
        """Test complete coding session workflow.

        Workflow:
        1. Start session
        2. Track file changes
        3. Record errors
        4. Record decisions
        5. End session with AI summary
        6. Verify all data stored
        """
        mock_acompletion.return_value = mock_llm_response

        # 1. Start coding session
        session_id = await coding_memory.start_coding_session(
            description="Implement JWT authentication",
            tags=["feature", "auth"],
        )

        assert session_id.startswith("session_")
        assert coding_memory.current_session_id == session_id

        # 2. Track file changes
        change1_id = await coding_memory.track_file_change(
            file_path="src/auth.py",
            action="create",
            diff="+ def validate_token(): ...",
            reason="Add JWT validation logic",
        )

        change2_id = await coding_memory.track_file_change(
            file_path="src/middleware.py",
            action="edit",
            diff="+ auth_middleware = ...",
            reason="Add auth middleware",
            related_files=["src/auth.py"],
        )

        assert change1_id.startswith("change_")
        assert change2_id.startswith("change_")

        # 3. Record errors
        error1_id = await coding_memory.record_error(
            error_type="TypeError",
            message="can't compare offset-naive and offset-aware datetimes",
            stack_trace="Traceback:\n  File 'auth.py', line 42",
            file_path="src/auth.py",
            line_number=42,
        )

        # Record solution after fixing
        error2_id = await coding_memory.record_error(
            error_type="ImportError",
            message="No module named 'jwt'",
            stack_trace="Traceback:\n  File 'auth.py', line 1",
            file_path="src/auth.py",
            line_number=1,
            solution="Added PyJWT to requirements.txt",
            tags=["dependency"],
        )

        assert error1_id.startswith("error_")
        assert error2_id.startswith("error_")

        # 4. Record design decisions
        decision_id = await coding_memory.record_decision(
            decision="Use JWT tokens for authentication",
            rationale="Stateless auth enables horizontal scaling",
            alternatives=["Session-based", "OAuth"],
            impact="No session storage needed",
            tags=["architecture"],
        )

        assert decision_id.startswith("decision_")

        # 5. End session with AI summary
        result = await coding_memory.end_coding_session(success=True)

        assert result["session_id"] == session_id
        assert result["success"] is True
        assert result["summary"] is not None
        assert coding_memory.current_session_id is None  # Session ended

        # 6. Verify statistics
        assert len(result["files_touched"]) == 2  # 2 files modified
        assert result["errors_encountered"] == 2  # 2 errors recorded
        assert result["errors_fixed"] == 1  # 1 error with solution
        assert result["decisions_made"] == 1  # 1 decision recorded

    @pytest.mark.asyncio
    async def test_session_cannot_start_twice(self, coding_memory):
        """Test that only one session can be active at a time."""
        # Start first session
        session1_id = await coding_memory.start_coding_session(
            description="Session 1"
        )

        assert coding_memory.current_session_id == session1_id

        # Try to start second session (should fail)
        with pytest.raises(RuntimeError, match="Session already active"):
            await coding_memory.start_coding_session(description="Session 2")

        # End first session
        await coding_memory.end_coding_session(
            summary="Manual summary", success=True
        )

        # Now should be able to start new session
        session2_id = await coding_memory.start_coding_session(
            description="Session 2"
        )

        assert session2_id.startswith("session_")
        assert coding_memory.current_session_id == session2_id

    @pytest.mark.asyncio
    async def test_session_end_without_start(self, coding_memory):
        """Test that ending session without starting fails."""
        with pytest.raises(RuntimeError, match="No active session"):
            await coding_memory.end_coding_session()

    @pytest.mark.asyncio
    async def test_project_scoping(self):
        """Test that projects are properly scoped."""
        # Create two managers for different projects
        mem1 = CodingMemoryManager(
            user_id="test_user",
            project_id="project_a",
            enable_rag=False,
            enable_graph=False,
        )

        mem2 = CodingMemoryManager(
            user_id="test_user",
            project_id="project_b",
            enable_rag=False,
            enable_graph=False,
        )

        # Start sessions in both
        session1 = await mem1.start_coding_session(description="Project A work")
        session2 = await mem2.start_coding_session(description="Project B work")

        # Sessions should be independent
        assert mem1.current_session_id != mem2.current_session_id
        assert mem1.project_id == "project_a"
        assert mem2.project_id == "project_b"

        # End sessions
        await mem1.end_coding_session(summary="Done A")
        await mem2.end_coding_session(summary="Done B")

        assert mem1.current_session_id is None
        assert mem2.current_session_id is None
