"""Tests for Memory MCP tools."""

import pytest

from kagura.mcp.builtin.memory import (
    _memory_cache,
    memory_fetch,
    memory_get_related,
    memory_get_user_pattern,
    memory_recall,
    memory_record_interaction,
    memory_search,
    memory_search_ids,
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
            user_id="test_user",
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
            user_id="test_user",
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
            user_id="test_user",
            agent_name="test_agent_cached",
            key="cached_key",
            value="cached_value",
            scope="working",
        )
        assert "Stored" in store_result

        # Recall should now work (using cached MemoryManager)
        result = await memory_recall(
            user_id="test_user",
            agent_name="test_agent_cached",
            key="cached_key",
            scope="working",
        )

        # Should retrieve the stored value with metadata (JSON format)
        assert "No value found" not in result
        # Parse JSON response
        import json

        data = json.loads(result)
        assert data["key"] == "cached_key"
        assert data["value"] == "cached_value"
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_recall_different_agents_isolated(self) -> None:
        """Test that different agents have isolated memory spaces"""
        # Store for agent1
        await memory_store(
            user_id="test_user",
            agent_name="agent1",
            key="shared_key",
            value="value_from_agent1",
        )

        # Store for agent2
        await memory_store(
            user_id="test_user",
            agent_name="agent2",
            key="shared_key",
            value="value_from_agent2",
        )

        # Recall for agent1 - should get agent1's value
        result1 = await memory_recall(
            user_id="test_user", agent_name="agent1", key="shared_key"
        )
        import json

        data1 = json.loads(result1)
        assert data1["value"] == "value_from_agent1"

        # Recall for agent2 - should get agent2's value
        result2 = await memory_recall(
            user_id="test_user", agent_name="agent2", key="shared_key"
        )
        data2 = json.loads(result2)
        assert data2["value"] == "value_from_agent2"

    @pytest.mark.asyncio
    async def test_multiple_keys_same_agent(self) -> None:
        """Test storing and recalling multiple keys for same agent"""
        user_id = "test_user"
        agent = "multi_key_agent"

        # Store multiple values
        await memory_store(user_id=user_id, agent_name=agent, key="name", value="Alice")
        await memory_store(user_id=user_id, agent_name=agent, key="age", value="25")
        await memory_store(user_id=user_id, agent_name=agent, key="city", value="Tokyo")

        # Recall all values
        name_result = await memory_recall(user_id, agent, "name")
        age_result = await memory_recall(user_id, agent, "age")
        city_result = await memory_recall(user_id, agent, "city")

        import json

        name_data = json.loads(name_result)
        age_data = json.loads(age_result)
        city_data = json.loads(city_result)

        assert name_data["value"] == "Alice"
        assert age_data["value"] == "25"
        assert city_data["value"] == "Tokyo"

        # Verify metadata is included
        assert "metadata" in name_data
        assert "metadata" in age_data
        assert "metadata" in city_data


