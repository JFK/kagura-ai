"""
MCP CLI commands for Kagura AI

Provides commands to start MCP server and manage MCP integration.
"""

import asyncio
import sys

import click
from mcp.server.stdio import stdio_server  # type: ignore

from kagura.mcp import create_mcp_server


@click.group()
def mcp():
    """MCP (Model Context Protocol) commands

    Manage MCP server and integration with Claude Code, Cline, etc.

    Examples:
      kagura mcp serve           Start MCP server
      kagura mcp list            List available agents
    """
    pass


@mcp.command()
@click.option("--name", default="kagura-ai", help="Server name (default: kagura-ai)")
@click.pass_context
def serve(ctx: click.Context, name: str):
    """Start MCP server

    Starts the MCP server using stdio transport.
    This command is typically called by MCP clients (Claude Code, Cline, etc.).

    Example:
      kagura mcp serve

    Configuration for Claude Code (~/.config/claude-code/mcp.json):
      {
        "mcpServers": {
          "kagura": {
            "command": "kagura",
            "args": ["mcp", "serve"]
          }
        }
      }
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Starting Kagura MCP server: {name}", err=True)

    # Auto-register built-in tools
    try:
        import kagura.mcp.builtin  # noqa: F401

        if verbose:
            click.echo("Loaded built-in MCP tools", err=True)
    except ImportError:
        if verbose:
            click.echo("Warning: Could not load built-in tools", err=True)

    # Create MCP server
    server = create_mcp_server(name)

    # Run server with stdio transport
    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

    # Run async server
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        if verbose:
            click.echo("\nMCP server stopped", err=True)
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error running MCP server: {e}", err=True)
        sys.exit(1)


@mcp.command()
@click.pass_context
def list(ctx: click.Context):
    """List available Kagura agents

    Shows all agents that will be exposed as MCP tools.

    Example:
      kagura mcp list
    """
    from kagura.core.registry import agent_registry

    agents = agent_registry.get_all()

    if not agents:
        click.echo("No agents registered.")
        click.echo("\nTo register agents, use @agent decorator:")
        click.echo("  from kagura import agent")
        click.echo("  ")
        click.echo("  @agent")
        click.echo("  async def my_agent(query: str) -> str:")
        click.echo("      '''Answer: {{ query }}'''")
        click.echo("      pass")
        return

    click.echo(f"Registered agents ({len(agents)}):\n")

    for agent_name, agent_func in agents.items():
        # Get description from docstring
        description = agent_func.__doc__ or "No description"
        # Clean description (first line only)
        description = description.strip().split("\n")[0]

        click.echo(f"  • {agent_name}")
        click.echo(f"    {description}")
        click.echo()


__all__ = ["mcp"]
