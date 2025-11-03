#!/usr/bin/env python3
"""Analyze MCP tool usage from telemetry data.

This script analyzes tool usage patterns to inform decisions about:
- Tool deprecation candidates
- High-priority tools for optimization
- Usage trends and patterns
"""

import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from kagura.config.paths import get_data_dir


def analyze_tool_usage(
    days: int = 30, threshold_percent: float = 0.1
) -> dict[str, Any]:
    """Analyze tool usage from telemetry database.

    Args:
        days: Number of days to analyze (default: 30)
        threshold_percent: Usage threshold for deprecation warning (default: 0.1%)

    Returns:
        Dictionary with analysis results
    """
    db_path = get_data_dir() / "telemetry.db"

    if not db_path.exists():
        return {"error": f"Telemetry database not found: {db_path}"}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Calculate time threshold
    time_threshold = (datetime.now() - timedelta(days=days)).timestamp()

    # Get MCP tool calls
    cursor.execute(
        """
        SELECT agent_name, COUNT(*) as calls,
               SUM(CASE WHEN error IS NULL THEN 1 ELSE 0 END) as success,
               SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors,
               AVG(duration) as avg_duration
        FROM executions
        WHERE agent_name LIKE 'mcp_%'
        AND started_at >= ?
        GROUP BY agent_name
        ORDER BY calls DESC
    """,
        (time_threshold,),
    )

    results = cursor.fetchall()
    conn.close()

    # Process results
    tool_stats = []
    total_calls = sum(r[1] for r in results)

    for agent_name, calls, success, errors, avg_duration in results:
        # Clean tool name
        tool_name = agent_name.replace("mcp_kagura_tool_", "").replace("mcp_", "")

        percentage = (calls / total_calls * 100) if total_calls > 0 else 0
        success_rate = (success / calls * 100) if calls > 0 else 0

        tool_stats.append(
            {
                "name": tool_name,
                "calls": calls,
                "percentage": percentage,
                "success": success,
                "errors": errors,
                "success_rate": success_rate,
                "avg_duration": avg_duration or 0.0,
            }
        )

    # Categorize tools
    high_usage = [t for t in tool_stats if t["percentage"] >= 1.0]
    medium_usage = [t for t in tool_stats if 0.5 <= t["percentage"] < 1.0]
    low_usage = [t for t in tool_stats if 0.1 <= t["percentage"] < 0.5]
    deprecation_candidates = [t for t in tool_stats if t["percentage"] < threshold_percent]

    return {
        "days": days,
        "total_calls": total_calls,
        "unique_tools": len(tool_stats),
        "tool_stats": tool_stats,
        "high_usage": high_usage,
        "medium_usage": medium_usage,
        "low_usage": low_usage,
        "deprecation_candidates": deprecation_candidates,
    }


def display_analysis(analysis: dict[str, Any]) -> None:
    """Display analysis results with rich formatting.

    Args:
        analysis: Analysis results from analyze_tool_usage()
    """
    console = Console()

    if "error" in analysis:
        console.print(f"[red]Error: {analysis['error']}[/red]")
        return

    console.print(f"\n[bold cyan]Tool Usage Analysis (Last {analysis['days']} Days)[/bold cyan]")
    console.print(f"Total MCP calls: {analysis['total_calls']}")
    console.print(f"Unique tools: {analysis['unique_tools']}")
    console.print()

    # Top tools table
    console.print("[bold]Top 10 Most Used Tools[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Tool Name", style="white")
    table.add_column("Calls", justify="right", style="green")
    table.add_column("%", justify="right", style="yellow")
    table.add_column("Success Rate", justify="right", style="blue")
    table.add_column("Avg Time", justify="right", style="dim")

    for i, tool in enumerate(analysis["tool_stats"][:10], 1):
        table.add_row(
            str(i),
            tool["name"],
            str(tool["calls"]),
            f"{tool['percentage']:.1f}%",
            f"{tool['success_rate']:.1f}%",
            f"{tool['avg_duration']:.2f}s",
        )

    console.print(table)
    console.print()

    # Deprecation candidates
    if analysis["deprecation_candidates"]:
        console.print(f"[bold yellow]⚠ Deprecation Candidates (< 0.1% usage)[/bold yellow]")
        dep_table = Table(show_header=True, header_style="bold red")
        dep_table.add_column("Tool Name", style="red")
        dep_table.add_column("Calls", justify="right")
        dep_table.add_column("%", justify="right")

        for tool in analysis["deprecation_candidates"]:
            dep_table.add_row(
                tool["name"], str(tool["calls"]), f"{tool['percentage']:.3f}%"
            )

        console.print(dep_table)
        console.print()

    # Summary
    console.print("[bold]Summary[/bold]")
    console.print(f"  ✅ High usage (≥1%): {len(analysis['high_usage'])} tools")
    console.print(f"  ⚠  Medium usage (0.5-1%): {len(analysis['medium_usage'])} tools")
    console.print(f"  🔍 Low usage (0.1-0.5%): {len(analysis['low_usage'])} tools")
    console.print(
        f"  ❌ Deprecation candidates (<0.1%): {len(analysis['deprecation_candidates'])} tools"
    )
    console.print()


if __name__ == "__main__":
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1

    analysis = analyze_tool_usage(days=days, threshold_percent=threshold)
    display_analysis(analysis)
