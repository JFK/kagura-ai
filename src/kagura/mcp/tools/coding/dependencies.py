"""Dependency analysis MCP tools.

Analyzes file dependencies and refactoring impact.
"""

from __future__ import annotations

from kagura import tool
from kagura.utils.common.mcp_helpers import parse_json_list
from kagura.mcp.tools.coding.common import get_coding_memory


@tool
async def coding_analyze_file_dependencies(
    user_id: str,
    project_id: str,
    file_path: str,
) -> str:
    """Analyze dependencies for a Python file using AST parsing.

    Automatically parses import statements and builds dependency graph.
    Useful for understanding file relationships and refactoring impact.

    Args:
        user_id: User identifier
        project_id: Project identifier
        file_path: Path to file to analyze

    Returns:
        Dependency analysis with imports, importers, depth, and circular dependencies

    Example:
        await coding_analyze_file_dependencies(
            user_id="dev_john",
            project_id="api-service",
            file_path="src/auth.py"
        )
    """
    memory = get_coding_memory(user_id, project_id)

    deps = await memory.analyze_file_dependencies(file_path)

    result = f"📊 Dependency Analysis: {file_path}\n\n"

    if deps["imports"]:
        result += f"**Imports ({len(deps['imports'])} files):**\n"
        for imp in deps["imports"]:
            result += f"- {imp}\n"
        result += "\n"
    else:
        result += "**Imports:** None (leaf file)\n\n"

    if deps["imported_by"]:
        result += f"**Imported By ({len(deps['imported_by'])} files):**\n"
        for importer in deps["imported_by"]:
            result += f"- {importer}\n"
        result += "\n"
    else:
        result += "**Imported By:** None (no dependents)\n\n"

    result += f"**Import Depth:** {deps['import_depth']}\n\n"

    if deps["circular_deps"]:
        result += "⚠️  **Circular Dependencies Detected:**\n"
        for cycle in deps["circular_deps"]:
            result += f"- {' → '.join(cycle)}\n"
    else:
        result += "✅ **No Circular Dependencies**\n"

    return result


@tool
async def coding_analyze_refactor_impact(
    user_id: str,
    project_id: str,
    file_path: str,
) -> str:
    """Analyze the impact of refactoring a file.

    Shows which files would be affected and assesses risk level.
    Helps make informed refactoring decisions.

    Args:
        user_id: User identifier
        project_id: Project identifier
        file_path: File to refactor

    Returns:
        Impact analysis with affected files, risk level, and recommendations

    Example:
        await coding_analyze_refactor_impact(
            user_id="dev_john",
            project_id="api-service",
            file_path="src/models/user.py"
        )
    """
    memory = get_coding_memory(user_id, project_id)

    impact = await memory.analyze_refactor_impact(file_path)

    risk_emoji = {
        "low": "✅",
        "medium": "⚠️ ",
        "high": "🚨",
        "unknown": "❓",
    }

    result = f"🔍 Refactoring Impact Analysis: {file_path}\n\n"
    result += (
        f"**Risk Level:** {risk_emoji[impact['risk_level']]} "
        f"{impact['risk_level'].upper()}\n\n"
    )

    if impact["affected_files"]:
        result += f"**Affected Files ({len(impact['affected_files'])}):**\n"
        for affected in impact["affected_files"][:10]:  # Limit display
            result += f"- {affected}\n"

        if len(impact["affected_files"]) > 10:
            result += f"- ... and {len(impact['affected_files']) - 10} more\n"

        result += "\n"

    result += "**Recommendations:**\n"
    for rec in impact["recommendations"]:
        result += f"{rec}\n"

    return result


@tool
async def coding_suggest_refactor_order(
    user_id: str,
    project_id: str,
    files: str,  # JSON array
) -> str:
    """Suggest safe order to refactor multiple files based on dependencies.

    Uses topological sorting to refactor leaf dependencies first.

    Args:
        user_id: User identifier
        project_id: Project identifier
        files: JSON array of file paths to refactor

    Returns:
        Suggested refactoring order with explanation

    Example:
        await coding_suggest_refactor_order(
            user_id="dev_john",
            project_id="api-service",
            files='["src/main.py", "src/auth.py", "src/models/user.py"]'
        )
    """
    memory = get_coding_memory(user_id, project_id)

    # Parse files from JSON using common helper
    files_list = parse_json_list(files, param_name="files")
    if not files_list:
        return "❌ Error: files parameter must be a non-empty JSON array"

    order = await memory.suggest_refactor_order(files_list)

    result = "📋 Suggested Refactoring Order:\n\n"

    for i, file in enumerate(order, 1):
        result += f"{i}. {file}\n"

    result += (
        "\n💡 Refactor in this order to minimize breaking changes.\n"
        "Leaf dependencies (files with no internal imports) come first."
    )

    return result
