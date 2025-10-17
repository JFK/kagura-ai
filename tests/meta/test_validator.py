"""Tests for CodeValidator"""

import pytest

from kagura.meta.validator import CodeValidator, ValidationError


def test_validator_valid_basic_agent():
    """Test validator with valid basic agent code"""
    validator = CodeValidator()
    code = """
from kagura import agent

@agent(name="test")
async def test_agent(x: str) -> str:
    '''Test agent'''
    return x
"""
    assert validator.validate(code) is True


def test_validator_valid_agent_with_decorator_call():
    """Test validator with @agent(...) decorator"""
    validator = CodeValidator()
    code = """
from kagura import agent

@agent(model="gpt-5-mini", temperature=0.7)
async def test_agent(x: str) -> str:
    '''Test agent'''
    return x
"""
    assert validator.validate(code) is True


def test_validator_syntax_error():
    """Test validator catches syntax errors"""
    validator = CodeValidator()
    code = """
from kagura import agent

@agent
async def test_agent(x: str) -> str
    return x  # Missing colon
"""
    with pytest.raises(ValidationError, match="Syntax error"):
        validator.validate(code)


def test_validator_missing_decorator():
    """Test validator catches missing @agent decorator"""
    validator = CodeValidator()
    code = """
from kagura import agent

async def test_agent(x: str) -> str:
    '''Missing decorator'''
    return x
"""
    with pytest.raises(ValidationError, match="Missing @agent decorator"):
        validator.validate(code)


def test_validator_dangerous_import():
    """Test validator blocks dangerous imports"""
    validator = CodeValidator()
    code = """
from kagura import agent
import subprocess

@agent
async def test_agent(x: str) -> str:
    subprocess.run(["ls"])
    return x
"""
    with pytest.raises(ValidationError, match="Disallowed import"):
        validator.validate(code)


def test_validator_dangerous_name():
    """Test validator blocks dangerous names"""
    validator = CodeValidator()
    code = """
from kagura import agent

@agent
async def test_agent(x: str) -> str:
    eval("print('hello')")
    return x
"""
    with pytest.raises(ValidationError, match="Disallowed name"):
        validator.validate(code)
