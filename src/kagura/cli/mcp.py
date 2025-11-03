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
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    )
    # Force immediate flush
    file_handler.setLevel(logging.DEBUG)

    # Set log level from environment variable (default: INFO)
    log_level_name = os.environ.get("KAGURA_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Setup root kagura logger (applies to all kagura.* modules)
    root_logger = logging.getLogger("kagura")
    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level)

    # Also setup MCP-specific logger
    logger = logging.getLogger("kagura.mcp")
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
@click.option("--api-url", default="http://localhost:8000", help="API server URL")
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
        console.print(
            "[red]✗ Error: API base URL must start with http:// or https://[/red]"
        )
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
@click.option(
    "--remote-only",
    is_flag=True,
    help="Show only remote-capable tools",
)
@click.option(
    "--local-only",
    is_flag=True,
    help="Show only local-only tools",
)
@click.option(
    "--category",
    "-c",
    help="Filter by category",
    type=str,
)
@click.pass_context
def list_tools(
    ctx: click.Context,
    remote_only: bool,
    local_only: bool,
    category: str | None,
):
    """List available MCP tools

    Shows all MCP tools that Kagura provides, with remote capability indicators.

    Examples:
      kagura mcp tools
      kagura mcp tools --remote-only
      kagura mcp tools --category memory --remote-only
    """
    from rich.console import Console
    from rich.table import Table

    from kagura.core.registry import tool_registry
    from kagura.mcp.tool_classification import is_remote_capable

    console = Console()

    # Validate conflicting flags
    if remote_only and local_only:
        console.print(
            "[red]Error: --remote-only and --local-only are mutually exclusive.[/red]\n"
        )
        console.print("Use one or the other, not both.\n")
        ctx.exit(1)

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

    def infer_category(tool_name: str) -> str:
        """Infer category from tool name prefix.

        Args:
            tool_name: Name of the tool

        Returns:
            Category name
        """
        prefix_mapping = {
            "memory_": "memory",
            "coding_": "coding",
            "claude_code_": "coding",
            "github_": "github",
            "gh_": "github",  # Legacy gh_*_safe tools
            "brave_": "brave_search",
            "youtube_": "youtube",
            "get_youtube_": "youtube",
            "file_": "file",
            "dir_": "file",
            "multimodal_": "multimodal",
            "arxiv_": "academic",
            "fact_check_": "fact_check",
            "media_": "media",
            "meta_": "meta",
            "telemetry_": "observability",
            "route_": "routing",
            "web_": "web",
            "shell_": "shell",
        }

        for prefix, cat in prefix_mapping.items():
            if tool_name.startswith(prefix):
                return cat

        return "other"

    # Filter tools
    filtered_tools = {}
    for tool_name, tool_func in all_tools.items():
        # Filter by remote/local
        if remote_only and not is_remote_capable(tool_name):
            continue
        if local_only and is_remote_capable(tool_name):
            continue

        # Filter by category
        if category:
            tool_category = infer_category(tool_name)
            if tool_category != category:
                continue

        filtered_tools[tool_name] = tool_func

    if not filtered_tools:
        console.print("[yellow]No tools match the specified filters.[/yellow]")
        return

    # Count remote vs local
    remote_count = sum(1 for name in filtered_tools if is_remote_capable(name))
    local_count = len(filtered_tools) - remote_count

    console.print(f"\n[bold]Kagura MCP Tools ({len(filtered_tools)})[/bold]")
    console.print(
        f"[dim]Remote-capable: {remote_count} | Local-only: {local_count}[/dim]\n"
    )

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Remote", justify="center", style="bold")
    table.add_column("Description")

    for tool_name, tool_func in sorted(filtered_tools.items()):
        # Determine category using inference
        tool_category = infer_category(tool_name)

        # Remote indicator
        remote_indicator = "✓" if is_remote_capable(tool_name) else "✗"
        remote_style = "green" if is_remote_capable(tool_name) else "red"

        # Get description from docstring
        description = tool_func.__doc__ or "No description"
        description = description.strip().split("\n")[0]
        if len(description) > 50:
            description = description[:47] + "..."

        table.add_row(
            tool_name,
            tool_category,
            f"[{remote_style}]{remote_indicator}[/{remote_style}]",
            description,
        )

    console.print(table)
    console.print("\n[dim]Legend: ✓ = Remote-capable | ✗ = Local-only[/dim]")
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
    executions = store.get_executions(agent_name=agent, since=since, limit=100000)

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
    sorted_tools = sorted(tool_stats.items(), key=lambda x: x[1]["calls"], reverse=True)

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


