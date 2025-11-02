"""Tests for NeuralMemoryEngine integration."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from kagura.core.memory.neural.config import NeuralMemoryConfig
from kagura.core.memory.neural.engine import NeuralMemoryEngine
from kagura.core.memory.neural.models import MemoryKind, SourceKind


@pytest.fixture
def mock_graph():
    """Create mock graph."""
    graph = MagicMock()
    graph.graph = MagicMock()
    graph.graph.nodes = {}
    graph.graph.edges = MagicMock(return_value=[])
    return graph


@pytest.fixture
def mock_rag():
    """Create mock RAG."""
    rag = MagicMock()
    rag.recall = AsyncMock(return_value=[])
    rag.store = AsyncMock(return_value="test_hash")
    return rag


@pytest.fixture
def config():
    """Create test configuration."""
    return NeuralMemoryConfig()


@pytest.fixture
def engine(mock_graph, mock_rag, config):
    """Create neural memory engine."""
    return NeuralMemoryEngine(mock_graph, mock_rag, config)


class TestNeuralMemoryEngine:
    """Test suite for NeuralMemoryEngine."""

    def test_initialization(self, engine, mock_graph, mock_rag, config):
        """Test engine initializes correctly."""
        assert engine.graph == mock_graph
        assert engine.rag == mock_rag
        assert engine.config == config
        assert engine.activation_spreader is not None
        assert engine.hebbian_learner is not None
        assert engine.co_activation_tracker is not None
        assert engine.decay_manager is not None
        assert engine.scorer is not None

    @pytest.mark.asyncio
    async def test_recall_empty_results(self, engine, mock_rag):
        """Test recall with no RAG results."""
        mock_rag.recall = AsyncMock(return_value=[])

        results = await engine.recall("user1", "test query")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_store(self, engine, mock_graph, mock_rag):
        """Test storing a memory."""
        # Mock embedding function
        with patch.object(engine, "_get_embedding", return_value=[0.1] * 1024):
            node_id = await engine.store(
                user_id="user1",
                text="Python is great",
                kind=MemoryKind.FACT,
                source=SourceKind.USER,
            )

        assert node_id.startswith("neural_")
        mock_graph.add_node.assert_called_once()
        mock_rag.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_forget(self, engine, mock_graph):
        """Test forgetting a memory (GDPR compliance)."""
        mock_graph.graph.remove_node = Mock()

        result = await engine.forget("user1", "node_123")

        # Should attempt to remove node
        mock_graph.graph.remove_node.assert_called_once_with("node_123")

    @pytest.mark.asyncio
    async def test_consolidate(self, engine, mock_graph):
        """Test consolidation process."""
        # Mock nodes
        mock_graph.graph.nodes = MagicMock()
        mock_graph.graph.nodes.return_value = [
            ("node_a", {"user_id": "user1", "use_count": 5, "importance": 0.8})
        ]

        with patch.object(engine.decay_manager, "consolidate_to_long_term", return_value=[]):
            with patch.object(
                engine.decay_manager,
                "apply_decay",
                return_value={"edges_decayed": 10, "edges_pruned": 2},
            ):
                stats = await engine.consolidate("user1")

        assert "promoted_nodes" in stats
        assert "edges_decayed" in stats
        assert "edges_pruned" in stats

    @pytest.mark.asyncio
    async def test_start_background_decay(self, engine):
        """Test starting background decay task."""
        engine.start_background_decay()

        assert engine._decay_task is not None

        # Clean up
        engine.stop_background_decay()

    @pytest.mark.asyncio
    async def test_stop_background_decay(self, engine):
        """Test stopping background decay task."""
        import asyncio

        engine.start_background_decay()
        await asyncio.sleep(0.01)  # Let task start
        engine.stop_background_decay()
        await asyncio.sleep(0.01)  # Let cancellation process

        # Task should be done (cancelled or finished)
        assert engine._decay_task.done() or engine._decay_task.cancelled()


class TestNeuralMemoryEngineIntegration:
    """Integration tests with real components (light mocking)."""

    @pytest.mark.asyncio
    async def test_update_node_usage(self, engine, mock_graph):
        """Test node usage statistics update."""
        from kagura.core.memory.neural.models import NeuralMemoryNode

        node = NeuralMemoryNode(
            id="test_node",
            user_id="user1",
            kind=MemoryKind.FACT,
            text="test",
            embedding=[0.1],
            created_at=datetime.now(timezone.utc),
        )

        # Mock graph nodes
        mock_graph.graph.nodes = {"test_node": {"use_count": 0}}
        mock_graph.graph.has_node = Mock(return_value=True)

        await engine._update_node_usage("user1", node)

        # Should increment use_count
        assert mock_graph.graph.nodes["test_node"]["use_count"] == 1
