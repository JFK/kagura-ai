"""Tests for Neural Memory data models."""

from datetime import datetime, timezone

import pytest

from kagura.core.memory.neural.models import (
    ActivationState,
    CoActivationRecord,
    HebbianUpdate,
    MemoryKind,
    NeuralMemoryNode,
    RecallResult,
    SourceKind,
)


class TestNeuralMemoryNode:
    """Test suite for NeuralMemoryNode."""

    def test_valid_node_creation(self):
        """Test creating a valid memory node."""
        node = NeuralMemoryNode(
            id="test_001",
            user_id="user_123",
            kind=MemoryKind.FACT,
            text="Python is a programming language",
            embedding=[0.1, 0.2, 0.3],
            created_at=datetime.now(timezone.utc),
            importance=0.7,
            confidence=0.9,
            source=SourceKind.USER,
        )

        assert node.id == "test_001"
        assert node.user_id == "user_123"
        assert node.kind == MemoryKind.FACT
        assert node.importance == 0.7
        assert node.confidence == 0.9

    def test_importance_validation(self):
        """Test importance must be in [0, 1]."""
        with pytest.raises(ValueError, match="importance must be in"):
            NeuralMemoryNode(
                id="test",
                user_id="user",
                kind=MemoryKind.FACT,
                text="test",
                embedding=[0.1],
                created_at=datetime.now(timezone.utc),
                importance=1.5,  # Invalid
            )

        with pytest.raises(ValueError, match="importance must be in"):
            NeuralMemoryNode(
                id="test",
                user_id="user",
                kind=MemoryKind.FACT,
                text="test",
                embedding=[0.1],
                created_at=datetime.now(timezone.utc),
                importance=-0.1,  # Invalid
            )

    def test_confidence_validation(self):
        """Test confidence must be in [0, 1]."""
        with pytest.raises(ValueError, match="confidence must be in"):
            NeuralMemoryNode(
                id="test",
                user_id="user",
                kind=MemoryKind.FACT,
                text="test",
                embedding=[0.1],
                created_at=datetime.now(timezone.utc),
                confidence=2.0,  # Invalid
            )

    def test_use_count_validation(self):
        """Test use_count must be non-negative."""
        with pytest.raises(ValueError, match="use_count must be non-negative"):
            NeuralMemoryNode(
                id="test",
                user_id="user",
                kind=MemoryKind.FACT,
                text="test",
                embedding=[0.1],
                created_at=datetime.now(timezone.utc),
                use_count=-1,  # Invalid
            )

    def test_embedding_validation(self):
        """Test embedding must not be empty."""
        with pytest.raises(ValueError, match="embedding must not be empty"):
            NeuralMemoryNode(
                id="test",
                user_id="user",
                kind=MemoryKind.FACT,
                text="test",
                embedding=[],  # Invalid
                created_at=datetime.now(timezone.utc),
            )


class TestActivationState:
    """Test suite for ActivationState."""

    def test_valid_activation(self):
        """Test creating valid activation state."""
        state = ActivationState(node_id="node_001", activation=0.8, hop=1)

        assert state.node_id == "node_001"
        assert state.activation == 0.8
        assert state.hop == 1

    def test_activation_validation(self):
        """Test activation must be in [0, 1]."""
        with pytest.raises(ValueError, match="activation must be in"):
            ActivationState(node_id="node_001", activation=1.5)

        with pytest.raises(ValueError, match="activation must be in"):
            ActivationState(node_id="node_001", activation=-0.1)

    def test_hop_validation(self):
        """Test hop must be non-negative."""
        with pytest.raises(ValueError, match="hop must be non-negative"):
            ActivationState(node_id="node_001", activation=0.5, hop=-1)

    def test_default_values(self):
        """Test default values are set correctly."""
        state = ActivationState(node_id="node_001", activation=0.5)

        assert state.hop == 0
        assert state.source_node_id is None
        assert isinstance(state.timestamp, datetime)


class TestCoActivationRecord:
    """Test suite for CoActivationRecord."""

    def test_node_id_ordering(self):
        """Test node IDs are automatically ordered."""
        record = CoActivationRecord(node_id_1="node_b", node_id_2="node_a")

        # Should be swapped to maintain alphabetical order
        assert record.node_id_1 == "node_a"
        assert record.node_id_2 == "node_b"

    def test_update_method(self):
        """Test update() increments count and updates activation product."""
        record = CoActivationRecord(
            node_id_1="node_a", node_id_2="node_b", user_id="user_123"
        )

        initial_count = record.count
        record.update(0.8, 0.6)

        assert record.count == initial_count + 1
        assert record.total_activation_product > 0

    def test_average_activation_product(self):
        """Test average_activation_product property."""
        record = CoActivationRecord(
            node_id_1="node_a",
            node_id_2="node_b",
            total_activation_product=2.4,
            count=3,
            user_id="user_123",
        )

        assert record.average_activation_product == 0.8  # 2.4 / 3

    def test_average_activation_product_zero_count(self):
        """Test average_activation_product with zero count."""
        record = CoActivationRecord(
            node_id_1="node_a",
            node_id_2="node_b",
            total_activation_product=0.0,
            count=0,
            user_id="user_123",
        )

        assert record.average_activation_product == 0.0


class TestRecallResult:
    """Test suite for RecallResult."""

    def test_valid_result(self):
        """Test creating valid recall result."""
        node = NeuralMemoryNode(
            id="test",
            user_id="user",
            kind=MemoryKind.FACT,
            text="test",
            embedding=[0.1],
            created_at=datetime.now(timezone.utc),
        )

        result = RecallResult(
            node=node, score=0.85, components={"semantic": 0.9, "graph": 0.8}
        )

        assert result.node == node
        assert result.score == 0.85
        assert result.components["semantic"] == 0.9

    def test_score_validation(self):
        """Test score must be non-negative."""
        node = NeuralMemoryNode(
            id="test",
            user_id="user",
            kind=MemoryKind.FACT,
            text="test",
            embedding=[0.1],
            created_at=datetime.now(timezone.utc),
        )

        with pytest.raises(ValueError, match="score must be non-negative"):
            RecallResult(node=node, score=-0.1)


class TestHebbianUpdate:
    """Test suite for HebbianUpdate."""

    def test_valid_update(self):
        """Test creating valid Hebbian update."""
        update = HebbianUpdate(
            user_id="user_123",
            src_id="node_a",
            dst_id="node_b",
            delta_weight=0.05,
        )

        assert update.user_id == "user_123"
        assert update.src_id == "node_a"
        assert update.dst_id == "node_b"
        assert update.delta_weight == 0.05
        assert isinstance(update.timestamp, datetime)


class TestEnums:
    """Test suite for enum types."""

    def test_memory_kind_values(self):
        """Test MemoryKind enum values."""
        assert MemoryKind.FACT.value == "fact"
        assert MemoryKind.PREFERENCE.value == "preference"
        assert MemoryKind.TASK.value == "task"
        assert MemoryKind.DIALOGUE.value == "dialogue"
        assert MemoryKind.SUMMARY.value == "summary"
        assert MemoryKind.TOOL_LOG.value == "tool-log"

    def test_source_kind_values(self):
        """Test SourceKind enum values."""
        assert SourceKind.USER.value == "user"
        assert SourceKind.SYSTEM.value == "system"
        assert SourceKind.WEB.value == "web"
        assert SourceKind.FILE.value == "file"
        assert SourceKind.TOOL.value == "tool"
        assert SourceKind.LLM.value == "llm"
