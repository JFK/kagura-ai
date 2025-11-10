"""MCP CLI commands - Model Context Protocol integration

Provides CLI commands for managing MCP server and integration with Claude Desktop, Cline, etc.
"""

import click

from kagura.cli.mcp import config, core, monitor, telemetry, tools


@click.group()
def mcp():
    """MCP (Model Context Protocol) commands

    Manage MCP server and integration with Claude Desktop, Cline, etc.

    \b
    Examples:
      kagura mcp serve           Start MCP server
      kagura mcp doctor          Run diagnostics
      kagura mcp install         Configure Claude Desktop
      kagura mcp tools           List MCP tools
    """
    pass


# Register all commands from modules
mcp.add_command(core.serve)
mcp.add_command(core.doctor)
mcp.add_command(config.install)
mcp.add_command(config.uninstall)
mcp.add_command(config.connect)
mcp.add_command(config.test_remote, name="test-remote")
mcp.add_command(tools.list_tools, name="tools")
mcp.add_command(tools.stats_command, name="stats")
mcp.add_command(monitor.monitor_command, name="monitor")
mcp.add_command(monitor.log_command, name="log")
mcp.add_command(telemetry.telemetry_group, name="telemetry")

__all__ = ["mcp"]
