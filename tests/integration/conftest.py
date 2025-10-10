"""Fixtures for integration tests"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_llm_response():
    """Fixture to mock LLM responses"""
    def _mock(response_text: str):
        # Create message mock with tool_calls explicitly set to None
        message_mock = MagicMock(
            content=response_text,
            tool_calls=None
        )
        return patch(
            'litellm.acompletion',
            new_callable=AsyncMock,
            return_value=MagicMock(
                choices=[
                    MagicMock(message=message_mock)
                ]
            )
        )
    return _mock


@pytest.fixture
async def test_agent():
    """Fixture providing a test agent"""
    from kagura import agent

    @agent(model="gpt-4o-mini")
    async def test_func(query: str) -> str:
        '''Answer: {{ query }}'''
        pass

    return test_func
