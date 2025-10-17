"""
Kagura AI 2.0 - Python-First AI Agent Framework

Example:
    from kagura import agent

    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        pass

    result = await hello("World")
"""

from typing import TYPE_CHECKING

# Version (lightweight, always loaded)
from .version import __version__

# Type hints for static analysis (not executed at runtime)
if TYPE_CHECKING:
    from .agents import (
        ChatbotPreset,
        CodeReviewPreset,
        ContentWriterPreset,
        DataAnalystPreset,
        LearningTutorPreset,
        PersonalAssistantPreset,
        ProjectManagerPreset,
        ResearchPreset,
        TechnicalSupportPreset,
        TranslatorPreset,
    )
    from .builder import AgentBuilder
    from .core.cache import LLMCache
    from .core.compression import CompressionPolicy, ContextManager
    from .core.decorators import agent, tool, workflow
    from .core.llm import LLMConfig, get_llm_cache, set_llm_cache
    from .core.memory import MemoryManager
    from .exceptions import (
        AgentNotRegisteredError,
        AuthenticationError,
        CodeExecutionError,
        CompressionError,
        ContextLimitExceededError,
        ExecutionError,
        InvalidCredentialsError,
        InvalidRouterStrategyError,
        KaguraError,
        LLMAPIError,
        LLMError,
        LLMRateLimitError,
        LLMTimeoutError,
        ModelNotSupportedError,
        NoAgentFoundError,
        NotAuthenticatedError,
        PermissionDeniedError,
        ResourceError,
        RoutingError,
        SchemaValidationError,
        SecurityError,
        TokenCountError,
        TokenRefreshError,
        UserCancelledError,
        ValidationError,
    )

# All other imports are lazy-loaded via __getattr__


