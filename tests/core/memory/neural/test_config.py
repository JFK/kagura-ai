"""Tests for NeuralMemoryConfig."""

import warnings

import pytest

from kagura.core.memory.neural.config import NeuralMemoryConfig


class TestNeuralMemoryConfig:
    """Test suite for NeuralMemoryConfig validation and properties."""

    def test_default_config_valid(self):
        """Test that default configuration is valid."""
        config = NeuralMemoryConfig()
        assert config.learning_rate == 0.05
        assert config.decay_lambda == 0.01
        assert config.weight_max == 3.0

    def test_learning_rate_validation(self):
        """Test learning_rate must be in [0, 1]."""
        # Valid
        config = NeuralMemoryConfig(learning_rate=0.5)
        assert config.learning_rate == 0.5

        # Invalid: too high
        with pytest.raises(ValueError, match="learning_rate must be in"):
            NeuralMemoryConfig(learning_rate=1.5)

        # Invalid: negative
        with pytest.raises(ValueError, match="learning_rate must be in"):
            NeuralMemoryConfig(learning_rate=-0.1)

    def test_decay_lambda_validation(self):
        """Test decay_lambda must be in [0, 1]."""
        with pytest.raises(ValueError, match="decay_lambda must be in"):
            NeuralMemoryConfig(decay_lambda=2.0)

    def test_weight_max_validation(self):
        """Test weight_max must be positive."""
        with pytest.raises(ValueError, match="weight_max must be positive"):
            NeuralMemoryConfig(weight_max=0)

        with pytest.raises(ValueError, match="weight_max must be positive"):
            NeuralMemoryConfig(weight_max=-1.0)

    def test_spread_hops_validation(self):
        """Test spread_hops must be in [1, 3]."""
        # Valid
        for hops in [1, 2, 3]:
            config = NeuralMemoryConfig(spread_hops=hops)
            assert config.spread_hops == hops

        # Invalid
        with pytest.raises(ValueError, match="spread_hops must be in"):
            NeuralMemoryConfig(spread_hops=0)

        with pytest.raises(ValueError, match="spread_hops must be in"):
            NeuralMemoryConfig(spread_hops=4)

    def test_spread_decay_validation(self):
        """Test spread_decay must be in [0, 1]."""
        with pytest.raises(ValueError, match="spread_decay must be in"):
            NeuralMemoryConfig(spread_decay=1.5)

    def test_recency_tau_days_validation(self):
        """Test recency_tau_days must be positive."""
        with pytest.raises(ValueError, match="recency_tau_days must be positive"):
            NeuralMemoryConfig(recency_tau_days=0)

        with pytest.raises(ValueError, match="recency_tau_days must be positive"):
            NeuralMemoryConfig(recency_tau_days=-5)

    def test_importance_ema_alpha_validation(self):
        """Test importance_ema_alpha must be in [0, 1]."""
        with pytest.raises(ValueError, match="importance_ema_alpha must be in"):
            NeuralMemoryConfig(importance_ema_alpha=1.5)

    def test_co_activation_window_validation(self):
        """Test co_activation_window must be positive."""
        with pytest.raises(ValueError, match="co_activation_window must be positive"):
            NeuralMemoryConfig(co_activation_window=0)

    def test_min_co_activation_count_validation(self):
        """Test min_co_activation_count must be positive."""
        with pytest.raises(ValueError, match="min_co_activation_count must be positive"):
            NeuralMemoryConfig(min_co_activation_count=0)

    def test_decay_rate_validation(self):
        """Test decay_rate must be non-negative."""
        # Valid
        config = NeuralMemoryConfig(decay_rate=0.0)
        assert config.decay_rate == 0.0

        # Invalid
        with pytest.raises(ValueError, match="decay_rate must be non-negative"):
            NeuralMemoryConfig(decay_rate=-0.1)

    def test_prune_threshold_validation(self):
        """Test prune_threshold must be in [0, 1]."""
        with pytest.raises(ValueError, match="prune_threshold must be in"):
            NeuralMemoryConfig(prune_threshold=1.5)

    def test_consolidation_use_count_min_validation(self):
        """Test consolidation_use_count_min must be positive."""
        with pytest.raises(ValueError, match="consolidation_use_count_min must be positive"):
            NeuralMemoryConfig(consolidation_use_count_min=0)

    def test_consolidation_importance_min_validation(self):
        """Test consolidation_importance_min must be in [0, 1]."""
        with pytest.raises(ValueError, match="consolidation_importance_min must be in"):
            NeuralMemoryConfig(consolidation_importance_min=1.5)

    def test_gradient_clipping_validation(self):
        """Test gradient_clipping must be positive."""
        with pytest.raises(ValueError, match="gradient_clipping must be positive"):
            NeuralMemoryConfig(gradient_clipping=0)

    def test_batch_update_size_validation(self):
        """Test batch_update_size must be positive."""
        with pytest.raises(ValueError, match="batch_update_size must be positive"):
            NeuralMemoryConfig(batch_update_size=0)

    def test_async_update_delay_ms_validation(self):
        """Test async_update_delay_ms must be non-negative."""
        with pytest.raises(ValueError, match="async_update_delay_ms must be non-negative"):
            NeuralMemoryConfig(async_update_delay_ms=-100)

    def test_max_candidates_k_validation(self):
        """Test max_candidates_k must be positive."""
        with pytest.raises(ValueError, match="max_candidates_k must be positive"):
            NeuralMemoryConfig(max_candidates_k=0)

    def test_scoring_weights_sum_warning(self):
        """Test warning when scoring weights don't sum to ~1.0."""
        # Should warn
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            NeuralMemoryConfig(
                alpha=0.1, beta=0.1, gamma=0.1, delta=0.1, epsilon=0.1
            )  # sum=0.5
            assert len(w) == 1
            assert "sum to" in str(w[0].message)

        # Should not warn
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            NeuralMemoryConfig(
                alpha=0.55, beta=0.20, gamma=0.10, delta=0.10, epsilon=0.05
            )  # sum=1.0
            assert len(w) == 0

    def test_scoring_weights_normalized_property(self):
        """Test scoring_weights_normalized returns normalized weights."""
        config = NeuralMemoryConfig(
            alpha=0.5, beta=0.2, gamma=0.1, delta=0.1, epsilon=0.1
        )  # sum=1.0

        normalized = config.scoring_weights_normalized

        assert "alpha" in normalized
        assert "beta" in normalized
        assert "gamma" in normalized
        assert "delta" in normalized
        assert "epsilon" in normalized
        assert "zeta" in normalized

        # Check normalization (should sum to 1.0 excluding zeta)
        total = (
            normalized["alpha"]
            + normalized["beta"]
            + normalized["gamma"]
            + normalized["delta"]
            + normalized["epsilon"]
        )
        assert abs(total - 1.0) < 1e-6

        # Zeta (penalty) should not be normalized
        assert normalized["zeta"] == config.zeta

    def test_all_parameters_customizable(self):
        """Test that all parameters can be customized."""
        config = NeuralMemoryConfig(
            learning_rate=0.1,
            decay_lambda=0.02,
            weight_max=5.0,
            top_m_edges=64,
            spread_hops=2,
            spread_decay=0.7,
            spread_threshold=0.02,
            alpha=0.6,
            beta=0.15,
            gamma=0.12,
            delta=0.08,
            epsilon=0.05,
            zeta=0.3,
            recency_tau_days=21.0,
            importance_ema_alpha=0.4,
            track_co_activation=False,
            co_activation_window=600,
            min_co_activation_count=3,
            enable_decay=False,
            decay_background_interval=7200,
            decay_rate=0.002,
            prune_threshold=0.1,
            consolidation_use_count_min=5,
            consolidation_importance_min=0.7,
            consolidation_diversity_min=0.3,
            enable_user_sharding=False,
            enable_trust_modulation=False,
            gradient_clipping=1.0,
            batch_update_size=200,
            async_update_delay_ms=5000,
            max_candidates_k=128,
        )

        assert config.learning_rate == 0.1
        assert config.track_co_activation is False
        assert config.max_candidates_k == 128
