"""pytest plugin for Kagura agent testing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest  # type: ignore

if TYPE_CHECKING:
    from kagura.testing import AgentTestCase


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for agent testing.

    Args:
        config: pytest configuration object
    """
    config.addinivalue_line(
        "markers",
        "agent: mark test as agent test (for agent-specific testing)",
    )
    config.addinivalue_line(
        "markers",
        "benchmark: mark test as performance benchmark",
    )


@pytest.fixture
def agent_context() -> AgentTestCase:
    """Provide agent testing context.

    Returns:
        AgentTestCase instance for use in tests

    Example:
        >>> def test_with_context(agent_context):
        ...     agent_context.assert_contains("hello world", "hello")
    """
    from kagura.testing import AgentTestCase

    return AgentTestCase()
