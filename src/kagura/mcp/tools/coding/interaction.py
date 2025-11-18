"""Interaction tracking MCP tool.

Tracks AI-User interactions during coding sessions.
"""

from __future__ import annotations

import logging

from kagura import tool
from kagura.utils.common.mcp_helpers import parse_json_dict
from kagura.mcp.tools.coding.common import get_coding_memory

logger = logging.getLogger(__name__)


@tool
async def coding_track_interaction(
    user_id: str,
    project_id: str,
    user_query: str,
    ai_response: str,
    interaction_type: str,
    metadata: str = "{}",
) -> str:
    """Track AI-User interaction with automatic importance classification.

    Records conversations during coding sessions for cross-session context.
    High importance interactions (≥8.0) are automatically recorded to GitHub.

    **When to use:**
    - After important Q&A exchanges
    - When making design decisions through conversation
    - When struggling with a problem and finding solution
    - When discovering important insights
    - During implementation discussions

    Args:
        user_id: User identifier (developer, e.g., "kiyota")
        project_id: Project identifier (e.g., "kagura-ai")
        user_query: User's question or input
        ai_response: AI assistant's response
        interaction_type: Type of interaction:
            - "question": General questions (low importance)
            - "decision": Design/architecture decisions (high importance)
            - "struggle": Problem-solving discussions (high importance)
            - "discovery": New insights or findings (high importance)
            - "implementation": Code implementation discussions (medium)
            - "error_fix": Error resolution discussions (high importance)
        metadata: JSON object with additional context (optional)

    Returns:
        Confirmation with interaction ID

    Examples:
        # Record an error resolution discussion
        await coding_track_interaction(
            user_id="kiyota",
            project_id="kagura-ai",
            user_query="Why does memory_search_hybrid fail with 'str' vs 'int'?",
            ai_response="MCP tools receive params as strings. Convert to float/int.",
            interaction_type="error_fix"
        )

        # Record a design decision
        await coding_track_interaction(
            user_id="kiyota",
            project_id="kagura-ai",
            user_query="Should we use --body or --body-file for GitHub comments?",
            ai_response="Use --body-file for safety and reliability...",
            interaction_type="decision",
            metadata='{"context": "GitHub integration"}'
        )
    """
    coding_mem = get_coding_memory(user_id, project_id)

    # Parse metadata using common helper
    metadata_dict = parse_json_dict(metadata, param_name="metadata")

    try:
        interaction_id = await coding_mem.track_interaction(
            user_query=user_query,
            ai_response=ai_response,
            interaction_type=interaction_type,
            metadata=metadata_dict,
        )

        return (
            f"✅ Interaction tracked: {interaction_id}\n"
            f"Type: {interaction_type}\n"
            f"Session: {coding_mem.current_session_id or 'No active session'}\n"
            f"\nNote: Importance will be classified in background. "
            f"High importance (≥8.0) interactions are automatically recorded to GitHub."
        )
    except ValueError as e:
        logger.error(f"Invalid interaction type: {e}")
        return f"❌ Error: {e}"
    except Exception as e:
        logger.error(f"Failed to track interaction: {e}", exc_info=True)
        return f"❌ Failed to track interaction: {e}"
