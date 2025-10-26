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

    Manage MCP server and integration with Claude Desktop, Cline, etc.

    Examples:
      kagura mcp serve           Start MCP server
      kagura mcp list            List available agents
      kagura mcp doctor          Run diagnostics
      kagura mcp install         Configure Claude Desktop
      kagura mcp tools           List MCP tools
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


@mcp.command()
@click.option("--api-url", default="http://localhost:8080", help="API server URL")
@click.pass_context
def doctor(ctx: click.Context, api_url: str):
    """Run MCP diagnostics

    Checks health of MCP server, API server, and related services.

    Example:
      kagura mcp doctor
    """
    from rich.console import Console
    from rich.table import Table

    from kagura.mcp.diagnostics import MCPDiagnostics

    console = Console()
    console.print("\n[bold]Kagura MCP Diagnostics[/bold]\n")

    # Run diagnostics
    diag = MCPDiagnostics(api_base_url=api_url)

    with console.status("[bold green]Running diagnostics..."):
        results = asyncio.run(diag.run_full_diagnostics())

    # Display results
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="dim")
    table.add_column("Status")
    table.add_column("Details")

    # Helper to get details string
    def _get_details_str(status_dict: dict[str, Any]) -> str:
        details = status_dict.get("details", "")
        if isinstance(details, dict):
            # If details is a dict, convert to string
            return str(details)[:50]
        return str(details)[:50]

    # API Server
    api_status = results.get("api_server", {})
    status_icon = _get_status_icon(api_status.get("status"))
    table.add_row(
        "API Server",
        f"{status_icon} {api_status.get('status', 'unknown')}",
        _get_details_str(api_status),
    )

    # Memory Manager
    mem_status = results.get("memory_manager", {})
    status_icon = _get_status_icon(mem_status.get("status"))
    details = (
        f"Persistent: {mem_status.get('persistent_count', 0)}, "
        f"RAG: {mem_status.get('rag_count', 0)}"
        if mem_status.get("status") == "healthy"
        else _get_details_str(mem_status)
    )
    table.add_row("Memory Manager", f"{status_icon} {mem_status.get('status', 'unknown')}", details[:50])

    # Claude Desktop
    claude_status = results.get("claude_desktop", {})
    status_icon = _get_status_icon(claude_status.get("status"))
    table.add_row(
        "Claude Desktop",
        f"{status_icon} {claude_status.get('status', 'unknown')}",
        _get_details_str(claude_status),
    )

    # Storage
    storage_status = results.get("storage", {})
    status_icon = _get_status_icon(storage_status.get("status"))
    details = (
        f"{storage_status.get('size_mb', 0):.1f} MB"
        if "size_mb" in storage_status
        else _get_details_str(storage_status)
    )
    table.add_row(
        "Storage", f"{status_icon} {storage_status.get('status', 'unknown')}", details[:50]
    )

    console.print(table)

    # Overall status
    overall = results.get("overall", "unknown")
    console.print(f"\n[bold]Overall Status:[/bold] {_get_status_icon(overall)} {overall}\n")

    # Recommendations
    if overall != "healthy":
        console.print("[bold yellow]Recommendations:[/bold yellow]")
        if api_status.get("status") == "unreachable":
            console.print("  • Start API server: [cyan]uvicorn kagura.api.server:app[/cyan]")
        if claude_status.get("status") == "not_configured":
            console.print("  • Configure Claude Desktop: [cyan]kagura mcp install[/cyan]")
        if mem_status.get("status") == "error":
            console.print("  • Initialize RAG: [cyan]kagura init --rag[/cyan]")
        if storage_status.get("status") in ("warning", "critical"):
            console.print(
                "  • Clean up storage: [cyan]kagura memory prune --older-than 90[/cyan]"
            )
        console.print()


def _get_status_icon(status: str) -> str:
    """Get emoji icon for status.

    Args:
        status: Status string

    Returns:
        Emoji icon
    """
    icons = {
        "healthy": "✅",
        "configured": "✅",
        "degraded": "⚠️",
        "warning": "⚠️",
        "unhealthy": "❌",
        "error": "❌",
        "unreachable": "❌",
        "critical": "🔴",
        "not_configured": "⚠️",
        "not_initialized": "⚠️",
    }
    return icons.get(status, "❓")


