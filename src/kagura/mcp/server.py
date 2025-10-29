"""
MCP Server implementation for Kagura AI

Exposes Kagura agents as MCP tools, enabling integration with
Claude Code, Cline, and other MCP clients.
"""

import inspect
import logging
import time
from typing import Any, Literal

from mcp.server import Server  # type: ignore
from mcp.types import TextContent, Tool  # type: ignore

from kagura.core.registry import agent_registry
from kagura.core.tool_registry import tool_registry
from kagura.core.workflow_registry import workflow_registry

from .permissions import get_allowed_tools, get_denied_tools
from .schema import generate_json_schema

logger = logging.getLogger(__name__)


def create_mcp_server(
    name: str = "kagura-ai",
    context: Literal["local", "remote"] = "local",
) -> Server:
    """Create MCP server instance with tool access control.

    Args:
        name: Server name (default: "kagura-ai")
        context: Execution context ("local" or "remote")
                 - "local": All tools allowed (stdio transport)
                 - "remote": Only safe tools allowed (HTTP/SSE transport)

    Returns:
        Configured MCP Server instance with filtered tools

    Example:
        >>> # Local server (all tools)
        >>> server = create_mcp_server(context="local")
        >>>
        >>> # Remote server (safe tools only)
        >>> server = create_mcp_server(context="remote")

    Note:
        Remote context filters out dangerous tools like:
        - file_read, file_write (filesystem access)
        - shell_exec (command execution)
        - media_open_* (local app execution)
    """
    server = Server(name)

    # Log context
    logger.info(f"Creating MCP server '{name}' in {context} context")

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

        # 4. Filter tools by context (local vs remote)
        if context == "remote":
            # Get tool names (strip kagura_ prefix for permission check)
            all_tool_names = [tool.name for tool in mcp_tools]

            # Extract base names (remove kagura_tool_ prefix)
            base_names = []
            for name in all_tool_names:
                if name.startswith("kagura_tool_"):
                    base_names.append(name.replace("kagura_tool_", ""))
                elif name.startswith("kagura_workflow_"):
                    base_names.append(name.replace("kagura_workflow_", ""))
                elif name.startswith("kagura_"):
                    base_names.append(name.replace("kagura_", ""))
                else:
                    base_names.append(name)

            # Filter based on permissions
            allowed_base_names = get_allowed_tools(base_names, context="remote")
            denied_names = get_denied_tools(base_names, context="remote")

            # Rebuild tool name set for filtering
            allowed_names_set = set()
            for base_name in allowed_base_names:
                # Reconstruct full names
                allowed_names_set.add(f"kagura_tool_{base_name}")
                allowed_names_set.add(f"kagura_workflow_{base_name}")
                allowed_names_set.add(f"kagura_{base_name}")

            # Filter mcp_tools
            filtered_tools = [
                tool for tool in mcp_tools if tool.name in allowed_names_set
            ]

            # Log filtering
            if denied_names:
                more_msg = (
                    f" and {len(denied_names) - 5} more"
                    if len(denied_names) > 5
                    else ""
                )
                logger.warning(
                    f"Remote context: Filtered out {len(denied_names)} "
                    f"dangerous tools: {', '.join(denied_names[:5])}{more_msg}"
                )

            logger.info(
                f"Remote context: Exposing {len(filtered_tools)}/{len(mcp_tools)} tools"
            )

            return filtered_tools

        # Local context - return all tools
        logger.info(f"Local context: Exposing all {len(mcp_tools)} tools")
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
        logger.debug(f"handle_call_tool called: name={name}, args={arguments}")

        if not name.startswith("kagura_"):
            raise ValueError(f"Invalid tool name: {name}")

        args = arguments or {}
        logger.debug(f"Processed args: {args}")

        # Get telemetry collector
        from kagura.observability import get_global_telemetry

        telemetry = get_global_telemetry()
        collector = telemetry.get_collector()

        # Remove agent_name from args to avoid conflict
        # Memory tools have agent_name parameter, causing duplication
        tracking_args = {k: v for k, v in args.items() if k != "agent_name"}

        # Track execution with telemetry
        async with collector.track_execution(f"mcp_{name}", **tracking_args):
            # Determine tool type
            if name.startswith("kagura_tool_"):
                collector.add_tag("type", "tool")
                item_name = name.replace("kagura_tool_", "", 1)
            elif name.startswith("kagura_workflow_"):
                collector.add_tag("type", "workflow")
                item_name = name.replace("kagura_workflow_", "", 1)
            else:
                collector.add_tag("type", "agent")
                item_name = name.replace("kagura_", "", 1)

            collector.add_tag("item_name", item_name)
            collector.add_tag("mcp_name", name)

            # Route to appropriate registry and execute
            start_time = time.time()
            try:
                logger.debug(f"Executing tool: {item_name}")
                if name.startswith("kagura_tool_"):
                    # Execute @tool
                    tool_func = tool_registry.get(item_name)
                    if tool_func is None:
                        raise ValueError(f"Tool not found: {item_name}")

                    # Tools can be async or sync
                    logger.debug(f"Calling tool function: {item_name}")
                    if inspect.iscoroutinefunction(tool_func):
                        result = await tool_func(**args)
                    else:
                        result = tool_func(**args)
                    logger.debug(f"Tool {item_name} returned, converting to string")
                    result_text = str(result)
                    logger.debug(f"Result text length: {len(result_text)}")

                elif name.startswith("kagura_workflow_"):
                    # Execute @workflow
                    workflow_func = workflow_registry.get(item_name)
                    if workflow_func is None:
                        raise ValueError(f"Workflow not found: {item_name}")

                    # Workflows can be async or sync
                    if inspect.iscoroutinefunction(workflow_func):
                        result = await workflow_func(**args)
                    else:
                        result = workflow_func(**args)
                    result_text = str(result)

                else:
                    # Execute @agent
                    agent_func = agent_registry.get(item_name)
                    if agent_func is None:
                        raise ValueError(f"Agent not found: {item_name}")

                    # Agents are async
                    if inspect.iscoroutinefunction(agent_func):
                        result = await agent_func(**args)
                    else:
                        result = agent_func(**args)
                    result_text = str(result)

                # Record successful tool call
                duration = time.time() - start_time
                logger.debug(f"Tool {item_name} completed in {duration:.2f}s")
                collector.record_tool_call(item_name, duration, **tracking_args)

            except Exception as e:
                # Record failed tool call
                duration = time.time() - start_time
                logger.error(f"Tool {item_name} failed: {str(e)}")
                collector.record_tool_call(
                    item_name, duration, error=str(e), **tracking_args
                )

                # Return error as text content
                result_text = f"Error executing '{name}': {str(e)}"

            # Return as TextContent
            logger.debug(f"Creating TextContent response, length={len(result_text)}")
            response = [TextContent(type="text", text=result_text)]
            logger.debug("Returning response")
            return response

    return server


__all__ = ["create_mcp_server"]
