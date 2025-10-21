"""Tests for Memory MCP tools."""

import pytest

from kagura.mcp.builtin.memory import (
    _memory_cache,
    memory_recall,
    memory_search,
    memory_store,
)


@pytest.fixture(autouse=True)
def clear_memory_cache():
    """Clear global memory cache before and after each test"""
    _memory_cache.clear()
    yield
    _memory_cache.clear()


class TestMemoryStore:
    """Test memory_store tool."""

    @pytest.mark.asyncio
    async def test_store_working_memory(self) -> None:
        """Test storing value in working memory"""
        result = await memory_store(
            agent_name="test_agent",
            key="test_key",
            value="test_value",
            scope="working",
        )

        assert "Stored" in result
        assert "test_key" in result
        assert "working" in result


class TestMemoryRecall:
    """Test memory_recall tool."""

    @pytest.mark.asyncio
    async def test_recall_not_found_message(self) -> None:
        """Test that recall returns helpful message when key not found (regression test for #333)"""
        result = await memory_recall(
            agent_name="test_agent_nonexistent",
            key="nonexistent_key",
            scope="working",
        )

        # Should return helpful message, not empty string
        assert result != ""
        assert "No value found" in result
        assert "nonexistent_key" in result
        assert "working" in result

    @pytest.mark.asyncio
    async def test_recall_after_store(self) -> None:
        """Test recalling a value after storing it (regression test for cache fix)"""
        # Store a value
        store_result = await memory_store(
            agent_name="test_agent_cached",
            key="cached_key",
            value="cached_value",
            scope="working",
        )
        assert "Stored" in store_result

        # Recall should now work (using cached MemoryManager)
        result = await memory_recall(
            agent_name="test_agent_cached", key="cached_key", scope="working"
        )

        # Should retrieve the stored value (not "No value found")
        assert result == "cached_value"
        assert "No value found" not in result

    @pytest.mark.asyncio
    async def test_recall_different_agents_isolated(self) -> None:
        """Test that different agents have isolated memory spaces"""
        # Store for agent1
        await memory_store(
            agent_name="agent1", key="shared_key", value="value_from_agent1"
        )

        # Store for agent2
        await memory_store(
            agent_name="agent2", key="shared_key", value="value_from_agent2"
        )

        # Recall for agent1 - should get agent1's value
        result1 = await memory_recall(agent_name="agent1", key="shared_key")
        assert result1 == "value_from_agent1"

        # Recall for agent2 - should get agent2's value
        result2 = await memory_recall(agent_name="agent2", key="shared_key")
        assert result2 == "value_from_agent2"

    @pytest.mark.asyncio
    async def test_multiple_keys_same_agent(self) -> None:
        """Test storing and recalling multiple keys for same agent"""
        agent = "multi_key_agent"

        # Store multiple values
        await memory_store(agent, "name", "Alice")
        await memory_store(agent, "age", "25")
        await memory_store(agent, "city", "Tokyo")

        # Recall all values
        name = await memory_recall(agent, "name")
        age = await memory_recall(agent, "age")
        city = await memory_recall(agent, "city")

        assert name == "Alice"
        assert age == "25"
        assert city == "Tokyo"


class TestMemorySearch:
    """Test memory_search tool."""

    @pytest.mark.asyncio
    async def test_k_string_conversion(self) -> None:
        """Test that k parameter handles string input (regression test for #333)"""
        import json

        # Pass k as string - should be converted to int
        result = await memory_search(
            agent_name="test_agent", query="test query", k="5"  # type: ignore[arg-type]
        )

        # Should get proper JSON response, not TypeError
        # The fact that we got here without TypeError proves the fix works
        data = json.loads(result)

        # Either error (ChromaDB not installed) or empty results
        # Both are acceptable - the important thing is no TypeError
        assert isinstance(data, (dict, list))


class TestMemoryCaching:
    """Test MemoryManager caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_reuses_instance(self) -> None:
        """Test that same agent_name reuses MemoryManager instance"""
        # First call creates instance
        await memory_store("cached_agent", "key1", "value1")

        # Check cache has entry
        assert len(_memory_cache) == 1
        assert "cached_agent:rag=False" in _memory_cache

        # Second call should reuse instance
        await memory_store("cached_agent", "key2", "value2")

        # Cache should still have only 1 entry
        assert len(_memory_cache) == 1

    @pytest.mark.asyncio
    async def test_cache_separate_rag_instances(self) -> None:
        """Test that RAG and non-RAG instances are cached separately"""
        # Regular memory call
        await memory_store("agent_rag", "key1", "value1")

        # RAG memory call
        await memory_search("agent_rag", "query", k=5)

        # Should have 2 cache entries (one with RAG, one without)
        assert len(_memory_cache) == 2
        assert "agent_rag:rag=False" in _memory_cache
        assert "agent_rag:rag=True" in _memory_cache
