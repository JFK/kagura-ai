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
    """Create memory request.

    Note: v4.4.0 removed working memory - all memories are now persistent.
    """

    key: str = Field(..., description="Unique memory key")
    value: str = Field(..., description="Memory content")
    type: Literal["normal", "coding"] = Field(
        default="normal", description="Memory type: normal or coding session"
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
    type: Literal["normal", "coding"] | None = Field(None, description="Updated memory type")
    tags: list[str] | None = Field(None, description="Updated tags")
    importance: float | None = Field(
        None, ge=0.0, le=1.0, description="Updated importance"
    )
    metadata: dict[str, Any] | None = Field(None, description="Updated metadata")


class MemoryResponse(BaseModel):
    """Memory response.

    Note: v4.4.0 removed working memory - scope is always "persistent".
    """

    key: str
    value: str
    scope: str = "persistent"  # Always persistent in v4.4.0+
    type: str = "normal"
    tags: list[str]
    importance: float
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    user_id: str | None = None
    agent_name: str | None = None


class MemoryListResponse(BaseModel):
    """List of memories response."""

    memories: list[MemoryResponse]
    total: int
    page: int
    page_size: int


# Search
class SearchRequest(BaseModel):
    """Search memories request.

    Note: v4.4.0 removed working memory - all searches are in persistent storage.
    """

    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    filter_tags: list[str] | None = Field(
        None, description="Filter by tags (AND logic)"
    )


class SearchResult(BaseModel):
    """Single search result.

    Note: v4.4.0 removed working memory - scope is always "persistent".
    """

    key: str
    value: str
    scope: str = "persistent"  # Always persistent in v4.4.0+
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
    """Recall memories request (semantic similarity).

    Note: v4.4.0 removed working memory - all searches are in persistent storage.
    """

    query: str = Field(..., description="Query text for semantic search")
    k: int = Field(default=5, ge=1, le=50, description="Number of results")
    include_graph: bool = Field(
        default=False, description="Include graph-related memories (v4.0.0+)"
    )


class RecallResult(BaseModel):
    """Single recall result.

    Note: v4.4.0 removed working memory - scope is always "persistent".
    """

    key: str
    value: str
    scope: str = "persistent"  # Always persistent in v4.4.0+
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


# Graph Memory (Issue #345)
class InteractionCreate(BaseModel):
    """Create AI-User interaction request."""

    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="User's query")
    response: str = Field(..., description="AI's response")
    ai_platform: str | None = Field(
        None, description="(Optional) AI platform (claude, chatgpt, etc.)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class InteractionResponse(BaseModel):
    """Interaction creation response."""

    interaction_id: str
    user_id: str
    ai_platform: str
    message: str


class RelatedNodesRequest(BaseModel):
    """Get related nodes request."""

    depth: int = Field(default=2, ge=1, le=5, description="Traversal depth")
    rel_type: str | None = Field(
        None,
        description=(
            "Filter by relationship type "
            "(related_to, depends_on, learned_from, influences, works_on)"
        ),
    )


class GraphNode(BaseModel):
    """Graph node representation."""

    id: str
    type: str
    data: dict[str, Any] = Field(default_factory=dict)


class RelatedNodesResponse(BaseModel):
    """Related nodes response."""

    node_id: str
    depth: int
    rel_type: str | None
    related_count: int
    related_nodes: list[GraphNode]


class UserPattern(BaseModel):
    """User interaction pattern analysis."""

    total_interactions: int
    topics: list[str]
    avg_interactions_per_topic: float
    most_discussed_topic: str | None
    platforms: dict[str, int]


class UserPatternResponse(BaseModel):
    """User pattern analysis response."""

    user_id: str
    pattern: UserPattern


# Coding Sessions (Issue #666 - Phase 2)
class FileChange(BaseModel):
    """File change in coding session."""

    file_path: str = Field(..., description="Path to changed file")
    action: str = Field(..., description="Action: create, edit, delete, rename, refactor")
    diff: str | None = Field(None, description="Change summary")
    reason: str | None = Field(None, description="Reason for change")
    line_range: str | None = Field(None, description="Line range affected (e.g., '10,50')")


class Decision(BaseModel):
    """Design decision in coding session."""

    decision: str = Field(..., description="Decision statement")
    rationale: str = Field(..., description="Reasoning behind decision")
    alternatives: list[str] = Field(default_factory=list, description="Other options considered")
    impact: str | None = Field(None, description="Expected impact")
    tags: list[str] = Field(default_factory=list, description="Tags")


class ErrorRecord(BaseModel):
    """Error record in coding session."""

    error_type: str = Field(..., description="Error classification")
    message: str = Field(..., description="Error message")
    file_path: str | None = Field(None, description="File where error occurred")
    line_number: int | None = Field(None, description="Line number")
    solution: str | None = Field(None, description="How error was resolved")


class SessionSummary(BaseModel):
    """Coding session summary."""

    id: str = Field(..., description="Session ID")
    project_id: str = Field(..., description="Project identifier")
    description: str = Field(..., description="Session description")
    start_time: datetime = Field(..., description="Session start time")
    end_time: datetime | None = Field(None, description="Session end time")
    duration_seconds: int | None = Field(None, description="Duration in seconds")
    file_changes_count: int = Field(0, description="Number of file changes")
    decisions_count: int = Field(0, description="Number of decisions")
    errors_count: int = Field(0, description="Number of errors")
    github_issue: int | None = Field(None, description="Linked GitHub issue number")
    success: bool | None = Field(None, description="Whether session was successful")


class SessionDetailResponse(BaseModel):
    """Coding session detail response."""

    session: SessionSummary = Field(..., description="Session summary")
    file_changes: list[FileChange] = Field(default_factory=list, description="File changes")
    decisions: list[Decision] = Field(default_factory=list, description="Design decisions")
    errors: list[ErrorRecord] = Field(default_factory=list, description="Errors encountered")


class SessionListResponse(BaseModel):
    """Coding sessions list response."""

    sessions: list[SessionSummary] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")


# Bulk Operations (Issue #666 - Phase 2)
class BulkDeleteRequest(BaseModel):
    """Bulk delete memories request.

    Note: v4.4.0 removed working memory - all deletions are from persistent storage.
    """

    keys: list[str] = Field(..., description="List of memory keys to delete")
    agent_name: str = Field(default="global", description="Agent name")


class BulkDeleteResponse(BaseModel):
    """Bulk delete memories response."""

    deleted_count: int = Field(..., description="Number of successfully deleted memories")
    failed_keys: list[str] = Field(default_factory=list, description="Keys that failed to delete")
    errors: dict[str, str] = Field(
        default_factory=dict, description="Error messages for failed keys"
    )


# Error
class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    status_code: int
    detail: str | None = None


# ============================================================================
# Issue #720: New search models for MCP tools integration
# ============================================================================


class SemanticSearchRequest(BaseModel):
    """Request for semantic (RAG/vector) search."""

    query: str = Field(..., min_length=1, description="Search query (natural language)")
    k: int = Field(5, ge=1, le=100, description="Number of results")
    agent_name: str = Field("global", description="Agent identifier")


class KeywordSearchRequest(BaseModel):
    """Request for keyword (BM25) search."""

    query: str = Field(..., min_length=1, description="Search keywords")
    k: int = Field(5, ge=1, le=100, description="Number of results")
    agent_name: str = Field("global", description="Agent identifier")


class TimelineSearchRequest(BaseModel):
    """Request for timeline search."""

    time_range: str = Field(..., description="Time range: last_24h, last_week, YYYY-MM-DD, etc.")
    event_type: str | None = Field(None, description="Optional event type filter")
    k: int = Field(20, ge=1, le=1000, description="Number of results")
    agent_name: str = Field("global", description="Agent identifier")


class SearchResultMemory(BaseModel):
    """Memory with search score."""

    key: str
    content: str
    score: float = Field(..., description="Relevance score (RAG similarity or BM25 score)")
    agent_name: str
    metadata: dict[str, Any] | None = None


class SearchResultsResponse(BaseModel):
    """Response for all search types."""

    memories: list[SearchResultMemory]
    total: int
    search_mode: str = Field(..., description="semantic, keyword, or timeline")
    query_info: dict[str, Any] | None = Field(None, description="Query metadata")
