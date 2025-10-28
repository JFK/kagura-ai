"""Tests for MCP tool permission system."""


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
        assert "safe" in info["reason"].lower()

    def test_file_tool_info(self):
        """Test info for file tools."""
        info = get_tool_permission_info("file_read")
        assert info["remote"] is False
        assert "filesystem" in info["reason"].lower()

    def test_shell_tool_info(self):
        """Test info for shell execution."""
        info = get_tool_permission_info("shell_exec")
        assert info["remote"] is False
        assert "shell" in info["reason"].lower() or "command" in info["reason"].lower()

    def test_media_tool_info(self):
        """Test info for media tools."""
        info = get_tool_permission_info("media_open_audio")
        assert info["remote"] is False
        assert "application" in info["reason"].lower()

    def test_unknown_tool_info(self):
        """Test info for unknown tools."""
        info = get_tool_permission_info("unknown_tool")
        assert info["remote"] is False
        assert "unknown" in info["reason"].lower() or "deny" in info["reason"].lower()


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
            assert (
                TOOL_PERMISSIONS[tool]["remote"] is False
            ), f"{tool} should be dangerous"

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
            assert (
                is_tool_allowed(tool, "remote") is True
            ), f"{tool} should be allowed for ChatGPT"

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
            assert (
                is_tool_allowed(tool, "local") is True
            ), f"{tool} should be allowed locally"
