"""Abstract base class for GraphMemory storage backends.

Issue #554 - Cloud-Native Infrastructure Migration
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import networkx as nx


class GraphBackend(ABC):
    """Abstract base class for GraphMemory storage backends.

    Defines the interface that all storage backends must implement.
    This allows GraphMemory to support multiple storage options (JSON, PostgreSQL, etc.)
    without changing the core graph manipulation logic.

    Example:
        >>> from kagura.core.graph.backends import JSONBackend, PostgresBackend
        >>>
        >>> # Local development (file-based)
        >>> backend = JSONBackend(persist_path=Path("graph.json"))
        >>>
        >>> # Production (PostgreSQL)
        >>> backend = PostgresBackend(database_url="postgresql://...")
        >>>
        >>> graph_memory = GraphMemory(backend=backend)
    """

    @abstractmethod
    def save(self, graph: "nx.DiGraph") -> None:
        """Save graph to backend storage.

        Args:
            graph: NetworkX DiGraph to save

        Raises:
            IOError: If save operation fails
        """
        pass

    @abstractmethod
    def load(self) -> "nx.DiGraph":
        """Load graph from backend storage.

        Returns:
            NetworkX DiGraph loaded from storage.
            Returns empty DiGraph if storage doesn't exist.

        Raises:
            IOError: If load operation fails
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """Check if graph exists in backend storage.

        Returns:
            True if graph exists, False otherwise
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """Delete graph from backend storage.

        Raises:
            IOError: If delete operation fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close backend connection and cleanup resources.

        Should be called when backend is no longer needed.
        For file-based backends, this is usually a no-op.
        For database backends, this closes connections.
        """
        pass
