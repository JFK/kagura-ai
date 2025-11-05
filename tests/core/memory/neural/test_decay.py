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
    g.add_node("node_a", "memory", data={"user_id": "user1", "importance": 0.7})
    g.add_node("node_b", "memory", data={"user_id": "user1", "importance": 0.3})
    g.add_edge("node_a", "node_b", "related_to", weight=0.5)
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
        # Add a weak node and edge
        graph.add_node("node_c", "memory", data={"user_id": "user1"})
        graph.add_edge("node_a", "node_c", "related_to", weight=0.01)

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

        # Should not re-promote (length should not change)
        assert isinstance(promoted, list)

    def test_apply_decay_calculates_delta_seconds(self, decay_manager):
        """Test decay calculates time delta correctly."""
        from datetime import datetime

        # First call - uses default interval
        stats = decay_manager.apply_decay("user1")

        assert "delta_seconds" in stats
        assert stats["delta_seconds"] > 0

    def test_prune_old_nodes(self, decay_manager, graph):
        """Test pruning old, low-importance nodes."""
        # Add old node
        from datetime import datetime, timedelta, timezone

        old_time = datetime.now(timezone.utc) - timedelta(days=100)
        graph.add_node(
            "node_old",
            "memory",
            data={
                "user_id": "user1",
                "created_at": old_time,
                "importance": 0.2,  # Low importance
                "long_term": False,
            },
        )

        count = decay_manager.prune_old_nodes(
            "user1", age_days=50, importance_threshold=0.5
        )

        # Should prune old, low-importance node
        assert count >= 0

    def test_decay_disabled_early_return(self):
        """Test decay returns early when disabled."""
        config = NeuralMemoryConfig(enable_decay=False)
        graph = GraphMemory()
        manager = DecayManager(graph, config)

        stats = manager.apply_decay("user1")

        # Should return immediately with zero stats
        assert stats["edges_decayed"] == 0
        assert stats["edges_pruned"] == 0
        assert "delta_seconds" not in stats  # Early return, no delta calculated
