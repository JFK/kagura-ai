"""MCP tools and statistics commands"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from kagura.core.registry import tool_registry
from kagura.mcp.tool_classification import is_remote_capable
from kagura.observability import EventStore


@click.command(name="tools")
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
        import kagura.mcp.tools  # noqa: F401  # Auto-register tools
    except ImportError:
        console.print("[yellow]Warning: Could not load built-in tools[/yellow]\n")

    all_tools = tool_registry.get_all()

    if not all_tools:
        console.print("[yellow]No MCP tools registered.[/yellow]")
        console.print("\n[dim]Tools are auto-registered when you import modules.[/dim]")
        console.print("[dim]Example: from kagura.mcp.tools.memory import storage[/dim]\n")
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


@click.command(name="stats")
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
