"""Tests for GraphMemory (NetworkX-based knowledge graph).

Issue #345: GraphDB integration for AI-User relationship memory
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from kagura.core.graph import GraphMemory


@pytest.fixture
def graph_memory() -> GraphMemory:
    """Create a fresh GraphMemory instance for testing."""
    return GraphMemory()


@pytest.fixture
def graph_with_data() -> GraphMemory:
    """Create GraphMemory with sample data."""
    graph = GraphMemory()

    # Add nodes
    graph.add_node("mem_001", "memory", {"key": "python_tips"})
    graph.add_node("mem_002", "memory", {"key": "fastapi_guide"})
    graph.add_node("topic_python", "topic", {"name": "Python"})
    graph.add_node("topic_webdev", "topic", {"name": "Web Development"})
    graph.add_node("user_001", "user", {"user_id": "jfk"})

    # Add edges
    graph.add_edge("mem_001", "topic_python", "related_to", weight=0.9)
    graph.add_edge("mem_002", "topic_python", "related_to", weight=0.7)
    graph.add_edge("mem_002", "topic_webdev", "related_to", weight=0.8)

    return graph


class TestGraphMemoryBasics:
    """Test basic GraphMemory operations."""

    def test_init_empty(self, graph_memory: GraphMemory) -> None:
        """Test initialization creates empty graph."""
        assert graph_memory.graph.number_of_nodes() == 0
        assert graph_memory.graph.number_of_edges() == 0
        assert graph_memory.persist_path is None

    def test_init_with_persist_path(self) -> None:
        """Test initialization with persist path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persist_path = Path(tmpdir) / "graph.pkl"
            graph = GraphMemory(persist_path=persist_path)
            assert graph.persist_path == persist_path

    def test_add_node_valid(self, graph_memory: GraphMemory) -> None:
        """Test adding valid nodes."""
        graph_memory.add_node("node_001", "memory", {"key": "test"})

        assert graph_memory.graph.has_node("node_001")
        node_data = graph_memory.graph.nodes["node_001"]
        assert node_data["type"] == "memory"
        assert node_data["key"] == "test"
        assert "created_at" in node_data

    def test_add_node_invalid_type(self, graph_memory: GraphMemory) -> None:
        """Test adding node with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid node_type"):
            graph_memory.add_node("node_001", "invalid_type")

    def test_add_node_all_types(self, graph_memory: GraphMemory) -> None:
        """Test adding all valid node types."""
        for node_type in GraphMemory.NODE_TYPES:
            graph_memory.add_node(f"node_{node_type}", node_type)
            assert graph_memory.graph.has_node(f"node_{node_type}")
            assert graph_memory.graph.nodes[f"node_{node_type}"]["type"] == node_type

    def test_add_edge_valid(self, graph_memory: GraphMemory) -> None:
        """Test adding valid edges."""
        graph_memory.add_node("src", "memory")
        graph_memory.add_node("dst", "topic")
        graph_memory.add_edge("src", "dst", "related_to", weight=0.8)

        assert graph_memory.graph.has_edge("src", "dst")
        edge_data = graph_memory.graph.edges["src", "dst"]
        assert edge_data["type"] == "related_to"
        assert edge_data["weight"] == 0.8
        assert "created_at" in edge_data

    def test_add_edge_invalid_type(self, graph_memory: GraphMemory) -> None:
        """Test adding edge with invalid type raises ValueError."""
        graph_memory.add_node("src", "memory")
        graph_memory.add_node("dst", "topic")

        with pytest.raises(ValueError, match="Invalid rel_type"):
            graph_memory.add_edge("src", "dst", "invalid_rel")

    def test_add_edge_missing_nodes(self, graph_memory: GraphMemory) -> None:
        """Test adding edge with missing nodes raises ValueError."""
        with pytest.raises(ValueError, match="Source node .* does not exist"):
            graph_memory.add_edge("missing_src", "dst", "related_to")

        graph_memory.add_node("src", "memory")
        with pytest.raises(ValueError, match="Destination node .* does not exist"):
            graph_memory.add_edge("src", "missing_dst", "related_to")

    def test_add_edge_all_types(self, graph_memory: GraphMemory) -> None:
        """Test adding all valid edge types."""
        graph_memory.add_node("src", "memory")
        graph_memory.add_node("dst", "topic")

        for i, edge_type in enumerate(GraphMemory.EDGE_TYPES):
            # Create unique dst for each edge
            dst_id = f"dst_{i}"
            graph_memory.add_node(dst_id, "topic")
            graph_memory.add_edge("src", dst_id, edge_type)
            assert graph_memory.graph.edges["src", dst_id]["type"] == edge_type


class TestGraphQuery:
    """Test graph querying operations."""

    def test_query_graph_basic(self, graph_with_data: GraphMemory) -> None:
        """Test basic graph query."""
        result = graph_with_data.query_graph(["mem_001"], hops=1)

        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) > 0

        # Should include mem_001 and its neighbors
        node_ids = {node["id"] for node in result["nodes"]}
        assert "mem_001" in node_ids
        assert "topic_python" in node_ids

    def test_query_graph_multi_hop(self, graph_with_data: GraphMemory) -> None:
        """Test multi-hop graph query."""
        result = graph_with_data.query_graph(["mem_001"], hops=2)

        node_ids = {node["id"] for node in result["nodes"]}
        # Should reach mem_002 through topic_python
        assert "mem_002" in node_ids

    def test_query_graph_with_filter(self, graph_with_data: GraphMemory) -> None:
        """Test graph query with relationship filter."""
        result = graph_with_data.query_graph(
            ["mem_001"], hops=1, rel_filters=["related_to"]
        )

        # Should only follow "related_to" edges
        edge_types = {edge["type"] for edge in result["edges"]}
        assert edge_types == {"related_to"}

    def test_query_graph_nonexistent_node(self, graph_with_data: GraphMemory) -> None:
        """Test query with non-existent node."""
        result = graph_with_data.query_graph(["nonexistent"], hops=1)

        # Should return empty result
        assert len(result["nodes"]) == 0
        assert len(result["edges"]) == 0

    def test_get_related(self, graph_with_data: GraphMemory) -> None:
        """Test get_related method."""
        related = graph_with_data.get_related("mem_001", depth=2)

        # Should not include the seed node itself
        node_ids = {node["id"] for node in related}
        assert "mem_001" not in node_ids

        # Should include neighbors
        assert "topic_python" in node_ids

    def test_get_related_with_filter(self, graph_with_data: GraphMemory) -> None:
        """Test get_related with relationship filter."""
        related = graph_with_data.get_related("mem_001", depth=1, rel_type="related_to")

        assert len(related) > 0

    def test_get_related_nonexistent(self, graph_memory: GraphMemory) -> None:
        """Test get_related with non-existent node."""
        related = graph_memory.get_related("nonexistent")
        assert related == []


class TestInteractionRecording:
    """Test AI-User interaction recording."""

    def test_record_interaction(self, graph_memory: GraphMemory) -> None:
        """Test recording a basic interaction."""
        interaction_id = graph_memory.record_interaction(
            user_id="user_001",
            query="How to use FastAPI?",
            response="FastAPI is a modern web framework...",
            metadata={"ai_platform": "claude"},
        )

        # Check interaction node created
        assert graph_memory.graph.has_node(interaction_id)
        interaction_data = graph_memory.graph.nodes[interaction_id]
        assert interaction_data["type"] == "interaction"
        assert interaction_data["user_id"] == "user_001"
        assert interaction_data["ai_platform"] == "claude"
        assert interaction_data["query"] == "How to use FastAPI?"
        assert "timestamp" in interaction_data

        # Check user node created
        assert graph_memory.graph.has_node("user_001")

        # Check edge created
        assert graph_memory.graph.has_edge(interaction_id, "user_001")
        edge_data = graph_memory.graph.edges[interaction_id, "user_001"]
        assert edge_data["type"] == "learned_from"

    def test_record_interaction_with_metadata(self, graph_memory: GraphMemory) -> None:
        """Test recording interaction with metadata."""
        metadata = {"project": "kagura", "session_id": "sess_123", "ai_platform": "chatgpt"}
        interaction_id = graph_memory.record_interaction(
            user_id="user_002",
            query="Test query",
            response="Test response",
            metadata=metadata,
        )

        interaction_data = graph_memory.graph.nodes[interaction_id]
        assert interaction_data["project"] == "kagura"
        assert interaction_data["session_id"] == "sess_123"

    def test_record_multiple_interactions(self, graph_memory: GraphMemory) -> None:
        """Test recording multiple interactions for same user."""
        interaction_1 = graph_memory.record_interaction(
            user_id="user_001",
            query="Query 1",
            response="Response 1",
        )

        interaction_2 = graph_memory.record_interaction(
            user_id="user_001",
            query="Query 2",
            response="Response 2",
            metadata={"ai_platform": "claude"},
        )

        # Both interactions should be linked to same user
        assert graph_memory.graph.has_edge(interaction_1, "user_001")
        assert graph_memory.graph.has_edge(interaction_2, "user_001")


class TestUserPattern:
    """Test user pattern analysis."""

    def test_get_user_topics(self, graph_memory: GraphMemory) -> None:
        """Test getting user topics."""
        # Create user and interactions
        user_id = "user_001"
        interaction_id = graph_memory.record_interaction(
            user_id=user_id,
            query="Python question",
            response="Python answer",
            metadata={"ai_platform": "claude"},
        )

        # Create topic and link to interaction
        graph_memory.add_node("topic_python", "topic", {"name": "Python"})
        graph_memory.add_edge(interaction_id, "topic_python", "related_to")

        topics = graph_memory.get_user_topics(user_id)
        assert len(topics) > 0
        topic_ids = {t["id"] for t in topics}
        assert "topic_python" in topic_ids

    def test_get_user_topics_nonexistent(self, graph_memory: GraphMemory) -> None:
        """Test get_user_topics with non-existent user."""
        topics = graph_memory.get_user_topics("nonexistent_user")
        assert topics == []

    def test_get_user_interactions(self, graph_memory: GraphMemory) -> None:
        """Test getting user interactions."""
        user_id = "user_001"

        # Record multiple interactions
        interaction_1 = graph_memory.record_interaction(
            user_id=user_id,
            query="Query 1",
            response="Response 1",
            metadata={"ai_platform": "claude"},
        )

        interaction_2 = graph_memory.record_interaction(
            user_id=user_id,
            query="Query 2",
            response="Response 2",
            metadata={"ai_platform": "claude"},
        )

        interactions = graph_memory.get_user_interactions(user_id)
        assert len(interactions) == 2

        interaction_ids = {i["id"] for i in interactions}
        assert interaction_1 in interaction_ids
        assert interaction_2 in interaction_ids

    def test_get_user_interactions_with_limit(self, graph_memory: GraphMemory) -> None:
        """Test getting user interactions with limit."""
        user_id = "user_001"

        # Record 5 interactions
        for i in range(5):
            graph_memory.record_interaction(
                user_id=user_id,
                query=f"Query {i}",
                response=f"Response {i}",
                metadata={"ai_platform": "claude"},
            )

        interactions = graph_memory.get_user_interactions(user_id, limit=3)
        assert len(interactions) == 3

    def test_get_user_interactions_sorted(self, graph_memory: GraphMemory) -> None:
        """Test user interactions are sorted by timestamp."""
        user_id = "user_001"

        # Record interactions
        for i in range(3):
            graph_memory.record_interaction(
                user_id=user_id,
                query=f"Query {i}",
                response=f"Response {i}",
                metadata={"ai_platform": "claude"},
            )

        interactions = graph_memory.get_user_interactions(user_id)

        # Should be sorted by timestamp (newest first)
        timestamps = [i["timestamp"] for i in interactions]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_analyze_user_pattern_basic(self, graph_memory: GraphMemory) -> None:
        """Test basic user pattern analysis."""
        user_id = "user_001"

        # Record interactions
        interaction_1 = graph_memory.record_interaction(
            user_id=user_id,
            query="Python question",
            response="Python answer",
            metadata={"ai_platform": "claude"},
        )

        interaction_2 = graph_memory.record_interaction(
            user_id=user_id,
            query="JavaScript question",
            response="JavaScript answer",
            metadata={"ai_platform": "chatgpt"},
        )

        # Add topics
        graph_memory.add_node("topic_python", "topic", {"name": "Python"})
        graph_memory.add_node("topic_js", "topic", {"name": "JavaScript"})
        graph_memory.add_edge(interaction_1, "topic_python", "related_to")
        graph_memory.add_edge(interaction_2, "topic_js", "related_to")

        pattern = graph_memory.analyze_user_pattern(user_id)

        assert pattern["total_interactions"] == 2
        assert len(pattern["topics"]) == 2
        assert "topic_python" in pattern["topics"]
        assert "topic_js" in pattern["topics"]
        assert pattern["platforms"] == {"claude": 1, "chatgpt": 1}
        assert pattern["avg_interactions_per_topic"] == 1.0

    def test_analyze_user_pattern_most_discussed(
        self, graph_memory: GraphMemory
    ) -> None:
        """Test most discussed topic detection."""
        user_id = "user_001"

        # Create 3 Python interactions
        for i in range(3):
            interaction_id = graph_memory.record_interaction(
                user_id=user_id,
                query=f"Python question {i}",
                response=f"Python answer {i}",
                metadata={"ai_platform": "claude"},
            )
            if i == 0:
                graph_memory.add_node("topic_python", "topic", {"name": "Python"})
            graph_memory.add_edge(interaction_id, "topic_python", "related_to")

        # Create 1 JavaScript interaction
        interaction_id = graph_memory.record_interaction(
            user_id=user_id,
            query="JS question",
            response="JS answer",
            metadata={"ai_platform": "claude"},
        )
        graph_memory.add_node("topic_js", "topic", {"name": "JavaScript"})
        graph_memory.add_edge(interaction_id, "topic_js", "related_to")

        pattern = graph_memory.analyze_user_pattern(user_id)

        assert pattern["most_discussed_topic"] == "topic_python"

    def test_analyze_user_pattern_nonexistent(self, graph_memory: GraphMemory) -> None:
        """Test pattern analysis for non-existent user."""
        pattern = graph_memory.analyze_user_pattern("nonexistent_user")

        assert pattern["total_interactions"] == 0
        assert pattern["topics"] == []
        assert pattern["avg_interactions_per_topic"] == 0.0
        assert pattern["most_discussed_topic"] is None
        assert pattern["platforms"] == {}


class TestNodeEdgeAccess:
    """Test node and edge access methods."""

    def test_get_node(self, graph_with_data: GraphMemory) -> None:
        """Test getting node data."""
        node = graph_with_data.get_node("mem_001")

        assert node is not None
        assert node["id"] == "mem_001"
        assert node["type"] == "memory"
        assert node["key"] == "python_tips"

    def test_get_node_nonexistent(self, graph_memory: GraphMemory) -> None:
        """Test getting non-existent node."""
        node = graph_memory.get_node("nonexistent")
        assert node is None

    def test_get_edge(self, graph_with_data: GraphMemory) -> None:
        """Test getting edge data."""
        edge = graph_with_data.get_edge("mem_001", "topic_python")

        assert edge is not None
        assert edge["src"] == "mem_001"
        assert edge["dst"] == "topic_python"
        assert edge["type"] == "related_to"
        assert edge["weight"] == 0.9

    def test_get_edge_nonexistent(self, graph_memory: GraphMemory) -> None:
        """Test getting non-existent edge."""
        edge = graph_memory.get_edge("src", "dst")
        assert edge is None


class TestPersistence:
    """Test graph persistence (save/load)."""

    def test_persist_and_load(self, graph_with_data: GraphMemory) -> None:
        """Test saving and loading graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persist_path = Path(tmpdir) / "graph.pkl"
            graph_with_data.persist_path = persist_path

            # Save graph
            graph_with_data.persist()
            assert persist_path.exists()

            # Load into new instance
            loaded_graph = GraphMemory(persist_path=persist_path)
            assert (
                loaded_graph.graph.number_of_nodes()
                == graph_with_data.graph.number_of_nodes()
            )
            assert (
                loaded_graph.graph.number_of_edges()
                == graph_with_data.graph.number_of_edges()
            )

            # Verify data integrity
            assert loaded_graph.graph.has_node("mem_001")
            assert loaded_graph.graph.has_edge("mem_001", "topic_python")

    def test_persist_no_path(self, graph_memory: GraphMemory) -> None:
        """Test persist without path raises error."""
        with pytest.raises(ValueError, match="persist_path not set"):
            graph_memory.persist()

    def test_load_no_path(self) -> None:
        """Test load without path raises error."""
        graph = GraphMemory()
        with pytest.raises(ValueError, match="persist_path not set"):
            graph.load()

    def test_load_nonexistent_file(self) -> None:
        """Test load non-existent file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persist_path = Path(tmpdir) / "nonexistent.pkl"
            graph = GraphMemory(persist_path=persist_path)
            with pytest.raises(FileNotFoundError):
                graph.load()

    def test_auto_load_on_init(self) -> None:
        """Test graph auto-loads if persist_path exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persist_path = Path(tmpdir) / "graph.pkl"

            # Create and save graph
            graph1 = GraphMemory(persist_path=persist_path)
            graph1.add_node("node_001", "memory")
            graph1.persist()

            # Create new instance with same path - should auto-load
            graph2 = GraphMemory(persist_path=persist_path)
            assert graph2.graph.has_node("node_001")


