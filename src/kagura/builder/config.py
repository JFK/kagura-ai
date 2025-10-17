"""Configuration classes for AgentBuilder."""

from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import BaseModel, ConfigDict, Field


class MemoryConfig(BaseModel):
    """Memory configuration for agents."""

    type: str = Field(
        default="working",
        description="Memory type: working, context, persistent, rag",
    )
    persist_dir: Optional[Path] = Field(
        default=None, description="Directory for persistent storage"
    )
    max_messages: int = Field(
        default=100, description="Maximum number of messages to store"
    )
    enable_rag: bool = Field(default=False, description="Enable RAG (semantic search)")
    session_id: Optional[str] = Field(
        default=None, description="Session ID for memory isolation"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RoutingConfig(BaseModel):
    """Routing configuration for agents."""

    strategy: str = Field(
        default="semantic",
        description="Routing strategy: keyword, llm, semantic",
    )
    routes: dict[str, Any] = Field(
        default_factory=dict, description="Route definitions"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class HooksConfig(BaseModel):
    """Hooks configuration for agents."""

    pre: list[Callable] = Field(default_factory=list, description="Pre-execution hooks")
    post: list[Callable] = Field(
        default_factory=list, description="Post-execution hooks"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentConfiguration(BaseModel):
    """Complete agent configuration."""

    name: str = Field(description="Agent name")
    model: str = Field(default="gpt-5-mini", description="LLM model to use")
    memory: Optional[MemoryConfig] = Field(
        default=None, description="Memory configuration"
    )
    routing: Optional[RoutingConfig] = Field(
        default=None, description="Routing configuration"
    )
    tools: list[Callable] = Field(
        default_factory=list, description="Tools available to agent"
    )
    hooks: Optional[HooksConfig] = Field(
        default=None, description="Hooks configuration"
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="LLM context parameters"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)
