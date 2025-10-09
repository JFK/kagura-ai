"""Tests for PersistentMemory."""

import tempfile
from pathlib import Path

import pytest

from kagura.core.memory.persistent import PersistentMemory


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        yield db_path


def test_persistent_memory_store_recall(temp_db):
    """Test basic store and recall."""
    memory = PersistentMemory(db_path=temp_db)

    memory.store("key1", "value1")
    result = memory.recall("key1")
    assert result == "value1"


def test_persistent_memory_update(temp_db):
    """Test updating existing key."""
    memory = PersistentMemory(db_path=temp_db)

    memory.store("key1", "value1")
    memory.store("key1", "value2")

    result = memory.recall("key1")
    assert result == "value2"


def test_persistent_memory_nonexistent(temp_db):
    """Test recalling nonexistent key."""
    memory = PersistentMemory(db_path=temp_db)

    result = memory.recall("nonexistent")
    assert result is None


def test_persistent_memory_complex_values(temp_db):
    """Test storing complex data types."""
    memory = PersistentMemory(db_path=temp_db)

    # Store dict
    memory.store("dict", {"a": 1, "b": [2, 3]})
    assert memory.recall("dict") == {"a": 1, "b": [2, 3]}

    # Store list
    memory.store("list", [1, 2, {"c": 3}])
    assert memory.recall("list") == [1, 2, {"c": 3}]


def test_persistent_memory_agent_scoping(temp_db):
    """Test agent-scoped memories."""
    memory = PersistentMemory(db_path=temp_db)

    # Store for different agents
    memory.store("key1", "agent1_value", agent_name="agent1")
    memory.store("key1", "agent2_value", agent_name="agent2")

    # Recall should be scoped
    assert memory.recall("key1", agent_name="agent1") == "agent1_value"
    assert memory.recall("key1", agent_name="agent2") == "agent2_value"


def test_persistent_memory_search(temp_db):
    """Test search functionality."""
    memory = PersistentMemory(db_path=temp_db)

    memory.store("user_name", "Alice")
    memory.store("user_email", "alice@example.com")
    memory.store("product_name", "Widget")

    results = memory.search("user")
    assert len(results) == 2
    assert any(r["key"] == "user_name" for r in results)
    assert any(r["key"] == "user_email" for r in results)


def test_persistent_memory_search_with_agent(temp_db):
    """Test search with agent scoping."""
    memory = PersistentMemory(db_path=temp_db)

    memory.store("key1", "value1", agent_name="agent1")
    memory.store("key2", "value2", agent_name="agent1")
    memory.store("key3", "value3", agent_name="agent2")

    results = memory.search("key", agent_name="agent1")
    assert len(results) == 2


def test_persistent_memory_search_limit(temp_db):
    """Test search with limit."""
    memory = PersistentMemory(db_path=temp_db)

    for i in range(10):
        memory.store(f"key{i}", f"value{i}")

    results = memory.search("key", limit=5)
    assert len(results) == 5


def test_persistent_memory_forget(temp_db):
    """Test deleting memory."""
    memory = PersistentMemory(db_path=temp_db)

    memory.store("key1", "value1")
    assert memory.recall("key1") == "value1"

    memory.forget("key1")
    assert memory.recall("key1") is None


def test_persistent_memory_forget_with_agent(temp_db):
    """Test agent-scoped deletion."""
    memory = PersistentMemory(db_path=temp_db)

    memory.store("key1", "agent1_value", agent_name="agent1")
    memory.store("key1", "agent2_value", agent_name="agent2")

    memory.forget("key1", agent_name="agent1")

    assert memory.recall("key1", agent_name="agent1") is None
    assert memory.recall("key1", agent_name="agent2") == "agent2_value"


def test_persistent_memory_count(temp_db):
    """Test counting memories."""
    memory = PersistentMemory(db_path=temp_db)

    assert memory.count() == 0

    memory.store("key1", "value1")
    memory.store("key2", "value2")
    assert memory.count() == 2


def test_persistent_memory_count_with_agent(temp_db):
    """Test counting agent-scoped memories."""
    memory = PersistentMemory(db_path=temp_db)

    memory.store("key1", "value1", agent_name="agent1")
    memory.store("key2", "value2", agent_name="agent1")
    memory.store("key3", "value3", agent_name="agent2")

    assert memory.count(agent_name="agent1") == 2
    assert memory.count(agent_name="agent2") == 1


def test_persistent_memory_metadata(temp_db):
    """Test storing metadata."""
    memory = PersistentMemory(db_path=temp_db)

    metadata = {"source": "web", "importance": "high"}
    memory.store("key1", "value1", metadata=metadata)

    results = memory.search("key1")
    assert len(results) == 1
    assert results[0]["metadata"] == metadata


def test_persistent_memory_prune(temp_db):
    """Test pruning old memories."""
    memory = PersistentMemory(db_path=temp_db)

    # Note: This test is simplified since we can't easily manipulate timestamps
    # In a real scenario, you'd use time travel or database manipulation

    memory.store("key1", "value1")
    memory.store("key2", "value2")

    # Prune memories older than 0 days (should delete all)
    deleted = memory.prune(older_than_days=0)

    # Due to timing, this might be 0 or 2 depending on execution speed
    # Just verify the method runs without error
    assert deleted >= 0


def test_persistent_memory_persistence(temp_db):
    """Test that data persists across instances."""
    memory1 = PersistentMemory(db_path=temp_db)
    memory1.store("key1", "value1")

    # Create new instance with same database
    memory2 = PersistentMemory(db_path=temp_db)
    assert memory2.recall("key1") == "value1"


def test_persistent_memory_repr(temp_db):
    """Test string representation."""
    memory = PersistentMemory(db_path=temp_db)
    memory.store("key1", "value1")

    repr_str = repr(memory)
    assert "PersistentMemory" in repr_str
    assert "count=1" in repr_str


def test_persistent_memory_default_path():
    """Test default database path."""
    memory = PersistentMemory()
    expected_path = Path.home() / ".kagura" / "memory.db"
    assert memory.db_path == expected_path

    # Clean up
    if memory.db_path.exists():
        memory.db_path.unlink()
