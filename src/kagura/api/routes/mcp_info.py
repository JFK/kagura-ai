"""MCP Tools Information API.

Provides endpoints for Web UI to discover and display available MCP tools.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tools")
async def list_mcp_tools() -> dict[str, Any]:
    """List all available MCP tools with metadata.

    Returns:
        Dictionary with tool information including:
        - name: Tool name
        - category: Tool category (coding, memory, web, etc.)
        - remote_capable: Whether tool works remotely
        - description: Tool description
    """
    from kagura.core.tool_registry import tool_registry
    from kagura.mcp.permissions import TOOL_PERMISSIONS

    # Import all tools to ensure registration
    try:
        import kagura.mcp.tools  # noqa: F401
    except ImportError:
        pass

    # Get all registered tools
    all_tools = tool_registry.get_all()

    tools_info = []
    for tool_name, tool_func in all_tools.items():
        # Infer category from tool name prefix
        category = tool_name.split("_")[0] if "_" in tool_name else "other"

        # Check if remote-capable
        permissions = TOOL_PERMISSIONS.get(tool_name, {})
        remote_capable = permissions.get("remote", False)

        # Get description from docstring
        description = ""
        if tool_func.__doc__:
            # First line of docstring
            description = tool_func.__doc__.strip().split("\n")[0]

        tools_info.append({
            "name": tool_name,
            "category": category,
            "remote_capable": remote_capable,
            "description": description,
        })

    # Sort by category, then name
    tools_info.sort(key=lambda t: (t["category"], t["name"]))

    return {
        "tools": tools_info,
        "total": len(tools_info),
        "categories": list(set(t["category"] for t in tools_info)),
    }


@router.get("/tools/{tool_name}")
async def get_mcp_tool_details(tool_name: str) -> dict[str, Any]:
    """Get detailed information about a specific MCP tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool metadata including full docstring, parameters, examples
    """
    from kagura.core.tool_registry import tool_registry
    from kagura.mcp.permissions import TOOL_PERMISSIONS

    # Import all tools
    try:
        import kagura.mcp.tools  # noqa: F401
    except ImportError:
        pass

    all_tools = tool_registry.get_all()

    if tool_name not in all_tools:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    tool_func = all_tools[tool_name]

    # Extract metadata
    category = tool_name.split("_")[0] if "_" in tool_name else "other"
    permissions = TOOL_PERMISSIONS.get(tool_name, {})
    remote_capable = permissions.get("remote", False)

    # Parse docstring for details
    full_doc = tool_func.__doc__ or ""
    lines = full_doc.strip().split("\n")

    short_desc = lines[0] if lines else ""

    # Extract Args section
    args_section = ""
    examples_section = ""

    in_args = False
    in_examples = False

    for line in lines:
        if "Args:" in line:
            in_args = True
            in_examples = False
            continue
        elif "Returns:" in line or "Raises:" in line:
            in_args = False
            in_examples = False
            continue
        elif "Example" in line:
            in_args = False
            in_examples = True
            continue

        if in_args:
            args_section += line + "\n"
        elif in_examples:
            examples_section += line + "\n"

    return {
        "name": tool_name,
        "category": category,
        "remote_capable": remote_capable,
        "description": short_desc,
        "full_description": full_doc,
        "parameters": args_section.strip(),
        "examples": examples_section.strip(),
        "permissions": permissions,
    }


@router.get("/categories")
async def list_mcp_categories() -> dict[str, Any]:
    """List all MCP tool categories with tool counts.

    Returns:
        Dictionary with category information
    """
    from kagura.core.tool_registry import tool_registry

    # Import all tools
    try:
        import kagura.mcp.tools  # noqa: F401
    except ImportError:
        pass

    all_tools = tool_registry.get_all()

    # Group by category
    categories = {}
    for tool_name in all_tools:
        category = tool_name.split("_")[0] if "_" in tool_name else "other"
        if category not in categories:
            categories[category] = {"count": 0, "tools": []}
        categories[category]["count"] += 1
        categories[category]["tools"].append(tool_name)

    return {
        "categories": categories,
        "total_categories": len(categories),
        "total_tools": len(all_tools),
    }
