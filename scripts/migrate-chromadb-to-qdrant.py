#!/usr/bin/env python3
"""Migrate Kagura AI RAG data from ChromaDB to Qdrant.

Issue #554 - Cloud-Native Infrastructure Migration (Phase 3)

Migrates vector embeddings and documents from ChromaDB to Qdrant.

Usage:
    python scripts/migrate-chromadb-to-qdrant.py \\
        --chromadb-path ~/.cache/kagura/chromadb \\
        --qdrant-url http://localhost:6333 \\
        --collection kagura_memory

Environment variables:
    QDRANT_URL: Qdrant server URL (alternative to --qdrant-url)
    QDRANT_API_KEY: Qdrant Cloud API key (for cloud deployments)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def migrate_collection(
    chromadb_path: Path,
    qdrant_url: str,
    collection_name: str,
    api_key: Optional[str] = None,
    batch_size: int = 100,
) -> None:
    """Migrate a collection from ChromaDB to Qdrant.

    Args:
        chromadb_path: Path to ChromaDB persistent storage directory
        qdrant_url: Qdrant server URL
        collection_name: Collection name to migrate
        api_key: Optional Qdrant API key
        batch_size: Batch size for migration (default: 100)

    Raises:
        ImportError: If chromadb or qdrant-client not installed
        ValueError: If collection doesn't exist in ChromaDB
    """
    logger.info(f"Migrating collection '{collection_name}': ChromaDB → Qdrant")

    # Load ChromaDB collection
    logger.info(f"  Loading ChromaDB from {chromadb_path}")

    try:
        import chromadb  # type: ignore
        from chromadb.config import Settings  # type: ignore

        chroma_client = chromadb.PersistentClient(
            path=str(chromadb_path),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get collection
        try:
            collection = chroma_client.get_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Collection '{collection_name}' not found in ChromaDB")
            raise ValueError(f"Collection not found: {e}") from e

        # Get all data from ChromaDB
        logger.info("  Fetching all documents from ChromaDB...")
        data = collection.get(include=["embeddings", "metadatas", "documents"])

        doc_count = len(data["ids"])  # type: ignore[arg-type]
        logger.info(f"  Found {doc_count} documents in ChromaDB")

        if doc_count == 0:
            logger.info("  No documents to migrate")
            return

    except ImportError:
        raise ImportError(
            "chromadb not installed. Install with: pip install chromadb"
        )

    # Setup Qdrant
    logger.info(f"  Connecting to Qdrant at {qdrant_url}")

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams

        qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=api_key,
            timeout=30,
            prefer_grpc=True,
        )

        # Test connection
        qdrant_client.get_collections()

    except ImportError:
        raise ImportError(
            "qdrant-client not installed. Install with: pip install qdrant-client"
        )
    except Exception as e:
        raise ConnectionError(f"Failed to connect to Qdrant: {e}") from e

    # Get embedding dimension from first embedding
    embedding_dim = len(data["embeddings"][0])  # type: ignore[index, arg-type]
    logger.info(f"  Detected embedding dimension: {embedding_dim}")

    # Create collection in Qdrant
    logger.info(f"  Creating Qdrant collection '{collection_name}'")

    try:
        # Check if collection exists
        collections = qdrant_client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)

        if exists:
            logger.warning(f"  Collection '{collection_name}' already exists in Qdrant")
            response = input("  Delete existing collection? (yes/no): ")
            if response.lower() == "yes":
                qdrant_client.delete_collection(collection_name=collection_name)
                logger.info("  Deleted existing collection")
            else:
                logger.info("  Keeping existing collection, migration aborted")
                return

        # Create new collection
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE,
            ),
        )
        logger.info("  Created Qdrant collection")

    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise

    # Migrate documents in batches
    logger.info(f"  Migrating {doc_count} documents (batch_size={batch_size})")

    ids = data["ids"]  # type: ignore[index]
    embeddings = data["embeddings"]  # type: ignore[index]
    documents = data["documents"]  # type: ignore[index]
    metadatas = data["metadatas"] or [{} for _ in ids]  # type: ignore[index]

    for i in range(0, doc_count, batch_size):
        batch_end = min(i + batch_size, doc_count)
        batch_ids = ids[i:batch_end]  # type: ignore[index]
        batch_embeddings = embeddings[i:batch_end]  # type: ignore[index]
        batch_documents = documents[i:batch_end]  # type: ignore[index]
        batch_metadatas = metadatas[i:batch_end]  # type: ignore[index]

        # Prepare points
        points = []
        for doc_id, embedding, document, metadata in zip(
            batch_ids, batch_embeddings, batch_documents, batch_metadatas
        ):
            # Add document text to metadata
            payload = metadata.copy() if metadata else {}
            payload["text"] = document
            payload["doc_id"] = doc_id

            points.append(
                PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        # Upload batch
        try:
            qdrant_client.upsert(
                collection_name=collection_name,
                points=points,
            )

            logger.info(
                f"  Progress: {batch_end}/{doc_count} "
                f"({batch_end*100//doc_count}%)"
            )

        except Exception as e:
            logger.error(f"Failed to upload batch {i}-{batch_end}: {e}")
            raise

    logger.info("  ✅ Migration complete")

    # Verify count
    final_count = qdrant_client.count(collection_name=collection_name).count
    logger.info(f"  Verified: {final_count} documents in Qdrant")

    if final_count != doc_count:
        logger.warning(
            f"  ⚠ Count mismatch: ChromaDB={doc_count}, Qdrant={final_count}"
        )


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate Kagura AI RAG data from ChromaDB to Qdrant"
    )
    parser.add_argument(
        "--chromadb-path",
        type=Path,
        help="Path to ChromaDB directory (default: ~/.cache/kagura/chromadb)",
    )
    parser.add_argument(
        "--qdrant-url",
        help="Qdrant server URL (or set QDRANT_URL env var)",
    )
    parser.add_argument(
        "--collection",
        default="kagura_memory",
        help="Collection name (default: kagura_memory)",
    )
    parser.add_argument(
        "--api-key",
        help="Qdrant Cloud API key (or set QDRANT_API_KEY env var)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for migration (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (validate but don't migrate)",
    )

    args = parser.parse_args()

    # Get Qdrant URL
    qdrant_url = args.qdrant_url or os.getenv("QDRANT_URL")
    if not qdrant_url:
        logger.error("--qdrant-url or QDRANT_URL environment variable required")
        sys.exit(1)

    # Get API key (optional)
    api_key = args.api_key or os.getenv("QDRANT_API_KEY")

    # Get ChromaDB path
    if args.chromadb_path:
        chromadb_path = args.chromadb_path
    else:
        from kagura.config.paths import get_cache_dir

        chromadb_path = get_cache_dir() / "chromadb"

    logger.info("=" * 60)
    logger.info("Kagura AI ChromaDB → Qdrant Migration Tool")
    logger.info("=" * 60)
    logger.info(f"ChromaDB path: {chromadb_path}")
    logger.info(f"Qdrant URL: {qdrant_url}")
    logger.info(f"Collection: {args.collection}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 60)
    logger.info("")

    if not chromadb_path.exists():
        logger.error(f"ChromaDB path not found: {chromadb_path}")
        sys.exit(1)

    if args.dry_run:
        logger.info("DRY RUN MODE - No data will be migrated")
        logger.info("")

        # Just validate ChromaDB
        try:
            import chromadb  # type: ignore

            client = chromadb.PersistentClient(path=str(chromadb_path))
            collection = client.get_collection(name=args.collection)
            count = collection.count()
            logger.info(f"ChromaDB collection '{args.collection}': {count} documents")
        except Exception as e:
            logger.error(f"Failed to validate ChromaDB: {e}")
            sys.exit(1)

        logger.info("Validation successful!")
        sys.exit(0)

    # Perform migration
    try:
        migrate_collection(
            chromadb_path=chromadb_path,
            qdrant_url=qdrant_url,
            collection_name=args.collection,
            api_key=api_key,
            batch_size=args.batch_size,
        )

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Migration Complete!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Set environment variable:")
        logger.info(f"       export VECTOR_BACKEND=qdrant")
        logger.info(f"       export QDRANT_URL={qdrant_url}")
        if api_key:
            logger.info(f"       export QDRANT_API_KEY=<your-api-key>")
        logger.info("  2. Test Kagura AI with Qdrant backend")
        logger.info("")

    except Exception as e:
        logger.error("")
        logger.error("=" * 60)
        logger.error(f"❌ Migration Failed: {e}")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
