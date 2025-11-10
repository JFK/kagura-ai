"""PostgreSQL-based backend for GraphMemory.

Issue #554 - Cloud-Native Infrastructure Migration

Production-ready backend using PostgreSQL JSONB for graph storage.
Supports multi-instance deployments and cloud environments.
"""

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .base import GraphBackend

if TYPE_CHECKING:
    import networkx as nx

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class GraphModel(Base):
    """SQLAlchemy model for graph storage.

    Schema:
        - user_id: Unique identifier for user/agent (allows multi-user support)
        - graph_data: NetworkX DiGraph serialized as JSONB
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
    """

    __tablename__ = "graph_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    graph_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class PostgresBackend(GraphBackend):
    """PostgreSQL-based storage backend for GraphMemory.

    Production backend for cloud deployments with multi-instance support.
    Stores NetworkX DiGraph as JSONB in PostgreSQL.

    Args:
        database_url: PostgreSQL connection URL (e.g., postgresql://user:pass@host:5432/db)
        user_id: User/agent identifier for multi-user support (default: "global")
        create_tables: Automatically create tables if they don't exist (default: True)

    Example:
        >>> backend = PostgresBackend(
        ...     database_url="postgresql://localhost:5432/kagura",
        ...     user_id="user_001"
        ... )
        >>> backend.save(graph)
        >>> loaded_graph = backend.load()
        >>> backend.close()

    Note:
        Uses SQLAlchemy 2.0+ declarative style.
        Connection pooling is handled by SQLAlchemy.
    """

    def __init__(
        self,
        database_url: str,
        user_id: str = "global",
        create_tables: bool = True,
    ):
        """Initialize PostgreSQL backend.

        Args:
            database_url: PostgreSQL connection URL
            user_id: User/agent identifier for multi-user support
            create_tables: Automatically create tables if they don't exist

        Raises:
            ImportError: If SQLAlchemy is not installed
            ValueError: If database_url is invalid
        """
        if not database_url:
            raise ValueError("database_url is required for PostgresBackend")

        self.database_url = database_url
        self.user_id = user_id

        # Create SQLAlchemy engine
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections every hour
            echo=False,  # Set to True for SQL debugging
        )

        # Create tables if needed
        if create_tables:
            Base.metadata.create_all(self.engine)
            logger.debug("Created graph_memory table (if not exists)")

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        logger.info(
            f"Initialized PostgresBackend for user_id={user_id} "
            f"(host={self._get_host()})"
        )

    def _get_host(self) -> str:
        """Extract host from database URL for logging."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(self.database_url)
            return parsed.hostname or "unknown"
        except Exception:
            return "unknown"

    def _get_session(self) -> Session:
        """Get new database session.

        Returns:
            SQLAlchemy Session instance
        """
        return self.SessionLocal()

    def save(self, graph: "nx.DiGraph") -> None:
        """Save graph to PostgreSQL.

        Args:
            graph: NetworkX DiGraph to save

        Raises:
            IOError: If database operation fails
        """
        import networkx as nx

        # Convert NetworkX graph to JSON-serializable format
        # edges="links" ensures forward compatibility with NetworkX 3.6+
        data = nx.node_link_data(graph, edges="links")

        session = self._get_session()
        try:
            # Upsert (update or insert)
            existing = (
                session.query(GraphModel).filter_by(user_id=self.user_id).first()
            )

            if existing:
                # Update existing graph
                existing.graph_data = data  # type: ignore[assignment]
                existing.updated_at = datetime.now()  # type: ignore[assignment]
                logger.debug(
                    f"Updated graph for user_id={self.user_id} "
                    f"({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)"
                )
            else:
                # Insert new graph
                new_graph = GraphModel(user_id=self.user_id, graph_data=data)  # type: ignore[arg-type]
                session.add(new_graph)
                logger.info(
                    f"Created new graph for user_id={self.user_id} "
                    f"({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)"
                )

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save graph for user_id={self.user_id}: {e}")
            raise IOError(f"Failed to save graph to PostgreSQL: {e}") from e
        finally:
            session.close()

    def load(self) -> "nx.DiGraph":
        """Load graph from PostgreSQL.

        Returns:
            NetworkX DiGraph loaded from database.
            Returns empty DiGraph if no graph exists for this user.

        Raises:
            IOError: If database operation fails
        """
        import networkx as nx

        session = self._get_session()
        try:
            result = (
                session.query(GraphModel).filter_by(user_id=self.user_id).first()
            )

            if not result:
                logger.debug(
                    f"No graph found for user_id={self.user_id}, returning empty graph"
                )
                return nx.DiGraph()

            # Convert JSON data back to NetworkX graph
            # edges="links" ensures forward compatibility with NetworkX 3.6+
            graph: nx.DiGraph = nx.node_link_graph(result.graph_data, edges="links")  # type: ignore[assignment, arg-type]

            logger.debug(
                f"Loaded graph for user_id={self.user_id} "
                f"({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)"
            )

            return graph

        except Exception as e:
            logger.error(f"Failed to load graph for user_id={self.user_id}: {e}")
            raise IOError(f"Failed to load graph from PostgreSQL: {e}") from e
        finally:
            session.close()

    def exists(self) -> bool:
        """Check if graph exists in PostgreSQL.

        Returns:
            True if graph exists for this user, False otherwise

        Raises:
            IOError: If database operation fails
        """
        session = self._get_session()
        try:
            result = (
                session.query(GraphModel.id)
                .filter_by(user_id=self.user_id)
                .first()
            )
            exists = result is not None
            logger.debug(f"Graph exists for user_id={self.user_id}: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Failed to check graph existence for user_id={self.user_id}: {e}")
            raise IOError(f"Failed to check graph existence: {e}") from e
        finally:
            session.close()

    def delete(self) -> None:
        """Delete graph from PostgreSQL.

        Raises:
            IOError: If database operation fails
        """
        session = self._get_session()
        try:
            deleted = (
                session.query(GraphModel)
                .filter_by(user_id=self.user_id)
                .delete()
            )
            session.commit()

            if deleted > 0:
                logger.info(f"Deleted graph for user_id={self.user_id}")
            else:
                logger.warning(
                    f"No graph found to delete for user_id={self.user_id}"
                )

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete graph for user_id={self.user_id}: {e}")
            raise IOError(f"Failed to delete graph from PostgreSQL: {e}") from e
        finally:
            session.close()

    def close(self) -> None:
        """Close database connection and cleanup resources.

        Should be called when backend is no longer needed.
        Disposes of the SQLAlchemy engine and connection pool.
        """
        try:
            self.engine.dispose()
            logger.info(f"Closed PostgresBackend for user_id={self.user_id}")
        except Exception as e:
            logger.error(f"Error closing PostgresBackend: {e}")
