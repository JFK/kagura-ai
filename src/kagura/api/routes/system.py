"""System endpoints.

Health check and metrics API routes:
- GET /api/v1/health - Health check
- GET /api/v1/metrics - System metrics
"""

import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter

from kagura.api import models
from kagura.api.dependencies import MemoryManagerDep

router = APIRouter()

# Track API start time for uptime calculation
_START_TIME = time.time()


@router.get("/health", response_model=models.HealthResponse)
async def health_check(memory: MemoryManagerDep) -> dict[str, Any]:
    """Health check endpoint.

    Args:
        memory: MemoryManager dependency

    Returns:
        Health status and service statuses
    """
    services = {}

    # API always healthy if we got here
    services["api"] = "healthy"

    # Check persistent memory (SQLite)
    try:
        memory.persistent.count(memory.agent_name)
        services["database"] = "healthy"
    except Exception:
        services["database"] = "unhealthy"

    # Check RAG (ChromaDB)
    if memory.rag or memory.persistent_rag:
        try:
            if memory.rag:
                memory.rag.count(memory.agent_name)
            if memory.persistent_rag:
                memory.persistent_rag.count(memory.agent_name)
            services["vector_db"] = "healthy"
        except Exception:
            services["vector_db"] = "unhealthy"
    else:
        services["vector_db"] = "disabled"

    # Overall status
    unhealthy_services = [k for k, v in services.items() if v == "unhealthy"]
    if unhealthy_services:
        status = "unhealthy"
    elif any(v == "degraded" for v in services.values()):
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "timestamp": datetime.now(),
        "services": services,
    }


@router.get("/metrics", response_model=models.MetricsResponse)
async def get_metrics(memory: MemoryManagerDep) -> dict[str, Any]:
    """Get system metrics.

    Args:
        memory: MemoryManager dependency

    Returns:
        System metrics (memory count, storage size, etc.)
    """
    uptime = time.time() - _START_TIME

    # Count memories
    memory_count = 0
    try:
        memory_count += memory.persistent.count(memory.agent_name)
    except Exception:
        pass

    try:
        if memory.rag:
            memory_count += memory.rag.count(memory.agent_name)
    except Exception:
        pass

    # Estimate storage size (rough approximation)
    # TODO: Get actual database file size
    storage_size_mb = memory_count * 0.001  # Assume ~1KB per memory

    return {
        "memory_count": memory_count,
        "storage_size_mb": storage_size_mb,
        "cache_hit_rate": None,  # TODO: Implement with Redis
        "api_requests_total": None,  # TODO: Implement request counter
        "uptime_seconds": uptime,
    }
