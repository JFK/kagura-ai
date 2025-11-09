"""Memory CLI commands - memory management.

Provides commands for memory setup, operations, queries, and diagnostics.
"""

from __future__ import annotations

import click

from kagura.cli.memory import diagnostics, operations, query, setup


@click.group(name="memory")
def memory_group() -> None:
    """Memory management commands.

    Manage memory export, import, and consolidation.
    """
    pass


# Register all commands
memory_group.add_command(setup.setup_command, name="setup")
memory_group.add_command(setup.install_reranking, name="install-reranking")
memory_group.add_command(operations.export_memory, name="export")
memory_group.add_command(operations.import_memory, name="import")
memory_group.add_command(operations.reindex, name="reindex")
memory_group.add_command(query.list_memories, name="list")
memory_group.add_command(query.search_memory, name="search")
memory_group.add_command(query.stats, name="stats")
memory_group.add_command(diagnostics.index, name="index")
memory_group.add_command(diagnostics.doctor, name="doctor")

__all__ = ["memory_group"]
