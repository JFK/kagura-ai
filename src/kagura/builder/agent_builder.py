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
        ...     .with_model("gpt-5-mini")
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
            model: Model identifier (e.g., "gpt-5-mini", "claude-3-sonnet")

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

    def with_session_id(self, session_id: str) -> "AgentBuilder":
        """Set session ID for memory isolation.

        Session IDs allow multiple isolated conversation contexts for the same agent.
        Each session maintains its own memory state.

        Args:
            session_id: Unique identifier for this conversation session

        Returns:
            Self for method chaining

        Raises:
            ValueError: If memory is not configured before setting session_id

        Example:
            >>> agent = (
            ...     AgentBuilder("chatbot")
            ...     .with_memory(type="persistent")
            ...     .with_session_id("user_123_session_1")
            ...     .build()
            ... )
        """
        if self._config.memory is None:
            raise ValueError(
                "Memory must be configured before setting session_id. "
                "Call .with_memory() first."
            )
        self._config.memory.session_id = session_id
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
        from kagura.core.memory import MemoryManager

        # Store config for closure
        config = self._config

        # Prepare decorator arguments
        agent_kwargs: dict[str, Any] = {
            "model": config.model,
            **config.context,
        }

        # Add memory configuration
        if config.memory:
            agent_kwargs["enable_memory"] = True
            if config.memory.persist_dir:
                agent_kwargs["persist_dir"] = config.memory.persist_dir
            agent_kwargs["max_messages"] = config.memory.max_messages

        # Add tools
        if config.tools:
            agent_kwargs["tools"] = config.tools

        # Build agent with memory parameter if memory is enabled
        enhanced_agent: Callable
        if config.memory:

            @agent(**agent_kwargs)
            async def _agent_with_memory(
                prompt: str, memory: MemoryManager, **kwargs: Any
            ) -> str:
                """Enhanced agent with memory and tools.

                Args:
                    prompt: User prompt
                    memory: Memory manager
                    **kwargs: Additional arguments

                Returns:
                    Agent response
                """
                # Set session ID if configured
                if config.memory and config.memory.session_id:
                    memory.set_session_id(config.memory.session_id)

                # TODO: Phase 2 - Integrate routing
                # TODO: Phase 2 - Integrate hooks

                # Process prompt - actual LLM call handled by @agent decorator
                return f"{prompt}"

            enhanced_agent = _agent_with_memory

        else:

            @agent(**agent_kwargs)
            async def _agent_no_memory(prompt: str, **kwargs: Any) -> str:
                """Enhanced agent with tools (no memory).

                Args:
                    prompt: User prompt
                    **kwargs: Additional arguments

                Returns:
                    Agent response
                """
                # TODO: Phase 2 - Integrate routing
                # TODO: Phase 2 - Integrate hooks

                # Process prompt - actual LLM call handled by @agent decorator
                return f"{prompt}"

            enhanced_agent = _agent_no_memory

        # Wrap with hooks if configured
        if config.hooks and (config.hooks.pre or config.hooks.post):
            base_agent = enhanced_agent

            async def hooked_agent(*args: Any, **kwargs: Any) -> Any:
                """Agent wrapper with pre/post hooks."""
                # Run pre-hooks
                if config.hooks:
                    for hook in config.hooks.pre:
                        result = hook(*args, **kwargs)
                        # Support both sync and async hooks
                        if hasattr(result, "__await__"):
                            await result

                # Run agent
                agent_result = await base_agent(*args, **kwargs)

                # Run post-hooks
                if config.hooks:
                    for hook in config.hooks.post:
                        result = hook(agent_result)
                        # Support both sync and async hooks
                        if hasattr(result, "__await__"):
                            await result

                return agent_result

            # Copy metadata from base agent
            hooked_agent._builder_config = config  # type: ignore
            hooked_agent._agent_name = config.name  # type: ignore
            hooked_agent._base_agent = base_agent  # type: ignore

            return hooked_agent

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
