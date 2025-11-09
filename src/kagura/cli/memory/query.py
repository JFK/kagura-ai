"""Memory query and search commands.

Provides commands for listing, searching and viewing memory statistics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.table import Table

from kagura.config.project import get_default_user as _get_default_user_impl

if TYPE_CHECKING:
    from kagura.core.memory import MemoryManager

console = Console()


def _get_default_user() -> str:
    """Get default user with fallback.

    Returns:
        Default user ID (auto-detected or 'kiyota')
    """
    return _get_default_user_impl() or "kiyota"


def _get_lightweight_memory_manager(
    user_id: str,
    agent_name: str,
    enable_rag: bool = True,
) -> MemoryManager:
    """Create lightweight MemoryManager for fast CLI startup.

    Disables slow components not needed for CLI queries:
    - Reranker (~6.5s saved) - Issue #548
    - RecallScorer (~1s saved)
    - Graph memory
    - Compression

    Args:
        user_id: User identifier
        agent_name: Agent name
        enable_rag: Enable RAG for semantic search (default: True)

    Returns:
        MemoryManager with lightweight config optimized for CLI

    Related: Issue #548, #527 - CLI performance optimization
    """
    from kagura.config.memory_config import MemorySystemConfig, RerankConfig
    from kagura.core.memory import MemoryManager

    # Lightweight config for fast CLI startup
    config = MemorySystemConfig(
        enable_access_tracking=False,  # Disable RecallScorer (~1s saved)
        rerank=RerankConfig(enabled=False),  # Disable reranker (~6.5s saved)
    )

    return MemoryManager(
        user_id=user_id,
        agent_name=agent_name,
        enable_rag=enable_rag,  # Keep RAG for semantic search
        enable_compression=False,  # Not needed for CLI
        enable_graph=False,  # Not needed for CLI queries
        memory_config=config,  # Pass lightweight config
    )


@click.command(name="list")
@click.option(
    "--user-id",
    default=None,
    help="Filter by user ID (default: all users)",
)
@click.option(
    "--agent-name",
    default=None,
    help="Filter by agent name (default: all agents)",
)
@click.option(
    "--scope",
    type=click.Choice(["working", "persistent", "all"]),
    default="all",
    help="Memory scope to list",
)
@click.option(
    "--limit",
    default=20,
    type=int,
    help="Maximum number of memories to show (default: 20)",
)
def list_memories(
    user_id: str | None,
    agent_name: str | None,
    scope: str,
    limit: int,
) -> None:
    """List stored memories.

    Shows keys, values (truncated), and metadata for stored memories.

    Examples:
        # List all memories
        kagura memory list

        # List for specific user
        kagura memory list --user-id kiyota

        # List persistent memories only
        kagura memory list --scope persistent --limit 50
    """
    console.print("\n[cyan]Memory List[/cyan]")
    console.print()

    # Auto-detect user if not provided
    user_id = user_id or _get_default_user()

    try:
        # Use lightweight config for fast CLI startup (Issue #548, #527)
        manager = _get_lightweight_memory_manager(
            user_id=user_id,
            agent_name=agent_name or "global",
            enable_rag=False,  # List doesn't need RAG
        )

        # Get memories based on scope
        memories = []

        if scope in ["working", "all"]:
            # Working memory
            for key, value in manager.working._data.items():
                memories.append(
                    {
                        "scope": "working",
                        "key": key,
                        "value": str(value)[:100],
                        "user": user_id or "system",
                    }
                )

        if scope in ["persistent", "all"]:
            # Persistent memory
            persistent_memories = manager.persistent.search(
                query="%",
                user_id=user_id or "system",
                agent_name=agent_name,
                limit=limit,
            )

            for mem in persistent_memories:
                memories.append(
                    {
                        "scope": "persistent",
                        "key": mem.get("key", ""),
                        "value": str(mem.get("value", ""))[:100],
                        "user": mem.get("user_id", ""),
                    }
                )

        if not memories:
            console.print("[yellow]No memories found[/yellow]")
            return

        # Show only first `limit` memories
        memories = memories[:limit]

        # Display table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Scope", style="cyan")
        table.add_column("Key", style="white")
        table.add_column("Value (truncated)", style="dim")
        table.add_column("User", style="green")

        for mem in memories:
            table.add_row(
                mem["scope"],
                mem["key"],
                mem["value"],
                mem["user"],
            )

        console.print(table)
        console.print(
            f"\n[dim]Showing {len(memories)} of {len(memories)} memories[/dim]"
        )
        console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Failed to list memories: {e}[/red]")
        raise click.Abort()


@click.command(name="search")
@click.argument("query")
@click.option(
    "--user-id",
    default=None,
    help="Filter by user ID (default: system)",
)
@click.option(
    "--agent-name",
    default=None,
    help="Filter by agent name",
)
@click.option(
    "--top-k",
    default=10,
    type=int,
    help="Number of results to return (default: 10)",
)
def search_memory(
    query: str,
    user_id: str | None,
    agent_name: str | None,
    top_k: int,
) -> None:
    """Search memories semantically.

    Uses RAG (semantic search) to find relevant memories.

    Examples:
        # Search all memories
        kagura memory search "authentication decision"

        # Search for specific user
        kagura memory search "bug fix" --user-id kiyota --top-k 5
    """
    console.print(f'\n[cyan]Searching for: "{query}"[/cyan]')
    console.print()

    try:
        # Use lightweight config for fast CLI startup (Issue #548, #527)
        manager = _get_lightweight_memory_manager(
            user_id=user_id or "system",
            agent_name=agent_name or "global",
            enable_rag=True,
        )

        # Perform semantic search (use hybrid if available)
        if manager.persistent_rag and manager.lexical_searcher:
            # Use hybrid search (BM25 + RAG + reranking)
            results = manager.recall_hybrid(
                query=query,
                top_k=top_k,
                scope="persistent",
            )
        elif manager.persistent_rag:
            # Fallback to RAG-only search
            results = manager.recall_semantic(
                query=query,
                top_k=top_k,
                scope="persistent",
            )
        else:
            console.print("[red]✗ RAG not available[/red]")
            console.print(
                "[dim]Install: pip install chromadb sentence-transformers[/dim]"
            )
            return

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        # Display results
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Content", style="white")
        table.add_column("Score", style="green", width=8)

        # Handle different result formats
        for i, result in enumerate(results, 1):
            if isinstance(result, dict):
                # Get content value (handle both string and dict)
                content_val = result.get("value", result.get("content", ""))
                if isinstance(content_val, str):
                    content = content_val[:200]
                else:
                    # Handle dict or other types
                    content = str(content_val)[:200]

                # Get score (try different field names)
                score = result.get(
                    "score",
                    result.get(
                        "similarity",
                        result.get("rrf_score", result.get("distance", 0.0)),
                    ),
                )
            else:
                content = str(result)[:200]
                score = 0.0

            table.add_row(
                str(i),
                content,
                f"{score:.3f}",
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(results)} results[/dim]")
        search_type = "Hybrid (BM25 + RAG)" if manager.lexical_searcher else "RAG only"
        console.print(f"[dim]Search type: {search_type}[/dim]")
        console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Search failed: {e}[/red]")
        raise click.Abort()


@click.command(name="stats")
@click.option(
    "--user-id",
    default=None,
    help="Filter by user ID (default: all users)",
)
@click.option(
    "--breakdown-by",
    default="scope",
    type=click.Choice(["scope", "user", "agent", "all"]),
    help="How to break down statistics (default: scope)",
)
def stats(
    user_id: str | None,
    breakdown_by: str,
) -> None:
    """Show memory statistics.

    Displays counts and sizes for different memory types.

    Examples:
        # System-wide stats
        kagura memory stats

        # Stats by user
        kagura memory stats --breakdown-by user

        # Stats for specific user
        kagura memory stats --user-id kiyota --breakdown-by scope
    """
    from kagura.config.paths import get_data_dir

    console.print("\n[cyan]Memory Statistics[/cyan]")
    console.print()

    try:
        # Get database info first (before creating MemoryManager)
        db_path = get_data_dir() / "memory.db"
        db_size_mb = 0.0
        if db_path.exists():
            db_size_mb = db_path.stat().st_size / (1024**2)

        # Scan all ChromaDB locations for RAG counts (before creating MemoryManager to avoid locks)
        rag_count = 0
        rag_by_collection = {}

        try:
            import chromadb

            from kagura.config.paths import get_cache_dir

            vector_db_paths = [
                get_cache_dir() / "chromadb",  # Default CLI location
                get_data_dir() / "sessions" / "memory" / "vector_db",
                get_data_dir() / "api" / "default_user" / "vector_db",
                get_data_dir() / "vector_db",  # Legacy location
            ]

            for vdb_path in vector_db_paths:
                if vdb_path.exists():
                    try:
                        client = chromadb.PersistentClient(path=str(vdb_path))
                        for col in client.list_collections():
                            count = col.count()
                            if count > 0:  # Only count non-empty collections
                                rag_count += count
                                # Aggregate counts if collection name already exists
                                rag_by_collection[col.name] = (
                                    rag_by_collection.get(col.name, 0) + count
                                )
                    except Exception:
                        pass
        except ImportError:
            pass

        # Use lightweight config for fast CLI startup (Issue #548, #527)
        manager = _get_lightweight_memory_manager(
            user_id=user_id or "system",
            agent_name="stats",
            enable_rag=False,  # Don't enable RAG to avoid locking ChromaDB
        )

        # Count memories
        working_count = len(manager.working._data)

        if user_id:
            persistent_count = manager.persistent.count(user_id=user_id)
        else:
            persistent_count = manager.persistent.count()

        # Display main table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Segment", style="cyan")
        table.add_column("Count", style="white", justify="right")
        table.add_column("Details", style="dim")

        table.add_row("Working", str(working_count), "Temporary session data")
        table.add_row(
            "Persistent", str(persistent_count), f"SQLite DB ({db_size_mb:.2f} MB)"
        )
        table.add_row("RAG Index", str(rag_count), "Vector embeddings")

        console.print(table)
        console.print()

        # Show per-user breakdown if requested
        if breakdown_by in ["user", "all"] and not user_id:
            from kagura.utils import MemoryDatabaseQuery

            user_stats = MemoryDatabaseQuery.get_user_stats()

            if user_stats:
                console.print("[cyan]By User:[/cyan]")
                user_table = Table(show_header=True, header_style="bold magenta")
                user_table.add_column("User ID", style="cyan")
                user_table.add_column("Memories", style="white", justify="right")
                user_table.add_column("RAG Indexed", style="green", justify="right")

                for user, count in user_stats:
                    # Count RAG vectors for this user
                    user_rag = sum(
                        v
                        for k, v in rag_by_collection.items()
                        if user in k or "global" in k
                    )
                    user_table.add_row(
                        user, str(count), str(user_rag) if user_rag > 0 else "-"
                    )

                console.print(user_table)
                console.print()

        # Show RAG collections breakdown if there are any
        if rag_by_collection and breakdown_by in ["all"]:
            console.print("[cyan]RAG Collections:[/cyan]")
            rag_table = Table(show_header=True, header_style="bold magenta")
            rag_table.add_column("Collection", style="cyan")
            rag_table.add_column("Vectors", style="white", justify="right")

            for col_name, count in sorted(
                rag_by_collection.items(), key=lambda x: x[1], reverse=True
            ):
                rag_table.add_row(col_name, str(count))

            console.print(rag_table)
            console.print()

        # Show recommendations
        if persistent_count > 0 and rag_count == 0:
            console.print(
                "[yellow]⚠ Tip: Run 'kagura memory index' to enable semantic search[/yellow]"
            )
            console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Failed to get stats: {e}[/red]")
        raise click.Abort()