class TestStats:
    """Test graph statistics."""

    def test_stats_empty(self, graph_memory: GraphMemory) -> None:
        """Test stats for empty graph."""
        stats = graph_memory.stats()

        assert stats["total_nodes"] == 0
        assert stats["total_edges"] == 0
        assert stats["node_counts"] == {}
        assert stats["edge_counts"] == {}
        assert stats["is_connected"] is False

    def test_stats_with_data(self, graph_with_data: GraphMemory) -> None:
        """Test stats with data."""
        stats = graph_with_data.stats()

        assert stats["total_nodes"] == 5
        assert stats["total_edges"] == 3
        assert stats["node_counts"]["memory"] == 2
        assert stats["node_counts"]["topic"] == 2
        assert stats["node_counts"]["user"] == 1
        assert stats["edge_counts"]["related_to"] == 3

    def test_repr(self, graph_with_data: GraphMemory) -> None:
        """Test string representation."""
        repr_str = repr(graph_with_data)

        assert "GraphMemory" in repr_str
        assert "nodes=5" in repr_str
        assert "edges=3" in repr_str


class TestClear:
    """Test graph clearing."""

    def test_clear(self, graph_with_data: GraphMemory) -> None:
        """Test clearing graph."""
        assert graph_with_data.graph.number_of_nodes() > 0
        assert graph_with_data.graph.number_of_edges() > 0

        graph_with_data.clear()

        assert graph_with_data.graph.number_of_nodes() == 0
        assert graph_with_data.graph.number_of_edges() == 0


