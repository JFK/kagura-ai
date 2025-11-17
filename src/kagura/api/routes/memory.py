"""Memory CRUD endpoints.

Memory management API routes:
- POST /api/v1/memory - Create memory
- GET /api/v1/memory/{key} - Get memory
- PUT /api/v1/memory/{key} - Update memory
- DELETE /api/v1/memory/{key} - Delete memory
- GET /api/v1/memory - List memories
- GET /api/v1/memory/doctor - Memory system health check (Issue #664)
- POST /api/v1/memory/bulk-delete - Bulk delete memories (Issue #666)
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

logger = logging.getLogger(__name__)

from kagura.api import models
from kagura.api.dependencies import (
    MemoryManagerDep,
    get_current_user,
    get_current_user_optional,
)
from kagura.api.models_doctor import MemoryDoctorResponse, MemoryStats
from kagura.config.paths import get_data_dir
from kagura.config.project import get_reranking_enabled
from kagura.utils import (
    MemoryDatabaseQuery,
    build_full_metadata,
    decode_chromadb_metadata,
    extract_memory_fields,
    prepare_for_chromadb,
)

router = APIRouter()


# ============================================================================
# Memory Doctor (Issue #664)
# Must be defined BEFORE /{key} route to avoid path conflicts
# ============================================================================


def _check_memory_system() -> tuple[MemoryStats, list[str]]:
    """Check memory system status.

    Returns:
        Tuple of (stats, recommendations)
    """
    recommendations = []

    # Check database
    import os

    # Determine if using PostgreSQL or SQLite
    using_postgres = os.getenv("PERSISTENT_BACKEND") == "postgres" or os.getenv("DATABASE_URL", "").startswith("postgresql")

    if using_postgres:
        # PostgreSQL: Check database connection and size
        database_exists = True  # Assume exists if using PostgreSQL
        try:
            # Query database size and verify connection
            database_size_mb = MemoryDatabaseQuery.get_db_size_mb()
            _ = MemoryDatabaseQuery.count_memories()
        except Exception as e:
            database_exists = False
            database_size_mb = None
            recommendations.append(
                "PostgreSQL database connection failed. Check DATABASE_URL."
            )
    else:
        # SQLite: Check file existence
        db_path = get_data_dir() / "memory.db"
        database_exists = db_path.exists()
        database_size_mb = db_path.stat().st_size / (1024**2) if database_exists else None

        if not database_exists:
            recommendations.append(
                "Database not initialized (will be created on first use)"
            )

    # Check memory counts
    persistent_count = 0
    rag_count = 0
    rag_enabled = False

    try:
        persistent_count = MemoryDatabaseQuery.count_memories()
    except Exception:
        pass

    # Check RAG (vector database) - Use centralized resource manager
    try:
        from kagura.core.resources import get_rag_collection_count

        rag_count = get_rag_collection_count()
        rag_enabled = True

        # Recommendation if RAG is empty
        if rag_count == 0 and persistent_count > 0:
            recommendations.append(
                "RAG index is empty but memories exist. "
                "Run 'kagura memory index' to build index"
            )

    except ImportError as e:
        if "qdrant" in str(e).lower():
            recommendations.append(
                "Qdrant configured but not installed. Install: pip install qdrant-client"
            )
        else:
            recommendations.append(
                "RAG not available. Install: pip install chromadb sentence-transformers"
            )
    except Exception as e:
        logger.warning(f"Failed to check RAG: {e}")
        recommendations.append(
            f"RAG connection failed: {str(e)[:100]}"
        )

    # Check reranking
    reranking_enabled = get_reranking_enabled()
    reranking_model_installed = False

    if not reranking_enabled:
        try:
            import sentence_transformers  # type: ignore # noqa: F401

            cache_dir = get_data_dir() / "models"
            model_path = cache_dir / "cross-encoder_ms-marco-MiniLM-L-6-v2"

            if model_path.exists():
                reranking_model_installed = True
                recommendations.append(
                    "Reranking model installed but not enabled. "
                    "Set: export KAGURA_ENABLE_RERANKING=true"
                )
            else:
                recommendations.append(
                    "Reranking not available. Install: kagura memory setup --reranking"
                )
        except ImportError:
            recommendations.append(
                "sentence-transformers not installed (required for reranking)"
            )
        except RuntimeError as e:
            error_msg = str(e).split("\n")[0]
            recommendations.append(
                f"sentence-transformers load failed: {error_msg}. "
                "Check torchvision compatibility or reinstall dependencies."
            )
    else:
        reranking_model_installed = True

    stats = MemoryStats(
        database_exists=database_exists,
        database_size_mb=database_size_mb,
        persistent_count=persistent_count,
        rag_enabled=rag_enabled,
        rag_count=rag_count,
        reranking_enabled=reranking_enabled,
        reranking_model_installed=reranking_model_installed,
    )

    return stats, recommendations


@router.get("/doctor", response_model=MemoryDoctorResponse)
async def get_memory_doctor(user: dict[str, Any] | None = Depends(get_current_user_optional)) -> MemoryDoctorResponse:
    """Get memory system health check.

    Returns comprehensive memory system diagnostics including:
    - Database status and size
    - Persistent memory count
    - RAG (vector database) status and count
    - Reranking model status

    Note: Working memory (RAM) has been removed in v4.4.0.

    Args:
        user: Authenticated user (dependency)

    Returns:
        Memory system health check results with recommendations

    Example:
        GET /api/v1/memory/doctor
        Response: {
            "stats": {
                "database_exists": true,
                "database_size_mb": 15.2,
                "persistent_count": 1250,
                "rag_enabled": true,
                "rag_count": 1250,
                "reranking_enabled": false,
                "reranking_model_installed": true
            },
            "status": "warning",
            "recommendations": [
                "Reranking model installed but not enabled. Set: export KAGURA_ENABLE_RERANKING=true"
            ]
        }
    """
    stats, recommendations = _check_memory_system()

    # Determine overall status
    status = "ok"
    if not stats.rag_enabled:
        status = "warning"
    elif stats.rag_count == 0 and stats.persistent_count > 0:
        status = "warning"
    elif not stats.database_exists:
        status = "info"

    return MemoryDoctorResponse(
        stats=stats,
        status=status,
        recommendations=recommendations,
    )


@router.post("", response_model=models.MemoryResponse, status_code=201)
async def create_memory(
    request: models.MemoryCreate, memory: MemoryManagerDep
) -> dict[str, Any]:
    """Create a new memory.

    Note: All memories are stored in persistent storage (v4.4.0 removed working memory).

    Args:
        request: Memory creation request
        memory: MemoryManager dependency

    Returns:
        Created memory details

    Raises:
        HTTPException: If memory key already exists
    """
    # Check if memory already exists in persistent storage
    existing = memory.recall(request.key)
    if existing is not None:
        raise HTTPException(
            status_code=409, detail=f"Memory '{request.key}' already exists"
        )

    # Build metadata with standard fields
    full_metadata = build_full_metadata(
        tags=request.tags,
        importance=request.importance,
        user_metadata=request.metadata,
    )

    # Prepare metadata for ChromaDB storage
    chromadb_metadata = prepare_for_chromadb(full_metadata)
    # Persistent memory: use remember() with ChromaDB-compatible metadata
    memory.remember(request.key, request.value, chromadb_metadata)

    return {
        "key": request.key,
        "value": request.value,
        "scope": "persistent",
        "tags": request.tags,
        "importance": request.importance,
        "metadata": request.metadata or {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.get("/{key}", response_model=models.MemoryResponse)
async def get_memory(
    key: Annotated[str, Path(description="Memory key")],
    memory: MemoryManagerDep,
) -> dict[str, Any]:
    """Get memory by key.

    Note: All memories are retrieved from persistent storage (v4.4.0 removed working memory).

    Args:
        key: Memory key
        memory: MemoryManager dependency

    Returns:
        Memory details

    Raises:
        HTTPException: If memory not found
    """
    # Retrieve from persistent memory
    value = memory.recall(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Memory '{key}' not found")

    # Get full memory data from persistent storage
    metadata_dict = {}
    mem_list = memory.search_memory(f"%{key}%", limit=1)
    if mem_list:
        mem_data = mem_list[0]
        metadata_dict = mem_data.get("metadata", {})

    # Decode and extract metadata fields
    metadata_dict = decode_chromadb_metadata(metadata_dict)
    mem_fields = extract_memory_fields(metadata_dict)

    return {
        "key": key,
        "value": value,
        "scope": "persistent",
        "tags": mem_fields["tags"],
        "importance": mem_fields["importance"],
        "metadata": mem_fields.get("user_metadata", {}),
        "created_at": datetime.fromisoformat(mem_fields["created_at"])
        if mem_fields["created_at"]
        else datetime.now(),
        "updated_at": datetime.fromisoformat(mem_fields["updated_at"])
        if mem_fields["updated_at"]
        else datetime.now(),
    }


@router.put("/{key}", response_model=models.MemoryResponse)
async def update_memory(
    key: Annotated[str, Path(description="Memory key")],
    request: models.MemoryUpdate,
    memory: MemoryManagerDep,
) -> dict[str, Any]:
    """Update memory.

    Note: All memories are updated in persistent storage (v4.4.0 removed working memory).

    Args:
        key: Memory key
        request: Memory update request
        memory: MemoryManager dependency

    Returns:
        Updated memory details

    Raises:
        HTTPException: If memory not found
    """
    # Get existing memory
    try:
        existing = await get_memory(key, memory)
    except HTTPException as e:
        raise e

    # Update fields
    updated_value = request.value if request.value is not None else existing["value"]
    updated_tags = request.tags if request.tags is not None else existing["tags"]
    updated_importance = (
        request.importance if request.importance is not None else existing["importance"]
    )
    updated_metadata = (
        request.metadata if request.metadata is not None else existing["metadata"]
    )

    # Build updated metadata
    full_metadata = build_full_metadata(
        tags=updated_tags,
        importance=updated_importance,
        user_metadata=updated_metadata,
        created_at=existing["created_at"],
        updated_at=datetime.now(),
    )

    # Prepare metadata for ChromaDB storage
    chromadb_metadata = prepare_for_chromadb(full_metadata)
    # Delete and recreate (no update method in MemoryManager)
    memory.forget(key)
    memory.remember(key, updated_value, chromadb_metadata)

    return {
        "key": key,
        "value": updated_value,
        "scope": "persistent",
        "tags": updated_tags,
        "importance": updated_importance,
        "metadata": updated_metadata,
        "created_at": existing["created_at"],
        "updated_at": datetime.now(),
    }


@router.delete("/{key}", status_code=204)
async def delete_memory(
    key: Annotated[str, Path(description="Memory key")],
    memory: MemoryManagerDep,
) -> None:
    """Delete memory.

    Note: All memories are deleted from persistent storage (v4.4.0 removed working memory).

    Args:
        key: Memory key
        memory: MemoryManager dependency

    Raises:
        HTTPException: If memory not found
    """
    # Delete from persistent memory
    existing = memory.recall(key)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Memory '{key}' not found")

    memory.forget(key)


@router.get("", response_model=models.MemoryListResponse)
async def list_memories(
    memory: MemoryManagerDep,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
) -> dict[str, Any]:
    """List memories with pagination.

    Note: All memories are retrieved from persistent storage (v4.4.0 removed working memory).

    Args:
        memory: MemoryManager dependency
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of memories
    """
    all_memories: list[dict[str, Any]] = []

    # Collect persistent memory
    # Search all persistent memories across all users (admin view)
    # Use direct backend access to bypass user_id filtering
    persistent_list = memory.persistent.fetch_all(
        user_id="",  # Empty string to get all users in SQLite
        agent_name=None,
        limit=1000
    ) if hasattr(memory.persistent, 'fetch_all') else []

    logger.info(
        f"[list_memories] fetch_all returned {len(persistent_list)} records "
        f"(user_id='', agent_name=None)"
    )

    # Fallback: if fetch_all doesn't work, use search with current user
    if not persistent_list:
        persistent_list = memory.search_memory("%", limit=1000)
        logger.info(f"[list_memories] search fallback returned {len(persistent_list)} records")

    for mem in persistent_list:
        key = mem.get("key", "")
        agent_name = mem.get("agent_name")

        # Skip coding memories (they have their own endpoint)
        # Filter by agent_name (primary) and key pattern (fallback for old data)
        if agent_name == "coding-memory":
            continue

        # Fallback: Skip coding-related keys for old data without agent_name
        if key.startswith("project:") and any(x in key for x in [":session:", ":error:", ":file_change:", ":decision:"]):
            logger.debug(f"[list_memories] Skipping coding key (fallback): {key}")
            continue

        metadata_dict = mem.get("metadata", {})

        # Handle None metadata (can occur with coding sessions)
        if metadata_dict is None:
            metadata_dict = {}

        # Decode and extract metadata fields
        metadata_dict = decode_chromadb_metadata(metadata_dict)
        mem_fields = extract_memory_fields(metadata_dict)

        # Convert dict values to JSON string (coding sessions store dict)
        value = mem["value"]
        if isinstance(value, dict):
            import json
            value = json.dumps(value, ensure_ascii=False)

        all_memories.append(
            {
                "key": mem["key"],
                "value": value,
                "scope": "persistent",
                "tags": mem_fields["tags"],
                "importance": mem_fields["importance"],
                "metadata": mem_fields.get("user_metadata", {}),
                "created_at": datetime.fromisoformat(mem_fields["created_at"])
                if mem_fields["created_at"]
                else datetime.now(),
                "updated_at": datetime.fromisoformat(mem_fields["updated_at"])
                if mem_fields["updated_at"]
                else datetime.now(),
                "user_id": mem.get("user_id"),
                "agent_name": mem.get("agent_name"),
            }
        )

    total = len(all_memories)

    logger.info(
        f"[list_memories] After filtering: {total} memories "
        f"(page={page}, page_size={page_size})"
    )

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    page_memories = all_memories[start:end]

    logger.info(
        f"[list_memories] Returning {len(page_memories)}/{total} memories"
    )

    return {
        "memories": page_memories,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============================================================================
# Bulk Operations (Issue #666 - Phase 2)
# ============================================================================


@router.post("/bulk-delete", response_model=models.BulkDeleteResponse)
async def bulk_delete_memories(
    request: models.BulkDeleteRequest,
    memory: MemoryManagerDep,
    user: dict[str, Any] = Depends(get_current_user),
) -> models.BulkDeleteResponse:
    """Delete multiple memories at once.

    Performs bulk deletion of memories. Returns count of successful
    deletions and list of failed keys with error messages.

    Note: All memories are deleted from persistent storage (v4.4.0 removed working memory).

    Args:
        request: Bulk delete request with keys list
        memory: MemoryManager dependency
        user: Authenticated user (dependency)

    Returns:
        Deletion results

    Example:
        POST /api/v1/memory/bulk-delete
        Body: {
            "keys": ["key1", "key2", "key3"],
            "agent_name": "global"
        }
        Response: {
            "deleted_count": 2,
            "failed_keys": ["key3"],
            "errors": {
                "key3": "Memory not found"
            }
        }
    """
    deleted_count = 0
    failed_keys = []
    errors = {}

    for key in request.keys:
        try:
            # Delete from persistent memory
            existing = memory.recall(key)
            if existing is not None:
                memory.forget(key)
                deleted_count += 1
            else:
                failed_keys.append(key)
                errors[key] = "Memory not found in persistent storage"

        except Exception as e:
            logger.error(f"Failed to delete memory {key}: {e}")
            failed_keys.append(key)
            errors[key] = str(e)

    return models.BulkDeleteResponse(
        deleted_count=deleted_count,
        failed_keys=failed_keys,
        errors=errors,
    )
