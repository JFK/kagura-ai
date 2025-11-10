#!/usr/bin/env python3
"""Migrate Kagura AI data from SQLite/JSON to PostgreSQL.

Issue #554 - Cloud-Native Infrastructure Migration

Migrates:
1. GraphMemory: JSON file → PostgreSQL JSONB
2. Persistent Memory: SQLite → PostgreSQL

Usage:
    python scripts/migrate-to-postgres.py \\
        --database-url postgresql://localhost:5432/kagura \\
        --graph-json ~/.local/share/kagura/graph.json \\
        --sqlite-db ~/.local/share/kagura/memory.db

Environment variables:
    DATABASE_URL: PostgreSQL connection URL (alternative to --database-url)
"""

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def migrate_graph_memory(
    json_path: Path, database_url: str, user_id: str = "global"
) -> None:
    """Migrate GraphMemory from JSON file to PostgreSQL.

    Args:
        json_path: Path to graph.json file
        database_url: PostgreSQL connection URL
        user_id: User ID for the graph (default: "global")
    """
    logger.info(f"Migrating GraphMemory: {json_path} → PostgreSQL")

    # Check if JSON file exists
    if not json_path.exists():
        logger.warning(f"JSON file not found: {json_path}, skipping graph migration")
        return

    # Load graph from JSON
    logger.info(f"  Loading graph from {json_path}")
    import networkx as nx

    with open(json_path) as f:
        data = json.load(f)

    graph: nx.DiGraph = nx.node_link_graph(data, edges="links")  # type: ignore[assignment]

    logger.info(
        f"  Loaded graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges"
    )

    # Save to PostgreSQL
    logger.info(f"  Saving to PostgreSQL (user_id={user_id})")

    from kagura.core.graph.backends import PostgresBackend

    backend = PostgresBackend(database_url=database_url, user_id=user_id)

    try:
        backend.save(graph)
        logger.info("  ✅ GraphMemory migration successful")
    finally:
        backend.close()


def migrate_persistent_memory(sqlite_path: Path, database_url: str) -> None:
    """Migrate Persistent Memory from SQLite to PostgreSQL.

    Args:
        sqlite_path: Path to memory.db SQLite file
        database_url: PostgreSQL connection URL
    """
    logger.info(f"Migrating Persistent Memory: {sqlite_path} → PostgreSQL")

    # Check if SQLite file exists
    if not sqlite_path.exists():
        logger.warning(
            f"SQLite file not found: {sqlite_path}, skipping persistent memory migration"
        )
        return

    # Count records in SQLite
    with sqlite3.connect(sqlite_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM memories")
        total_count = cursor.fetchone()[0]

    logger.info(f"  Found {total_count} memories in SQLite")

    if total_count == 0:
        logger.info("  No memories to migrate")
        return

    # Load all memories from SQLite
    logger.info("  Loading memories from SQLite")
    with sqlite3.connect(sqlite_path) as conn:
        cursor = conn.execute(
            """
            SELECT key, value, user_id, agent_name, metadata,
                   access_count, last_accessed_at, created_at, updated_at
            FROM memories
            """
        )
        memories = cursor.fetchall()

    # Insert into PostgreSQL
    logger.info(f"  Inserting {len(memories)} memories into PostgreSQL")

    from kagura.core.memory.backends import SQLAlchemyPersistentBackend

    backend = SQLAlchemyPersistentBackend(database_url=database_url)

    try:
        from sqlalchemy import text

        session = backend._get_session()

        for i, row in enumerate(memories, 1):
            (
                key,
                value,
                user_id,
                agent_name,
                metadata,
                access_count,
                last_accessed_at,
                created_at,
                updated_at,
            ) = row

            # Insert using raw SQL for efficiency
            session.execute(
                text(
                    """
                    INSERT INTO memories
                        (key, value, user_id, agent_name, metadata,
                         access_count, last_accessed_at, created_at, updated_at)
                    VALUES
                        (:key, :value, :user_id, :agent_name, :metadata,
                         :access_count, :last_accessed_at, :created_at, :updated_at)
                    ON CONFLICT (user_id, key, COALESCE(agent_name, ''))
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        metadata = EXCLUDED.metadata,
                        updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "key": key,
                    "value": value,
                    "user_id": user_id,
                    "agent_name": agent_name,
                    "metadata": metadata,
                    "access_count": access_count or 0,
                    "last_accessed_at": last_accessed_at,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )

            if i % 100 == 0:
                logger.info(f"  Progress: {i}/{len(memories)} ({i*100//len(memories)}%)")

        session.commit()
        logger.info("  ✅ Persistent Memory migration successful")

    except Exception as e:
        session.rollback()
        logger.error(f"  ❌ Migration failed: {e}")
        raise
    finally:
        session.close()
        backend.close()


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate Kagura AI data from SQLite/JSON to PostgreSQL"
    )
    parser.add_argument(
        "--database-url",
        help="PostgreSQL connection URL (or set DATABASE_URL env var)",
    )
    parser.add_argument(
        "--graph-json",
        type=Path,
        help="Path to graph.json file (default: ~/.local/share/kagura/graph.json)",
    )
    parser.add_argument(
        "--sqlite-db",
        type=Path,
        help="Path to memory.db SQLite file (default: ~/.local/share/kagura/memory.db)",
    )
    parser.add_argument(
        "--graph-user-id",
        default="global",
        help="User ID for GraphMemory (default: global)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (validate but don't migrate)",
    )

    args = parser.parse_args()

    # Get database URL
    database_url = args.database_url or os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("--database-url or DATABASE_URL environment variable required")
        sys.exit(1)

    # Get default paths
    from kagura.config.paths import get_data_dir

    data_dir = get_data_dir()
    graph_json = args.graph_json or data_dir / "graph.json"
    sqlite_db = args.sqlite_db or data_dir / "memory.db"

    logger.info("=" * 60)
    logger.info("Kagura AI Migration Tool")
    logger.info("=" * 60)
    logger.info(f"Target PostgreSQL: {database_url.split('@')[-1]}")
    logger.info(f"GraphMemory JSON: {graph_json}")
    logger.info(f"Persistent Memory SQLite: {sqlite_db}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 60)
    logger.info("")

    if args.dry_run:
        logger.info("DRY RUN MODE - No data will be migrated")
        logger.info("")

    # Migrate GraphMemory
    if graph_json.exists():
        if not args.dry_run:
            try:
                migrate_graph_memory(graph_json, database_url, args.graph_user_id)
            except Exception as e:
                logger.error(f"GraphMemory migration failed: {e}")
                sys.exit(1)
        else:
            logger.info(f"Would migrate GraphMemory from {graph_json}")
    else:
        logger.info(f"Skipping GraphMemory (file not found: {graph_json})")

    logger.info("")

    # Migrate Persistent Memory
    if sqlite_db.exists():
        if not args.dry_run:
            try:
                migrate_persistent_memory(sqlite_db, database_url)
            except Exception as e:
                logger.error(f"Persistent Memory migration failed: {e}")
                sys.exit(1)
        else:
            logger.info(f"Would migrate Persistent Memory from {sqlite_db}")
    else:
        logger.info(f"Skipping Persistent Memory (file not found: {sqlite_db})")

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ Migration Complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Verify data in PostgreSQL")
    logger.info("  2. Set environment variables:")
    logger.info("       export GRAPH_BACKEND=postgres")
    logger.info("       export PERSISTENT_BACKEND=postgres")
    logger.info(f"       export DATABASE_URL={database_url}")
    logger.info("  3. Test Kagura AI with PostgreSQL backend")
    logger.info("")


if __name__ == "__main__":
    main()
