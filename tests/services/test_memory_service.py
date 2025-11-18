"""Tests for MemoryService."""

from __future__ import annotations

import pytest

from kagura.services.memory_service import MemoryResult, MemoryService, SearchResult


class MockPersistentMemory:
    """Mock PersistentMemory for testing."""

    def __init__(self):
        self.storage: dict[str, tuple[str, dict]] = {}  # key -> (value, metadata)

    def store(self, key: str, value: str, user_id: str, agent_name: str | None, metadata: dict) -> None:
        """Mock store operation."""
        self.storage[key] = (value, metadata)

    def recall(self, key: str, user_id: str, agent_name: str | None, track_access: bool = False, include_metadata: bool = False) -> str | None:
        """Mock recall operation."""
        if key in self.storage:
            return self.storage[key][0]
        return None

    def forget(self, key: str, user_id: str, agent_name: str | None) -> None:
        """Mock delete operation."""
        if key in self.storage:
            del self.storage[key]

    def fetch_all(self, user_id: str, agent_name: str | None) -> list[dict]:
        """Mock list all operation."""
        return [
            {"key": key, "value": value, "metadata": metadata}
            for key, (value, metadata) in self.storage.items()
        ]


class MockMemoryManager:
    """Mock MemoryManager for testing."""

    def __init__(self, user_id: str = "test_user", agent_name: str = "test_agent"):
        self.user_id = user_id
        self.agent_name = agent_name
        self.persistent = MockPersistentMemory()

    def recall(self, key: str) -> str | None:
        """Mock recall operation via persistent."""
        return self.persistent.recall(key, self.user_id, self.agent_name)

    def forget(self, key: str) -> None:
        """Mock delete operation via persistent."""
        self.persistent.forget(key, self.user_id, self.agent_name)

    def search_memory(self, query: str, limit: int = 10) -> list[dict]:
        """Mock search operation."""
        # Simple mock: return all items containing query substring
        results = []
        for key, (value, metadata) in self.persistent.storage.items():
            if query.lower() in value.lower() or query.lower() in key.lower():
                results.append(
                    {
                        "key": key,
                        "value": value,
                        "metadata": metadata,
                    }
                )
        return results[:limit]


@pytest.fixture
def mock_memory_manager():
    """Create mock memory manager."""
    return MockMemoryManager()


@pytest.fixture
def memory_service(mock_memory_manager):
    """Create MemoryService with mock."""
    return MemoryService(mock_memory_manager)


