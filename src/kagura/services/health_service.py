"""Health service - System diagnostics and health checks.

Simplified implementation for Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kagura.services.base import BaseService


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    status: str  # "healthy", "degraded", "unhealthy"
    checks: dict[str, Any]
    message: str | None = None

    @property
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.status == "healthy"


class HealthService(BaseService):
    """Business logic for system diagnostics.

    Simplified implementation for Phase 1.
    Provides basic health check functionality.
    """

    async def check_memory_system(self) -> dict[str, Any]:
        """Check memory system health.

        Returns:
            Health check result
        """
        try:
            # Basic check: try to import core modules
            from kagura.core.memory import MemoryManager

            return {
                "status": "healthy",
                "module": "MemoryManager",
                "available": True,
            }
        except Exception as e:
            self.logger.error(f"Memory system check failed: {e}")
            return {
                "status": "unhealthy",
                "module": "MemoryManager",
                "available": False,
                "error": str(e),
            }

    async def check_coding_system(self) -> dict[str, Any]:
        """Check coding memory system health.

        Returns:
            Health check result
        """
        try:
            from kagura.core.memory.coding_memory import CodingMemoryManager

            return {
                "status": "healthy",
                "module": "CodingMemoryManager",
                "available": True,
            }
        except Exception as e:
            self.logger.error(f"Coding system check failed: {e}")
            return {
                "status": "unhealthy",
                "module": "CodingMemoryManager",
                "available": False,
                "error": str(e),
            }

    async def run_diagnostics(self) -> HealthCheckResult:
        """Run full system diagnostics.

        Returns:
            HealthCheckResult with all checks
        """
        checks = {
            "memory": await self.check_memory_system(),
            "coding": await self.check_coding_system(),
        }

        # Determine overall status
        unhealthy_count = sum(
            1 for check in checks.values() if check["status"] == "unhealthy"
        )

        if unhealthy_count == 0:
            status = "healthy"
            message = "All systems operational"
        elif unhealthy_count == len(checks):
            status = "unhealthy"
            message = "All systems failing"
        else:
            status = "degraded"
            message = f"{unhealthy_count}/{len(checks)} systems failing"

        return HealthCheckResult(status=status, checks=checks, message=message)
