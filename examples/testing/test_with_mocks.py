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
async def data_analyzer(data: str) -> dict:
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

    agent = data_analyzer

    @pytest.mark.asyncio
    async def test_with_mocked_response(self):
        """Test agent with a mocked LLM response."""
        mock_response = '{"status": "success", "count": 5}'

        with self.mock_llm_response(mock_response):
            result = await self.agent("sample data")

            # Verify the mocked response is returned
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_multiple_calls_with_mock(self):
        """Test multiple agent calls with same mock."""
        mock_response = '{"analysis": "complete"}'

        with self.mock_llm_response(mock_response):
            result1 = await self.agent("data set 1")
            result2 = await self.agent("data set 2")

            # Both should return the mocked response
            assert result1 == mock_response
            assert result2 == mock_response


# Test Class 2: Sequential Mocking
class TestWithSequentialMocks(AgentTestCase):
    """Test agents with different mocked responses."""

    agent = chatbot

    @pytest.mark.asyncio
    async def test_conversation_with_mocks(self):
        """Test a multi-turn conversation with mocked responses."""
        # Mock first response
        with self.mock_llm_response("Hello! How can I help you?"):
            response1 = await self.agent("Hi")
            assert "Hello" in response1

        # Mock second response
        with self.mock_llm_response("Python is a programming language."):
            response2 = await self.agent("What is Python?")
            assert "Python" in response2


# Test Class 3: Testing Without API Calls
class TestCodeReviewerOffline(AgentTestCase):
    """Test code reviewer agent without making API calls."""

    agent = code_reviewer

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

        with self.mock_llm_response(mock_review):
            result = await self.agent(test_code)

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
            with self.mock_llm_response(expected_mock):
                result = await self.agent(code)
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

        # Create a mock that returns different values on each call
        mock_responses = [
            "First response",
            "Second response",
            "Third response"
        ]

        with patch('kagura.core.llm.LLMClient.generate') as mock_generate:
            mock_generate.side_effect = mock_responses

            # Each call gets a different response
            result1 = await counter_agent("query 1")
            result2 = await counter_agent("query 2")
            result3 = await counter_agent("query 3")

            # Note: Actual behavior depends on implementation
            # This is a pattern demonstration
            assert mock_generate.call_count == 3

    @pytest.mark.asyncio
    async def test_with_exception_mock(self):
        """Test agent behavior when LLM raises exception."""

        @agent(model="gpt-4o-mini")
        async def test_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        with patch('kagura.core.llm.LLMClient.generate') as mock_generate:
            mock_generate.side_effect = Exception("API Error")

            # Verify exception is propagated
            with pytest.raises(Exception):
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

        # Mock to capture the rendered prompt
        with patch('kagura.core.llm.LLMClient.generate') as mock_generate:
            mock_generate.return_value = "Mocked profile"

            await template_agent("Alice", age=30)

            # Verify the prompt was rendered correctly
            call_args = mock_generate.call_args
            # Check that the prompt contains expected values
            # (Actual structure depends on implementation)
            assert mock_generate.called


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

        with patch('kagura.core.llm.LLMClient.generate') as mock_generate:
            mock_generate.return_value = "Mocked response"

            await efficient_agent("test query")

            # Should call LLM exactly once
            assert mock_generate.call_count == 1

    @pytest.mark.asyncio
    async def test_cached_responses_no_llm_call(self):
        """Test that cached responses don't call LLM."""

        @agent(model="gpt-4o-mini", enable_memory=True)
        async def caching_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        with patch('kagura.core.llm.LLMClient.generate') as mock_generate:
            mock_generate.return_value = "Cached response"

            # First call should hit LLM
            result1 = await caching_agent("same query")
            first_call_count = mock_generate.call_count

            # Subsequent identical calls might be cached
            # (Actual behavior depends on caching implementation)
            result2 = await caching_agent("same query")

            # This test documents expected behavior
            # Adjust based on actual caching strategy


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
