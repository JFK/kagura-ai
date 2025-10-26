"""Memory CRUD endpoints.

Memory management API routes:
- POST /api/v1/memory - Create memory
- GET /api/v1/memory/{key} - Get memory
- PUT /api/v1/memory/{key} - Update memory
- DELETE /api/v1/memory/{key} - Delete memory
- GET /api/v1/memory - List memories
"""

import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query

from kagura.api import models
from kagura.api.dependencies import MemoryManagerDep

router = APIRouter()


def _decode_metadata(metadata_dict: dict[str, Any]) -> dict[str, Any]:
    """Decode JSON strings in metadata (ChromaDB compatibility).

    Args:
        metadata_dict: Metadata with potential JSON strings

    Returns:
        Decoded metadata with lists/dicts restored
    """
    decoded = {}
    for k, v in metadata_dict.items():
        if isinstance(v, str) and (v.startswith("[") or v.startswith("{")):
            try:
                decoded[k] = json.loads(v)
            except json.JSONDecodeError:
                decoded[k] = v
        else:
            decoded[k] = v
    return decoded


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

    # Prepare metadata with tags and importance
    now = datetime.now()
    full_metadata = {
        **(request.metadata or {}),
        "tags": request.tags,
        "importance": request.importance,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    # Store memory based on scope
    if request.scope == "working":
        # Working memory: store value directly
        memory.set_temp(request.key, request.value)
        # Store metadata separately
        memory.set_temp(f"_meta_{request.key}", full_metadata)
    else:  # persistent
        # For ChromaDB compatibility, convert list values to JSON strings
        import json

        chromadb_metadata = {}
        for k, v in full_metadata.items():
            if isinstance(v, list):
                chromadb_metadata[k] = json.dumps(v)  # Convert list to JSON string
            elif isinstance(v, dict):
                chromadb_metadata[k] = json.dumps(v)  # Convert dict to JSON string
            else:
                chromadb_metadata[k] = v

        # Persistent memory: use remember() with ChromaDB-compatible metadata
        memory.remember(request.key, request.value, chromadb_metadata)

    return {
        "key": request.key,
        "value": request.value,
        "scope": request.scope,
        "tags": request.tags,
        "importance": request.importance,
        "metadata": request.metadata or {},
        "created_at": now,
        "updated_at": now,
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

    # Decode metadata (ChromaDB compatibility)
    metadata_dict = _decode_metadata(metadata_dict)

    # Extract tags, importance from metadata
    tags = metadata_dict.get("tags", [])
    importance = metadata_dict.get("importance", 0.5)
    created_at_str = metadata_dict.get("created_at")
    updated_at_str = metadata_dict.get("updated_at")

    # Remove internal fields from metadata
    user_metadata = {
        k: v
        for k, v in metadata_dict.items()
        if k not in ("tags", "importance", "created_at", "updated_at")
    }

    return {
        "key": key,
        "value": value,
        "scope": found_scope or "working",
        "tags": tags,
        "importance": importance,
        "metadata": user_metadata,
        "created_at": datetime.fromisoformat(created_at_str)
        if created_at_str
        else datetime.now(),
        "updated_at": datetime.fromisoformat(updated_at_str)
        if updated_at_str
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

    # Prepare updated metadata
    full_metadata = {
        **updated_metadata,
        "tags": updated_tags,
        "importance": updated_importance,
        "created_at": existing["created_at"].isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    # Update memory based on scope
    if found_scope == "working":
        memory.set_temp(key, updated_value)
        memory.set_temp(f"_meta_{key}", full_metadata)
    else:  # persistent
        # For ChromaDB compatibility, convert list/dict values to JSON strings
        import json

        chromadb_metadata = {}
        for k, v in full_metadata.items():
            if isinstance(v, list):
                chromadb_metadata[k] = json.dumps(v)
            elif isinstance(v, dict):
                chromadb_metadata[k] = json.dumps(v)
            else:
                chromadb_metadata[k] = v

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

            # Decode metadata (ChromaDB compatibility)
            metadata_dict = _decode_metadata(metadata_dict)

            tags = metadata_dict.get("tags", [])
            importance = metadata_dict.get("importance", 0.5)
            created_at_str = metadata_dict.get("created_at")
            updated_at_str = metadata_dict.get("updated_at")

            user_metadata = {
                k: v
                for k, v in metadata_dict.items()
                if k not in ("tags", "importance", "created_at", "updated_at")
            }

            all_memories.append(
                {
                    "key": mem["key"],
                    "value": mem["value"],
                    "scope": "persistent",
                    "tags": tags,
                    "importance": importance,
                    "metadata": user_metadata,
                    "created_at": datetime.fromisoformat(created_at_str)
                    if created_at_str
                    else datetime.now(),
                    "updated_at": datetime.fromisoformat(updated_at_str)
                    if updated_at_str
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