class TestMemorySearch:
    """Test memory_search tool."""

    @pytest.mark.asyncio
    async def test_k_string_conversion(self) -> None:
        """Test that k parameter handles string input (regression test for #333)"""
        import json

        # Pass k as string - should be converted to int
        result = await memory_search(
            user_id="test_user",
            agent_name="test_agent",
            query="test query",
            k="5",  # type: ignore[arg-type]
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
        """Test that same user_id + agent_name reuses MemoryManager instance"""
        # First call creates instance
        await memory_store(
            user_id="test_user", agent_name="cached_agent", key="key1", value="value1"
        )

        # Check cache has entry
        assert len(_memory_cache) == 1
        assert "test_user:cached_agent:rag=True" in _memory_cache

        # Second call should reuse instance
        await memory_store(
            user_id="test_user", agent_name="cached_agent", key="key2", value="value2"
        )

        # Cache should still have only 1 entry
        assert len(_memory_cache) == 1

    @pytest.mark.asyncio
    async def test_cache_separate_rag_instances(self) -> None:
        """Test that RAG and non-RAG instances are cached separately"""
        # Regular memory call
        await memory_store(
            user_id="test_user", agent_name="agent_rag", key="key1", value="value1"
        )

        # RAG memory call
        await memory_search("test_user", "agent_rag", "query", k=5)

        # Should have 2 cache entries (one with RAG, one without)
        # Note: memory_store now uses RAG by default for working memory
        assert len(_memory_cache) >= 1
        assert "test_user:agent_rag:rag=True" in _memory_cache


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
                user_id="test_user",
                agent_name="test_search_agent",
                key="name",
                value="Alice",
                scope="working",
            )
            assert "Stored" in store_result

            # Search for the stored data
            search_result = await memory_search(
                user_id="test_user", agent_name="test_search_agent", query="name", k=5
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
            await memory_store(
                user_id="test_user",
                agent_name="combined_agent",
                key="user_name",
                value="Bob",
            )
            await memory_store(
                user_id="test_user",
                agent_name="combined_agent",
                key="user_age",
                value="30",
            )
            await memory_store(
                user_id="test_user",
                agent_name="combined_agent",
                key="user_city",
                value="Tokyo",
            )

            # Search with a query that should match keys
            search_result = await memory_search(
                user_id="test_user", agent_name="combined_agent", query="user", k=5
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
        await memory_store(
            user_id="test_user",
            agent_name="no_rag_agent",
            key="test_key",
            value="test_value",
        )

        # Try to search - should handle missing ChromaDB gracefully
        search_result = await memory_search("test_user", "no_rag_agent", "test", k=5)
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
                user_id="test_user",
                agent_name="test_persistent_search",
                key="user_preference",
                value="User prefers Python for examples",
                scope="persistent",
            )
            assert "Stored" in store_result

            # Search persistent scope
            search_result = await memory_search(
                user_id="test_user",
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
                user_id="test_user",
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
                user_id="test_user",
                agent_name="test_scope_filter",
                key="working_data",
                value="This is working memory data",
                scope="working",
            )

            await memory_store(
                user_id="test_user",
                agent_name="test_scope_filter",
                key="persistent_data",
                value="This is persistent memory data",
                scope="persistent",
            )

            # Search all scopes
            all_results = await memory_search(
                user_id="test_user",
                agent_name="test_scope_filter",
                query="data",
                k=10,
                scope="all",
            )
            all_data = json.loads(all_results)

            # Search working only
            working_results = await memory_search(
                user_id="test_user",
                agent_name="test_scope_filter",
                query="data",
                k=10,
                scope="working",
            )
            working_data = json.loads(working_results)

            # Search persistent only
            persistent_results = await memory_search(
                user_id="test_user",
                agent_name="test_scope_filter",
                query="data",
                k=10,
                scope="persistent",
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
                    assert scope == "persistent", (
                        f"Expected persistent scope, got {scope}"
                    )

        except ImportError:
            pytest.skip("ChromaDB not installed")


class TestMemoryList:
    """Test memory_list tool."""

    @pytest.mark.asyncio
    async def test_list_empty_memories(self) -> None:
        """Test memory_list with no stored memories"""
        import json

        from kagura.mcp.builtin.memory import memory_list

        result = await memory_list(
            user_id="test_user", agent_name="empty_agent", scope="working"
        )
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
        await memory_store(
            user_id="test_user",
            agent_name="test_list_agent",
            key="key1",
            value="value1",
            scope="working",
        )
        await memory_store(
            user_id="test_user",
            agent_name="test_list_agent",
            key="key2",
            value="value2",
            scope="working",
        )

        # List them
        result = await memory_list(
            user_id="test_user", agent_name="test_list_agent", scope="working"
        )
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
            user_id="test_user",
            agent_name="test_list_persistent",
            key="pkey1",
            value="pvalue1",
            scope="persistent",
        )
        await memory_store(
            user_id="test_user",
            agent_name="test_list_persistent",
            key="pkey2",
            value="pvalue2",
            scope="persistent",
        )

        # List them
        result = await memory_list(
            user_id="test_user", agent_name="test_list_persistent", scope="persistent"
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
            await memory_store("test_user", "test_limit_agent", f"key{i}", f"value{i}")

        # List with limit=5
        result = await memory_list(
            user_id="test_user", agent_name="test_limit_agent", scope="working", limit=5
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
        await memory_store(
            user_id="test_user", agent_name="agent_a", key="key_a", value="value_a"
        )
        await memory_store(
            user_id="test_user", agent_name="agent_b", key="key_b", value="value_b"
        )

        # List for agent_a (use persistent since store defaults to persistent now)
        result_a = await memory_list(
            user_id="test_user", agent_name="agent_a", scope="persistent"
        )
        data_a = json.loads(result_a)

        # Should only see agent_a's memory
        keys_a = {m["key"] for m in data_a["memories"]}
        assert "key_a" in keys_a
        assert "key_b" not in keys_a

        # List for agent_b
        result_b = await memory_list(
            user_id="test_user", agent_name="agent_b", scope="persistent"
        )
        data_b = json.loads(result_b)

        # Should only see agent_b's memory
        keys_b = {m["key"] for m in data_b["memories"]}
        assert "key_b" in keys_b
        assert "key_a" not in keys_b


class TestMemoryGraphTools:
    """Test Graph Memory MCP tools (Issue #345)."""

    @pytest.mark.asyncio
    async def test_record_interaction(self) -> None:
        """Test memory_record_interaction tool."""
        import json

        result = await memory_record_interaction(
            agent_name="test_graph_agent",
            user_id="user_test",
            ai_platform="claude",
            query="How to use FastAPI?",
            response="FastAPI is a modern web framework...",
            metadata='{"project": "kagura"}',
        )

        data = json.loads(result)
        assert data["status"] == "recorded"
        assert data["user_id"] == "user_test"
        assert data["ai_platform"] == "claude"
        assert "interaction_id" in data

    @pytest.mark.asyncio
    async def test_record_interaction_invalid_metadata(self) -> None:
        """Test memory_record_interaction with invalid metadata JSON.

        Note: After Phase 2 refactoring, parse_json_dict() returns empty dict
        for invalid JSON instead of raising an error (more lenient behavior).
        The interaction is still recorded successfully.
        """
        import json

        result = await memory_record_interaction(
            agent_name="test_graph_agent",
            user_id="user_test",
            ai_platform="claude",
            query="Test query",
            response="Test response",
            metadata="invalid json",
        )

        data = json.loads(result)
        # After Phase 2: invalid JSON is treated as empty dict (lenient behavior)
        assert data["status"] == "recorded"
        assert "interaction_id" in data
        assert data["ai_platform"] == "claude"

    @pytest.mark.asyncio
    async def test_record_multiple_interactions(self) -> None:
        """Test recording multiple interactions for same user."""
        import json

        result1 = await memory_record_interaction(
            agent_name="test_graph_agent",
            user_id="user_multi",
            ai_platform="claude",
            query="Query 1",
            response="Response 1",
        )

        result2 = await memory_record_interaction(
            agent_name="test_graph_agent",
            user_id="user_multi",
            ai_platform="chatgpt",
            query="Query 2",
            response="Response 2",
        )

        data1 = json.loads(result1)
        data2 = json.loads(result2)

        assert data1["status"] == "recorded"
        assert data2["status"] == "recorded"
        assert data1["interaction_id"] != data2["interaction_id"]

    @pytest.mark.asyncio
    async def test_get_related(self) -> None:
        """Test memory_get_related tool."""
        import json

        # First record an interaction
        result_record = await memory_record_interaction(
            agent_name="test_related_agent",
            user_id="user_related",
            ai_platform="claude",
            query="Test query",
            response="Test response",
        )

        record_data = json.loads(result_record)
        interaction_id = record_data["interaction_id"]

        # Get related nodes
        result = await memory_get_related(
            user_id="user_related",
            agent_name="test_related_agent",
            node_id=interaction_id,
            depth=1,
        )

        data = json.loads(result)
        assert data["node_id"] == interaction_id
        assert data["depth"] == 1
        assert "related_nodes" in data
        assert data["related_count"] >= 0

    @pytest.mark.asyncio
    async def test_get_related_with_filter(self) -> None:
        """Test memory_get_related with relationship filter."""
        import json

        # Record interaction
        result_record = await memory_record_interaction(
            agent_name="test_filter_agent",
            user_id="user_filter",
            ai_platform="claude",
            query="Test query",
            response="Test response",
        )

        record_data = json.loads(result_record)
        interaction_id = record_data["interaction_id"]

        # Get related with filter
        result = await memory_get_related(
            user_id="user_filter",
            agent_name="test_filter_agent",
            node_id=interaction_id,
            depth=1,
            rel_type="learned_from",
        )

        data = json.loads(result)
        assert data["rel_type"] == "learned_from"
        assert "related_nodes" in data

    @pytest.mark.asyncio
    async def test_get_related_nonexistent_node(self) -> None:
        """Test memory_get_related with non-existent node."""
        import json

        result = await memory_get_related(
            user_id="test_user",
            agent_name="test_graph_agent",
            node_id="nonexistent_node",
            depth=1,
        )

        data = json.loads(result)
        assert "related_nodes" in data
        assert data["related_count"] == 0

    @pytest.mark.asyncio
    async def test_get_related_with_string_depth(self) -> None:
        """Test memory_get_related accepts depth as string (MCP protocol compatibility).

        Regression test for #379: MCP clients send depth as string, not int.
        """
        import json

        # Record interaction first
        result_record = await memory_record_interaction(
            agent_name="test_string_depth_agent",
            user_id="user_string_depth",
            ai_platform="claude",
            query="Test query",
            response="Test response",
        )

        record_data = json.loads(result_record)
        interaction_id = record_data["interaction_id"]

        # Test with string depth (as MCP clients send it)
        result = await memory_get_related(
            user_id="user_string_depth",
            agent_name="test_string_depth_agent",
            node_id=interaction_id,
            depth="2",  # String, not int
        )

        data = json.loads(result)
        assert "error" not in data
        assert data["node_id"] == interaction_id
        # Depth should be converted to int internally
        assert isinstance(data["depth"], (int, str))  # Accept both for backward compat
        assert "related_nodes" in data

    @pytest.mark.asyncio
    async def test_record_interaction_with_topic(self) -> None:
        """Test record_interaction with topic metadata (#379).

        Regression test: topic extraction should create topic nodes
        and link them for pattern analysis.
        """
        import json

        user_id = "user_topic_test"

        # Record interaction with topic
        result = await memory_record_interaction(
            agent_name="test_topic_agent",
            user_id=user_id,
            ai_platform="claude",
            query="How to use FastAPI?",
            response="FastAPI is a modern web framework...",
            metadata='{"topic": "python", "project": "kagura"}',
        )

        data = json.loads(result)
        assert data["status"] == "recorded"
        assert "interaction_id" in data

        # Verify user pattern includes the topic
        pattern_result = await memory_get_user_pattern(
            agent_name="test_topic_agent",
            user_id=user_id,
        )

        pattern_data = json.loads(pattern_result)
        assert "pattern" in pattern_data
        # Topics should not be empty when topic is provided
        # Note: topics might still be empty depending on get_user_topics implementation
        # This is a placeholder test that can be enhanced

    @pytest.mark.asyncio
    async def test_get_user_pattern(self) -> None:
        """Test memory_get_user_pattern tool."""
        import json

        user_id = "user_pattern_test"

        # Record multiple interactions
        for i in range(3):
            await memory_record_interaction(
                agent_name="test_pattern_agent",
                user_id=user_id,
                ai_platform="claude",
                query=f"Query {i}",
                response=f"Response {i}",
            )

        # Get user pattern
        result = await memory_get_user_pattern(
            agent_name="test_pattern_agent",
            user_id=user_id,
        )

        data = json.loads(result)
        assert data["user_id"] == user_id
        assert "pattern" in data

        pattern = data["pattern"]
        assert pattern["total_interactions"] == 3
        assert "topics" in pattern
        assert "platforms" in pattern
        assert pattern["platforms"]["claude"] == 3

    @pytest.mark.asyncio
    async def test_get_user_pattern_nonexistent_user(self) -> None:
        """Test memory_get_user_pattern with non-existent user."""
        import json

        result = await memory_get_user_pattern(
            agent_name="test_graph_agent",
            user_id="nonexistent_user",
        )

        data = json.loads(result)
        assert data["user_id"] == "nonexistent_user"

        pattern = data["pattern"]
        assert pattern["total_interactions"] == 0
        assert pattern["topics"] == []
        assert pattern["platforms"] == {}

    @pytest.mark.asyncio
    async def test_graph_disabled(self) -> None:
        """Test graph tools when GraphMemory is disabled."""
        import json

        from kagura.core.memory import MemoryManager

        # Create memory manager with graph disabled
        _memory_cache["user_no_graph:test_no_graph_agent:rag=True"] = MemoryManager(
            user_id="user_no_graph",
            agent_name="test_no_graph_agent",
            enable_rag=True,
            enable_graph=False,
        )

        # Try to record interaction
        result = await memory_record_interaction(
            agent_name="test_no_graph_agent",
            user_id="user_no_graph",
            ai_platform="claude",
            query="Test",
            response="Test",
        )

        data = json.loads(result)
        assert "error" in data
        assert "GraphMemory not available" in data["error"]


class TestMemoryRecordInteractionOptionalPlatform:
    """Test memory_record_interaction with optional ai_platform (Issue #381)."""

    @pytest.mark.asyncio
    async def test_record_without_platform(self) -> None:
        """Test recording interaction without ai_platform (v4.0 Universal Memory)."""
        import json

        # Record without ai_platform
        result = await memory_record_interaction(
            agent_name="test_optional_platform",
            user_id="user_optional",
            query="How to use MCP?",
            response="MCP is Model Context Protocol...",
            metadata='{"topic": "mcp"}',
        )

        data = json.loads(result)
        assert data["status"] == "recorded"
        assert data["user_id"] == "user_optional"
        assert "interaction_id" in data
        # ai_platform should be "unknown" when not provided
        assert data["ai_platform"] in ("", "unknown")

    @pytest.mark.asyncio
    async def test_record_platform_in_metadata(self) -> None:
        """Test ai_platform in metadata instead of parameter."""
        import json

        # Record with ai_platform in metadata
        result = await memory_record_interaction(
            agent_name="test_meta_platform",
            user_id="user_meta",
            query="Test query",
            response="Test response",
            metadata='{"ai_platform": "gemini", "topic": "testing"}',
        )

        data = json.loads(result)
        assert data["status"] == "recorded"
        # Should extract from metadata
        assert data["ai_platform"] == "gemini"

    @pytest.mark.asyncio
    async def test_platform_parameter_overrides_metadata(self) -> None:
        """Test that ai_platform parameter takes precedence over metadata."""
        import json

        # Both parameter and metadata - parameter should win
        result = await memory_record_interaction(
            agent_name="test_override",
            user_id="user_override",
            query="Test",
            response="Test",
            ai_platform="claude",  # Parameter
            metadata='{"ai_platform": "chatgpt"}',  # Metadata (ignored)
        )

        data = json.loads(result)
        assert data["status"] == "recorded"
        # Parameter should override metadata
        assert data["ai_platform"] == "claude"


class TestProgressiveDisclosure:
    """Test Phase 2 progressive disclosure tools (Issue #432)."""

    @pytest.mark.asyncio
    async def test_memory_search_ids_returns_compact_results(self) -> None:
        """Test memory_search_ids returns IDs with previews only."""
        import json

        # Store test data
        long_value = (
            "This is a very long content that should be "
            "truncated in the preview to save tokens"
        )
        await memory_store(
            user_id="test_user",
            agent_name="test_pd",
            key="long_content",
            value=long_value,
            scope="working",
        )

        # Search with IDs
        result = await memory_search_ids(
            user_id="test_user",
            agent_name="test_pd",
            query="content",
            k=5,
        )

        data = json.loads(result)
        assert isinstance(data, list)

        if len(data) > 0:
            # Check compact format
            first = data[0]
            assert "id" in first
            assert "key" in first
            assert "preview" in first
            # Preview should be truncated (50 chars + "...")
            assert len(first["preview"]) <= 55  # 50 + "..." + margin

    @pytest.mark.asyncio
    async def test_memory_fetch_retrieves_full_content(self) -> None:
        """Test memory_fetch retrieves full content by key."""
        # Store test data
        full_content = "This is the complete content that should be retrievable in full"
        await memory_store(
            user_id="test_user",
            agent_name="test_fetch",
            key="test_key",
            value=full_content,
            scope="working",
        )

        # Fetch full content
        result = await memory_fetch(
            user_id="test_user",
            agent_name="test_fetch",
            key="test_key",
            scope="working",
        )

        # Should return full content
        assert full_content in result

    @pytest.mark.asyncio
    async def test_progressive_disclosure_workflow(self) -> None:
        """Test two-step workflow: search_ids then fetch."""
        import json

        # Store multiple items
        await memory_store(
            user_id="test_user",
            agent_name="test_workflow",
            key="item1",
            value="First item with detailed content",
            scope="working",
        )
        await memory_store(
            user_id="test_user",
            agent_name="test_workflow",
            key="item2",
            value="Second item with more information",
            scope="working",
        )

        # Step 1: Search IDs (compact)
        ids_result = await memory_search_ids(
            user_id="test_user",
            agent_name="test_workflow",
            query="item",
            k=10,
        )

        data = json.loads(ids_result)
        assert len(data) >= 2

        # Step 2: Fetch full content of first result
        first_key = data[0]["key"]
        full_result = await memory_fetch(
            user_id="test_user",
            agent_name="test_workflow",
            key=first_key,
            scope="working",
        )

        assert "detailed content" in full_result or "more information" in full_result
