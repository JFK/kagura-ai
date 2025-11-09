"""Coding session management and inspection commands."""

import json
from datetime import datetime, timezone

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from kagura.cli.coding.utils import (
    _check_project_required,
    _get_default_user,
    _get_lightweight_coding_memory,
    _parse_time_filter,
)
from kagura.config.project import get_default_project as _get_default_project


@click.command()
@click.option(
    "--user",
    "-u",
    default=None,
    help="User ID (default: $KAGURA_DEFAULT_USER or kiyota)",
)
def projects(user: str | None):
    """List all projects with coding memory.

    Shows unique project names and session counts.

    Example:
        kagura coding projects
        kagura coding projects --user kiyota

        # Or set default:
        export KAGURA_DEFAULT_USER=kiyota
        kagura coding projects
    """
    console = Console()

    # Use environment variable default
    user = user or _get_default_user()

    try:
        from kagura.config.paths import get_data_dir

        # Query database for all unique project IDs
        data_dir = get_data_dir()
        db_path = data_dir / "memory.db"

        if not db_path.exists():
            console.print("[yellow]No coding memory database found.[/yellow]")
            return

        import sqlite3

        conn = sqlite3.connect(db_path)

        # Extract unique project IDs from keys like "project:PROJECT_ID:..."
        query = """
            SELECT DISTINCT
                SUBSTR(key, 9, INSTR(SUBSTR(key, 9), ':') - 1) as project_id,
                COUNT(*) as memory_count
            FROM memories
            WHERE key LIKE 'project:%' AND user_id = ?
            GROUP BY project_id
            ORDER BY memory_count DESC
        """

        cursor = conn.execute(query, (user,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            console.print(f"[yellow]No projects found for user '{user}'[/yellow]")
            return

        # Display table
        table = Table(title=f"Coding Projects (user: {user})", show_header=True)
        table.add_column("Project ID", style="cyan", width=30)
        table.add_column("Memories", justify="right", width=12)

        for project_id, count in rows:
            if project_id:  # Skip empty project IDs
                table.add_row(project_id, str(count))

        console.print(table)
        console.print(f"\n[dim]Total: {len(rows)} projects[/dim]")
        console.print(
            "[dim]Use: kagura coding sessions --project <PROJECT> to see details[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


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
@click.option("--limit", "-n", default=20, help="Maximum results (default: 20)")
@click.option(
    "--success",
    type=click.Choice(["true", "false", "all"]),
    default="all",
    help="Filter by success status",
)
@click.option("--since", help="Time filter (e.g., 7d, 30d, 2024-11-01)")
def sessions_command(
    project: str | None, user: str | None, limit: int, success: str, since: str | None
):
    """List coding sessions for a project.

    Shows session history with descriptions, durations, and outcomes.

    Examples:
        kagura coding sessions --project kagura-ai
        kagura coding sessions --success true  # Uses $KAGURA_DEFAULT_PROJECT
        kagura coding sessions --since 7d

        # Set defaults:
        export KAGURA_DEFAULT_PROJECT=kagura-ai
        export KAGURA_DEFAULT_USER=kiyota
    """
    console = Console()

    # Use environment variable defaults
    project = project or _get_default_project()
    user = user or _get_default_user()

    if not project:
        console.print(
            "[red]Error: No project specified and $KAGURA_DEFAULT_PROJECT not set[/red]"
        )
        console.print("[dim]Usage: kagura coding sessions --project PROJECT[/dim]")
        console.print("[dim]Or set: export KAGURA_DEFAULT_PROJECT=your-project[/dim]")
        return

    try:
        # Create manager with lightweight config for fast CLI startup
        coding_mem = _get_lightweight_coding_memory(user_id=user, project_id=project)

        # Search for all sessions using LIKE pattern
        pattern = f"project:{project}:session:"
        results = coding_mem.persistent.search(
            query=pattern, user_id=user, agent_name=None, limit=1000
        )

        if not results:
            console.print(f"[yellow]No sessions found for project '{project}'[/yellow]")
            return

        # Extract session data
        sessions_data = []
        for result in results:
            value_str = result.get("value", "{}")
            try:
                data = (
                    json.loads(value_str) if isinstance(value_str, str) else value_str
                )
                # session_id should already be in data, but double-check
                if "session_id" not in data:
                    key = result.get("key", "")
                    session_id = key.split(":")[-1] if ":" in key else "unknown"
                    data["session_id"] = session_id
                sessions_data.append(data)
            except json.JSONDecodeError:
                continue

        # Filter by success
        if success != "all":
            success_bool = success == "true"
            sessions_data = [
                s for s in sessions_data if s.get("success") == success_bool
            ]

        # Filter by time
        if since:
            cutoff_time = _parse_time_filter(since)
            sessions_data = [
                s
                for s in sessions_data
                if datetime.fromisoformat(s["start_time"]).replace(tzinfo=timezone.utc)
                >= cutoff_time
            ]

        # Sort by start_time (newest first)
        sessions_data.sort(key=lambda s: s.get("start_time", ""), reverse=True)

        # Limit results
        sessions_data = sessions_data[:limit]

        # Display table
        table = Table(title=f"Coding Sessions: {project}", show_header=True)
        table.add_column("Session ID", style="cyan", no_wrap=True)
        table.add_column("Description", style="white", width=35)
        table.add_column("Start", style="dim", width=16)
        table.add_column("End", style="dim", width=16)
        table.add_column("Duration", justify="right", width=10)
        table.add_column("Status", justify="center", width=10)

        for session in sessions_data:
            session_id = session["session_id"]
            description = session.get("description", "No description")[:32]

            # Format timestamps
            start_time = session.get("start_time", "")
            end_time = session.get("end_time", "")

            try:
                start_dt = datetime.fromisoformat(start_time).strftime("%m-%d %H:%M")
            except Exception:
                start_dt = "-"

            # Check if session is active (no end_time or end_time is None)
            is_active = not end_time or end_time == "None"

            if is_active:
                end_dt = "[yellow]Active[/yellow]"
                # Calculate ongoing duration from start time
                try:
                    start = datetime.fromisoformat(start_time)
                    ongoing_duration = (
                        datetime.now(timezone.utc) - start.replace(tzinfo=timezone.utc)
                    ).total_seconds() / 60
                    duration_str = f"[yellow]{ongoing_duration:.0f}m[/yellow]"
                except Exception:
                    duration_str = "[yellow]ongoing[/yellow]"
            else:
                try:
                    end_dt = datetime.fromisoformat(end_time).strftime("%m-%d %H:%M")
                except Exception:
                    end_dt = "-"

                # Calculate duration from stored value or compute from times
                duration = session.get("duration_minutes", 0)
                if not duration and start_time and end_time:
                    try:
                        start = datetime.fromisoformat(start_time)
                        end = datetime.fromisoformat(end_time)
                        duration = (end - start).total_seconds() / 60
                    except Exception:
                        duration = 0
                duration_str = f"{duration:.0f}m" if duration else "-"

            success_status = session.get("success")
            if is_active:
                status_icon = "[yellow]🔄 Active[/yellow]"
            else:
                status_icon = (
                    "✅ Done"
                    if success_status
                    else ("⚠️ Issue" if success_status is False else "ℹ️ Info")
                )

            table.add_row(
                session_id, description, start_dt, end_dt, duration_str, status_icon
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(sessions_data)} sessions[/dim]")
        console.print("[dim]Use: kagura coding session <SESSION_ID> for details[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


@click.command()
@click.argument("session_id")
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
def session_command(session_id: str, project: str | None, user: str | None):
    """Show detailed session information.

    Example:
        kagura coding session session_abc123 --project kagura-ai
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

        # Get session
        key = f"project:{project}:session:{session_id}"
        data = coding_mem.persistent.recall(key=key, user_id=user)

        if not data:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        # Display session details with Panel
        # Header
        success_status = data.get("success")
        status_icon = (
            "✅" if success_status else ("⚠️" if success_status is False else "ℹ️")
        )

        console.print(f"\n[bold cyan]Session: {session_id}[/bold cyan] {status_icon}")
        console.print(f"[dim]Project: {project}[/dim]")
        console.print()

        # Overview panel
        end_time = data.get("end_time")
        is_active = not end_time or end_time == "None"

        if is_active:
            # Calculate ongoing duration
            try:
                start = datetime.fromisoformat(data.get("start_time", ""))
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                duration = (now - start).total_seconds() / 60
                duration_str = f"[yellow]{duration:.1f} minutes (ongoing)[/yellow]"
                end_str = "[yellow]In progress[/yellow]"
            except Exception:
                duration_str = "[yellow]In progress[/yellow]"
                end_str = "[yellow]In progress[/yellow]"
        else:
            duration = data.get("duration_minutes", 0)
            if not duration and data.get("start_time") and end_time:
                # Calculate from timestamps
                try:
                    start = datetime.fromisoformat(data.get("start_time"))
                    end = datetime.fromisoformat(end_time)
                    duration = (end - start).total_seconds() / 60
                except Exception:
                    duration = 0
            duration_str = f"{duration:.1f} minutes" if duration else "Unknown"
            end_str = end_time

        overview = (
            f"[bold]Description:[/bold] {data.get('description', 'N/A')}\n"
            f"[bold]Start:[/bold] {data.get('start_time', 'N/A')}\n"
            f"[bold]End:[/bold] {end_str}\n"
            f"[bold]Duration:[/bold] {duration_str}\n"
            f"[bold]Success:[/bold] {success_status if not is_active else '[yellow]In progress[/yellow]'}"
        )

        console.print(Panel(overview, title="Overview", border_style="blue"))
        console.print()

        # Activities panel
        files_touched = data.get("files_touched", [])
        activities = (
            f"[bold]Files touched:[/bold] {len(files_touched)}\n"
            f"[bold]Errors encountered:[/bold] {data.get('errors_encountered', 0)}\n"
            f"[bold]Errors fixed:[/bold] {data.get('errors_fixed', 0)}\n"
            f"[bold]Decisions made:[/bold] {data.get('decisions_made', 0)}"
        )

        console.print(Panel(activities, title="Statistics", border_style="green"))
        console.print()

        # Files touched (detailed)
        if files_touched:
            console.print("[bold cyan]Files Modified:[/bold cyan]")
            for i, file in enumerate(files_touched[:10], 1):
                console.print(f"  {i}. {file}")
            if len(files_touched) > 10:
                console.print(f"  [dim]... and {len(files_touched) - 10} more[/dim]")
            console.print()

        # Tags
        if data.get("tags"):
            console.print(f"[bold cyan]Tags:[/bold cyan] {', '.join(data['tags'])}")
            console.print()

        # Summary
        if data.get("summary"):
            console.print(
                Panel(
                    data["summary"], title="AI-Generated Summary", border_style="yellow"
                )
            )
            console.print()

        # Additional details link
        console.print("[dim]For file changes, errors, and decisions, use:[/dim]")
        console.print(f"[dim]  • kagura coding errors --project {project}[/dim]")
        console.print(f"[dim]  • kagura coding decisions --project {project}[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise
