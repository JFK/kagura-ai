"""Fixtures for integration tests"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_llm_response():
    """Fixture to mock LLM responses"""
    def _mock(response_text: str):
        return patch(
            'litellm.acompletion',
            new_callable=AsyncMock,
            return_value=MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(content=response_text)
                    )
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
