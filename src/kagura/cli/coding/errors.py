"""Error tracking and inspection commands."""

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
@click.option("--limit", "-n", default=20, help="Maximum results")
@click.option("--unresolved", is_flag=True, help="Show only unresolved errors")
@click.option("--type", "error_type", help="Filter by error type (e.g., TypeError)")
def errors_command(
    project: str | None,
    user: str | None,
    limit: int,
    unresolved: bool,
    error_type: str | None,
):
    """List errors encountered in a project.

    Examples:
        kagura coding errors --project kagura-ai
        kagura coding errors --project kagura-ai --unresolved
        kagura coding errors --project kagura-ai --type TypeError
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

        # Search for all errors using LIKE pattern
        pattern = f"project:{project}:error:"
        results = coding_mem.persistent.search(
            query=pattern, user_id=user, agent_name=None, limit=1000
        )

        if not results:
            console.print(f"[yellow]No errors found for project '{project}'[/yellow]")
            return

        # Extract error data
        errors_data = []
        for result in results:
            value_str = result.get("value", "{}")
            try:
                data = (
                    json.loads(value_str) if isinstance(value_str, str) else value_str
                )
                # Extract error_id from key: project:PROJECT:error:ERROR_ID
                key = result.get("key", "")
                error_id = key.split(":")[-1] if ":" in key else "unknown"
                data["error_id"] = error_id
                errors_data.append(data)
            except json.JSONDecodeError:
                continue

        # Filter by unresolved
        if unresolved:
            errors_data = [e for e in errors_data if not e.get("resolved", False)]

        # Filter by error type
        if error_type:
            errors_data = [
                e
                for e in errors_data
                if error_type.lower() in e.get("error_type", "").lower()
            ]

        # Sort by timestamp (newest first)
        errors_data.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

        # Limit results
        errors_data = errors_data[:limit]

        # Display table
        table = Table(title=f"Errors: {project}", show_header=True)
        table.add_column("Error ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="red", width=15)
        table.add_column("Location", style="yellow", no_wrap=True)
        table.add_column("Status", justify="center", width=8)
        table.add_column("Date", width=12)

        for error in errors_data:
            error_id = error.get("error_id", "unknown")
            err_type = error.get("error_type", "Unknown")
            file_path = error.get("file_path", "")
            line = error.get("line_number", 0)
            location = f"{file_path}:{line}" if file_path else "N/A"
            resolved = error.get("resolved", False)
            status_icon = "✅" if resolved else "❌"
            timestamp = error.get("timestamp", "")
            date_str = timestamp[:10] if timestamp else "N/A"

            table.add_row(
                error_id,
                err_type,
                location,  # Show full path (no truncation)
                status_icon,
                date_str,
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(errors_data)} errors[/dim]")
        hint = f"Use: kagura coding error <ERROR_ID> --project {project} for details"
        console.print(f"[dim]{hint}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


@click.command()
@click.argument("error_id")
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
def error_command(error_id: str, project: str | None, user: str | None):
    """Show detailed error information including solution.

    Example:
        kagura coding error error_abc123 --project kagura-ai
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

        # Get error
        key = f"project:{project}:error:{error_id}"
        data = coding_mem.persistent.recall(key=key, user_id=user)

        if not data:
            console.print(f"[red]Error not found: {error_id}[/red]")
            return

        # Display error details
        console.print(
            f"\n[bold red]{data.get('error_type', 'Error')}: {error_id}[/bold red]"
        )
        console.print(f"Project: {project}")

        console.print("\n[bold]Message:[/bold]")
        console.print(data.get("message", "N/A"))

        console.print("\n[bold]Location:[/bold]")
        console.print(f"  File: {data.get('file_path', 'N/A')}")
        console.print(f"  Line: {data.get('line_number', 'N/A')}")

        if data.get("stack_trace"):
            console.print("\n[bold]Stack Trace:[/bold]")
            console.print(data["stack_trace"][:500])

        if data.get("solution"):
            console.print("\n[bold green]Solution:[/bold green]")
            console.print(data["solution"])

        console.print("\n[bold]Status:[/bold]")
        console.print(f"  Resolved: {'✅ Yes' if data.get('resolved') else '❌ No'}")
        console.print(f"  Frequency: {data.get('frequency', 1)}")
        console.print(f"  Timestamp: {data.get('timestamp', 'N/A')}")

        if data.get("tags"):
            console.print(f"  Tags: {', '.join(data['tags'])}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise
