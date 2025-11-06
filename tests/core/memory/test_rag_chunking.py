"""Integration tests for RAG chunking functionality."""

import tempfile
from pathlib import Path

import pytest

pytest.importorskip("chromadb")
pytest.importorskip("langchain_text_splitters")

from kagura.config.memory_config import ChunkingConfig  # noqa: E402
from kagura.core.memory.rag import MemoryRAG  # noqa: E402


@pytest.fixture
def chunking_config():
    """Chunking config for testing."""
    return ChunkingConfig(
        enabled=True,
        max_chunk_size=100,  # Small for testing
        overlap=20,
        min_chunk_size=50,
    )


@pytest.fixture
def temp_rag(chunking_config):
    """Temporary RAG instance with chunking enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rag = MemoryRAG(
            collection_name="test_chunking",
            persist_dir=Path(tmpdir),
            chunking_config=chunking_config,
        )
        yield rag


@pytest.mark.integration
def test_rag_chunking_disabled_backward_compat():
    """Test that RAG works without chunking (backward compatibility)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Chunking explicitly disabled
        config = ChunkingConfig(enabled=False)
        rag = MemoryRAG(
            collection_name="test_no_chunk",
            persist_dir=Path(tmpdir),
            chunking_config=config,
        )

        long_text = "Word " * 100  # 500 chars
        doc_id = rag.store(long_text, user_id="test_user")

        # Should store as single document
        assert isinstance(doc_id, str)
        assert len(doc_id) == 16

        # Verify single document in DB
        assert rag.count() == 1

        # Recall should work
        results = rag.recall("Word", user_id="test_user", top_k=5)
        assert len(results) == 1
        assert "Word" in results[0]["content"]


@pytest.mark.integration
def test_rag_chunking_short_text_not_chunked(temp_rag):
    """Test that short text below min_chunk_size is NOT chunked."""
    short_text = "Short text here."  # < min_chunk_size (50)
    doc_id = temp_rag.store(short_text, user_id="test_user")

    # Should store as single document (not chunked)
    assert temp_rag.count() == 1

    results = temp_rag.recall("text", user_id="test_user")
    assert len(results) == 1
    # Should NOT have is_chunk metadata
    assert results[0]["metadata"].get("is_chunk") is None


@pytest.mark.integration
def test_rag_chunking_long_text_creates_chunks(temp_rag):
    """Test that long text above min_chunk_size IS chunked."""
    # Create long text with clear boundaries
    long_text = "Sentence number {}. " * 50  # Format later
    long_text = "".join(f"Sentence number {i}. " for i in range(50))  # ~1000 chars

    parent_id = temp_rag.store(
        long_text, user_id="test_user", metadata={"type": "test_doc"}
    )

    # Should create multiple chunks
    total_docs = temp_rag.count()
    assert total_docs > 1, f"Expected multiple chunks, got {total_docs}"

    # Verify chunks have correct metadata
    results = temp_rag.recall("Sentence", user_id="test_user", top_k=20)

    # Find chunks (filter by is_chunk metadata)
    chunk_results = [r for r in results if r["metadata"].get("is_chunk") is True]
    assert len(chunk_results) > 0, "No chunks found with is_chunk=True"

    # Check first chunk metadata structure
    first_chunk = chunk_results[0]
    assert first_chunk["metadata"]["parent_id"] == parent_id
    assert first_chunk["metadata"]["chunk_index"] >= 0
    assert first_chunk["metadata"]["total_chunks"] == total_docs
    assert first_chunk["metadata"]["is_chunk"] is True

    # Original metadata preserved
    assert first_chunk["metadata"]["type"] == "test_doc"
    assert first_chunk["metadata"]["user_id"] == "test_user"


@pytest.mark.integration
def test_rag_chunking_metadata_preserved_across_chunks(temp_rag):
    """Test that original metadata is preserved in all chunks."""
    # Note: ChromaDB only supports str, int, float, bool, None in metadata (no lists)
    original_metadata = {
        "file_path": "test.txt",
        "author": "test_author",
        "tags": "important,project_a",  # Comma-separated string (not list)
        "version": 1,
        "is_final": True,
    }

    long_text = "Content line {}. " * 60
    long_text = "".join(f"Content line {i}. " for i in range(60))

    parent_id = temp_rag.store(
        long_text,
        user_id="test_user",
        metadata=original_metadata,
        agent_name="test_agent",
    )

    # Query all chunks
    results = temp_rag.recall("Content", user_id="test_user", top_k=30)

    # Verify all chunks have original metadata
    chunk_results = [r for r in results if r["metadata"].get("is_chunk") is True]
    assert len(chunk_results) > 0

    for result in chunk_results:
        meta = result["metadata"]
        # Original metadata preserved
        assert meta["file_path"] == "test.txt"
        assert meta["author"] == "test_author"
        assert meta["tags"] == "important,project_a"
        assert meta["version"] == 1
        assert meta["is_final"] is True
        assert meta["user_id"] == "test_user"
        assert meta["agent_name"] == "test_agent"

        # Chunk metadata added
        assert meta["parent_id"] == parent_id
        assert "chunk_index" in meta
        assert "total_chunks" in meta


