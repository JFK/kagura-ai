"""Tests for System endpoints (v4.0 REST API)."""

from fastapi.testclient import TestClient

from kagura.api.server import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test GET /api/v1/health - Health check."""

    def test_health_check_returns_status(self):
        """Test that health endpoint returns status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "services" in data

    def test_health_check_includes_services(self):
        """Test that health check includes service statuses."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        services = data["services"]

        # Should include these services
        assert "api" in services
        assert "database" in services
        assert "vector_db" in services

        # Each service should have a status
        for service, status in services.items():
            assert status in ["healthy", "unhealthy", "disabled"]


class TestMetricsEndpoint:
    """Test GET /api/v1/metrics - System metrics."""

    def test_metrics_returns_counts(self):
        """Test that metrics endpoint returns memory counts."""
        response = client.get("/api/v1/metrics")

        assert response.status_code == 200
        data = response.json()

        assert "memory_count" in data
        assert "storage_size_mb" in data
        assert "uptime_seconds" in data

        # Memory count should be non-negative integer
        assert isinstance(data["memory_count"], int)
        assert data["memory_count"] >= 0

        # Storage size should be non-negative float
        assert isinstance(data["storage_size_mb"], (int, float))
        assert data["storage_size_mb"] >= 0.0

        # Uptime should be positive
        assert data["uptime_seconds"] > 0

    def test_metrics_optional_fields(self):
        """Test optional metrics fields."""
        response = client.get("/api/v1/metrics")

        assert response.status_code == 200
        data = response.json()

        # These may be None in alpha
        assert "cache_hit_rate" in data
        assert "api_requests_total" in data
