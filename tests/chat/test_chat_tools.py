"""Tests for chat tools integration with tool_registry (RFC-036 Phase 1)."""


from kagura.core.tool_registry import tool_registry


def test_chat_tools_registered_in_tool_registry():
    """Test that chat tools are automatically registered via @tool decorator."""
    # Import tools module to trigger @tool decorators
    from kagura.chat import tools  # noqa: F401

    # Verify tools are registered
    expected_tools = [
        "file_read",
        "file_write",
        "file_search",
        "execute_python",
        "shell_exec",
        "brave_search",
        "url_fetch",
        "analyze_image_url",
        "youtube_transcript",
        "youtube_metadata",
    ]

    all_tools = tool_registry.get_all()

    for tool_name in expected_tools:
        assert (
            tool_name in all_tools
        ), f"Tool '{tool_name}' not registered in tool_registry"


def test_file_read_tool_exists():
    """Test that file_read tool is registered and callable."""
    from kagura.chat import tools  # noqa: F401

    tool_func = tool_registry.get("file_read")
    assert tool_func is not None, "file_read tool not found in registry"
    assert callable(tool_func), "file_read is not callable"


def test_shell_exec_tool_exists():
    """Test that shell_exec tool is registered."""
    from kagura.chat import tools  # noqa: F401

    tool_func = tool_registry.get("shell_exec")
    assert tool_func is not None, "shell_exec tool not found in registry"
    assert callable(tool_func), "shell_exec is not callable"


def test_youtube_tools_exist():
    """Test that YouTube tools are registered."""
    from kagura.chat import tools  # noqa: F401

    # YouTube transcript
    yt_transcript = tool_registry.get("youtube_transcript")
    assert yt_transcript is not None, "youtube_transcript not found"
    assert callable(yt_transcript), "youtube_transcript is not callable"

    # YouTube metadata
    yt_metadata = tool_registry.get("youtube_metadata")
    assert yt_metadata is not None, "youtube_metadata not found"
    assert callable(yt_metadata), "youtube_metadata is not callable"


def test_web_tools_exist():
    """Test that web tools are registered."""
    from kagura.chat import tools  # noqa: F401

    # Brave search
    brave = tool_registry.get("brave_search")
    assert brave is not None, "brave_search not found"
    assert callable(brave), "brave_search is not callable"

    # URL fetch
    url_fetch = tool_registry.get("url_fetch")
    assert url_fetch is not None, "url_fetch not found"
    assert callable(url_fetch), "url_fetch is not callable"

    # Image analysis
    analyze_img = tool_registry.get("analyze_image_url")
    assert analyze_img is not None, "analyze_image_url not found"
    assert callable(analyze_img), "analyze_image_url is not callable"


def test_tool_registry_can_list_all_chat_tools():
    """Test that we can get all registered chat tools dynamically."""
    from kagura.chat import tools  # noqa: F401

    all_tools = tool_registry.get_all()

    # Should have at least 10 chat tools registered
    chat_tool_names = [
        "file_read",
        "file_write",
        "file_search",
        "execute_python",
        "shell_exec",
        "brave_search",
        "url_fetch",
        "analyze_image_url",
        "youtube_transcript",
        "youtube_metadata",
    ]

    registered_chat_tools = [name for name in chat_tool_names if name in all_tools]

    assert len(registered_chat_tools) >= 10, (
        f"Expected at least 10 chat tools, found {len(registered_chat_tools)}: "
        f"{registered_chat_tools}"
    )