@mcp.command(name="monitor")
@click.option(
    "--tool", "-t", help="Filter by tool name pattern", type=str, default=None
)
@click.option(
    "--refresh",
    "-r",
    help="Refresh interval in seconds",
    type=float,
    default=1.0,
)
@click.option(
    "--db", help="Path to telemetry database", type=click.Path(), default=None
)
@click.pass_context
def monitor_command(
    ctx: click.Context,
    tool: str | None,
    refresh: float,
    db: str | None,
):
    """Live monitoring dashboard for MCP tools

    Shows real-time MCP tool usage statistics with auto-refresh.
    Similar to 'kagura monitor' but for MCP tools specifically.

    \b
    Examples:
        kagura mcp monitor                     # Monitor all tools
        kagura mcp monitor --tool memory_*     # Monitor memory tools
        kagura mcp monitor --refresh 2         # Refresh every 2 seconds
    """
    import time
    from collections import defaultdict
    from datetime import datetime, timedelta
    from pathlib import Path

    from rich.console import Console
    from rich.live import Live
    from rich.table import Table

    from kagura.observability import EventStore

    console = Console()

    # Load event store
    db_path = Path(db) if db else None
    store = EventStore(db_path)

    console.print("\n[cyan]Starting MCP Monitor... (Press Ctrl+C to exit)[/cyan]")
    console.print()
    time.sleep(0.5)

    def create_dashboard() -> Table:
        """Create dashboard table with current stats."""
        # Get recent events (last 5 minutes)
        cutoff = datetime.now() - timedelta(minutes=5)
        events = store.get_executions(since=cutoff.timestamp(), limit=1000)

        # Filter MCP tool events (executions that have tool_name)
        mcp_events = [e for e in events if e.get("metadata", {}).get("tool_name")]

        # Apply tool filter
        if tool:
            import fnmatch

            mcp_events = [
                e for e in mcp_events if fnmatch.fnmatch(e.get("tool_name", ""), tool)
            ]

        # Calculate statistics
        tool_stats = defaultdict(lambda: {"calls": 0, "errors": 0, "total_time": 0})

        for event in mcp_events:
            metadata = event.get("metadata", {})
            tool_name = metadata.get("tool_name", "unknown")
            tool_stats[tool_name]["calls"] += 1

            # Check for errors
            if event.get("status") == "failed" or event.get("error"):
                tool_stats[tool_name]["errors"] += 1

            # Duration (stored in seconds, convert to ms)
            duration_sec = event.get("duration", 0)
            tool_stats[tool_name]["total_time"] += duration_sec * 1000

        # Create table
        table = Table(title="MCP Tools - Live Monitor (Last 5 min)", show_header=True)
        table.add_column("Tool Name", style="cyan")
        table.add_column("Calls", justify="right", style="white")
        table.add_column("Success Rate", justify="right", style="green")
        table.add_column("Avg Time", justify="right", style="yellow")
        table.add_column("Errors", justify="right", style="red")

        # Sort by call count
        sorted_tools = sorted(
            tool_stats.items(), key=lambda x: x[1]["calls"], reverse=True
        )

        for tool_name, stats in sorted_tools[:15]:  # Top 15 tools
            calls = stats["calls"]
            errors = stats["errors"]
            success_rate = ((calls - errors) / calls * 100) if calls > 0 else 0
            avg_time = (stats["total_time"] / calls) if calls > 0 else 0

            table.add_row(
                tool_name,
                str(calls),
                f"{success_rate:.1f}%",
                f"{avg_time:.0f}ms",
                str(errors) if errors > 0 else "-",
            )

        if not sorted_tools:
            table.add_row("No activity", "-", "-", "-", "-")

        return table

    try:
        with Live(
            create_dashboard(), refresh_per_second=1 / refresh, console=console
        ) as live:
            while True:
                time.sleep(refresh)
                live.update(create_dashboard())
    except KeyboardInterrupt:
        console.print("\n[cyan]Monitor stopped.[/cyan]\n")


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


