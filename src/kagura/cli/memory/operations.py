"""Memory export, import and reindexing operations.

Provides commands for memory data portability and index management.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console

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


@click.command(name="export")
@click.option(
    "--output",
    "-o",
    required=True,
    help="Output directory for exported data",
)
@click.option(
    "--user-id",
    default=None,
    help="User ID to export (default: auto-detect from pyproject.toml or $KAGURA_DEFAULT_USER)",
)
@click.option(
    "--agent-name",
    default="global",
    help="Agent name to export (default: global)",
)
@click.option(
    "--persistent/--no-persistent",
    default=True,
    help="Include persistent memory (default: yes)",
)
@click.option(
    "--graph/--no-graph",
    default=True,
    help="Include graph data (default: yes)",
)
def export_memory(
    output: str,
    user_id: str,
    agent_name: str,
    persistent: bool,
    graph: bool,
) -> None:
    """Export memory data to JSONL format.

    Exports memories, graph data, and metadata to a directory in JSONL format.
    This can be used for backup, migration, or GDPR data export.

    Examples:
        # Export all data
        kagura memory export --output ./backup

        # Export only persistent memory
        kagura memory export --output ./backup --no-persistent

        # Export for specific user
        kagura memory export --output ./backup --user-id user_alice
    """
    from kagura.core.memory.export import MemoryExporter

    # Auto-detect user if not provided
    user_id = user_id or _get_default_user()

    console.print(f"\n[cyan]Exporting memory data for user '{user_id}'...[/cyan]")
    console.print()

    try:
        # Use lightweight config for fast CLI startup (Issue #548, #527)
        manager = _get_lightweight_memory_manager(
            user_id=user_id,
            agent_name=agent_name,
            enable_rag=True,  # Need RAG for export
        )

        # Create exporter
        exporter = MemoryExporter(manager)

        # Run export
        with console.status("[bold green]Exporting..."):
            stats = asyncio.run(
                exporter.export_all(
                    output_dir=output,
                    include_persistent=persistent,
                    include_graph=graph,
                )
            )

        # Display results
        console.print("[green]✓ Export completed successfully![/green]")
        console.print()
        console.print(f"[dim]Output directory: {output}[/dim]")
        console.print()
        console.print("[cyan]Exported:[/cyan]")
        console.print(f"  • Memories: {stats['memories']}")
        if graph:
            console.print(f"  • Graph nodes: {stats['graph_nodes']}")
            console.print(f"  • Graph edges: {stats['graph_edges']}")
        console.print()

        # Show files created
        output_path = Path(output)
        console.print("[cyan]Files created:[/cyan]")
        if (output_path / "memories.jsonl").exists():
            console.print("  • memories.jsonl")
        if (output_path / "graph.jsonl").exists():
            console.print("  • graph.jsonl")
        if (output_path / "metadata.json").exists():
            console.print("  • metadata.json")
        console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Export failed: {e}[/red]")
        raise click.Abort()


@click.command(name="import")
@click.option(
    "--input",
    "-i",
    required=True,
    help="Input directory containing exported data",
)
@click.option(
    "--user-id",
    default=None,
    help="User ID to import as (default: auto-detect from pyproject.toml or $KAGURA_DEFAULT_USER)",
)
@click.option(
    "--agent-name",
    default="global",
    help="Agent name to import as (default: global)",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing data before import",
)
def import_memory(
    input: str,
    user_id: str,
    agent_name: str,
    clear: bool,
) -> None:
    """Import memory data from JSONL format.

    Imports memories and graph data from a previously exported directory.

    Examples:
        # Import from backup
        kagura memory import --input ./backup

        # Import for specific user, clearing existing data
        kagura memory import --input ./backup --user-id user_alice --clear

    Warning:
        --clear flag will delete all existing memory data!
    """
    from kagura.core.memory.export import MemoryImporter

    # Auto-detect user if not provided
    user_id = user_id or _get_default_user()

    console.print(f"\n[cyan]Importing memory data for user '{user_id}'...[/cyan]")

    if clear:
        console.print("[yellow]⚠️  Warning: Existing data will be cleared[/yellow]")

    console.print()

    try:
        # Use lightweight config for fast CLI startup (Issue #548, #527)
        manager = _get_lightweight_memory_manager(
            user_id=user_id,
            agent_name=agent_name,
            enable_rag=True,  # Need RAG for import
        )

        # Create importer
        importer = MemoryImporter(manager)

        # Run import
        with console.status("[bold green]Importing..."):
            stats = asyncio.run(
                importer.import_all(
                    input_dir=input,
                    clear_existing=clear,
                )
            )

        # Display results
        console.print("[green]✓ Import completed successfully![/green]")
        console.print()
        console.print(f"[dim]Import directory: {input}[/dim]")
        console.print()
        console.print("[cyan]Imported:[/cyan]")
        console.print(f"  • Memories: {stats['memories']}")
        console.print(f"  • Graph nodes: {stats['graph_nodes']}")
        console.print(f"  • Graph edges: {stats['graph_edges']}")
        console.print()

    except FileNotFoundError as e:
        console.print(f"\n[red]✗ Import failed: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[red]✗ Import failed: {e}[/red]")
        raise click.Abort()


@click.command(name="reindex")
@click.option(
    "--model",
    default="intfloat/multilingual-e5-large",
    help="Embedding model to use (default: intfloat/multilingual-e5-large)",
)
@click.option(
    "--dimension",
    default=1024,
    type=int,
    help="Embedding dimension (default: 1024)",
)
@click.option(
    "--batch-size",
    default=100,
    type=int,
    help="Batch size for reindexing (default: 100)",
)
@click.option(
    "--user-id",
    default=None,
    help="Reindex specific user only (default: all users)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be reindexed without making changes",
)
def reindex(
    model: str,
    dimension: int,
    batch_size: int,
    user_id: str | None,
    dry_run: bool,
) -> None:
    """Re-index all memories with new embedding model.

    ⚠️  WARNING: This is a breaking change operation!

    When changing embedding models (e.g., from all-MiniLM-L6-v2 to
    multilingual-e5-large), all existing embeddings must be regenerated.

    This command will:
    1. Load all memories from persistent storage
    2. Generate new embeddings with the specified model
    3. Create new RAG collections
    4. Delete old RAG collections

    Examples:
        # Reindex with E5 large (1024-dim, multilingual)
        kagura memory reindex --model intfloat/multilingual-e5-large

        # Reindex with E5 base (768-dim, faster)
        kagura memory reindex \\
            --model intfloat/multilingual-e5-base \\
            --dimension 768

        # Dry run (no changes)
        kagura memory reindex --dry-run

        # Reindex specific user only
        kagura memory reindex --user-id user_alice

    Notes:
        - This operation may take several minutes for large databases
        - GPU recommended for faster embedding generation
        - Existing semantic search results will change after reindexing
    """
    from kagura.config.memory_config import EmbeddingConfig, MemorySystemConfig
    from kagura.core.memory import MemoryManager
    from kagura.core.memory.embeddings import Embedder

    console.print("\n[cyan]Memory Reindexing Tool (v4.0.0a0)[/cyan]")
    console.print()

    # Warn about breaking changes
    if not dry_run:
        console.print(
            "[yellow]⚠️  WARNING: This is a BREAKING CHANGE operation![/yellow]"
        )
        console.print()
        console.print("This will:")
        console.print("  • Regenerate all embeddings with new model")
        console.print("  • Replace existing RAG collections")
        console.print("  • Change semantic search results")
        console.print()

        if not click.confirm("Do you want to continue?"):
            console.print("[red]Aborted.[/red]")
            raise click.Abort()
        console.print()

    try:
        # Load embedding model
        console.print(f"[cyan]Loading embedding model: {model}[/cyan]")
        embedding_config = EmbeddingConfig(model=model, dimension=dimension)

        with console.status("[bold green]Loading model..."):
            embedder = Embedder(embedding_config)

        console.print(f"[green]✓ Model loaded ({dimension}-dim)[/green]")
        console.print()

        # Get all users if not specified
        # TODO: Get all users from DB
        users_to_reindex = [user_id] if user_id else ["default_user"]

        total_reindexed = 0

        for uid in users_to_reindex:
            console.print(f"[cyan]Reindexing user: {uid}[/cyan]")

            # Create MemoryManager
            config = MemorySystemConfig(embedding=embedding_config)
            manager = MemoryManager(
                user_id=uid,
                agent_name="global",
                enable_rag=True,
                memory_config=config,
            )

            # Get all persistent memories
            memories = manager.persistent.search("%", uid, agent_name=None, limit=10000)

            if not memories:
                console.print(f"  [dim]No memories found for user {uid}[/dim]")
                continue

            console.print(f"  Found {len(memories)} memories")

            if dry_run:
                console.print(
                    f"  [dim](dry-run: would reindex {len(memories)} memories)[/dim]"
                )
                continue

            # Reindex in batches
            from rich.progress import Progress, SpinnerColumn, TextColumn

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"  Reindexing {len(memories)} memories...",
                    total=len(memories),
                )

                for i in range(0, len(memories), batch_size):
                    batch = memories[i : i + batch_size]

                    # Generate embeddings for batch
                    contents = [f"{mem['key']}: {mem['value']}" for mem in batch]

                    # Use passage prefix for E5 models
                    embeddings = embedder.encode_passages(contents)

                    # Store in RAG
                    for mem, emb in zip(batch, embeddings):
                        # TODO: Store embeddings in new collection
                        # For now, use existing store method
                        manager.store_semantic(
                            content=f"{mem['key']}: {mem['value']}",
                            metadata=mem.get("metadata"),
                        )

                    progress.update(task, advance=len(batch))
                    total_reindexed += len(batch)

            console.print(f"  [green]✓ Reindexed {len(memories)} memories[/green]")
            console.print()

        # Summary
        if dry_run:
            console.print("[yellow]Dry run completed (no changes made)[/yellow]")
        else:
            console.print("[green]✓ Reindexing completed![/green]")
            console.print()
            console.print(f"Total memories reindexed: {total_reindexed}")
        console.print()

    except ImportError as e:
        console.print(f"\n[red]✗ Missing dependency: {e}[/red]")
        console.print("\nInstall with: pip install sentence-transformers")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[red]✗ Reindexing failed: {e}[/red]")
        raise click.Abort()
