"""Tests for Memory RAG (semantic search)"""

import pytest

from kagura.core.memory import MemoryManager, MemoryRAG

# Check if ChromaDB is available
try:
    import chromadb  # noqa: F401

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


@pytest.mark.integration
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
def test_memory_rag_initialization(tmp_path):
    """Test MemoryRAG initialization"""
    rag = MemoryRAG(collection_name="test_collection", persist_dir=tmp_path)
    assert rag is not None
    assert rag.count() == 0


@pytest.mark.integration
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
def test_memory_rag_store_and_recall(tmp_path):
    """Test storing and recalling memories"""
    rag = MemoryRAG(collection_name="test_collection", persist_dir=tmp_path)

    # Store memory
    content_hash = rag.store(
        "Python is a programming language", metadata={"type": "fact"}
    )
    assert isinstance(content_hash, str)
    assert len(content_hash) == 16

    # Recall memory
    results = rag.recall("What is Python?", top_k=1)
    assert len(results) > 0
    assert "Python" in results[0]["content"]
    assert "distance" in results[0]
    assert "metadata" in results[0]


@pytest.mark.integration
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
def test_memory_rag_agent_scoping(tmp_path):
    """Test agent-scoped memories"""
    rag = MemoryRAG(collection_name="test_collection", persist_dir=tmp_path)

    # Store memories for different agents
    rag.store("Agent A memory", agent_name="agent_a")
    rag.store("Agent B memory", agent_name="agent_b")

    # Query with agent filter
    results_a = rag.recall("memory", top_k=10, agent_name="agent_a")
    assert len(results_a) > 0
    assert "Agent A" in results_a[0]["content"]

    results_b = rag.recall("memory", top_k=10, agent_name="agent_b")
    assert len(results_b) > 0
    assert "Agent B" in results_b[0]["content"]


@pytest.mark.integration
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
def test_memory_rag_delete_all(tmp_path):
    """Test deleting all memories"""
    rag = MemoryRAG(collection_name="test_collection", persist_dir=tmp_path)

    # Store memories
    rag.store("Memory 1", agent_name="agent_a")
    rag.store("Memory 2", agent_name="agent_a")
    rag.store("Memory 3", agent_name="agent_b")
    assert rag.count() == 3

    # Delete all for agent_a
    rag.delete_all(agent_name="agent_a")
    assert rag.count() == 1

    # Delete all
    rag.delete_all()
    assert rag.count() == 0


@pytest.mark.integration
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
def test_memory_rag_semantic_search(tmp_path):
    """Test semantic search functionality"""
    rag = MemoryRAG(collection_name="test_collection", persist_dir=tmp_path)

    # Store related documents
    rag.store("The sky is blue")
    rag.store("The ocean is deep")
    rag.store("Python is a programming language")

    # Search for similar content
    results = rag.recall("What color is the sky?", top_k=1)
    assert len(results) > 0
    # Should return the "sky is blue" document
    assert "sky" in results[0]["content"].lower()


@pytest.mark.integration
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
def test_memory_manager_with_rag(tmp_path):
    """Test MemoryManager with RAG enabled"""
    memory = MemoryManager(agent_name="test_agent", persist_dir=tmp_path, enable_rag=True)

    # Store semantic memory
    content_hash = memory.store_semantic("Python is great for AI development")
    assert isinstance(content_hash, str)

    # Recall semantic memory
    results = memory.recall_semantic("AI development", top_k=1)
    assert len(results) > 0
    assert "Python" in results[0]["content"]


@pytest.mark.integration
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
def test_memory_manager_rag_not_enabled(tmp_path):
    """Test MemoryManager RAG methods when RAG is not enabled"""
    memory = MemoryManager(agent_name="test_agent", persist_dir=tmp_path, enable_rag=False)

    # Should raise error
    with pytest.raises(ValueError, match="RAG not enabled"):
        memory.store_semantic("Some content")

    with pytest.raises(ValueError, match="RAG not enabled"):
        memory.recall_semantic("Some query")


@pytest.mark.integration
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
def test_memory_manager_repr_with_rag(tmp_path):
    """Test MemoryManager __repr__ with RAG"""
    memory = MemoryManager(agent_name="test_agent", persist_dir=tmp_path, enable_rag=True)

    # Store some data
    memory.set_temp("key", "value")
    memory.add_message("user", "Hello")
    memory.remember("fact", "Python is awesome")
    memory.store_semantic("Semantic data")

    repr_str = repr(memory)
    assert "test_agent" in repr_str
    assert "working=1" in repr_str
    assert "context=1" in repr_str
    assert "persistent=1" in repr_str
    assert "rag=1" in repr_str


def test_memory_rag_import_error():
    """Test MemoryRAG raises ImportError when ChromaDB not installed"""
    if CHROMADB_AVAILABLE:
        pytest.skip("ChromaDB is installed, cannot test import error")

    with pytest.raises(ImportError, match="ChromaDB not installed"):
        MemoryRAG()
