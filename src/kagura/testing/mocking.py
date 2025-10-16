"""Mocking utilities for agent testing."""

from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock, patch


class LLMRecorder:
    """Context manager to record LLM API calls.

    Example:
        >>> with LLMRecorder(storage) as recorder:
        ...     result = await agent("test")
        >>> print(recorder.calls)
    """

    def __init__(self, storage: list[dict[str, Any]]) -> None:
        """Initialize recorder.

        Args:
            storage: List to store recorded calls
        """
        self.storage = storage
        self.original_completion: Any = None

    def __enter__(self) -> "LLMRecorder":
        """Start recording."""
        try:
            import litellm
        except ImportError:
            # If litellm not installed, recording is no-op
            return self

        self.original_completion = litellm.completion

        def recording_completion(*args: Any, **kwargs: Any) -> dict[str, Any]:
            """Wrapper to record call details."""
            result = self.original_completion(*args, **kwargs)

            # Record call metadata
            usage = result.get("usage", {})
            self.storage.append(
                {
                    "model": kwargs.get("model", "unknown"),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }
            )

            return result

        litellm.completion = recording_completion
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop recording."""
        try:
            import litellm
        except ImportError:
            return

        if self.original_completion:
            litellm.completion = self.original_completion


class LLMMock:
    """Context manager to mock LLM responses.

    Example:
        >>> with LLMMock("Mocked response"):
        ...     result = await agent("test")
    """

    def __init__(self, response: str) -> None:
        """Initialize mock.

        Args:
            response: Mock response to return
        """
        self.response = response
        self.patcher: Any = None

    def __enter__(self) -> "LLMMock":
        """Start mocking."""

        async def mock_acompletion(*args: Any, **kwargs: Any) -> dict[str, Any]:
            """Return mock response (async version)."""

            # Create a simple namespace object to hold message content
            class Message:
                def __init__(self, content: str):
                    self.content = content
                    self.tool_calls = None

            class Choice:
                def __init__(self, message: Message):
                    self.message = message

            class Response:
                def __init__(self, content: str):
                    self.choices = [Choice(Message(content))]
                    self.usage = {
                        "prompt_tokens": 10,
                        "completion_tokens": 10,
                        "total_tokens": 20,
                    }

            return Response(self.response)  # type: ignore

        self.patcher = patch("litellm.acompletion", side_effect=mock_acompletion)
        self.patcher.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop mocking."""
        if self.patcher:
            self.patcher.__exit__(*args)


class ToolMock:
    """Context manager to mock tool calls.

    Example:
        >>> with ToolMock("search_tool", return_value=[...]):
        ...     result = await agent("search query")
    """

    def __init__(self, tool_name: str, return_value: Any) -> None:
        """Initialize tool mock.

        Args:
            tool_name: Name of tool to mock
            return_value: Value to return when tool is called
        """
        self.tool_name = tool_name
        self.return_value = return_value
        self.mock: MagicMock = MagicMock(return_value=return_value)

    def __enter__(self) -> "ToolMock":
        """Start mocking tool."""
        # TODO: Implement tool registry patching
        # For now, this is a placeholder
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop mocking tool."""
        pass


@contextmanager
def mock_memory(history: list[dict[str, str]]) -> Iterator[None]:
    """Context manager to mock agent memory.

    Args:
        history: List of message dicts with 'role' and 'content'

    Example:
        >>> with mock_memory([{"role": "user", "content": "Hello"}]):
        ...     result = await agent("Follow-up")
    """
    # TODO: Implement memory mocking
    # This is a placeholder for Phase 2
    yield