@mcp.command()
@click.option("--server-name", default="kagura-memory", help="MCP server name")
@click.pass_context
def install(ctx: click.Context, server_name: str):
    """Install Kagura to Claude Desktop

    Automatically configures Claude Desktop to use Kagura MCP server.

    Example:
      kagura mcp install
    """
    from rich.console import Console

    from kagura.mcp.config import MCPConfig

    console = Console()
    config = MCPConfig()

    # Check if already configured
    if config.is_configured_in_claude_desktop(server_name):
        console.print(
            f"[yellow]Kagura is already configured in Claude Desktop as '{server_name}'[/yellow]"
        )
        if not click.confirm("Overwrite existing configuration?"):
            console.print("[dim]Installation cancelled.[/dim]")
            return

    # Add to Claude Desktop config
    console.print(f"\n[bold]Installing Kagura MCP to Claude Desktop...[/bold]")

    # Determine kagura command path
    import shutil

    kagura_command = shutil.which("kagura") or "kagura"

    success = config.add_to_claude_desktop(server_name, kagura_command)

    if success:
        console.print(f"[green]✅ Successfully installed![/green]\n")
        console.print(f"[bold]Configuration:[/bold]")
        console.print(f"  Server name: {server_name}")
        console.print(f"  Command: {kagura_command} mcp serve")
        console.print(f"  Config file: {config.claude_config_path}")
        console.print(
            f"\n[bold yellow]Next steps:[/bold yellow]"
        )
        console.print("  1. Restart Claude Desktop")
        console.print("  2. Start a new conversation")
        console.print("  3. Try: 'Remember that I prefer Python'")
        console.print()
    else:
        console.print(f"[red]❌ Installation failed[/red]")
        console.print(f"Check permissions for: {config.claude_config_path}")


@mcp.command()
@click.option("--server-name", default="kagura-memory", help="MCP server name")
@click.pass_context
def uninstall(ctx: click.Context, server_name: str):
    """Remove Kagura from Claude Desktop

    Removes Kagura MCP server configuration from Claude Desktop.

    Example:
      kagura mcp uninstall
    """
    from rich.console import Console

    from kagura.mcp.config import MCPConfig

    console = Console()
    config = MCPConfig()

    if not config.is_configured_in_claude_desktop(server_name):
        console.print(
            f"[yellow]Kagura '{server_name}' is not configured in Claude Desktop[/yellow]"
        )
        return

    if not click.confirm(f"Remove '{server_name}' from Claude Desktop configuration?"):
        console.print("[dim]Uninstallation cancelled.[/dim]")
        return

    success = config.remove_from_claude_desktop(server_name)

    if success:
        console.print(f"[green]✅ Successfully removed '{server_name}'[/green]")
        console.print(f"Config file: {config.claude_config_path}")
        console.print("\n[yellow]Restart Claude Desktop to apply changes.[/yellow]\n")
    else:
        console.print(f"[red]❌ Uninstallation failed[/red]")


@mcp.command(name="tools")
@click.pass_context
def list_tools(ctx: click.Context):
    """List available MCP tools

    Shows all MCP tools that Kagura provides.

    Example:
      kagura mcp tools
    """
    from rich.console import Console
    from rich.table import Table

    from kagura.core.registry import tool_registry

    console = Console()

    # Auto-load built-in tools
    try:
        import kagura.mcp.builtin  # noqa: F401
    except ImportError:
        console.print("[yellow]Warning: Could not load built-in tools[/yellow]\n")

    all_tools = tool_registry.get_all()

    if not all_tools:
        console.print("[yellow]No MCP tools registered.[/yellow]")
        console.print("\n[dim]Tools are auto-registered when you import modules.[/dim]")
        console.print("[dim]Example: from kagura.mcp.builtin import memory[/dim]\n")
        return

    console.print(f"\n[bold]Kagura MCP Tools ({len(all_tools)})[/bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Description")

    # Categorize tools
    categories = {
        "memory": [
            "memory_store",
            "memory_recall",
            "memory_search",
            "memory_list",
            "memory_feedback",
            "memory_delete",
        ],
        "web": ["web_search", "brave_search"],
        "youtube": ["youtube_transcript", "youtube_metadata"],
        "file": ["file_read", "file_write", "file_list"],
        "multimodal": ["gemini_vision", "gemini_audio"],
    }

    for tool_name, tool_func in sorted(all_tools.items()):
        # Determine category
        category = "other"
        for cat, tool_names in categories.items():
            if tool_name in tool_names:
                category = cat
                break

        # Get description from docstring
        description = tool_func.__doc__ or "No description"
        description = description.strip().split("\n")[0]
        if len(description) > 60:
            description = description[:57] + "..."

        table.add_row(tool_name, category, description)

    console.print(table)
    console.print()


__all__ = ["mcp"]
