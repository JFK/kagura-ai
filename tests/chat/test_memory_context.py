"""
Tests for chat memory context functionality
"""

import tempfile
from pathlib import Path

import pytest

from kagura.chat.session import ChatSession


@pytest.fixture
def temp_session_dir():
    """Create temporary session directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.asyncio
async def test_chat_memory_preserves_context(temp_session_dir: Path) -> None:
    """Test that chat memory preserves conversation context"""
    session = ChatSession(
        session_dir=temp_session_dir,
    )

    # Add messages to memory
    session.memory.add_message("user", "私の名前は清田です。")
    session.memory.add_message("assistant", "こんにちは、清田さん！")
    session.memory.add_message("user", "私の名前は？")

    # Get LLM context
    context = await session.memory.get_llm_context()

    # Should have individual messages, not compressed summary
    assert len(context) == 3

    # Check message structure
    assert context[0]["role"] == "user"
    assert "清田" in context[0]["content"]

    assert context[1]["role"] == "assistant"
    assert "清田さん" in context[1]["content"]

    assert context[2]["role"] == "user"
    assert "私の名前は" in context[2]["content"]


@pytest.mark.asyncio
async def test_chat_memory_no_compression(temp_session_dir: Path) -> None:
    """Test that chat session has compression disabled"""
    session = ChatSession(
        session_dir=temp_session_dir,
    )

    # Verify compression is disabled
    assert session.memory.enable_compression is False
    assert session.memory.context_manager is None


@pytest.mark.asyncio
async def test_chat_memory_multiple_turns(temp_session_dir: Path) -> None:
    """Test memory with multiple conversation turns"""
    session = ChatSession(
        session_dir=temp_session_dir,
    )

    # Simulate multiple turns
    turns = [
        ("user", "こんにちは"),
        ("assistant", "こんにちは！どのようにお手伝いできますか？"),
        ("user", "私はPythonを学んでいます"),
        ("assistant", "素晴らしいですね！Pythonは素晴らしい言語です。"),
        ("user", "おすすめの学習方法は？"),
    ]

    for role, content in turns:
        session.memory.add_message(role, content)

    # Get context
    context = await session.memory.get_llm_context()

    # Should preserve all messages
    assert len(context) == 5

    # Verify order
    for i, (expected_role, expected_content) in enumerate(turns):
        assert context[i]["role"] == expected_role
        assert expected_content in context[i]["content"]
