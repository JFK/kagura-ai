"""Tests for GraphMemory backend implementations.

Issue #554 - Cloud-Native Infrastructure Migration
"""

import json
import os
import tempfile
from pathlib import Path

import networkx as nx
import pytest

from kagura.core.graph.backends import GraphBackend, JSONBackend


class TestGraphBackendInterface:
    """Test GraphBackend abstract interface compliance."""

    def test_json_backend_implements_interface(self):
        """JSONBackend should implement all GraphBackend methods."""
        backend = JSONBackend(persist_path=Path("/tmp/test.json"))

        assert isinstance(backend, GraphBackend)
        assert hasattr(backend, "save")
        assert hasattr(backend, "load")
        assert hasattr(backend, "exists")
        assert hasattr(backend, "delete")
        assert hasattr(backend, "close")


class TestJSONBackend:
    """Test JSONBackend implementation."""

    @pytest.fixture
    def temp_json_file(self):
        """Create temporary JSON file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def sample_graph(self):
        """Create sample graph for testing."""
        graph = nx.DiGraph()
        graph.add_node("node1", type="memory", key="test_key")
        graph.add_node("node2", type="topic", name="test_topic")
        graph.add_edge("node1", "node2", type="related_to", weight=0.8)
        return graph

    def test_save_and_load(self, temp_json_file, sample_graph):
        """Test save and load operations."""
        backend = JSONBackend(persist_path=temp_json_file)

        # Save graph
        backend.save(sample_graph)

        assert temp_json_file.exists()

        # Load graph
        loaded_graph = backend.load()

        assert loaded_graph.number_of_nodes() == sample_graph.number_of_nodes()
        assert loaded_graph.number_of_edges() == sample_graph.number_of_edges()
        assert list(loaded_graph.nodes()) == list(sample_graph.nodes())

        # Check node attributes
        assert loaded_graph.nodes["node1"]["type"] == "memory"
        assert loaded_graph.nodes["node2"]["type"] == "topic"

        # Check edge attributes
        assert loaded_graph.edges["node1", "node2"]["type"] == "related_to"
        assert loaded_graph.edges["node1", "node2"]["weight"] == 0.8

    def test_load_nonexistent_returns_empty(self, temp_json_file):
        """Loading non-existent file should return empty graph."""
        backend = JSONBackend(persist_path=temp_json_file)

        # File doesn't exist yet
        assert not backend.exists()

        # Load should return empty graph
        loaded_graph = backend.load()
        assert isinstance(loaded_graph, nx.DiGraph)
        assert loaded_graph.number_of_nodes() == 0
        assert loaded_graph.number_of_edges() == 0

    def test_exists(self, temp_json_file, sample_graph):
        """Test exists() method."""
        backend = JSONBackend(persist_path=temp_json_file)

        # Initially doesn't exist
        assert not backend.exists()

        # After save, should exist
        backend.save(sample_graph)
        assert backend.exists()

    def test_delete(self, temp_json_file, sample_graph):
        """Test delete() method."""
        backend = JSONBackend(persist_path=temp_json_file)

        # Save graph
        backend.save(sample_graph)
        assert backend.exists()

        # Delete
        backend.delete()
        assert not backend.exists()

    def test_close(self, temp_json_file):
        """Test close() method (no-op for JSON backend)."""
        backend = JSONBackend(persist_path=temp_json_file)
        backend.close()  # Should not raise

    def test_save_creates_parent_directory(self, sample_graph):
        """Save should create parent directory if it doesn't exist."""
        temp_dir = Path(tempfile.mkdtemp())
        temp_file = temp_dir / "subdir" / "graph.json"

        try:
            backend = JSONBackend(persist_path=temp_file)
            backend.save(sample_graph)

            assert temp_file.exists()
            assert temp_file.parent.exists()

        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
            if temp_file.parent.exists():
                temp_file.parent.rmdir()
            if temp_dir.exists():
                temp_dir.rmdir()


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set (PostgreSQL tests require database)",
)
class TestPostgresBackend:
    """Test PostgresBackend implementation.

    Note: These tests require a PostgreSQL database.
    Set TEST_DATABASE_URL environment variable to run.

    Example:
        export TEST_DATABASE_URL=postgresql://localhost:5432/kagura_test
        pytest tests/graph/test_backends.py::TestPostgresBackend
    """

    @pytest.fixture
    def database_url(self):
        """Get test database URL from environment."""
        return os.getenv("TEST_DATABASE_URL")

    @pytest.fixture
    def sample_graph(self):
        """Create sample graph for testing."""
        graph = nx.DiGraph()
        graph.add_node("node1", type="memory", key="test_key")
        graph.add_node("node2", type="topic", name="test_topic")
        graph.add_edge("node1", "node2", type="related_to", weight=0.8)
        return graph

    @pytest.fixture
    def backend(self, database_url):
        """Create PostgresBackend instance for testing."""
        from kagura.core.graph.backends import PostgresBackend

        backend = PostgresBackend(
            database_url=database_url, user_id="test_user", create_tables=True
        )

        yield backend

        # Cleanup: Delete test data
        try:
            backend.delete()
        finally:
            backend.close()

    def test_save_and_load(self, backend, sample_graph):
        """Test save and load operations."""
        # Save graph
        backend.save(sample_graph)

        # Load graph
        loaded_graph = backend.load()

        assert loaded_graph.number_of_nodes() == sample_graph.number_of_nodes()
        assert loaded_graph.number_of_edges() == sample_graph.number_of_edges()

        # Check node attributes
        assert loaded_graph.nodes["node1"]["type"] == "memory"
        assert loaded_graph.nodes["node2"]["type"] == "topic"

        # Check edge attributes
        assert loaded_graph.edges["node1", "node2"]["type"] == "related_to"
        assert loaded_graph.edges["node1", "node2"]["weight"] == 0.8

    def test_upsert_behavior(self, backend, sample_graph):
        """Test that save updates existing graph."""
        # First save
        backend.save(sample_graph)

        # Modify graph and save again
        sample_graph.add_node("node3", type="user", name="test_user")
        backend.save(sample_graph)

        # Load should have updated graph
        loaded_graph = backend.load()
        assert loaded_graph.number_of_nodes() == 3
        assert "node3" in loaded_graph.nodes()

    def test_exists(self, backend, sample_graph):
        """Test exists() method."""
        # Initially doesn't exist
        assert not backend.exists()

        # After save, should exist
        backend.save(sample_graph)
        assert backend.exists()

    def test_delete(self, backend, sample_graph):
        """Test delete() method."""
        # Save graph
        backend.save(sample_graph)
        assert backend.exists()

        # Delete
        backend.delete()
        assert not backend.exists()

    def test_multi_user_isolation(self, database_url, sample_graph):
        """Test that different users have isolated graphs."""
        from kagura.core.graph.backends import PostgresBackend

        user1_backend = PostgresBackend(database_url=database_url, user_id="user1")
        user2_backend = PostgresBackend(database_url=database_url, user_id="user2")

        try:
            # User1 saves graph
            user1_backend.save(sample_graph)

            # User2 should not see User1's graph
            assert not user2_backend.exists()

            # User2 loads empty graph
            user2_graph = user2_backend.load()
            assert user2_graph.number_of_nodes() == 0

        finally:
            user1_backend.delete()
            user2_backend.delete()
            user1_backend.close()
            user2_backend.close()
