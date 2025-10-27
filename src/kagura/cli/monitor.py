"""Monitor command for observing agent execution telemetry."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import click

from ..observability import EventStore
from ..observability.dashboard import Dashboard


@click.group(invoke_without_command=True)
@click.option("--agent", "-a", help="Filter by agent name", type=str, default=None)
@click.option(
    "--refresh",
    "-r",
    help="Refresh interval in seconds",
    type=float,
    default=1.0,
)
@click.option(
    "--db",
    help="Path to telemetry database",
    type=click.Path(),
    default=None,
)
@click.pass_context
def monitor(
    ctx: click.Context,
    agent: Optional[str],
    refresh: float,
    db: Optional[str],
) -> None:
    """Monitor agent execution telemetry.

    When called without a subcommand, starts live monitoring (default behavior).

    Examples:
        kagura monitor                         # Live dashboard (default)
        kagura monitor --agent my_agent        # Monitor specific agent
        kagura monitor live                    # Explicit live dashboard
        kagura monitor list                    # List recent executions
        kagura monitor stats                   # Show statistics
        kagura monitor trace <execution_id>    # Show trace details
        kagura monitor cost                    # Show cost summary
    """
    if ctx.invoked_subcommand is None:
        # No subcommand provided, run live monitoring
        db_path = Path(db) if db else None
        store = EventStore(db_path)
        dashboard = Dashboard(store)

        click.echo("Starting live monitor... (Press Ctrl+C to exit)")
        time.sleep(0.5)

        try:
            dashboard.show_live(agent_name=agent, refresh_rate=refresh)
        except KeyboardInterrupt:
            click.echo("\nMonitoring stopped.")


@monitor.command()
@click.option("--agent", "-a", help="Filter by agent name", type=str, default=None)
@click.option(
    "--refresh",
    "-r",
    help="Refresh interval in seconds",
    type=float,
    default=1.0,
)
@click.option(
    "--db",
    help="Path to telemetry database",
    type=click.Path(),
    default=None,
)
def live(agent: Optional[str], refresh: float, db: Optional[str]) -> None:
    """Show live monitoring dashboard.

    \b
    Examples:
        kagura monitor live                    # Monitor all agents
        kagura monitor live --agent my_agent   # Monitor specific agent
        kagura monitor live --refresh 2.0      # Refresh every 2 seconds
    """
    db_path = Path(db) if db else None
    store = EventStore(db_path)
    dashboard = Dashboard(store)

    click.echo("Starting live monitor... (Press Ctrl+C to exit)")
    time.sleep(0.5)  # Brief pause before starting

    try:
        dashboard.show_live(agent_name=agent, refresh_rate=refresh)
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped.")


@monitor.command()
@click.option("--agent", "-a", help="Filter by agent name", type=str, default=None)
@click.option(
    "--status",
    "-s",
    help="Filter by status (completed/failed)",
    type=click.Choice(["completed", "failed"]),
    default=None,
)
@click.option(
    "--limit",
    "-n",
    help="Maximum number of executions to show",
    type=int,
    default=20,
)
@click.option(
    "--db",
    help="Path to telemetry database",
    type=click.Path(),
    default=None,
)
def list(
    agent: Optional[str], status: Optional[str], limit: int, db: Optional[str]
) -> None:
    """List recent agent executions.

    \b
    Examples:
        kagura monitor list                        # List all recent executions
        kagura monitor list --agent my_agent       # List for specific agent
        kagura monitor list --status failed        # List failed executions
        kagura monitor list --limit 50             # Show last 50 executions
    """
    db_path = Path(db) if db else None
    store = EventStore(db_path)
    dashboard = Dashboard(store)

    dashboard.show_list(agent_name=agent, limit=limit, status=status)


@monitor.command()
@click.option("--agent", "-a", help="Filter by agent name", type=str, default=None)
@click.option(
    "--since",
    "-s",
    help="Show stats since timestamp (unix timestamp)",
    type=float,
    default=None,
)
@click.option(
    "--db",
    help="Path to telemetry database",
    type=click.Path(),
    default=None,
)
def stats(agent: Optional[str], since: Optional[float], db: Optional[str]) -> None:
    """Show statistics summary.

    \b
    Examples:
        kagura monitor stats                    # Overall statistics
        kagura monitor stats --agent my_agent   # Stats for specific agent
        kagura monitor stats --since 1696953600 # Stats since timestamp
    """
    db_path = Path(db) if db else None
    store = EventStore(db_path)
    dashboard = Dashboard(store)

    dashboard.show_stats(agent_name=agent, since=since)


@monitor.command()
@click.argument("execution_id", type=str)
@click.option(
    "--db",
    help="Path to telemetry database",
    type=click.Path(),
    default=None,
)
def trace(execution_id: str, db: Optional[str]) -> None:
    """Show detailed trace for specific execution.

    \b
    Examples:
        kagura monitor trace exec_abc123        # Show trace details
    """
    db_path = Path(db) if db else None
    store = EventStore(db_path)
    dashboard = Dashboard(store)

    dashboard.show_trace(execution_id)


@monitor.command()
@click.option(
    "--since",
    "-s",
    help="Show cost since timestamp (unix timestamp)",
    type=float,
    default=None,
)
@click.option(
    "--group-by",
    "-g",
    help="Group by agent or date",
    type=click.Choice(["agent", "date"]),
    default="agent",
)
@click.option(
    "--db",
    help="Path to telemetry database",
    type=click.Path(),
    default=None,
)
def cost(since: Optional[float], group_by: str, db: Optional[str]) -> None:
    """Show comprehensive cost and API usage summary.

    Displays LLM costs, embedding usage, and API quota information.

    \b
    Examples:
        kagura monitor cost                     # Cost by agent
        kagura monitor cost --group-by date     # Cost by date
        kagura monitor cost --since 1696953600  # Cost since timestamp

    \b
    Tracks:
        • LLM calls (OpenAI, Anthropic, Google)
        • Embeddings (local E5 or OpenAI)
        • Brave Search quota (2000/month free tier)
        • arXiv search (free, unlimited)
    """
    from rich.console import Console

    db_path = Path(db) if db else None
    store = EventStore(db_path)
    dashboard = Dashboard(store)
    console = Console()

    # Show LLM costs (existing)
    dashboard.show_cost_summary(since=since, group_by=group_by)

    # Show API usage info (Phase 1 - Basic display)
    console.print()
    console.print("[bold cyan]API Usage Information[/bold cyan]")
    console.print()

    # Embeddings
    console.print("[cyan]Embeddings:[/cyan]")
    console.print("  • Model: intfloat/multilingual-e5-large (local)")
    console.print("  • Cost: $0.00 (free, runs locally)")
    console.print("  • Languages: 100+ (including Japanese)")
    console.print()

    # Brave Search
    console.print("[cyan]Brave Search:[/cyan]")
    console.print("  • Free Tier: 2,000 queries/month")
    console.print("  • Current usage: [yellow]Not tracked yet[/yellow]")
    console.print("  • Estimate: Check https://api.search.brave.com/app/dashboard")
    console.print()

    # Other APIs
    console.print("[cyan]Other APIs:[/cyan]")
    console.print("  • arXiv: Free, unlimited")
    console.print("  • YouTube: Free (yt-dlp, no API)")
    console.print()

    console.print("[dim]Note: Full API tracking coming in v4.1.0 (#414)[/dim]")
    console.print()
