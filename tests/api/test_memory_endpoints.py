"""Tests for Memory CRUD endpoints (v4.0 REST API)."""

import pytest
from fastapi.testclient import TestClient

from kagura.api.server import app

client = TestClient(app)


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_returns_api_info(self):
        """Test that root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Kagura Memory API"
        assert data["version"] == "4.0.0a0"
        assert data["status"] == "active"
        assert data["docs"] == "/docs"


class TestMemoryCreate:
    """Test POST /api/v1/memory - Create memory."""

    def test_create_persistent_memory(self):
        """Test creating a persistent memory."""
        response = client.post(
            "/api/v1/memory",
            json={
                "key": "test_persistent_1",
                "value": "Test persistent memory value",
                "scope": "persistent",
                "tags": ["test", "persistent"],
                "importance": 0.8,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["key"] == "test_persistent_1"
        assert data["value"] == "Test persistent memory value"
        assert data["scope"] == "persistent"
        assert data["tags"] == ["test", "persistent"]
        assert data["importance"] == 0.8

    def test_create_working_memory(self):
        """Test creating a working memory."""
        response = client.post(
            "/api/v1/memory",
            json={
                "key": "test_working_1",
                "value": "Test working memory value",
                "scope": "working",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["key"] == "test_working_1"
        assert data["scope"] == "working"

    def test_create_duplicate_memory_fails(self):
        """Test that creating duplicate memory returns 409."""
        # Create first memory
        client.post(
            "/api/v1/memory",
            json={
                "key": "duplicate_key",
                "value": "First value",
                "scope": "persistent",
            },
        )

        # Try to create duplicate
        response = client.post(
            "/api/v1/memory",
            json={
                "key": "duplicate_key",
                "value": "Second value",
                "scope": "persistent",
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["error"]


class TestMemoryGet:
    """Test GET /api/v1/memory/{key} - Get memory."""

    def setup_method(self):
        """Create test memory before each test."""
        client.post(
            "/api/v1/memory",
            json={
                "key": "get_test_key",
                "value": "Get test value",
                "scope": "persistent",
                "tags": ["get-test"],
                "importance": 0.7,
            },
        )

    def test_get_existing_memory(self):
        """Test getting an existing memory."""
        response = client.get("/api/v1/memory/get_test_key")

        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "get_test_key"
        assert data["value"] == "Get test value"
        assert data["tags"] == ["get-test"]
        assert data["importance"] == 0.7

    def test_get_nonexistent_memory(self):
        """Test getting a memory that doesn't exist."""
        response = client.get("/api/v1/memory/nonexistent_key")

        assert response.status_code == 404
        assert "not found" in response.json()["error"]


class TestMemoryUpdate:
    """Test PUT /api/v1/memory/{key} - Update memory."""

    def setup_method(self):
        """Create test memory before each test."""
        client.post(
            "/api/v1/memory",
            json={
                "key": "update_test_key",
                "value": "Original value",
                "scope": "persistent",
                "tags": ["original"],
                "importance": 0.5,
            },
        )

    def test_update_memory_value(self):
        """Test updating memory value."""
        response = client.put(
            "/api/v1/memory/update_test_key",
            json={"value": "Updated value"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "Updated value"
        assert data["tags"] == ["original"]  # Tags unchanged

    def test_update_memory_tags(self):
        """Test updating memory tags."""
        response = client.put(
            "/api/v1/memory/update_test_key",
            json={"tags": ["updated", "new-tag"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["updated", "new-tag"]

    def test_update_memory_importance(self):
        """Test updating memory importance."""
        response = client.put(
            "/api/v1/memory/update_test_key",
            json={"importance": 0.9},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["importance"] == 0.9

    def test_update_nonexistent_memory(self):
        """Test updating a memory that doesn't exist."""
        response = client.put(
            "/api/v1/memory/nonexistent_key",
            json={"value": "New value"},
        )

        assert response.status_code == 404


class TestMemoryDelete:
    """Test DELETE /api/v1/memory/{key} - Delete memory."""

    def setup_method(self):
        """Create test memory before each test."""
        client.post(
            "/api/v1/memory",
            json={
                "key": "delete_test_key",
                "value": "To be deleted",
                "scope": "persistent",
            },
        )

    def test_delete_existing_memory(self):
        """Test deleting an existing memory."""
        response = client.delete("/api/v1/memory/delete_test_key?scope=persistent")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get("/api/v1/memory/delete_test_key")
        assert get_response.status_code == 404

    def test_delete_nonexistent_memory(self):
        """Test deleting a memory that doesn't exist."""
        response = client.delete("/api/v1/memory/nonexistent_key")

        assert response.status_code == 404


class TestMemoryList:
    """Test GET /api/v1/memory - List memories."""

    def setup_method(self):
        """Create test memories before each test."""
        for i in range(5):
            client.post(
                "/api/v1/memory",
                json={
                    "key": f"list_test_{i}",
                    "value": f"Value {i}",
                    "scope": "persistent",
                },
            )

    def test_list_all_memories(self):
        """Test listing all memories."""
        response = client.get("/api/v1/memory?scope=persistent")

        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
        assert "total" in data
        assert data["total"] >= 5  # At least our 5 test memories

    def test_list_with_pagination(self):
        """Test pagination."""
        response = client.get("/api/v1/memory?scope=persistent&page=1&page_size=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data["memories"]) <= 3
        assert data["page"] == 1
        assert data["page_size"] == 3
