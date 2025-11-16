"""JSON file-based backend for GraphMemory.

Issue #554 - Cloud-Native Infrastructure Migration

This is the default backend, extracted from the original GraphMemory implementation.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .base import GraphBackend

if TYPE_CHECKING:
    import networkx as nx

logger = logging.getLogger(__name__)


class JSONBackend(GraphBackend):
    """JSON file-based storage backend for GraphMemory.

    Default backend for local development and single-instance deployments.
    Stores NetworkX DiGraph as JSON file on disk.

    Args:
        persist_path: Path to JSON file for graph storage

    Example:
        >>> from pathlib import Path
        >>> backend = JSONBackend(persist_path=Path("graph.json"))
        >>> backend.save(graph)
        >>> loaded_graph = backend.load()

    Note:
        Uses NetworkX's node_link_data format with edges="links"
        for forward compatibility with NetworkX 3.6+.
    """

    def __init__(self, persist_path: Path):
        """Initialize JSON backend.

        Args:
            persist_path: Path to JSON file for graph storage
        """
        self.persist_path = persist_path
        logger.debug(f"Initialized JSONBackend with path: {persist_path}")

    def save(self, graph: "nx.DiGraph") -> None:
        """Save graph to JSON file.

        Args:
            graph: NetworkX DiGraph to save

        Raises:
            IOError: If file write fails
        """
        import networkx as nx

        # Ensure parent directory exists
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert NetworkX graph to JSON-serializable format
        # edges="links" ensures forward compatibility with NetworkX 3.6+
        data = nx.node_link_data(graph, edges="links")

        # Save graph using JSON
        with open(self.persist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.debug(
            f"Saved graph with {graph.number_of_nodes()} nodes, "
            f"{graph.number_of_edges()} edges to {self.persist_path}"
        )

    def load(self) -> "nx.DiGraph":
        """Load graph from JSON file.

        Returns:
            NetworkX DiGraph loaded from file.
            Returns empty DiGraph if file doesn't exist.

        Raises:
            IOError: If file read fails
            ValueError: If JSON format is invalid
        """
        import networkx as nx

        if not self.exists():
            logger.debug(f"Graph file not found: {self.persist_path}, returning empty graph")
            return nx.DiGraph()

        # Load graph using JSON
        with open(self.persist_path, encoding="utf-8") as f:
            data = json.load(f)

        # Convert JSON data back to NetworkX graph
        # edges="links" ensures forward compatibility with NetworkX 3.6+
        graph: nx.DiGraph = nx.node_link_graph(data, edges="links")  # type: ignore[assignment]

        logger.debug(
            f"Loaded graph with {graph.number_of_nodes()} nodes, "
            f"{graph.number_of_edges()} edges from {self.persist_path}"
        )

        return graph

    def exists(self) -> bool:
        """Check if graph JSON file exists.

        Returns:
            True if file exists, False otherwise
        """
        return self.persist_path.exists()

    def delete(self) -> None:
        """Delete graph JSON file.

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if self.exists():
            self.persist_path.unlink()
            logger.info(f"Deleted graph file: {self.persist_path}")
        else:
            logger.warning(f"Graph file not found, nothing to delete: {self.persist_path}")

    def close(self) -> None:
        """Close backend connection.

        For JSON backend, this is a no-op since there's no persistent connection.
        """
        pass
