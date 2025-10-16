"""AgentTestCase - Base class for agent testing."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from .mocking import LLMMock, LLMRecorder, ToolMock
    from .utils import Timer


class AgentTestCase:
    """Base class for testing Kagura agents.

    Provides assertion methods and utilities for testing AI agents,
    handling the non-deterministic nature of LLM outputs.

    Note:
        This class can be used in two ways:
        1. As a test class base (pytest will call setup_method before each test)
        2. As a standalone utility (instantiate directly with AgentTestCase())

        Both __init__ and setup_method initialize the same attributes to ensure
        proper functionality in either usage pattern.

    Example:
        >>> from kagura.testing import AgentTestCase
        >>> class TestMyAgent(AgentTestCase):
        ...     agent = my_agent
        ...     async def test_basic(self):
        ...         result = await self.agent("Hello")
        ...         self.assert_not_empty(result)
    """

    agent: Optional[Callable] = None  # Agent to test

    def __init__(self) -> None:
        """Initialize test case.

        This method is called when:
        1. The class is instantiated directly (e.g., in fixtures)
        2. Pytest creates test class instances

        Pytest will not show collection warnings if __init__ has no parameters.
        """
        self._llm_calls: list[dict[str, Any]] = []
        self._tool_calls: list[dict[str, Any]] = []
        self._start_time: Optional[float] = None
        self._duration: float = 0.0

    def setup_method(self, method: Any) -> None:
        """Setup method called by pytest before each test method.

        This reinitializes all instance attributes before each test method,
        ensuring test isolation.

        Args:
            method: Test method being executed
        """
        self._llm_calls: list[dict[str, Any]] = []
        self._tool_calls: list[dict[str, Any]] = []
        self._start_time: Optional[float] = None
        self._duration: float = 0.0

    # ===== Content Assertions =====

    def assert_contains(self, text: str, substring: str) -> None:
        """Assert text contains substring.

        Args:
            text: Text to check
            substring: Expected substring

        Raises:
            AssertionError: If substring not found
        """
        assert substring in text, f"Expected '{substring}' in text, got: {text}"

    def assert_contains_any(self, text: str, options: list[str]) -> None:
        """Assert text contains at least one of the options.

        Args:
            text: Text to check
            options: List of possible substrings

        Raises:
            AssertionError: If none of the options found
        """
        assert any(
            opt in text for opt in options
        ), f"Expected one of {options} in text, got: {text}"

    def assert_not_contains(self, text: str, substring: str) -> None:
        """Assert text does not contain substring.

        Args:
            text: Text to check
            substring: Forbidden substring

        Raises:
            AssertionError: If substring found
        """
        assert (
            substring not in text
        ), f"Did not expect '{substring}' in text, got: {text}"

    def assert_matches_pattern(self, text: str, pattern: str) -> None:
        """Assert text matches regex pattern.

        Args:
            text: Text to check
            pattern: Regex pattern

        Raises:
            AssertionError: If pattern doesn't match
        """
        assert re.search(
            pattern, text
        ), f"Text does not match pattern '{pattern}': {text}"

    def assert_not_empty(self, text: str) -> None:
        """Assert text is not empty.

        Args:
            text: Text to check

        Raises:
            AssertionError: If text is empty or only whitespace
        """
        assert text and text.strip(), "Expected non-empty text"

    def assert_language(self, text: str, expected_lang: str) -> None:
        """Assert text is in expected language.

        Args:
            text: Text to check
            expected_lang: Expected language code (e.g., 'en', 'ja')

        Raises:
            AssertionError: If language doesn't match
            ImportError: If langdetect not installed
        """
        try:
            from langdetect import detect  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "langdetect is required for language detection. "
                "Install with: pip install langdetect"
            )

        detected = detect(text)
        assert (
            detected == expected_lang
        ), f"Expected language '{expected_lang}', got '{detected}'"

    # ===== LLM Behavior Assertions =====

    def assert_llm_calls(
        self,
        count: Optional[int] = None,
        model: Optional[str] = None,
    ) -> None:
        """Assert number and characteristics of LLM calls.

        Args:
            count: Expected number of LLM calls (optional)
            model: Expected model name (optional)

        Raises:
            AssertionError: If LLM calls don't match expectations
        """
        if count is not None:
            actual = len(self._llm_calls)
            assert actual == count, f"Expected {count} LLM calls, got {actual}"

        if model is not None:
            models = [call.get("model") for call in self._llm_calls]
            assert all(
                m == model for m in models
            ), f"Expected all calls to use model '{model}', got {set(models)}"

    def assert_token_usage(
        self,
        max_tokens: Optional[int] = None,
        min_tokens: Optional[int] = None,
    ) -> None:
        """Assert token usage is within bounds.

        Args:
            max_tokens: Maximum allowed tokens (optional)
            min_tokens: Minimum expected tokens (optional)

        Raises:
            AssertionError: If token usage out of bounds
        """
        total_tokens = sum(
            call.get("prompt_tokens", 0) + call.get("completion_tokens", 0)
            for call in self._llm_calls
        )

        if max_tokens is not None:
            assert (
                total_tokens <= max_tokens
            ), f"Token usage {total_tokens} exceeds max {max_tokens}"

        if min_tokens is not None:
            assert (
                total_tokens >= min_tokens
            ), f"Token usage {total_tokens} below min {min_tokens}"

    def assert_tool_calls(self, expected_tools: list[str]) -> None:
        """Assert specific tools were called.

        Args:
            expected_tools: List of expected tool names

        Raises:
            AssertionError: If expected tools not called
        """
        called_tools = [call.get("name") for call in self._tool_calls]
        for tool in expected_tools:
            assert (
                tool in called_tools
            ), f"Expected tool '{tool}' to be called, got {called_tools}"

    # ===== Performance Assertions =====

    def assert_duration(self, max_seconds: float) -> None:
        """Assert execution duration is within limit.

        Args:
            max_seconds: Maximum allowed duration in seconds

        Raises:
            AssertionError: If duration exceeds limit
        """
        assert (
            self._duration <= max_seconds
        ), f"Execution took {self._duration:.2f}s, max {max_seconds}s"

    def assert_cost(self, max_cost: float) -> None:
        """Assert execution cost is within budget.

        Args:
            max_cost: Maximum allowed cost in USD

        Raises:
            AssertionError: If cost exceeds budget
        """
        total_cost = sum(call.get("cost", 0.0) for call in self._llm_calls)
        assert (
            total_cost <= max_cost
        ), f"Cost ${total_cost:.4f} exceeds max ${max_cost:.4f}"

    # ===== Structured Output Assertions =====

    def assert_valid_model(self, result: Any, model_class: type) -> None:
        """Assert result is valid instance of Pydantic model.

        Args:
            result: Result to check
            model_class: Expected Pydantic model class

        Raises:
            AssertionError: If result is not instance of model_class
        """
        assert isinstance(
            result, model_class
        ), f"Expected {model_class.__name__}, got {type(result).__name__}"

    def assert_field_value(self, result: Any, field: str, expected: Any) -> None:
        """Assert model field has expected value.

        Args:
            result: Pydantic model instance
            field: Field name
            expected: Expected value

        Raises:
            AssertionError: If field value doesn't match
        """
        actual = getattr(result, field)
        assert actual == expected, f"Expected {field}={expected}, got {actual}"

    # ===== Context Managers =====

    def record_llm_calls(self) -> LLMRecorder:
        """Context manager to record LLM calls.

        Returns:
            LLMRecorder context manager

        Example:
            >>> with self.record_llm_calls():
            ...     result = await self.agent("test")
            >>> self.assert_llm_calls(count=1)
        """
        from .mocking import LLMRecorder

        return LLMRecorder(self._llm_calls)

    def mock_llm(self, response: str) -> LLMMock:
        """Context manager to mock LLM responses.

        Args:
            response: Mock response to return

        Returns:
            LLMMock context manager

        Example:
            >>> with self.mock_llm("Mocked response"):
            ...     result = await self.agent("test")
        """
        from .mocking import LLMMock

        return LLMMock(response)

    def mock_tool(self, tool_name: str, return_value: Any) -> ToolMock:
        """Context manager to mock tool calls.

        Args:
            tool_name: Name of tool to mock
            return_value: Value to return

        Returns:
            ToolMock context manager

        Example:
            >>> with self.mock_tool("search", return_value=[...]):
            ...     result = await self.agent("search query")
        """
        from .mocking import ToolMock

        return ToolMock(tool_name, return_value)

    def measure_time(self) -> Timer:
        """Context manager to measure execution time.

        Returns:
            Timer context manager

        Example:
            >>> with self.measure_time() as timer:
            ...     result = await self.agent("test")
            >>> print(f"Took {timer.duration:.2f}s")
        """
        from .utils import Timer

        return Timer()
