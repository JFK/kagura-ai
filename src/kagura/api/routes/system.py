"""System endpoints.

Health check and metrics API routes:
- GET /api/v1/health - Health check
- GET /api/v1/metrics - System metrics

Issue #650: Application restart endpoint:
- POST /api/v1/system/restart - Restart application (Admin only, auto after config update)
"""

import logging
import os
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kagura.api import models
from kagura.api.dependencies import AdminUser, MemoryManagerDep

logger = logging.getLogger(__name__)

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


# ============================================================================
# Application Restart (Issue #650)
# ============================================================================


class RestartResponse(BaseModel):
    """Application restart response."""

    status: str
    message: str
    container_name: str


@router.post("/system/restart", response_model=RestartResponse)
async def restart_application(admin_user: AdminUser):
    """Restart application container.

    Requires ADMIN role. Restarts the kagura-api Docker container
    to apply configuration changes from .env.cloud.

    Args:
        admin_user: Authenticated admin user

    Returns:
        Restart status

    Raises:
        HTTPException(500): If Docker client unavailable or restart fails
        HTTPException(403): If not admin

    Example:
        POST /api/v1/system/restart
        Response: {
            "status": "restarting",
            "message": "Application container restarting in ~10 seconds",
            "container_name": "kagura-api"
        }

    Note:
        This endpoint will kill itself as the container restarts.
        Client should poll /health after ~30 seconds to verify restart.

    Security:
        Requires Docker socket mount in docker-compose.cloud.yml:
        volumes:
          - /var/run/docker.sock:/var/run/docker.sock:ro
    """
    container_name = os.getenv("DOCKER_CONTAINER_NAME", "kagura-api")

    try:
        import docker

        client = docker.from_env()

        # Get container
        try:
            container = client.containers.get(container_name)
        except docker.errors.NotFound:
            raise HTTPException(
                status_code=500,
                detail=f"Container '{container_name}' not found. "
                "Ensure DOCKER_CONTAINER_NAME environment variable is set correctly.",
            )

        # Log restart
        logger.warning(
            f"Application restart initiated by {admin_user['email']} "
            f"(container={container_name})"
        )

        # Restart container
        # Note: This will kill the current process
        container.restart()

        # This line may not be reached if restart is immediate
        return RestartResponse(
            status="restarting",
            message=f"Application container '{container_name}' is restarting. "
            "Please wait ~30 seconds and refresh.",
            container_name=container_name,
        )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Docker Python SDK not installed. "
            "Install with: pip install docker",
        )
    except Exception as e:
        logger.error(f"Container restart failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Restart failed: {str(e)}. "
            "Ensure Docker socket is mounted and permissions are correct.",
        )
