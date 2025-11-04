"""Hybrid search combining vector and lexical search with RRF fusion.

Implements Reciprocal Rank Fusion (RRF) to combine results from:
- Vector search (semantic similarity)
- Lexical search (keyword matching)

Based on "Reciprocal Rank Fusion outperforms Condorcet and individual Rank
Learning Methods" (Cormack et al., SIGIR 2009).

Example:
    >>> from kagura.core.memory.hybrid_search import rrf_fusion
    >>> vector_results = [
    ...     {"id": "doc1", "score": 0.9, "rank": 1},
    ...     {"id": "doc2", "score": 0.7, "rank": 2},
    ... ]
    >>> lexical_results = [
    ...     {"id": "doc2", "score": 5.2, "rank": 1},
    ...     {"id": "doc3", "score": 3.1, "rank": 2},
    ... ]
    >>> fused = rrf_fusion(vector_results, lexical_results, k=60)
"""

import math
from datetime import datetime, timezone
from typing import Any


def rrf_fusion(
    vector_results: list[dict[str, Any]],
    lexical_results: list[dict[str, Any]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Combine search results using Reciprocal Rank Fusion (RRF).

    RRF formula: RRF(d) = Σ_s 1 / (k + rank_s(d))

    where:
    - d is a document
    - s is a search system (vector or lexical)
    - rank_s(d) is the rank of document d in system s
    - k is a constant (typically 60)

    Args:
        vector_results: Results from vector search with 'id' and 'rank' fields
        lexical_results: Results from lexical search with 'id' and 'rank' fields
        k: RRF constant (default: 60, as per original paper)

    Returns:
        List of (doc_id, rrf_score) tuples, sorted by score descending

    Example:
        >>> fused = rrf_fusion(vector_results, lexical_results, k=60)
        >>> print(fused[0])  # Best result
        ('doc2', 0.0328)  # (id, rrf_score)

    Note:
        - k=60 is the standard value from the original RRF paper
        - Lower k gives more weight to top-ranked documents
        - Higher k gives more uniform weighting across ranks
    """
    rrf_scores: dict[str, float] = {}

    # Add scores from vector search
    for result in vector_results:
        doc_id = result["id"]
        rank = result["rank"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    # Add scores from lexical search
    for result in lexical_results:
        doc_id = result["id"]
        rank = result["rank"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    # Sort by RRF score (descending)
    sorted_results = sorted(
        rrf_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return sorted_results


def rrf_fusion_multi(
    results_list: list[list[dict[str, Any]]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Combine results from multiple search systems using RRF.

    Generalized version of rrf_fusion for N search systems.

    Args:
        results_list: List of result lists from different search systems
        k: RRF constant (default: 60)

    Returns:
        List of (doc_id, rrf_score) tuples, sorted by score descending

    Example:
        >>> fused = rrf_fusion_multi([
        ...     vector_results,
        ...     lexical_results,
        ...     graph_results,
        ... ], k=60)
    """
    rrf_scores: dict[str, float] = {}

    for results in results_list:
        for result in results:
            doc_id = result["id"]
            rank = result["rank"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    # Sort by RRF score (descending)
    sorted_results = sorted(
        rrf_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return sorted_results


def weighted_rrf_fusion(
    vector_results: list[dict[str, Any]],
    lexical_results: list[dict[str, Any]],
    k: int = 60,
    vector_weight: float = 0.5,
    lexical_weight: float = 0.5,
) -> list[tuple[str, float]]:
    """Weighted version of RRF fusion.

    Allows adjusting the relative importance of vector vs lexical search.

    Formula: Weighted_RRF(d) = w_v * RRF_v(d) + w_l * RRF_l(d)

    Args:
        vector_results: Results from vector search
        lexical_results: Results from lexical search
        k: RRF constant
        vector_weight: Weight for vector search (default: 0.5)
        lexical_weight: Weight for lexical search (default: 0.5)

    Returns:
        List of (doc_id, weighted_rrf_score) tuples

    Note:
        Weights should sum to 1.0 for normalized scores.
        Use this when one search method is significantly better than the other.
    """
    rrf_scores: dict[str, float] = {}

    # Add weighted scores from vector search
    for result in vector_results:
        doc_id = result["id"]
        rank = result["rank"]
        score = vector_weight * (1.0 / (k + rank))
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + score

    # Add weighted scores from lexical search
    for result in lexical_results:
        doc_id = result["id"]
        rank = result["rank"]
        score = lexical_weight * (1.0 / (k + rank))
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + score

    # Sort by weighted RRF score (descending)
    sorted_results = sorted(
        rrf_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return sorted_results


def apply_time_decay(
    results: list[dict[str, Any]],
    decay_days: float = 30.0,
) -> list[dict[str, Any]]:
    """Apply exponential time decay boosting to search results.

    Recent memories are more relevant and receive a higher score boost.
    Uses exponential decay: score_new = score * exp(-days_old / decay_days)

    Args:
        results: Search results with 'score' and 'created_at' fields
        decay_days: Time constant for exponential decay (default: 30.0 days)
            At decay_days, memories decay by ~63% (1 - 1/e), not 50%

    Returns:
        Results with time-decayed scores, re-sorted by new scores

    Example:
        >>> from datetime import datetime, timedelta
        >>> results = [
        ...     {"id": "old", "score": 0.8, "created_at": datetime.now() - timedelta(days=60)},
        ...     {"id": "recent", "score": 0.7, "created_at": datetime.now() - timedelta(days=5)},
        ... ]
        >>> decayed = apply_time_decay(results, decay_days=30.0)
        >>> # Recent memory will likely rank higher after decay

    Note:
        - decay_days=30: memories decay by ~63% after 30 days
        - Lower decay_days = stronger recency bias
        - Higher decay_days = weaker recency bias
        - If 'created_at' is missing, assumes current time (no decay)
    """
    now = datetime.now(timezone.utc)
    decayed_results = []

    for result in results:
        result_copy = result.copy()

        # Get creation time (default to now if missing)
        created_at = result.get("created_at")
        if created_at is None:
            # No timestamp, no decay
            decayed_results.append(result_copy)
            continue

        # Calculate days old
        if isinstance(created_at, str):
            # Parse ISO format timestamp
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                # Invalid timestamp, no decay
                decayed_results.append(result_copy)
                continue

        days_old = (now - created_at).total_seconds() / 86400.0  # seconds to days

        # Apply exponential decay
        decay_factor = math.exp(-days_old / decay_days)

        # Get original score (try multiple field names)
        # Use explicit None checking to handle score=0.0 correctly
        score = result.get("score")
        if score is not None:
            original_score = score
        else:
            rrf_score = result.get("rrf_score")
            original_score = rrf_score if rrf_score is not None else 0.0

        # Apply decay
        result_copy["score"] = original_score * decay_factor
        result_copy["_time_decay_factor"] = decay_factor
        result_copy["_days_old"] = days_old

        decayed_results.append(result_copy)

    # Re-sort by new scores
    decayed_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    return decayed_results
