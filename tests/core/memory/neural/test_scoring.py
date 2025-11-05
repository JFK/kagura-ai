"""Tests for unified scoring system."""

from datetime import datetime, timezone, timedelta
import math

import pytest
import numpy as np

from kagura.core.graph.memory import GraphMemory
from kagura.core.memory.neural.activation import ActivationSpreader
from kagura.core.memory.neural.config import NeuralMemoryConfig
from kagura.core.memory.neural.models import NeuralMemoryNode, MemoryKind, SourceKind
from kagura.core.memory.neural.scoring import UnifiedScorer
from kagura.core.memory.neural.utils import (
    IMPORTANCE_STORED_WEIGHT,
    IMPORTANCE_FREQUENCY_WEIGHT,
)


@pytest.fixture
def config():
    """Create test configuration."""
    return NeuralMemoryConfig()


@pytest.fixture
def graph():
    """Create test graph."""
    return GraphMemory()


@pytest.fixture
def activation_spreader(graph, config):
    """Create activation spreader."""
    return ActivationSpreader(graph, config)


@pytest.fixture
def scorer(config, activation_spreader):
    """Create unified scorer."""
    return UnifiedScorer(config, activation_spreader)


@pytest.fixture
def test_node():
    """Create test node."""
    return NeuralMemoryNode(
        id="test_001",
        user_id="user_123",
        kind=MemoryKind.FACT,
        text="Python is great",
        embedding=[0.1, 0.2, 0.3],
        created_at=datetime.now(timezone.utc) - timedelta(days=7),
        last_used_at=datetime.now(timezone.utc) - timedelta(days=1),
        use_count=5,
        importance=0.7,
        confidence=0.9,
        source=SourceKind.USER,
    )


class TestUnifiedScorer:
    """Test suite for UnifiedScorer."""

    def test_initialization(self, scorer, config, activation_spreader):
        """Test scorer initializes correctly."""
        assert scorer.config == config
        assert scorer.activation_spreader == activation_spreader

    def test_calculate_recency_score(self, scorer, test_node):
        """Test recency score calculation."""
        current_time = datetime.now(timezone.utc)
        score = scorer._calculate_recency_score(test_node, current_time)

        # Should be exponential decay
        assert 0.0 < score <= 1.0

    def test_calculate_recency_score_never_used(self, scorer):
        """Test recency score for node never used."""
        node = NeuralMemoryNode(
            id="test",
            user_id="user",
            kind=MemoryKind.FACT,
            text="test",
            embedding=[0.1],
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
            last_used_at=None,  # Never used
        )

        current_time = datetime.now(timezone.utc)
        score = scorer._calculate_recency_score(node, current_time)

        assert 0.0 < score <= 1.0

    def test_calculate_importance_score(self, scorer, test_node):
        """Test importance score calculation."""
        score = scorer._calculate_importance_score(test_node)

        # Should combine stored importance and log frequency
        assert 0.0 <= score <= 1.0

    def test_calculate_importance_score_zero_use(self, scorer):
        """Test importance score with zero use count."""
        node = NeuralMemoryNode(
            id="test",
            user_id="user",
            kind=MemoryKind.FACT,
            text="test",
            embedding=[0.1],
            created_at=datetime.now(timezone.utc),
            use_count=0,
            importance=0.5,
        )

        score = scorer._calculate_importance_score(node)

        # Should be: STORED_WEIGHT * 0.5 + FREQ_WEIGHT * 0 = 0.35
        expected = IMPORTANCE_STORED_WEIGHT * 0.5
        assert abs(score - expected) < 1e-6

    def test_calculate_redundancy_penalty_no_selection(self, scorer, test_node):
        """Test redundancy penalty with no selected nodes."""
        penalty = scorer._calculate_redundancy_penalty(test_node, [])

        assert penalty == 0.0

    def test_calculate_redundancy_penalty_with_selection(self, scorer, test_node):
        """Test redundancy penalty with selected nodes."""
        # Similar embedding should have high penalty
        similar_embedding = [0.11, 0.21, 0.31]
        penalty = scorer._calculate_redundancy_penalty(test_node, [similar_embedding])

        assert 0.0 <= penalty <= 1.0

    def test_cosine_similarity(self, scorer):
        """Test cosine similarity calculation."""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]  # Identical

        sim = scorer._cosine_similarity(emb1, emb2)
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self, scorer):
        """Test cosine similarity for orthogonal vectors."""
        emb1 = [1.0, 0.0]
        emb2 = [0.0, 1.0]

        sim = scorer._cosine_similarity(emb1, emb2)
        assert abs(sim - 0.0) < 1e-6

    def test_cosine_similarity_zero_vector(self, scorer):
        """Test cosine similarity with zero vector."""
        emb1 = [0.0, 0.0]
        emb2 = [1.0, 0.0]

        sim = scorer._cosine_similarity(emb1, emb2)
        assert sim == 0.0

    def test_score_candidates(self, scorer, test_node):
        """Test scoring candidates."""
        candidates = [(test_node, 0.8)]

        results = scorer.score_candidates(
            query_embedding=[0.1, 0.2, 0.3],
            candidates=candidates,
            seed_nodes=None,
            selected_nodes=None,
        )

        assert len(results) == 1
        assert results[0].node == test_node
        assert 0.0 <= results[0].score <= 1.0
        assert "semantic" in results[0].components

    def test_mmr_rerank(self, scorer):
        """Test MMR re-ranking."""
        # Create test nodes with similar embeddings
        nodes = [
            NeuralMemoryNode(
                id=f"node_{i}",
                user_id="user",
                kind=MemoryKind.FACT,
                text=f"text_{i}",
                embedding=[float(i), 0.5, 0.5],
                created_at=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]

        from kagura.core.memory.neural.models import RecallResult

        results = [
            RecallResult(node=node, score=0.9 - i * 0.1) for i, node in enumerate(nodes)
        ]

        query_emb = [0.0, 0.5, 0.5]
        reranked = scorer.mmr_rerank(query_emb, results, lambda_param=0.5, top_k=2)

        assert len(reranked) <= 2
        # Should promote diversity

    def test_mmr_rerank_single_result(self, scorer, test_node):
        """Test MMR with single result (edge case)."""
        from kagura.core.memory.neural.models import RecallResult

        results = [RecallResult(node=test_node, score=0.9)]

        reranked = scorer.mmr_rerank([0.1, 0.2, 0.3], results, top_k=1)

        assert len(reranked) == 1
        assert reranked[0].node == test_node
