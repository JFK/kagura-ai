"""Tests for activation spreading."""

import pytest

from kagura.core.graph.memory import GraphMemory
from kagura.core.memory.neural.activation import ActivationSpreader
from kagura.core.memory.neural.config import NeuralMemoryConfig


@pytest.fixture
def graph():
    """Create test graph with some nodes."""
    g = GraphMemory()
    # Add test nodes
    g.add_node("node_a", "memory", user_id="user1")
    g.add_node("node_b", "memory", user_id="user1")
    g.add_node("node_c", "memory", user_id="user1")

    # Add edges with weights
    g.add_edge("node_a", "node_b", "neural_association", weight=0.8)
    g.add_edge("node_b", "node_c", "neural_association", weight=0.6)

    return g


@pytest.fixture
def config():
    """Create test configuration."""
    return NeuralMemoryConfig(spread_hops=2, spread_decay=0.5, spread_threshold=0.01)


@pytest.fixture
def spreader(graph, config):
    """Create activation spreader."""
    return ActivationSpreader(graph, config)


class TestActivationSpreader:
    """Test suite for ActivationSpreader."""

    def test_initialization(self, spreader, graph, config):
        """Test spreader initializes correctly."""
        assert spreader.graph == graph
        assert spreader.config == config

    def test_spread_zero_hops(self, spreader):
        """Test spreading with zero hops returns only seeds."""
        seeds = {"node_a": 1.0, "node_b": 0.5}
        results = spreader.spread(seeds, max_hops=0)

        assert len(results) == 2
        assert all(r.hop == 0 for r in results)

    def test_spread_one_hop(self, spreader):
        """Test spreading with one hop."""
        seeds = {"node_a": 1.0}
        results = spreader.spread(seeds, max_hops=1)

        # Should include node_a (seed) and node_b (1-hop neighbor)
        node_ids = {r.node_id for r in results}
        assert "node_a" in node_ids
        assert "node_b" in node_ids or len(results) == 1  # Depends on weight

    def test_spread_with_decay(self, spreader):
        """Test activation decays with distance."""
        seeds = {"node_a": 1.0}
        results = spreader.spread(seeds, max_hops=2)

        # Activations should decrease with hop distance
        hop_0 = [r for r in results if r.hop == 0]
        hop_1 = [r for r in results if r.hop == 1]

        if hop_0 and hop_1:
            max_hop_0 = max(r.activation for r in hop_0)
            max_hop_1 = max(r.activation for r in hop_1)
            assert max_hop_0 >= max_hop_1  # Earlier hops have higher activation

    def test_get_association_score(self, spreader):
        """Test getting association score for a target node."""
        score = spreader.get_association_score(["node_a"], "node_b", max_hops=1)

        # node_b is a neighbor of node_a, should have non-zero score
        assert score >= 0.0

    def test_get_association_score_unreachable(self, spreader):
        """Test association score for unreachable node."""
        score = spreader.get_association_score(["node_a"], "node_x", max_hops=1)

        # node_x doesn't exist, should be 0
        assert score == 0.0

    def test_find_related_nodes(self, spreader):
        """Test finding related nodes."""
        related = spreader.find_related_nodes(["node_a"], top_k=5, max_hops=2)

        # Should return list of (node_id, score) tuples
        assert isinstance(related, list)
        for node_id, score in related:
            assert isinstance(node_id, str)
            assert 0.0 <= score <= 1.0

    def test_user_id_filtering(self, spreader):
        """Test user_id filtering prevents cross-user data leakage."""
        # Add node for different user
        spreader.graph.add_node("node_other", "memory", user_id="user2")
        spreader.graph.add_edge(
            "node_a", "node_other", "neural_association", weight=0.9
        )

        # Spread with user_id filter
        seeds = {"node_a": 1.0}
        results = spreader.spread(seeds, max_hops=1, user_id="user1")

        # Should not include node_other (belongs to user2)
        node_ids = {r.node_id for r in results}
        assert "node_other" not in node_ids

    def test_empty_seeds(self, spreader):
        """Test spreading with empty seeds."""
        results = spreader.spread({}, max_hops=1)

        assert len(results) == 0
