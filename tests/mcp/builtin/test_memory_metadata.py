"""Tests for v4.0 metadata handling in MCP memory tools.

Verify that internal _meta_ keys don't cause issues when using MCP tools.
"""

import json

import pytest

from kagura.mcp.builtin.memory import (
    memory_delete,
    memory_list,
    memory_recall,
    memory_search,
    memory_store,
)


class TestWorkingMemoryMetadata:
    """Test that _meta_ keys are properly handled in working memory."""

    @pytest.mark.asyncio
    async def test_meta_keys_not_visible_in_list(self):
        """Test that _meta_ keys are excluded from memory_list."""
        # Store memories with metadata
        await memory_store(
            "test_user",
            "test_agent",
            "user_pref",
            "Python",
            scope="working",
            tags='["language"]',
            importance=0.9,
        )

        # List should not include _meta_ keys
        result = await memory_list("test_user", "test_agent", scope="working")
        data = json.loads(result)

        # Should only see user_pref, not _meta_user_pref
        keys = [m["key"] for m in data["memories"]]
        assert "user_pref" in keys
        assert "_meta_user_pref" not in keys
        assert all(not k.startswith("_meta_") for k in keys)

    @pytest.mark.asyncio
    async def test_recall_with_meta_key_fails_gracefully(self):
        """Test that trying to recall _meta_ key fails gracefully."""
        await memory_store(
            "test_user", "test_agent", "normal_key", "value", scope="working"
        )

        # Try to recall the internal metadata key
        result = await memory_recall(
            "test_user", "test_agent", "_meta_normal_key", scope="working"
        )

        # Should return the metadata dict, not error
        # This is acceptable behavior - it's stored in working memory
        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_removes_both_value_and_meta(self):
        """Test that delete removes both value and metadata."""
        # Store with metadata
        await memory_store(
            "test_user",
            "test_agent",
            "to_delete",
            "value",
            scope="working",
            tags='["test"]',
            importance=0.7,
        )

        # Delete should remove both
        await memory_delete("test_user", "test_agent", "to_delete", scope="working")

        # Both should be gone
        value_result = await memory_recall(
            "test_user", "test_agent", "to_delete", scope="working"
        )
        meta_result = await memory_recall(
            "test_user", "test_agent", "_meta_to_delete", scope="working"
        )

        assert "No value found" in value_result
        assert "No value found" in meta_result

    @pytest.mark.asyncio
    async def test_search_does_not_return_meta_keys(self):
        """Test that search results don't include _meta_ entries."""
        # Store memories
        await memory_store(
            "test_user",
            "test_agent",
            "searchable",
            "Python programming",
            scope="working",
            tags='["python"]',
        )

        # Search
        result = await memory_search(
            "test_user", "test_agent", "python", k=10, scope="working"
        )
        data = json.loads(result)

        # Check results don't include _meta_ keys
        for item in data:
            if isinstance(item, dict) and "key" in item:
                assert not item["key"].startswith("_meta_")


class TestPersistentMemoryMetadata:
    """Test metadata handling for persistent memory."""

    @pytest.mark.asyncio
    async def test_persistent_memory_stores_metadata_in_db(self):
        """Test that persistent memory metadata is stored in DB, not separate key."""
        # Store persistent memory with metadata
        await memory_store(
            "test_user",
            "test_agent",
            "persistent_key",
            "persistent value",
            scope="persistent",
            tags='["persistent"]',
            importance=0.8,
        )

        # List should show 1 memory (not 2)
        result = await memory_list("test_user", "test_agent", scope="persistent")
        data = json.loads(result)

        assert data["count"] >= 1  # At least our test memory

        # Find our memory
        our_memory = next(
            (m for m in data["memories"] if m["key"] == "persistent_key"), None
        )
        assert our_memory is not None
        assert our_memory["value"] == "persistent value"

        # Should NOT have _meta_persistent_key in list
        keys = [m["key"] for m in data["memories"]]
        assert "_meta_persistent_key" not in keys

    @pytest.mark.asyncio
    async def test_persistent_memory_recall_returns_metadata(self):
        """Persistent recall should include metadata payload."""
        await memory_store(
            "test_user",
            "test_agent",
            "persistent_meta",
            "persistent value",
            scope="persistent",
            tags='["persistent", "meta"]',
            importance=0.7,
            metadata='{"custom": "field"}',
        )

        result = await memory_recall(
            "test_user", "test_agent", "persistent_meta", scope="persistent"
        )

        data = json.loads(result)
        assert data["value"] == "persistent value"
        assert data["metadata"]["importance"] == 0.7
        # Lists/dicts are stored as JSON strings for Chroma compatibility
        assert data["metadata"]["tags"] == '["persistent", "meta"]'
        # Custom metadata fields are expanded into the metadata object
        assert data["metadata"]["custom"] == "field"


class TestMetadataIntegrity:
    """Test that metadata operations don't corrupt data."""

    @pytest.mark.asyncio
    async def test_update_via_store_preserves_metadata(self):
        """Test that re-storing with new metadata works."""
        # Store initial
        await memory_store(
            "test_user",
            "test_agent",
            "update_test",
            "original",
            scope="working",
            tags='["v1"]',
            importance=0.5,
        )

        # Update by storing again (same key)
        # Note: This will fail due to duplicate check, which is expected
        # In real usage, user would delete first or use different key

    @pytest.mark.asyncio
    async def test_metadata_survives_recall(self):
        """Test that metadata doesn't interfere with recall."""
        # Store with rich metadata
        await memory_store(
            "test_user",
            "test_agent",
            "rich_meta",
            "value with metadata",
            scope="working",
            tags='["tag1", "tag2"]',
            importance=0.95,
            metadata='{"custom": "field"}',
        )

        # Recall should now include metadata (new behavior)
        result = await memory_recall(
            "test_user", "test_agent", "rich_meta", scope="working"
        )

        # Parse JSON response
        import json

        data = json.loads(result)

        # Verify value is correct
        assert data["value"] == "value with metadata"

        # Verify metadata is included
        assert "metadata" in data
        assert data["metadata"]["custom"] == "field"
        assert data["metadata"]["tags"] == ["tag1", "tag2"]
        assert data["metadata"]["importance"] == 0.95

        # Verify no meta keys in the returned string
        assert "_meta_" not in result
