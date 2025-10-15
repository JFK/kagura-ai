"""
Tests for chat utility functions
"""

from kagura.chat.utils import extract_response_content


class MockLLMResponse:
    """Mock LLMResponse for testing"""

    def __init__(self, content: str):
        self.content = content


class NestedMockLLMResponse:
    """Mock nested LLMResponse for testing"""

    def __init__(self, content: MockLLMResponse):
        self.content = content


def test_extract_response_content_from_string() -> None:
    """Test extracting content from plain string"""
    result = extract_response_content("Hello, world!")
    assert result == "Hello, world!"


def test_extract_response_content_from_llm_response() -> None:
    """Test extracting content from LLMResponse object"""
    response = MockLLMResponse("Test content")
    result = extract_response_content(response)
    assert result == "Test content"


def test_extract_response_content_from_nested_llm_response() -> None:
    """Test extracting content from nested LLMResponse"""
    inner = MockLLMResponse("Nested content")
    response = NestedMockLLMResponse(inner)
    result = extract_response_content(response)
    assert result == "Nested content"


def test_extract_response_content_from_int() -> None:
    """Test extracting content from other types"""
    result = extract_response_content(42)
    assert result == "42"


def test_extract_response_content_from_none() -> None:
    """Test extracting content from None"""
    result = extract_response_content(None)
    assert result == "None"
