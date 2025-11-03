"""CLI commands for Coding Memory inspection.

Provides terminal access to coding sessions, decisions, errors, and file changes
stored in Kagura's Coding Memory system.

Environment Variables:
    KAGURA_DEFAULT_PROJECT: Default project ID for all commands
    KAGURA_DEFAULT_USER: Default user ID (default: kiyota)
"""

import json
import os
from datetime import datetime, timedelta, timezone

import click
from rich.console import Console
from rich.table import Table


def _get_default_project() -> str | None:
    """Get default project from environment variable.

    Returns:
        Default project ID or None
    """
    return os.getenv("KAGURA_DEFAULT_PROJECT")


def _get_default_user() -> str:
    """Get default user from environment variable.

    Returns:
        Default user ID (default: kiyota)
    """
    return os.getenv("KAGURA_DEFAULT_USER", "kiyota")


def _check_project_required(project: str | None, console: Console) -> str | None:
    """Check and return project, show error if missing.

    Args:
        project: Project ID (may be None)
        console: Rich console for output

    Returns:
        Project ID or None (if error shown)
    """
    proj = project or _get_default_project()
    if not proj:
        console.print(
            "[red]Error: No project specified and $KAGURA_DEFAULT_PROJECT not set[/red]"
        )
        console.print("[dim]Set: export KAGURA_DEFAULT_PROJECT=your-project[/dim]")
    return proj


@click.group()
def coding():
    """Coding memory inspection commands.

    Query sessions, decisions, errors, and file changes from terminal.
    Useful for reviewing past work and restoring context.

    Examples:
        kagura coding projects
        kagura coding sessions --project kagura-ai
        kagura coding decisions --project kagura-ai --recent 10
        kagura coding errors --project kagura-ai --unresolved
        kagura coding search --project kagura-ai --query "authentication"
    """
    pass


@coding.command()
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


@coding.command()
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
def sessions(
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
        from kagura.core.memory.coding_memory import CodingMemoryManager

        # Create manager
        coding_mem = CodingMemoryManager(
            user_id=user, project_id=project, enable_rag=False
        )

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


@coding.command()
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
def session(session_id: str, project: str | None, user: str | None):
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
        from kagura.core.memory.coding_memory import CodingMemoryManager

        coding_mem = CodingMemoryManager(
            user_id=user, project_id=project, enable_rag=False
        )

        # Get session
        key = f"project:{project}:session:{session_id}"
        data = coding_mem.persistent.recall(key=key, user_id=user)

        if not data:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        # Display session details with Panel
        from rich.panel import Panel

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
                from datetime import datetime, timezone

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
                    from datetime import datetime

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


@coding.command()
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
def decisions(
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
        from kagura.core.memory.coding_memory import CodingMemoryManager

        coding_mem = CodingMemoryManager(
            user_id=user, project_id=project, enable_rag=False
        )

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


@coding.command()
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
def decision(decision_id: str, project: str | None, user: str | None):
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
        from kagura.core.memory.coding_memory import CodingMemoryManager

        coding_mem = CodingMemoryManager(
            user_id=user, project_id=project, enable_rag=False
        )

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


@coding.command()
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
def errors(
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
        from kagura.core.memory.coding_memory import CodingMemoryManager

        coding_mem = CodingMemoryManager(
            user_id=user, project_id=project, enable_rag=False
        )

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


@coding.command()
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
def error(error_id: str, project: str | None, user: str | None):
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
        from kagura.core.memory.coding_memory import CodingMemoryManager

        coding_mem = CodingMemoryManager(
            user_id=user, project_id=project, enable_rag=False
        )

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


@coding.command()
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
@click.option("--query", "-q", required=True, help="Search query")
@click.option(
    "--type",
    "search_type",
    type=click.Choice(["all", "session", "decision", "error", "change"]),
    default="all",
    help="Search scope",
)
@click.option("--limit", "-n", default=10, help="Maximum results")
def search(
    project: str | None, user: str | None, query: str, search_type: str, limit: int
):
    """Search coding memory with hybrid search (BM25 + RAG).

    Uses both keyword matching and semantic search for best results.
    Searches across sessions, decisions, errors, and file changes.

    Examples:
        kagura coding search --project kagura-ai --query "authentication"
        kagura coding search --query "issue-502"  # Finds exact matches
        kagura coding search --query "memory leak fix" --type error
    """
    console = Console()

    # Use environment variable defaults
    project = _check_project_required(project, console)
    user = user or _get_default_user()
    if not project:
        return

    try:
        from kagura.core.memory.coding_memory import CodingMemoryManager

        coding_mem = CodingMemoryManager(
            user_id=user, project_id=project, enable_rag=True
        )

        # Use hybrid search (BM25 + RAG) for best results
        try:
            results = coding_mem.recall_hybrid(
                query=query,
                top_k=limit * 2,  # Get more for filtering
                scope="persistent",  # Search persistent memory only
                enable_rerank=True,  # Use reranking if available
            )
        except Exception as e:
            # Fallback to RAG only if hybrid fails
            console.print(
                f"[yellow]Hybrid search unavailable ({e}), using RAG only[/yellow]"
            )
            if not coding_mem.persistent_rag:
                msg = "RAG not enabled. Install with: uv sync --all-extras"
                console.print(f"[yellow]{msg}[/yellow]")
                return

            results = coding_mem.persistent_rag.recall(
                query=query,
                user_id=user,
                top_k=limit * 2,
                agent_name=coding_mem.agent_name,
            )

        # Filter by type
        if search_type != "all":
            # Map plural to singular for metadata type matching
            plural_to_singular = {
                "sessions": "session",
                "decisions": "decision",
                "errors": "error",
                "changes": "change",
            }
            singular_type = plural_to_singular.get(search_type, search_type)
            type_prefix = f"project:{project}:{search_type}:"
            results = [
                r
                for r in results
                if r.get("metadata", {}).get("type") == singular_type
                or r.get("id", "").startswith(type_prefix)
            ]

        # Filter by project
        results = [
            r for r in results if r.get("metadata", {}).get("project_id") == project
        ]

        results = results[:limit]

        if not results:
            console.print(f"[yellow]No results found for '{query}'[/yellow]")
            return

        # Display results
        table = Table(title=f"Search Results: '{query}'", show_header=True)
        table.add_column("Type", style="cyan", width=12)
        table.add_column("Content", style="white", width=60)
        table.add_column("Score", justify="right", width=8)

        for result in results:
            metadata = result.get("metadata", {})
            result_type = metadata.get("type", "unknown")
            # RAG uses 'content' key, not 'value'
            content = str(result.get("content", result.get("value", "")))[:60]
            # Hybrid search uses rrf_score, RAG uses distance
            score = result.get(
                "rrf_score", result.get("distance", result.get("score", 0))
            )

            table.add_row(result_type, content, f"{score:.3f}")

        console.print(table)
        console.print(f"\n[dim]Found {len(results)} results[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


def _parse_time_filter(since: str) -> datetime:
    """Parse time filter string.

    Args:
        since: Time string (e.g., '7d', '30d', '2024-11-01')

    Returns:
        Datetime object
    """
    if since.endswith("d"):
        # Days ago
        days = int(since[:-1])
        return datetime.now(timezone.utc) - timedelta(days=days)
    elif since.endswith("h"):
        # Hours ago
        hours = int(since[:-1])
        return datetime.now(timezone.utc) - timedelta(hours=hours)
    else:
        # ISO date
        return datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
