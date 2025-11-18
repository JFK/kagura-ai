"""Service Layer for Kagura AI.

Provides business logic layer that sits between interface layers (MCP, API, CLI)
and core data access layers. This eliminates code duplication across interfaces.

Architecture:
    MCP Tools ──┐
    API Routes ─┼──> Services ──> Core Memory/Storage
    CLI Commands─┘

Services:
    - MemoryService: Memory CRUD operations
    - CodingService: Coding session management
    - HealthService: System diagnostics and health checks
    - AuthService: Authentication business logic

Benefits:
    - Single source of truth for business logic
    - 40% code reduction (eliminates duplication)
    - Easier testing (mock services, not infrastructure)
    - Consistent behavior across all interfaces
"""

from kagura.services.base import BaseService
from kagura.services.memory_service import (
    MemoryResult,
    MemoryService,
    SearchResult,
)

__all__ = [
    # Base
    "BaseService",
    # Memory Service
    "MemoryService",
    "MemoryResult",
    "SearchResult",
]
