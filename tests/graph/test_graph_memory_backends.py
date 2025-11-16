"""Integration tests for GraphMemory with different backends.

Issue #554 - Cloud-Native Infrastructure Migration
"""

import os
import tempfile
from pathlib import Path

import pytest

from kagura.core.graph.memory import GraphMemory


class TestGraphMemoryWithJSONBackend:
    """Test GraphMemory with JSONBackend (default)."""

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

    def test_legacy_persist_path_mode(self, temp_json_file):
        """Test legacy mode with persist_path (backward compatibility)."""
        graph = GraphMemory(persist_path=temp_json_file)

        # Add nodes and edges
        graph.add_node("node1", "memory", {"key": "test"})
        graph.add_node("node2", "topic", {"name": "test_topic"})
        graph.add_edge("node1", "node2", "related_to", weight=0.8)

        # Persist
        graph.persist()

        # Load in new instance
        graph2 = GraphMemory(persist_path=temp_json_file)

        assert graph2.graph.number_of_nodes() == 2
        assert graph2.graph.number_of_edges() == 1
        assert "node1" in graph2.graph.nodes()

    def test_backend_type_json(self, temp_json_file):
        """Test explicit backend_type='json' mode."""
        graph = GraphMemory(persist_path=temp_json_file, backend_type="json")

        graph.add_node("node1", "memory", {"key": "test"})
        graph.persist()

        # Verify file exists
        assert temp_json_file.exists()

        # Load
        graph2 = GraphMemory(persist_path=temp_json_file, backend_type="json")
        assert graph2.graph.number_of_nodes() == 1

    def test_environment_variable_json(self, temp_json_file, monkeypatch):
        """Test GRAPH_BACKEND environment variable with json."""
        monkeypatch.setenv("GRAPH_BACKEND", "json")

        graph = GraphMemory(persist_path=temp_json_file)

        graph.add_node("node1", "memory", {"key": "test"})
        graph.persist()

        assert temp_json_file.exists()


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set (PostgreSQL tests require database)",
)
class TestGraphMemoryWithPostgresBackend:
    """Test GraphMemory with PostgresBackend.

    Note: Requires TEST_DATABASE_URL environment variable.

    Example:
        export TEST_DATABASE_URL=postgresql://localhost:5432/kagura_test
        pytest tests/graph/test_graph_memory_backends.py::TestGraphMemoryWithPostgresBackend
    """

    @pytest.fixture
    def database_url(self):
        """Get test database URL from environment."""
        return os.getenv("TEST_DATABASE_URL")

    @pytest.fixture
    def graph_memory(self, database_url, monkeypatch):
        """Create GraphMemory with PostgresBackend."""
        monkeypatch.setenv("DATABASE_URL", database_url)
        monkeypatch.setenv("GRAPH_BACKEND", "postgres")

        graph = GraphMemory(user_id="test_user_integration")

        yield graph

        # Cleanup
        if hasattr(graph, "backend") and graph.backend:
            try:
                graph.backend.delete()
                graph.backend.close()
            except Exception:
                pass

    def test_postgres_backend_mode(self, graph_memory):
        """Test GraphMemory with postgres backend."""
        # Add nodes and edges
        graph_memory.add_node("node1", "memory", {"key": "test"})
        graph_memory.add_node("node2", "topic", {"name": "test_topic"})
        graph_memory.add_edge("node1", "node2", "related_to", weight=0.8)

        # Persist
        graph_memory.persist()

        # Verify backend is PostgresBackend
        from kagura.core.graph.backends import PostgresBackend

        assert isinstance(graph_memory.backend, PostgresBackend)

    def test_reload_from_postgres(self, database_url, monkeypatch):
        """Test that graph persists across instances."""
        monkeypatch.setenv("DATABASE_URL", database_url)
        monkeypatch.setenv("GRAPH_BACKEND", "postgres")

        # First instance: Save data
        graph1 = GraphMemory(user_id="test_reload")
        graph1.add_node("node1", "memory", {"key": "test"})
        graph1.persist()

        try:
            # Second instance: Load data
            graph2 = GraphMemory(user_id="test_reload")
            assert graph2.graph.number_of_nodes() == 1
            assert "node1" in graph2.graph.nodes()

        finally:
            # Cleanup
            if hasattr(graph1, "backend") and graph1.backend:
                graph1.backend.delete()
                graph1.backend.close()

    def test_explicit_postgres_backend(self, database_url):
        """Test explicit PostgresBackend injection."""
        from kagura.core.graph.backends import PostgresBackend

        backend = PostgresBackend(database_url=database_url, user_id="test_explicit")

        try:
            graph = GraphMemory(backend=backend)

            graph.add_node("node1", "memory", {"key": "test"})
            graph.persist()

            # Load in new instance with same backend
            graph2 = GraphMemory(backend=backend)
            assert graph2.graph.number_of_nodes() == 1

        finally:
            backend.delete()
            backend.close()
