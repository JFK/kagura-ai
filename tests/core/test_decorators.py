"""Tests for decorators (stub)"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from kagura import agent, tool, workflow


@pytest.mark.asyncio
async def test_agent_decorator_exists():
    """Test that @agent decorator exists"""
    with patch("kagura.core.decorators.call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Hello, World!"

        @agent
        async def hello(name: str) -> str:
            """Say hello to {{ name }}"""
            pass

        result = await hello("World")
        assert isinstance(result, str)
        assert "World" in result


@pytest.mark.asyncio
async def test_agent_decorator_with_params():
    """Test @agent decorator with parameters"""
    with patch("kagura.core.decorators.call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Greetings, Alice!"

        @agent(model="gpt-5-mini", temperature=0.5)
        async def greet(name: str) -> str:
            """Greet {{ name }}"""
            pass

        result = await greet("Alice")
        assert isinstance(result, str)
        assert "Alice" in result


def test_tool_decorator():
    """Test @tool decorator"""

    @tool
    def add(a: int, b: int) -> int:
        return a + b

    result = add(2, 3)
    assert result == 5


def test_tool_decorator_with_parens():
    """Test @tool() decorator with parentheses"""

    @tool()
    def multiply(a: int, b: int) -> int:
        return a * b

    result = multiply(3, 4)
    assert result == 12


@pytest.mark.asyncio
async def test_workflow_decorator():
    """Test @workflow decorator"""

    @workflow
    async def process(data: str) -> str:
        return f"Processed: {data}"

    result = await process("test")
    assert result == "Processed: test"


@pytest.mark.asyncio
async def test_workflow_decorator_with_parens():
    """Test @workflow() decorator with parentheses"""

    @workflow()
    async def pipeline(data: str) -> str:
        return f"Pipeline: {data}"

    result = await pipeline("input")
    assert result == "Pipeline: input"


# MultimodalRAG integration tests
# Skip if chromadb or multimodal dependencies not available
pytestmark_multimodal = pytest.mark.skipif(
    not pytest.importorskip("chromadb", reason="chromadb not installed"),
    reason="multimodal dependencies not available",
)


@pytest.mark.asyncio
@pytestmark_multimodal
async def test_agent_with_multimodal_rag():
    """Test @agent decorator with MultimodalRAG integration"""
    # Create temporary directory with test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "docs").mkdir()
        (tmp_path / "README.md").write_text("# Test Project\nThis is a test.")
        (tmp_path / "docs" / "guide.txt").write_text("User guide content.")

        with patch(
            "kagura.core.decorators.call_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = "Documentation answer"

            # Mock GeminiLoader and DirectoryScanner
            with patch(
                "kagura.core.memory.multimodal_rag.GeminiLoader"
            ) as mock_gemini_cls:
                with patch(
                    "kagura.core.memory.multimodal_rag.DirectoryScanner"
                ) as mock_scanner_cls:
                    # Setup mocks
                    mock_gemini = Mock()
                    mock_gemini_cls.return_value = mock_gemini

                    mock_scanner = Mock()
                    mock_scanner_cls.return_value = mock_scanner

                    @agent(enable_multimodal_rag=True, rag_directory=tmp_path)
                    async def docs_assistant(query: str, rag) -> str:
                        """Answer {{ query }} using documentation"""
                        pass

                    result = await docs_assistant("How to use?")
                    assert isinstance(result, str)
                    assert result == "Documentation answer"


@pytest.mark.asyncio
@pytestmark_multimodal
async def test_agent_multimodal_rag_validation():
    """Test MultimodalRAG validation in @agent decorator"""
    # Missing rag_directory
    with pytest.raises(ValueError, match="rag_directory is required"):

        @agent(enable_multimodal_rag=True)
        async def invalid_agent1(query: str, rag) -> str:
            """Query: {{ query }}"""
            pass

    # Missing rag parameter
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="must have 'rag' parameter"):

            @agent(enable_multimodal_rag=True, rag_directory=Path(tmpdir))
            async def invalid_agent2(query: str) -> str:
                """Query: {{ query }}"""
                pass


@pytest.mark.asyncio
@pytestmark_multimodal
async def test_agent_multimodal_rag_with_memory():
    """Test @agent with both MultimodalRAG and memory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "test.txt").write_text("Test content")

        with patch(
            "kagura.core.decorators.call_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = "Combined response"

            # Mock GeminiLoader and DirectoryScanner
            with patch(
                "kagura.core.memory.multimodal_rag.GeminiLoader"
            ) as mock_gemini_cls:
                with patch(
                    "kagura.core.memory.multimodal_rag.DirectoryScanner"
                ) as mock_scanner_cls:
                    mock_gemini = Mock()
                    mock_gemini_cls.return_value = mock_gemini

                    mock_scanner = Mock()
                    mock_scanner_cls.return_value = mock_scanner

                    @agent(
                        enable_memory=True,
                        enable_multimodal_rag=True,
                        rag_directory=tmp_path,
                    )
                    async def full_assistant(query: str, memory, rag) -> str:
                        """Answer {{ query }} using memory and RAG"""
                        pass

                    result = await full_assistant("What's this about?")
                    assert isinstance(result, str)
                    assert result == "Combined response"
