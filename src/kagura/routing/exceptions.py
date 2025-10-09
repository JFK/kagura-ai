"""Exceptions for agent routing system."""


class RoutingError(Exception):
    """Base exception for routing errors."""

    pass


class NoAgentFoundError(RoutingError):
    """Raised when no suitable agent is found for routing."""

    def __init__(self, message: str, user_input: str | None = None) -> None:
        """Initialize exception.

        Args:
            message: Error message
            user_input: User input that failed to route
        """
        super().__init__(message)
        self.user_input = user_input


class AgentNotRegisteredError(RoutingError):
    """Raised when trying to access an unregistered agent."""

    def __init__(self, agent_name: str) -> None:
        """Initialize exception.

        Args:
            agent_name: Name of unregistered agent
        """
        super().__init__(f"Agent '{agent_name}' is not registered")
        self.agent_name = agent_name


class InvalidRouterStrategyError(RoutingError):
    """Raised when an invalid routing strategy is specified."""

    def __init__(self, strategy: str, valid_strategies: list[str]) -> None:
        """Initialize exception.

        Args:
            strategy: Invalid strategy name
            valid_strategies: List of valid strategy names
        """
        super().__init__(
            f"Invalid strategy '{strategy}'. "
            f"Valid strategies: {', '.join(valid_strategies)}"
        )
        self.strategy = strategy
        self.valid_strategies = valid_strategies