@mcp.command(name="install-reranking")
@click.option(
    "--model",
    default="cross-encoder/ms-marco-MiniLM-L-6-v2",
    help="Cross-encoder model to install",
)
def install_reranking(model: str):
    """Install semantic reranking model

    Downloads and caches the cross-encoder model for improved semantic
    search precision. First-time download may take 2-5 minutes.

    Once installed, reranking is automatically enabled for all memory
    search operations.

    Examples:
        # Install default model
        kagura mcp install-reranking

        # Install specific model
        kagura mcp install-reranking --model cross-encoder/ms-marco-MiniLM-L-12-v2
    """
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn

    console = Console()

    console.print("\n[bold]Installing Semantic Reranking Support[/bold]\n")

    # Check sentence-transformers installation
    try:
        import sentence_transformers  # noqa: F401

        console.print("[green]✓[/green] sentence-transformers installed")
    except ImportError:
        console.print("[red]✗[/red] sentence-transformers not installed")
        console.print()
        console.print("Install with: [cyan]uv add sentence-transformers[/cyan]")
        console.print("Or: [cyan]pip install sentence-transformers[/cyan]")
        console.print()
        raise click.Abort()

    # Check if model is already cached
    from kagura.core.memory.reranker import is_reranker_available

    if is_reranker_available(model):
        console.print(f"[green]✓[/green] Model '{model}' already cached")
        console.print()
        console.print("[dim]Reranking is ready to use![/dim]")
        console.print()
        return

    # Download model with progress
    console.print(f"[yellow]Downloading model:[/yellow] {model}")
    console.print("[dim]This may take 2-5 minutes...[/dim]")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading model...", total=None)

        try:
            from sentence_transformers import CrossEncoder

            # Intentional cache warming: load model to trigger download, then discard.
            # The cached model will be reloaded when actually used.
            _ = CrossEncoder(model)

            progress.update(task, description="[green]✓ Model downloaded![/green]")
        except Exception as e:
            progress.stop()
            console.print(f"[red]✗ Download failed:[/red] {e}")
            raise click.Abort()

    console.print()
    console.print("[green]✓ Reranking model installed successfully![/green]")
    console.print()
    console.print("[yellow]To enable reranking:[/yellow]")
    console.print("  Set env var: [cyan]KAGURA_ENABLE_RERANKING=true[/cyan]")
    console.print("  Or in Python:")
    console.print("    [cyan]config = MemorySystemConfig()[/cyan]")
    console.print("    [cyan]config.rerank.enabled = True[/cyan]")
    console.print()


@mcp.command()
@click.option(
    "--tool", "-t", help="Filter by tool name pattern", type=str, default=None
)
@click.option(
    "--interval",
    "-i",
    help="Refresh interval in seconds",
    type=float,
    default=1.0,
)
def monitor(tool: str | None, interval: float) -> None:
    """Live MCP tool monitoring dashboard.

    Shows real-time statistics for MCP tool calls with auto-refresh.

    Examples:
        kagura mcp monitor                    # Monitor all tools
        kagura mcp monitor --tool memory_*    # Filter specific tools
        kagura mcp monitor --interval 0.5     # Refresh every 0.5 seconds
    """
    import time

    from rich.console import Console
    from rich.live import Live
    from rich.table import Table

    from kagura.config.paths import get_data_dir

    console = Console()
    console.print("[bold]MCP Tool Monitor[/bold] - Press Ctrl+C to exit\n")

    try:
        import sqlite3

        db_path = get_data_dir() / "telemetry.db"

        if not db_path.exists():
            console.print(
                "[yellow]No telemetry data found. Start using MCP tools first.[/yellow]"
            )
            return

        def generate_table() -> Table:
            """Generate current statistics table."""
            table = Table(title="Live MCP Tool Statistics", show_header=True)
            table.add_column("Tool", style="cyan", width=30)
            table.add_column("Calls", justify="right", width=8)
            table.add_column("Success", justify="right", width=10)
            table.add_column("Errors", justify="right", width=8)
            table.add_column("Avg Time", justify="right", width=10)

            conn = sqlite3.connect(db_path)

            # Query recent tool stats (last 5 minutes)
            # Note: started_at is Unix timestamp (REAL), so use unixepoch() or strftime()
            query = """
                SELECT
                    agent_name as tool,
                    COUNT(*) as calls,
                    SUM(CASE WHEN error IS NULL THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors,
                    AVG(duration) as avg_duration
                FROM executions
                WHERE started_at >= (strftime('%s', 'now') - 300)
            """

            if tool:
                query += f" AND agent_name LIKE '%{tool}%'"

            query += """
                GROUP BY agent_name
                ORDER BY calls DESC
                LIMIT 20
            """

            cursor = conn.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                tool_name, calls, success_count, errors_count, avg_dur = row
                success_rate = (
                    f"{(success_count / calls) * 100:.1f}%" if calls > 0 else "-"
                )
                avg_time = f"{avg_dur:.2f}s" if avg_dur else "-"

                table.add_row(
                    tool_name or "unknown",
                    str(calls),
                    success_rate,
                    str(errors_count),
                    avg_time,
                )

            conn.close()

            if not rows:
                table.add_row("No activity", "-", "-", "-", "-")

            return table

        # Live monitoring loop
        with Live(
            generate_table(), refresh_per_second=1 / interval, console=console
        ) as live:
            while True:
                time.sleep(interval)
                live.update(generate_table())

    except KeyboardInterrupt:
        console.print("\n[dim]Monitoring stopped.[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


__all__ = ["mcp"]
