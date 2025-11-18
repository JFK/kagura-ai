"""Decision recording MCP tool.

Records design and architectural decisions with rationale.
"""

from __future__ import annotations

from kagura import tool
from kagura.utils.common.mcp_helpers import parse_json_list, to_float_clamped
from kagura.mcp.tools.coding.common import get_coding_memory


@tool
async def coding_record_decision(
    user_id: str,
    project_id: str,
    decision: str,
    rationale: str,
    alternatives: str = "[]",
    impact: str | None = None,
    tags: str = "[]",
    related_files: str = "[]",
    confidence: float = 0.8,
) -> str:
    """Record design and architectural decisions with rationale
    for project context tracking.

    Use this tool to document important technical decisions. This helps:
    1. Future you remember WHY certain choices were made
    2. Other developers understand the reasoning
    3. AI assistants provide context-aware suggestions

    When to use:
    - When choosing between technical approaches
    - When making architectural decisions
    - When selecting libraries/frameworks
    - When establishing coding patterns/standards

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        decision: Brief statement of the decision made (1-2 sentences)
        rationale: Detailed reasoning behind the decision
        alternatives: JSON array of other options considered
            (e.g., '["Option A", "Option B"]')
        impact: Expected impact on the project (optional)
        tags: JSON array of categorization tags (e.g., '["architecture", "security"]')
        related_files: JSON array of files affected by this decision
        confidence: Confidence level in this decision (0.0-1.0, default 0.8)

    Returns:
        Confirmation with decision ID

    Examples:
            rationale=(
                "Stateless auth enables horizontal scaling without "
                "session store. JWTs can be validated without database "
                "lookups, improving performance. Better for planned "
                "mobile app integration."
            ),
            user_id="dev_john",
            project_id="api-service",
            decision="Use JWT tokens for authentication instead of sessions",
            rationale=(
                "Stateless auth enables horizontal scaling without session store. "
                "JWTs can be validated without database lookups, "
                "improving performance. "
                "Better for planned mobile app integration."
            ),
            alternatives='["Session-based auth", "OAuth-only"]',
            impact=(
                "Eliminates need for session storage. "
                "Requires key rotation strategy."
            ),
            tags='["architecture", "authentication", "security"]',
            related_files='["src/auth.py", "src/middleware.py"]',
            confidence=0.9
        )

        # Recording a library choice
        await coding_record_decision(
            user_id="dev_john",
            project_id="api-service",
            decision="Use Pydantic for data validation",
            rationale="Type-safe validation with excellent FastAPI integration. "
                     "Clear error messages and automatic API docs generation.",
            alternatives='["Marshmallow", "Cerberus", "manual validation"]',
            impact="All API models will use Pydantic BaseModel",
            tags='["library", "validation"]',
            confidence=0.95
        )
    """
    memory = get_coding_memory(user_id, project_id)

    # Parse JSON arrays using common helpers
    alternatives_list = parse_json_list(alternatives, param_name="alternatives")
    tags_list = parse_json_list(tags, param_name="tags")
    related_files_list = parse_json_list(related_files, param_name="related_files")

    # Convert confidence to float using common helper
    confidence_float = to_float_clamped(
        confidence, min_val=0.0, max_val=1.0, default=0.8, param_name="confidence"
    )

    decision_id = await memory.record_decision(
        decision=decision,
        rationale=rationale,
        alternatives=alternatives_list,
        impact=impact,
        tags=tags_list,
        related_files=related_files_list,
        confidence=confidence_float,
    )

    return (
        f"✅ Decision recorded: {decision_id}\n"
        f"Decision: {decision}\n"
        f"Confidence: {confidence_float:.0%}\n"
        f"Project: {project_id}\n"
        f"Tags: {', '.join(tags_list) if tags_list else 'None'}"
    )
