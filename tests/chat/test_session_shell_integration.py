"""Integration tests for shell tool in chat session."""

import pytest

from kagura.chat.session import _shell_exec_tool_wrapper


class TestShellToolIntegration:
    """Tests for shell tool integration with chat agent."""

    @pytest.mark.asyncio
    async def test_shell_tool_wrapper_exists(self):
        """Test that shell tool wrapper is callable."""
        assert callable(_shell_exec_tool_wrapper)

    @pytest.mark.asyncio
    async def test_shell_tool_wrapper_signature(self):
        """Test shell tool wrapper has correct signature."""
        import inspect

        sig = inspect.signature(_shell_exec_tool_wrapper)
        params = list(sig.parameters.keys())

        assert "command" in params

    @pytest.mark.asyncio
    async def test_shell_tool_wrapper_basic_execution(self):
        """Test that shell tool wrapper can be imported and used."""
        # Just verify it exists and is properly structured
        # Actual execution is tested in test_shell_tool.py
        assert _shell_exec_tool_wrapper.__name__ == "_shell_exec_tool_wrapper"
        assert _shell_exec_tool_wrapper.__doc__ is not None
