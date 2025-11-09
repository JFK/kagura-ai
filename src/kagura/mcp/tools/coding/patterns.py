"""Pattern analysis MCP tool.

Analyzes coding patterns and preferences from session history.
"""

from __future__ import annotations

from kagura import tool
from kagura.mcp.tools.coding.common import get_coding_memory


@tool
async def coding_analyze_patterns(
    user_id: str,
    project_id: str,
) -> str:
    """Analyze coding patterns and preferences from session history using AI.

    Use this tool to get insights into your coding style and patterns. The AI analyzes:
    - Language preferences (type hints, docstrings, async usage)
    - Library preferences (frameworks, testing tools, etc.)
    - Naming conventions (functions, classes, variables)
    - Code organization (file length, function length, patterns)
    - Testing practices (coverage, style, mock usage)
    - Common error patterns and anti-patterns

    This helps:
    - AI assistants generate code matching your style
    - Identify areas for improvement
    - Maintain consistency across the project
    - Learn from your coding patterns

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier

    Returns:
        Detailed analysis of coding patterns and preferences

    Note:
        Requires sufficient coding history (10+ file changes recommended)
        for reliable pattern extraction.

    Example:
        await coding_analyze_patterns(
            user_id="dev_john",
            project_id="api-service"
        )
    """
    memory = get_coding_memory(user_id, project_id)

    patterns = await memory.analyze_coding_patterns()

    if patterns.get("confidence") == "low":
        return (
            f"⚠️ Insufficient data for reliable pattern analysis\n"
            f"Project: {project_id}\n\n"
            f"Continue coding and recording changes to build pattern history.\n"
            "Recommended: 10+ file changes for basic analysis, "
            "30+ for detailed insights."
        )

    result = f"🔍 Coding Pattern Analysis: {project_id}\n\n"

    # Language preferences
    if patterns.get("language_preferences"):
        result += "**Language Preferences:**\n"
        for key, value in patterns["language_preferences"].items():
            if isinstance(value, dict) and "confidence" in value:
                result += (
                    f"- {key}: {value.get('style', 'N/A')} "
                    f"(confidence: {value['confidence']})\n"
                )
        result += "\n"

    # Library preferences
    if patterns.get("library_preferences"):
        result += "**Library Preferences:**\n"
        for lib, details in patterns["library_preferences"].items():
            if isinstance(details, dict):
                result += (
                    f"- {lib}: confidence {details.get('confidence', 'unknown')}\n"
                )
        result += "\n"

    # Naming conventions
    if patterns.get("naming_conventions"):
        result += "**Naming Conventions:**\n"
        for element, style in patterns["naming_conventions"].items():
            if isinstance(style, dict):
                result += f"- {element}: {style.get('style', 'N/A')}\n"
        result += "\n"

    # Code organization
    if patterns.get("code_organization"):
        result += "**Code Organization:**\n"
        for aspect, pref in patterns["code_organization"].items():
            if isinstance(pref, dict):
                result += f"- {aspect}: {pref.get('preference', 'N/A')}\n"
        result += "\n"

    # Testing practices
    if patterns.get("testing_practices"):
        result += "**Testing Practices:**\n"
        for practice, level in patterns["testing_practices"].items():
            if isinstance(level, dict):
                result += f"- {practice}: {level.get('level', 'N/A')}\n"
        result += "\n"

    result += (
        "\n💡 This analysis helps AI assistants generate code that matches your style!"
    )

    return result