class TestMemoryService:
    """Test suite for MemoryService."""

    def test_store_memory_success(self, memory_service, mock_memory_manager):
        """Test successful memory storage."""
        result = memory_service.store_memory(
            key="test_key",
            value="test value",
            tags=["test", "example"],
            importance=0.8,
        )

        assert result.success is True
        assert result.key == "test_key"
        assert "successfully" in result.message.lower()

        # Verify actually stored
        stored_value = mock_memory_manager.recall("test_key")
        assert stored_value == "test value"

    def test_store_memory_validation(self, memory_service):
        """Test memory storage validation."""
        # Empty key
        with pytest.raises(ValueError, match="key"):
            memory_service.store_memory(key="", value="test")

        # Empty value
        with pytest.raises(ValueError, match="value"):
            memory_service.store_memory(key="test", value="")

        # Invalid importance
        with pytest.raises(ValueError, match="importance"):
            memory_service.store_memory(
                key="test", value="test", importance=1.5
            )

        with pytest.raises(ValueError, match="importance"):
            memory_service.store_memory(
                key="test", value="test", importance=-0.1
            )

    def test_store_memory_with_metadata(self, memory_service, mock_memory_manager):
        """Test memory storage with custom metadata."""
        custom_metadata = {"source": "user", "category": "preference"}

        result = memory_service.store_memory(
            key="pref_key",
            value="dark mode",
            metadata=custom_metadata,
        )

        assert result.success is True

        # Verify metadata was stored
        _, stored_metadata = mock_memory_manager.persistent.storage["pref_key"]
        assert stored_metadata["metadata"] == custom_metadata

    def test_recall_memory_success(self, memory_service, mock_memory_manager):
        """Test successful memory recall."""
        # Store first
        mock_memory_manager.persistent.store("existing_key", "existing value", "test_user", "test_agent", {})

        # Recall
        result = memory_service.recall_memory("existing_key")

        assert result.success is True
        assert result.key == "existing_key"
        assert result.metadata["value"] == "existing value"

    def test_recall_memory_not_found(self, memory_service):
        """Test recalling non-existent memory."""
        result = memory_service.recall_memory("nonexistent_key")

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_delete_memory_success(self, memory_service, mock_memory_manager):
        """Test successful memory deletion."""
        # Store first
        mock_memory_manager.persistent.store("delete_me", "value", "test_user", "test_agent", {})

        # Delete
        result = memory_service.delete_memory("delete_me")

        assert result.success is True
        assert "successfully" in result.message.lower()

        # Verify actually deleted
        stored = mock_memory_manager.recall("delete_me")
        assert stored is None

    def test_delete_memory_not_found(self, memory_service):
        """Test deleting non-existent memory."""
        result = memory_service.delete_memory("nonexistent")

        # Note: forget() doesn't raise error for non-existent keys
        # So this test expects success=True (no-op deletion)
        assert result.success is True

    def test_search_memory(self, memory_service, mock_memory_manager):
        """Test memory search."""
        # Store some test data
        mock_memory_manager.persistent.store("pref1", "dark mode preference", "test_user", "test_agent", {"importance": 0.8})
        mock_memory_manager.persistent.store("pref2", "light theme setting", "test_user", "test_agent", {"importance": 0.5})
        mock_memory_manager.persistent.store("goal", "project goal", "test_user", "test_agent", {"importance": 0.9})

        # Search
        result = memory_service.search_memory(query="mode", limit=10)

        assert isinstance(result, SearchResult)
        assert result.count >= 1
        assert any("dark mode" in r["value"] for r in result.results)

    def test_search_memory_with_filters(self, memory_service, mock_memory_manager):
        """Test memory search with importance filter."""
        # Store data with different importance levels
        mock_memory_manager.persistent.store("low", "low importance", "test_user", "test_agent", {"importance": 0.3})
        mock_memory_manager.persistent.store("high", "high importance", "test_user", "test_agent", {"importance": 0.9})

        # Search with minimum importance
        result = memory_service.search_memory(
            query="importance", min_importance=0.5
        )

        # Should only return high importance item
        assert result.count == 1
        assert result.results[0]["key"] == "high"

    def test_list_memories(self, memory_service, mock_memory_manager):
        """Test listing all memories."""
        # Store multiple memories
        for i in range(5):
            mock_memory_manager.persistent.store(f"key{i}", f"value{i}", "test_user", "test_agent", {})

        # List all
        result = memory_service.list_memories(limit=10)

        assert result.count == 5
        assert result.metadata["total"] == 5

    def test_list_memories_pagination(self, memory_service, mock_memory_manager):
        """Test memory listing with pagination."""
        # Store 10 memories
        for i in range(10):
            mock_memory_manager.persistent.store(f"key{i}", f"value{i}", "test_user", "test_agent", {})

        # Get first page
        page1 = memory_service.list_memories(limit=3, offset=0)
        assert page1.count == 3

        # Get second page
        page2 = memory_service.list_memories(limit=3, offset=3)
        assert page2.count == 3

        # Pages should have different items
        page1_keys = {r["key"] for r in page1.results}
        page2_keys = {r["key"] for r in page2.results}
        assert page1_keys != page2_keys

    def test_memory_result_dataclass(self):
        """Test MemoryResult dataclass."""
        result = MemoryResult(
            key="test",
            success=True,
            message="Test message",
        )

        assert result.key == "test"
        assert result.success is True
        assert result.message == "Test message"
        assert result.metadata == {}

    def test_search_result_dataclass(self):
        """Test SearchResult dataclass."""
        result = SearchResult(
            results=[{"key": "test", "value": "test value"}],
            count=1,
        )

        assert result.count == 1
        assert len(result.results) == 1
        assert result.metadata == {}
