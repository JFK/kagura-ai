"""Smart model selection for cost optimization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """Task classification for model selection.

    Each task type maps to an optimal model based on:
    - Required capabilities
    - Cost efficiency
    - Response quality
    """

    SEARCH = "search"  # Web search, file search
    CLASSIFICATION = "classification"  # Intent detection, routing
    SUMMARIZATION = "summarization"  # Text summarization
    TRANSLATION = "translation"  # Language translation
    CODE_GENERATION = "code_generation"  # Code writing
    CODE_REVIEW = "code_review"  # Code analysis
    COMPLEX_REASONING = "complex_reasoning"  # Multi-step reasoning
    CHAT = "chat"  # General conversation


@dataclass
class ModelConfig:
    """Model configuration for specific task.

    Attributes:
        model: Model identifier (e.g., "gpt-5-mini", "gpt-5-nano")
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate (None = model default)
    """

    model: str
    temperature: float
    max_tokens: int | None = None


class ModelSelector:
    """Select optimal model for each task type.

    This class provides intelligent model selection based on task requirements,
    optimizing for both cost and quality.

    Cost Optimization (OpenAI GPT-5):
    - nano ($0.05/1M in): 80-90% cheaper for search/classification
    - mini ($0.25/1M in): General chat, summarization
    - standard ($1.25/1M in): Code generation, complex tasks
    - pro ($15/1M in): Advanced reasoning

    Example:
        >>> selector = ModelSelector()
        >>> config = selector.select_model(TaskType.SEARCH)
        >>> print(config.model)  # "gpt-5-mini" (fallback if GPT-5 unavailable)
    """

    # Default model mappings (optimized for cost/quality)
    # Note: Using gpt-4o-mini as fallback until GPT-5 is GA
    TASK_MODELS: dict[TaskType, ModelConfig] = {
        TaskType.SEARCH: ModelConfig("gpt-5-mini", 0.3, 500),
        TaskType.CLASSIFICATION: ModelConfig("gpt-5-mini", 0.3, 100),
        TaskType.SUMMARIZATION: ModelConfig("gpt-5-mini", 0.5, 1000),
        TaskType.TRANSLATION: ModelConfig("gpt-5-mini", 0.3, 2000),
        TaskType.CODE_GENERATION: ModelConfig("gpt-4o", 0.7, 4000),
        TaskType.CODE_REVIEW: ModelConfig("gpt-4o", 0.5, 2000),
        TaskType.COMPLEX_REASONING: ModelConfig("gpt-4o", 0.7, 8000),
        TaskType.CHAT: ModelConfig("gpt-5-mini", 0.7, 2000),
    }

    # Future: GPT-5 models (when available)
    GPT5_MODELS: dict[TaskType, ModelConfig] = {
        TaskType.SEARCH: ModelConfig("gpt-5-nano", 0.3, 500),
        TaskType.CLASSIFICATION: ModelConfig("gpt-5-nano", 0.3, 100),
        TaskType.SUMMARIZATION: ModelConfig("gpt-5-nano", 0.5, 1000),
        TaskType.TRANSLATION: ModelConfig("gpt-5-mini", 0.3, 2000),
        TaskType.CODE_GENERATION: ModelConfig("gpt-5", 0.7, 4000),
        TaskType.CODE_REVIEW: ModelConfig("gpt-5", 0.5, 2000),
        TaskType.COMPLEX_REASONING: ModelConfig("gpt-5-pro", 0.7, 8000),
        TaskType.CHAT: ModelConfig("gpt-5-mini", 0.7, 2000),
    }

    def __init__(self, use_gpt5: bool = False) -> None:
        """Initialize model selector.

        Args:
            use_gpt5: Use GPT-5 models if True (default: False)
        """
        self.use_gpt5 = use_gpt5
        self.models = self.GPT5_MODELS if use_gpt5 else self.TASK_MODELS

    def select_model(self, task_type: TaskType) -> ModelConfig:
        """Select optimal model for task type.

        Args:
            task_type: Type of task to perform

        Returns:
            ModelConfig with optimal settings for the task

        Example:
            >>> selector = ModelSelector()
            >>> config = selector.select_model(TaskType.SEARCH)
            >>> print(config.model)  # "gpt-5-mini"
            >>> print(config.temperature)  # 0.3
        """
        return self.models.get(task_type, self.models[TaskType.CHAT])

    def get_model_for_search(self) -> str:
        """Get model for search tasks (convenience method).

        Returns:
            Model identifier for search tasks
        """
        return self.select_model(TaskType.SEARCH).model

    def get_model_for_code(self) -> str:
        """Get model for code generation (convenience method).

        Returns:
            Model identifier for code generation
        """
        return self.select_model(TaskType.CODE_GENERATION).model

    def get_model_for_chat(self) -> str:
        """Get model for chat tasks (convenience method).

        Returns:
            Model identifier for chat
        """
        return self.select_model(TaskType.CHAT).model
