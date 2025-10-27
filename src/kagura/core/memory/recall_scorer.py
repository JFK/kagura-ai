"""Multi-dimensional recall scoring inspired by DNC/NTM.

Implements composite scoring from multiple signals:
1. Semantic similarity (content-based addressing)
2. Recency (temporal decay)
3. Access frequency (usage-based weighting)
4. Graph distance (relational proximity)
5. Importance (user-assigned priority)

Based on research from:
- Differentiable Neural Computer (DNC) - Graves et al. 2016
- Neural Turing Machine (NTM) - Graves et al. 2014

Example:
    >>> scorer = RecallScorer()
    >>> score = scorer.compute_score(
    ...     semantic_sim=0.85,
    ...     created_at=datetime.now() - timedelta(days=7),
    ...     last_accessed=datetime.now() - timedelta(days=1),
    ...     access_count=5,
    ...     graph_distance=2,
    ...     importance=0.8
    ... )
    >>> print(f"Composite score: {score:.3f}")
"""

from datetime import datetime
from typing import Optional

import numpy as np

from kagura.config.memory_config import RecallScorerConfig


class RecallScorer:
    """Multi-dimensional memory recall scorer.

    Computes composite recall scores from multiple signals, inspired by
    DNC/NTM's memory addressing mechanisms.

    Attributes:
        config: Recall scorer configuration
    """

    def __init__(self, config: Optional[RecallScorerConfig] = None):
        """Initialize recall scorer.

        Args:
            config: RecallScorerConfig instance (defaults to standard weights)
        """
        self.config = config or RecallScorerConfig()

    def compute_score(
        self,
        semantic_sim: float,
        created_at: datetime,
        last_accessed: Optional[datetime] = None,
        access_count: int = 0,
        graph_distance: Optional[int] = None,
        importance: float = 0.5,
    ) -> float:
        """Compute composite recall score from multiple signals.

        Args:
            semantic_sim: Semantic similarity (0.0-1.0, cosine distance)
            created_at: Memory creation timestamp
            last_accessed: Last access timestamp (None if never accessed)
            access_count: Number of times memory has been accessed
            graph_distance: Graph distance in hops (None if not in graph)
            importance: User-assigned importance (0.0-1.0)

        Returns:
            Composite score (0.0-1.0, higher is better)

        Note:
            Each component is normalized to [0, 1] and combined using
            weighted average based on config.weights.
        """
        weights = self.config.weights

        # 1. Semantic similarity (already normalized 0-1)
        s_semantic = float(semantic_sim)

        # 2. Recency decay (exponential)
        s_recency = self._compute_recency_score(created_at, last_accessed)

        # 3. Access frequency (log-scaled)
        s_frequency = self._compute_frequency_score(access_count)

        # 4. Graph distance (inverse)
        s_graph = self._compute_graph_score(graph_distance)

        # 5. Importance (already normalized 0-1)
        s_importance = float(importance)

        # Weighted combination
        composite_score = (
            weights.get("semantic_similarity", 0.3) * s_semantic
            + weights.get("recency", 0.2) * s_recency
            + weights.get("access_frequency", 0.15) * s_frequency
            + weights.get("graph_distance", 0.15) * s_graph
            + weights.get("importance", 0.2) * s_importance
        )

        # Clamp to [0, 1]
        return float(np.clip(composite_score, 0.0, 1.0))

    def _compute_recency_score(
        self, created_at: datetime, last_accessed: Optional[datetime]
    ) -> float:
        """Compute recency score with exponential decay.

        Uses last_accessed if available, otherwise uses created_at.
        Decay rate: exp(-days / decay_days), where decay_days is configured.

        Args:
            created_at: Memory creation timestamp
            last_accessed: Last access timestamp (None if never accessed)

        Returns:
            Recency score (0.0-1.0)
        """
        now = datetime.now()
        reference_time = last_accessed if last_accessed else created_at

        # Handle timezone-naive vs timezone-aware datetime
        if reference_time.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=reference_time.tzinfo)
        elif reference_time.tzinfo is None and now.tzinfo is not None:
            reference_time = reference_time.replace(tzinfo=now.tzinfo)

        days_elapsed = (now - reference_time).total_seconds() / 86400.0

        # Exponential decay: e^(-t/τ)
        # τ = decay_days (30 by default, meaning ~63% decay after 30 days)
        decay_constant = float(self.config.recency_decay_days)
        score = np.exp(-days_elapsed / decay_constant)

        return float(score)

    def _compute_frequency_score(self, access_count: int) -> float:
        """Compute frequency score with logarithmic scaling.

        Uses log scaling to prevent frequently-accessed memories from
        dominating the score (diminishing returns).

        Args:
            access_count: Number of accesses

        Returns:
            Frequency score (0.0-1.0)
        """
        saturation = float(self.config.frequency_saturation)

        # Log scaling: log(1 + count) / log(1 + saturation)
        # Saturates at saturation_point (100 by default)
        if access_count <= 0:
            return 0.0

        score = np.log1p(access_count) / np.log1p(saturation)
        return float(np.clip(score, 0.0, 1.0))

    def _compute_graph_score(self, graph_distance: Optional[int]) -> float:
        """Compute graph distance score (inverse distance).

        Closer nodes in the knowledge graph get higher scores.
        Uses 1/(1 + distance) scaling.

        Args:
            graph_distance: Distance in hops (None if not in graph)

        Returns:
            Graph score (0.0-1.0)
        """
        if graph_distance is None:
            # Not in graph or no graph connection
            return 0.0

        # Inverse distance: 1 / (1 + distance)
        # distance=0 (same node) -> 1.0
        # distance=1 (1 hop) -> 0.5
        # distance=2 (2 hops) -> 0.33
        # distance=∞ -> 0.0
        score = 1.0 / (1.0 + float(graph_distance))
        return float(score)

    def compute_batch_scores(
        self,
        semantic_sims: list[float],
        created_ats: list[datetime],
        last_accesseds: list[Optional[datetime]],
        access_counts: list[int],
        graph_distances: list[Optional[int]],
        importances: list[float],
    ) -> list[float]:
        """Compute scores for a batch of memories (optimized).

        Args:
            semantic_sims: List of semantic similarities
            created_ats: List of creation timestamps
            last_accesseds: List of last access timestamps
            access_counts: List of access counts
            graph_distances: List of graph distances
            importances: List of importance values

        Returns:
            List of composite scores

        Note:
            All input lists must have the same length.
        """
        n = len(semantic_sims)
        if not all(
            len(lst) == n
            for lst in [
                created_ats,
                last_accesseds,
                access_counts,
                graph_distances,
                importances,
            ]
        ):
            raise ValueError("All input lists must have the same length")

        scores = []
        for i in range(n):
            score = self.compute_score(
                semantic_sim=semantic_sims[i],
                created_at=created_ats[i],
                last_accessed=last_accesseds[i],
                access_count=access_counts[i],
                graph_distance=graph_distances[i],
                importance=importances[i],
            )
            scores.append(score)

        return scores

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RecallScorer("
            f"weights={self.config.weights}, "
            f"decay_days={self.config.recency_decay_days})"
        )
