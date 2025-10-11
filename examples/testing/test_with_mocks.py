"""Testing with Mocks Example

This example demonstrates how to test agents with mocked LLM responses
to avoid API calls and ensure deterministic testing.
"""

import pytest
from unittest.mock import AsyncMock, patch
from kagura import agent
from kagura.testing import AgentTestCase


# Define agents for testing
@agent(model="gpt-4o-mini")
async def data_analyzer(data: str) -> str:
    """Analyze the following data and return a JSON summary: {{ data }}"""
    pass


@agent(model="gpt-4o-mini", enable_memory=True)
async def chatbot(message: str) -> str:
    """Respond to: {{ message }}"""
    pass


@agent(model="gpt-4o-mini")
async def code_reviewer(code: str) -> str:
    """Review this code and provide feedback: {{ code }}"""
    pass


# Test Class 1: Basic Mocking
class TestWithBasicMocks(AgentTestCase):
    """Test agents with basic LLM mocking."""

    @pytest.mark.asyncio
    async def test_with_mocked_response(self):
        """Test agent with a mocked LLM response."""
        mock_response = '{"status": "success", "count": 5}'

        with self.mock_llm(mock_response):
            result = await data_analyzer("sample data")

            # Verify the mocked response is returned
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_multiple_calls_with_mock(self):
        """Test multiple agent calls with same mock."""
        mock_response = '{"analysis": "complete"}'

        with self.mock_llm(mock_response):
            result1 = await data_analyzer("data set 1")
            result2 = await data_analyzer("data set 2")

            # Both should return the mocked response
            assert result1 == mock_response
            assert result2 == mock_response


# Test Class 2: Sequential Mocking
class TestWithSequentialMocks(AgentTestCase):
    """Test agents with different mocked responses."""

    @pytest.mark.asyncio
    async def test_conversation_with_mocks(self):
        """Test a multi-turn conversation with mocked responses."""
        # Mock first response
        with self.mock_llm("Hello! How can I help you?"):
            response1 = await chatbot("Hi")
            assert "Hello" in response1

        # Mock second response
        with self.mock_llm("Python is a programming language."):
            response2 = await chatbot("What is Python?")
            assert "Python" in response2


# Test Class 3: Testing Without API Calls
class TestCodeReviewerOffline(AgentTestCase):
    """Test code reviewer agent without making API calls."""

    @pytest.mark.asyncio
    async def test_review_logic_without_api(self):
        """Test the agent's behavior without actual API calls."""
        test_code = """
def hello():
    print('Hello World')
        """

        mock_review = """
Good: Simple and clear function.
Improvement: Add docstring and type hints.
        """

        with self.mock_llm(mock_review):
            result = await code_reviewer(test_code)

            # Verify we got the mocked review
            self.assert_contains(result, "Good")
            self.assert_contains(result, "Improvement")

    @pytest.mark.asyncio
    async def test_handles_different_code_types(self):
        """Test with different code types (still mocked)."""
        test_cases = [
            ("def foo(): pass", "Mock review for simple function"),
            ("class Bar: pass", "Mock review for class"),
            ("import sys", "Mock review for import"),
        ]

        for code, expected_mock in test_cases:
            with self.mock_llm(expected_mock):
                result = await code_reviewer(code)
                assert result == expected_mock


# Test Class 4: Advanced Mocking with Side Effects
class TestWithSideEffects:
    """Test agents with mock side effects (advanced patterns)."""

    @pytest.mark.asyncio
    async def test_with_mock_side_effect(self):
        """Test agent with mock that has side effects."""

        @agent(model="gpt-4o-mini")
        async def counter_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        # Create mock responses that return different values on each call
        response_index = 0
        mock_responses = [
            "First response",
            "Second response",
            "Third response"
        ]

        async def mock_side_effect(*args, **kwargs):
            nonlocal response_index
            response = mock_responses[response_index]
            response_index += 1

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

            return Response(response)

        with patch('litellm.acompletion', side_effect=mock_side_effect) as mock_generate:
            # Each call gets a different response
            result1 = await counter_agent("query 1")
            result2 = await counter_agent("query 2")
            result3 = await counter_agent("query 3")

            # Verify each call returned the correct response
            assert result1 == "First response"
            assert result2 == "Second response"
            assert result3 == "Third response"
            assert mock_generate.call_count == 3

    @pytest.mark.asyncio
    async def test_with_exception_mock(self):
        """Test agent behavior when LLM raises exception."""

        @agent(model="gpt-4o-mini")
        async def test_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        async def mock_exception(*args, **kwargs):
            raise Exception("API Error")

        with patch('litellm.acompletion', side_effect=mock_exception):
            # Verify exception is propagated
            with pytest.raises(Exception, match="API Error"):
                await test_agent("test query")


# Test Class 5: Testing Prompt Generation (Without LLM)
class TestPromptGeneration:
    """Test prompt generation logic without calling LLM."""

    @pytest.mark.asyncio
    async def test_prompt_template_rendering(self):
        """Test that prompt template is correctly rendered."""

        @agent(model="gpt-4o-mini")
        async def template_agent(name: str, age: int) -> str:
            """Create profile for {{ name }} who is {{ age }} years old"""
            pass

        captured_prompt = None

        async def mock_capture(*args, **kwargs):
            nonlocal captured_prompt
            # Capture the prompt from messages
            messages = kwargs.get("messages", [])
            if messages:
                captured_prompt = messages[0].get("content", "")

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

            return Response("Mocked profile")

        with patch('litellm.acompletion', side_effect=mock_capture) as mock_generate:
            result = await template_agent("Alice", age=30)

            # Verify the mock was called
            assert mock_generate.called
            # Verify the rendered prompt contains the values
            assert captured_prompt is not None
            assert "Alice" in captured_prompt
            assert "30" in captured_prompt
            assert result == "Mocked profile"


# Test Class 6: Cost and Performance Testing with Mocks
class TestCostOptimization(AgentTestCase):
    """Test cost optimization strategies using mocks."""

    @pytest.mark.asyncio
    async def test_agent_calls_llm_once(self):
        """Verify agent makes only one LLM call."""

        @agent(model="gpt-4o-mini")
        async def efficient_agent(query: str) -> str:
            """Answer: {{ query }}"""
            pass

        async def mock_response(*args, **kwargs):
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

            return Response("Mocked response")

        with patch('litellm.acompletion', side_effect=mock_response) as mock_generate:
            result = await efficient_agent("test query")

            # Should call LLM exactly once
            assert mock_generate.call_count == 1
            assert result == "Mocked response"

    @pytest.mark.asyncio
    async def test_cached_responses_no_llm_call(self):
        """Test that cached responses don't call LLM."""

        @agent(model="gpt-4o-mini", enable_memory=True)
        async def caching_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        async def mock_response(*args, **kwargs):
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

            return Response("Cached response")

        with patch('litellm.acompletion', side_effect=mock_response) as mock_generate:
            # First call should hit LLM
            result1 = await caching_agent("same query")
            first_call_count = mock_generate.call_count

            # Subsequent identical calls might be cached
            # (Actual behavior depends on caching implementation)
            result2 = await caching_agent("same query")

            # This test documents expected behavior
            # Note: Current implementation doesn't cache, so both calls hit LLM
            assert result1 == "Cached response"
            assert result2 == "Cached response"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
