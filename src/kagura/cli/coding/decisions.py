"""Design decision tracking and inspection commands."""

import json

import click
from rich.console import Console
from rich.table import Table

from kagura.cli.coding.utils import (
    _check_project_required,
    _get_default_user,
    _get_lightweight_coding_memory,
)


@click.command()
@click.option(
    "--project",
    "-p",
    default=None,
    help="Project ID (default: $KAGURA_DEFAULT_PROJECT)",
)
@click.option(
    "--user",
    "-u",
    default=None,
    help="User ID (default: $KAGURA_DEFAULT_USER or kiyota)",
)
@click.option("--limit", "-n", default=10, help="Maximum results")
@click.option("--min-confidence", type=float, help="Minimum confidence (0.0-1.0)")
@click.option("--tag", help="Filter by tag")
def decisions_command(
    project: str | None,
    user: str | None,
    limit: int,
    min_confidence: float | None,
    tag: str | None,
):
    """List design decisions for a project.

    Examples:
        kagura coding decisions --project kagura-ai
        kagura coding decisions --project kagura-ai --min-confidence 0.8
        kagura coding decisions --project kagura-ai --tag architecture
    """
    console = Console()

    # Use environment variable defaults
    project = _check_project_required(project, console)
    user = user or _get_default_user()
    if not project:
        return

    try:
        # Create manager with lightweight config for fast CLI startup
        coding_mem = _get_lightweight_coding_memory(user_id=user, project_id=project)

        # Search for all decisions using LIKE pattern
        pattern = f"project:{project}:decision:"
        results = coding_mem.persistent.search(
            query=pattern, user_id=user, agent_name=None, limit=1000
        )

        if not results:
            console.print(
                f"[yellow]No decisions found for project '{project}'[/yellow]"
            )
            return

        # Extract decision data
        decisions_data = []
        for result in results:
            value_str = result.get("value", "{}")
            try:
                data = (
                    json.loads(value_str) if isinstance(value_str, str) else value_str
                )
                # Extract decision_id from key: project:PROJECT:decision:DECISION_ID
                key = result.get("key", "")
                decision_id = key.split(":")[-1] if ":" in key else "unknown"
                data["decision_id"] = decision_id
                decisions_data.append(data)
            except json.JSONDecodeError:
                continue

        # Filter by confidence
        if min_confidence is not None:
            decisions_data = [
                d for d in decisions_data if d.get("confidence", 0) >= min_confidence
            ]

        # Filter by tag
        if tag:
            decisions_data = [d for d in decisions_data if tag in d.get("tags", [])]

        # Sort by timestamp (newest first)
        decisions_data.sort(key=lambda d: d.get("timestamp", ""), reverse=True)

        # Limit results
        decisions_data = decisions_data[:limit]

        # Display table
        table = Table(title=f"Design Decisions: {project}", show_header=True)
        table.add_column("Decision ID", style="cyan", no_wrap=True)
        table.add_column("Decision", style="white", width=50)
        table.add_column("Confidence", justify="right", width=10)
        table.add_column("Date", width=12)

        for decision in decisions_data:
            decision_id = decision.get("decision_id", "unknown")
            decision_text = decision.get("decision", "")[:50]
            confidence = decision.get("confidence", 0)
            timestamp = decision.get("timestamp", "")
            date_str = timestamp[:10] if timestamp else "N/A"

            table.add_row(
                decision_id,
                decision_text,
                f"{confidence * 100:.0f}%",
                date_str,
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(decisions_data)} decisions[/dim]")
        hint = f"Use: kagura coding decision <ID> --project {project} for details"
        console.print(f"[dim]{hint}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


@click.command()
@click.argument("decision_id")
@click.option(
    "--project",
    "-p",
    default=None,
    help="Project ID (default: $KAGURA_DEFAULT_PROJECT)",
)
@click.option(
    "--user",
    "-u",
    default=None,
    help="User ID (default: $KAGURA_DEFAULT_USER or kiyota)",
)
def decision_command(decision_id: str, project: str | None, user: str | None):
    """Show detailed decision information.

    Example:
        kagura coding decision decision_abc123 --project kagura-ai
    """
    console = Console()

    # Use environment variable defaults
    project = _check_project_required(project, console)
    user = user or _get_default_user()
    if not project:
        return

    try:
        # Create manager with lightweight config for fast CLI startup
        coding_mem = _get_lightweight_coding_memory(user_id=user, project_id=project)

        # Get decision
        key = f"project:{project}:decision:{decision_id}"
        data = coding_mem.persistent.recall(key=key, user_id=user)

        if not data:
            console.print(f"[red]Decision not found: {decision_id}[/red]")
            return

        # Display decision details
        console.print(f"\n[bold]Decision: {decision_id}[/bold]")
        console.print(f"Project: {project}")
        console.print(f"\n[bold cyan]{data.get('decision', 'N/A')}[/bold cyan]")

        console.print("\n[bold]Rationale:[/bold]")
        console.print(data.get("rationale", "N/A"))

        if data.get("alternatives"):
            console.print("\n[bold]Alternatives considered:[/bold]")
            for alt in data["alternatives"]:
                console.print(f"  • {alt}")

        if data.get("impact"):
            console.print("\n[bold]Impact:[/bold]")
            console.print(data["impact"])

        console.print("\n[bold]Metadata:[/bold]")
        console.print(f"  Confidence: {data.get('confidence', 0) * 100:.0f}%")
        console.print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
        console.print(f"  Reviewed: {data.get('reviewed', False)}")

        if data.get("tags"):
            console.print(f"  Tags: {', '.join(data['tags'])}")

        if data.get("related_files"):
            console.print("\n[bold]Related files:[/bold]")
            for file in data["related_files"]:
                console.print(f"  • {file}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise
