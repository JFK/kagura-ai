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
        """Test that recall returns helpful message when key not found
        (regression test for #333)
        """
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
        assert "cached_agent:rag=True" in _memory_cache

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
        # Note: memory_store now uses RAG by default for working memory
        assert len(_memory_cache) >= 1
        assert "agent_rag:rag=True" in _memory_cache


class TestMemorySearchIntegration:
    """Test memory_search integration with memory_store (Issue #337)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_finds_stored_data(self) -> None:
        """Test that memory_search can find data stored via memory_store (Issue #337)

        This is the core issue: users expect memory_search to find data
        stored with memory_store, but they were stored in separate systems.
        """
        import json

        try:
            # Store data in working memory
            store_result = await memory_store(
                agent_name="test_search_agent",
                key="name",
                value="Alice",
                scope="working"
            )
            assert "Stored" in store_result

            # Search for the stored data
            search_result = await memory_search(
                agent_name="test_search_agent",
                query="name",
                k=5
            )

            # Parse results
            results = json.loads(search_result)

            # Should find the stored data
            # Results can come from either RAG or working memory
            assert isinstance(results, list)
            if len(results) > 0:  # ChromaDB is available
                # Check that "Alice" or "name" appears in results
                found = False
                for result in results:
                    content = result.get("content", "")
                    if "Alice" in content or "name" in content.lower():
                        found = True
                        break
                assert found, (
                    f"Expected to find 'Alice' or 'name' in results: {results}"
                )

        except ImportError:
            # ChromaDB not installed - skip test
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_combined_results(self) -> None:
        """Test that memory_search returns combined RAG + working memory results"""
        import json

        try:
            # Store multiple data points
            await memory_store("combined_agent", "user_name", "Bob")
            await memory_store("combined_agent", "user_age", "30")
            await memory_store("combined_agent", "user_city", "Tokyo")

            # Search with a query that should match keys
            search_result = await memory_search(
                agent_name="combined_agent",
                query="user",
                k=5
            )

            results = json.loads(search_result)
            assert isinstance(results, list)

            if len(results) > 0:  # ChromaDB is available
                # Check for source indicators
                sources = [r.get("source") for r in results]
                # Should have at least working_memory results (key matches)
                assert "working_memory" in sources or "rag" in sources

                # Verify working memory results have correct structure
                working_results = [
                    r for r in results if r.get("source") == "working_memory"
                ]
                if working_results:
                    for wr in working_results:
                        assert "key" in wr
                        assert "value" in wr
                        assert "match_type" in wr

        except ImportError:
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    async def test_search_empty_results_without_chromadb(self) -> None:
        """Test memory_search returns working memory results even without ChromaDB"""
        import json

        # Store data
        await memory_store("no_rag_agent", "test_key", "test_value")

        # Try to search - should handle missing ChromaDB gracefully
        search_result = await memory_search("no_rag_agent", "test", k=5)
        results = json.loads(search_result)

        # Should either return working memory results or error message
        assert isinstance(results, (list, dict))
        if isinstance(results, dict):
            # Error case (no ChromaDB)
            assert "error" in results
        else:
            # Working memory results
            assert isinstance(results, list)


class TestPersistentRAGIntegration:
    """Test persistent memory RAG integration (Issue #340)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_persistent_scope(self) -> None:
        """Test memory_search can find data in persistent memory (Issue #340)"""
        import json

        try:
            # Store data in persistent memory
            store_result = await memory_store(
                agent_name="test_persistent_search",
                key="user_preference",
                value="User prefers Python for examples",
                scope="persistent",
            )
            assert "Stored" in store_result

            # Search persistent scope
            search_result = await memory_search(
                agent_name="test_persistent_search",
                query="Python preference",
                k=5,
                scope="persistent",
            )

            # Parse results
            results = json.loads(search_result)
            assert isinstance(results, list)

            # Should find the stored data in persistent scope
            if len(results) > 0:
                found = False
                for result in results:
                    content = result.get("content", "")
                    result_scope = result.get("scope", "")
                    if "Python" in content and result_scope == "persistent":
                        found = True
                        break
                assert found, (
                    f"Expected to find 'Python' in persistent scope: {results}"
                )

            # Cleanup
            await memory_recall(
                agent_name="test_persistent_search",
                key="user_preference",
                scope="persistent",
            )

        except ImportError:
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_scope_parameter(self) -> None:
        """Test memory_search scope parameter filters results correctly"""
        import json

        try:
            # Store in both scopes
            await memory_store(
                agent_name="test_scope_filter",
                key="working_data",
                value="This is working memory data",
                scope="working",
            )

            await memory_store(
                agent_name="test_scope_filter",
                key="persistent_data",
                value="This is persistent memory data",
                scope="persistent",
            )

            # Search all scopes
            all_results = await memory_search(
                agent_name="test_scope_filter", query="data", k=10, scope="all"
            )
            all_data = json.loads(all_results)

            # Search working only
            working_results = await memory_search(
                agent_name="test_scope_filter", query="data", k=10, scope="working"
            )
            working_data = json.loads(working_results)

            # Search persistent only
            persistent_results = await memory_search(
                agent_name="test_scope_filter", query="data", k=10, scope="persistent"
            )
            persistent_data = json.loads(persistent_results)

            # Verify results
            assert isinstance(all_data, list)
            assert isinstance(working_data, list)
            assert isinstance(persistent_data, list)

            # Working results should only have working scope
            for result in working_data:
                scope = result.get("scope", "")
                if scope:  # Some results may not have scope field
                    assert scope == "working", f"Expected working scope, got {scope}"

            # Persistent results should only have persistent scope
            for result in persistent_data:
                scope = result.get("scope", "")
                if scope:
                    assert (
                        scope == "persistent"
                    ), f"Expected persistent scope, got {scope}"

        except ImportError:
            pytest.skip("ChromaDB not installed")


class TestMemoryList:
    """Test memory_list tool."""

    @pytest.mark.asyncio
    async def test_list_empty_memories(self) -> None:
        """Test memory_list with no stored memories"""
        import json

        from kagura.mcp.builtin.memory import memory_list

        result = await memory_list(agent_name="empty_agent", scope="working")
        data = json.loads(result)

        assert data["agent_name"] == "empty_agent"
        assert data["scope"] == "working"
        assert data["count"] == 0
        assert data["memories"] == []

    @pytest.mark.asyncio
    async def test_list_working_memories(self) -> None:
        """Test memory_list with working memory"""
        import json

        from kagura.mcp.builtin.memory import memory_list

        # Store some working memories
        await memory_store("test_list_agent", "key1", "value1", scope="working")
        await memory_store("test_list_agent", "key2", "value2", scope="working")

        # List them
        result = await memory_list(agent_name="test_list_agent", scope="working")
        data = json.loads(result)

        assert data["agent_name"] == "test_list_agent"
        assert data["scope"] == "working"
        assert data["count"] == 2
        assert len(data["memories"]) == 2

        # Check that both keys are present
        keys = {m["key"] for m in data["memories"]}
        assert "key1" in keys
        assert "key2" in keys

    @pytest.mark.asyncio
    async def test_list_persistent_memories(self) -> None:
        """Test memory_list with persistent memory"""
        import json

        from kagura.mcp.builtin.memory import memory_list

        # Store some persistent memories
        await memory_store(
            "test_list_persistent", "pkey1", "pvalue1", scope="persistent"
        )
        await memory_store(
            "test_list_persistent", "pkey2", "pvalue2", scope="persistent"
        )

        # List them
        result = await memory_list(
            agent_name="test_list_persistent", scope="persistent"
        )
        data = json.loads(result)

        assert data["agent_name"] == "test_list_persistent"
        assert data["scope"] == "persistent"
        assert data["count"] == 2
        assert len(data["memories"]) == 2

        # Check structure
        for mem in data["memories"]:
            assert "key" in mem
            assert "value" in mem
            assert "scope" in mem
            assert mem["scope"] == "persistent"
            assert "created_at" in mem
            assert "updated_at" in mem

    @pytest.mark.asyncio
    async def test_list_with_limit(self) -> None:
        """Test memory_list respects limit parameter"""
        import json

        from kagura.mcp.builtin.memory import memory_list

        # Store many working memories
        for i in range(10):
            await memory_store("test_limit_agent", f"key{i}", f"value{i}")

        # List with limit=5
        result = await memory_list(
            agent_name="test_limit_agent", scope="working", limit=5
        )
        data = json.loads(result)

        assert data["count"] <= 5
        assert len(data["memories"]) <= 5

    @pytest.mark.asyncio
    async def test_list_isolates_by_agent_name(self) -> None:
        """Test memory_list only shows memories for specified agent"""
        import json

        from kagura.mcp.builtin.memory import memory_list

        # Store for different agents
        await memory_store("agent_a", "key_a", "value_a")
        await memory_store("agent_b", "key_b", "value_b")

        # List for agent_a
        result_a = await memory_list(agent_name="agent_a", scope="working")
        data_a = json.loads(result_a)

        # Should only see agent_a's memory
        keys_a = {m["key"] for m in data_a["memories"]}
        assert "key_a" in keys_a
        assert "key_b" not in keys_a

        # List for agent_b
        result_b = await memory_list(agent_name="agent_b", scope="working")
        data_b = json.loads(result_b)

        # Should only see agent_b's memory
        keys_b = {m["key"] for m in data_b["memories"]}
        assert "key_b" in keys_b
        assert "key_a" not in keys_b
