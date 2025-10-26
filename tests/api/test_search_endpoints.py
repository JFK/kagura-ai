"""Tests for Search & Recall endpoints (v4.0 REST API)."""

import pytest
from fastapi.testclient import TestClient

from kagura.api.server import app

client = TestClient(app)


class TestSearchEndpoint:
    """Test POST /api/v1/search - Full-text search."""

    def setup_method(self):
        """Create test memories before each test."""
        test_memories = [
            {
                "key": "python_guide",
                "value": "Python is a high-level programming language",
                "scope": "persistent",
                "tags": ["python", "programming"],
            },
            {
                "key": "javascript_guide",
                "value": "JavaScript is a scripting language for web",
                "scope": "persistent",
                "tags": ["javascript", "web"],
            },
        ]

        for memory in test_memories:
            client.post("/api/v1/memory", json=memory)

    def test_search_memories(self):
        """Test basic search."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "python",
                "scope": "all",
                "limit": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert data["query"] == "python"

        # Should find python_guide
        assert any(r["key"] == "python_guide" for r in data["results"])

    def test_search_with_tag_filter(self):
        """Test search with tag filtering."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "language",
                "scope": "all",
                "limit": 10,
                "filter_tags": ["python"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # All results should have 'python' tag
        for result in data["results"]:
            assert "python" in result["tags"]

    def test_search_with_limit(self):
        """Test search limit parameter."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "programming",
                "limit": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 1


class TestRecallEndpoint:
    """Test POST /api/v1/recall - Semantic recall."""

    def setup_method(self):
        """Create test memories before each test."""
        test_memories = [
            {
                "key": "best_practices",
                "value": "Always use type hints for better code quality",
                "scope": "persistent",
                "tags": ["python", "best-practices"],
            },
        ]

        for memory in test_memories:
            client.post("/api/v1/memory", json=memory)

    def test_recall_semantic_search(self):
        """Test semantic recall."""
        response = client.post(
            "/api/v1/recall",
            json={
                "query": "How should I write Python code?",
                "k": 5,
                "scope": "all",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["query"] == "How should I write Python code?"
        assert data["k"] == 5

        # Results should have similarity scores
        if data["results"]:
            for result in data["results"]:
                assert "similarity" in result
                assert 0.0 <= result["similarity"] <= 1.0

    def test_recall_with_k_parameter(self):
        """Test k parameter limits results."""
        response = client.post(
            "/api/v1/recall",
            json={
                "query": "Python programming",
                "k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 3

    def test_recall_without_rag(self):
        """Test recall gracefully handles RAG not enabled."""
        # This test depends on environment
        # If RAG is disabled, should return empty results
        response = client.post(
            "/api/v1/recall",
            json={
                "query": "test query",
                "k": 5,
            },
        )

        assert response.status_code == 200
        # Should not crash, may return empty results
