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
