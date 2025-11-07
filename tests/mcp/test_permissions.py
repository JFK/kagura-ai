"""Tests for MCP tool permission system."""

import pytest

from kagura.mcp.permissions import (
    TOOL_PERMISSIONS,
    get_allowed_tools,
    get_denied_tools,
    get_tool_permission_info,
    is_tool_allowed,
)


class TestIsToolAllowed:
    """Test is_tool_allowed function."""

    def test_local_context_allows_all_tools(self):
        """Test that local context allows all tools."""
        # Safe tools
        assert is_tool_allowed("memory_store", "local") is True
        assert is_tool_allowed("brave_web_search", "local") is True

        # Dangerous tools
        assert is_tool_allowed("file_read", "local") is True
        assert is_tool_allowed("shell_exec", "local") is True
        assert is_tool_allowed("file_write", "local") is True

    def test_remote_context_allows_safe_tools(self):
        """Test that remote context allows safe tools."""
        assert is_tool_allowed("memory_store", "remote") is True
        assert is_tool_allowed("memory_recall", "remote") is True
        assert is_tool_allowed("brave_web_search", "remote") is True
        assert is_tool_allowed("youtube_summarize", "remote") is True

    def test_remote_context_denies_dangerous_tools(self):
        """Test that remote context denies dangerous tools."""
        # File operations
        assert is_tool_allowed("file_read", "remote") is False
        assert is_tool_allowed("file_write", "remote") is False
        assert is_tool_allowed("dir_list", "remote") is False

        # Shell execution
        assert is_tool_allowed("shell_exec", "remote") is False

        # Media operations
        assert is_tool_allowed("media_open_audio", "remote") is False
        assert is_tool_allowed("media_open_image", "remote") is False
        assert is_tool_allowed("media_open_video", "remote") is False

    def test_unknown_tools_denied_by_default(self):
        """Test that unknown tools are denied in remote context (fail-safe)."""
        assert is_tool_allowed("unknown_tool", "remote") is False
        assert is_tool_allowed("new_dangerous_tool", "remote") is False

    def test_unknown_tools_allowed_in_local(self):
        """Test that unknown tools are allowed in local context."""
        assert is_tool_allowed("unknown_tool", "local") is True


class TestGetAllowedTools:
    """Test get_allowed_tools function."""

    def test_local_context_returns_all_tools(self):
        """Test that local context returns all tools."""
        tools = ["memory_store", "file_read", "brave_web_search", "shell_exec"]
        allowed = get_allowed_tools(tools, "local")
        assert allowed == tools

    def test_remote_context_filters_dangerous_tools(self):
        """Test that remote context filters dangerous tools."""
        tools = ["memory_store", "file_read", "brave_web_search", "shell_exec"]
        allowed = get_allowed_tools(tools, "remote")

        # Should include safe tools only
        assert "memory_store" in allowed
        assert "brave_web_search" in allowed

        # Should exclude dangerous tools
        assert "file_read" not in allowed
        assert "shell_exec" not in allowed

    def test_empty_list(self):
        """Test with empty tool list."""
        assert get_allowed_tools([], "remote") == []


class TestGetDeniedTools:
    """Test get_denied_tools function."""

    def test_remote_context_returns_dangerous_tools(self):
        """Test that remote context returns dangerous tools."""
        tools = ["memory_store", "file_read", "brave_web_search", "shell_exec"]
        denied = get_denied_tools(tools, "remote")

        # Should include dangerous tools only
        assert "file_read" in denied
        assert "shell_exec" in denied

        # Should exclude safe tools
        assert "memory_store" not in denied
        assert "brave_web_search" not in denied

    def test_local_context_returns_empty(self):
        """Test that local context returns empty list."""
        tools = ["memory_store", "file_read", "brave_web_search", "shell_exec"]
        denied = get_denied_tools(tools, "local")
        assert denied == []


