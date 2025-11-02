"""Memory export/import functionality.

Exports and imports memories, graph data, and interactions in JSONL format.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from kagura.core.memory import MemoryManager


class MemoryExporter:
    """Export memory data to JSONL format."""

    def __init__(self, manager: MemoryManager):
        """Initialize exporter.

        Args:
            manager: MemoryManager instance to export from
        """
        self.manager = manager

    async def export_all(
        self,
        output_dir: str | Path,
        include_working: bool = True,
        include_persistent: bool = True,
        include_graph: bool = True,
    ) -> dict[str, int]:
        """Export all memory data to JSONL files.

        Args:
            output_dir: Output directory path
            include_working: Export working memory
            include_persistent: Export persistent memory
            include_graph: Export graph data

        Returns:
            Dict with export counts: {
                "memories": count,
                "graph_nodes": count,
                "graph_edges": count
            }

        Example:
            >>> exporter = MemoryExporter(manager)
            >>> stats = await exporter.export_all("./backup")
            >>> print(f"Exported {stats['memories']} memories")
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        stats = {
            "memories": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
        }

        # Export memories
        if include_working or include_persistent:
            memories_file = output_path / "memories.jsonl"
            count = await self._export_memories(
                memories_file,
                include_working=include_working,
                include_persistent=include_persistent,
            )
            stats["memories"] = count

        # Export graph
        if include_graph and self.manager.graph:
            graph_file = output_path / "graph.jsonl"
            node_count, edge_count = await self._export_graph(graph_file)
            stats["graph_nodes"] = node_count
            stats["graph_edges"] = edge_count

        # Export metadata
        metadata_file = output_path / "metadata.json"
        await self._export_metadata(metadata_file, stats)

        return stats

    async def _export_memories(
        self,
        output_file: Path,
        include_working: bool = True,
        include_persistent: bool = True,
    ) -> int:
        """Export memories to JSONL.

        Args:
            output_file: Output JSONL file path
            include_working: Include working memory
            include_persistent: Include persistent memory

        Returns:
            Number of memories exported
        """
        count = 0

        with open(output_file, "w") as f:
            # Export working memory
            if include_working:
                working_keys = self.manager.working.keys()
                for key in working_keys:
                    value = self.manager.working.get(key)
                    memory_record = {
                        "type": "memory",
                        "scope": "working",
                        "key": key,
                        "value": value,
                        "user_id": self.manager.user_id,
                        "agent_name": self.manager.agent_name,
                        "exported_at": datetime.now().isoformat(),
                    }
                    f.write(json.dumps(memory_record) + "\n")
                    count += 1

            # Export persistent memory
            if include_persistent and self.manager.persistent:
                # Query SQLite database
                db_path = self.manager.persistent.db_path

                if db_path.exists():
                    with sqlite3.connect(db_path) as conn:
                        conn.row_factory = sqlite3.Row

                        cursor = conn.execute(
                            """
                            SELECT key, value, user_id, agent_name,
                                   created_at, updated_at, metadata
                            FROM memories
                            WHERE user_id = ?
                            ORDER BY created_at
                            """,
                            (self.manager.user_id,),
                        )

                        for row in cursor:
                            memory_record = {
                                "type": "memory",
                                "scope": "persistent",
                                "key": row["key"],
                                "value": json.loads(row["value"]),
                                "user_id": row["user_id"],
                                "agent_name": row["agent_name"],
                                "created_at": row["created_at"],
                                "updated_at": row["updated_at"],
                                "metadata": (
                                    json.loads(row["metadata"])
                                    if row["metadata"]
                                    else None
                                ),
                                "exported_at": datetime.now().isoformat(),
                            }
                            f.write(json.dumps(memory_record) + "\n")
                            count += 1

        return count

    async def _export_graph(self, output_file: Path) -> tuple[int, int]:
        """Export graph data to JSONL.

        Args:
            output_file: Output JSONL file path

        Returns:
            Tuple of (node_count, edge_count)
        """
        if not self.manager.graph:
            return 0, 0

        node_count = 0
        edge_count = 0

        with open(output_file, "w") as f:
            # Export nodes
            for node_id, node_data in self.manager.graph.graph.nodes(data=True):  # type: ignore
                # Extract data safely
                items = node_data.items() if node_data else []  # type: ignore
                filtered_data = {k: v for k, v in items if k != "type"}  # type: ignore

                node_record = {
                    "type": "node",
                    "id": node_id,
                    "node_type": node_data.get("type") if node_data else None,  # type: ignore
                    "data": filtered_data,
                    "exported_at": datetime.now().isoformat(),
                }
                f.write(json.dumps(node_record) + "\n")
                node_count += 1

            # Export edges
            for src, dst, edge_data in self.manager.graph.graph.edges(data=True):  # type: ignore
                # Extract edge data safely
                edge_items = edge_data.items() if edge_data else []  # type: ignore
                filtered_edge_data = {
                    k: v
                    for k, v in edge_items  # type: ignore
                    if k not in ("type", "weight")
                }

                edge_record = {
                    "type": "edge",
                    "src": src,
                    "dst": dst,
                    "rel_type": edge_data.get("type") if edge_data else None,  # type: ignore
                    "weight": edge_data.get("weight", 1.0) if edge_data else 1.0,  # type: ignore
                    "data": filtered_edge_data,
                    "exported_at": datetime.now().isoformat(),
                }
                f.write(json.dumps(edge_record) + "\n")
                edge_count += 1

        return node_count, edge_count

    async def _export_metadata(self, output_file: Path, stats: dict[str, int]) -> None:
        """Export metadata about the export.

        Args:
            output_file: Output JSON file path
            stats: Export statistics
        """
        metadata = {
            "exported_at": datetime.now().isoformat(),
            "user_id": self.manager.user_id,
            "agent_name": self.manager.agent_name,
            "stats": stats,
            "format_version": "1.0",
        }

        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)


