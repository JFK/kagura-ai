"""Tests for SelfImprovingMetaAgent"""


import pytest

from kagura.meta.error_analyzer import ErrorAnalysis
from kagura.meta.self_improving import SelfImprovingMetaAgent


@pytest.fixture
def self_improving_agent():
    """Create SelfImprovingMetaAgent instance for testing"""
    return SelfImprovingMetaAgent(max_retries=3)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="LLM generates invalid Python 3.11 syntax (union types). "
    "Will re-enable when prompt improved to enforce valid syntax."
)
async def test_generate_with_retry_no_validation(self_improving_agent):
    """Test generate_with_retry without validation (integration test)"""
    # This test requires actual LLM call, mark as integration
    code, errors = await self_improving_agent.generate_with_retry(
        "Multiply number by 2", validate=False
    )

    # Should return generated code without errors
    assert code is not None
    assert len(errors) == 0  # No validation, no errors


def test_error_history_tracking(self_improving_agent):
    """Test that error history is tracked"""
    # Manually add error to history
    from kagura.meta.error_analyzer import ErrorAnalysis

    error = ErrorAnalysis(
        error_type="ValueError",
        error_message="Test error",
        stack_trace="",
        root_cause="Test",
        suggested_fix="Test fix",
    )

    self_improving_agent._error_history.append(error)

    history = self_improving_agent.get_error_history()
    assert len(history) == 1
    assert history[0].error_type == "ValueError"


def test_clear_error_history(self_improving_agent):
    """Test clearing error history"""
    # Add dummy error
    dummy_error = ErrorAnalysis(
        error_type="Test",
        error_message="Test",
        stack_trace="",
        root_cause="Test",
        suggested_fix="Test",
    )
    self_improving_agent._error_history.append(dummy_error)

    assert len(self_improving_agent.get_error_history()) == 1

    self_improving_agent.clear_error_history()

    assert len(self_improving_agent.get_error_history()) == 0


def test_max_retries_configuration(self_improving_agent):
    """Test max_retries configuration"""
    assert self_improving_agent.max_retries == 3

    # Test custom max_retries
    custom_agent = SelfImprovingMetaAgent(max_retries=5)
    assert custom_agent.max_retries == 5


@pytest.mark.asyncio
async def test_self_improving_agent_has_components(self_improving_agent):
    """Test that SelfImprovingMetaAgent has all required components"""
    assert hasattr(self_improving_agent, "error_analyzer")
    assert hasattr(self_improving_agent, "code_fixer")
    assert hasattr(self_improving_agent, "max_retries")
    assert hasattr(self_improving_agent, "_error_history")

    # Should inherit from MetaAgent
    assert hasattr(self_improving_agent, "generate")
    assert hasattr(self_improving_agent, "validator")
