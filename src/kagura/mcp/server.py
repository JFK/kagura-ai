"""
MCP Server implementation for Kagura AI

Exposes Kagura agents as MCP tools, enabling integration with
Claude Code, Cline, and other MCP clients.
"""

import inspect
from typing import Any

from mcp.server import Server  # type: ignore
from mcp.types import TextContent, Tool  # type: ignore

from kagura.core.registry import agent_registry
from kagura.core.tool_registry import tool_registry
from kagura.core.workflow_registry import workflow_registry

from .schema import generate_json_schema


def create_mcp_server(name: str = "kagura-ai") -> Server:
    """Create MCP server instance

    Args:
        name: Server name (default: "kagura-ai")

    Returns:
        Configured MCP Server instance

    Example:
        >>> server = create_mcp_server()
        >>> # Run server with stdio transport
        >>> # await server.run(read_stream, write_stream)
    """
    server = Server(name)

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List all Kagura agents, tools, and workflows as MCP tools

        Returns all registered items from agent_registry, tool_registry,
        and workflow_registry, converting them to MCP Tool format.

        Returns:
            List of MCP Tool objects
        """
        mcp_tools: list[Tool] = []

        # 1. Get all registered agents
        agents = agent_registry.get_all()
        for agent_name, agent_func in agents.items():
            # Generate JSON Schema from function signature
            try:
                input_schema = generate_json_schema(agent_func)
            except Exception:
                # Fallback to empty schema if generation fails
                input_schema = {"type": "object", "properties": {}}

            # Extract description from docstring
            description = agent_func.__doc__ or f"Kagura agent: {agent_name}"
            # Clean up description (first line only)
            description = description.strip().split("\n")[0]

            # Create MCP Tool
            mcp_tools.append(
                Tool(
                    name=f"kagura_{agent_name}",
                    description=description,
                    inputSchema=input_schema,
                )
            )

        # 2. Get all registered tools
        tools = tool_registry.get_all()
        for tool_name, tool_func in tools.items():
            # Generate JSON Schema
            try:
                input_schema = generate_json_schema(tool_func)
            except Exception:
                input_schema = {"type": "object", "properties": {}}

            description = tool_func.__doc__ or f"Kagura tool: {tool_name}"
            description = description.strip().split("\n")[0]

            mcp_tools.append(
                Tool(
                    name=f"kagura_tool_{tool_name}",
                    description=description,
                    inputSchema=input_schema,
                )
            )

        # 3. Get all registered workflows
        workflows = workflow_registry.get_all()
        for workflow_name, workflow_func in workflows.items():
            # Generate JSON Schema
            try:
                input_schema = generate_json_schema(workflow_func)
            except Exception:
                input_schema = {"type": "object", "properties": {}}

            description = workflow_func.__doc__ or f"Kagura workflow: {workflow_name}"
            description = description.strip().split("\n")[0]

            mcp_tools.append(
                Tool(
                    name=f"kagura_workflow_{workflow_name}",
                    description=description,
                    inputSchema=input_schema,
                )
            )

        return mcp_tools

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        """Execute a Kagura agent, tool, or workflow

        Args:
            name: Tool name (format: "kagura_<agent_name>",
                "kagura_tool_<tool_name>", or "kagura_workflow_<workflow_name>")
            arguments: Tool input arguments

        Returns:
            List of TextContent with execution result

        Raises:
            ValueError: If name is invalid or item not found
        """
        if not name.startswith("kagura_"):
            raise ValueError(f"Invalid tool name: {name}")

        args = arguments or {}

        # Route to appropriate registry
        try:
            if name.startswith("kagura_tool_"):
                # Execute @tool
                tool_name = name.replace("kagura_tool_", "", 1)
                tool_func = tool_registry.get(tool_name)
                if tool_func is None:
                    raise ValueError(f"Tool not found: {tool_name}")

                # Tools are synchronous
                result = tool_func(**args)
                result_text = str(result)

            elif name.startswith("kagura_workflow_"):
                # Execute @workflow
                workflow_name = name.replace("kagura_workflow_", "", 1)
                workflow_func = workflow_registry.get(workflow_name)
                if workflow_func is None:
                    raise ValueError(f"Workflow not found: {workflow_name}")

                # Workflows can be async or sync
                if inspect.iscoroutinefunction(workflow_func):
                    result = await workflow_func(**args)
                else:
                    result = workflow_func(**args)
                result_text = str(result)

            else:
                # Execute @agent
                agent_name = name.replace("kagura_", "", 1)
                agent_func = agent_registry.get(agent_name)
                if agent_func is None:
                    raise ValueError(f"Agent not found: {agent_name}")

                # Agents are async
                if inspect.iscoroutinefunction(agent_func):
                    result = await agent_func(**args)
                else:
                    result = agent_func(**args)
                result_text = str(result)

        except Exception as e:
            # Return error as text content
            result_text = f"Error executing '{name}': {str(e)}"

        # Return as TextContent
        return [TextContent(type="text", text=result_text)]

    return server


__all__ = ["create_mcp_server"]
