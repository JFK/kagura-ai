"""Tests for CodeFixer"""

import pytest

from kagura.meta.error_analyzer import ErrorAnalysis
from kagura.meta.fixer import CodeFixer


@pytest.fixture
def fixer():
    """Create CodeFixer instance for testing"""
    return CodeFixer()


def test_apply_fix_with_code_snippet(fixer):
    """Test applying fix with complete function replacement"""
    original_code = """from kagura import agent

@agent
async def test_agent(x: int) -> int:
    return x + y  # y is undefined
"""

    # Fix code must be complete function including decorators
    analysis = ErrorAnalysis(
        error_type="NameError",
        error_message="name 'y' is not defined",
        stack_trace="",
        root_cause="Variable y is not defined",
        suggested_fix="Define y or remove it",
        fix_code="""from kagura import agent

@agent
async def test_agent(x: int) -> int:
    return x + x  # Fixed
""",
    )

    fixed_code = fixer.apply_fix(original_code, analysis)

    # Fix should be applied
    assert fixed_code is not None
    assert "x + x" in fixed_code


def test_apply_fix_no_fix_code(fixer):
    """Test apply_fix when no fix code provided"""
    original_code = """
@agent
async def test_agent():
    pass
"""

    analysis = ErrorAnalysis(
        error_type="ValueError",
        error_message="Test error",
        stack_trace="",
        root_cause="Test",
        suggested_fix="Test fix",
        fix_code=None,  # No fix code
    )

    fixed_code = fixer.apply_fix(original_code, analysis)

    assert fixed_code is None  # Should return None when no fix_code


def test_apply_fix_invalid_syntax(fixer):
    """Test apply_fix with invalid fix code"""
    original_code = """
@agent
async def test_agent():
    return 1
"""

    analysis = ErrorAnalysis(
        error_type="SyntaxError",
        error_message="Test",
        stack_trace="",
        root_cause="Test",
        suggested_fix="Test",
        fix_code="def invalid syntax here:",  # Invalid syntax
    )

    # Should handle gracefully
    fixed_code = fixer.apply_fix(original_code, analysis)

    # Either returns original or None
    assert fixed_code is None or fixed_code == original_code


def test_replace_function_simple(fixer):
    """Test _replace_function method"""
    original = """
def hello():
    return "old"

def other():
    return "keep"
"""

    new_func = """def hello():
    return "new"
"""

    fixed = fixer._replace_function(original, "hello", new_func)

    assert "new" in fixed
    assert "keep" in fixed  # Other function preserved


def test_apply_fix_with_validation(fixer):
    """Test that fixed code is validated"""
    original_code = """from kagura import agent

@agent
async def test_agent(x: int) -> int:
    return x * 2
"""

    analysis = ErrorAnalysis(
        error_type="TypeError",
        error_message="Test",
        stack_trace="",
        root_cause="Test",
        suggested_fix="Test",
        fix_code="""from kagura import agent

@agent
async def test_agent(x: int) -> int:
    return x * 3  # Fixed
""",
    )

    fixed_code = fixer.apply_fix(original_code, analysis)

    # Should validate successfully
    assert fixed_code is not None
    assert "x * 3" in fixed_code
