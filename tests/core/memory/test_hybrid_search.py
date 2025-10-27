"""Tests for hybrid search with RRF fusion."""

from kagura.core.memory.hybrid_search import (
    rrf_fusion,
    rrf_fusion_multi,
    weighted_rrf_fusion,
)


def test_rrf_fusion_basic():
    """Test basic RRF fusion."""
    vector_results = [
        {"id": "doc1", "rank": 1, "score": 0.9},
        {"id": "doc2", "rank": 2, "score": 0.7},
        {"id": "doc3", "rank": 3, "score": 0.5},
    ]

    lexical_results = [
        {"id": "doc2", "rank": 1, "score": 5.2},
        {"id": "doc3", "rank": 2, "score": 3.1},
        {"id": "doc4", "rank": 3, "score": 2.0},
    ]

    fused = rrf_fusion(vector_results, lexical_results, k=60)

    # Should return tuples of (doc_id, rrf_score)
    assert isinstance(fused, list)
    assert all(isinstance(item, tuple) for item in fused)
    assert all(len(item) == 2 for item in fused)

    # doc2 appears in both, should rank highest
    doc_ids = [doc_id for doc_id, _ in fused]
    assert "doc2" in doc_ids

    # Scores should be in descending order
    scores = [score for _, score in fused]
    assert scores == sorted(scores, reverse=True)


def test_rrf_fusion_empty():
    """Test RRF fusion with empty results."""
    vector_results = []
    lexical_results = []

    fused = rrf_fusion(vector_results, lexical_results, k=60)
    assert fused == []


def test_rrf_fusion_one_source():
    """Test RRF fusion with only one source."""
    vector_results = [
        {"id": "doc1", "rank": 1},
        {"id": "doc2", "rank": 2},
    ]
    lexical_results = []

    fused = rrf_fusion(vector_results, lexical_results, k=60)

    # Should still work with one source
    assert len(fused) == 2
    assert fused[0][0] == "doc1"  # Rank 1 should be first


def test_rrf_fusion_k_parameter():
    """Test different k values."""
    vector_results = [{"id": "doc1", "rank": 1}]
    lexical_results = [{"id": "doc1", "rank": 1}]

    # k=60 (standard)
    fused_60 = rrf_fusion(vector_results, lexical_results, k=60)

    # k=10 (gives more weight to top ranks)
    fused_10 = rrf_fusion(vector_results, lexical_results, k=10)

    # Both should return same doc, but different scores
    assert fused_60[0][0] == fused_10[0][0]
    assert fused_60[0][1] != fused_10[0][1]

    # Lower k gives higher scores for top-ranked docs
    assert fused_10[0][1] > fused_60[0][1]


def test_rrf_fusion_multi():
    """Test multi-source RRF fusion."""
    results_list = [
        [{"id": "doc1", "rank": 1}, {"id": "doc2", "rank": 2}],  # Vector
        [{"id": "doc2", "rank": 1}, {"id": "doc3", "rank": 2}],  # Lexical
        [{"id": "doc1", "rank": 1}, {"id": "doc3", "rank": 2}],  # Graph
    ]

    fused = rrf_fusion_multi(results_list, k=60)

    # Should combine all three sources
    assert isinstance(fused, list)
    assert len(fused) > 0

    # Scores should be in descending order
    scores = [score for _, score in fused]
    assert scores == sorted(scores, reverse=True)


def test_rrf_fusion_multi_empty():
    """Test multi-source fusion with empty results."""
    results_list = [[], [], []]
    fused = rrf_fusion_multi(results_list, k=60)
    assert fused == []


def test_weighted_rrf_fusion():
    """Test weighted RRF fusion."""
    vector_results = [{"id": "doc1", "rank": 1}]
    lexical_results = [{"id": "doc2", "rank": 1}]

    # Equal weights (0.5, 0.5)
    fused_equal = weighted_rrf_fusion(
        vector_results,
        lexical_results,
        k=60,
        vector_weight=0.5,
        lexical_weight=0.5,
    )

    # Vector-heavy (0.8, 0.2)
    fused_vector_heavy = weighted_rrf_fusion(
        vector_results,
        lexical_results,
        k=60,
        vector_weight=0.8,
        lexical_weight=0.2,
    )

    # Lexical-heavy (0.2, 0.8)
    fused_lexical_heavy = weighted_rrf_fusion(
        vector_results,
        lexical_results,
        k=60,
        vector_weight=0.2,
        lexical_weight=0.8,
    )

    # Equal weights: both docs should be present
    assert len(fused_equal) == 2

    # Vector-heavy: doc1 should score higher
    doc1_score_vh = next(s for d, s in fused_vector_heavy if d == "doc1")
    doc2_score_vh = next(s for d, s in fused_vector_heavy if d == "doc2")
    assert doc1_score_vh > doc2_score_vh

    # Lexical-heavy: doc2 should score higher
    doc1_score_lh = next(s for d, s in fused_lexical_heavy if d == "doc1")
    doc2_score_lh = next(s for d, s in fused_lexical_heavy if d == "doc2")
    assert doc2_score_lh > doc1_score_lh


def test_weighted_rrf_zero_weight():
    """Test weighted fusion with zero weight."""
    vector_results = [{"id": "doc1", "rank": 1}]
    lexical_results = [{"id": "doc2", "rank": 1}]

    # Zero lexical weight = vector only
    fused = weighted_rrf_fusion(
        vector_results,
        lexical_results,
        k=60,
        vector_weight=1.0,
        lexical_weight=0.0,
    )

    # doc1 should have non-zero score, doc2 should have zero
    doc1_score = next(s for d, s in fused if d == "doc1")
    doc2_score = next(s for d, s in fused if d == "doc2")

    assert doc1_score > 0.0
    assert doc2_score == 0.0
