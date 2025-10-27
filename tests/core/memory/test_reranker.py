"""Tests for cross-encoder reranking."""

import pytest

pytest.importorskip("sentence_transformers")

from kagura.config.memory_config import RerankConfig
from kagura.core.memory.reranker import MemoryReranker


def test_rerank_config_defaults():
    """Test default reranking configuration."""
    config = RerankConfig()
    assert config.enabled is True
    assert config.model == "cross-encoder/ms-marco-MiniLM-L-6-v2"
    assert config.candidates_k == 100
    assert config.top_k == 20
    assert config.batch_size == 32


def test_rerank_config_custom():
    """Test custom reranking configuration."""
    config = RerankConfig(
        enabled=False,
        model="test-model",
        candidates_k=50,
        top_k=10,
        batch_size=16,
    )
    assert config.enabled is False
    assert config.model == "test-model"
    assert config.candidates_k == 50
    assert config.top_k == 10
    assert config.batch_size == 16


@pytest.mark.slow
def test_reranker_initialization():
    """Test reranker initialization."""
    config = RerankConfig()
    reranker = MemoryReranker(config)

    assert reranker.config == config
    assert reranker.model is not None


@pytest.mark.slow
def test_reranker_rerank():
    """Test reranking candidates."""
    config = RerankConfig()
    reranker = MemoryReranker(config)

    query = "What is Python?"
    candidates = [
        {"content": "Python is a programming language", "distance": 0.3},
        {"content": "Java is also a programming language", "distance": 0.4},
        {"content": "FastAPI is a Python web framework", "distance": 0.5},
    ]

    reranked = reranker.rerank(query, candidates, top_k=2)

    # Should return top 2
    assert len(reranked) == 2
    # All should have rerank_score
    assert all("rerank_score" in r for r in reranked)
    # Rerank scores should be in descending order
    assert reranked[0]["rerank_score"] >= reranked[1]["rerank_score"]


@pytest.mark.slow
def test_reranker_empty_candidates():
    """Test reranking with empty candidates."""
    config = RerankConfig()
    reranker = MemoryReranker(config)

    query = "test query"
    candidates = []

    reranked = reranker.rerank(query, candidates, top_k=10)
    assert reranked == []


@pytest.mark.slow
def test_reranker_batch():
    """Test batch reranking."""
    config = RerankConfig()
    reranker = MemoryReranker(config)

    queries = ["What is Python?", "What is Java?"]
    candidates_list = [
        [
            {"content": "Python is a programming language", "distance": 0.3},
            {"content": "Java is also a language", "distance": 0.4},
        ],
        [
            {"content": "Java is a programming language", "distance": 0.3},
            {"content": "Python is also a language", "distance": 0.4},
        ],
    ]

    reranked = reranker.rerank_batch(queries, candidates_list, top_k=1)

    assert len(reranked) == 2
    assert all(len(r) == 1 for r in reranked)
    assert all("rerank_score" in r[0] for r in reranked)


@pytest.mark.slow
def test_reranker_score_pair():
    """Test scoring a single query-document pair."""
    config = RerankConfig()
    reranker = MemoryReranker(config)

    query = "What is Python?"
    document = "Python is a programming language"

    score = reranker.score_pair(query, document)
    assert isinstance(score, float)


def test_reranker_repr():
    """Test reranker string representation."""
    config = RerankConfig(model="test-model", batch_size=16)
    reranker = MemoryReranker.__new__(MemoryReranker)
    reranker.config = config

    repr_str = repr(reranker)
    assert "test-model" in repr_str
    assert "16" in repr_str
