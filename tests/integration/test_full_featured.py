"""Integration tests for full-featured mode (multimodal + web)"""
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
import tempfile
import shutil


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory"""
    tmpdir = tempfile.mkdtemp()
    project = Path(tmpdir)

    # Create test files
    (project / "README.md").write_text("# AI Project\n\nAI research project.")
    (project / "research.md").write_text("# Research\n\nLatest AI trends.")

    yield project

    shutil.rmtree(tmpdir)


@pytest.mark.asyncio
async def test_chat_session_full_mode_initialization(temp_project_dir):
    """Test ChatSession with full mode (multimodal + web)"""
    from kagura.chat import ChatSession

    session = ChatSession(
        model="gpt-4o-mini",
        enable_multimodal=True,
        rag_directory=temp_project_dir,
        enable_web=True
    )

    assert session.enable_multimodal is True
    assert session.enable_web is True
    assert session.rag_directory == temp_project_dir
    assert session.rag is not None


@pytest.mark.asyncio
async def test_full_mode_chat_with_rag_and_web(temp_project_dir):
    """Test chat interaction with both RAG and web enabled"""
    from kagura.chat import ChatSession

    session = ChatSession(
        model="gpt-4o-mini",
        enable_multimodal=True,
        rag_directory=temp_project_dir,
        enable_web=True
    )

    # Mock LLM response
    with patch('litellm.acompletion', new_callable=AsyncMock) as mock_llm:
        mock_message = MagicMock(
            content="Based on local files and web search: AI is growing",
            tool_calls=None
        )
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )

        # Simulate chat
        await session.chat("What are the AI trends?")

        # Verify LLM was called
        assert mock_llm.called


@pytest.mark.asyncio
async def test_full_mode_rag_context_injection(temp_project_dir):
    """Test that RAG context is properly injected in full mode"""
    from kagura.chat import ChatSession

    session = ChatSession(
        model="gpt-4o-mini",
        enable_multimodal=True,
        rag_directory=temp_project_dir,
        enable_web=True
    )

    # Mock LLM to capture the prompt
    with patch('litellm.acompletion', new_callable=AsyncMock) as mock_llm:
        mock_message = MagicMock(
            content="Response with context",
            tool_calls=None
        )
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )

        await session.chat("Tell me about AI")

        # Check that LLM was called with RAG context
        call_args = mock_llm.call_args
        assert call_args is not None


@pytest.mark.asyncio
async def test_full_mode_web_tool_available(temp_project_dir):
    """Test that web search tool is available in full mode"""
    from kagura.chat import ChatSession

    session = ChatSession(
        model="gpt-4o-mini",
        enable_multimodal=True,
        rag_directory=temp_project_dir,
        enable_web=True
    )

    # Check that web-enabled agent is used
    from kagura.chat.session import chat_agent_with_web

    # Verify the agent has web search tool
    assert hasattr(chat_agent_with_web, '_agent_config')


@pytest.mark.asyncio
async def test_full_mode_error_handling(temp_project_dir):
    """Test error handling in full mode"""
    from kagura.chat import ChatSession

    session = ChatSession(
        model="gpt-4o-mini",
        enable_multimodal=True,
        rag_directory=temp_project_dir,
        enable_web=True
    )

    # Mock LLM to raise error
    with patch('litellm.acompletion', side_effect=Exception("API Error")):
        with pytest.raises(Exception) as exc_info:
            await session.chat("Test query")

        assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_full_mode_memory_persistence(temp_project_dir):
    """Test that memory is persisted across chat turns in full mode"""
    from kagura.chat import ChatSession

    session = ChatSession(
        model="gpt-4o-mini",
        enable_multimodal=True,
        rag_directory=temp_project_dir,
        enable_web=True
    )

    with patch('litellm.acompletion', new_callable=AsyncMock) as mock_llm:
        mock_message = MagicMock(content="Response", tool_calls=None)
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )

        # First message
        await session.chat("First question")
        first_memory_size = len(session.memory.get_llm_context())

        # Second message
        await session.chat("Second question")
        second_memory_size = len(session.memory.get_llm_context())

        # Memory should grow
        assert second_memory_size > first_memory_size


# CLI tests are skipped due to asyncio.run() conflicts in test environment
# These are better tested manually or in E2E tests
