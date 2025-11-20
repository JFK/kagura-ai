"""Centralized resource management for database, RAG, and authentication.

This module provides singleton resource managers to prevent redundant
connections and ensure consistent configuration across the application.

Issue #XXX: Refactor to centralize resource management
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qdrant_client import QdrantClient  # type: ignore
    from sqlalchemy import Engine

logger = logging.getLogger(__name__)


# ============================================================================
# Database Resource Management
# ============================================================================

_engine_cache: dict[str, "Engine"] = {}


def get_database_engine(database_url: str | None = None, create_tables: bool = True) -> "Engine":
    """Get or create shared SQLAlchemy database engine.

    This is the single source of truth for database connections.
    Uses connection pooling and caching to prevent redundant connections.

    Args:
        database_url: Database URL (defaults to env var or SQLite)
        create_tables: Whether to create tables if they don't exist

    Returns:
        SQLAlchemy Engine instance (cached singleton per URL)

    Example:
        >>> engine = get_database_engine()
        >>> with engine.connect() as conn:
        ...     result = conn.execute(text("SELECT COUNT(*) FROM memories"))
    """
    from sqlalchemy import create_engine, event

    from kagura.config.paths import get_data_dir

    # Determine database URL
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "")

    if not database_url or database_url == "sqlite":
        # Default to SQLite
        db_path = get_data_dir() / "memory.db"
        database_url = f"sqlite:///{db_path}"

    # Check cache
    if database_url in _engine_cache:
        logger.debug(f"Reusing cached database engine: {database_url[:50]}...")
        return _engine_cache[database_url]

    # Create new engine
    logger.info(f"Creating new database engine: {database_url[:50]}...")

    if database_url.startswith("sqlite"):
        # SQLite-specific configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_size=5,
            max_overflow=10,
        )

        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):  # type: ignore
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    else:
        # PostgreSQL-specific configuration
        engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
        )

    # Create tables if needed
    if create_tables:
        from kagura.core.memory.backends.persistent_sqlalchemy import Base

        Base.metadata.create_all(engine)

    # Cache and return
    _engine_cache[database_url] = engine
    return engine


def get_database_url() -> str:
    """Get the configured database URL.

    Returns:
        Database URL (from env var or default SQLite path)
    """
    database_url = os.getenv("DATABASE_URL", "")

    if not database_url or database_url == "sqlite":
        from kagura.config.paths import get_data_dir

        db_path = get_data_dir() / "memory.db"
        return f"sqlite:///{db_path}"

    return database_url


def is_postgres() -> bool:
    """Check if using PostgreSQL backend.

    Returns:
        True if PostgreSQL, False if SQLite
    """
    backend = os.getenv("PERSISTENT_BACKEND", "").lower()
    database_url = get_database_url()

    return backend == "postgres" or database_url.startswith("postgresql")


# ============================================================================
# RAG (Vector Database) Resource Management
# ============================================================================

_rag_client_cache: dict[str, Any] = {}


def get_rag_backend() -> str:
    """Get the configured RAG backend type.

    Returns:
        "qdrant", "chromadb", or "auto"
    """
    backend = os.getenv("PERSISTENT_BACKEND", "").lower()
    qdrant_url = os.getenv("QDRANT_URL", "")

    if backend == "qdrant" or qdrant_url:
        return "qdrant"
    else:
        return "chromadb"


def get_rag_client(
    backend: str | None = None,
    path: str | None = None,
    collection: str | None = None,
) -> Any:
    """Get or create shared RAG (vector database) client.

    Supports both ChromaDB (local) and Qdrant (cloud/local).
    Uses caching to prevent redundant connections.

    Args:
        backend: "chromadb", "qdrant", or None (auto-detect)
        path: Path for ChromaDB (defaults to cache_dir/chromadb)
        collection: Collection name (optional, for validation)

    Returns:
        ChromaDB PersistentClient or QdrantClient instance

    Example:
        >>> client = get_rag_client()
        >>> collections = client.list_collections()
    """
    # Auto-detect backend
    if backend is None:
        backend = get_rag_backend()

    if backend == "qdrant":
        return _get_qdrant_client()
    else:
        return _get_chromadb_client(path)


def _get_qdrant_client() -> "QdrantClient":
    """Get or create Qdrant client (internal).

    Returns:
        QdrantClient instance (cached singleton)
    """
    from qdrant_client import QdrantClient  # type: ignore

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY")

    cache_key = f"qdrant:{qdrant_url}"

    if cache_key in _rag_client_cache:
        logger.debug(f"Reusing cached Qdrant client: {qdrant_url}")
        return _rag_client_cache[cache_key]

    logger.info(f"Creating new Qdrant client: {qdrant_url}")

    client = QdrantClient(
        url=qdrant_url,
        api_key=api_key,
        timeout=10,
    )

    _rag_client_cache[cache_key] = client
    return client


def _get_chromadb_client(path: str | None = None) -> Any:
    """Get or create ChromaDB client (internal).

    Args:
        path: ChromaDB directory path (defaults to cache_dir/chromadb)

    Returns:
        ChromaDB PersistentClient instance (cached singleton per path)
    """
    import chromadb

    from kagura.config.paths import get_cache_dir

    if path is None:
        path = str(get_cache_dir() / "chromadb")

    cache_key = f"chromadb:{path}"

    if cache_key in _rag_client_cache:
        logger.debug(f"Reusing cached ChromaDB client: {path}")
        return _rag_client_cache[cache_key]

    logger.info(f"Creating new ChromaDB client: {path}")

    client = chromadb.PersistentClient(path=path)

    _rag_client_cache[cache_key] = client
    return client


def get_rag_collection_count() -> int:
    """Get total count of vectors across all RAG collections.

    Returns:
        Total number of vectors stored
    """
    backend = get_rag_backend()
    total_count = 0

    try:
        if backend == "qdrant":
            client = get_rag_client()
            collections = client.get_collections().collections

            for col in collections:
                try:
                    info = client.get_collection(col.name)
                    total_count += info.points_count or 0
                except Exception as e:
                    logger.warning(f"Failed to count Qdrant collection {col.name}: {e}")

        else:
            # ChromaDB: check multiple possible paths
            from kagura.config.paths import get_cache_dir, get_data_dir

            paths = [
                str(get_cache_dir() / "chromadb"),
                str(get_data_dir() / "chromadb"),
            ]

            for path_str in paths:
                try:
                    client = _get_chromadb_client(path_str)
                    for col in client.list_collections():
                        total_count += col.count()
                except Exception as e:
                    logger.debug(f"Failed to count ChromaDB at {path_str}: {e}")

    except Exception as e:
        logger.error(f"Failed to count RAG vectors: {e}")

    return total_count


# ============================================================================
# Authentication Resource Management
# ============================================================================


def get_user_id_from_request(request: Any = None, user: dict[str, Any] | None = None) -> str:
    """Extract user ID from request or authenticated user context.

    This is the single source of truth for user ID extraction.

    Args:
        request: FastAPI Request object (optional)
        user: Authenticated user dict from get_current_user_optional (optional)

    Returns:
        User ID string, or "system" if not authenticated

    Example:
        >>> user_id = get_user_id_from_request(user=user)
        >>> manager = MemoryManager(user_id=user_id)
    """
    # Priority 1: user dict from authentication
    if user and isinstance(user, dict):
        return user.get("sub", user.get("email", user.get("id", "system")))

    # Priority 2: request headers (legacy, deprecated)
    if request and hasattr(request, "headers"):
        user_id = request.headers.get("X-User-ID")
        if user_id:
            logger.warning("X-User-ID header is deprecated, use session auth instead")
            return user_id

    # Default: system user
    return "system"


def get_user_id_for_query(user: dict[str, Any] | None, allow_all_users: bool = True) -> str:
    """Get user ID for database queries.

    Args:
        user: Authenticated user dict (optional)
        allow_all_users: If True, return "" for admin view when not authenticated

    Returns:
        User ID string, or "" to query all users (admin view)
    """
    if user and isinstance(user, dict):
        return user.get("sub", user.get("email", ""))

    if allow_all_users:
        # Empty string = all users (admin view)
        return ""
    else:
        # Restrict to system user
        return "system"


# ============================================================================
# Cleanup and Lifecycle Management
# ============================================================================


def clear_resource_cache() -> None:
    """Clear all cached resources.

    Use this for testing or when configuration changes.
    """
    global _engine_cache, _rag_client_cache

    logger.info("Clearing all resource caches")

    # Close database engines
    for url, engine in _engine_cache.items():
        logger.debug(f"Disposing engine: {url[:50]}...")
        engine.dispose()

    _engine_cache.clear()
    _rag_client_cache.clear()


def get_resource_stats() -> dict[str, Any]:
    """Get statistics about cached resources.

    Returns:
        Dict with cache statistics
    """
    return {
        "database_engines": len(_engine_cache),
        "database_urls": list(_engine_cache.keys()),
        "rag_clients": len(_rag_client_cache),
        "rag_backends": list(_rag_client_cache.keys()),
    }
