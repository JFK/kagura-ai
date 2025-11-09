"""MCP monitoring and logging commands"""

import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import click
from rich.console import Console
from rich.live import Live
from rich.table import Table

from kagura.config.paths import get_cache_dir
from kagura.observability import EventStore


@click.command(name="monitor")
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


@click.command(name="log")
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
