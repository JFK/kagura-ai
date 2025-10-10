"""Tests for AgentBuilder Presets."""

from pathlib import Path

import pytest

from kagura.presets import ChatbotPreset, CodeReviewPreset, ResearchPreset


def test_chatbot_preset_initialization():
    """Test ChatbotPreset initialization."""
    chatbot = ChatbotPreset("test_chatbot")

    assert chatbot.name == "test_chatbot"
    assert chatbot._config.name == "test_chatbot"


def test_chatbot_preset_configuration():
    """Test ChatbotPreset default configuration."""
    chatbot = ChatbotPreset("test_chatbot").with_model("gpt-4o-mini")
    agent = chatbot.build()

    config = agent._builder_config
    assert config.name == "test_chatbot"
    assert config.model == "gpt-4o-mini"

    # Verify memory configuration
    assert config.memory is not None
    assert config.memory.type == "context"
    assert config.memory.max_messages == 100

    # Verify context configuration
    assert config.context["temperature"] == 0.8
    assert config.context["max_tokens"] == 1000


def test_chatbot_preset_customization():
    """Test ChatbotPreset customization."""
    chatbot = (
        ChatbotPreset("custom_chatbot")
        .with_model("gpt-4o")
        .with_context(temperature=0.9, max_tokens=1500)
    )

    agent = chatbot.build()
    config = agent._builder_config

    # Custom values override defaults
    assert config.model == "gpt-4o"
    assert config.context["temperature"] == 0.9
    assert config.context["max_tokens"] == 1500

    # Memory defaults preserved
    assert config.memory is not None
    assert config.memory.type == "context"


def test_research_preset_initialization():
    """Test ResearchPreset initialization."""
    researcher = ResearchPreset("test_researcher")

    assert researcher.name == "test_researcher"
    assert researcher._config.name == "test_researcher"


def test_research_preset_configuration():
    """Test ResearchPreset default configuration."""
    researcher = ResearchPreset("test_researcher").with_model("gpt-4o")
    agent = researcher.build()

    config = agent._builder_config
    assert config.name == "test_researcher"
    assert config.model == "gpt-4o"

    # Verify RAG memory configuration
    assert config.memory is not None
    assert config.memory.type == "rag"
    assert config.memory.enable_rag is True
    assert config.memory.max_messages == 200

    # Verify context configuration
    assert config.context["temperature"] == 0.3
    assert config.context["max_tokens"] == 2000


def test_research_preset_with_persist_dir():
    """Test ResearchPreset with persist directory."""
    persist_dir = Path("/tmp/kagura_research")
    researcher = (
        ResearchPreset("test_researcher", persist_dir=persist_dir)
        .with_model("gpt-4o-mini")
    )

    agent = researcher.build()
    config = agent._builder_config

    assert config.memory is not None
    assert config.memory.persist_dir == persist_dir


def test_code_review_preset_initialization():
    """Test CodeReviewPreset initialization."""
    reviewer = CodeReviewPreset("test_reviewer")

    assert reviewer.name == "test_reviewer"
    assert reviewer._config.name == "test_reviewer"


def test_code_review_preset_configuration():
    """Test CodeReviewPreset default configuration."""
    reviewer = CodeReviewPreset("test_reviewer").with_model("gpt-4o")
    agent = reviewer.build()

    config = agent._builder_config
    assert config.name == "test_reviewer"
    assert config.model == "gpt-4o"

    # Verify working memory configuration
    assert config.memory is not None
    assert config.memory.type == "working"
    assert config.memory.max_messages == 50

    # Verify context configuration (very low temperature for code)
    assert config.context["temperature"] == 0.1
    assert config.context["max_tokens"] == 1500


def test_all_presets_are_buildable():
    """Test that all presets can be built successfully."""
    presets = [
        ChatbotPreset("chatbot"),
        ResearchPreset("researcher"),
        CodeReviewPreset("reviewer"),
    ]

    for preset in presets:
        agent = preset.with_model("gpt-4o-mini").build()
        assert agent is not None
        assert callable(agent)
        assert hasattr(agent, "_builder_config")
        assert hasattr(agent, "_agent_name")


def test_presets_maintain_fluent_api():
    """Test that presets maintain fluent API chaining."""
    agent = (
        ChatbotPreset("fluent_test")
        .with_model("gpt-4o-mini")
        .with_context(temperature=0.7)
        .with_memory(type="persistent")  # Override preset default
        .build()
    )

    config = agent._builder_config

    # Verify overridden memory type
    assert config.memory is not None
    assert config.memory.type == "persistent"

    # Verify custom context
    assert config.context["temperature"] == 0.7
