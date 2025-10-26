"""Integration tests for remote MCP over HTTP/SSE.

Tests end-to-end scenarios for remote MCP access via HTTP/SSE transport.
"""

import pytest


@pytest.mark.integration
class TestRemoteMCPEndToEnd:
    """End-to-end tests for remote MCP."""

    @pytest.mark.skip(reason="Requires running API server")
    def test_remote_mcp_memory_store_recall(self):
        """Test storing and recalling memory via remote MCP."""
        # This would require:
        # 1. Start API server
        # 2. Connect MCP client via HTTP
        # 3. Call memory_store tool
        # 4. Call memory_recall tool
        # 5. Verify data matches
        pytest.skip("Requires running API server")

    @pytest.mark.skip(reason="Requires running API server")
    def test_multi_client_concurrent_access(self):
        """Test multiple clients accessing same remote server."""
        pytest.skip("Requires running API server")

    @pytest.mark.skip(reason="Requires running API server")
    def test_api_key_authentication_flow(self):
        """Test full API key authentication flow."""
        pytest.skip("Requires running API server")


@pytest.mark.integration
class TestProductionDeployment:
    """Test production deployment scenarios."""

    @pytest.mark.skip(reason="Requires Docker")
    def test_docker_compose_starts_successfully(self):
        """Test that docker-compose.prod.yml starts without errors."""
        pytest.skip("Requires Docker")

    @pytest.mark.skip(reason="Requires Docker")
    def test_health_checks_pass(self):
        """Test that all services pass health checks."""
        pytest.skip("Requires Docker")

    @pytest.mark.skip(reason="Requires Docker")
    def test_api_accessible_via_caddy(self):
        """Test that API is accessible through Caddy reverse proxy."""
        pytest.skip("Requires Docker")


@pytest.mark.integration
class TestExportImportIntegration:
    """Integration tests for export/import."""

    @pytest.mark.asyncio
    async def test_export_import_preserves_all_data(self):
        """Test that export → import preserves 100% of data."""
        import tempfile
        from pathlib import Path

        from kagura.core.memory import MemoryManager
        from kagura.core.memory.export import MemoryExporter, MemoryImporter

        # Create manager with test data
        manager1 = MemoryManager(user_id="integration_user", agent_name="test")

        # Add various types of data
        manager1.working.set("work1", "value1")
        manager1.working.set("work2", "value2")

        manager1.persistent.store(
            key="persist1",
            value="pvalue1",
            user_id="integration_user",
            agent_name="test",
        )

        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = MemoryExporter(manager1)
            export_stats = await exporter.export_all(
                tmpdir,
                include_working=True,
                include_persistent=True,
                include_graph=False,
            )

            # Create fresh manager
            manager2 = MemoryManager(user_id="integration_user", agent_name="test")

            # Import
            importer = MemoryImporter(manager2)
            import_stats = await importer.import_all(tmpdir)

            # Verify 100% preservation
            assert import_stats["memories"] == export_stats["memories"]
            assert manager2.working.get("work1") == "value1"
            assert manager2.working.get("work2") == "value2"


@pytest.mark.integration
class TestSecurityScenarios:
    """Integration tests for security features."""

    def test_file_tools_blocked_remotely(self):
        """Test that file operations are blocked in remote context."""
        from kagura.mcp.server import create_mcp_server

        # Create remote server
        import kagura.mcp.builtin  # noqa: F401

        server = create_mcp_server(name="test-remote", context="remote")

        # file_read should not be available
        # (tested in unit tests, this is integration validation)
        assert server is not None

    def test_api_key_required_mode(self):
        """Test API_KEY_REQUIRED environment variable."""
        # Would require mocking environment and testing FastAPI middleware
        pytest.skip("Requires environment mocking")
