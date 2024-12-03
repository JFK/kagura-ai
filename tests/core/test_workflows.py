from unittest.mock import patch

import pytest
from pydantic import BaseModel

from kagura.core.agent import Agent
from kagura.core.models import ModelRegistry

pytestmark = pytest.mark.asyncio


class TestWorkflows:
    @pytest.mark.skip()
    async def test_sequential_workflow(self):
        """Test sequential workflow execution"""
        # Mock responses for each node in the workflow
        mock_responses = {
            "fetcher": {"content": "Raw content"},
            "processor": {"processed_content": "Processed content"},
            "analyzer": {"analysis": "Content analysis"},
        }

        with patch("kagura.core.agent.Agent.execute") as mock_execute:

            async def mock_node_execution(*args, **kwargs):
                agent_name = args[0].agent_name
                return mock_responses.get(agent_name, {})

            mock_execute.side_effect = mock_node_execution

            workflow_agent = Agent.assigner("test_workflow")
            updates = []

            async for update in await workflow_agent.execute_workflow():
                updates.append(update)

            assert len(updates) == len(mock_responses) + 1  # +1 for completion
            assert updates[-1].get("COMPLETED") == True

    @pytest.mark.skip()
    async def test_conditional_workflow(self):
        """Test workflow with conditional routing"""

        def condition_checker(state):
            return "success" if state.get("success", True) else "retry"

        with patch("kagura.core.agent.Agent.execute") as mock_execute:
            # Test successful path
            mock_execute.return_value = {"success": True, "result": "Success"}

            workflow_agent = Agent.assigner("conditional_workflow")
            updates = []

            async for update in await workflow_agent.execute_workflow():
                updates.append(update)

            assert any(update.get("success") for update in updates)

            # Test retry path
            mock_execute.return_value = {"success": False, "result": "Retry"}
            updates = []

            async for update in await workflow_agent.execute_workflow():
                updates.append(update)

            assert any(update.get("retry") for update in updates)

    @pytest.mark.skip()
    async def test_error_recovery_workflow(self):
        """Test workflow error recovery"""
        with patch("kagura.core.agent.Agent.execute") as mock_execute:
            error_state = {"ERROR_MESSAGE": "Test error", "SUCCESS": False}
            success_state = {"result": "Success", "SUCCESS": True}

            # Simulate error then recovery
            mock_execute.side_effect = [error_state, success_state]

            workflow_agent = Agent.assigner("error_recovery_workflow")
            updates = []

            async for update in await workflow_agent.execute_workflow():
                updates.append(update)

            assert any(update.get("ERROR_MESSAGE") for update in updates)
            assert updates[-1].get("SUCCESS") == True

    @pytest.mark.skip()
    async def test_workflow_state_binding(self):
        """Test state binding between workflow nodes"""

        # Create test state models
        class SourceState(BaseModel):
            data: str

        class TargetState(BaseModel):
            input_data: str

        ModelRegistry.register("SourceState", SourceState)
        ModelRegistry.register("TargetState", TargetState)

        with patch("kagura.core.agent.Agent.execute") as mock_execute:
            source_data = "Test data"
            mock_execute.return_value = SourceState(data=source_data)

            workflow_agent = Agent.assigner("state_binding_workflow")
            updates = []

            async for update in await workflow_agent.execute_workflow():
                updates.append(update)

            # Verify state binding
            target_states = [u for u in updates if isinstance(u, TargetState)]
            assert any(state.input_data == source_data for state in target_states)
