"""MCP core commands - server and diagnostics

Provides core MCP server management commands (serve, doctor).
"""

import asyncio
import os
import sys
from typing import Any

import click
from mcp.server.stdio import stdio_server  # type: ignore

from kagura.config.paths import get_cache_dir
from kagura.mcp import create_mcp_server


@click.command()
@click.option("--name", default="kagura-ai", help="Server name (default: kagura-ai)")
@click.option(
    "--remote",
    is_flag=True,
    help="Use remote API connection (requires: kagura mcp connect)",
)
@click.option(
    "--categories",
    default=None,
    help="Comma-separated list of categories to enable (e.g., 'coding,memory,github')",
)
@click.pass_context
def serve(ctx: click.Context, name: str, remote: bool, categories: str | None):
    """Start MCP server

    Starts the MCP server using stdio transport.
    This command is typically called by MCP clients (Claude Code, Cline, etc.).

    Examples:
        # Local mode (default, all tools available)
        kagura mcp serve

        # Remote mode (connect to remote API, safe tools only)
        kagura mcp serve --remote

        # Filter by categories (only coding and memory tools)
        kagura mcp serve --categories coding,memory,github

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

    Category Filtering (environment variable):
      {
        "mcpServers": {
          "kagura-memory": {
            "command": "kagura",
            "args": ["mcp", "serve"],
            "env": {
              "KAGURA_MCP_CATEGORIES": "memory,coding"
            }
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
        import kagura.mcp.tools  # noqa: F401  # Auto-register tools

        logger.info("Loaded built-in MCP tools")
        if verbose:
            click.echo("Loaded built-in MCP tools", err=True)
    except ImportError:
        logger.warning("Could not load built-in tools")
        if verbose:
            click.echo("Warning: Could not load built-in tools", err=True)

    # Parse categories parameter
    enabled_categories = None
    if categories:
        enabled_categories = set(cat.strip() for cat in categories.split(","))
        logger.info(f"Category filter enabled: {', '.join(sorted(enabled_categories))}")
        if verbose:
            click.echo(
                f"Category filter: {', '.join(sorted(enabled_categories))}", err=True
            )
    else:
        # Check environment variable as fallback
        env_categories = os.getenv("KAGURA_MCP_CATEGORIES")
        if env_categories:
            enabled_categories = set(cat.strip() for cat in env_categories.split(","))
            logger.info(
                f"Category filter from env: {', '.join(sorted(enabled_categories))}"
            )
            if verbose:
                click.echo(
                    f"Category filter (from env): {', '.join(sorted(enabled_categories))}",
                    err=True,
                )

    # Create MCP server with optional category filter
    server = create_mcp_server(
        name, context="local", categories=enabled_categories
    )
    if enabled_categories:
        logger.info(
            f"MCP server created with context: local, categories: {', '.join(sorted(enabled_categories))}"
        )
    else:
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


@click.command()
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


__all__ = ["serve", "doctor"]
