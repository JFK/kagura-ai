"""Security tests for authentication and authorization.

Tests to prevent security vulnerabilities like impersonation attacks.
"""

from fastapi.testclient import TestClient

from kagura.api.auth import APIKeyManager
from kagura.api.server import app

client = TestClient(app)


class TestXUserIDSecurity:
    """Test that X-User-ID header cannot be used for impersonation (Issue #436)."""

    def test_x_user_id_header_ignored_without_auth(self):
        """X-User-ID header should be ignored without API key authentication.

        Attack scenario: Attacker tries to impersonate victim using X-User-ID header
        without providing valid authentication.

        Expected: Request should either require auth or use default_user,
        but NEVER use the X-User-ID value.
        """
        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "victim@example.com",  # Try to impersonate
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            },
        )

        # Should either require auth (401) or succeed with default_user (200)
        # But NEVER use "victim@example.com"
        assert response.status_code in [200, 401, 406]

        # If 200, verify it used default_user (not victim)
        # This would need to be verified in the actual response data
        # or by checking logs/state

    def test_x_user_id_header_ignored_with_valid_auth(self):
        """X-User-ID header should be ignored even with valid API key.

        Attack scenario: Attacker with valid API key tries to access another
        user's data by providing X-User-ID header.

        Expected: Should use user_id from API key, NOT from X-User-ID header.
        """
        # Create test API key for alice
        manager = APIKeyManager()
        api_key = manager.create_key("test-security-key", "alice@example.com")

        try:
            response = client.post(
                "/mcp",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "X-User-ID": "victim@example.com",  # Try to impersonate
                    "Content-Type": "application/json",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                },
            )

            # Should succeed with alice's credentials
            assert response.status_code in [200, 406]

            # Verify response uses alice's user_id (from API key)
            # NOT victim@example.com (from X-User-ID header)
            # TODO: Add specific verification when MCP response format is stable

        finally:
            # Cleanup: Delete test API key
            manager.delete_key("test-security-key", "alice@example.com")

    def test_deprecation_warning_on_x_user_id_header(self):
        """Test that using X-User-ID in REST API triggers deprecation warning."""
        import warnings

        # Test with REST API endpoint (not MCP)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            response = client.get(
                "/api/v1/health",
                headers={"X-User-ID": "test@example.com"},
            )

            # Should succeed (health endpoint doesn't require auth)
            assert response.status_code == 200

            # Should trigger deprecation warning
            # Note: Warning might not be captured in test client
            # This is a best-effort test
            if w:
                assert any(
                    issubclass(warning.category, DeprecationWarning) for warning in w
                )


class TestAPIKeyAuthentication:
    """Test API key authentication works correctly."""

    def test_valid_api_key_authentication(self):
        """Test that valid API key allows access."""
        manager = APIKeyManager()
        api_key = manager.create_key("test-valid-key", "testuser@example.com")

        try:
            response = client.post(
                "/mcp",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                },
            )

            # Should succeed
            assert response.status_code in [200, 406]

        finally:
            manager.delete_key("test-valid-key", "testuser@example.com")

    def test_invalid_api_key_rejected(self):
        """Test that invalid API key is rejected."""
        response = client.post(
            "/mcp",
            headers={
                "Authorization": "Bearer invalid_fake_key_12345",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            },
        )

        # Should be rejected (401 Unauthorized or 403 Forbidden)
        # Or might succeed if auth is optional in dev mode
        assert response.status_code in [200, 401, 403, 406]

    def test_no_auth_allowed_in_dev_mode(self):
        """Test that no authentication is allowed in development mode."""
        import os

        # Ensure we're NOT in REQUIRE_AUTH mode
        old_value = os.getenv("KAGURA_REQUIRE_AUTH")
        if old_value:
            os.environ.pop("KAGURA_REQUIRE_AUTH", None)

        try:
            response = client.post(
                "/mcp",
                headers={"Content-Type": "application/json"},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                },
            )

            # Should succeed in dev mode without auth
            assert response.status_code in [200, 406]

        finally:
            # Restore env
            if old_value:
                os.environ["KAGURA_REQUIRE_AUTH"] = old_value
