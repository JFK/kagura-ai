"""Tests for MCP auto-logging middleware.

Related: Issue #400 - Auto-remember MCP tool requests and results
"""

import os

import pytest

from kagura.mcp.middleware import (
    EXCLUDED_TOOLS,
    is_auto_logging_enabled,
    log_tool_call_to_memory,
    should_log_tool,
)


class TestAutoLoggingEnabled:
    """Tests for is_auto_logging_enabled()"""

    def test_enabled_by_default(self):
        """Test that auto-logging is enabled by default."""
        # Remove env var if present
        os.environ.pop("KAGURA_DISABLE_AUTO_LOGGING", None)
        assert is_auto_logging_enabled() is True

    def test_disabled_by_env_var_true(self, monkeypatch):
        """Test KAGURA_DISABLE_AUTO_LOGGING=true disables logging."""
        monkeypatch.setenv("KAGURA_DISABLE_AUTO_LOGGING", "true")
        assert is_auto_logging_enabled() is False

    def test_disabled_by_env_var_1(self, monkeypatch):
        """Test KAGURA_DISABLE_AUTO_LOGGING=1 disables logging."""
        monkeypatch.setenv("KAGURA_DISABLE_AUTO_LOGGING", "1")
        assert is_auto_logging_enabled() is False

    def test_disabled_by_env_var_yes(self, monkeypatch):
        """Test KAGURA_DISABLE_AUTO_LOGGING=yes disables logging."""
        monkeypatch.setenv("KAGURA_DISABLE_AUTO_LOGGING", "yes")
        assert is_auto_logging_enabled() is False


class TestShouldLogTool:
    """Tests for should_log_tool() - Critical for recursion prevention"""

    def test_excludes_memory_store(self):
        """CRITICAL: memory_store must be excluded to prevent infinite loop."""
        assert should_log_tool("memory_store") is False

    def test_excludes_memory_recall(self):
        """CRITICAL: memory_recall must be excluded."""
        assert should_log_tool("memory_recall") is False

    def test_excludes_memory_search(self):
        """CRITICAL: memory_search must be excluded."""
        assert should_log_tool("memory_search") is False

    def test_excludes_memory_delete(self):
        """memory_delete should be excluded."""
        assert should_log_tool("memory_delete") is False

    def test_excludes_memory_get_tool_history(self):
        """CRITICAL: memory_get_tool_history must be excluded (self-reference)."""
        assert should_log_tool("memory_get_tool_history") is False

    def test_excludes_all_memory_tools_in_list(self):
        """All tools in EXCLUDED_TOOLS must be excluded."""
        for tool in EXCLUDED_TOOLS:
            assert should_log_tool(tool) is False, (
                f"{tool} should be excluded but wasn't"
            )

    def test_excludes_any_memory_prefix(self):
        """Any tool starting with 'memory_' should be excluded (catch-all)."""
        assert should_log_tool("memory_custom_tool") is False
        assert should_log_tool("memory_foo") is False
        assert should_log_tool("memory_") is False

    def test_allows_non_memory_tools(self):
        """Non-memory tools should be allowed."""
        assert should_log_tool("brave_web_search") is True
        assert should_log_tool("file_read") is True
        assert should_log_tool("github_issue_view") is True
        assert should_log_tool("youtube_summarize") is True

    def test_respects_global_disable(self, monkeypatch):
        """When globally disabled, all tools should return False."""
        monkeypatch.setenv("KAGURA_DISABLE_AUTO_LOGGING", "true")
        assert should_log_tool("brave_web_search") is False
        assert should_log_tool("file_read") is False


