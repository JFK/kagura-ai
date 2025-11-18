"""User pattern analysis for graph memory.

Analyzes user interaction patterns and interests.
"""

from __future__ import annotations

import json

from kagura import tool
from kagura.utils.common.mcp_helpers import format_error
from kagura.mcp.tools.memory.common import get_memory_manager


@tool
async def memory_get_user_pattern(
    agent_name: str,
    user_id: str,
) -> str:
    """Analyze user's interaction patterns and interests

    Analyzes a user's interaction history to discover patterns, interests,
    and preferences. Returns statistics about topics, platforms, and
    interaction frequency across all AI tools.

    🔍 USE WHEN:
    - Understanding user's interests and discussion patterns
    - Personalizing responses based on past interactions
    - Discovering which topics the user discusses most
    - Analyzing cross-platform usage (Claude vs ChatGPT, etc.)

    Args:
        agent_name: Agent identifier (use "global" for cross-thread sharing)
        user_id: User identifier to analyze

    Returns:
        JSON string with user pattern analysis including:
        - total_interactions: Number of recorded interactions
        - topics: List of topics user has discussed
        - avg_interactions_per_topic: Average interactions per topic
        - most_discussed_topic: Most frequently discussed topic
        - platforms: Platform usage statistics (e.g., {"claude": 30})

    💡 EXAMPLE:
        # Analyze user's patterns
        memory_get_user_pattern(agent_name="global", user_id="user_jfk")

    📊 RETURNS:
        {
          "user_id": "user_jfk",
          "pattern": {
            "total_interactions": 42,
            "topics": ["python", "fastapi", "asyncio"],
            "avg_interactions_per_topic": 14.0,
            "most_discussed_topic": "python",
            "platforms": {"claude": 30, "chatgpt": 12}
          }
        }

    💡 TIP: To get meaningful topic analysis, record interactions with
        "topic" in metadata:
        metadata='{"topic": "python"}'

    Note:
        Requires enable_graph=True in MemoryManager (enabled by default).
        User must have recorded interactions via memory_record_interaction.
    """
    enable_rag = True
    memory = get_memory_manager(user_id, agent_name, enable_rag=enable_rag)

    # Check if graph is available
    if not memory.graph:
        return format_error(
            "GraphMemory not available",
            details={"message": "Graph memory is disabled or NetworkX not installed"},
        )

    # Analyze user pattern
    try:
        pattern = memory.graph.analyze_user_pattern(user_id)

        return json.dumps(
            {
                "user_id": user_id,
                "pattern": pattern,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to analyze user pattern: {str(e)}"}, indent=2
        )
