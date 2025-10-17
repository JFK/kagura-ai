"""Tests for ChatSession"""
import json
from unittest.mock import AsyncMock, patch

import pytest

from kagura.chat.session import ChatSession


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create temporary session directory"""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    return session_dir


@pytest.fixture
def chat_session(temp_session_dir):
    """Create ChatSession instance"""
    session = ChatSession(session_dir=temp_session_dir)
    # Disable compression for predictable test behavior
    session.memory.enable_compression = False
    session.memory.context_manager = None
    return session


def test_chat_session_initialization(chat_session, temp_session_dir):
    """Test ChatSession initialization"""
    assert chat_session.model == "gpt-5-mini"
    assert chat_session.session_dir == temp_session_dir
    assert chat_session.memory is not None


def test_show_welcome(chat_session):
    """Test welcome message display"""
    # Should not raise errors
    chat_session.show_welcome()


def test_show_help(chat_session):
    """Test help message display"""
    # Should not raise errors
    chat_session.show_help()


@pytest.mark.asyncio
async def test_clear_history(chat_session):
    """Test clearing conversation history"""
    # Add some messages
    chat_session.memory.add_message("user", "Hello")
    chat_session.memory.add_message("assistant", "Hi")

    # Clear
    chat_session.clear_history()

    # Verify cleared
    messages = await chat_session.memory.get_llm_context()
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_save_session(chat_session, temp_session_dir):
    """Test saving session"""
    # Add some messages
    chat_session.memory.add_message("user", "Hello")
    chat_session.memory.add_message("assistant", "Hi")

    # Save session
    session_name = "test_session"
    await chat_session.save_session(session_name)

    # Verify file exists
    session_file = temp_session_dir / f"{session_name}.json"
    assert session_file.exists()

    # Verify content
    with open(session_file) as f:
        data = json.load(f)

    assert data["name"] == session_name
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_save_session_auto_name(chat_session, temp_session_dir):
    """Test saving session with auto-generated name"""
    chat_session.memory.add_message("user", "Test")

    # Save with auto-generated name
    await chat_session.save_session()

    # Verify at least one .json file exists
    json_files = list(temp_session_dir.glob("*.json"))
    assert len(json_files) >= 1


@pytest.mark.asyncio
async def test_load_session(chat_session, temp_session_dir):
    """Test loading session"""
    # Create a session file manually
    session_name = "load_test"
    session_data = {
        "name": session_name,
        "created_at": "2025-01-01T00:00:00",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ],
    }

    session_file = temp_session_dir / f"{session_name}.json"
    with open(session_file, "w") as f:
        json.dump(session_data, f)

    # Load session
    await chat_session.load_session(session_name)

    # Verify messages loaded
    messages = await chat_session.memory.get_llm_context()
    assert len(messages) == 2
    assert messages[0]["content"] == "Hello"
    assert messages[1]["content"] == "Hi there"


@pytest.mark.asyncio
async def test_load_nonexistent_session(chat_session):
    """Test loading non-existent session"""
    # Should not raise error, just print message
    await chat_session.load_session("nonexistent")


def test_model_switching(chat_session):
    """Test /model command switches model"""
    assert chat_session.model == "gpt-4o-mini"

    # Switch model
    chat_session.handle_model_command("gpt-5")
    assert chat_session.model == "gpt-5"

    # Switch again
    chat_session.handle_model_command("claude-3.5-sonnet")
    assert chat_session.model == "claude-3.5-sonnet"


@pytest.mark.asyncio
async def test_chat_interaction(chat_session):
    """Test basic chat interaction"""
    # Mock the agent decorator to return our mock agent
    async def mock_agent_func(prompt, memory):
        return "AI response"

    with patch("kagura.chat.session.agent") as mock_decorator:
        # Make decorator return a function that returns our mock
        mock_decorator.return_value = lambda func: mock_agent_func

        await chat_session.chat("Hello")

        # Verify decorator was called with correct model
        assert mock_decorator.called

        # Verify messages in memory
        messages = await chat_session.memory.get_llm_context()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
