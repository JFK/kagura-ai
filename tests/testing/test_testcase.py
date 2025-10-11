"""Tests for AgentTestCase base class."""

import pytest

from kagura.testing import AgentTestCase


def test_testcase_initialization():
    """Test AgentTestCase initialization."""
    testcase = AgentTestCase()
    testcase.setup_method(None)  # Initialize instance attributes

    assert testcase.agent is None
    assert testcase._llm_calls == []
    assert testcase._tool_calls == []
    assert testcase._start_time is None
    assert testcase._duration == 0.0


# ===== Content Assertions Tests =====


def test_assert_contains_success():
    """Test assert_contains with matching substring."""
    testcase = AgentTestCase()

    # Should not raise
    testcase.assert_contains("hello world", "hello")
    testcase.assert_contains("hello world", "world")
    testcase.assert_contains("hello world", "hello world")


def test_assert_contains_failure():
    """Test assert_contains with non-matching substring."""
    testcase = AgentTestCase()

    with pytest.raises(AssertionError, match="Expected 'goodbye'"):
        testcase.assert_contains("hello world", "goodbye")


def test_assert_contains_any_success():
    """Test assert_contains_any with at least one match."""
    testcase = AgentTestCase()

    # Should not raise
    testcase.assert_contains_any("hello world", ["hello", "goodbye"])
    testcase.assert_contains_any("hello world", ["world", "universe"])
    testcase.assert_contains_any("hello world", ["hello", "world"])


def test_assert_contains_any_failure():
    """Test assert_contains_any with no matches."""
    testcase = AgentTestCase()

    with pytest.raises(AssertionError, match="Expected one of"):
        testcase.assert_contains_any("hello world", ["goodbye", "farewell"])


def test_assert_not_contains_success():
    """Test assert_not_contains with non-matching substring."""
    testcase = AgentTestCase()

    # Should not raise
    testcase.assert_not_contains("hello world", "goodbye")
    testcase.assert_not_contains("hello world", "universe")


def test_assert_not_contains_failure():
    """Test assert_not_contains with matching substring."""
    testcase = AgentTestCase()

    with pytest.raises(AssertionError, match="Did not expect 'hello'"):
        testcase.assert_not_contains("hello world", "hello")


def test_assert_matches_pattern_success():
    """Test assert_matches_pattern with matching pattern."""
    testcase = AgentTestCase()

    # Should not raise
    testcase.assert_matches_pattern("hello123", r"\d+")
    testcase.assert_matches_pattern("test@example.com", r"\w+@\w+\.\w+")
    testcase.assert_matches_pattern("123-4567", r"\d{3}-\d{4}")


def test_assert_matches_pattern_failure():
    """Test assert_matches_pattern with non-matching pattern."""
    testcase = AgentTestCase()

    with pytest.raises(AssertionError, match="does not match pattern"):
        testcase.assert_matches_pattern("hello", r"\d+")


def test_assert_not_empty_success():
    """Test assert_not_empty with non-empty text."""
    testcase = AgentTestCase()

    # Should not raise
    testcase.assert_not_empty("hello")
    testcase.assert_not_empty("  hello  ")
    testcase.assert_not_empty("a")


def test_assert_not_empty_failure():
    """Test assert_not_empty with empty text."""
    testcase = AgentTestCase()

    with pytest.raises(AssertionError, match="Expected non-empty text"):
        testcase.assert_not_empty("")

    with pytest.raises(AssertionError, match="Expected non-empty text"):
        testcase.assert_not_empty("   ")


def test_assert_language_success():
    """Test assert_language with correct language."""
    pytest.importorskip("langdetect", reason="langdetect not installed")
    testcase = AgentTestCase()

    # Should not raise (using language detection)
    testcase.assert_language("This is English text", "en")
    testcase.assert_language("これは日本語です", "ja")


def test_assert_language_failure():
    """Test assert_language with incorrect language."""
    pytest.importorskip("langdetect", reason="langdetect not installed")
    testcase = AgentTestCase()

    with pytest.raises(AssertionError, match="Expected language"):
        testcase.assert_language("This is English text", "ja")


# ===== LLM Behavior Assertions Tests =====