class TestTemporalGraphMemory:
    """Tests for temporal graph features (v4.0.0a0 Phase 3)."""

    def test_add_edge_with_temporal_attributes(
        self, graph_memory: GraphMemory
    ) -> None:
        """Test adding edge with temporal validity."""
        graph_memory.add_node("person_kiyota", "user")
        graph_memory.add_node("company_snapdish", "topic")

        now = datetime.now()
        graph_memory.add_edge(
            "person_kiyota",
            "company_snapdish",
            "works_on",
            valid_from=now - timedelta(days=365),
            valid_until=None,
            source="https://snapdish.co",
            confidence=1.0,
        )

        edge = graph_memory.get_edge("person_kiyota", "company_snapdish")
        assert edge is not None
        assert "valid_from" in edge
        assert "valid_until" in edge
        assert edge["valid_until"] is None
        assert edge["source"] == "https://snapdish.co"
        assert edge["confidence"] == 1.0

    def test_is_edge_valid_at_current(self, graph_memory: GraphMemory) -> None:
        """Test checking edge validity at current time."""
        graph_memory.add_node("node_a", "memory")
        graph_memory.add_node("node_b", "memory")

        now = datetime.now()
        graph_memory.add_edge(
            "node_a",
            "node_b",
            "related_to",
            valid_from=now - timedelta(days=10),
            valid_until=None,
        )

        assert graph_memory.is_edge_valid_at("node_a", "node_b") is True

    def test_is_edge_valid_at_past(self, graph_memory: GraphMemory) -> None:
        """Test checking edge validity at past timestamp."""
        graph_memory.add_node("node_a", "memory")
        graph_memory.add_node("node_b", "memory")

        now = datetime.now()
        graph_memory.add_edge(
            "node_a",
            "node_b",
            "related_to",
            valid_from=now - timedelta(days=10),
            valid_until=now - timedelta(days=5),
        )

        # Not valid now (expired 5 days ago)
        assert graph_memory.is_edge_valid_at("node_a", "node_b") is False

        # Valid 7 days ago
        past = now - timedelta(days=7)
        assert graph_memory.is_edge_valid_at("node_a", "node_b", past) is True

    def test_invalidate_edge(self, graph_memory: GraphMemory) -> None:
        """Test invalidating an edge."""
        graph_memory.add_node("person_kiyota", "user")
        graph_memory.add_node("company_old", "topic")

        graph_memory.add_edge("person_kiyota", "company_old", "works_on")

        # Valid initially
        assert graph_memory.is_edge_valid_at("person_kiyota", "company_old") is True

        # Invalidate
        graph_memory.invalidate_edge("person_kiyota", "company_old")

        # Now invalid
        assert graph_memory.is_edge_valid_at("person_kiyota", "company_old") is False

    def test_query_graph_temporal_filters_invalid(
        self, graph_memory: GraphMemory
    ) -> None:
        """Test temporal query filters out invalid edges."""
        graph_memory.add_node("node_a", "memory")
        graph_memory.add_node("node_b", "memory")
        graph_memory.add_node("node_c", "memory")

        now = datetime.now()

        # Valid edge
        graph_memory.add_edge(
            "node_a", "node_b", "related_to", valid_until=None
        )

        # Invalid edge (expired)
        graph_memory.add_edge(
            "node_b",
            "node_c",
            "related_to",
            valid_until=now - timedelta(days=5),
        )

        result = graph_memory.query_graph_temporal(["node_a"], hops=2)

        node_ids = {n["id"] for n in result["nodes"]}
        assert "node_a" in node_ids
        assert "node_b" in node_ids
        assert "node_c" not in node_ids  # Filtered out

    def test_temporal_contradiction_handling(self, graph_memory: GraphMemory) -> None:
        """Test handling contradictory information over time."""
        graph_memory.add_node("person_kiyota", "user")
        graph_memory.add_node("company_old", "topic")
        graph_memory.add_node("company_snapdish", "topic")

        # Old relationship
        graph_memory.add_edge("person_kiyota", "company_old", "works_on")

        # New information contradicts old - invalidate
        graph_memory.invalidate_edge("person_kiyota", "company_old")

        # Add new relationship
        graph_memory.add_edge("person_kiyota", "company_snapdish", "works_on")

        # Current query should only show new relationship
        result = graph_memory.query_graph_temporal(
            ["person_kiyota"], hops=1, rel_filters=["works_on"]
        )

        node_ids = {n["id"] for n in result["nodes"]}
        assert "company_snapdish" in node_ids
        assert "company_old" not in node_ids