class TestLogToolCallToMemory:
    """Tests for log_tool_call_to_memory()"""

    @pytest.mark.asyncio
    async def test_logs_tool_call(self):
        """Test actual logging to memory."""
        import asyncio

        user_id = "test_middleware_user"
        tool_name = "brave_web_search"
        arguments = {"query": "test", "count": 5}
        result = "Test search results..."

        # Log tool call (now fire-and-forget with create_task)
        await log_tool_call_to_memory(user_id, tool_name, arguments, result)

        # Wait for async task to complete (fire-and-forget means we need to wait)
        await asyncio.sleep(0.5)

        # Verify stored in memory
        from kagura.mcp.builtin.memory import memory_get_tool_history

        history = await memory_get_tool_history(
            user_id, tool_filter=tool_name, limit="1"
        )

        import json

        data = json.loads(history)

        assert len(data) > 0
        assert data[0]["tool"] == tool_name
        assert data[0]["args"]["query"] == "test"
        assert "Test search results" in data[0]["result_preview"]

    @pytest.mark.asyncio
    async def test_truncates_long_results(self, monkeypatch):
        """Test large results are truncated."""
        import asyncio

        monkeypatch.setenv("KAGURA_AUTO_LOG_MAX_LENGTH", "100")

        long_result = "x" * 500  # 500 chars
        user_id = "test_truncate_user"

        await log_tool_call_to_memory(
            user_id=user_id,
            tool_name="test_tool",
            arguments={},
            result=long_result,
        )

        # Wait for async task to complete
        await asyncio.sleep(0.5)

        # Verify truncated in storage
        from kagura.mcp.builtin.memory import memory_get_tool_history

        history = await memory_get_tool_history(
            user_id, tool_filter="test_tool", limit="1"
        )

        import json

        data = json.loads(history)

        # Should be truncated to 100 + "... (truncated)"
        assert len(data[0]["result_preview"]) <= 110
        assert (
            "truncated" in data[0]["result_preview"]
            or len(data[0]["result_preview"]) == 100
        )

    @pytest.mark.asyncio
    async def test_skips_memory_tools(self):
        """CRITICAL: Memory tools should NOT be logged (prevent recursion)."""
        user_id = "test_recursion_user"

        # Try to log memory_store (should be skipped silently)
        await log_tool_call_to_memory(
            user_id=user_id,
            tool_name="memory_store",
            arguments={},
            result="should not be logged",
        )

        # Verify NOT stored
        from kagura.mcp.builtin.memory import memory_get_tool_history

        history = await memory_get_tool_history(
            user_id, tool_filter="memory_store", limit="10"
        )

        import json

        data = json.loads(history)

        # Should have no results (memory_store calls not logged)
        for entry in data:
            assert entry["tool"] != "memory_store", (
                "memory_store should never be logged!"
            )

    @pytest.mark.asyncio
    async def test_non_blocking_on_error(self):
        """Test that logging errors don't crash tool execution."""
        # Force an error (e.g., None user_id)
        try:
            await log_tool_call_to_memory(
                user_id=None,  # Invalid - will cause error
                tool_name="test",
                arguments={},
                result="test",
            )
            # Should not raise exception (non-blocking)
        except Exception as e:
            pytest.fail(f"Logging should be non-blocking, but raised: {e}")


class TestExcludedToolsComprehensive:
    """Comprehensive test of excluded tools list"""

    def test_all_memory_tools_excluded(self):
        """Test comprehensive exclusion of memory tools."""
        memory_tools = [
            "memory_store",
            "memory_recall",
            "memory_search",
            "memory_delete",
            "memory_feedback",
            "memory_list",
            "memory_stats",
            "memory_fuzzy_recall",
            "memory_timeline",
            "memory_get_tool_history",
            "memory_search_ids",
            "memory_fetch",
            "memory_search_hybrid",
        ]

        for tool in memory_tools:
            assert should_log_tool(tool) is False, f"{tool} should be excluded"

    def test_excluded_tools_constant_complete(self):
        """Verify EXCLUDED_TOOLS constant includes all critical tools."""
        critical_tools = [
            "memory_store",  # Would cause direct recursion
            "memory_recall",
            "memory_get_tool_history",  # Self-reference
        ]

        for tool in critical_tools:
            assert tool in EXCLUDED_TOOLS, (
                f"CRITICAL: {tool} must be in EXCLUDED_TOOLS!"
            )
