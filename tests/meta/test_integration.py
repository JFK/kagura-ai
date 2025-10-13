"""Integration tests for Meta Agent pipeline"""

import ast

import pytest

from kagura.meta import MetaAgent
from kagura.meta.generator import CodeGenerator
from kagura.meta.parser import NLSpecParser
from kagura.meta.spec import AgentSpec
from kagura.meta.validator import CodeValidator, ValidationError


class TestMetaAgentIntegration:
    """Integration tests for Meta Agent pipeline"""

    @pytest.mark.asyncio
    async def test_end_to_end_spec_to_code(self):
        """Test complete pipeline: spec → generate → validate"""
        # Create spec
        spec = AgentSpec(
            name="word_counter",
            description="Count words in text",
            input_type="str",
            output_type="int",
            system_prompt="Count the number of words in the input text.",
        )

        # Generate code
        generator = CodeGenerator()
        code = generator.generate(spec)

        # Validate code
        validator = CodeValidator()
        assert validator.validate(code) is True

        # Verify code structure
        tree = ast.parse(code)
        func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        assert len(func_defs) == 1
        assert func_defs[0].name == "word_counter"

    @pytest.mark.asyncio
    async def test_agent_with_tools_generation(self):
        """Test agent generation with code execution tool"""
        spec = AgentSpec(
            name="math_solver",
            description="Solve math problems using Python",
            input_type="str",
            output_type="str",
            tools=["code_executor"],
            system_prompt="Solve math problems by executing Python code.",
        )

        generator = CodeGenerator()
        code = generator.generate(spec)

        # Verify CodeExecutor import present
        assert "from kagura.core.executor import CodeExecutor" in code
        assert "tools=[CodeExecutor()]" in code

        # Validate
        validator = CodeValidator()
        assert validator.validate(code) is True

    @pytest.mark.asyncio
    async def test_agent_with_memory_generation(self):
        """Test agent generation with memory"""
        spec = AgentSpec(
            name="chatbot",
            description="Conversational chatbot",
            input_type="str",
            output_type="str",
            has_memory=True,
            system_prompt="You are a friendly chatbot.",
        )

        generator = CodeGenerator()
        code = generator.generate(spec)

        # Verify memory imports
        assert "from kagura.core.memory import MemoryManager" in code
        assert "memory: MemoryManager" in code
        assert "enable_memory=True" in code

        # Validate
        validator = CodeValidator()
        assert validator.validate(code) is True

    @pytest.mark.asyncio
    async def test_generator_save_and_load(self, tmp_path):
        """Test saving generated code to file"""
        spec = AgentSpec(
            name="test_agent",
            description="Test agent",
            system_prompt="You are a test agent.",
        )

        generator = CodeGenerator()
        code = generator.generate(spec)

        # Save to file
        output_path = tmp_path / "agents" / "test_agent.py"
        generator.save(code, output_path)

        # Verify file exists and content matches
        assert output_path.exists()
        saved_code = output_path.read_text(encoding="utf-8")
        assert saved_code == code

        # Verify it's valid Python
        ast.parse(saved_code)

    @pytest.mark.asyncio
    async def test_validator_blocks_dangerous_code(self):
        """Test validator blocks insecure code"""
        # Generate code with subprocess (should fail validation)
        dangerous_code = """
from kagura import agent
import subprocess

@agent
async def dangerous_agent(x: str) -> str:
    subprocess.run(["ls"])
    return x
"""

        validator = CodeValidator()
        with pytest.raises(ValidationError, match="Disallowed import"):
            validator.validate(dangerous_code)

    @pytest.mark.asyncio
    async def test_validator_requires_agent_decorator(self):
        """Test validator requires @agent decorator"""
        code_without_decorator = """
from kagura import agent

async def test_agent(x: str) -> str:
    return x
"""

        validator = CodeValidator()
        with pytest.raises(ValidationError, match="Missing @agent decorator"):
            validator.validate(code_without_decorator)


class TestNLSpecParserIntegration:
    """Integration tests for NLSpecParser"""

    def test_tool_detection(self):
        """Test tool detection from descriptions"""
        parser = NLSpecParser()

        # Test code executor detection
        tools = parser.detect_tools("Execute Python code to calculate results")
        assert "code_executor" in tools

        # Test web search detection
        tools = parser.detect_tools("Search the web for information")
        assert "web_search" in tools

        # Test memory detection
        tools = parser.detect_tools("Remember user preferences in conversation")
        assert "memory" in tools

        # Test file operations detection
        tools = parser.detect_tools("Read file and write results")
        assert "file_ops" in tools


class TestMetaAgentAPI:
    """Integration tests for MetaAgent API"""

    @pytest.mark.asyncio
    async def test_meta_agent_generate_from_spec(self):
        """Test MetaAgent.generate_from_spec()"""
        spec = AgentSpec(
            name="translator",
            description="Translate text",
            system_prompt="You are a translator.",
        )

        meta = MetaAgent(validate=True)
        code = await meta.generate_from_spec(spec)

        # Verify code structure
        assert "@agent" in code
        assert "async def translator" in code
        assert "You are a translator." in code

    @pytest.mark.asyncio
    async def test_meta_agent_generate_and_save(self, tmp_path):
        """Test MetaAgent generate and save workflow"""
        spec = AgentSpec(
            name="summarizer",
            description="Summarize text",
            system_prompt="You are a text summarizer.",
        )

        meta = MetaAgent()
        output_path = tmp_path / "summarizer.py"

        # Generate and save manually
        code = await meta.generate_from_spec(spec)
        meta.generator.save(code, output_path)

        # Verify file created
        assert output_path.exists()

        # Verify content
        saved_code = output_path.read_text(encoding="utf-8")
        assert saved_code == code
        assert "@agent" in saved_code

    @pytest.mark.asyncio
    async def test_meta_agent_validation_disabled(self):
        """Test MetaAgent with validation disabled"""
        spec = AgentSpec(
            name="test",
            description="Test",
            system_prompt="Test",
        )

        # Should not raise even if code is invalid
        meta = MetaAgent(validate=False)
        code = await meta.generate_from_spec(spec)

        # Code should still be generated
        assert "@agent" in code
