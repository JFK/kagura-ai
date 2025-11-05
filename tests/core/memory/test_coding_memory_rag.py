"""Tests for coding memory RAG integration."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kagura.core.memory.coding_memory import CodingMemoryManager


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock summary"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    return mock_response


@pytest.fixture
def coding_memory_with_rag(tmp_path):
    """Create coding memory with RAG enabled."""
    try:
        import chromadb  # noqa: F401

        return CodingMemoryManager(
            user_id="test_rag_user",
            project_id="test_rag_project",
            persist_dir=tmp_path,
            enable_rag=True,  # Enable RAG for testing
            enable_graph=False,  # Disable graph for simpler tests
            auto_approve=True,
        )
    except ImportError:
        pytest.skip("ChromaDB not available")


class TestCodingMemoryRAG:
    """Test RAG integration in coding memory."""

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    @patch("kagura.llm.vision.acompletion")
    async def test_search_similar_errors_with_rag(
        self, mock_vision, mock_analyzer, mock_llm_response, coding_memory_with_rag
    ):
        """Test that search_similar_errors actually returns results."""
        mock_vision.return_value = mock_llm_response
        mock_analyzer.return_value = mock_llm_response

        memory = coding_memory_with_rag

        # Record an error
        error1_id = await memory.record_error(
            error_type="TypeError",
            message="can't compare offset-naive and offset-aware datetimes",
            stack_trace="Traceback:\n  File 'auth.py', line 42",
            file_path="src/auth.py",
            line_number=42,
            solution="Use datetime.now(timezone.utc) consistently",
            tags=["datetime", "timezone"],
        )

        # Record another similar error
        error2_id = await memory.record_error(
            error_type="TypeError",
            message="unsupported operand type(s) for -: 'datetime.datetime' and 'NoneType'",
            stack_trace="Traceback:\n  File 'utils.py', line 15",
            file_path="src/utils.py",
            line_number=15,
            solution="Check for None before datetime operations",
        )

        # Search for similar errors
        results = await memory.search_similar_errors(query="datetime type error", k=5)

        # Should find the errors we just recorded
        assert len(results) > 0, "RAG search should return results"
        assert any(e.error_type == "TypeError" for e in results), (
            "Should find TypeError"
        )

        # Check that errors have solutions
        errors_with_solutions = [e for e in results if e.solution]
        assert len(errors_with_solutions) > 0, "Should have errors with solutions"

    @pytest.mark.asyncio
    async def test_file_changes_retrievable_via_rag(self, coding_memory_with_rag):
        """Test that recent file changes can be retrieved via RAG."""
        memory = coding_memory_with_rag

        # Track some file changes
        await memory.track_file_change(
            file_path="src/auth.py",
            action="create",
            diff="+ def validate_token(): ...",
            reason="Add JWT validation",
        )

        await memory.track_file_change(
            file_path="src/middleware.py",
            action="edit",
            diff="+ auth_middleware = ...",
            reason="Add auth middleware",
        )

        # Retrieve recent changes via RAG
        recent = await memory._get_recent_file_changes(limit=10)

        # Should retrieve the changes
        assert len(recent) > 0, "Should retrieve file changes via RAG"
        assert any(fc.file_path == "src/auth.py" for fc in recent), (
            "Should find auth.py change"
        )

    @pytest.mark.asyncio
    async def test_decisions_retrievable_via_rag(self, coding_memory_with_rag):
        """Test that recent decisions can be retrieved via RAG."""
        memory = coding_memory_with_rag

        # Record decisions
        await memory.record_decision(
            decision="Use JWT for authentication",
            rationale="Stateless scaling",
            impact="No session storage",
            tags=["architecture"],
        )

        await memory.record_decision(
            decision="Use Pydantic for validation",
            rationale="Type safety",
            impact="Better error messages",
            tags=["library"],
        )

        # Retrieve recent decisions via RAG
        recent = await memory._get_recent_decisions(limit=10)

        # Should retrieve decisions
        assert len(recent) > 0, "Should retrieve decisions via RAG"
        assert any("JWT" in d.decision for d in recent), "Should find JWT decision"

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    @patch("kagura.llm.vision.acompletion")
    async def test_project_scoping_in_rag(
        self, mock_vision, mock_analyzer, mock_llm_response, tmp_path
    ):
        """Test that RAG correctly scopes by project_id."""
        mock_vision.return_value = mock_llm_response
        mock_analyzer.return_value = mock_llm_response

        # Create two memories for different projects
        mem1 = CodingMemoryManager(
            user_id="test_user",
            project_id="project_a",
            persist_dir=tmp_path / "mem1",
            enable_rag=True,
            enable_graph=False,
        )

        mem2 = CodingMemoryManager(
            user_id="test_user",
            project_id="project_b",
            persist_dir=tmp_path / "mem2",
            enable_rag=True,
            enable_graph=False,
        )

        # Record error in project A
        await mem1.record_error(
            error_type="ValueError",
            message="Project A error",
            stack_trace="...",
            file_path="src/a.py",
            line_number=10,
        )

        # Record error in project B
        await mem2.record_error(
            error_type="ValueError",
            message="Project B error",
            stack_trace="...",
            file_path="src/b.py",
            line_number=20,
        )

        # Search in project A - should only find project A errors
        results_a = await mem1.search_similar_errors("error", k=10)
        results_b = await mem2.search_similar_errors("error", k=10)

        # Each project should only see its own errors
        if results_a:
            assert all(e.file_path == "src/a.py" for e in results_a), (
                "Project A should only see its own errors"
            )

        if results_b:
            assert all(e.file_path == "src/b.py" for e in results_b), (
                "Project B should only see its own errors"
            )

    @pytest.mark.asyncio
    @patch("kagura.llm.coding_analyzer.acompletion")
    @patch("kagura.llm.vision.acompletion")
    async def test_error_with_solution_retrievable(
        self, mock_vision, mock_analyzer, mock_llm_response, coding_memory_with_rag
    ):
        """Test that errors with solutions are retrievable and complete."""
        mock_vision.return_value = mock_llm_response
        mock_analyzer.return_value = mock_llm_response

        memory = coding_memory_with_rag

        # Record error with solution
        await memory.record_error(
            error_type="ImportError",
            message="No module named 'jwt'",
            stack_trace="...",
            file_path="src/auth.py",
            line_number=1,
            solution="pip install PyJWT",
        )

        # Search and retrieve
        results = await memory.search_similar_errors("import jwt module", k=5)

        assert len(results) > 0, "Should find error"
        found_error = results[0]
        assert found_error.error_type == "ImportError"
        assert found_error.solution is not None
        assert "PyJWT" in found_error.solution
        assert found_error.resolved is True  # Has solution
