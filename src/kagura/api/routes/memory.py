"""Memory CRUD endpoints.

Memory management API routes:
- POST /api/v1/memory - Create memory
- GET /api/v1/memory/{key} - Get memory
- PUT /api/v1/memory/{key} - Update memory
- DELETE /api/v1/memory/{key} - Delete memory
- GET /api/v1/memory - List memories
- GET /api/v1/memory/doctor - Memory system health check (Issue #664)
"""

from datetime import datetime
from pathlib import Path as FilePath
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from kagura.api import models
from kagura.api.dependencies import MemoryManagerDep, get_current_user
from kagura.api.models_doctor import MemoryDoctorResponse, MemoryStats
from kagura.config.paths import get_cache_dir, get_data_dir
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

    # Check RAG
    try:
        import chromadb

        rag_count = 0
        vector_db_paths = [
            get_cache_dir() / "chromadb",  # Default CLI location
            get_data_dir() / "chromadb",  # Alternative location
        ]

        for vdb_path in vector_db_paths:
            if vdb_path.exists():
                try:
                    client = chromadb.PersistentClient(path=str(vdb_path))
                    for col in client.list_collections():
                        rag_count += col.count()
                except Exception:
                    pass

        rag_enabled = True

        if rag_count == 0 and persistent_count > 0:
            recommendations.append(
                "RAG index is empty but memories exist. "
                "Run 'kagura memory index' to build index"
            )

    except ImportError:
        recommendations.append(
            "RAG not available. Install: pip install chromadb sentence-transformers"
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
async def get_memory_doctor(user: dict[str, Any] = Depends(get_current_user)) -> MemoryDoctorResponse:
    """Get memory system health check.

    Returns comprehensive memory system diagnostics including:
    - Database status and size
    - Persistent memory count
    - RAG (vector database) status and count
    - Reranking model status

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

    Args:
        request: Memory creation request
        memory: MemoryManager dependency

    Returns:
        Created memory details

    Raises:
        HTTPException: If memory key already exists
    """
    # Check if memory already exists
    if request.scope == "working":
        if memory.has_temp(request.key):
            raise HTTPException(
                status_code=409, detail=f"Memory '{request.key}' already exists"
            )
    else:  # persistent
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

    # Store memory based on scope
    if request.scope == "working":
        # Working memory: store value directly
        memory.set_temp(request.key, request.value)
        # Store metadata separately
        memory.set_temp(f"_meta_{request.key}", full_metadata)
    else:  # persistent
        # Prepare metadata for ChromaDB storage
        chromadb_metadata = prepare_for_chromadb(full_metadata)
        # Persistent memory: use remember() with ChromaDB-compatible metadata
        memory.remember(request.key, request.value, chromadb_metadata)

    return {
        "key": request.key,
        "value": request.value,
        "scope": request.scope,
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
    scope: Annotated[str | None, Query(description="Memory scope")] = None,
) -> dict[str, Any]:
    """Get memory by key.

    Args:
        key: Memory key
        memory: MemoryManager dependency
        scope: Optional scope hint (working/persistent)

    Returns:
        Memory details

    Raises:
        HTTPException: If memory not found
    """
    # Try to find memory in both scopes if not specified
    value = None
    found_scope = None
    metadata_dict = {}

    if scope is None or scope == "working":
        # Try working memory first
        value = memory.get_temp(key)
        if value is not None:
            found_scope = "working"
            metadata_dict = memory.get_temp(f"_meta_{key}", {})

    if value is None and (scope is None or scope == "persistent"):
        # Try persistent memory
        value = memory.recall(key)
        if value is not None:
            found_scope = "persistent"
            # Get full memory data from persistent storage
            mem_list = memory.search_memory(f"%{key}%", limit=1)
            if mem_list:
                mem_data = mem_list[0]
                metadata_dict = mem_data.get("metadata", {})

    if value is None:
        raise HTTPException(status_code=404, detail=f"Memory '{key}' not found")

    # Decode and extract metadata fields
    metadata_dict = decode_chromadb_metadata(metadata_dict)
    mem_fields = extract_memory_fields(metadata_dict)

    return {
        "key": key,
        "value": value,
        "scope": found_scope or "working",
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
    scope: Annotated[str | None, Query(description="Memory scope")] = None,
) -> dict[str, Any]:
    """Update memory.

    Args:
        key: Memory key
        request: Memory update request
        memory: MemoryManager dependency
        scope: Optional scope hint (working/persistent)

    Returns:
        Updated memory details

    Raises:
        HTTPException: If memory not found
    """
    # Get existing memory
    try:
        existing = await get_memory(key, memory, scope)
    except HTTPException as e:
        raise e

    found_scope = existing["scope"]

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

    # Update memory based on scope
    if found_scope == "working":
        memory.set_temp(key, updated_value)
        memory.set_temp(f"_meta_{key}", full_metadata)
    else:  # persistent
        # Prepare metadata for ChromaDB storage
        chromadb_metadata = prepare_for_chromadb(full_metadata)
        # Delete and recreate (no update method in MemoryManager)
        memory.forget(key)
        memory.remember(key, updated_value, chromadb_metadata)

    return {
        "key": key,
        "value": updated_value,
        "scope": found_scope,
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
    scope: Annotated[str | None, Query(description="Memory scope")] = None,
) -> None:
    """Delete memory.

    Args:
        key: Memory key
        memory: MemoryManager dependency
        scope: Optional scope hint (working/persistent)

    Raises:
        HTTPException: If memory not found
    """
    deleted = False

    if scope is None or scope == "working":
        # Try working memory
        if memory.has_temp(key):
            memory.delete_temp(key)
            memory.delete_temp(f"_meta_{key}")  # Delete metadata
            deleted = True

    if not deleted and (scope is None or scope == "persistent"):
        # Try persistent memory
        existing = memory.recall(key)
        if existing is not None:
            memory.forget(key)
            deleted = True

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory '{key}' not found")


@router.get("", response_model=models.MemoryListResponse)
async def list_memories(
    memory: MemoryManagerDep,
    scope: Annotated[str | None, Query(description="Filter by scope")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
) -> dict[str, Any]:
    """List memories with pagination.

    Args:
        memory: MemoryManager dependency
        scope: Optional scope filter
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of memories
    """
    all_memories: list[dict[str, Any]] = []

    # Collect working memory
    if scope is None or scope == "working":
        # Working memory doesn't have list API, skip for now
        # TODO: Add list capability to WorkingMemory
        pass

    # Collect persistent memory
    if scope is None or scope == "persistent":
        # Search all persistent memories (LIKE '%')
        persistent_list = memory.search_memory("%", limit=1000)
        for mem in persistent_list:
            metadata_dict = mem.get("metadata", {})

            # Decode and extract metadata fields
            metadata_dict = decode_chromadb_metadata(metadata_dict)
            mem_fields = extract_memory_fields(metadata_dict)

            all_memories.append(
                {
                    "key": mem["key"],
                    "value": mem["value"],
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
            )

    total = len(all_memories)

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    page_memories = all_memories[start:end]

    return {
        "memories": page_memories,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
