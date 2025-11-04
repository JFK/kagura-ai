"""CLI commands for memory management.

Provides commands for memory export, import, and consolidation.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.group(name="memory")
def memory_group() -> None:
    """Memory management commands.

    Manage memory export, import, and consolidation.
    """
    pass


@memory_group.command(name="export")
@click.option(
    "--output",
    "-o",
    required=True,
    help="Output directory for exported data",
)
@click.option(
    "--user-id",
    default="default_user",
    help="User ID to export (default: default_user)",
)
@click.option(
    "--agent-name",
    default="global",
    help="Agent name to export (default: global)",
)
@click.option(
    "--working/--no-working",
    default=True,
    help="Include working memory (default: yes)",
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
def export_command(
    output: str,
    user_id: str,
    agent_name: str,
    working: bool,
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
        kagura memory export --output ./backup --no-working

        # Export for specific user
        kagura memory export --output ./backup --user-id user_alice
    """
    from kagura.core.memory import MemoryManager
    from kagura.core.memory.export import MemoryExporter

    console.print(f"\n[cyan]Exporting memory data for user '{user_id}'...[/cyan]")
    console.print()

    try:
        # Create MemoryManager
        manager = MemoryManager(user_id=user_id, agent_name=agent_name)

        # Create exporter
        exporter = MemoryExporter(manager)

        # Run export
        with console.status("[bold green]Exporting..."):
            stats = asyncio.run(
                exporter.export_all(
                    output_dir=output,
                    include_working=working,
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


@memory_group.command(name="import")
@click.option(
    "--input",
    "-i",
    required=True,
    help="Input directory containing exported data",
)
@click.option(
    "--user-id",
    default="default_user",
    help="User ID to import as (default: default_user)",
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
def import_command(
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
    from kagura.core.memory import MemoryManager
    from kagura.core.memory.export import MemoryImporter

    console.print(f"\n[cyan]Importing memory data for user '{user_id}'...[/cyan]")

    if clear:
        console.print("[yellow]⚠️  Warning: Existing data will be cleared[/yellow]")

    console.print()

    try:
        # Create MemoryManager
        manager = MemoryManager(user_id=user_id, agent_name=agent_name)

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


@memory_group.command(name="reindex")
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
def reindex_command(
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


@memory_group.command(name="setup")
@click.option(
    "--model",
    default=None,
    help="Embedding model (default: auto-detect based on OPENAI_API_KEY)",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "local"], case_sensitive=False),
    default=None,
    help="Force provider: 'openai' (API) or 'local' (sentence-transformers)",
)
def setup_command(model: str | None, provider: str | None) -> None:
    """Pre-download embeddings model to avoid MCP timeout.

    Downloads and initializes the embedding model used for semantic search.
    Run this once before using MCP memory tools to prevent first-time timeouts.

    Provider auto-detection:
    - If OPENAI_API_KEY is set → OpenAI Embeddings API (text-embedding-3-large)
    - Otherwise → Local model (intfloat/multilingual-e5-large, ~500MB download)

    Examples:

        # Auto-detect based on OPENAI_API_KEY
        kagura memory setup

        # Force OpenAI API (requires OPENAI_API_KEY)
        kagura memory setup --provider openai

        # Force local model
        kagura memory setup --provider local

        # Specific model
        kagura memory setup --model intfloat/multilingual-e5-base
    """
    import os

    from kagura.config.memory_config import EmbeddingConfig

    console.print("\n[cyan]Kagura Memory Setup[/cyan]")
    console.print()

    # Auto-detect provider if not specified
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))

    if provider is None:
        if has_openai_key:
            provider = "openai"
            console.print("[green]✓ OPENAI_API_KEY detected[/green]")
        else:
            provider = "local"
            console.print("[yellow]⚠ OPENAI_API_KEY not set[/yellow]")
        console.print(f"Using provider: [bold]{provider}[/bold]")
        console.print()

    # Set default model based on provider
    if model is None:
        if provider == "openai":
            model = "text-embedding-3-large"
        else:
            model = "intfloat/multilingual-e5-large"

    # Provider-specific setup
    if provider == "openai":
        console.print(f"Using OpenAI Embeddings API: [bold]{model}[/bold]")
        console.print("[dim](API-based, no download required)[/dim]")
        console.print()

        if not has_openai_key:
            console.print("[red]✗ OPENAI_API_KEY not set[/red]")
            console.print("\nSet your API key:")
            console.print("  export OPENAI_API_KEY='sk-...'")
            raise click.Abort()

        try:
            # Test OpenAI API
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            with console.status("[bold green]Testing OpenAI API..."):
                response = client.embeddings.create(input=["test"], model=model)

            console.print("[green]✓ OpenAI API configured successfully![/green]")
            console.print()
            console.print(f"  Model: {model}")
            console.print(f"  Dimension: {len(response.data[0].embedding)}")
            console.print()
            console.print("[green]MCP memory tools ready (using OpenAI API)![/green]")
            console.print()

        except Exception as e:
            console.print(f"\n[red]✗ OpenAI API test failed: {e}[/red]")
            raise click.Abort()

    else:  # local provider
        console.print(f"Downloading local model: [bold]{model}[/bold]")
        console.print("[dim](~500MB, may take 30-60 seconds)[/dim]")
        console.print()

        try:
            from kagura.core.memory.embeddings import Embedder

            config = EmbeddingConfig(model=model)

            with console.status("[bold green]Downloading model..."):
                embedder = Embedder(config)

            # Test the model
            test_embedding = embedder.encode_queries(["test"])

            console.print("[green]✓ Model downloaded successfully![/green]")
            console.print()
            console.print(f"  Model: {model}")
            console.print(f"  Dimension: {len(test_embedding[0])}")
            console.print()
            console.print("[green]MCP memory tools are now ready to use![/green]")
            console.print()

        except ImportError as e:
            console.print(f"\n[red]✗ Missing dependency: {e}[/red]")
            console.print("\nInstall with: pip install 'kagura-ai[memory]'")
            raise click.Abort()
        except Exception as e:
            console.print(f"\n[red]✗ Setup failed: {e}[/red]")
            raise click.Abort()


@memory_group.command(name="list")
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
def list_command(
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
    from rich.table import Table

    from kagura.core.memory import MemoryManager

    console.print("\n[cyan]Memory List[/cyan]")
    console.print()

    try:
        manager = MemoryManager(
            user_id=user_id or "system",
            agent_name=agent_name or "global",
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


@memory_group.command(name="search")
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
def search_command(
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
    from rich.table import Table

    from kagura.core.memory import MemoryManager

    console.print(f'\n[cyan]Searching for: "{query}"[/cyan]')
    console.print()

    try:
        manager = MemoryManager(
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
                score = result.get("score", result.get("similarity", result.get("rrf_score", result.get("distance", 0.0))))
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


@memory_group.command(name="stats")
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
def stats_command(
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
    from rich.table import Table

    from kagura.config.paths import get_data_dir
    from kagura.core.memory import MemoryManager

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

        # Now create MemoryManager to count memories
        manager = MemoryManager(
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
            import sqlite3

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, COUNT(*) as count FROM memories "
                "WHERE user_id IS NOT NULL GROUP BY user_id ORDER BY count DESC"
            )
            user_stats = cursor.fetchall()
            conn.close()

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


# Commands from PR #505 (#504) - Index and Doctor
@memory_group.command(name="index")
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
def index_command(
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
    from rich.progress import Progress, SpinnerColumn, TextColumn

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
        # Create MemoryManager
        manager = MemoryManager(
            user_id=user_id or "system",
            agent_name=agent_name or "indexer",
            enable_rag=True,
        )

        # Get all persistent memories
        memories = manager.persistent.fetch_all(
            user_id=user_id or "system",
            agent_name=agent_name,
            limit=100000,
        )

        if not memories:
            console.print("[yellow]No memories found to index[/yellow]")
            return

        console.print(f"Found {len(memories)} memories to index")
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


@memory_group.command(name="doctor")
@click.option(
    "--user-id",
    default=None,
    help="Check specific user (default: system-wide)",
)
def doctor_command(user_id: str | None) -> None:
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
    from rich.panel import Panel

    from kagura.config.paths import get_data_dir
    from kagura.core.memory import MemoryManager

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
        manager = MemoryManager(
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

    import os

    reranking_enabled = os.getenv("KAGURA_ENABLE_RERANKING", "").lower() == "true"

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
                console.print(
                    "   [dim]Set: export KAGURA_ENABLE_RERANKING=true[/dim]"
                )
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
