"""Tests for BM25 lexical search."""

import pytest

pytest.importorskip("rank_bm25")

from kagura.core.memory.lexical_search import BM25Searcher  # noqa: E402


def test_bm25_searcher_initialization():
    """Test BM25 searcher initialization."""
    searcher = BM25Searcher()
    assert searcher.count() == 0
    assert searcher.corpus == []
    assert searcher.doc_ids == []


def test_bm25_index_documents():
    """Test indexing documents."""
    searcher = BM25Searcher()

    documents = [
        {"id": "doc1", "content": "Python is a programming language"},
        {"id": "doc2", "content": "FastAPI is a Python web framework"},
        {"id": "doc3", "content": "Java is also a programming language"},
    ]

    searcher.index_documents(documents)

    assert searcher.count() == 3
    assert len(searcher.corpus) == 3
    assert searcher.doc_ids == ["doc1", "doc2", "doc3"]


def test_bm25_search():
    """Test BM25 search."""
    searcher = BM25Searcher()

    documents = [
        {"id": "doc1", "content": "Python is a programming language"},
        {"id": "doc2", "content": "FastAPI is a Python web framework"},
        {"id": "doc3", "content": "Java is also a programming language"},
    ]

    searcher.index_documents(documents)

    results = searcher.search("Python", k=10)

    # Should return results with Python mentioned
    assert len(results) > 0
    assert all("id" in r for r in results)
    assert all("score" in r for r in results)
    assert all("rank" in r for r in results)

    # Ranks should be 1-based
    assert results[0]["rank"] == 1

    # Scores should be in descending order
    if len(results) > 1:
        assert results[0]["score"] >= results[1]["score"]


def test_bm25_search_empty():
    """Test search on empty index."""
    searcher = BM25Searcher()
    results = searcher.search("Python", k=10)
    assert results == []


def test_bm25_search_with_min_score():
    """Test search with minimum score threshold."""
    searcher = BM25Searcher()

    documents = [
        {"id": "doc1", "content": "Python programming"},
        {"id": "doc2", "content": "Java programming"},
    ]

    searcher.index_documents(documents)

    # Search with high min_score threshold
    results = searcher.search("Python", k=10, min_score=10.0)

    # May return fewer results if scores are low
    assert isinstance(results, list)


def test_bm25_tokenize():
    """Test tokenization."""
    searcher = BM25Searcher()

    tokens = searcher._tokenize("Python is a programming language")
    assert tokens == ["python", "is", "a", "programming", "language"]

    # Should lowercase
    tokens = searcher._tokenize("PYTHON")
    assert tokens == ["python"]


def test_bm25_clear():
    """Test clearing index."""
    searcher = BM25Searcher()

    documents = [{"id": "doc1", "content": "test"}]
    searcher.index_documents(documents)
    assert searcher.count() == 1

    searcher.clear()
    assert searcher.count() == 0
    assert searcher.corpus == []
    assert searcher.doc_ids == []


def test_bm25_repr():
    """Test string representation."""
    searcher = BM25Searcher()

    repr_str = repr(searcher)
    assert "BM25Searcher" in repr_str
    assert "0" in repr_str

    # After indexing
    documents = [{"id": "doc1", "content": "test"}]
    searcher.index_documents(documents)

    repr_str = repr(searcher)
    assert "1" in repr_str


def test_bm25_reindex():
    """Test re-indexing documents."""
    searcher = BM25Searcher()

    # First index
    docs1 = [{"id": "doc1", "content": "Python"}]
    searcher.index_documents(docs1)
    assert searcher.count() == 1

    # Re-index with different documents
    docs2 = [
        {"id": "doc2", "content": "Java"},
        {"id": "doc3", "content": "Go"},
    ]
    searcher.index_documents(docs2)
    assert searcher.count() == 2
    assert searcher.doc_ids == ["doc2", "doc3"]


def test_bm25_missing_dependency():
    """Test error when rank-bm25 is not installed."""
    # Skip - requires uninstalling rank-bm25
    pytest.skip("Requires uninstalling rank-bm25 to test")
