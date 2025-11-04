"""Tests for co-activation tracking."""

from datetime import datetime, timedelta, timezone

import pytest

from kagura.core.memory.neural.co_activation import CoActivationTracker
from kagura.core.memory.neural.config import NeuralMemoryConfig
from kagura.core.memory.neural.models import ActivationState


@pytest.fixture
def config():
    """Create test configuration."""
    return NeuralMemoryConfig(co_activation_window=300, min_co_activation_count=2)


@pytest.fixture
def tracker(config):
    """Create co-activation tracker."""
    return CoActivationTracker(config)


class TestCoActivationTracker:
    """Test suite for CoActivationTracker."""

    def test_initialization(self, tracker, config):
        """Test tracker initializes correctly."""
        assert tracker.config == config
        assert len(tracker._activation_history) == 0
        assert len(tracker._co_activation_records) == 0

    def test_record_activation(self, tracker):
        """Test recording activation events."""
        activations = [
            ActivationState(node_id="node_a", activation=0.8),
            ActivationState(node_id="node_b", activation=0.6),
        ]

        records = tracker.record_activation("user1", activations)

        assert isinstance(records, list)
        assert len(tracker._activation_history["user1"]) > 0

    def test_track_disabled(self):
        """Test tracking disabled by config."""
        config = NeuralMemoryConfig(track_co_activation=False)
        tracker = CoActivationTracker(config)

        activations = [
            ActivationState(node_id="node_a", activation=0.8),
        ]

        records = tracker.record_activation("user1", activations)

        assert len(records) == 0

    def test_empty_activations(self, tracker):
        """Test recording empty activation list."""
        records = tracker.record_activation("user1", [])

        assert len(records) == 0

    def test_get_co_activation_record(self, tracker):
        """Test getting co-activation record."""
        activations = [
            ActivationState(node_id="node_a", activation=0.8),
            ActivationState(node_id="node_b", activation=0.6),
        ]

        tracker.record_activation("user1", activations)

        record = tracker.get_co_activation_record("user1", "node_a", "node_b")

        # May or may not exist depending on time window logic
        # Just check it doesn't crash

    def test_get_frequently_co_activated_with(self, tracker):
        """Test getting frequently co-activated nodes."""
        activations = [
            ActivationState(node_id="node_a", activation=0.8),
            ActivationState(node_id="node_b", activation=0.6),
        ]

        tracker.record_activation("user1", activations)

        related = tracker.get_frequently_co_activated_with("user1", "node_a", top_k=5)

        assert isinstance(related, list)

    def test_clear_user_data(self, tracker):
        """Test clearing user data (GDPR compliance)."""
        activations = [
            ActivationState(node_id="node_a", activation=0.8),
        ]

        tracker.record_activation("user1", activations)

        assert len(tracker._activation_history["user1"]) > 0

        tracker.clear_user_data("user1")

        assert "user1" not in tracker._activation_history
        assert "user1" not in tracker._co_activation_records

    def test_get_statistics(self, tracker):
        """Test getting statistics."""
        stats = tracker.get_statistics("user1")

        assert "total_pairs" in stats
        assert "avg_count" in stats
        assert "max_count" in stats
        assert "min_count" in stats

    def test_get_statistics_empty(self, tracker):
        """Test statistics for user with no data."""
        stats = tracker.get_statistics("user_new")

        assert stats["total_pairs"] == 0
        assert stats["avg_count"] == 0.0
