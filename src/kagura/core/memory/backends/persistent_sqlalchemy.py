"""SQLAlchemy-based backend for Persistent Memory.

Issue #554 - Cloud-Native Infrastructure Migration

Supports both SQLite (default) and PostgreSQL via DATABASE_URL.
Uses singleton pattern for Engine (connection pool shared across instances).
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)


# Singleton Engine cache (shared across all instances)
_engine_cache: dict[str, Engine] = {}


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class MemoryModel(Base):
    """SQLAlchemy model for persistent memory storage.

    Compatible with both SQLite and PostgreSQL.

    Schema:
        - key: Memory key
        - value: JSON-serialized value
        - user_id: User/owner identifier
        - agent_name: Optional agent scope
        - metadata: Additional metadata (JSON)
        - access_count: Number of times accessed
        - last_accessed_at: Last access timestamp
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
    """

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    user_id = Column(String(255), nullable=False, default="default_user")
    agent_name = Column(String(255), nullable=True)
    # Note: 'metadata' is SQLAlchemy reserved word, use 'memory_metadata' for Python attribute
    # but keep DB column name as 'metadata' for SQLite compatibility
    memory_metadata = Column('metadata', Text, nullable=True)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Composite unique constraint
    __table_args__ = (
        Index("idx_key", "key"),
        Index("idx_agent", "agent_name"),
        Index("idx_user", "user_id"),
        Index("idx_user_agent", "user_id", "agent_name"),
        Index("idx_user_key", "user_id", "key"),
        Index("idx_key_agent", "key", "agent_name"),
    )


class SQLAlchemyPersistentBackend:
    """SQLAlchemy-based backend for persistent memory.

    Supports both SQLite and PostgreSQL via database URL.
    Uses singleton pattern for Engine to share connection pools across instances.

    Args:
        database_url: Database connection URL
            - SQLite: sqlite:///path/to/memory.db
            - PostgreSQL: postgresql://user:pass@host:5432/db

    Example:
        >>> # SQLite (default)
        >>> backend = SQLAlchemyPersistentBackend("sqlite:///~/.local/share/kagura/memory.db")
        >>>
        >>> # PostgreSQL (production)
        >>> backend = SQLAlchemyPersistentBackend("postgresql://localhost:5432/kagura")

    Note:
        Multiple instances with the same database_url will share a single Engine
        (and connection pool) for efficiency. This is the recommended SQLAlchemy pattern.
    """

    def __init__(self, database_url: str, create_tables: bool = True):
        """Initialize SQLAlchemy backend.

        Args:
            database_url: Database connection URL
            create_tables: Automatically create tables if they don't exist
        """
        self.database_url = database_url

        # Get or create shared engine (singleton pattern)
        self.engine = self._get_or_create_engine(database_url)

        # Create tables if needed
        if create_tables:
            Base.metadata.create_all(self.engine)
            logger.debug("Created memories table (if not exists)")

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        logger.info(f"Initialized SQLAlchemyPersistentBackend ({self._get_backend_type()})")

    @staticmethod
    def _get_or_create_engine(database_url: str) -> Engine:
        """Get or create SQLAlchemy engine (singleton pattern).

        Reuses existing engine if already created for the same database_url.
        This shares connection pools across all backend instances.

        Args:
            database_url: Database connection URL

        Returns:
            SQLAlchemy Engine instance (cached)
        """
        global _engine_cache

        if database_url not in _engine_cache:
            logger.info(f"Creating new Engine for {database_url.split('@')[-1]}")

            engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,  # Recycle connections every hour
                pool_size=5,  # Connection pool size
                max_overflow=10,  # Max additional connections
                echo=False,  # Set to True for SQL debugging
            )

            _engine_cache[database_url] = engine
        else:
            logger.debug(f"Reusing cached Engine for {database_url.split('@')[-1]}")

        return _engine_cache[database_url]

    def _get_backend_type(self) -> str:
        """Get backend type (sqlite or postgres) from URL."""
        if self.database_url.startswith("sqlite"):
            return "sqlite"
        elif self.database_url.startswith("postgresql"):
            return "postgresql"
        else:
            return "unknown"

    def _get_session(self) -> Session:
        """Get new database session."""
        return self.SessionLocal()

    def store(
        self,
        key: str,
        value: Any,
        user_id: str,
        agent_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Store persistent memory.

        Args:
            key: Memory key
            value: Value to store (will be JSON serialized)
            user_id: User identifier (memory owner)
            agent_name: Optional agent name for scoping
            metadata: Optional metadata
        """
        value_json = json.dumps(value)
        metadata_json = json.dumps(metadata) if metadata else None

        session = self._get_session()
        try:
            # Check if exists (user_id + key + agent_name combination)
            existing = (
                session.query(MemoryModel)
                .filter_by(key=key, user_id=user_id)
                .filter(
                    (MemoryModel.agent_name == agent_name)
                    if agent_name
                    else (MemoryModel.agent_name.is_(None))
                )
                .first()
            )

            if existing:
                # Update
                existing.value = value_json  # type: ignore[assignment]
                existing.memory_metadata = metadata_json  # type: ignore[assignment]
                existing.updated_at = datetime.now()  # type: ignore[assignment]
            else:
                # Insert
                new_memory = MemoryModel(
                    key=key,
                    value=value_json,
                    user_id=user_id,
                    agent_name=agent_name,
                    memory_metadata=metadata_json,
                )
                session.add(new_memory)

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to store memory (key={key}, user_id={user_id}): {e}")
            raise
        finally:
            session.close()

    def recall(
        self,
        key: str,
        user_id: str,
        agent_name: Optional[str] = None,
        track_access: bool = False,
        include_metadata: bool = False,
    ) -> Optional[Any]:
        """Retrieve persistent memory.

        Args:
            key: Memory key
            user_id: User identifier (memory owner)
            agent_name: Optional agent name for scoping
            track_access: If True, record access for frequency tracking
            include_metadata: If True, return tuple of (value, metadata)

        Returns:
            Stored value or tuple of (value, metadata) if include_metadata is True.
        """
        session = self._get_session()
        try:
            # Query with agent_name priority (exact match > NULL)
            query = session.query(MemoryModel).filter_by(key=key, user_id=user_id)

            if agent_name:
                query = query.filter(
                    (MemoryModel.agent_name == agent_name)
                    | (MemoryModel.agent_name.is_(None))
                ).order_by(
                    # Exact match first, then NULL
                    func.coalesce(
                        (MemoryModel.agent_name == agent_name).cast(Integer), 1
                    ),
                    MemoryModel.updated_at.desc(),
                )
            else:
                query = query.filter(MemoryModel.agent_name.is_(None))

            result = query.first()

            if result:
                value = json.loads(result.value)
                metadata = json.loads(result.memory_metadata) if result.memory_metadata else None

                # Track access if requested
                if track_access:
                    self.record_access(key, user_id, result.agent_name)

                if include_metadata:
                    return value, metadata
                return value

            if include_metadata:
                return None
            return None

        except Exception as e:
            logger.error(f"Failed to recall memory (key={key}, user_id={user_id}): {e}")
            raise
        finally:
            session.close()

    def record_access(
        self, key: str, user_id: str, agent_name: Optional[str] = None
    ) -> None:
        """Record memory access for frequency tracking.

        Args:
            key: Memory key
            user_id: User identifier (memory owner)
            agent_name: Optional agent name for scoping
        """
        session = self._get_session()
        try:
            result = (
                session.query(MemoryModel)
                .filter_by(key=key, user_id=user_id)
                .filter(
                    (MemoryModel.agent_name == agent_name)
                    if agent_name
                    else (MemoryModel.agent_name.is_(None))
                )
                .first()
            )

            if result:
                result.access_count = (result.access_count or 0) + 1  # type: ignore[assignment, operator]
                result.last_accessed_at = datetime.now()  # type: ignore[assignment]
                session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to record access (key={key}, user_id={user_id}): {e}")
        finally:
            session.close()

    def delete(
        self, key: str, user_id: str, agent_name: Optional[str] = None
    ) -> bool:
        """Delete persistent memory.

        Args:
            key: Memory key
            user_id: User identifier (memory owner)
            agent_name: Optional agent name for scoping

        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()
        try:
            query = session.query(MemoryModel).filter_by(key=key, user_id=user_id)

            if agent_name:
                query = query.filter_by(agent_name=agent_name)
            else:
                query = query.filter(MemoryModel.agent_name.is_(None))

            deleted = query.delete()
            session.commit()

            return deleted > 0

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete memory (key={key}, user_id={user_id}): {e}")
            raise
        finally:
            session.close()

    def list_keys(
        self, user_id: str, agent_name: Optional[str] = None, limit: int = 100
    ) -> list[str]:
        """List all memory keys for a user.

        Args:
            user_id: User identifier
            agent_name: Optional agent name filter
            limit: Maximum results

        Returns:
            List of memory keys
        """
        session = self._get_session()
        try:
            query = session.query(MemoryModel.key).filter_by(user_id=user_id)

            if agent_name:
                query = query.filter_by(agent_name=agent_name)

            query = query.order_by(MemoryModel.updated_at.desc()).limit(limit)

            return [row[0] for row in query.all()]

        except Exception as e:
            logger.error(f"Failed to list keys for user_id={user_id}: {e}")
            raise
        finally:
            session.close()

    def count(
        self,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> int:
        """Count memories.

        Args:
            user_id: Optional user identifier filter
            agent_name: Optional agent name filter

        Returns:
            Number of memories matching the filters
        """
        session = self._get_session()
        try:
            query = session.query(MemoryModel)

            if user_id is not None:
                query = query.filter_by(user_id=user_id)

            if agent_name is not None:
                query = query.filter(
                    (MemoryModel.agent_name == agent_name)
                    | (MemoryModel.agent_name.is_(None))
                )

            count = query.count()
            return count

        except Exception as e:
            logger.error(f"Failed to count memories: {e}")
            raise
        finally:
            session.close()

    def fetch_all(
        self,
        user_id: str,
        agent_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Fetch all memories for a user (optionally scoped by agent).

        Args:
            user_id: User identifier (memory owner)
            agent_name: Optional agent name filter
            limit: Optional maximum number of results to return

        Returns:
            List of memory dictionaries ordered by updated_at descending

        Example:
            >>> backend = SQLAlchemyPersistentBackend(db_url="sqlite:///test.db")
            >>> memories = backend.fetch_all("user1", "agent1", limit=10)
            >>> len(memories)
            10
        """
        session = self._get_session()
        try:
            query = session.query(MemoryModel).filter_by(user_id=user_id)

            if agent_name is not None:
                # Include both agent-scoped AND global (agent_name IS NULL) memories
                # This matches the logic in recall() and search()
                query = query.filter(
                    (MemoryModel.agent_name == agent_name)
                    | (MemoryModel.agent_name.is_(None))
                )

            query = query.order_by(MemoryModel.updated_at.desc())

            if limit is not None:
                query = query.limit(limit)

            results: list[dict[str, Any]] = []
            for row in query.all():
                results.append(
                    {
                        "key": row.key,
                        "value": json.loads(row.value),
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                        "metadata": json.loads(row.memory_metadata) if row.memory_metadata else None,
                        "access_count": row.access_count if row.access_count is not None else 0,
                        "last_accessed_at": row.last_accessed_at,
                    }
                )

            logger.debug(f"Fetched {len(results)} memories for user_id={user_id}, agent_name={agent_name}")
            return results

        except Exception as e:
            logger.error(f"Failed to fetch_all for user_id={user_id}: {e}")
            raise
        finally:
            session.close()

    def search(
        self,
        query: str,
        user_id: str,
        agent_name: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search memories by key pattern (SQL LIKE).

        Args:
            query: Search pattern (will be wrapped with % for LIKE query)
            user_id: User identifier (memory owner)
            agent_name: Optional agent name filter
            limit: Maximum number of results to return

        Returns:
            List of memory dictionaries matching the pattern

        Example:
            >>> backend = SQLAlchemyPersistentBackend(db_url="sqlite:///test.db")
            >>> results = backend.search("session", "user1", "agent1", limit=5)
            >>> len(results) <= 5
            True
        """
        session = self._get_session()
        try:
            # SQL LIKE pattern matching (case-insensitive on PostgreSQL via ILIKE)
            pattern = f"%{query}%"

            query_obj = session.query(MemoryModel).filter(
                MemoryModel.user_id == user_id,
                MemoryModel.key.ilike(pattern)  # Case-insensitive LIKE
            )

            # Agent name filtering with global fallback
            if agent_name is not None:
                query_obj = query_obj.filter(
                    (MemoryModel.agent_name == agent_name)
                    | (MemoryModel.agent_name.is_(None))
                )

            query_obj = query_obj.order_by(MemoryModel.updated_at.desc()).limit(limit)

            results: list[dict[str, Any]] = []
            for row in query_obj.all():
                results.append(
                    {
                        "key": row.key,
                        "value": json.loads(row.value),
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                        "metadata": json.loads(row.memory_metadata) if row.memory_metadata else None,
                        "access_count": row.access_count if row.access_count is not None else 0,
                        "last_accessed_at": row.last_accessed_at,
                    }
                )

            logger.debug(
                f"Search found {len(results)} results for query='{query}', "
                f"user_id={user_id}, agent_name={agent_name}"
            )
            return results

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connection and cleanup resources."""
        try:
            self.engine.dispose()
            logger.info("Closed SQLAlchemyPersistentBackend")
        except Exception as e:
            logger.error(f"Error closing backend: {e}")
