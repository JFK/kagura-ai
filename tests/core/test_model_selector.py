"""Tests for ModelSelector."""


from kagura.core.model_selector import ModelConfig, ModelSelector, TaskType


class TestTaskType:
    """Test TaskType enum."""

    def test_task_types_exist(self) -> None:
        """Test all task types are defined"""
        assert TaskType.SEARCH.value == "search"
        assert TaskType.CLASSIFICATION.value == "classification"
        assert TaskType.SUMMARIZATION.value == "summarization"
        assert TaskType.TRANSLATION.value == "translation"
        assert TaskType.CODE_GENERATION.value == "code_generation"
        assert TaskType.CODE_REVIEW.value == "code_review"
        assert TaskType.COMPLEX_REASONING.value == "complex_reasoning"
        assert TaskType.CHAT.value == "chat"


class TestModelConfig:
    """Test ModelConfig dataclass."""

    def test_model_config_creation(self) -> None:
        """Test creating ModelConfig"""
        config = ModelConfig(model="gpt-5-mini", temperature=0.5, max_tokens=1000)

        assert config.model == "gpt-5-mini"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000

    def test_model_config_defaults(self) -> None:
        """Test ModelConfig with default values"""
        config = ModelConfig(model="gpt-4o", temperature=0.7)

        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens is None


class TestModelSelector:
    """Test ModelSelector class."""

    def test_init_default(self) -> None:
        """Test default initialization (GPT-4o models)"""
        selector = ModelSelector()

        assert selector.use_gpt5 is False
        assert selector.models == selector.TASK_MODELS

    def test_init_gpt5(self) -> None:
        """Test initialization with GPT-5 models"""
        selector = ModelSelector(use_gpt5=True)

        assert selector.use_gpt5 is True
        assert selector.models == selector.GPT5_MODELS

    def test_select_model_search(self) -> None:
        """Test selecting model for search task"""
        selector = ModelSelector()
        config = selector.select_model(TaskType.SEARCH)

        assert isinstance(config, ModelConfig)
        assert config.model == "gpt-5-mini"
        assert config.temperature == 0.3
        assert config.max_tokens == 500

    def test_select_model_code_generation(self) -> None:
        """Test selecting model for code generation"""
        selector = ModelSelector()
        config = selector.select_model(TaskType.CODE_GENERATION)

        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 4000

    def test_select_model_chat(self) -> None:
        """Test selecting model for chat"""
        selector = ModelSelector()
        config = selector.select_model(TaskType.CHAT)

        assert config.model == "gpt-5-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000

    def test_select_model_complex_reasoning(self) -> None:
        """Test selecting model for complex reasoning"""
        selector = ModelSelector()
        config = selector.select_model(TaskType.COMPLEX_REASONING)

        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 8000

    def test_gpt5_models(self) -> None:
        """Test GPT-5 model selection"""
        selector = ModelSelector(use_gpt5=True)

        # Search should use nano (cheapest)
        search_config = selector.select_model(TaskType.SEARCH)
        assert search_config.model == "gpt-5-nano"

        # Chat should use mini
        chat_config = selector.select_model(TaskType.CHAT)
        assert chat_config.model == "gpt-5-mini"

        # Code should use standard
        code_config = selector.select_model(TaskType.CODE_GENERATION)
        assert code_config.model == "gpt-5"

        # Complex reasoning should use pro
        reasoning_config = selector.select_model(TaskType.COMPLEX_REASONING)
        assert reasoning_config.model == "gpt-5-pro"

    def test_convenience_methods(self) -> None:
        """Test convenience methods"""
        selector = ModelSelector()

        assert selector.get_model_for_search() == "gpt-5-mini"
        assert selector.get_model_for_code() == "gpt-4o"
        assert selector.get_model_for_chat() == "gpt-5-mini"

    def test_cost_optimization(self) -> None:
        """Test that search uses cheaper model than chat"""
        selector = ModelSelector()

        search_config = selector.select_model(TaskType.SEARCH)
        chat_config = selector.select_model(TaskType.CHAT)

        # Both use gpt-4o-mini, but search has lower max_tokens
        assert search_config.model == chat_config.model
        assert search_config.max_tokens < chat_config.max_tokens  # type: ignore

    def test_all_task_types_have_models(self) -> None:
        """Test that all task types have model mappings"""
        selector = ModelSelector()

        for task_type in TaskType:
            config = selector.select_model(task_type)
            assert isinstance(config, ModelConfig)
            assert config.model  # Not empty
            assert 0.0 <= config.temperature <= 1.0
