"""Memory CRUD endpoints.

Memory management API routes:
- POST /api/v1/memory - Create memory
- GET /api/v1/memory/{key} - Get memory
- PUT /api/v1/memory/{key} - Update memory
- DELETE /api/v1/memory/{key} - Delete memory
- GET /api/v1/memory - List memories
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from kagura.api import models

# TODO: Import MemoryManager once integrated
# from kagura.core.memory import MemoryManager

router = APIRouter()


# Placeholder: Memory storage (will be replaced with MemoryManager)
_MEMORY_STORE: dict[str, dict] = {}


@router.post("", response_model=models.MemoryResponse, status_code=201)
async def create_memory(request: models.MemoryCreate) -> dict:
    """Create a new memory.

    Args:
        request: Memory creation request

    Returns:
        Created memory details

    Raises:
        HTTPException: If memory key already exists
    """
    if request.key in _MEMORY_STORE:
        raise HTTPException(status_code=409, detail=f"Memory '{request.key}' already exists")

    now = datetime.now()
    memory = {
        "key": request.key,
        "value": request.value,
        "scope": request.scope,
        "tags": request.tags,
        "importance": request.importance,
        "metadata": request.metadata,
        "created_at": now,
        "updated_at": now,
    }

    _MEMORY_STORE[request.key] = memory

    # TODO: Integrate with MemoryManager
    # manager = MemoryManager()
    # await manager.store(
    #     key=request.key,
    #     value=request.value,
    #     scope=request.scope,
    #     tags=request.tags,
    #     importance=request.importance,
    #     metadata=request.metadata,
    # )

    return memory


@router.get("/{key}", response_model=models.MemoryResponse)
async def get_memory(
    key: Annotated[str, Path(description="Memory key")]
) -> dict:
    """Get memory by key.

    Args:
        key: Memory key

    Returns:
        Memory details

    Raises:
        HTTPException: If memory not found
    """
    if key not in _MEMORY_STORE:
        raise HTTPException(status_code=404, detail=f"Memory '{key}' not found")

    return _MEMORY_STORE[key]


@router.put("/{key}", response_model=models.MemoryResponse)
async def update_memory(
    key: Annotated[str, Path(description="Memory key")],
    request: models.MemoryUpdate,
) -> dict:
    """Update memory.

    Args:
        key: Memory key
        request: Memory update request

    Returns:
        Updated memory details

    Raises:
        HTTPException: If memory not found
    """
    if key not in _MEMORY_STORE:
        raise HTTPException(status_code=404, detail=f"Memory '{key}' not found")

    memory = _MEMORY_STORE[key]

    # Update fields
    if request.value is not None:
        memory["value"] = request.value
    if request.tags is not None:
        memory["tags"] = request.tags
    if request.importance is not None:
        memory["importance"] = request.importance
    if request.metadata is not None:
        memory["metadata"] = request.metadata

    memory["updated_at"] = datetime.now()

    return memory


@router.delete("/{key}", status_code=204)
async def delete_memory(
    key: Annotated[str, Path(description="Memory key")]
) -> None:
    """Delete memory.

    Args:
        key: Memory key

    Raises:
        HTTPException: If memory not found
    """
    if key not in _MEMORY_STORE:
        raise HTTPException(status_code=404, detail=f"Memory '{key}' not found")

    del _MEMORY_STORE[key]

    # TODO: Integrate with MemoryManager
    # manager = MemoryManager()
    # await manager.delete(key)


@router.get("", response_model=models.MemoryListResponse)
async def list_memories(
    scope: Annotated[str | None, Query(description="Filter by scope")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
) -> dict:
    """List memories with pagination.

    Args:
        scope: Optional scope filter
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of memories
    """
    # Filter by scope if provided
    memories = list(_MEMORY_STORE.values())
    if scope:
        memories = [m for m in memories if m["scope"] == scope]

    total = len(memories)

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    page_memories = memories[start:end]

    return {
        "memories": page_memories,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
