"""Tests for AgentBuilder Presets."""

from kagura.agents import ChatbotPreset


def test_chatbot_preset_initialization():
    """Test ChatbotPreset initialization."""
    chatbot = ChatbotPreset("test_chatbot")

    assert chatbot.name == "test_chatbot"
    assert chatbot._config.name == "test_chatbot"


def test_chatbot_preset_configuration():
    """Test ChatbotPreset default configuration."""
    chatbot = ChatbotPreset("test_chatbot").with_model("gpt-5-mini")
    agent = chatbot.build()

    config = agent._builder_config
    assert config.name == "test_chatbot"
    assert config.model == "gpt-5-mini"

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


def test_all_presets_are_buildable():
    """Test that all presets can be built successfully."""
    presets = [
        ChatbotPreset("chatbot"),
    ]

    for preset in presets:
        agent = preset.with_model("gpt-5-mini").build()
        assert agent is not None
        assert callable(agent)
        assert hasattr(agent, "_builder_config")
        assert hasattr(agent, "_agent_name")


def test_presets_maintain_fluent_api():
    """Test that presets maintain fluent API chaining."""
    agent = (
        ChatbotPreset("fluent_test")
        .with_model("gpt-5-mini")
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
