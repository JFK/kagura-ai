"""Neural Memory Network configuration.

This module defines the configuration dataclass for the Neural Memory system,
including hyperparameters for Hebbian learning, activation spreading, scoring,
and forgetting mechanisms.
"""

from dataclasses import dataclass


@dataclass
class NeuralMemoryConfig:
    """Configuration for Neural Memory Network.

    Attributes:
        # Hebbian Learning
        learning_rate: Learning rate (η) for Hebbian updates (0.0-1.0)
        decay_lambda: L2 decay coefficient (λ) to prevent weight explosion
        weight_max: Maximum edge weight (clipping threshold)
        top_m_edges: Keep only top-M strongest edges per node (sparsity)

        # Activation Spreading
        spread_hops: Number of hops for activation propagation (1-3)
        spread_decay: Decay factor (λ) for each hop (0.0-1.0)
        spread_threshold: Minimum activation value to continue spreading

        # Scoring Weights (must sum to ~1.0 for semantic+graph+temporal+trust)
        alpha: Weight for semantic similarity (embedding cosine)
        beta: Weight for graph association (activation spreading)
        gamma: Weight for recency (temporal decay)
        delta: Weight for importance (use count + LLM score)
        epsilon: Weight for trust (confidence score)
        zeta: Weight for redundancy penalty (MMR-style)

        # Temporal Parameters
        recency_tau_days: Time constant (τ) for exponential recency decay
        importance_ema_alpha: EMA smoothing for importance updates

        # Co-Activation Tracking
        track_co_activation: Enable co-activation tracking
        co_activation_window: Time window (seconds) for same-session tracking
        min_co_activation_count: Minimum count to create/strengthen edge

        # Forgetting/Decay
        enable_decay: Enable automatic edge weight decay
        decay_background_interval: Interval (seconds) for background decay task
        decay_rate: Exponential decay rate for unused edges
        prune_threshold: Remove edges below this weight

        # Consolidation (Short-term → Long-term)
        consolidation_use_count_min: Min use_count for long-term promotion
        consolidation_importance_min: Min importance for long-term promotion
        consolidation_diversity_min: Min diversity score for long-term promotion

        # Privacy & Security (SISA-compliant)
        enable_user_sharding: Isolate memory graphs by user_id
        enable_trust_modulation: Modulate learning rate by confidence score
        gradient_clipping: Clip total Δw per update (DP-SGD style)

        # Performance
        batch_update_size: Batch size for delayed Hebbian updates
        async_update_delay_ms: Delay (ms) before applying updates
        max_candidates_k: Maximum candidates for primary retrieval
    """

    # Hebbian Learning
    learning_rate: float = 0.05
    decay_lambda: float = 0.01
    weight_max: float = 3.0
    top_m_edges: int = 32

    # Activation Spreading
    spread_hops: int = 1
    spread_decay: float = 0.6
    spread_threshold: float = 0.01

    # Scoring Weights (Research paper defaults)
    alpha: float = 0.55  # Semantic similarity
    beta: float = 0.20  # Graph association
    gamma: float = 0.10  # Recency
    delta: float = 0.10  # Importance
    epsilon: float = 0.05  # Trust
    zeta: float = 0.25  # Redundancy penalty

    # Temporal Parameters
    recency_tau_days: float = 14.0  # 2-week half-life
    importance_ema_alpha: float = 0.3

    # Co-Activation Tracking
    track_co_activation: bool = True
    co_activation_window: int = 300  # 5 minutes
    min_co_activation_count: int = 2

    # Forgetting/Decay
    enable_decay: bool = True
    decay_background_interval: int = 3600  # 1 hour
    decay_rate: float = 0.001
    prune_threshold: float = 0.05

    # Consolidation
    consolidation_use_count_min: int = 3
    consolidation_importance_min: float = 0.65
    consolidation_diversity_min: float = 0.2

    # Privacy & Security
    enable_user_sharding: bool = True  # MANDATORY for GDPR
    enable_trust_modulation: bool = True  # Poisoning defense
    gradient_clipping: float = 0.5  # Max total Δw per node per update

    # Performance
    batch_update_size: int = 100
    async_update_delay_ms: int = 2000  # 2 seconds
    max_candidates_k: int = 64

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        # Validate ranges
        if not (0.0 <= self.learning_rate <= 1.0):
            raise ValueError(
                f"learning_rate must be in [0, 1], got {self.learning_rate}"
            )
        if not (0.0 <= self.decay_lambda <= 1.0):
            raise ValueError(f"decay_lambda must be in [0, 1], got {self.decay_lambda}")
        if not self.weight_max > 0:
            raise ValueError(f"weight_max must be positive, got {self.weight_max}")
        if not self.top_m_edges > 0:
            raise ValueError(f"top_m_edges must be positive, got {self.top_m_edges}")

        if not (1 <= self.spread_hops <= 3):
            raise ValueError(f"spread_hops must be in [1, 3], got {self.spread_hops}")
        if not (0.0 <= self.spread_decay <= 1.0):
            raise ValueError(f"spread_decay must be in [0, 1], got {self.spread_decay}")

        # Validate scoring weights (should sum to ~1.0 for primary signals)
        primary_sum = self.alpha + self.beta + self.gamma + self.delta + self.epsilon
        if not (0.9 <= primary_sum <= 1.1):
            import warnings

            warnings.warn(
                f"Scoring weights sum to {primary_sum:.2f}, expected ~1.0. "
                "This may cause score normalization issues."
            )

        if not self.recency_tau_days > 0:
            raise ValueError(
                f"recency_tau_days must be positive, got {self.recency_tau_days}"
            )
        if not (0.0 <= self.importance_ema_alpha <= 1.0):
            raise ValueError(
                f"importance_ema_alpha must be in [0, 1], "
                f"got {self.importance_ema_alpha}"
            )

        if not self.co_activation_window > 0:
            raise ValueError(
                f"co_activation_window must be positive, "
                f"got {self.co_activation_window}"
            )
        if not self.min_co_activation_count > 0:
            raise ValueError(
                f"min_co_activation_count must be positive, "
                f"got {self.min_co_activation_count}"
            )

        if not self.decay_rate >= 0:
            raise ValueError(f"decay_rate must be non-negative, got {self.decay_rate}")
        if not (0.0 <= self.prune_threshold <= 1.0):
            raise ValueError(
                f"prune_threshold must be in [0, 1], got {self.prune_threshold}"
            )

        if not self.consolidation_use_count_min > 0:
            raise ValueError(
                f"consolidation_use_count_min must be positive, "
                f"got {self.consolidation_use_count_min}"
            )
        if not (0.0 <= self.consolidation_importance_min <= 1.0):
            raise ValueError(
                f"consolidation_importance_min must be in [0, 1], "
                f"got {self.consolidation_importance_min}"
            )

        if not self.gradient_clipping > 0:
            raise ValueError(
                f"gradient_clipping must be positive, got {self.gradient_clipping}"
            )

        if not self.batch_update_size > 0:
            raise ValueError(
                f"batch_update_size must be positive, got {self.batch_update_size}"
            )
        if not self.async_update_delay_ms >= 0:
            raise ValueError(
                f"async_update_delay_ms must be non-negative, "
                f"got {self.async_update_delay_ms}"
            )
        if not self.max_candidates_k > 0:
            raise ValueError(
                f"max_candidates_k must be positive, got {self.max_candidates_k}"
            )

    @property
    def scoring_weights_normalized(self) -> dict[str, float]:
        """Get normalized scoring weights (sum=1.0)."""
        total = self.alpha + self.beta + self.gamma + self.delta + self.epsilon
        return {
            "alpha": self.alpha / total,
            "beta": self.beta / total,
            "gamma": self.gamma / total,
            "delta": self.delta / total,
            "epsilon": self.epsilon / total,
            "zeta": self.zeta,  # Penalty, not normalized
        }
