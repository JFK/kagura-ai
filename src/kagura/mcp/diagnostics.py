"""MCP diagnostics and health checks.

Provides diagnostic utilities for MCP server and related services.
"""

import json
from pathlib import Path
from typing import Any

import httpx


class MCPDiagnostics:
    """MCP server diagnostics and health checks."""

    def __init__(self, api_base_url: str = "http://localhost:8080"):
        """Initialize diagnostics.

        Args:
            api_base_url: Base URL for Kagura API server
        """
        self.api_base_url = api_base_url

    async def check_api_server(self) -> dict[str, Any]:
        """Check if API server is running.

        Returns:
            Status dict with 'status' and 'details'
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/health", timeout=5.0
                )
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "details": response.json(),
                        "url": self.api_base_url,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "details": f"HTTP {response.status_code}",
                        "url": self.api_base_url,
                    }
        except httpx.ConnectError:
            return {
                "status": "unreachable",
                "details": "Cannot connect to API server",
                "url": self.api_base_url,
            }
        except Exception as e:
            return {"status": "error", "details": str(e), "url": self.api_base_url}

    async def check_memory_manager(self) -> dict[str, Any]:
        """Check MemoryManager initialization.

        Returns:
            Status dict
        """
        try:
            from kagura.core.memory import MemoryManager

            manager = MemoryManager(agent_name="diagnostics", enable_rag=True)

            # Count memories
            persistent_count = manager.persistent.count("diagnostics")
            rag_count = manager.rag.count("diagnostics") if manager.rag else 0

            return {
                "status": "healthy",
                "persistent_count": persistent_count,
                "rag_count": rag_count,
                "rag_enabled": manager.rag is not None,
            }
        except ImportError as e:
            return {"status": "error", "details": f"Import error: {e}"}
        except Exception as e:
            return {"status": "error", "details": str(e)}

    def check_claude_desktop_config(self) -> dict[str, Any]:
        """Check Claude Desktop MCP configuration.

        Returns:
            Status dict
        """
        # Claude Desktop config path
        config_path = Path.home() / ".config" / "claude" / "claude_desktop_config.json"

        if not config_path.exists():
            return {
                "status": "not_configured",
                "details": "Claude Desktop config not found",
                "path": str(config_path),
            }

        try:
            with open(config_path) as f:
                config = json.load(f)

            # Check if kagura is configured
            mcp_servers = config.get("mcpServers", {})
            kagura_config = mcp_servers.get("kagura-memory")

            if kagura_config:
                return {
                    "status": "configured",
                    "details": "Kagura MCP server configured",
                    "config": kagura_config,
                    "path": str(config_path),
                }
            else:
                return {
                    "status": "not_configured",
                    "details": "Kagura not in mcpServers",
                    "path": str(config_path),
                }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "details": "Invalid JSON in config file",
                "path": str(config_path),
            }
        except Exception as e:
            return {
                "status": "error",
                "details": str(e),
                "path": str(config_path),
            }

    def check_storage_usage(self) -> dict[str, Any]:
        """Check storage usage.

        Returns:
            Status dict with storage info
        """
        try:
            kagura_dir = Path.home() / ".kagura"

            if not kagura_dir.exists():
                return {
                    "status": "not_initialized",
                    "details": "~/.kagura directory not found",
                }

            # Calculate directory size
            total_size = sum(
                f.stat().st_size for f in kagura_dir.rglob("*") if f.is_file()
            )
            size_mb = total_size / (1024 * 1024)

            # Check if approaching limits (warning at 500MB, critical at 1GB)
            if size_mb > 1000:
                status = "critical"
            elif size_mb > 500:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "size_mb": round(size_mb, 2),
                "path": str(kagura_dir),
            }
        except Exception as e:
            return {"status": "error", "details": str(e)}

    async def run_full_diagnostics(self) -> dict[str, Any]:
        """Run all diagnostic checks.

        Returns:
            Comprehensive diagnostic report
        """
        results = {}

        # Check API server
        results["api_server"] = await self.check_api_server()

        # Check MemoryManager
        results["memory_manager"] = await self.check_memory_manager()

        # Check Claude Desktop config
        results["claude_desktop"] = self.check_claude_desktop_config()

        # Check storage
        results["storage"] = self.check_storage_usage()

        # Overall status
        statuses = [v.get("status") for v in results.values()]
        if "error" in statuses or "unreachable" in statuses:
            overall = "unhealthy"
        elif "warning" in statuses or "critical" in statuses:
            overall = "degraded"
        else:
            overall = "healthy"

        results["overall"] = overall

        return results
