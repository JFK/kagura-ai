"""Tests for pytest plugin."""

import pytest

from kagura.testing import AgentTestCase


def test_agent_context_fixture(agent_context):
    """Test agent_context fixture provides AgentTestCase."""
    assert isinstance(agent_context, AgentTestCase)
    assert agent_context.agent is None
    assert agent_context._llm_calls == []


def test_agent_context_fixture_usage(agent_context):
    """Test using agent_context fixture for assertions."""
    # Should be able to use assertion methods
    agent_context.assert_contains("hello world", "hello")
    agent_context.assert_not_empty("test")

    # Should raise on failure
    with pytest.raises(AssertionError):
        agent_context.assert_contains("hello", "goodbye")


@pytest.mark.agent
def test_agent_marker():
    """Test that @pytest.mark.agent works."""
    # This test should be marked with 'agent'
    assert True


@pytest.mark.benchmark
def test_benchmark_marker():
    """Test that @pytest.mark.benchmark works."""
    # This test should be marked with 'benchmark'
    assert True
