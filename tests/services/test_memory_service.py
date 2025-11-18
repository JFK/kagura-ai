"""Tests for MemoryService."""

from __future__ import annotations

import pytest

from kagura.services.memory_service import MemoryResult, MemoryService, SearchResult


class MockMemoryManager:
    """Mock MemoryManager for testing."""

    def __init__(self, user_id: str = "test_user", agent_name: str = "test_agent"):
        self.user_id = user_id
        self.agent_name = agent_name
        self.storage: dict[str, tuple[str, dict]] = {}  # key -> (value, metadata)

    async def store(self, key: str, value: str, metadata: dict) -> None:
        """Mock store operation."""
        self.storage[key] = (value, metadata)

    async def recall(self, key: str) -> str | None:
        """Mock recall operation."""
        if key in self.storage:
            return self.storage[key][0]
        return None

    async def delete(self, key: str) -> bool:
        """Mock delete operation."""
        if key in self.storage:
            del self.storage[key]
            return True
        return False

    async def search(self, query: str, k: int = 10) -> list[dict]:
        """Mock search operation."""
        # Simple mock: return all items containing query substring
        results = []
        for key, (value, metadata) in self.storage.items():
            if query.lower() in value.lower() or query.lower() in key.lower():
                results.append(
                    {
                        "key": key,
                        "value": value,
                        "metadata": metadata,
                    }
                )
        return results[:k]

    async def list_all(self) -> list[dict]:
        """Mock list all operation."""
        return [
            {"key": key, "value": value, "metadata": metadata}
            for key, (value, metadata) in self.storage.items()
        ]


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

    @pytest.mark.asyncio
    async def test_store_memory_success(self, memory_service, mock_memory_manager):
        """Test successful memory storage."""
        result = await memory_service.store_memory(
            key="test_key",
            value="test value",
            tags=["test", "example"],
            importance=0.8,
        )

        assert result.success is True
        assert result.key == "test_key"
        assert "successfully" in result.message.lower()

        # Verify actually stored
        stored_value = await mock_memory_manager.recall("test_key")
        assert stored_value == "test value"

    @pytest.mark.asyncio
    async def test_store_memory_validation(self, memory_service):
        """Test memory storage validation."""
        # Empty key
        with pytest.raises(ValueError, match="key"):
            await memory_service.store_memory(key="", value="test")

        # Empty value
        with pytest.raises(ValueError, match="value"):
            await memory_service.store_memory(key="test", value="")

        # Invalid importance
        with pytest.raises(ValueError, match="importance"):
            await memory_service.store_memory(
                key="test", value="test", importance=1.5
            )

        with pytest.raises(ValueError, match="importance"):
            await memory_service.store_memory(
                key="test", value="test", importance=-0.1
            )

    @pytest.mark.asyncio
    async def test_store_memory_with_metadata(self, memory_service, mock_memory_manager):
        """Test memory storage with custom metadata."""
        custom_metadata = {"source": "user", "category": "preference"}

        result = await memory_service.store_memory(
            key="pref_key",
            value="dark mode",
            metadata=custom_metadata,
        )

        assert result.success is True

        # Verify metadata was stored
        _, stored_metadata = mock_memory_manager.storage["pref_key"]
        assert stored_metadata["metadata"] == custom_metadata

    @pytest.mark.asyncio
    async def test_recall_memory_success(self, memory_service, mock_memory_manager):
        """Test successful memory recall."""
        # Store first
        await mock_memory_manager.store("existing_key", "existing value", {})

        # Recall
        result = await memory_service.recall_memory("existing_key")

        assert result.success is True
        assert result.key == "existing_key"
        assert result.metadata["value"] == "existing value"

    @pytest.mark.asyncio
    async def test_recall_memory_not_found(self, memory_service):
        """Test recalling non-existent memory."""
        result = await memory_service.recall_memory("nonexistent_key")

        assert result.success is False
        assert "not found" in result.message.lower()

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, memory_service, mock_memory_manager):
        """Test successful memory deletion."""
        # Store first
        await mock_memory_manager.store("delete_me", "value", {})

        # Delete
        result = await memory_service.delete_memory("delete_me")

        assert result.success is True
        assert "successfully" in result.message.lower()

        # Verify actually deleted
        stored = await mock_memory_manager.recall("delete_me")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, memory_service):
        """Test deleting non-existent memory."""
        result = await memory_service.delete_memory("nonexistent")

        assert result.success is False
        assert "not found" in result.message.lower()

    @pytest.mark.asyncio
    async def test_search_memory(self, memory_service, mock_memory_manager):
        """Test memory search."""
        # Store some test data
        await mock_memory_manager.store("pref1", "dark mode preference", {"importance": 0.8})
        await mock_memory_manager.store("pref2", "light theme setting", {"importance": 0.5})
        await mock_memory_manager.store("goal", "project goal", {"importance": 0.9})

        # Search
        result = await memory_service.search_memory(query="mode", limit=10)

        assert isinstance(result, SearchResult)
        assert result.count >= 1
        assert any("dark mode" in r["value"] for r in result.results)

    @pytest.mark.asyncio
    async def test_search_memory_with_filters(self, memory_service, mock_memory_manager):
        """Test memory search with importance filter."""
        # Store data with different importance levels
        await mock_memory_manager.store("low", "low importance", {"importance": 0.3})
        await mock_memory_manager.store("high", "high importance", {"importance": 0.9})

        # Search with minimum importance
        result = await memory_service.search_memory(
            query="importance", min_importance=0.5
        )

        # Should only return high importance item
        assert result.count == 1
        assert result.results[0]["key"] == "high"

    @pytest.mark.asyncio
    async def test_list_memories(self, memory_service, mock_memory_manager):
        """Test listing all memories."""
        # Store multiple memories
        for i in range(5):
            await mock_memory_manager.store(f"key{i}", f"value{i}", {})

        # List all
        result = await memory_service.list_memories(limit=10)

        assert result.count == 5
        assert result.metadata["total"] == 5

    @pytest.mark.asyncio
    async def test_list_memories_pagination(self, memory_service, mock_memory_manager):
        """Test memory listing with pagination."""
        # Store 10 memories
        for i in range(10):
            await mock_memory_manager.store(f"key{i}", f"value{i}", {})

        # Get first page
        page1 = await memory_service.list_memories(limit=3, offset=0)
        assert page1.count == 3

        # Get second page
        page2 = await memory_service.list_memories(limit=3, offset=3)
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
