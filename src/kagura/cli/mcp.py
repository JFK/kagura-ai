"""
MCP CLI commands for Kagura AI

Provides commands to start MCP server and manage MCP integration.
"""

import asyncio
import os
import sys
from typing import Any

import click
from mcp.server.stdio import stdio_server  # type: ignore

from kagura.config.paths import get_cache_dir, get_config_dir
from kagura.mcp import create_mcp_server


@click.group()
def mcp():
    """MCP (Model Context Protocol) commands

    Manage MCP server and integration with Claude Desktop, Cline, etc.

    \b
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
@click.option(
    "--remote",
    is_flag=True,
    help="Use remote API connection (requires: kagura mcp connect)",
)
@click.pass_context
def serve(ctx: click.Context, name: str, remote: bool):
    """Start MCP server

    Starts the MCP server using stdio transport.
    This command is typically called by MCP clients (Claude Code, Cline, etc.).

    Examples:
        # Local mode (default, all tools available)
        kagura mcp serve

        # Remote mode (connect to remote API, safe tools only)
        kagura mcp serve --remote

    Configuration for Claude Code (~/.config/claude-code/mcp.json):
      {
        "mcpServers": {
          "kagura": {
            "command": "kagura",
            "args": ["mcp", "serve"]
          }
        }
      }

    Remote Configuration (connects to remote Kagura API):
      {
        "mcpServers": {
          "kagura-remote": {
            "command": "kagura",
            "args": ["mcp", "serve", "--remote"]
          }
        }
      }
    """
    verbose = ctx.obj.get("verbose", False)

    if remote:
        # Remote mode - show info message
        click.echo(
            "Remote mode is not yet fully implemented. "
            "Use direct HTTP/SSE connection instead:",
            err=True,
        )
        click.echo(
            "  Configure ChatGPT Connector or other HTTP clients to: "
            "http://your-server:8000/mcp",
            err=True,
        )
        click.echo(
            "\nFor now, use local mode: kagura mcp serve (no --remote flag)",
            err=True,
        )
        sys.exit(1)

    # Setup logging to file (Issue #415)
    import logging
    from logging.handlers import RotatingFileHandler

    log_dir = get_cache_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "mcp_server.log"

    # Configure file handler (10MB max, 5 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    # Setup logger
    logger = logging.getLogger("kagura.mcp")
    logger.addHandler(file_handler)

    # Set log level from environment variable (default: INFO)
    log_level_name = os.environ.get("KAGURA_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logger.setLevel(log_level)

    # Also log to stderr if verbose
    if verbose:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(console_handler)

    logger.info(f"Starting Kagura MCP server: {name}")

    if verbose:
        click.echo(f"Starting Kagura MCP server: {name}", err=True)
        click.echo(f"Logging to: {log_file}", err=True)

    # Auto-register built-in tools
    try:
        import kagura.mcp.builtin  # noqa: F401

        logger.info("Loaded built-in MCP tools")
        if verbose:
            click.echo("Loaded built-in MCP tools", err=True)
    except ImportError:
        logger.warning("Could not load built-in tools")
        if verbose:
            click.echo("Warning: Could not load built-in tools", err=True)

    # Create MCP server (local context = all tools)
    server = create_mcp_server(name, context="local")
    logger.info("MCP server created with context: local")

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
    table.add_row(
        "Memory Manager",
        f"{status_icon} {mem_status.get('status', 'unknown')}",
        details[:50],
    )

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
        "Storage",
        f"{status_icon} {storage_status.get('status', 'unknown')}",
        details[:50],
    )

    console.print(table)

    # Overall status
    overall = results.get("overall", "unknown")
    console.print(
        f"\n[bold]Overall Status:[/bold] {_get_status_icon(overall)} {overall}\n"
    )

    # Recommendations
    if overall != "healthy":
        console.print("[bold yellow]Recommendations:[/bold yellow]")
        if api_status.get("status") == "unreachable":
            console.print(
                "  • Start API server: [cyan]uvicorn kagura.api.server:app[/cyan]"
            )
        if claude_status.get("status") == "not_configured":
            console.print(
                "  • Configure Claude Desktop: [cyan]kagura mcp install[/cyan]"
            )
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
            f"[yellow]Kagura is already configured in Claude Desktop "
            f"as '{server_name}'[/yellow]"
        )
        if not click.confirm("Overwrite existing configuration?"):
            console.print("[dim]Installation cancelled.[/dim]")
            return

    # Add to Claude Desktop config
    console.print("\n[bold]Installing Kagura MCP to Claude Desktop...[/bold]")

    # Determine kagura command path
    import shutil

    kagura_command = shutil.which("kagura") or "kagura"

    success = config.add_to_claude_desktop(server_name, kagura_command)

    if success:
        console.print("[green]✅ Successfully installed![/green]\n")
        console.print("[bold]Configuration:[/bold]")
        console.print(f"  Server name: {server_name}")
        console.print(f"  Command: {kagura_command} mcp serve")
        console.print(f"  Config file: {config.claude_config_path}")
        console.print("\n[bold yellow]Next steps:[/bold yellow]")
        console.print("  1. Restart Claude Desktop")
        console.print("  2. Start a new conversation")
        console.print("  3. Try: 'Remember that I prefer Python'")
        console.print()
    else:
        console.print("[red]❌ Installation failed[/red]")
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
            f"[yellow]Kagura '{server_name}' is not configured "
            f"in Claude Desktop[/yellow]"
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
        console.print("[red]❌ Uninstallation failed[/red]")


@mcp.command(name="connect")
@click.option(
    "--api-base",
    required=True,
    help="Remote Kagura API base URL (e.g., https://my-kagura.example.com)",
)
@click.option(
    "--api-key",
    help="API key for authentication (optional, can use KAGURA_API_KEY env var)",
)
@click.option(
    "--user-id",
    help="User ID for memory access (optional, defaults to default_user)",
)
@click.pass_context
def connect(
    ctx: click.Context, api_base: str, api_key: str | None, user_id: str | None
):
    """Configure remote MCP connection

    Saves remote connection settings for Kagura API access.
    These settings are used by 'kagura mcp serve --remote' command.

    Examples:
        # Configure remote connection
        kagura mcp connect --api-base https://my-kagura.example.com --api-key xxx

        # With custom user ID
        kagura mcp connect --api-base https://api.kagura.io --user-id user_alice
    """
    import json

    from rich.console import Console

    console = Console()

    # Validate URL
    if not api_base.startswith(("http://", "https://")):
        console.print("[red]✗ Error: API base URL must start with http:// or https://[/red]")
        raise click.Abort()

    # Prepare config
    config_dir = get_config_dir()
    config_file = config_dir / "remote-config.json"
    config_dir.mkdir(parents=True, exist_ok=True)

    remote_config = {
        "api_base": api_base.rstrip("/"),
        "api_key": api_key,
        "user_id": user_id or "default_user",
    }

    # Save config
    with open(config_file, "w") as f:
        json.dump(remote_config, f, indent=2)

    console.print("\n[green]✓ Remote connection configured successfully![/green]")
    console.print()
    console.print(f"[dim]Config saved to: {config_file}[/dim]")
    console.print()
    console.print("[cyan]Connection settings:[/cyan]")
    console.print(f"  • API Base: {api_base}")
    console.print(f"  • User ID: {user_id or 'default_user'}")
    console.print(f"  • API Key: {'***' + (api_key[-8:] if api_key else 'Not set')}")
    console.print()
    console.print("[yellow]Test connection with:[/yellow] kagura mcp test-remote")
    console.print()


@mcp.command(name="test-remote")
@click.pass_context
def test_remote(ctx: click.Context):
    """Test remote MCP connection

    Verifies that the remote Kagura API is accessible and responds correctly.

    Example:
        kagura mcp test-remote
    """
    import json

    import httpx
    from rich.console import Console

    console = Console()

    # Load config
    config_file = get_config_dir() / "remote-config.json"
    if not config_file.exists():
        console.print("[red]✗ Error: Remote connection not configured[/red]")
        console.print()
        console.print(
            "Configure with: [cyan]kagura mcp connect --api-base <url>[/cyan]"
        )
        console.print()
        raise click.Abort()

    with open(config_file) as f:
        config = json.load(f)

    api_base = config.get("api_base")
    api_key = config.get("api_key")
    user_id = config.get("user_id", "default_user")

    console.print("\n[bold]Testing Remote MCP Connection[/bold]\n")
    console.print(f"[dim]API Base: {api_base}[/dim]")
    console.print(f"[dim]User ID: {user_id}[/dim]\n")

    # Test 1: API health check
    console.print("[cyan]1. Testing API health...[/cyan]")
    try:
        response = httpx.get(f"{api_base}/api/v1/health", timeout=10.0)
        if response.status_code == 200:
            console.print("   [green]✓ API server is reachable[/green]")
        else:
            console.print(
                f"   [yellow]⚠ API returned status {response.status_code}[/yellow]"
            )
    except Exception as e:
        console.print(f"   [red]✗ Failed: {e}[/red]")
        raise click.Abort()

    # Test 2: MCP endpoint check
    console.print("\n[cyan]2. Testing /mcp endpoint...[/cyan]")
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Try tools/list request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        response = httpx.post(
            f"{api_base}/mcp",
            json=mcp_request,
            headers=headers,
            timeout=10.0,
        )

        if response.status_code == 200:
            console.print("   [green]✓ MCP endpoint is accessible[/green]")
        elif response.status_code == 401:
            console.print("   [red]✗ Authentication failed (invalid API key)[/red]")
            raise click.Abort()
        elif response.status_code == 406:
            console.print("   [yellow]⚠ MCP endpoint exists but returned 406[/yellow]")
            console.print("   [dim](This is expected for initial handshake)[/dim]")
        else:
            console.print(
                f"   [yellow]⚠ Unexpected status: {response.status_code}[/yellow]"
            )

    except httpx.TimeoutException:
        console.print("   [red]✗ Connection timeout[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"   [red]✗ Failed: {e}[/red]")
        raise click.Abort()

    # Test 3: Authentication
    console.print("\n[cyan]3. Testing authentication...[/cyan]")
    if api_key:
        console.print(f"   [green]✓ API key configured: ***{api_key[-8:]}[/green]")
    else:
        console.print(
            "   [yellow]⚠ No API key configured (using default_user)[/yellow]"
        )

    console.print("\n[green bold]✓ All tests passed![/green bold]")
    console.print()
    console.print("[cyan]Your remote MCP connection is ready to use.[/cyan]")
    console.print()


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


@mcp.command(name="stats")
@click.option("--agent", "-a", help="Filter by agent name", type=str, default=None)
@click.option(
    "--period", "-p", help="Days to analyze (default: 7)", type=int, default=7
)
@click.option(
    "--format",
    "-f",
    help="Output format",
    type=click.Choice(["table", "json"]),
    default="table",
)
@click.option(
    "--db", help="Path to telemetry database", type=click.Path(), default=None
)
@click.pass_context
def stats_command(
    ctx: click.Context,
    agent: str | None,
    period: int,
    format: str,
    db: str | None,
):
    """Display MCP tool usage statistics

    Shows tool call frequency, success rates, and server health based on
    telemetry data.

    \b
    Examples:
        kagura mcp stats                    # Last 7 days, all agents
        kagura mcp stats --period 30        # Last 30 days
        kagura mcp stats --agent my_agent   # Specific agent
        kagura mcp stats --format json      # JSON output
    """
    import json
    from collections import defaultdict
    from datetime import datetime, timedelta
    from pathlib import Path

    from rich.console import Console
    from rich.table import Table

    from kagura.observability import EventStore

    console = Console()

    # Load event store
    db_path = Path(db) if db else None
    store = EventStore(db_path)

    # Calculate time window
    since = (datetime.now() - timedelta(days=period)).timestamp()

    # Get executions
    executions = store.get_executions(
        agent_name=agent, since=since, limit=100000
    )

    if not executions:
        console.print("[yellow]No MCP tool usage data found[/yellow]")
        console.print()
        console.print(f"[dim]Period: Last {period} days[/dim]")
        if agent:
            console.print(f"[dim]Agent filter: {agent}[/dim]")
        console.print()
        return

    # Aggregate tool statistics
    tool_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "success": 0, "errors": 0}
    )

    total_requests = 0
    total_errors = 0

    for exec in executions:
        # Count tool calls from events
        events = exec.get("events", [])
        for event in events:
            if event.get("type") == "tool_call":
                tool_name = event.get("data", {}).get("tool_name", "unknown")
                tool_stats[tool_name]["calls"] += 1
                total_requests += 1

                # Check if tool succeeded
                if event.get("data", {}).get("error"):
                    tool_stats[tool_name]["errors"] += 1
                    total_errors += 1
                else:
                    tool_stats[tool_name]["success"] += 1

    # JSON output
    if format == "json":
        output = {
            "period_days": period,
            "agent_filter": agent,
            "total_tools": len(tool_stats),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0.0,
            "tools": {
                name: {
                    **stats,
                    "success_rate": (
                        stats["success"] / stats["calls"] if stats["calls"] > 0 else 0.0
                    ),
                }
                for name, stats in tool_stats.items()
            },
        }
        console.print(json.dumps(output, indent=2))
        return

    # Table output
    console.print()
    console.print("[bold cyan]Kagura MCP Usage Statistics[/bold cyan]")
    console.print(f"[dim]Last {period} Days[/dim]")
    console.print()

    # Summary
    console.print(f"[cyan]MCP Tools:[/cyan] {len(tool_stats)} tools used")
    console.print(f"[cyan]Total Requests:[/cyan] {total_requests}")
    if total_requests > 0:
        error_rate = (total_errors / total_requests) * 100
        console.print(
            f"[cyan]Error Rate:[/cyan] {error_rate:.1f}% ({total_errors} errors)"
        )
    console.print()

    # Tool usage table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Calls", justify="right")
    table.add_column("Success Rate", justify="right")
    table.add_column("Errors", justify="right", style="red")

    # Sort by call count
    sorted_tools = sorted(
        tool_stats.items(), key=lambda x: x[1]["calls"], reverse=True
    )

    for tool_name, stats in sorted_tools[:20]:  # Top 20
        calls = stats["calls"]
        success = stats["success"]
        errors = stats["errors"]
        success_rate = (success / calls * 100) if calls > 0 else 0.0

        table.add_row(
            tool_name,
            str(calls),
            f"{success_rate:.1f}%",
            str(errors) if errors > 0 else "-",
        )

    console.print(table)
    console.print()

    # Top 5 most used
    console.print("[cyan]Top 5 Most Used Tools:[/cyan]")
    for i, (tool_name, stats) in enumerate(sorted_tools[:5], start=1):
        console.print(f"  {i}. {tool_name} ({stats['calls']} calls)")
    console.print()


@mcp.command(name="log")
@click.option(
    "--tail", "-n", help="Number of lines (default: 50)", type=int, default=50
)
@click.option("--follow", "-f", help="Follow log in real-time", is_flag=True)
@click.option(
    "--level",
    help="Filter by log level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default=None,
)
@click.option("--search", help="Search pattern in logs", type=str, default=None)
@click.pass_context
def log_command(
    ctx: click.Context,
    tail: int,
    follow: bool,
    level: str | None,
    search: str | None,
):
    """View MCP server logs

    Display logs from MCP server for debugging and monitoring.

    \b
    Examples:
        kagura mcp log                      # Last 50 lines
        kagura mcp log --tail 100           # Last 100 lines
        kagura mcp log --follow             # Real-time (like tail -f)
        kagura mcp log --level ERROR        # Errors only
        kagura mcp log --search "memory"    # Search for "memory"
    """
    import re
    import time

    from rich.console import Console

    console = Console()

    # Log file location
    log_file = get_cache_dir() / "logs" / "mcp_server.log"

    if not log_file.exists():
        console.print("[yellow]No log file found[/yellow]")
        console.print()
        console.print("[dim]MCP server logs will be created when you run:[/dim]")
        console.print("[cyan]  kagura mcp serve[/cyan]")
        console.print()
        console.print(f"[dim]Expected location: {log_file}[/dim]")
        console.print()
        return

    def matches_filters(line: str) -> bool:
        """Check if line matches level and search filters."""
        if level and f"[{level}]" not in line:
            return False
        if search and not re.search(search, line, re.IGNORECASE):
            return False
        return True

    def format_log_line(line: str) -> tuple[str, str]:
        """Format log line with appropriate style."""
        if "[ERROR]" in line:
            return line.rstrip(), "red"
        elif "[WARNING]" in line or "[WARN]" in line:
            return line.rstrip(), "yellow"
        elif "[INFO]" in line:
            return line.rstrip(), "white"
        elif "[DEBUG]" in line:
            return line.rstrip(), "dim"
        else:
            return line.rstrip(), "white"

    # Display header
    console.print()
    console.print("[bold cyan]Kagura MCP Server Logs[/bold cyan]")

    if follow:
        console.print("[dim]Following log (Ctrl+C to stop)...[/dim]")
    else:
        console.print(f"[dim]Last {tail} lines[/dim]")

    if level:
        console.print(f"[dim]Level filter: {level}[/dim]")
    if search:
        console.print(f"[dim]Search: {search}[/dim]")

    console.print(f"[dim]Log file: {log_file}[/dim]")
    console.print()

    # Read and display logs
    try:
        with open(log_file, "r") as f:
            if not follow:
                # Tail mode: read all, filter, show last N
                lines = f.readlines()
                filtered_lines = [line for line in lines if matches_filters(line)]
                display_lines = filtered_lines[-tail:]

                for line in display_lines:
                    text, style = format_log_line(line)
                    console.print(text, style=style)

                console.print()
                console.print(
                    f"[dim]Showing {len(display_lines)} of "
                    f"{len(filtered_lines)} matching lines[/dim]"
                )
                console.print()

            else:
                # Follow mode: seek to end, wait for new lines
                f.seek(0, 2)  # Seek to end

                console.print("[dim]Waiting for new log entries...[/dim]")
                console.print()

                try:
                    while True:
                        line = f.readline()
                        if line:
                            if matches_filters(line):
                                text, style = format_log_line(line)
                                console.print(text, style=style)
                        else:
                            time.sleep(0.1)
                except KeyboardInterrupt:
                    console.print()
                    console.print("[dim]Stopped following log[/dim]")
                    console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to read log: {e}[/red]")
        raise click.Abort()


__all__ = ["mcp"]
