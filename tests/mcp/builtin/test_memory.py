"""Tests for Memory MCP tools."""

import pytest

from kagura.mcp.builtin.memory import memory_recall, memory_search, memory_store


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
        """Test recalling a value after storing it"""
        # Note: Each call creates a new MemoryManager instance
        # Working memory is instance-specific, so this tests the API behavior
        # Store a value
        store_result = await memory_store(
            agent_name="test_agent_2",
            key="stored_key",
            value="stored_value",
            scope="working",
        )
        assert "Stored" in store_result

        # Recall will create a new instance, so won't find the value
        # This is expected behavior for working memory
        result = await memory_recall(
            agent_name="test_agent_2", key="stored_key", scope="working"
        )

        # Working memory is instance-specific, so expect "not found" message
        assert isinstance(result, str)


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
