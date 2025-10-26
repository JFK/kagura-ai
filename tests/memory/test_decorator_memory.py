"""Tests for @agent decorator with memory integration."""

import tempfile
from pathlib import Path

from kagura.core.decorators import agent
from kagura.core.memory import MemoryManager


def test_agent_with_memory_enabled():
    """Test agent decorator with enable_memory=True."""

    @agent(enable_memory=True)
    async def test_agent_func(name: str, memory: MemoryManager) -> str:
        """Say hello to {{ name }}"""
        pass

    # Function should have memory enabled attribute
    assert hasattr(test_agent_func, "_enable_memory")
    assert test_agent_func._enable_memory is True  # type: ignore


def test_agent_without_memory():
    """Test agent decorator with enable_memory=False (default)."""

    @agent
    async def test_agent_func(name: str) -> str:
        """Say hello to {{ name }}"""
        pass

    # Function should not have memory enabled
    assert hasattr(test_agent_func, "_enable_memory")
    assert test_agent_func._enable_memory is False  # type: ignore


def test_agent_memory_parameters():
    """Test agent decorator memory parameters are preserved."""

    with tempfile.TemporaryDirectory() as tmpdir:
        persist_dir = Path(tmpdir)

        @agent(enable_memory=True, persist_dir=persist_dir, max_messages=5)
        async def test_agent_func(query: str, memory: MemoryManager) -> str:
            """Process {{ query }}"""
            pass

        # Should have memory enabled
        assert test_agent_func._enable_memory is True  # type: ignore


def test_agent_without_memory_param():
    """Test agent can be defined without memory parameter."""

    @agent(enable_memory=True)
    async def test_agent_func(query: str) -> str:
        """Process {{ query }}"""
        pass

    # Should still work without error
    assert hasattr(test_agent_func, "_enable_memory")