def test_assert_llm_calls_count():
    """Test assert_llm_calls with count assertion."""
    testcase = AgentTestCase()
    testcase.setup_method(None)  # Initialize instance attributes

    # Empty calls
    testcase.assert_llm_calls(count=0)

    # Add calls
    testcase._llm_calls = [
        {"model": "gpt-4o-mini"},
        {"model": "gpt-4o-mini"},
    ]
    testcase.assert_llm_calls(count=2)

    # Wrong count
    with pytest.raises(AssertionError, match="Expected 1 LLM calls, got 2"):
        testcase.assert_llm_calls(count=1)


def test_assert_llm_calls_model():
    """Test assert_llm_calls with model assertion."""
    testcase = AgentTestCase()

    testcase._llm_calls = [
        {"model": "gpt-4o-mini"},
        {"model": "gpt-4o-mini"},
    ]

    # Correct model
    testcase.assert_llm_calls(model="gpt-4o-mini")

    # Wrong model
    with pytest.raises(AssertionError, match="Expected all calls to use model"):
        testcase.assert_llm_calls(model="gpt-4o")


def test_assert_token_usage_max():
    """Test assert_token_usage with max_tokens."""
    testcase = AgentTestCase()

    testcase._llm_calls = [
        {"prompt_tokens": 100, "completion_tokens": 50},
        {"prompt_tokens": 200, "completion_tokens": 100},
    ]

    # Within limit (total: 450)
    testcase.assert_token_usage(max_tokens=500)
    testcase.assert_token_usage(max_tokens=450)

    # Exceeds limit
    with pytest.raises(AssertionError, match="exceeds max"):
        testcase.assert_token_usage(max_tokens=400)


def test_assert_token_usage_min():
    """Test assert_token_usage with min_tokens."""
    testcase = AgentTestCase()

    testcase._llm_calls = [
        {"prompt_tokens": 100, "completion_tokens": 50},
    ]

    # Above minimum (total: 150)
    testcase.assert_token_usage(min_tokens=100)
    testcase.assert_token_usage(min_tokens=150)

    # Below minimum
    with pytest.raises(AssertionError, match="below min"):
        testcase.assert_token_usage(min_tokens=200)


def test_assert_tool_calls():
    """Test assert_tool_calls assertion."""
    testcase = AgentTestCase()

    testcase._tool_calls = [
        {"name": "search_tool"},
        {"name": "calculator"},
    ]

    # Tools called
    testcase.assert_tool_calls(["search_tool"])
    testcase.assert_tool_calls(["calculator"])
    testcase.assert_tool_calls(["search_tool", "calculator"])

    # Tool not called
    with pytest.raises(AssertionError, match="Expected tool 'missing_tool'"):
        testcase.assert_tool_calls(["missing_tool"])


# ===== Performance Assertions Tests =====


def test_assert_duration():
    """Test assert_duration assertion."""
    testcase = AgentTestCase()

    testcase._duration = 2.5

    # Within limit
    testcase.assert_duration(max_seconds=3.0)
    testcase.assert_duration(max_seconds=2.5)

    # Exceeds limit
    with pytest.raises(AssertionError, match="Execution took"):
        testcase.assert_duration(max_seconds=2.0)


def test_assert_cost():
    """Test assert_cost assertion."""
    testcase = AgentTestCase()

    testcase._llm_calls = [
        {"cost": 0.001},
        {"cost": 0.002},
    ]

    # Within budget (total: 0.003)
    testcase.assert_cost(max_cost=0.01)
    testcase.assert_cost(max_cost=0.003)

    # Exceeds budget
    with pytest.raises(AssertionError, match="exceeds max"):
        testcase.assert_cost(max_cost=0.002)


# ===== Structured Output Assertions Tests =====


def test_assert_valid_model():
    """Test assert_valid_model with Pydantic model."""
    from pydantic import BaseModel

    class TestModel(BaseModel):
        name: str
        age: int

    testcase = AgentTestCase()

    # Valid instance
    instance = TestModel(name="Alice", age=30)
    testcase.assert_valid_model(instance, TestModel)

    # Invalid instance
    with pytest.raises(AssertionError, match="Expected TestModel"):
        testcase.assert_valid_model("not a model", TestModel)


def test_assert_field_value():
    """Test assert_field_value with Pydantic model."""
    from pydantic import BaseModel

    class TestModel(BaseModel):
        status: str
        count: int

    testcase = AgentTestCase()

    instance = TestModel(status="success", count=42)

    # Correct value
    testcase.assert_field_value(instance, "status", "success")
    testcase.assert_field_value(instance, "count", 42)

    # Incorrect value
    with pytest.raises(AssertionError, match="Expected status=failure"):
        testcase.assert_field_value(instance, "status", "failure")
