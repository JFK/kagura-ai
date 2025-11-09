"""MCP telemetry commands - tool usage analysis"""

import csv
import json

import click
from rich.console import Console


@click.group(name="telemetry")
def telemetry_group() -> None:
    """MCP telemetry and usage analysis.

    Commands for monitoring and analyzing MCP tool usage patterns.

    Examples:
        kagura mcp telemetry tools --since 30d
        kagura mcp telemetry tools --export usage.csv
    """
    pass


@telemetry_group.command(name="tools")
@click.option(
    "--since",
    default="30d",
    help="Time range (e.g., 7d, 30d, all)",
)
@click.option(
    "--threshold",
    default=0.1,
    type=float,
    help="Usage percentage threshold for categorization (default: 0.1)",
)
@click.option(
    "--export",
    type=click.Path(),
    default=None,
    help="Export results to CSV/JSON file",
)
def telemetry_tools_command(since: str, threshold: float, export: str | None) -> None:
    """Analyze MCP tool usage patterns.

    Shows tool call statistics, success rates, and usage trends.
    Helps identify commonly used tools and potential deprecation candidates.

    Examples:
        kagura mcp telemetry tools
        kagura mcp telemetry tools --since 7d
        kagura mcp telemetry tools --threshold 0.05 --export usage.csv
    """
    # Import and delegate to existing implementation
    from kagura.cli.telemetry_cli import analyze_tool_usage, display_analysis

    console = Console()

    # Parse time range
    if since == "all":
        days = 999999
    else:
        days = int(since.replace("d", ""))

    # Run analysis and display
    analysis = analyze_tool_usage(days=days, threshold_percent=threshold)
    display_analysis(analysis)

    # Export if requested
    if export and "error" not in analysis:
        if export.endswith(".csv"):
            # Export to CSV
            with open(export, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "name",
                        "calls",
                        "percentage",
                        "success",
                        "errors",
                        "success_rate",
                        "avg_duration",
                    ],
                )
                writer.writeheader()
                writer.writerows(analysis["tool_stats"])
            console.print(f"\n[green]✓ Exported to {export}[/green]\n")
        else:
            # Export to JSON
            with open(export, "w") as f:
                json.dump(analysis, f, indent=2)
            console.print(f"\n[green]✓ Exported to {export}[/green]\n")
