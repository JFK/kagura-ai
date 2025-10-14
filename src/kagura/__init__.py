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
from .presets import (
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
from .version import __version__

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