class TestGetToolPermissionInfo:
    """Test get_tool_permission_info function."""

    def test_safe_tool_info(self):
        """Test info for safe tools."""
        info = get_tool_permission_info("memory_store")
        assert info["remote"] is True
        reason = str(info["reason"])
        assert "safe" in reason.lower()

    def test_file_tool_info(self):
        """Test info for file tools."""
        info = get_tool_permission_info("file_read")
        assert info["remote"] is False
        reason = str(info["reason"])
        assert "filesystem" in reason.lower()

    def test_shell_tool_info(self):
        """Test info for shell execution."""
        info = get_tool_permission_info("shell_exec")
        assert info["remote"] is False
        reason = str(info["reason"])
        assert "shell" in reason.lower() or "command" in reason.lower()

    def test_media_tool_info(self):
        """Test info for media tools."""
        info = get_tool_permission_info("media_open_audio")
        assert info["remote"] is False
        reason = str(info["reason"])
        assert "application" in reason.lower()

    def test_unknown_tool_info(self):
        """Test info for unknown tools."""
        info = get_tool_permission_info("unknown_tool")
        assert info["remote"] is False
        reason = str(info["reason"])
        assert "unknown" in reason.lower() or "deny" in reason.lower()


class TestToolPermissionsConfig:
    """Test TOOL_PERMISSIONS configuration."""

    def test_all_memory_tools_are_safe(self):
        """Test that all memory tools are marked as safe."""
        memory_tools = [
            "memory_store",
            "memory_recall",
            "memory_search",
            "memory_list",
            "memory_delete",
            "memory_feedback",
        ]

        for tool in memory_tools:
            assert TOOL_PERMISSIONS[tool]["remote"] is True, f"{tool} should be safe"

    def test_all_file_tools_are_dangerous(self):
        """Test that all file tools are marked as dangerous."""
        file_tools = ["file_read", "file_write", "dir_list"]

        for tool in file_tools:
            assert TOOL_PERMISSIONS[tool]["remote"] is False, (
                f"{tool} should be dangerous"
            )

    def test_web_tools_are_safe(self):
        """Test that web/API tools are marked as safe."""
        web_tools = ["web_scrape", "brave_web_search", "brave_news_search"]

        for tool in web_tools:
            assert TOOL_PERMISSIONS[tool]["remote"] is True, f"{tool} should be safe"

    def test_shell_exec_is_dangerous(self):
        """Test that shell_exec is marked as dangerous."""
        assert TOOL_PERMISSIONS["shell_exec"]["remote"] is False


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_typical_remote_tool_list(self):
        """Test typical remote access scenario."""
        # All tools that might be available
        all_tools = [
            "memory_store",
            "memory_recall",
            "file_read",
            "file_write",
            "brave_web_search",
            "shell_exec",
            "youtube_summarize",
        ]

        allowed = get_allowed_tools(all_tools, "remote")
        denied = get_denied_tools(all_tools, "remote")

        # Should allow memory, web, youtube
        assert len(allowed) == 4
        assert "memory_store" in allowed
        assert "brave_web_search" in allowed
        assert "youtube_summarize" in allowed

        # Should deny file, shell
        assert len(denied) == 3
        assert "file_read" in denied
        assert "file_write" in denied
        assert "shell_exec" in denied

    def test_chatgpt_connector_scenario(self):
        """Test ChatGPT Connector scenario (remote access)."""
        # Tools that should be safe for ChatGPT to use
        safe_tools = [
            "memory_store",
            "memory_recall",
            "memory_search",
            "brave_web_search",
            "youtube_summarize",
        ]

        for tool in safe_tools:
            assert is_tool_allowed(tool, "remote") is True, (
                f"{tool} should be allowed for ChatGPT"
            )

    def test_local_claude_code_scenario(self):
        """Test local Claude Code scenario (all tools available)."""
        # All tools should be available locally
        all_tools = [
            "memory_store",
            "file_read",
            "shell_exec",
            "media_open_image",
        ]

        for tool in all_tools:
            assert is_tool_allowed(tool, "local") is True, (
                f"{tool} should be allowed locally"
            )


