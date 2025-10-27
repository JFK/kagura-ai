"""Tests for multi-dimensional recall scoring."""

from datetime import datetime, timedelta

import pytest

from kagura.config.memory_config import RecallScorerConfig
from kagura.core.memory.recall_scorer import RecallScorer


def test_recall_scorer_config_defaults():
    """Test default recall scorer configuration."""
    config = RecallScorerConfig()
    assert config.weights["semantic_similarity"] == 0.30
    assert config.weights["recency"] == 0.20
    assert config.weights["access_frequency"] == 0.15
    assert config.weights["graph_distance"] == 0.15
    assert config.weights["importance"] == 0.20
    assert config.recency_decay_days == 30
    assert config.frequency_saturation == 100


def test_recall_scorer_initialization():
    """Test recall scorer initialization."""
    config = RecallScorerConfig()
    scorer = RecallScorer(config)
    assert scorer.config == config


def test_recall_scorer_compute_score_recent():
    """Test scoring for recent memory."""
    scorer = RecallScorer()

    score = scorer.compute_score(
        semantic_sim=0.8,
        created_at=datetime.now() - timedelta(days=1),
        last_accessed=datetime.now(),
        access_count=5,
        graph_distance=1,
        importance=0.7,
    )

    assert 0.0 <= score <= 1.0
    # Recent memory with high similarity should score highly
    assert score > 0.5


def test_recall_scorer_compute_score_old():
    """Test scoring for old memory."""
    scorer = RecallScorer()

    score = scorer.compute_score(
        semantic_sim=0.8,
        created_at=datetime.now() - timedelta(days=180),
        last_accessed=datetime.now() - timedelta(days=180),
        access_count=1,
        graph_distance=5,
        importance=0.3,
    )

    assert 0.0 <= score <= 1.0
    # Old memory with low importance should score lower
    assert score < 0.7


def test_recall_scorer_recency_decay():
    """Test recency decay over time."""
    scorer = RecallScorer()

    now = datetime.now()
    recent_score = scorer._compute_recency_score(
        created_at=now - timedelta(days=1), last_accessed=now
    )
    old_score = scorer._compute_recency_score(
        created_at=now - timedelta(days=90), last_accessed=now - timedelta(days=90)
    )

    # Recent should score higher than old
    assert recent_score > old_score
    # Both should be in [0, 1]
    assert 0.0 <= recent_score <= 1.0
    assert 0.0 <= old_score <= 1.0


def test_recall_scorer_frequency_scaling():
    """Test frequency scaling with logarithmic saturation."""
    scorer = RecallScorer()

    low_freq_score = scorer._compute_frequency_score(access_count=1)
    mid_freq_score = scorer._compute_frequency_score(access_count=10)
    high_freq_score = scorer._compute_frequency_score(access_count=100)

    # More accesses should give higher scores
    assert low_freq_score < mid_freq_score < high_freq_score
    # All should be in [0, 1]
    assert all(
        0.0 <= s <= 1.0 for s in [low_freq_score, mid_freq_score, high_freq_score]
    )


def test_recall_scorer_frequency_zero():
    """Test frequency scoring with zero accesses."""
    scorer = RecallScorer()
    score = scorer._compute_frequency_score(access_count=0)
    assert score == 0.0


def test_recall_scorer_graph_distance():
    """Test graph distance scoring."""
    scorer = RecallScorer()

    close_score = scorer._compute_graph_score(graph_distance=0)
    mid_score = scorer._compute_graph_score(graph_distance=2)
    far_score = scorer._compute_graph_score(graph_distance=10)

    # Closer should score higher
    assert close_score > mid_score > far_score
    # Same node (distance=0) should score 1.0
    assert close_score == 1.0


def test_recall_scorer_graph_distance_none():
    """Test graph distance scoring when not in graph."""
    scorer = RecallScorer()
    score = scorer._compute_graph_score(graph_distance=None)
    assert score == 0.0


def test_recall_scorer_batch():
    """Test batch scoring."""
    scorer = RecallScorer()

    now = datetime.now()
    scores = scorer.compute_batch_scores(
        semantic_sims=[0.8, 0.6, 0.9],
        created_ats=[now - timedelta(days=i) for i in [1, 10, 5]],
        last_accesseds=[now] * 3,
        access_counts=[5, 2, 10],
        graph_distances=[1, 3, 2],
        importances=[0.7, 0.5, 0.9],
    )

    assert len(scores) == 3
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_recall_scorer_batch_length_mismatch():
    """Test batch scoring with mismatched lengths."""
    scorer = RecallScorer()

    now = datetime.now()
    with pytest.raises(ValueError, match="same length"):
        scorer.compute_batch_scores(
            semantic_sims=[0.8, 0.6],
            created_ats=[now],  # Wrong length
            last_accesseds=[now, now],
            access_counts=[5, 2],
            graph_distances=[1, 3],
            importances=[0.7, 0.5],
        )


def test_recall_scorer_custom_weights():
    """Test scoring with custom weights."""
    config = RecallScorerConfig(
        weights={
            "semantic_similarity": 0.5,
            "recency": 0.5,
            "access_frequency": 0.0,
            "graph_distance": 0.0,
            "importance": 0.0,
        }
    )
    scorer = RecallScorer(config)

    score = scorer.compute_score(
        semantic_sim=0.8,
        created_at=datetime.now(),
        last_accessed=datetime.now(),
        access_count=0,
        graph_distance=None,
        importance=0.0,
    )

    # With custom weights, should only consider semantic + recency
    assert 0.0 <= score <= 1.0


def test_recall_scorer_repr():
    """Test recall scorer string representation."""
    config = RecallScorerConfig(recency_decay_days=60)
    scorer = RecallScorer(config)

    repr_str = repr(scorer)
    assert "60" in repr_str
    assert "RecallScorer" in repr_str
