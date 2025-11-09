"""Coding utility commands and helpers."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from kagura.config.project import (
    detect_git_repo_name,
    load_pyproject_config,
)
from kagura.config.project import (
    get_default_project as _get_default_project_impl,
)
from kagura.config.project import (
    get_default_user as _get_default_user_impl,
)


def _get_lightweight_coding_memory(user_id: str, project_id: str):
    """Create CodingMemoryManager with CLI-optimized lightweight config.

    Disables expensive components not needed for CLI queries:
    - Access tracking (RecallScorer): Not used in CLI queries
    - Reranking: Not used in CLI list/search commands
    - Compression: Not needed for CLI
    - Graph: Not used in basic CLI commands

    This reduces initialization time from 8+ seconds to ~2-3 seconds.

    Args:
        user_id: User identifier
        project_id: Project identifier

    Returns:
        CodingMemoryManager with lightweight config

    Related: Issue #548 - CLI performance optimization
    """
    from kagura.config.memory_config import MemorySystemConfig, RerankConfig
    from kagura.core.memory.coding_memory import CodingMemoryManager

    # Lightweight config for fast CLI startup
    config = MemorySystemConfig(
        enable_access_tracking=False,  # Disable RecallScorer (~1s saved)
        # Disable reranker (~6.5s saved, Issue #548)
        rerank=RerankConfig(enabled=False),
    )

    return CodingMemoryManager(
        user_id=user_id,
        project_id=project_id,
        enable_rag=False,  # Already disabled in CLI
        enable_compression=False,  # Not needed for CLI
        enable_graph=False,  # Not needed for CLI queries
        memory_config=config,  # Pass lightweight config
    )


def _get_default_user() -> str:
    """Get default user with fallback.

    Returns:
        Default user ID (auto-detected or 'kiyota')
    """
    return _get_default_user_impl() or "kiyota"


def _get_default_project() -> str | None:
    """Get default project from config.

    Returns:
        Project ID or None
    """
    return _get_default_project_impl()


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
            "[red]Error: No project detected and $KAGURA_DEFAULT_PROJECT not set[/red]"
        )
        console.print("[yellow]💡 Tip: Auto-detection works when you:[/yellow]")
        console.print("[dim]  1. Run in a git repository (uses repo name)[/dim]")
        console.print(
            '[dim]  2. Add to pyproject.toml: [tool.kagura] project = "your-project"[/dim]'
        )
        console.print(
            "[dim]  3. Set environment: export KAGURA_DEFAULT_PROJECT=your-project[/dim]"
        )
        console.print("[dim]  4. Use flag: --project your-project[/dim]")
    return proj


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
@click.option("--query", "-q", required=True, help="Search query")
@click.option(
    "--type",
    "search_type",
    type=click.Choice(["all", "session", "decision", "error", "change"]),
    default="all",
    help="Search scope",
)
@click.option("--limit", "-n", default=10, help="Maximum results")
def search_command(
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
    from rich.table import Table

    from kagura.core.memory.coding_memory import CodingMemoryManager

    console = Console()

    # Use environment variable defaults
    project = _check_project_required(project, console)
    user = user or _get_default_user()
    if not project:
        return

    try:
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


@click.command()
def doctor_command() -> None:
    """Check Coding Memory configuration and auto-detection.

    Diagnoses project/user detection and shows Coding Memory statistics.

    Example:
        kagura coding doctor
    """
    console = Console()
    console.print("\n")
    console.print(
        Panel(
            "[bold]Coding Memory Configuration Check 🔧[/]\n"
            "Checking auto-detection and statistics...",
            style="blue",
        )
    )
    console.print()

    # 1. Auto-detection Status
    console.print("[bold cyan]1. Auto-detection Status[/]")

    # Project detection
    detected_project = _get_default_project()
    env_project = os.getenv("KAGURA_DEFAULT_PROJECT")
    pyproject_config = load_pyproject_config()
    git_repo = detect_git_repo_name()

    if detected_project:
        console.print(f"   [green]✓[/] Project: [bold]{detected_project}[/bold]")

        # Show source
        if env_project:
            console.print(
                "     [dim]└─ Source: Environment variable ($KAGURA_DEFAULT_PROJECT)[/dim]"
            )
        elif pyproject_config.get("project"):
            console.print("     [dim]└─ Source: pyproject.toml [tool.kagura][/dim]")
        elif git_repo:
            console.print("     [dim]└─ Source: Git repository auto-detection[/dim]")
    else:
        console.print("   [red]✗[/] Project: Not detected")
        console.print(
            "     [yellow]💡 Tip: Run in a git repo or add to pyproject.toml[/yellow]"
        )

    # User detection
    detected_user = _get_default_user()
    env_user = os.getenv("KAGURA_DEFAULT_USER")
    git_user = None
    try:
        import subprocess

        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )
        if result.returncode == 0:
            git_user = result.stdout.strip()
    except Exception:  # Git not available or config not set
        pass

    console.print(f"   [green]✓[/] User: [bold]{detected_user}[/bold]")
    if env_user:
        console.print(
            "     [dim]└─ Source: Environment variable ($KAGURA_DEFAULT_USER)[/dim]"
        )
    elif pyproject_config.get("user"):
        console.print("     [dim]└─ Source: pyproject.toml [tool.kagura][/dim]")
    elif git_user:
        console.print("     [dim]└─ Source: Git user.name config[/dim]")
    else:
        console.print("     [dim]└─ Source: Default (kiyota)[/dim]")

    console.print()

    # 2. Configuration Sources
    console.print("[bold cyan]2. Configuration Sources[/]")

    # Environment variables (reuse already-retrieved values)
    if env_project or env_user:
        console.print("   [green]✓[/] Environment Variables:")
        if env_project:
            console.print(f"     • KAGURA_DEFAULT_PROJECT={env_project}")
        if env_user:
            console.print(f"     • KAGURA_DEFAULT_USER={env_user}")
    else:
        console.print("   [dim]⊘[/] Environment Variables: Not set")

    # pyproject.toml
    if pyproject_config:
        console.print("   [green]✓[/] pyproject.toml [tool.kagura]:")
        for key, value in pyproject_config.items():
            console.print(f"     • {key} = {value}")
    else:
        pyproject_path = Path.cwd() / "pyproject.toml"
        if pyproject_path.exists():
            console.print("   [dim]⊘[/] pyproject.toml: No [tool.kagura] section")
        else:
            console.print("   [dim]⊘[/] pyproject.toml: Not found")

    # Git repository
    if git_repo:
        console.print(f"   [green]✓[/] Git Repository: {git_repo}")
        try:
            import subprocess

            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
            if result.returncode == 0:
                console.print(f"     [dim]└─ Remote: {result.stdout.strip()}[/dim]")
        except Exception:  # Git not available
            pass
    else:
        console.print("   [dim]⊘[/] Git Repository: Not detected")

    console.print()

    # 3. Coding Memory Statistics
    if not detected_project:
        console.print("[bold cyan]3. Coding Memory Statistics[/]")
        console.print("   [yellow]⊘[/] Cannot check: No project detected")
        console.print()
        return

    console.print("[bold cyan]3. Coding Memory Statistics[/]")

    from kagura.core.memory.coding_memory import CodingMemoryManager

    try:
        # Use CodingMemoryManager with lightweight config (same as sessions command)
        coding_mem = CodingMemoryManager(
            user_id=detected_user,
            project_id=detected_project,
            enable_rag=False,  # Fast startup
            enable_graph=False,
            enable_compression=False,
        )

        # Search for all project data using LIKE pattern (consistent with sessions command)
        pattern = f"project:{detected_project}:"
        results = coding_mem.persistent.search(
            query=pattern,
            user_id=detected_user,
            agent_name=None,  # Search across all agent names
            limit=1000,
        )

        # Count different types by key pattern
        session_count = sum(1 for s in results if ":session:" in s.get("key", ""))
        error_count = sum(1 for s in results if ":error:" in s.get("key", ""))
        decision_count = sum(1 for s in results if ":decision:" in s.get("key", ""))
        change_count = sum(1 for s in results if ":file_change:" in s.get("key", ""))

        console.print(f"   [green]✓[/] Sessions: {session_count}")
        console.print(f"   [green]✓[/] Errors recorded: {error_count}")
        console.print(f"   [green]✓[/] Decisions: {decision_count}")
        console.print(f"   [green]✓[/] File changes: {change_count}")

    except Exception as e:
        console.print(f"   [yellow]⊘[/] Could not load: {e}")

    console.print()

    # 4. Recommendations
    console.print("[bold cyan]4. Recommendations[/]")

    recommendations = []

    if not pyproject_config and Path.cwd().joinpath("pyproject.toml").exists():
        recommendations.append(
            "Add [tool.kagura] to pyproject.toml for explicit project/user config"
        )

    if not git_repo and not pyproject_config.get("project"):
        recommendations.append(
            "Initialize git repository or set project explicitly for auto-detection"
        )

    if recommendations:
        for rec in recommendations:
            console.print(f"   [yellow]💡[/] {rec}")
    else:
        console.print("   [green]✓[/] Configuration looks good!")

    console.print()

    # Summary
    console.print(
        Panel(
            f"[bold]Configuration Check Complete[/]\n\n"
            f"Project: [cyan]{detected_project or 'Not detected'}[/cyan]\n"
            f"User: [cyan]{detected_user}[/cyan]",
            style="green" if detected_project else "yellow",
        )
    )
    console.print()
