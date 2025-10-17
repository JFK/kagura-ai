"""Tests for mocking utilities."""

import pytest

from kagura.testing.mocking import LLMMock, LLMRecorder, ToolMock
from kagura.testing.utils import Timer


def test_llm_recorder_initialization():
    """Test LLMRecorder initialization."""
    storage: list = []
    recorder = LLMRecorder(storage)

    assert recorder.storage is storage
    assert recorder.original_completion is None


def test_llm_recorder_context():
    """Test LLMRecorder context manager."""
    storage: list = []

    with LLMRecorder(storage) as recorder:
        assert recorder.storage is storage

    # No litellm calls in this test, so storage should be empty
    assert len(storage) == 0


def test_llm_mock_initialization():
    """Test LLMMock initialization."""
    mock = LLMMock("test response")

    assert mock.response == "test response"
    assert mock.litellm_patcher is None  # Not started yet
    assert mock.openai_patcher is None  # Not started yet


def test_llm_mock_context():
    """Test LLMMock context manager."""
    with LLMMock("test response") as mock:
        assert mock.litellm_patcher is not None  # Patching LiteLLM
        assert mock.openai_patcher is not None  # Patching OpenAI SDK

    # Patchers should be cleaned up
    assert mock.litellm_patcher is not None  # Still exists but exited
    assert mock.openai_patcher is not None  # Still exists but exited


def test_tool_mock_initialization():
    """Test ToolMock initialization."""
    mock_results = [{"result": "data"}]
    tool_mock = ToolMock("search_tool", mock_results)

    assert tool_mock.tool_name == "search_tool"
    assert tool_mock.return_value == mock_results
    assert tool_mock.mock.return_value == mock_results


def test_tool_mock_context():
    """Test ToolMock context manager."""
    mock_results = [{"result": "data"}]

    with ToolMock("search_tool", mock_results) as tool_mock:
        assert tool_mock.tool_name == "search_tool"
        assert tool_mock.return_value == mock_results

    # No errors should occur
