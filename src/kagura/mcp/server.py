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
        """List all Kagura agents as MCP tools

        Returns all agents registered in agent_registry,
        converting them to MCP Tool format.

        Returns:
            List of MCP Tool objects
        """
        tools: list[Tool] = []

        # Get all registered agents
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
            tool = Tool(
                name=f"kagura_{agent_name}",
                description=description,
                inputSchema=input_schema,
            )

            tools.append(tool)

        return tools

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        """Execute a Kagura agent

        Args:
            name: Tool name (format: "kagura_<agent_name>")
            arguments: Tool input arguments

        Returns:
            List of TextContent with agent result

        Raises:
            ValueError: If agent name is invalid or agent not found
        """
        # Extract agent name from tool name
        if not name.startswith("kagura_"):
            raise ValueError(f"Invalid tool name: {name}")

        agent_name = name.replace("kagura_", "", 1)

        # Get agent from registry
        agent_func = agent_registry.get(agent_name)
        if agent_func is None:
            raise ValueError(f"Agent not found: {agent_name}")

        # Prepare arguments
        args = arguments or {}

        # Execute agent
        try:
            # Check if agent is async
            if inspect.iscoroutinefunction(agent_func):
                result = await agent_func(**args)
            else:
                result = agent_func(**args)

            # Convert result to string
            result_text = str(result)

        except Exception as e:
            # Return error as text content
            result_text = f"Error executing agent '{agent_name}': {str(e)}"

        # Return as TextContent
        return [TextContent(type="text", text=result_text)]

    return server


__all__ = ["create_mcp_server"]