@pytest.mark.integration
def test_rag_chunking_query_by_parent_id(temp_rag):
    """Test reconstructing full document by querying parent_id."""
    long_text = "Paragraph {}. " * 40
    long_text = "".join(f"Paragraph {i}. " for i in range(40))

    parent_id = temp_rag.store(long_text, user_id="test_user")

    # Query all chunks by parent_id using ChromaDB's get() API
    all_chunks = temp_rag.collection.get(where={"parent_id": parent_id})

    # Should retrieve all chunks
    assert len(all_chunks["ids"]) > 1, "Should have multiple chunks"

    # Verify chunk indices are sequential
    chunk_indices = [meta["chunk_index"] for meta in all_chunks["metadatas"]]
    assert chunk_indices == sorted(chunk_indices), "Chunks should be ordered by index"

    # Verify all chunks have same total_chunks
    total_chunks_values = [meta["total_chunks"] for meta in all_chunks["metadatas"]]
    assert len(set(total_chunks_values)) == 1, "All chunks should have same total_chunks"
    assert total_chunks_values[0] == len(all_chunks["ids"])


@pytest.mark.integration
def test_rag_chunking_semantic_search_finds_relevant_chunks(temp_rag):
    """Test that semantic search correctly finds relevant chunks."""
    # Store two different documents
    doc1_text = "Python is a programming language used for AI and web development. " * 15
    doc2_text = "JavaScript is primarily used for frontend web development and Node.js. " * 15

    parent_id1 = temp_rag.store(
        doc1_text, user_id="test_user", metadata={"doc": "python"}
    )
    parent_id2 = temp_rag.store(
        doc2_text, user_id="test_user", metadata={"doc": "javascript"}
    )

    # Search for Python-related content
    results = temp_rag.recall("Python programming AI", user_id="test_user", top_k=10)

    # Top results should be from doc1 (Python document)
    assert len(results) > 0, "Should find results"
    top_result = results[0]
    assert "Python" in top_result["content"], "Top result should contain 'Python'"
    assert (
        top_result["metadata"]["doc"] == "python"
    ), "Top result should be from Python doc"


@pytest.mark.integration
def test_rag_chunking_graceful_degradation_no_langchain(monkeypatch):
    """Test that chunking gracefully degrades when langchain not available."""
    import sys

    # Temporarily remove langchain_text_splitters from sys.modules
    langchain_modules = {
        k: v for k, v in sys.modules.items() if "langchain" in k.lower()
    }
    for module_name in langchain_modules.keys():
        monkeypatch.setitem(sys.modules, module_name, None)

    with tempfile.TemporaryDirectory() as tmpdir:
        config = ChunkingConfig(enabled=True)
        rag = MemoryRAG(
            collection_name="test_no_langchain",
            persist_dir=Path(tmpdir),
            chunking_config=config,
        )

        # Should fall back to single-document storage
        long_text = "Word " * 100
        doc_id = rag.store(long_text, user_id="test_user")

        # Should store as one document (chunking disabled due to import error)
        assert rag.count() == 1

        # Recall should still work
        results = rag.recall("Word", user_id="test_user")
        assert len(results) == 1


@pytest.mark.integration
def test_rag_chunking_with_agent_scoping(temp_rag):
    """Test that chunking works with agent_name scoping."""
    long_text = "Agent-scoped content. " * 50

    parent_id = temp_rag.store(
        long_text, user_id="test_user", agent_name="test_agent"
    )

    # Query chunks with agent scoping
    results = temp_rag.recall(
        "Agent-scoped", user_id="test_user", agent_name="test_agent", top_k=10
    )

    # Should find chunks from this agent
    assert len(results) > 0

    # Verify agent_name in metadata
    for result in results:
        if result["metadata"].get("is_chunk"):
            assert result["metadata"]["agent_name"] == "test_agent"
