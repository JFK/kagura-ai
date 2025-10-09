"""Agent routing system for intelligent agent selection.

This module provides intent-based routing to automatically select
the most appropriate agent based on user input.
"""

from dataclasses import dataclass
from typing import Any, Callable

from .exceptions import (
    InvalidRouterStrategyError,
    NoAgentFoundError,
)


@dataclass
class RegisteredAgent:
    """Metadata for a registered agent.

    Attributes:
        agent: The agent function
        name: Agent name
        intents: List of intent keywords/patterns
        description: Agent description
    """

    agent: Callable
    name: str
    intents: list[str]
    description: str


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

    VALID_STRATEGIES = ["intent"]

    def __init__(
        self,
        strategy: str = "intent",
        fallback_agent: Callable | None = None,
        confidence_threshold: float = 0.3,
    ) -> None:
        """Initialize agent router.

        Args:
            strategy: Routing strategy (currently only "intent" is supported)
            fallback_agent: Default agent to use when no match is found
            confidence_threshold: Minimum confidence score (0.0-1.0) required
                for routing. Lower values are more lenient.

        Raises:
            InvalidRouterStrategyError: If strategy is not valid
        """
        if strategy not in self.VALID_STRATEGIES:
            raise InvalidRouterStrategyError(strategy, self.VALID_STRATEGIES)

        self.strategy = strategy
        self.fallback_agent = fallback_agent
        self.confidence_threshold = confidence_threshold
        self._agents: dict[str, RegisteredAgent] = {}

    def register(
        self,
        agent: Callable,
        intents: list[str] | None = None,
        description: str = "",
        name: str | None = None,
    ) -> None:
        """Register an agent with routing patterns.

        Args:
            agent: Agent function to register
            intents: List of intent keywords/patterns for matching.
                Case-insensitive matching is used.
            description: Human-readable description of the agent
            name: Agent name (defaults to function name)

        Example:
            >>> router.register(
            ...     code_reviewer,
            ...     intents=["review", "check", "analyze"],
            ...     description="Reviews code for quality and bugs"
            ... )
        """
        agent_name = name or agent.__name__
        intents = intents or []

        self._agents[agent_name] = RegisteredAgent(
            agent=agent,
            name=agent_name,
            intents=intents,
            description=description,
        )

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
                return await self.fallback_agent(user_input, **kwargs)
            raise NoAgentFoundError(
                f"No agent found for input: {user_input!r}",
                user_input=user_input,
            )

        # Get best match
        best_agent, confidence = matched_agents[0]

        # Check confidence threshold
        if confidence < self.confidence_threshold:
            if self.fallback_agent:
                return await self.fallback_agent(user_input, **kwargs)
            raise NoAgentFoundError(
                f"Low confidence ({confidence:.2f}) for input: {user_input!r}. "
                f"Threshold: {self.confidence_threshold}",
                user_input=user_input,
            )

        # Execute the selected agent
        # Note: For Phase 1, we pass user_input as the first argument
        # Future phases may support more sophisticated parameter mapping
        return await best_agent(user_input, **kwargs)

    def get_matched_agents(
        self,
        user_input: str,
        top_k: int = 3,
    ) -> list[tuple[Callable, float]]:
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
        scores: list[tuple[Callable, float]] = []

        for agent_data in self._agents.values():
            score = self._calculate_score(user_input, agent_data)
            if score > 0:  # Only include agents with non-zero scores
                scores.append((agent_data.agent, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

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

    def _calculate_score(
        self,
        user_input: str,
        agent_data: RegisteredAgent,
    ) -> float:
        """Calculate matching score for an agent.

        Args:
            user_input: User input string
            agent_data: Registered agent metadata

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if self.strategy == "intent":
            return self._intent_score(user_input, agent_data.intents)
        return 0.0

    def _intent_score(self, user_input: str, intents: list[str]) -> float:
        """Calculate intent-based matching score.

        Uses simple keyword matching with case-insensitive comparison.
        Score is calculated as: (matched_intents / total_intents)

        Args:
            user_input: User input string
            intents: List of intent keywords

        Returns:
            Score between 0.0 and 1.0
        """
        if not intents:
            return 0.0

        input_lower = user_input.lower()
        matches = sum(1 for intent in intents if intent.lower() in input_lower)

        return matches / len(intents)
