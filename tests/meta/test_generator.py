"""Tests for CodeGenerator"""

import ast

import pytest

from kagura.meta.generator import CodeGenerator
from kagura.meta.spec import AgentSpec


@pytest.fixture
def generator():
    """Create CodeGenerator instance"""
    return CodeGenerator()


@pytest.fixture
def basic_spec():
    """Create basic AgentSpec"""
    return AgentSpec(
        name="test_agent",
        description="Test agent",
        input_type="str",
        output_type="str",
        system_prompt="You are a test agent.",
    )


def test_generator_basic_agent(generator, basic_spec):
    """Test generator with basic agent spec"""
    code = generator.generate(basic_spec)

    # Verify code is valid Python
    ast.parse(code)

    # Verify expected content
    assert "@agent" in code
    assert "async def test_agent" in code
    assert "input_data: str" in code
    assert "-> str" in code
    assert "You are a test agent." in code


def test_generator_agent_with_tools(generator):
    """Test generator with agent that has tools"""
    spec = AgentSpec(
        name="code_agent",
        description="Execute code",
        system_prompt="You can execute code.",
        tools=["code_executor"],
    )

    code = generator.generate(spec)

    # Verify code is valid Python
    ast.parse(code)

    # Verify tool imports and usage
    assert "from kagura.core.executor import CodeExecutor" in code
    assert "tools=[CodeExecutor()]" in code


def test_generator_agent_with_memory(generator):
    """Test generator with agent that has memory"""
    spec = AgentSpec(
        name="chat_agent",
        description="Chatbot",
        system_prompt="You are a chatbot.",
        has_memory=True,
    )

    code = generator.generate(spec)

    # Verify code is valid Python
    ast.parse(code)

    # Verify memory imports and usage
    assert "from kagura.core.memory import MemoryManager" in code
    assert "memory: MemoryManager" in code
    assert "enable_memory=True" in code


def test_generator_template_selection(generator):
    """Test template selection logic"""
    # Basic agent
    basic_spec = AgentSpec(
        name="test",
        description="Test",
        system_prompt="Test",
    )
    assert generator._select_template(basic_spec) == "agent_base.py.j2"

    # Agent with tools
    tool_spec = AgentSpec(
        name="test",
        description="Test",
        system_prompt="Test",
        tools=["code_executor"],
    )
    assert generator._select_template(tool_spec) == "agent_with_tools.py.j2"

    # Agent with memory
    memory_spec = AgentSpec(
        name="test",
        description="Test",
        system_prompt="Test",
        has_memory=True,
    )
    assert generator._select_template(memory_spec) == "agent_with_memory.py.j2"


def test_generator_save(generator, basic_spec, tmp_path):
    """Test saving generated code to file"""
    code = generator.generate(basic_spec)
    output_path = tmp_path / "agents" / "test_agent.py"

    generator.save(code, output_path)

    assert output_path.exists()
    assert output_path.read_text() == code
