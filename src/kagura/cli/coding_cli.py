"""CLI commands for Coding Memory inspection.

Provides terminal access to coding sessions, decisions, errors, and file changes
stored in Kagura's Coding Memory system.
"""

import json
from datetime import datetime, timedelta, timezone

import click
from rich.console import Console
from rich.table import Table


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
@click.option("--user", "-u", default="kiyota", help="User ID (default: kiyota)")
def projects(user: str):
    """List all projects with coding memory.

    Shows unique project names and session counts.

    Example:
        kagura coding projects
        kagura coding projects --user kiyota
    """
    console = Console()

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
@click.option("--project", "-p", required=True, help="Project ID")
@click.option("--user", "-u", default="kiyota", help="User ID (default: kiyota)")
@click.option("--limit", "-n", default=20, help="Maximum results (default: 20)")
@click.option(
    "--success",
    type=click.Choice(["true", "false", "all"]),
    default="all",
    help="Filter by success status",
)
@click.option("--since", help="Time filter (e.g., 7d, 30d, 2024-11-01)")
def sessions(project: str, user: str, limit: int, success: str, since: str | None):
    """List coding sessions for a project.

    Shows session history with descriptions, durations, and outcomes.

    Examples:
        kagura coding sessions --project kagura-ai
        kagura coding sessions --project kagura-ai --success true --limit 10
        kagura coding sessions --project kagura-ai --since 7d
    """
    console = Console()

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
                if datetime.fromisoformat(s["start_time"]) >= cutoff_time
            ]

        # Sort by start_time (newest first)
        sessions_data.sort(key=lambda s: s.get("start_time", ""), reverse=True)

        # Limit results
        sessions_data = sessions_data[:limit]

        # Display table
        table = Table(title=f"Coding Sessions: {project}", show_header=True)
        table.add_column("Session ID", style="cyan", no_wrap=True)
        table.add_column("Description", style="white", width=50)
        table.add_column("Duration", justify="right", width=10)
        table.add_column("Status", justify="center", width=8)

        for session in sessions_data:
            session_id = session["session_id"]
            description = session.get("description", "No description")[:40]
            duration = session.get("duration_minutes", 0)
            duration_str = f"{duration:.1f}m" if duration else "-"
            success_status = session.get("success")
            status_icon = (
                "✅" if success_status else ("⚠️" if success_status is False else "ℹ️")
            )

            table.add_row(session_id, description, duration_str, status_icon)

        console.print(table)
        console.print(f"\n[dim]Total: {len(sessions_data)} sessions[/dim]")
        console.print("[dim]Use: kagura coding session <SESSION_ID> for details[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


@coding.command()
@click.argument("session_id")
@click.option("--project", "-p", required=True, help="Project ID")
@click.option("--user", "-u", default="kiyota", help="User ID")
def session(session_id: str, project: str, user: str):
    """Show detailed session information.

    Example:
        kagura coding session session_abc123 --project kagura-ai
    """
    console = Console()

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

        # Display session details
        console.print(f"\n[bold]Session: {session_id}[/bold]")
        console.print(f"Project: {project}")
        console.print(f"Description: {data.get('description', 'N/A')}")
        console.print(f"Start: {data.get('start_time', 'N/A')}")
        console.print(f"End: {data.get('end_time', 'N/A')}")
        console.print(f"Duration: {data.get('duration_minutes', 0):.1f} minutes")
        console.print(f"Success: {data.get('success', 'N/A')}")

        console.print("\n[bold]Activities:[/bold]")
        console.print(f"  Files touched: {len(data.get('files_touched', []))}")
        console.print(f"  Errors encountered: {data.get('errors_encountered', 0)}")
        console.print(f"  Errors fixed: {data.get('errors_fixed', 0)}")
        console.print(f"  Decisions made: {data.get('decisions_made', 0)}")

        if data.get("tags"):
            console.print(f"\n[bold]Tags:[/bold] {', '.join(data['tags'])}")

        if data.get("summary"):
            console.print("\n[bold]Summary:[/bold]")
            console.print(data["summary"][:500])
            if len(data["summary"]) > 500:
                console.print("[dim]... (truncated)[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


@coding.command()
@click.option("--project", "-p", required=True, help="Project ID")
@click.option("--user", "-u", default="kiyota", help="User ID")
@click.option("--limit", "-n", default=10, help="Maximum results")
@click.option("--min-confidence", type=float, help="Minimum confidence (0.0-1.0)")
@click.option("--tag", help="Filter by tag")
def decisions(
    project: str, user: str, limit: int, min_confidence: float | None, tag: str | None
):
    """List design decisions for a project.

    Examples:
        kagura coding decisions --project kagura-ai
        kagura coding decisions --project kagura-ai --min-confidence 0.8
        kagura coding decisions --project kagura-ai --tag architecture
    """
    console = Console()

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
@click.option("--project", "-p", required=True, help="Project ID")
@click.option("--user", "-u", default="kiyota", help="User ID")
def decision(decision_id: str, project: str, user: str):
    """Show detailed decision information.

    Example:
        kagura coding decision decision_abc123 --project kagura-ai
    """
    console = Console()

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
@click.option("--project", "-p", required=True, help="Project ID")
@click.option("--user", "-u", default="kiyota", help="User ID")
@click.option("--limit", "-n", default=20, help="Maximum results")
@click.option("--unresolved", is_flag=True, help="Show only unresolved errors")
@click.option("--type", "error_type", help="Filter by error type (e.g., TypeError)")
def errors(
    project: str, user: str, limit: int, unresolved: bool, error_type: str | None
):
    """List errors encountered in a project.

    Examples:
        kagura coding errors --project kagura-ai
        kagura coding errors --project kagura-ai --unresolved
        kagura coding errors --project kagura-ai --type TypeError
    """
    console = Console()

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
        table.add_column("Location", style="yellow", width=30)
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
                location[:30],
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
@click.option("--project", "-p", required=True, help="Project ID")
@click.option("--user", "-u", default="kiyota", help="User ID")
def error(error_id: str, project: str, user: str):
    """Show detailed error information including solution.

    Example:
        kagura coding error error_abc123 --project kagura-ai
    """
    console = Console()

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
@click.option("--project", "-p", required=True, help="Project ID")
@click.option("--user", "-u", default="kiyota", help="User ID")
@click.option("--query", "-q", required=True, help="Search query")
@click.option(
    "--type",
    "search_type",
    type=click.Choice(["all", "session", "decision", "error", "change"]),
    default="all",
    help="Search scope",
)
@click.option("--limit", "-n", default=10, help="Maximum results")
def search(project: str, user: str, query: str, search_type: str, limit: int):
    """Search coding memory semantically.

    Searches across sessions, decisions, errors, and file changes.

    Examples:
        kagura coding search --project kagura-ai --query "authentication"
        kagura coding search --project kagura-ai --query "memory leak" --type error
    """
    console = Console()

    try:
        from kagura.core.memory.coding_memory import CodingMemoryManager

        coding_mem = CodingMemoryManager(
            user_id=user, project_id=project, enable_rag=True
        )

        if not coding_mem.persistent_rag:
            console.print(
                "[yellow]RAG not enabled. Install with: uv sync --all-extras[/yellow]"
            )
            return

        # Search using RAG
        results = coding_mem.persistent_rag.recall(
            query=query,
            user_id=user,
            top_k=limit * 2,  # Get more for filtering
            agent_name=coding_mem.agent_name,
        )

        # Filter by type
        if search_type != "all":
            type_prefix = f"project:{project}:{search_type}:"
            results = [
                r
                for r in results
                if r.get("metadata", {}).get("type") == search_type.rstrip("s")
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
            score = result.get("distance", result.get("score", 0))

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
