"""Agent routing system for intelligent agent selection.

This module provides intent-based routing to automatically select
the most appropriate agent based on user input.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from inspect import isawaitable
from typing import Any, Awaitable, Callable, Iterable

from .exceptions import (
    InvalidRouterStrategyError,
    NoAgentFoundError,
)


AgentCallable = Callable[..., Awaitable[Any] | Any]


@dataclass
class RegisteredAgent:
    """Metadata for a registered agent.

    Attributes:
        agent: The agent function
        name: Agent name
        intents: List of intent keywords/patterns (for intent strategy)
        samples: List of sample queries (for semantic strategy)
        description: Agent description
    """

    agent: AgentCallable
    name: str
    intents: Iterable[str] = ()
    samples: Iterable[str] = ()
    description: str = ""
    normalized_intents: tuple[str, ...] = field(init=False)
    intent_word_sets: tuple[frozenset[str], ...] = field(init=False)

    def __post_init__(self) -> None:
        """Normalise data eagerly for faster routing decisions."""

        cleaned_intents = tuple(
            intent.strip() for intent in self.intents if intent and intent.strip()
        )
        cleaned_samples = tuple(
            sample.strip() for sample in self.samples if sample and sample.strip()
        )

        self.intents = cleaned_intents
        self.samples = cleaned_samples
        self.normalized_intents = tuple(intent.lower() for intent in cleaned_intents)
        self.intent_word_sets = tuple(
            frozenset(filter(None, intent.split())) for intent in self.normalized_intents
        )


class AgentRouter:
    """Route user input to appropriate agents using intent-based matching.

    The router uses keyword matching to determine which agent best matches
    the user's input. Agents are registered with intent keywords, and the
    router calculates a confidence score for each agent based on keyword
    matches.

    Example:
        >>> from kagura import agent, AgentRouter
        >>>
        >>> @agent
        >>> async def code_reviewer(code: str) -> str:
        ...     '''Review code: {{ code }}'''
        ...     pass
        >>>
        >>> @agent
        >>> async def translator(text: str, lang: str) -> str:
        ...     '''Translate {{ text }} to {{ lang }}'''
        ...     pass
        >>>
        >>> router = AgentRouter()
        >>> router.register(
        ...     code_reviewer,
        ...     intents=["review", "check", "analyze"],
        ...     description="Reviews code quality"
        ... )
        >>> router.register(
        ...     translator,
        ...     intents=["translate", "翻訳"],
        ...     description="Translates text"
        ... )
        >>>
        >>> # Automatic routing
        >>> result = await router.route("Please review this code")
        >>> # → code_reviewer is automatically selected
    """

    VALID_STRATEGIES = ["intent", "semantic"]

    def __init__(
        self,
        strategy: str = "intent",
        fallback_agent: AgentCallable | None = None,
        confidence_threshold: float = 0.3,
        encoder: str = "openai",
    ) -> None:
        """Initialize agent router.

        Args:
            strategy: Routing strategy ("intent" for keyword matching,
                "semantic" for embedding-based routing)
            fallback_agent: Default agent to use when no match is found
            confidence_threshold: Minimum confidence score (0.0-1.0) required
                for routing. Lower values are more lenient.
            encoder: Encoder to use for semantic routing ("openai" or "cohere")

        Raises:
            InvalidRouterStrategyError: If strategy is not valid
        """
        if strategy not in self.VALID_STRATEGIES:
            raise InvalidRouterStrategyError(strategy, self.VALID_STRATEGIES)

        self.strategy = strategy
        self.fallback_agent = fallback_agent
        self.confidence_threshold = confidence_threshold
        self.encoder_type = encoder
        self._agents: dict[str, RegisteredAgent] = {}
        self._semantic_router: Any | None = None

    def register(
        self,
        agent: AgentCallable,
        intents: list[str] | None = None,
        samples: list[str] | None = None,
        description: str = "",
        name: str | None = None,
    ) -> None:
        """Register an agent with routing patterns.

        Args:
            agent: Agent function to register
            intents: List of intent keywords/patterns for matching.
                Case-insensitive matching is used. (For intent strategy)
            samples: List of sample queries for semantic matching.
                (For semantic strategy)
            description: Human-readable description of the agent
            name: Agent name (defaults to function name)

        Example:
            >>> # Intent-based routing
            >>> router.register(
            ...     code_reviewer,
            ...     intents=["review", "check", "analyze"],
            ...     description="Reviews code for quality and bugs"
            ... )
            >>> # Semantic routing
            >>> router.register(
            ...     code_reviewer,
            ...     samples=["Can you review this code?", "Check my code"],
            ...     description="Reviews code for quality and bugs"
            ... )
        """
        agent_name = name or agent.__name__
        intents = intents or []
        samples = samples or []

        self._agents[agent_name] = RegisteredAgent(
            agent=agent,
            name=agent_name,
            intents=intents,
            samples=samples,
            description=description.strip() if description else "",
        )

        # Reset semantic router to rebuild with new agent
        if self.strategy == "semantic":
            self._semantic_router = None

    async def route(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Route user input to the most appropriate agent.

        Args:
            user_input: User's natural language input
            context: Optional context information (reserved for future use)
            **kwargs: Additional arguments to pass to the selected agent

        Returns:
            Result from executing the selected agent

        Raises:
            NoAgentFoundError: When no suitable agent is found and no
                fallback agent is configured

        Example:
            >>> result = await router.route("Check this code for bugs")
            >>> # Automatically selects and executes code_reviewer
        """
        # Find best matching agent
        matched_agents = self.get_matched_agents(user_input, top_k=1)

        # Check if we have any matches
        if not matched_agents:
            if self.fallback_agent:
                return await self._invoke_agent(self.fallback_agent, user_input, **kwargs)
            raise NoAgentFoundError(
                f"No agent found for input: {user_input!r}",
                user_input=user_input,
            )

        # Get best match
        best_agent, confidence = matched_agents[0]

        # Check confidence threshold
        if confidence < self.confidence_threshold:
            if self.fallback_agent:
                return await self._invoke_agent(self.fallback_agent, user_input, **kwargs)
            raise NoAgentFoundError(
                f"Low confidence ({confidence:.2f}) for input: {user_input!r}. "
                f"Threshold: {self.confidence_threshold}",
                user_input=user_input,
            )

        # Execute the selected agent
        # Note: For Phase 1, we pass user_input as the first argument
        # Future phases may support more sophisticated parameter mapping
        return await self._invoke_agent(best_agent, user_input, **kwargs)

    def get_matched_agents(
        self,
        user_input: str,
        top_k: int = 3,
    ) -> list[tuple[AgentCallable, float]]:
        """Get top-k matched agents with confidence scores.

        Args:
            user_input: User input to match against
            top_k: Number of top matches to return

        Returns:
            List of (agent_function, confidence_score) tuples,
            sorted by confidence (highest first)

        Example:
            >>> matches = router.get_matched_agents("review my code", top_k=3)
            >>> for agent, score in matches:
            ...     print(f"{agent.__name__}: {score:.2f}")
            code_reviewer: 0.67
            general_assistant: 0.33
        """
        if self.strategy == "semantic":
            return self._semantic_matches(user_input, top_k)

        scores: list[tuple[AgentCallable, float]] = []

        for agent_data in self._agents.values():
            score = self._intent_score(user_input, agent_data)
            if score > 0:
                scores.append((agent_data.agent, score))

        scores.sort(key=lambda item: item[1], reverse=True)

        return scores[:top_k]

    def list_agents(self) -> list[str]:
        """List all registered agent names.

        Returns:
            List of registered agent names

        Example:
            >>> router.list_agents()
            ['code_reviewer', 'translator', 'general_assistant']
        """
        return list(self._agents.keys())

    def get_agent_info(self, agent_name: str) -> dict[str, Any]:
        """Get information about a registered agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary containing agent metadata

        Raises:
            AgentNotRegisteredError: If agent is not registered

        Example:
            >>> info = router.get_agent_info("code_reviewer")
            >>> print(info["description"])
            Reviews code for quality and bugs
        """
        from .exceptions import AgentNotRegisteredError

        if agent_name not in self._agents:
            raise AgentNotRegisteredError(agent_name)

        agent_data = self._agents[agent_name]
        return {
            "name": agent_data.name,
            "intents": agent_data.intents,
            "description": agent_data.description,
        }

    def _intent_score(self, user_input: str, agent_data: RegisteredAgent) -> float:
        """Calculate intent-based matching score.

        Uses flexible keyword matching with:
        - Case-insensitive comparison
        - Exact phrase matching (highest priority)
        - Word-level matching with overlap calculation
        - Normalized scoring that rewards any match

        The scoring algorithm prioritizes strong matches:
        1. Exact multi-word phrase match: score = 1.0 (immediate match)
        2. Single word exact match: contribute to overall score
        3. Word overlap: weighted by overlap ratio

        The final score is based on the best match found, not diluted
        by the number of intents. This prevents having many intents
        from reducing match confidence.

        Args:
            user_input: User input string
            agent_data: Registered agent metadata

        Returns:
            Score between 0.0 and 1.0
        """
        if not agent_data.normalized_intents:
            return 0.0

        input_lower = user_input.lower()
        if not input_lower.strip():
            return 0.0

        input_words = set(filter(None, input_lower.split()))

        max_score = 0.0

        for intent_lower, intent_words in zip(
            agent_data.normalized_intents, agent_data.intent_word_sets
        ):
            intent_score = 0.0

            # Check for exact phrase match (highest priority)
            if intent_lower in input_lower:
                # Multi-word phrases are strong signals
                if " " in intent_lower:
                    intent_score = 1.0  # Perfect match for phrase
                else:
                    intent_score = 0.8  # Strong match for single word
            else:
                # Check for word-level matches
                common_words = input_words & intent_words

                if common_words:
                    # Calculate overlap ratio
                    overlap_ratio = len(common_words) / len(intent_words)
                    intent_score = overlap_ratio * 0.6  # Partial match

            # Keep the highest score from any intent
            max_score = max(max_score, intent_score)

        return max_score

    def _semantic_matches(
        self,
        user_input: str,
        top_k: int,
    ) -> list[tuple[AgentCallable, float]]:
        """Calculate semantic similarity matches using semantic-router."""

        router = self._ensure_semantic_router()
        if router is None:
            return []

        try:
            result = router(user_input)
        except (ValueError, Exception):
            return []

        if not result:
            return []

        routes: list[Any]
        if isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
            routes = list(result)
        else:
            routes = [result]

        matches: list[tuple[AgentCallable, float]] = []
        for route in routes:
            agent_name = getattr(route, "name", None)
            if not agent_name:
                continue
            agent_data = self._agents.get(agent_name)
            if not agent_data:
                continue
            matches.append((agent_data.agent, self._extract_semantic_score(route)))
            if len(matches) >= top_k:
                break

        return matches

    def _ensure_semantic_router(self) -> Any | None:
        """Initialise and return the cached semantic router if available."""

        if self._semantic_router is None:
            self._init_semantic_router()
        return self._semantic_router

    @staticmethod
    def _extract_semantic_score(route: Any) -> float:
        """Extract and clamp the semantic score from a route object."""

        raw_score = getattr(route, "score", None)
        if raw_score is None:
            return 1.0
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            return 1.0
        return max(0.0, min(score, 1.0))

    async def _invoke_agent(
        self,
        agent: AgentCallable,
        user_input: str,
        **kwargs: Any,
    ) -> Any:
        """Execute an agent, awaiting the result when necessary."""

        result = agent(user_input, **kwargs)
        if isawaitable(result):
            return await result
        return result

    def _init_semantic_router(self) -> None:
        """Initialize semantic-router with registered agents."""
        try:
            from semantic_router import Route  # type: ignore
            from semantic_router import SemanticRouter as _SemanticRouter  # type: ignore

            # Create encoder
            encoder = self._create_encoder()
            if encoder is None:
                return

            # Create routes from registered agents
            routes = []
            for agent_data in self._agents.values():
                if agent_data.samples:
                    route = Route(
                        name=agent_data.name,
                        utterances=agent_data.samples,
                    )
                    routes.append(route)

            if not routes:
                return

            # Create semantic router
            self._semantic_router = _SemanticRouter(encoder=encoder, routes=routes)
        except (ImportError, ValueError, Exception):
            # ImportError: semantic-router not installed
            # ValueError: API key missing or invalid configuration
            # Exception: Any other initialization errors
            return

    def _create_encoder(self) -> Any | None:
        """Create encoder for semantic routing."""

        try:
            encoder_type = (self.encoder_type or "openai").lower()
            encoders_module = import_module("semantic_router.encoders")
            encoder_class_name = {
                "openai": "OpenAIEncoder",
                "cohere": "CohereEncoder",
            }.get(encoder_type, "OpenAIEncoder")
            encoder_cls = getattr(encoders_module, encoder_class_name)
            return encoder_cls()
        except (ImportError, AttributeError, ValueError):
            # ImportError: semantic-router not installed
            # ValueError: API key missing
            return None
