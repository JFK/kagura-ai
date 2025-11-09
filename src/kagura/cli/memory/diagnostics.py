"""Memory diagnostics and indexing commands.

Provides commands for building RAG indexes and running health checks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

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


@click.command(name="index")
@click.option(
    "--user-id",
    default=None,
    help="Index specific user only (default: all users)",
)
@click.option(
    "--agent-name",
    default=None,
    help="Index specific agent only (default: all agents)",
)
@click.option(
    "--rebuild",
    is_flag=True,
    help="Rebuild index from scratch (clear existing vectors)",
)
def index(
    user_id: str | None,
    agent_name: str | None,
    rebuild: bool,
) -> None:
    """Build RAG vector index from existing memories.

    Reads memories from persistent storage and creates vector embeddings
    for semantic search. Run this after:
    - Installing RAG dependencies
    - Importing memories from backup
    - Adding many new memories manually

    Examples:
        # Index all memories
        kagura memory index

        # Index specific user
        kagura memory index --user-id kiyota

        # Rebuild index from scratch
        kagura memory index --rebuild

    Notes:
        - Requires chromadb and sentence-transformers
        - May take several minutes for large databases
        - Existing vectors will be skipped unless --rebuild is used
    """
    from kagura.core.memory import MemoryManager

    console.print("\n[cyan]Memory Index Builder[/cyan]")
    console.print()

    # Check dependencies
    try:
        import chromadb  # type: ignore # noqa: F401
        import sentence_transformers  # type: ignore # noqa: F401
    except ImportError as e:
        console.print(f"[red]✗ Missing dependency: {e}[/red]")
        console.print("\nInstall with: pip install chromadb sentence-transformers")
        raise click.Abort()

    if rebuild:
        console.print(
            "[yellow]⚠️  Rebuilding index (existing vectors will be cleared)[/yellow]"
        )
        console.print()

    try:
        # Get all user_ids if not specified
        if user_id is None:
            from kagura.utils import MemoryDatabaseQuery

            user_ids = MemoryDatabaseQuery.list_users()

            if not user_ids:
                console.print("[yellow]No memories found to index[/yellow]")
                return
        else:
            user_ids = [user_id]

        # Collect memories from all users
        all_memories = []
        for uid in user_ids:
            manager = MemoryManager(
                user_id=uid,
                agent_name=agent_name or "indexer",
                enable_rag=True,
            )

            memories = manager.persistent.fetch_all(
                user_id=uid,
                agent_name=agent_name,
                limit=100000,
            )
            all_memories.extend(memories)

        if not all_memories:
            console.print("[yellow]No memories found to index[/yellow]")
            return

        console.print(
            f"Found {len(all_memories)} memories across {len(user_ids)} user(s) to index"
        )
        memories = all_memories

        # Use first user's manager for indexing
        manager = MemoryManager(
            user_id=user_ids[0],
            agent_name=agent_name or "indexer",
            enable_rag=True,
        )
        console.print()

        if rebuild and manager.persistent_rag:
            console.print("Clearing existing index...")
            # Clear existing collection
            try:
                manager.persistent_rag.collection.delete()
            except Exception:  # Ignore errors - operation is non-critical
                pass

        # Index memories with progress bar
        indexed_count = 0
        skipped_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Indexing {len(memories)} memories...",
                total=len(memories),
            )

            for mem in memories:
                try:
                    content = f"{mem['key']}: {mem['value']}"
                    metadata = mem.get("metadata", {})

                    # Store in persistent RAG (not working memory)
                    if manager.persistent_rag:
                        manager.persistent_rag.store(
                            content=content,
                            metadata=metadata or {},
                            user_id=user_id or "system",
                        )
                        indexed_count += 1
                    else:
                        skipped_count += 1

                except Exception:  # Skip duplicates or malformed data
                    # Store operation can fail for duplicate IDs or invalid content
                    skipped_count += 1

                progress.update(task, advance=1)

        console.print()
        console.print("[green]✓ Indexing complete![/green]")
        console.print()
        console.print(f"  Indexed: {indexed_count}")
        if skipped_count > 0:
            console.print(f"  Skipped: {skipped_count} (duplicates or errors)")
        console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Indexing failed: {e}[/red]")
        raise click.Abort()


@click.command(name="doctor")
@click.option(
    "--user-id",
    default=None,
    help="Check specific user (default: system-wide)",
)
def doctor(user_id: str | None) -> None:
    """Run memory system health check.

    Checks:
    - Database status and size
    - RAG availability and vector count
    - Reranking model status
    - Memory counts by scope

    Examples:
        # System-wide check
        kagura memory doctor

        # Check specific user
        kagura memory doctor --user-id kiyota
    """
    from kagura.config.paths import get_data_dir

    console.print("\n")
    console.print(
        Panel(
            "[bold]Memory System Health Check[/]\n"
            "Checking database, RAG, and reranking status...",
            style="blue",
        )
    )
    console.print()

    # Database check
    console.print("[bold cyan]1. Database Status[/]")
    db_path = get_data_dir() / "memory.db"

    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024**2)
        console.print(f"   [green]✓[/] Database exists: {db_path}")
        console.print(f"   [green]✓[/] Size: {size_mb:.2f} MB")
    else:
        console.print(f"   [yellow]⊘[/] Database not initialized: {db_path}")

    console.print()

    # Memory counts
    console.print("[bold cyan]2. Memory Counts[/]")

    # Initialize variables with safe defaults
    manager = None
    persistent_count = 0

    try:
        # Use lightweight config for fast CLI startup (Issue #548, #527)
        manager = _get_lightweight_memory_manager(
            user_id=user_id or "system",
            agent_name="doctor",
            enable_rag=True,
        )

        # Count persistent memories
        if user_id:
            persistent_count = manager.persistent.count(user_id=user_id)
        else:
            persistent_count = manager.persistent.count()

        console.print(f"   [green]✓[/] Persistent memories: {persistent_count}")

        # Count working memories
        working_count = len(manager.working._data)
        console.print(f"   [green]✓[/] Working memories: {working_count}")

    except Exception as e:
        console.print(f"   [red]✗[/] Error: {e}")
        console.print("   [dim]Continuing with partial diagnostics...[/dim]")

    console.print()

    # RAG status
    console.print("[bold cyan]3. RAG Status[/]")

    try:
        import chromadb

        rag_count = 0

        # Check multiple possible vector DB locations (like mcp doctor does)
        from kagura.config.paths import get_cache_dir, get_data_dir

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
                        rag_count += col.count()
                except Exception:
                    # Skip if collection read fails
                    pass

        console.print("   [green]✓[/] RAG enabled")
        console.print(f"   [green]✓[/] Vectors indexed: {rag_count}")

        if rag_count == 0 and persistent_count > 0:
            console.print(
                f"   [yellow]⚠[/] Index empty but {persistent_count} memories exist"
            )
            console.print("   [dim]Run 'kagura memory index' to build index[/dim]")

    except ImportError:
        console.print("   [red]✗[/] RAG not available")
        console.print(
            "   [dim]Install: pip install chromadb sentence-transformers[/dim]"
        )
    except Exception as e:
        console.print(f"   [red]✗[/] Error: {e}")

    console.print()

    # Reranking status
    console.print("[bold cyan]4. Reranking Status[/]")

    from kagura.config.project import get_reranking_enabled

    reranking_enabled = get_reranking_enabled()

    # Check sentence-transformers installation and model availability
    try:
        import sentence_transformers

        st_version = sentence_transformers.__version__
        console.print(f"   [green]✓[/] sentence-transformers v{st_version}")

        # Check if reranking model is cached
        from kagura.config.memory_config import MemorySystemConfig
        from kagura.core.memory.reranker import is_reranker_available

        config = MemorySystemConfig()
        model = config.rerank.model

        if is_reranker_available(model):
            console.print(f"   [green]✓[/] Model cached: {model}")

            if reranking_enabled:
                console.print("   [green]✓[/] Reranking enabled")
            else:
                console.print("   [yellow]⊘[/] Not enabled (but ready)")
                console.print("   [dim]Set: export KAGURA_ENABLE_RERANKING=true[/dim]")
        else:
            console.print(f"   [yellow]⊘[/] Model not cached: {model}")
            console.print("   [dim]Install: kagura mcp install-reranking[/dim]")

            if reranking_enabled:
                console.print(
                    "   [red]✗[/] Enabled but model missing (will fail!)[/red]"
                )

    except ImportError:
        console.print("   [red]✗[/] sentence-transformers not installed")
        console.print("   [dim]Install: pip install sentence-transformers[/dim]")

        if reranking_enabled:
            console.print(
                "   [red]✗[/] Enabled but dependencies missing (will fail!)[/red]"
            )

    console.print()

    # Summary
    console.print(
        Panel(
            "[bold]Health Check Complete[/]\n\n"
            "For more details, run:\n"
            "  • kagura doctor - Comprehensive system check\n"
            "  • kagura memory index - Build RAG index\n"
            "  • kagura memory setup - Download models",
            style="blue",
        )
    )
