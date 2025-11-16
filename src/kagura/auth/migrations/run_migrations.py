"""Run database migrations for Kagura auth.

Issue #653 - PostgreSQL backend for roles and audit logs

Simple migration runner that executes SQL files in order.

Usage:
    python -m kagura.auth.migrations.run_migrations

    # Or programmatically:
    >>> from kagura.auth.migrations.run_migrations import run_migrations
    >>> run_migrations("postgresql://user:pass@localhost/kagura")
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def run_migrations(database_url: str | None = None) -> None:
    """Run all migrations in order.

    Args:
        database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)

    Raises:
        ValueError: If database_url not provided and DATABASE_URL not set
        Exception: If migration fails

    Example:
        >>> run_migrations("postgresql://kagura_admin:pass@localhost/kagura")
    """
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "database_url required. "
            "Provide as argument or set DATABASE_URL environment variable."
        )

    logger.info(f"Running migrations on {db_url.split('@')[-1]}...")

    # Get migrations directory
    migrations_dir = Path(__file__).parent

    # Find all .sql files
    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        logger.warning(f"No migration files found in {migrations_dir}")
        return

    # Execute migrations
    try:
        import psycopg2

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        for sql_file in sql_files:
            logger.info(f"Running migration: {sql_file.name}")
            sql = sql_file.read_text()

            try:
                cursor.execute(sql)
                conn.commit()
                logger.info(f"✓ {sql_file.name} completed")
            except Exception as e:
                logger.error(f"✗ {sql_file.name} failed: {e}")
                conn.rollback()
                raise

        cursor.close()
        conn.close()

        logger.info(f"✓ All {len(sql_files)} migrations completed successfully")

    except ImportError:
        logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
        raise
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def main():
    """CLI entry point."""
    import sys

    logging.basicConfig(level=logging.INFO)

    db_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DATABASE_URL")

    if not db_url:
        print("Usage: python -m kagura.auth.migrations.run_migrations [DATABASE_URL]")
        print("\nOr set DATABASE_URL environment variable")
        sys.exit(1)

    try:
        run_migrations(db_url)
        print("\n✓ Migrations completed successfully!")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