def __getattr__(name: str):
    """Lazy import attributes on demand

    This avoids loading heavy modules (decorators, memory, etc.)
    when only importing the CLI.
    """
    # Core decorators
    if name in ("agent", "tool", "workflow"):
        from .core.decorators import agent, tool, workflow

        globals().update({"agent": agent, "tool": tool, "workflow": workflow})
        return globals()[name]

    # Builder
    if name == "AgentBuilder":
        from .builder import AgentBuilder

        globals()["AgentBuilder"] = AgentBuilder
        return AgentBuilder

    # Core utilities
    if name == "LLMCache":
        from .core.cache import LLMCache

        globals()["LLMCache"] = LLMCache
        return LLMCache

    if name in ("CompressionPolicy", "ContextManager"):
        from .core.compression import CompressionPolicy, ContextManager

        globals().update(
            {"CompressionPolicy": CompressionPolicy, "ContextManager": ContextManager}
        )
        return globals()[name]

    if name in ("LLMConfig", "get_llm_cache", "set_llm_cache"):
        from .core.llm import LLMConfig, get_llm_cache, set_llm_cache

        globals().update(
            {
                "LLMConfig": LLMConfig,
                "get_llm_cache": get_llm_cache,
                "set_llm_cache": set_llm_cache,
            }
        )
        return globals()[name]

    if name == "MemoryManager":
        from .core.memory import MemoryManager

        globals()["MemoryManager"] = MemoryManager
        return MemoryManager

    # Exceptions
    if name in (
        "AgentNotRegisteredError",
        "AuthenticationError",
        "CodeExecutionError",
        "CompressionError",
        "ContextLimitExceededError",
        "ExecutionError",
        "InvalidCredentialsError",
        "InvalidRouterStrategyError",
        "KaguraError",
        "LLMAPIError",
        "LLMError",
        "LLMRateLimitError",
        "LLMTimeoutError",
        "ModelNotSupportedError",
        "NoAgentFoundError",
        "NotAuthenticatedError",
        "PermissionDeniedError",
        "ResourceError",
        "RoutingError",
        "SchemaValidationError",
        "SecurityError",
        "TokenCountError",
        "TokenRefreshError",
        "UserCancelledError",
        "ValidationError",
    ):
        from .exceptions import (
            AgentNotRegisteredError,
            AuthenticationError,
            CodeExecutionError,
            CompressionError,
            ContextLimitExceededError,
            ExecutionError,
            InvalidCredentialsError,
            InvalidRouterStrategyError,
            KaguraError,
            LLMAPIError,
            LLMError,
            LLMRateLimitError,
            LLMTimeoutError,
            ModelNotSupportedError,
            NoAgentFoundError,
            NotAuthenticatedError,
            PermissionDeniedError,
            ResourceError,
            RoutingError,
            SchemaValidationError,
            SecurityError,
            TokenCountError,
            TokenRefreshError,
            UserCancelledError,
            ValidationError,
        )

        globals().update(
            {
                "AgentNotRegisteredError": AgentNotRegisteredError,
                "AuthenticationError": AuthenticationError,
                "CodeExecutionError": CodeExecutionError,
                "CompressionError": CompressionError,
                "ContextLimitExceededError": ContextLimitExceededError,
                "ExecutionError": ExecutionError,
                "InvalidCredentialsError": InvalidCredentialsError,
                "InvalidRouterStrategyError": InvalidRouterStrategyError,
                "KaguraError": KaguraError,
                "LLMAPIError": LLMAPIError,
                "LLMError": LLMError,
                "LLMRateLimitError": LLMRateLimitError,
                "LLMTimeoutError": LLMTimeoutError,
                "ModelNotSupportedError": ModelNotSupportedError,
                "NoAgentFoundError": NoAgentFoundError,
                "NotAuthenticatedError": NotAuthenticatedError,
                "PermissionDeniedError": PermissionDeniedError,
                "ResourceError": ResourceError,
                "RoutingError": RoutingError,
                "SchemaValidationError": SchemaValidationError,
                "SecurityError": SecurityError,
                "TokenCountError": TokenCountError,
                "TokenRefreshError": TokenRefreshError,
                "UserCancelledError": UserCancelledError,
                "ValidationError": ValidationError,
            }
        )
        return globals()[name]

    # Presets
    if name in (
        "ChatbotPreset",
        "CodeReviewPreset",
        "ContentWriterPreset",
        "DataAnalystPreset",
        "LearningTutorPreset",
        "PersonalAssistantPreset",
        "ProjectManagerPreset",
        "ResearchPreset",
        "TechnicalSupportPreset",
        "TranslatorPreset",
    ):
        from .agents import (
            ChatbotPreset,
            CodeReviewPreset,
            ContentWriterPreset,
            DataAnalystPreset,
            LearningTutorPreset,
            PersonalAssistantPreset,
            ProjectManagerPreset,
            ResearchPreset,
            TechnicalSupportPreset,
            TranslatorPreset,
        )

        globals().update(
            {
                "ChatbotPreset": ChatbotPreset,
                "CodeReviewPreset": CodeReviewPreset,
                "ContentWriterPreset": ContentWriterPreset,
                "DataAnalystPreset": DataAnalystPreset,
                "LearningTutorPreset": LearningTutorPreset,
                "PersonalAssistantPreset": PersonalAssistantPreset,
                "ProjectManagerPreset": ProjectManagerPreset,
                "ResearchPreset": ResearchPreset,
                "TechnicalSupportPreset": TechnicalSupportPreset,
                "TranslatorPreset": TranslatorPreset,
            }
        )
        return globals()[name]

    raise AttributeError(f"module 'kagura' has no attribute '{name}'")


__all__ = [
    "agent",
    "tool",
    "workflow",
    "AgentBuilder",
    # Presets
    "ChatbotPreset",
    "CodeReviewPreset",
    "ResearchPreset",
    "TranslatorPreset",
    "DataAnalystPreset",
    "PersonalAssistantPreset",
    "ContentWriterPreset",
    "TechnicalSupportPreset",
    "LearningTutorPreset",
    "ProjectManagerPreset",
    # Configuration
    "CompressionPolicy",
    "ContextManager",
    "MemoryManager",
    "LLMConfig",
    "LLMCache",
    "get_llm_cache",
    "set_llm_cache",
    # Exceptions
    "KaguraError",
    "AuthenticationError",
    "NotAuthenticatedError",
    "InvalidCredentialsError",
    "TokenRefreshError",
    "ExecutionError",
    "SecurityError",
    "UserCancelledError",
    "CodeExecutionError",
    "LLMError",
    "LLMAPIError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "CompressionError",
    "TokenCountError",
    "ModelNotSupportedError",
    "ContextLimitExceededError",
    "RoutingError",
    "NoAgentFoundError",
    "AgentNotRegisteredError",
    "InvalidRouterStrategyError",
    "ValidationError",
    "SchemaValidationError",
    "ResourceError",
    "PermissionDeniedError",
    # Version
    "__version__",
]
