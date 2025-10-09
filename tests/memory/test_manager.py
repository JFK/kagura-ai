"""Tests for MemoryManager."""

import tempfile
from pathlib import Path

import pytest

from kagura.core.memory.manager import MemoryManager


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_manager_initialization():
    """Test basic initialization."""
    manager = MemoryManager()
    assert manager.working is not None
    assert manager.context is not None
    assert manager.persistent is not None


def test_manager_with_agent_name(temp_dir):
    """Test initialization with agent name."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)
    assert manager.agent_name == "test_agent"


def test_manager_working_memory():
    """Test working memory operations."""
    manager = MemoryManager()

    manager.set_temp("key1", "value1")
    assert manager.get_temp("key1") == "value1"
    assert manager.has_temp("key1") is True

    manager.delete_temp("key1")
    assert manager.has_temp("key1") is False


def test_manager_context_memory():
    """Test context memory operations."""
    manager = MemoryManager()

    manager.add_message("user", "Hello")
    manager.add_message("assistant", "Hi there!")

    messages = manager.get_context()
    assert len(messages) == 2
    assert messages[0].content == "Hello"


def test_manager_get_llm_context():
    """Test LLM format context."""
    manager = MemoryManager()

    manager.add_message("user", "Hello")
    manager.add_message("assistant", "Hi")

    llm_context = manager.get_llm_context()
    assert len(llm_context) == 2
    assert llm_context[0] == {"role": "user", "content": "Hello"}


def test_manager_get_last_message():
    """Test getting last message."""
    manager = MemoryManager()

    manager.add_message("user", "Message 1")
    manager.add_message("assistant", "Message 2")

    last_msg = manager.get_last_message()
    assert last_msg is not None
    assert last_msg.content == "Message 2"


def test_manager_session_id():
    """Test session ID management."""
    manager = MemoryManager()

    assert manager.get_session_id() is None

    manager.set_session_id("session-123")
    assert manager.get_session_id() == "session-123"


def test_manager_persistent_memory(temp_dir):
    """Test persistent memory operations."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)

    manager.remember("key1", "value1")
    assert manager.recall("key1") == "value1"

    manager.forget("key1")
    assert manager.recall("key1") is None


def test_manager_search_memory(temp_dir):
    """Test memory search."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)

    manager.remember("user_name", "Alice")
    manager.remember("user_email", "alice@example.com")

    results = manager.search_memory("user")
    assert len(results) == 2


def test_manager_prune_old(temp_dir):
    """Test pruning old memories."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)

    manager.remember("key1", "value1")

    # Prune should run without error
    deleted = manager.prune_old(older_than_days=0)
    assert deleted >= 0


def test_manager_save_session(temp_dir):
    """Test saving session."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)

    manager.set_temp("temp_key", "temp_value")
    manager.add_message("user", "Hello")
    manager.set_session_id("session-123")

    manager.save_session("test_session")

    # Verify session was saved
    session_data = manager.recall("session:test_session")
    assert session_data is not None
    assert "working" in session_data
    assert "context" in session_data


def test_manager_load_session(temp_dir):
    """Test loading session."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)

    # Create and save session
    manager.add_message("user", "Hello")
    manager.add_message("assistant", "Hi")
    manager.set_session_id("session-123")
    manager.save_session("test_session")

    # Clear and load
    manager.clear_all()
    assert len(manager.get_context()) == 0

    success = manager.load_session("test_session")
    assert success is True

    messages = manager.get_context()
    assert len(messages) == 2
    assert manager.get_session_id() == "session-123"


def test_manager_load_nonexistent_session(temp_dir):
    """Test loading nonexistent session."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)

    success = manager.load_session("nonexistent")
    assert success is False


def test_manager_clear_all():
    """Test clearing all memory."""
    manager = MemoryManager()

    manager.set_temp("temp_key", "temp_value")
    manager.add_message("user", "Hello")

    assert len(manager.working) > 0
    assert len(manager.context) > 0

    manager.clear_all()

    assert len(manager.working) == 0
    assert len(manager.context) == 0


def test_manager_metadata(temp_dir):
    """Test storing with metadata."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)

    metadata = {"source": "web", "importance": "high"}
    manager.remember("key1", "value1", metadata=metadata)

    results = manager.search_memory("key1")
    assert len(results) == 1
    assert results[0]["metadata"] == metadata


def test_manager_max_messages():
    """Test max_messages parameter."""
    manager = MemoryManager(max_messages=2)

    manager.add_message("user", "Message 1")
    manager.add_message("assistant", "Message 2")
    manager.add_message("user", "Message 3")

    # Should only keep last 2
    messages = manager.get_context()
    assert len(messages) == 2
    assert messages[0].content == "Message 2"


def test_manager_repr(temp_dir):
    """Test string representation."""
    manager = MemoryManager(agent_name="test_agent", persist_dir=temp_dir)

    manager.set_temp("key1", "value1")
    manager.add_message("user", "Hello")
    manager.remember("persistent_key", "persistent_value")

    repr_str = repr(manager)
    assert "MemoryManager" in repr_str
    assert "agent=test_agent" in repr_str
    assert "working=1" in repr_str
    assert "context=1" in repr_str
    assert "persistent=1" in repr_str


def test_manager_agent_scoping(temp_dir):
    """Test that different agents have separate memories."""
    manager1 = MemoryManager(agent_name="agent1", persist_dir=temp_dir)
    manager2 = MemoryManager(agent_name="agent2", persist_dir=temp_dir)

    manager1.remember("key1", "agent1_value")
    manager2.remember("key1", "agent2_value")

    assert manager1.recall("key1") == "agent1_value"
    assert manager2.recall("key1") == "agent2_value"


def test_manager_context_with_metadata():
    """Test adding messages with metadata."""
    manager = MemoryManager()

    metadata = {"user_id": 123, "source": "web"}
    manager.add_message("user", "Hello", metadata=metadata)

    messages = manager.get_context()
    assert messages[0].metadata == metadata