class MemoryImporter:
    """Import memory data from JSONL format."""

    def __init__(self, manager: MemoryManager):
        """Initialize importer.

        Args:
            manager: MemoryManager instance to import into
        """
        self.manager = manager

    async def import_all(
        self,
        input_dir: str | Path,
        clear_existing: bool = False,
    ) -> dict[str, int]:
        """Import all memory data from JSONL files.

        Args:
            input_dir: Input directory path
            clear_existing: Clear existing data before import

        Returns:
            Dict with import counts

        Example:
            >>> importer = MemoryImporter(manager)
            >>> stats = await importer.import_all("./backup")
            >>> print(f"Imported {stats['memories']} memories")
        """
        input_path = Path(input_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"Import directory not found: {input_path}")

        stats = {
            "memories": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
        }

        # Clear existing data if requested
        if clear_existing:
            self.manager.working.clear()
            # TODO: Clear persistent memory (need clear method)

        # Import memories
        memories_file = input_path / "memories.jsonl"
        if memories_file.exists():
            count = await self._import_memories(memories_file)
            stats["memories"] = count

        # Import graph
        graph_file = input_path / "graph.jsonl"
        if graph_file.exists() and self.manager.graph:
            node_count, edge_count = await self._import_graph(graph_file)
            stats["graph_nodes"] = node_count
            stats["graph_edges"] = edge_count

        return stats

    async def _import_memories(self, input_file: Path) -> int:
        """Import memories from JSONL.

        Args:
            input_file: Input JSONL file path

        Returns:
            Number of memories imported
        """
        count = 0

        with open(input_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)

                if record.get("type") != "memory":
                    continue

                # Extract fields
                key = record["key"]
                value = record["value"]
                scope = record["scope"]
                metadata = record.get("metadata")

                # Import to appropriate scope
                if scope == "working":
                    self.manager.working.set(key, value)
                elif scope == "persistent" and self.manager.persistent:
                    self.manager.persistent.store(
                        key=key,
                        value=value,
                        user_id=self.manager.user_id,
                        agent_name=self.manager.agent_name,
                        metadata=metadata,
                    )

                count += 1

        return count

    async def _import_graph(self, input_file: Path) -> tuple[int, int]:
        """Import graph data from JSONL.

        Args:
            input_file: Input JSONL file path

        Returns:
            Tuple of (node_count, edge_count)
        """
        if not self.manager.graph:
            return 0, 0

        node_count = 0
        edge_count = 0

        with open(input_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)

                if record.get("type") == "node":
                    # Import node
                    node_id = record["id"]
                    node_type = record["node_type"]
                    data = record.get("data", {})

                    # GraphMemory add_node is not async
                    self.manager.graph.add_node(
                        node_id=node_id,
                        node_type=node_type,
                        data=data,
                    )
                    node_count += 1

                elif record.get("type") == "edge":
                    # Import edge
                    src = record["src"]
                    dst = record["dst"]
                    rel_type = record["rel_type"]
                    weight = record.get("weight", 1.0)

                    # GraphMemory add_edge is not async
                    self.manager.graph.add_edge(
                        src_id=src,
                        dst_id=dst,
                        rel_type=rel_type,
                        weight=weight,
                    )
                    edge_count += 1

        return node_count, edge_count
