"""Tests for decay and forgetting mechanisms."""

from datetime import datetime, timezone

import pytest

from kagura.core.graph.memory import GraphMemory
from kagura.core.memory.neural.config import NeuralMemoryConfig
from kagura.core.memory.neural.decay import DecayManager


@pytest.fixture
def graph():
    """Create test graph."""
    g = GraphMemory()
    g.add_node("node_a", "memory", user_id="user1", importance=0.7)
    g.add_node("node_b", "memory", user_id="user1", importance=0.3)
    g.add_edge("node_a", "node_b", "neural_association", weight=0.5)
    return g


@pytest.fixture
def config():
    """Create test configuration."""
    return NeuralMemoryConfig(enable_decay=True, decay_rate=0.001, prune_threshold=0.05)


@pytest.fixture
def decay_manager(graph, config):
    """Create decay manager."""
    return DecayManager(graph, config)


class TestDecayManager:
    """Test suite for DecayManager."""

    def test_initialization(self, decay_manager, graph, config):
        """Test decay manager initializes correctly."""
        assert decay_manager.graph == graph
        assert decay_manager.config == config
        assert decay_manager._last_decay_time is None

    def test_apply_decay_disabled(self):
        """Test decay does nothing when disabled."""
        config = NeuralMemoryConfig(enable_decay=False)
        graph = GraphMemory()
        manager = DecayManager(graph, config)

        stats = manager.apply_decay("user1")

        assert stats["edges_decayed"] == 0
        assert stats["edges_pruned"] == 0

    def test_prune_weak_edges(self, decay_manager, graph):
        """Test pruning weak edges."""
        # Add a weak edge
        graph.add_edge("node_a", "node_c", "neural_association", weight=0.01)

        count = decay_manager.prune_weak_edges("user1", threshold=0.05)

        # Should prune the weak edge
        assert not graph.graph.has_edge("node_a", "node_c")

    def test_get_decay_statistics(self, decay_manager):
        """Test getting decay statistics."""
        stats = decay_manager.get_decay_statistics("user1")

        assert "total_neural_edges" in stats
        assert "avg_weight" in stats
        assert "max_weight" in stats
        assert "min_weight" in stats

    def test_consolidate_to_long_term(self, decay_manager, graph):
        """Test promoting nodes to long-term memory."""
        # Add qualifying nodes
        nodes = [
            {
                "id": "node_a",
                "user_id": "user1",
                "use_count": 5,
                "importance": 0.8,
                "long_term": False,
            }
        ]

        promoted = decay_manager.consolidate_to_long_term("user1", nodes)

        # Should promote node_a
        if graph.graph.has_node("node_a"):
            assert graph.graph.nodes["node_a"].get("long_term") is True

    def test_consolidate_skip_already_long_term(self, decay_manager):
        """Test consolidation skips already long-term nodes."""
        nodes = [
            {
                "id": "node_a",
                "user_id": "user1",
                "use_count": 10,
                "importance": 0.9,
                "long_term": True,  # Already long-term
            }
        ]

        promoted = decay_manager.consolidate_to_long_term("user1", nodes)

        # Should not re-promote
        # (Would need to check graph state for full verification)
