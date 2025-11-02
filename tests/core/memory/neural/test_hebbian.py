"""Tests for Hebbian learning."""

from datetime import datetime, timezone

import pytest

from kagura.core.graph.memory import GraphMemory
from kagura.core.memory.neural.config import NeuralMemoryConfig
from kagura.core.memory.neural.hebbian import HebbianLearner
from kagura.core.memory.neural.models import ActivationState, NeuralMemoryNode, MemoryKind, SourceKind


@pytest.fixture
def graph():
    """Create a test graph."""
    return GraphMemory()


@pytest.fixture
def config():
    """Create test configuration."""
    return NeuralMemoryConfig(
        learning_rate=0.1,
        decay_lambda=0.01,
        weight_max=2.0,
        top_m_edges=5,
    )


@pytest.fixture
def hebbian(graph, config):
    """Create Hebbian learner."""
    return HebbianLearner(graph, config)


@pytest.fixture
def test_nodes():
    """Create test nodes."""
    return {
        "node_a": NeuralMemoryNode(
            id="node_a",
            user_id="user1",
            kind=MemoryKind.FACT,
            text="test_a",
            embedding=[0.1],
            created_at=datetime.now(timezone.utc),
            confidence=0.9,
        ),
        "node_b": NeuralMemoryNode(
            id="node_b",
            user_id="user1",
            kind=MemoryKind.FACT,
            text="test_b",
            embedding=[0.2],
            created_at=datetime.now(timezone.utc),
            confidence=0.8,
        ),
    }


class TestHebbianLearner:
    """Test suite for HebbianLearner."""

    def test_initialization(self, hebbian, graph, config):
        """Test Hebbian learner initializes correctly."""
        assert hebbian.graph == graph
        assert hebbian.config == config
        assert len(hebbian._update_queue) == 0

    def test_queue_update(self, hebbian, test_nodes):
        """Test queuing Hebbian updates."""
        activations = [
            ActivationState(node_id="node_a", activation=0.8),
            ActivationState(node_id="node_b", activation=0.6),
        ]

        hebbian.queue_update("user1", activations, test_nodes)

        assert "user1" in hebbian._update_queue
        assert len(hebbian._update_queue["user1"]) > 0  # Bidirectional updates

    def test_calculate_delta_weight(self, hebbian):
        """Test Hebbian weight delta calculation."""
        delta_w = hebbian._calculate_delta_weight(
            activation_i=0.8,
            activation_j=0.6,
            confidence_i=0.9,
            confidence_j=0.8,
            current_weight=0.5,
        )

        # Should be: η·(a_i·C_i)·(a_j·C_j) - λ·w
        # = 0.1 * (0.8*0.9) * (0.6*0.8) - 0.01 * 0.5
        expected = 0.1 * (0.8 * 0.9) * (0.6 * 0.8) - 0.01 * 0.5
        assert abs(delta_w - expected) < 1e-6

    def test_get_current_weight_nonexistent(self, hebbian):
        """Test getting weight for nonexistent edge returns 0."""
        weight = hebbian._get_current_weight("user1", "node_a", "node_b")
        assert weight == 0.0

    def test_apply_updates_empty_queue(self, hebbian):
        """Test applying updates with empty queue."""
        count = hebbian.apply_updates("user1")
        assert count == 0

    def test_gradient_clipping(self, hebbian):
        """Test gradient clipping works."""
        # Create large updates that should be clipped
        edge_deltas = {
            ("node_a", "node_b"): 1.0,
            ("node_a", "node_c"): 1.0,
            ("node_a", "node_d"): 1.0,
        }

        clipped = hebbian._clip_gradients(edge_deltas)

        # Total delta for node_a is 3.0, should be clipped to config.gradient_clipping (0.5)
        total_clipped = sum(abs(v) for (src, _), v in clipped.items() if src == "node_a")
        assert total_clipped <= hebbian.config.gradient_clipping
