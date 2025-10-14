"""Tests for ErrorAnalyzer"""

import pytest
from unittest.mock import AsyncMock, patch
from kagura.meta.error_analyzer import ErrorAnalyzer, ErrorAnalysis


@pytest.fixture
def error_analyzer():
    """Create ErrorAnalyzer instance for testing"""
    return ErrorAnalyzer()


@pytest.mark.asyncio
@patch("kagura.meta.error_analyzer.call_llm", new_callable=AsyncMock)
async def test_analyze_file_not_found_error(mock_call_llm, error_analyzer):
    """Test analyzing FileNotFoundError"""
    mock_call_llm.return_value = """
Root cause: The CSV file 'sales.csv' does not exist in the specified path
Suggested fix: Add file existence check before processing
Fix code: N/A
"""

    # Simulate FileNotFoundError
    try:
        raise FileNotFoundError("sales.csv not found")
    except FileNotFoundError as e:
        agent_code = """
@agent(tools=[execute_code])
async def data_analyst(csv_path: str) -> dict:
    pass
"""
        user_input = {"csv_path": "sales.csv"}

        analysis = await error_analyzer.analyze(e, agent_code, user_input)

        assert analysis.error_type == "FileNotFoundError"
        assert "sales.csv" in analysis.error_message
        assert "file" in analysis.root_cause.lower()
        assert "check" in analysis.suggested_fix.lower()
        assert analysis.fix_code is None  # N/A


@pytest.mark.asyncio
@patch("kagura.meta.error_analyzer.call_llm", new_callable=AsyncMock)
async def test_analyze_attribute_error(mock_call_llm, error_analyzer):
    """Test analyzing AttributeError"""
    mock_call_llm.return_value = """
Root cause: The DataFrame object does not have attribute 'clumn' (typo for 'column')
Suggested fix: Correct the attribute name from 'clumn' to 'column'
Fix code:
df['column'].mean()
"""

    try:
        # Simulate AttributeError
        raise AttributeError("'DataFrame' object has no attribute 'clumn'")
    except AttributeError as e:
        agent_code = "df['clumn'].mean()"
        user_input = {}

        analysis = await error_analyzer.analyze(e, agent_code, user_input)

        assert analysis.error_type == "AttributeError"
        assert "typo" in analysis.root_cause.lower() or "attribute" in analysis.root_cause.lower()
        assert analysis.fix_code is not None
        assert "column" in analysis.fix_code


@pytest.mark.asyncio
@patch("kagura.meta.error_analyzer.call_llm", new_callable=AsyncMock)
async def test_analyze_type_error(mock_call_llm, error_analyzer):
    """Test analyzing TypeError"""
    mock_call_llm.return_value = """
Root cause: Function expects int but received str
Suggested fix: Convert input to int before passing
Fix code:
result = fibonacci(int(n))
"""

    try:
        raise TypeError("unsupported operand type(s) for +: 'int' and 'str'")
    except TypeError as e:
        agent_code = "result = fibonacci(n)"
        user_input = {"n": "10"}

        analysis = await error_analyzer.analyze(e, agent_code, user_input)

        assert analysis.error_type == "TypeError"
        assert "type" in analysis.root_cause.lower() or "convert" in analysis.suggested_fix.lower()


@pytest.mark.asyncio
@patch("kagura.meta.error_analyzer.call_llm", new_callable=AsyncMock)
async def test_extract_section_parsing(mock_call_llm, error_analyzer):
    """Test _extract_section method"""
    mock_call_llm.return_value = """
Root cause: Missing import statement
Suggested fix: Add pandas import
Fix code:
import pandas as pd
df = pd.read_csv('data.csv')
"""

    try:
        raise ImportError("No module named 'pandas'")
    except ImportError as e:
        analysis = await error_analyzer.analyze(e, "", {})

        assert "import" in analysis.root_cause.lower()
        assert "pandas" in analysis.suggested_fix.lower()
        assert analysis.fix_code is not None
        assert "import pandas" in analysis.fix_code


@pytest.mark.asyncio
async def test_error_analysis_dataclass():
    """Test ErrorAnalysis dataclass"""
    analysis = ErrorAnalysis(
        error_type="ValueError",
        error_message="Invalid value",
        stack_trace="Traceback...",
        root_cause="Input validation missing",
        suggested_fix="Add input validation",
        fix_code="if x < 0: raise ValueError()",
    )

    assert analysis.error_type == "ValueError"
    assert analysis.error_message == "Invalid value"
    assert analysis.fix_code is not None
