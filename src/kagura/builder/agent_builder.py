"""AgentBuilder - Fluent API for building agents with integrated features."""

from pathlib import Path
from typing import Any, Callable, Optional

from .config import AgentConfiguration, HooksConfig, MemoryConfig, RoutingConfig


class AgentBuilder:
    """Fluent API for building agents with integrated features.

    Example:
        >>> from kagura import AgentBuilder
        >>> agent = (
        ...     AgentBuilder("my_agent")
        ...     .with_model("gpt-4o-mini")
        ...     .with_memory(type="rag", persist=True)
        ...     .with_tools([search_tool, calc_tool])
        ...     .build()
        ... )
    """

    def __init__(self, name: str):
        """Initialize AgentBuilder.

        Args:
            name: Agent name
        """
        self.name = name
        self._config = AgentConfiguration(name=name)

    def with_model(self, model: str) -> "AgentBuilder":
        """Set LLM model.

        Args:
            model: Model identifier (e.g., "gpt-4o-mini", "claude-3-sonnet")

        Returns:
            Self for method chaining
        """
        self._config.model = model
        return self

    def with_memory(
        self,
        type: str = "working",
        persist_dir: Optional[Path] = None,
        max_messages: int = 100,
        enable_rag: bool = False,
    ) -> "AgentBuilder":
        """Configure memory system.

        Args:
            type: Memory type - "working", "context", "persistent", "rag"
            persist_dir: Directory for persistent storage
            max_messages: Maximum number of messages to store
            enable_rag: Enable RAG (semantic search) with ChromaDB

        Returns:
            Self for method chaining
        """
        self._config.memory = MemoryConfig(
            type=type,
            persist_dir=persist_dir,
            max_messages=max_messages,
            enable_rag=enable_rag,
        )
        return self

    def with_routing(
        self,
        strategy: str = "semantic",
        routes: Optional[dict] = None,
    ) -> "AgentBuilder":
        """Configure agent routing.

        Args:
            strategy: Routing strategy - "keyword", "llm", "semantic"
            routes: Route definitions mapping route names to agents

        Returns:
            Self for method chaining
        """
        self._config.routing = RoutingConfig(
            strategy=strategy,
            routes=routes or {},
        )
        return self

    def with_tools(self, tools: list[Callable]) -> "AgentBuilder":
        """Add tools to agent.

        Args:
            tools: List of tool functions

        Returns:
            Self for method chaining
        """
        self._config.tools = tools
        return self

    def with_hooks(
        self,
        pre: Optional[list[Callable]] = None,
        post: Optional[list[Callable]] = None,
    ) -> "AgentBuilder":
        """Add pre/post hooks.

        Args:
            pre: Pre-execution hooks
            post: Post-execution hooks

        Returns:
            Self for method chaining
        """
        self._config.hooks = HooksConfig(
            pre=pre or [],
            post=post or [],
        )
        return self

    def with_context(self, **kwargs: Any) -> "AgentBuilder":
        """Set LLM generation parameters.

        Args:
            **kwargs: Context parameters (temperature, max_tokens, etc.)

        Returns:
            Self for method chaining
        """
        self._config.context.update(kwargs)
        return self

    def build(self) -> Callable:
        """Build the final agent.

        Returns:
            Callable agent function

        Raises:
            ValueError: If configuration is invalid
        """
        return self._build_agent()

    def _build_agent(self) -> Callable:
        """Internal: construct the agent with all features.

        Returns:
            Enhanced agent callable
        """
        from kagura import agent

        # Store config for closure
        config = self._config

        # Build base agent with integrated features
        @agent(model=config.model, **config.context)
        async def enhanced_agent(prompt: str, **kwargs: Any) -> str:
            """Enhanced agent with integrated features.

            Args:
                prompt: User prompt
                **kwargs: Additional arguments

            Returns:
                Agent response
            """
            # Note: Full integration of memory, routing, tools will be
            # implemented in subsequent phases. For now, we return
            # the base agent behavior.

            # TODO: Phase 1 - Integrate memory
            # TODO: Phase 1 - Integrate tools
            # TODO: Phase 2 - Integrate routing
            # TODO: Phase 2 - Integrate hooks

            # Placeholder: return prompt template
            return f"Process: {prompt}"

        # Attach metadata
        enhanced_agent._builder_config = config  # type: ignore
        enhanced_agent._agent_name = config.name  # type: ignore

        return enhanced_agent

    def __repr__(self) -> str:
        """String representation.

        Returns:
            Builder description
        """
        return f"AgentBuilder(name='{self.name}', model='{self._config.model}')"