class TestToolRegistrationCompleteness:
    """Test that all tools are registered in TOOL_PERMISSIONS."""

    def test_all_tools_registered_in_permissions(self):
        """Ensure every @tool decorated function is in TOOL_PERMISSIONS."""
        from kagura.core.tool_registry import tool_registry

        registered = set(tool_registry.get_all().keys())
        permissions = set(TOOL_PERMISSIONS.keys())

        missing = registered - permissions
        assert len(missing) == 0, (
            f"Missing from TOOL_PERMISSIONS ({len(missing)} tools): {sorted(missing)}"
        )

    @pytest.mark.skip(reason="Tool registration timing issue in CI - TODO: fix in v4.3.1")
    def test_no_orphan_permissions(self):
        """Ensure TOOL_PERMISSIONS doesn't have non-existent tools."""
        from kagura.core.tool_registry import tool_registry

        registered = set(tool_registry.get_all().keys())
        permissions = set(TOOL_PERMISSIONS.keys())

        orphans = permissions - registered
        assert len(orphans) == 0, (
            f"Orphan permissions ({len(orphans)} tools): {sorted(orphans)}"
        )


class TestNewToolPermissions:
    """Test permissions for newly added tools (v4.2.2)."""

    def test_memory_extended_tools_are_safe(self):
        """Test that extended memory tools are safe for remote."""
        extended_memory_tools = [
            "memory_fetch",
            "memory_fuzzy_recall",
            "memory_get_tool_history",
            "memory_search_ids",
            "memory_stats",
            "memory_timeline",
            "memory_get_chunk_context",
            "memory_get_chunk_metadata",
            "memory_get_full_document",
        ]

        for tool in extended_memory_tools:
            assert TOOL_PERMISSIONS[tool]["remote"] is True, (
                f"{tool} should be safe (database only)"
            )

    def test_coding_memory_tools_are_safe(self):
        """Test that coding memory tools are safe for remote."""
        safe_coding_tools = [
            "coding_start_session",
            "coding_end_session",
            "coding_track_file_change",
            "coding_record_error",
            "coding_search_errors",
            "coding_get_project_context",
        ]

        for tool in safe_coding_tools:
            assert TOOL_PERMISSIONS[tool]["remote"] is True, (
                f"{tool} should be safe (database only)"
            )

    def test_coding_file_tools_are_dangerous(self):
        """Test that coding tools with file access are dangerous."""
        dangerous_coding_tools = [
            "coding_index_source_code",
            "coding_analyze_file_dependencies",
            "coding_analyze_refactor_impact",
        ]

        for tool in dangerous_coding_tools:
            assert TOOL_PERMISSIONS[tool]["remote"] is False, (
                f"{tool} should be dangerous (reads server files)"
            )

    def test_meta_fix_code_error_is_dangerous(self):
        """Test that meta_fix_code_error is dangerous (RCE risk)."""
        assert TOOL_PERMISSIONS["meta_fix_code_error"]["remote"] is False
        info = get_tool_permission_info("meta_fix_code_error")
        assert info["reason"] == "Code generation/execution risk"

    def test_meta_create_agent_is_dangerous(self):
        """Test that meta_create_agent is dangerous (code generation)."""
        assert TOOL_PERMISSIONS["meta_create_agent"]["remote"] is False
        info = get_tool_permission_info("meta_create_agent")
        assert info["reason"] == "Code generation risk"

    def test_claude_code_tools_are_safe(self):
        """Test that Claude Code memory tools are safe."""
        claude_code_tools = [
            "claude_code_save_session",
            "claude_code_search_past_work",
        ]

        for tool in claude_code_tools:
            assert TOOL_PERMISSIONS[tool]["remote"] is True, (
                f"{tool} should be safe (database only)"
            )

    def test_arxiv_search_is_safe(self):
        """Test that arxiv_search is safe (API only)."""
        assert TOOL_PERMISSIONS["arxiv_search"]["remote"] is True
