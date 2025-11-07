"""Tests for chunk context retrieval features (Issue #581)."""

import pytest

from kagura.config.memory_config import ChunkingConfig, MemorySystemConfig
from kagura.core.memory.rag import MemoryRAG


@pytest.fixture
def temp_rag_with_chunks(tmp_path):
    """Create temporary RAG instance with chunking enabled."""
    from pathlib import Path

    config = ChunkingConfig(
        enabled=True, max_chunk_size=100, overlap=10, min_chunk_size=50
    )
    rag = MemoryRAG(
        collection_name="test_chunks",
        persist_dir=Path(tmp_path),
        chunking_config=config,
    )
    yield rag
    try:
        rag.delete_all()
    except Exception:
        pass


def test_get_chunk_context_basic(temp_rag_with_chunks):
    """Test getting chunk context with 1 neighbor."""
    # Store a long document that will be chunked
    long_text = "This is sentence one. " * 20  # ~440 chars, creates 4-5 chunks
    parent_id = temp_rag_with_chunks.store(
        content=long_text, user_id="user1", metadata={"title": "Test Doc"}
    )

    # Get context for chunk 1 (should return chunks 0, 1, 2)
    chunks = temp_rag_with_chunks.get_chunk_context(
        parent_id=parent_id, chunk_index=1, context_size=1
    )

    assert len(chunks) >= 2  # At least target chunk and 1 neighbor
    assert all("content" in c for c in chunks)
    assert all("metadata" in c for c in chunks)
    assert all("chunk_index" in c for c in chunks)

    # Verify sorted by chunk_index
    indices = [c["chunk_index"] for c in chunks]
    assert indices == sorted(indices)


def test_get_chunk_context_boundary(temp_rag_with_chunks):
    """Test chunk context at document boundaries."""
    long_text = "Sentence. " * 50  # ~500 chars, creates 5-6 chunks
    parent_id = temp_rag_with_chunks.store(content=long_text, user_id="user1")

    # Get context for first chunk (should not include negative indices)
    chunks = temp_rag_with_chunks.get_chunk_context(
        parent_id=parent_id, chunk_index=0, context_size=2
    )

    assert all(c["chunk_index"] >= 0 for c in chunks)
    assert chunks[0]["chunk_index"] == 0  # First chunk included


def test_get_full_document(temp_rag_with_chunks):
    """Test full document reconstruction."""
    original_text = "First sentence. Second sentence. Third sentence. " * 10
    parent_id = temp_rag_with_chunks.store(content=original_text, user_id="user1")

    # Reconstruct document
    doc = temp_rag_with_chunks.get_full_document(parent_id=parent_id)

    assert "full_content" in doc
    assert "chunks" in doc
    assert "total_chunks" in doc
    assert doc["parent_id"] == parent_id
    assert doc["total_chunks"] > 1  # Should be chunked

    # Content should be preserved (may have slight variations due to chunking)
    assert len(doc["full_content"]) > 0


def test_get_full_document_not_found(temp_rag_with_chunks):
    """Test full document retrieval for non-existent document."""
    doc = temp_rag_with_chunks.get_full_document(parent_id="nonexistent")

    assert "error" in doc
    assert doc["total_chunks"] == 0
    assert doc["full_content"] == ""


def test_get_chunk_metadata_all(temp_rag_with_chunks):
    """Test getting metadata for all chunks."""
    long_text = "Word " * 100  # ~500 chars
    parent_id = temp_rag_with_chunks.store(content=long_text, user_id="user1")

    # Get all metadata
    metadata_list = temp_rag_with_chunks.get_chunk_metadata(parent_id=parent_id)

    assert isinstance(metadata_list, list)
    assert len(metadata_list) > 1  # Multiple chunks
    assert all("chunk_index" in m for m in metadata_list)
    assert all("metadata" in m for m in metadata_list)

    # Verify sorted
    indices = [m["chunk_index"] for m in metadata_list]
    assert indices == sorted(indices)


def test_get_chunk_metadata_specific(temp_rag_with_chunks):
    """Test getting metadata for specific chunk."""
    long_text = "Text. " * 100
    parent_id = temp_rag_with_chunks.store(content=long_text, user_id="user1")

    # Get specific chunk metadata
    metadata = temp_rag_with_chunks.get_chunk_metadata(
        parent_id=parent_id, chunk_index=0
    )

    assert isinstance(metadata, dict)
    assert metadata["chunk_index"] == 0
    assert "metadata" in metadata
    assert "id" in metadata


def test_get_chunk_metadata_not_found(temp_rag_with_chunks):
    """Test metadata retrieval for non-existent chunk."""
    metadata = temp_rag_with_chunks.get_chunk_metadata(
        parent_id="nonexistent", chunk_index=0
    )

    assert metadata == {}


def test_chunk_context_user_scoping(temp_rag_with_chunks):
    """Test that chunk context respects user_id filtering."""
    # Store chunks for different users
    text = "Content. " * 50
    parent_id1 = temp_rag_with_chunks.store(content=text, user_id="user1")
    parent_id2 = temp_rag_with_chunks.store(content=text, user_id="user2")

    # Get context with user filter
    chunks_user1 = temp_rag_with_chunks.get_chunk_context(
        parent_id=parent_id1, chunk_index=0, user_id="user1"
    )

    chunks_user2 = temp_rag_with_chunks.get_chunk_context(
        parent_id=parent_id1, chunk_index=0, user_id="user2"
    )

    assert len(chunks_user1) > 0  # User1 can see their chunks
    assert len(chunks_user2) == 0  # User2 cannot see user1's chunks
