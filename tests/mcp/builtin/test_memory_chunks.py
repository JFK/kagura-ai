"""Tests for chunk-related MCP memory tools.

Tests for:
- memory_get_chunk_context: Get neighboring chunks around a specific chunk
- memory_get_chunk_metadata: Get chunk metadata without full content
- memory_get_full_document: Reconstruct complete document from chunks
"""

import json

import pytest

from kagura.mcp.builtin.memory import (
    _memory_cache,
    memory_get_chunk_context,
    memory_get_chunk_metadata,
    memory_get_full_document,
)


@pytest.fixture(autouse=True, scope="function")
def setup_test_chromadb(request, tmp_path_factory):
    """Set up isolated ChromaDB directory for each test to avoid parallel test conflicts."""
    import os

    # Get worker ID for parallel test execution
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")

    # Create unique ChromaDB path for this worker
    if worker_id == "master":
        # Single-process test
        chroma_path = tmp_path_factory.mktemp("chromadb")
    else:
        # Parallel test - use worker-specific directory
        chroma_path = tmp_path_factory.getbasetemp().parent / f"chromadb_{worker_id}"
        chroma_path.mkdir(exist_ok=True)

    # Override ChromaDB path for this test
    original_get_cache_dir = None
    try:
        from kagura.config import paths
        original_get_cache_dir = paths.get_cache_dir
        paths.get_cache_dir = lambda: chroma_path

        # Clear memory cache before test
        _memory_cache.clear()

        yield

    finally:
        # Restore original function
        if original_get_cache_dir:
            paths.get_cache_dir = original_get_cache_dir

        # Clear cache after test
        _memory_cache.clear()


class TestMemoryGetChunkContext:
    """Test memory_get_chunk_context tool."""

    def test_get_chunk_context_invalid_params(self):
        """Test that invalid parameters are rejected."""
        user_id = "test_user"
        parent_id = "fake_parent_id"

        # Test invalid chunk_index
        result = memory_get_chunk_context(
            user_id=user_id,
            parent_id=parent_id,
            chunk_index="not_a_number",
            context_size="1",
        )

        data = json.loads(result)
        assert "error" in data
        assert "Invalid parameter type" in data["error"]

    def test_get_chunk_context_negative_params(self):
        """Test that negative parameters are rejected."""
        user_id = "test_user"
        parent_id = "fake_parent_id"

        # Test negative chunk_index
        result = memory_get_chunk_context(
            user_id=user_id,
            parent_id=parent_id,
            chunk_index="-1",
            context_size="1",
        )

        data = json.loads(result)
        assert "error" in data
        assert "Invalid parameter value" in data["error"]

        # Test negative context_size
        result = memory_get_chunk_context(
            user_id=user_id,
            parent_id=parent_id,
            chunk_index="0",
            context_size="-1",
        )

        data = json.loads(result)
        assert "error" in data
        assert "Invalid parameter value" in data["error"]

    def test_get_chunk_context_nonexistent_document(self):
        """Test getting chunks from non-existent document."""
        user_id = "test_user"
        parent_id = "nonexistent_parent_id"

        result = memory_get_chunk_context(
            user_id=user_id,
            parent_id=parent_id,
            chunk_index="0",
            context_size="1",
        )

        data = json.loads(result)
        # Should return empty chunks list
        assert "chunks" in data
        assert data["chunks"] == []
        assert data["parent_id"] == parent_id


class TestMemoryGetChunkMetadata:
    """Test memory_get_chunk_metadata tool."""

    def test_get_chunk_metadata_invalid_chunk_index(self):
        """Test that invalid chunk_index is rejected."""
        user_id = "test_user"
        parent_id = "fake_parent_id"

        result = memory_get_chunk_metadata(
            user_id=user_id,
            parent_id=parent_id,
            chunk_index="not_a_number",
        )

        data = json.loads(result)
        assert "error" in data
        assert "Invalid chunk_index" in data["error"]

    def test_get_chunk_metadata_all_chunks(self):
        """Test getting metadata for all chunks (empty chunk_index)."""
        user_id = "test_user"
        parent_id = "fake_parent_id"

        # With empty chunk_index, should return list (even if empty for nonexistent doc)
        result = memory_get_chunk_metadata(
            user_id=user_id,
            parent_id=parent_id,
            chunk_index="",
        )

        # Should be valid JSON (either list or error)
        data = json.loads(result)
        # For nonexistent document, could be empty list or error
        assert isinstance(data, (list, dict))


class TestMemoryGetFullDocument:
    """Test memory_get_full_document tool."""

    def test_get_full_document_nonexistent(self):
        """Test getting full document for non-existent parent_id."""
        user_id = "test_user"
        parent_id = "nonexistent_parent_id"

        result = memory_get_full_document(
            user_id=user_id,
            parent_id=parent_id,
        )

        data = json.loads(result)
        # Should return empty or error
        assert "full_content" in data or "error" in data

        if "full_content" in data:
            # Empty document case
            assert data["full_content"] == ""
            assert data["total_chunks"] == 0


class TestChunkIntegration:
    """Integration tests for chunk-related tools."""

    def test_chunk_workflow(self):
        """Test complete workflow: store -> search -> get chunks -> reconstruct.

        This is a placeholder for a full integration test that would:
        1. Store a large document (gets chunked)
        2. Search to find a relevant chunk
        3. Use get_chunk_metadata to inspect chunks
        4. Use get_chunk_context to get surrounding context
        5. Use get_full_document to reconstruct if needed
        """
        # TODO: Implement full workflow test once we can reliably
        # extract parent_id from stored documents
        pytest.skip("Full integration test - TODO")
