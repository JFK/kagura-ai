"""Pydantic models for doctor API responses.

Models for system health check responses from doctor endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# System Doctor Models
class DependencyCheck(BaseModel):
    """Dependency check result."""

    name: str = Field(..., description="Package name")
    status: str = Field(..., description="Status: ok, warning, or error")
    message: str = Field(..., description="Status message with version or error")


class SystemCheck(BaseModel):
    """System requirement check."""

    status: str = Field(..., description="Status: ok, warning, or error")
    message: str = Field(..., description="Status message")


class APICheck(BaseModel):
    """API configuration check."""

    provider: str = Field(..., description="Provider name (e.g., OpenAI, Anthropic)")
    status: str = Field(..., description="Status: ok, warning, or error")
    message: str = Field(..., description="Status message")


class SystemDoctorResponse(BaseModel):
    """System doctor API response (Issue #668: Enhanced with backend checks, #707: GraphDB stats)."""

    python_version: SystemCheck = Field(..., description="Python version check")
    disk_space: SystemCheck = Field(..., description="Disk space check")
    dependencies: list[DependencyCheck] = Field(..., description="Dependency checks")

    # Backend Services (Issue #668, #707)
    postgres: SystemCheck = Field(..., description="PostgreSQL database connectivity")
    redis: SystemCheck = Field(..., description="Redis cache connectivity")
    qdrant: SystemCheck = Field(..., description="Qdrant vector database connectivity")
    graph_db: SystemCheck | None = Field(None, description="GraphDB status and statistics (Issue #707)")

    # API Configuration
    api_configuration: list[APICheck] = Field(..., description="API configuration checks")

    # Remote MCP (Issue #668)
    remote_mcp: SystemCheck = Field(..., description="Remote MCP server status")

    overall_status: str = Field(..., description="Overall status: ok, warning, or error")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations for improvement")


# Memory Doctor Models
class MemoryStats(BaseModel):
    """Memory system statistics.

    Note: v4.4.0 removed working memory - only persistent storage is tracked.
    """

    database_exists: bool = Field(..., description="Whether database exists")
    database_size_mb: float | None = Field(None, description="Database size in MB")
    persistent_count: int = Field(0, description="Number of persistent memories")
    rag_enabled: bool = Field(False, description="Whether RAG is enabled")
    rag_count: int = Field(0, description="Number of RAG vectors")
    reranking_enabled: bool = Field(False, description="Whether reranking is enabled")
    reranking_model_installed: bool = Field(False, description="Whether reranking model is installed")


class MemoryDoctorResponse(BaseModel):
    """Memory doctor API response."""

    stats: MemoryStats = Field(..., description="Memory system statistics")
    status: str = Field(..., description="Overall status: ok, warning, or error")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations for improvement")


# Coding Doctor Models
class CodingStats(BaseModel):
    """Coding memory statistics."""

    sessions_count: int = Field(0, description="Number of coding sessions")
    projects_count: int = Field(0, description="Number of tracked projects")


class CodingDoctorResponse(BaseModel):
    """Coding doctor API response."""

    stats: CodingStats = Field(..., description="Coding memory statistics")
    status: str = Field(..., description="Overall status: ok or info")


# Unified Doctor Response (optional, for combining all checks)
class UnifiedDoctorResponse(BaseModel):
    """Combined doctor response with all checks."""

    system: SystemDoctorResponse = Field(..., description="System health checks")
    memory: MemoryDoctorResponse = Field(..., description="Memory system health")
    coding: CodingDoctorResponse = Field(..., description="Coding memory health")
    overall_status: str = Field(..., description="Overall status across all systems")
