"""MCP Tool classification for remote capability and security.

This module defines which tools can be safely executed via remote MCP server
and which require local filesystem/shell access.
"""

# Remote-capable tools (API経由で安全に実行可能)
REMOTE_CAPABLE_TOOLS = {
    # Memory (all remote-capable)
    "memory_store",
    "memory_recall",
    "memory_search",
    "memory_list",
    "memory_delete",
    "memory_feedback",
    "memory_get_related",
    "memory_record_interaction",
    "memory_get_user_pattern",
    "memory_stats",
    "memory_search_ids",
    "memory_fetch",
    # Memory - Enhanced Search (v4.0.6+)
    "memory_search_hybrid",
    "memory_timeline",
    "memory_fuzzy_recall",
    # GitHub (API依存)
    "github_exec",
    "github_issue_view",
    "github_pr_view",
    "github_issue_list",
    "github_pr_create",
    "github_pr_merge",
    # Web/Search (API依存)
    "brave_web_search",
    "brave_news_search",
    "brave_image_search",
    "brave_video_search",
    "arxiv_search",
    "web_scrape",
    "youtube_get_transcript",
    "youtube_get_metadata",
    "youtube_summarize",
    "youtube_fact_check",
    "fact_check_claim",
    # Coding (記録系のみ、ファイル操作を伴わない)
    "coding_track_file_change",
    "coding_record_error",
    "coding_record_decision",
    "coding_start_session",
    "coding_end_session",
    "coding_resume_session",  # メモリーのみ操作
    "coding_get_current_session_status",  # メモリーのみ操作
    "coding_search_errors",
    "coding_get_project_context",
    "coding_analyze_patterns",
    "coding_link_github_issue",
    "coding_generate_pr_description",
    "coding_get_issue_context",
    # Claude Code Integration (メモリーのみ操作)
    "claude_code_save_session",
    "claude_code_search_past_work",
    # Meta
    "meta_create_agent",
    "telemetry_stats",
    "telemetry_cost",
    "route_query",
}

# Local-only tools (ファイルシステム/シェルアクセス必須)
LOCAL_ONLY_TOOLS = {
    # File operations
    "file_read",
    "file_write",
    "dir_list",
    # Shell (セキュリティリスク大)
    "shell_exec",
    # GitHub CLI (ローカルgh CLIを使用)
    "gh_safe_exec",
    "gh_pr_create_safe",
    "gh_pr_merge_safe",
    # Media (ローカルファイル操作)
    "media_open_image",
    "media_open_video",
    "media_open_audio",
    # Coding (ローカルファイル解析)
    "coding_analyze_file_dependencies",
    "coding_analyze_refactor_impact",
    "coding_suggest_refactor_order",
    "coding_track_interaction",  # ローカルメタデータを記録
    "coding_index_source_code",  # ローカルソースコードを読み込み
    "coding_search_source_code",  # インデックスされたローカルコードを検索
    # YouTube (ローカルでトランスクリプト取得)
    "get_youtube_transcript",
    "get_youtube_metadata",
    # Multimodal (ローカルファイル読み込み)
    "multimodal_index",
    "multimodal_search",
}


def is_remote_capable(tool_name: str) -> bool:
    """Check if a tool can be executed remotely.

    Args:
        tool_name: Name of the MCP tool

    Returns:
        True if tool can be executed via remote API, False if local-only
    """
    return tool_name in REMOTE_CAPABLE_TOOLS


def is_local_only(tool_name: str) -> bool:
    """Check if a tool requires local execution.

    Args:
        tool_name: Name of the MCP tool

    Returns:
        True if tool requires local filesystem/shell access
    """
    return tool_name in LOCAL_ONLY_TOOLS


def get_tool_security_level(tool_name: str) -> str:
    """Get security level classification for a tool.

    Args:
        tool_name: Name of the MCP tool

    Returns:
        Security level: "safe", "caution", or "high_risk"
    """
    if tool_name == "shell_exec":
        return "high_risk"
    elif tool_name in LOCAL_ONLY_TOOLS:
        return "caution"
    else:
        return "safe"
