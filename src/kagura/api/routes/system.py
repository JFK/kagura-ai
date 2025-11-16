"""System endpoints.

Health check and metrics API routes:
- GET /api/v1/health - Health check
- GET /api/v1/metrics - System metrics
- GET /api/v1/system/doctor - System health check (Issue #664)

Issue #650: Application restart endpoint:
- POST /api/v1/system/restart - Restart application (Admin only, auto after config update)
"""

import logging
import os
import shutil
import sys
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kagura.api import models
from kagura.api.dependencies import AdminUser, MemoryManagerDep
from kagura.api.models_doctor import (
    APICheck,
    DependencyCheck,
    SystemCheck,
    SystemDoctorResponse,
)
from kagura.config.paths import get_data_dir

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


class VectorCollectionInfo(BaseModel):
    """Vector collection information."""

    name: str
    vector_count: int
    embedding_dimension: int | None = None


class VectorCollectionsResponse(BaseModel):
    """Vector collections response."""

    backend: str  # "qdrant" or "chromadb"
    collections: list[VectorCollectionInfo]


# ============================================================================
# System Doctor (Issue #664)
# ============================================================================


def _check_python_version() -> SystemCheck:
    """Check Python version."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major < 3 or (version.major == 3 and version.minor < 11):
        return SystemCheck(
            status="error",
            message=f"Python {version_str} (requires 3.11+)"
        )
    return SystemCheck(status="ok", message=f"Python {version_str}")


def _check_disk_space() -> SystemCheck:
    """Check available disk space."""
    try:
        data_dir = get_data_dir()
        usage = shutil.disk_usage(data_dir)
        free_gb = usage.free / (1024**3)

        if free_gb < 1:
            return SystemCheck(
                status="warning",
                message=f"{free_gb:.1f} GB available (low)"
            )
        return SystemCheck(status="ok", message=f"{free_gb:.1f} GB available")
    except Exception as e:
        return SystemCheck(status="error", message=f"Could not check: {e}")


def _check_dependencies() -> list[DependencyCheck]:
    """Check optional dependencies."""
    results = []

    # ChromaDB (required for RAG)
    try:
        import chromadb  # type: ignore

        version = chromadb.__version__
        results.append(DependencyCheck(
            name="chromadb",
            status="ok",
            message=f"v{version}"
        ))
    except ImportError:
        results.append(DependencyCheck(
            name="chromadb",
            status="warning",
            message="Not installed (RAG disabled)"
        ))

    # Sentence Transformers (required for RAG embeddings)
    try:
        import sentence_transformers  # type: ignore

        version = sentence_transformers.__version__
        results.append(DependencyCheck(
            name="sentence-transformers",
            status="ok",
            message=f"v{version}"
        ))
    except ImportError:
        results.append(DependencyCheck(
            name="sentence-transformers",
            status="warning",
            message="Not installed (RAG disabled)"
        ))
    except RuntimeError as e:
        error_msg = str(e).split("\n")[0]
        results.append(DependencyCheck(
            name="sentence-transformers",
            status="error",
            message=f"Load failed: {error_msg}"
        ))

    return results


async def _check_api_configuration() -> list[APICheck]:
    """Check API key configuration and connectivity."""
    from kagura.utils.api.check import check_api_configuration

    api_results = await check_api_configuration()
    return [
        APICheck(provider=provider, status=status, message=msg)
        for provider, status, msg in api_results
    ]


def _check_postgres() -> SystemCheck:
    """Check PostgreSQL database connectivity (Issue #668)."""
    db_url = os.getenv("DATABASE_URL", "")

    if not db_url or "postgresql" not in db_url:
        return SystemCheck(status="info", message="Not configured (using SQLite)")

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(db_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            version_short = version.split(",")[0] if version else "Unknown"

        return SystemCheck(status="ok", message=f"Connected ({version_short})")
    except ImportError:
        return SystemCheck(status="error", message="sqlalchemy or psycopg2 not installed")
    except Exception as e:
        return SystemCheck(status="error", message=f"Connection failed: {str(e)[:50]}")


def _check_redis() -> SystemCheck:
    """Check Redis cache connectivity (Issue #668)."""
    redis_url = os.getenv("REDIS_URL")
    cache_backend = os.getenv("CACHE_BACKEND", "memory")

    if cache_backend != "redis":
        return SystemCheck(status="info", message="Not configured (using in-memory cache)")

    if not redis_url:
        return SystemCheck(status="warning", message="CACHE_BACKEND=redis but REDIS_URL not set")

    try:
        import redis

        client = redis.from_url(redis_url, socket_timeout=5, socket_connect_timeout=5)
        client.ping()
        info: dict[str, Any] = client.info("stats")  # type: ignore
        total_ops = int(info.get("total_commands_processed", 0))

        return SystemCheck(status="ok", message=f"Connected ({total_ops:,} ops processed)")
    except ImportError:
        return SystemCheck(status="error", message="redis package not installed")
    except Exception as e:
        return SystemCheck(status="error", message=f"Connection failed: {str(e)[:50]}")


def _check_qdrant() -> SystemCheck:
    """Check Qdrant vector database connectivity (Issue #668)."""
    qdrant_url = os.getenv("QDRANT_URL")
    vector_backend = os.getenv("VECTOR_BACKEND", "chromadb")

    if vector_backend != "qdrant":
        return SystemCheck(status="info", message="Not configured (using ChromaDB)")

    if not qdrant_url:
        return SystemCheck(status="warning", message="VECTOR_BACKEND=qdrant but QDRANT_URL not set")

    try:
        from kagura.core.resources import get_rag_client

        # Use centralized resource manager
        client = get_rag_client(backend="qdrant")
        collections = client.get_collections().collections
        collection_count = len(collections)

        return SystemCheck(status="ok", message=f"Connected to {qdrant_url} ({collection_count} collections)")
    except ImportError:
        return SystemCheck(status="error", message="qdrant-client not installed")
    except Exception as e:
        return SystemCheck(status="error", message=f"Connection failed: {str(e)[:50]}")


def _check_remote_mcp() -> SystemCheck:
    """Check remote MCP server status (Issue #668, #677).

    Checks if MCP server is actually running by importing the MCP transport module
    instead of relying on environment variables.
    """
    try:
        from kagura.api.routes.mcp_transport import _mcp_server

        if _mcp_server is not None:
            # MCP server is initialized and running
            # Count available tools if possible
            try:
                tool_count = len(_mcp_server.list_tools())
                return SystemCheck(
                    status="ok",
                    message=f"Available ({tool_count} tools, SSE endpoint: /mcp/sse)"
                )
            except Exception:
                # Can't get tool count, but server is running
                return SystemCheck(
                    status="ok",
                    message="Available (SSE endpoint: /mcp/sse)"
                )
        else:
            # MCP module exists but server not initialized
            return SystemCheck(
                status="info",
                message="Not initialized (restart may be needed)"
            )
    except ImportError:
        # MCP module not available (not included in build)
        return SystemCheck(
            status="info",
            message="MCP module not installed"
        )
    except Exception as e:
        # Unexpected error
        logger.warning(f"MCP status check failed: {e}")
        return SystemCheck(
            status="warning",
            message=f"Status check failed: {str(e)[:40]}"
        )


@router.get("/system/doctor", response_model=SystemDoctorResponse)
async def get_system_doctor() -> SystemDoctorResponse:
    """Get system health check information.

    Returns comprehensive system diagnostics including:
    - Python version and disk space
    - Backend services (PostgreSQL, Redis, Qdrant)
    - Optional dependencies (ChromaDB, sentence-transformers)
    - API configuration and connectivity
    - Remote MCP server status

    Issue #668: Enhanced with backend health checks

    Returns:
        System health check results with recommendations

    Example:
        GET /api/v1/system/doctor
        Response: {
            "python_version": {"status": "ok", "message": "Python 3.11.5"},
            "disk_space": {"status": "ok", "message": "100.5 GB available"},
            "postgres": {"status": "ok", "message": "Connected (PostgreSQL 14.x)"},
            "redis": {"status": "ok", "message": "Connected (1,234 ops processed)"},
            "qdrant": {"status": "ok", "message": "Connected (5 collections)"},
            "dependencies": [...],
            "api_configuration": [...],
            "remote_mcp": {"status": "info", "message": "Not enabled"},
            "overall_status": "ok",
            "recommendations": []
        }
    """
    python_version = _check_python_version()
    disk_space = _check_disk_space()
    dependencies = _check_dependencies()
    api_configuration = await _check_api_configuration()

    # Backend services (Issue #668)
    postgres = _check_postgres()
    redis = _check_redis()
    qdrant = _check_qdrant()
    remote_mcp = _check_remote_mcp()

    # Determine overall status
    overall_status = "ok"
    recommendations = []

    if python_version.status == "error":
        overall_status = "error"
        recommendations.append("Upgrade Python to version 3.11 or higher")

    if disk_space.status == "warning":
        if overall_status == "ok":
            overall_status = "warning"
        recommendations.append("Free up disk space (less than 1 GB available)")

    # Backend warnings
    for backend, name in [(postgres, "PostgreSQL"), (redis, "Redis"), (qdrant, "Qdrant")]:
        if backend.status == "error":
            overall_status = "error"
            recommendations.append(f"Check {name} connectivity")
        elif backend.status == "warning" and overall_status == "ok":
            overall_status = "warning"

    for dep in dependencies:
        if dep.status == "warning" and "chromadb" in dep.name.lower():
            if overall_status == "ok":
                overall_status = "warning"
            recommendations.append(
                "Install RAG dependencies: pip install chromadb sentence-transformers"
            )

    for api in api_configuration:
        if api.status == "error":
            overall_status = "error"
            recommendations.append(f"Check {api.provider} API key configuration")

    return SystemDoctorResponse(
        python_version=python_version,
        disk_space=disk_space,
        dependencies=dependencies,
        postgres=postgres,
        redis=redis,
        qdrant=qdrant,
        api_configuration=api_configuration,
        remote_mcp=remote_mcp,
        overall_status=overall_status,
        recommendations=recommendations,
    )


# ============================================================================
# Backend Configuration (Issue #694)
# ============================================================================


class BackendInfo(BaseModel):
    """Backend service information."""

    type: str
    url: str | None
    connected: bool
    status: str
    message: str
    stats: dict[str, Any] | None = None


class BackendStatusResponse(BaseModel):
    """All backend statuses."""

    database: BackendInfo
    vector_db: BackendInfo
    cache: BackendInfo


@router.get("/system/backends", response_model=BackendStatusResponse)
async def get_backend_status() -> BackendStatusResponse:
    """Get current backend configuration and status.

    Returns comprehensive information about all configured backends:
    - Database: SQLite or PostgreSQL
    - Vector DB: ChromaDB or Qdrant
    - Cache: In-memory or Redis

    Returns:
        Backend configuration and connectivity status

    Example:
        GET /api/v1/system/backends
        Response: {
            "database": {
                "type": "postgres",
                "url": "postgresql://...@34.84.179.196:5432/kagura",
                "connected": true,
                "status": "ok",
                "message": "Connected (PostgreSQL 14.x)",
                "stats": {"tables": 5, "rows": 1234}
            },
            "vector_db": {
                "type": "qdrant",
                "url": "http://qdrant:6333",
                "connected": true,
                "status": "ok",
                "message": "Connected (5 collections)",
                "stats": {"collections": 5, "vectors": 1234}
            },
            "cache": {
                "type": "redis",
                "url": "redis://10.71.69.43:6379",
                "connected": true,
                "status": "ok",
                "message": "Connected (10,000 ops)",
                "stats": {"entries": 50, "hit_rate": 85.5}
            }
        }
    """
    # Database
    db_url = os.getenv("DATABASE_URL", "")
    db_type = "postgres" if "postgresql" in db_url else "sqlite"
    db_check = _check_postgres()

    database = BackendInfo(
        type=db_type,
        url=db_url if db_type == "postgres" else f"{get_data_dir()}/api_keys.db",
        connected=db_check.status == "ok",
        status=db_check.status,
        message=db_check.message,
        stats=None,  # TODO: Add table/row counts
    )

    # Vector DB
    qdrant_url = os.getenv("QDRANT_URL")
    vector_type = "qdrant" if qdrant_url else "chromadb"
    vector_check = _check_qdrant() if vector_type == "qdrant" else SystemCheck(status="ok", message="ChromaDB (local)")

    vector_db = BackendInfo(
        type=vector_type,
        url=qdrant_url if vector_type == "qdrant" else f"{get_data_dir()}/chroma",
        connected=vector_check.status == "ok",
        status=vector_check.status,
        message=vector_check.message,
        stats=None,  # TODO: Add collection/vector counts
    )

    # Cache
    redis_url = os.getenv("REDIS_URL")
    cache_type = "redis" if redis_url and os.getenv("CACHE_BACKEND") == "redis" else "memory"
    cache_check = _check_redis() if cache_type == "redis" else SystemCheck(status="ok", message="In-memory cache")

    cache = BackendInfo(
        type=cache_type,
        url=redis_url if cache_type == "redis" else None,
        connected=cache_check.status == "ok",
        status=cache_check.status,
        message=cache_check.message,
        stats=None,  # TODO: Add cache stats
    )

    return BackendStatusResponse(
        database=database,
        vector_db=vector_db,
        cache=cache,
    )


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


# ============================================================================
# Vector Collections (Issue #684)
# ============================================================================


@router.get("/system/vector/collections", response_model=VectorCollectionsResponse)
async def get_vector_collections() -> VectorCollectionsResponse:
    """Get vector database collections information.

    Returns:
        List of vector collections with metadata

    Example:
        GET /api/v1/system/vector/collections
        Response: {
            "backend": "qdrant",
            "collections": [
                {
                    "name": "kagura_global_persistent",
                    "vector_count": 1234,
                    "embedding_dimension": 384
                }
            ]
        }

    Raises:
        HTTPException(503): If vector database is not accessible
    """
    vector_backend = os.getenv("VECTOR_BACKEND", "chromadb")
    collections: list[VectorCollectionInfo] = []

    try:
        if vector_backend == "qdrant":
            # Qdrant backend
            qdrant_url = os.getenv("QDRANT_URL")

            if not qdrant_url:
                raise HTTPException(
                    status_code=503,
                    detail="Qdrant not configured (QDRANT_URL not set)",
                )

            try:
                from qdrant_client import QdrantClient

                # Create Qdrant client directly
                client = QdrantClient(url=qdrant_url)

                # Get collections from Qdrant
                qdrant_collections = client.get_collections()

                for col in qdrant_collections.collections:
                    # Get collection info for vector count
                    col_info = client.get_collection(col.name)

                    # Get embedding dimension
                    dimension = None
                    if hasattr(col_info.config.params, "vectors"):
                        # Handle both named and default vectors
                        vectors_config = col_info.config.params.vectors
                        if hasattr(vectors_config, "size"):
                            dimension = vectors_config.size
                        elif isinstance(vectors_config, dict):
                            # Named vectors case
                            first_vector = next(iter(vectors_config.values()), None)
                            if first_vector and hasattr(first_vector, "size"):
                                dimension = first_vector.size

                    collections.append(
                        VectorCollectionInfo(
                            name=col.name,
                            vector_count=col_info.points_count,
                            embedding_dimension=dimension,
                        )
                    )

            except ImportError:
                raise HTTPException(
                    status_code=503,
                    detail="Qdrant client not installed. Install with: pip install qdrant-client",
                )

        else:
            # ChromaDB backend
            try:
                import chromadb  # type: ignore

                chroma_path = get_data_dir() / "chroma"
                client = chromadb.PersistentClient(path=str(chroma_path))

                chroma_collections = client.list_collections()

                for col in chroma_collections:
                    collections.append(
                        VectorCollectionInfo(
                            name=col.name,
                            vector_count=col.count(),
                            embedding_dimension=None,  # ChromaDB doesn't expose this easily
                        )
                    )

            except ImportError:
                raise HTTPException(
                    status_code=503,
                    detail="ChromaDB not installed. Install with: pip install chromadb",
                )

        return VectorCollectionsResponse(
            backend=vector_backend,
            collections=collections,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get vector collections: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Vector database error: {str(e)}",
        )
