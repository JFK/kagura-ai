"""Pydantic models for Kagura Memory API.

Request/Response schemas for REST API endpoints.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# Root
class RootResponse(BaseModel):
    """Root endpoint response."""

    name: str
    version: str
    status: str
    docs: str
    description: str


# Memory
class MemoryCreate(BaseModel):
    """Create memory request."""

    key: str = Field(..., description="Unique memory key")
    value: str = Field(..., description="Memory content")
    scope: Literal["working", "persistent"] = Field(
        default="working", description="Memory scope"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    importance: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Importance score (0-1)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MemoryUpdate(BaseModel):
    """Update memory request."""

    value: str | None = Field(None, description="Updated memory content")
    tags: list[str] | None = Field(None, description="Updated tags")
    importance: float | None = Field(
        None, ge=0.0, le=1.0, description="Updated importance"
    )
    metadata: dict[str, Any] | None = Field(None, description="Updated metadata")


class MemoryResponse(BaseModel):
    """Memory response."""

    key: str
    value: str
    scope: str
    tags: list[str]
    importance: float
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MemoryListResponse(BaseModel):
    """List of memories response."""

    memories: list[MemoryResponse]
    total: int
    page: int
    page_size: int


# Search
class SearchRequest(BaseModel):
    """Search memories request."""

    query: str = Field(..., description="Search query")
    scope: Literal["working", "persistent", "all"] = Field(
        default="all", description="Search scope"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    filter_tags: list[str] | None = Field(
        None, description="Filter by tags (AND logic)"
    )


class SearchResult(BaseModel):
    """Single search result."""

    key: str
    value: str
    scope: str
    tags: list[str]
    score: float = Field(..., description="Relevance score")
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    """Search results response."""

    results: list[SearchResult]
    total: int
    query: str


# Recall
class RecallRequest(BaseModel):
    """Recall memories request (semantic similarity)."""

    query: str = Field(..., description="Query text for semantic search")
    k: int = Field(default=5, ge=1, le=50, description="Number of results")
    scope: Literal["working", "persistent", "all"] = Field(
        default="all", description="Search scope"
    )
    include_graph: bool = Field(
        default=False, description="Include graph-related memories (v4.0.0+)"
    )


class RecallResult(BaseModel):
    """Single recall result."""

    key: str
    value: str
    scope: str
    similarity: float = Field(..., description="Semantic similarity score (0-1)")
    tags: list[str]
    metadata: dict[str, Any]


class RecallResponse(BaseModel):
    """Recall results response."""

    results: list[RecallResult]
    query: str
    k: int


# System
class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    services: dict[str, str] = Field(
        ..., description="Service statuses (api, database, cache, etc.)"
    )


class MetricsResponse(BaseModel):
    """System metrics response."""

    memory_count: int
    storage_size_mb: float
    cache_hit_rate: float | None
    api_requests_total: int | None
    uptime_seconds: float


# Error
class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    status_code: int
    detail: str | None = None
