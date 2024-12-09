from typing import List, Optional
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from kagura.core.agent import Agent
from kagura.core.models import (
    BaseResponseModel,
    ModelRegistry,
    validate_required_state_fields,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def sample_state_model():
    """Sample state model for testing"""

    class TestState(BaseModel):
        input_text: str
        output_text: str = ""
        error_message: Optional[str] = None
        success: bool = True

    ModelRegistry.register("TestState", TestState)
    return TestState


class TestStateManagement:
    async def test_state_model_validation(self, sample_state_model):
        """Test state model validation"""
        # Valid state
        state = sample_state_model(input_text="test", output_text="result")
        assert state.input_text == "test"
        assert state.output_text == "result"
        assert state.success == True

        # Invalid state (missing required field)
        with pytest.raises(ValidationError):
            sample_state_model(output_text="result")

    async def test_custom_model_registration(self):
        """Test custom model registration and retrieval"""

        class CustomModel(BaseModel):
            name: str
            value: int
            tags: Optional[List[str]] = None

        ModelRegistry.register("CustomModel", CustomModel)
        retrieved_model = ModelRegistry.get("CustomModel")

        assert retrieved_model == CustomModel
        assert "name" in ModelRegistry.get_fields("CustomModel")
        assert "value" in ModelRegistry.get_fields("CustomModel")
        assert "tags" in ModelRegistry.get_fields("CustomModel")

    async def test_state_field_validation(self, sample_state_model):
        """Test state field validation"""
        state = sample_state_model(input_text="test")

        # Valid validation
        try:
            validate_required_state_fields(state, ["input_text"])
        except Exception as e:
            pytest.fail(f"Validation should not raise an error: {str(e)}")

        # Invalid validation (missing field)
        with pytest.raises(Exception):
            validate_required_state_fields(state, ["non_existent_field"])

    async def test_state_error_handling(self, sample_state_model):
        """Test state error handling"""
        state = sample_state_model(input_text="test")

        # Set error state
        state.error_message = "Test error"
        state.success = False

        assert state.error_message == "Test error"
        assert state.success == False

        # Clear error state
        state.error_message = None
        state.success = True

        assert state.error_message is None
        assert state.success == True

    def teardown_method(self):
        """Clean up after each test"""
        ModelRegistry._models.clear()
        ModelRegistry._model_fields.clear()

    @pytest.mark.asyncio
    async def test_input_query_storage(self):
        input_query = {"text_input": "Sample text", "parameters": {"key": "value"}}
        mock_return_value = BaseResponseModel(INPUT_QUERY=input_query)

        with patch(
            "kagura.core.agent.Agent.execute", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_return_value

            agent = Agent.assigner("test_atomic_agent")
            result = await agent.execute(
                {"text_input": "Test input", "parameters": {"type": "test"}}
            )

            assert isinstance(result.INPUT_QUERY, dict)
            assert result.INPUT_QUERY["text_input"] == "Sample text"
            assert result.INPUT_QUERY == input_query
            mock_execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_text_output_conversion(self):
        mock_return_value = BaseResponseModel(TEXT_OUTPUT="Mocked output text")

        with patch(
            "kagura.core.agent.Agent.execute", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_return_value

            agent = Agent.assigner("test_atomic_agent")
            result = await agent.execute(
                {"text_input": "Test input", "parameters": {"type": "test"}}
            )

            assert result.TEXT_OUTPUT is not None
            assert result.TEXT_OUTPUT == "Mocked output text"
            mock_execute.assert_awaited_once()
