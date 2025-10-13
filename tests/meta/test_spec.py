"""Tests for AgentSpec model"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from kagura.meta.spec import AgentSpec


def test_agent_spec_basic():
    """Test basic AgentSpec creation"""
    spec = AgentSpec(
        name="test_agent",
        description="Test agent",
        system_prompt="You are a test agent.",
    )

    assert spec.name == "test_agent"
    assert spec.description == "Test agent"
    assert spec.input_type == "str"  # default
    assert spec.output_type == "str"  # default
    assert spec.tools == []  # default
    assert spec.has_memory is False  # default


def test_agent_spec_with_tools():
    """Test AgentSpec with tools"""
    spec = AgentSpec(
        name="code_agent",
        description="Execute code",
        system_prompt="You can execute code.",
        tools=["code_executor"],
    )

    assert "code_executor" in spec.tools


def test_agent_spec_with_memory():
    """Test AgentSpec with memory"""
    spec = AgentSpec(
        name="chat_agent",
        description="Chatbot",
        system_prompt="You are a chatbot.",
        has_memory=True,
    )

    assert spec.has_memory is True


def test_agent_spec_validation_missing_required():
    """Test AgentSpec validation with missing required fields"""
    with pytest.raises(PydanticValidationError):
        AgentSpec(name="test")  # Missing description and system_prompt


def test_agent_spec_with_examples():
    """Test AgentSpec with examples"""
    spec = AgentSpec(
        name="translator",
        description="Translate text",
        system_prompt="You are a translator.",
        examples=[{"input": "Hello", "output": "こんにちは"}],
    )

    assert len(spec.examples) == 1
    assert spec.examples[0]["input"] == "Hello"
