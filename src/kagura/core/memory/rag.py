"""Vector-based semantic memory search using ChromaDB.

This module provides RAG (Retrieval-Augmented Generation) capabilities
for semantic memory search using vector embeddings.
"""

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from kagura.config.paths import get_cache_dir

# ChromaDB (lightweight, local vector DB)
try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

if TYPE_CHECKING:
    from chromadb.types import Where  # type: ignore


class MemoryRAG:
    """Vector-based semantic memory search.

    Uses ChromaDB for efficient semantic search over stored memories.
    Memories are automatically embedded and indexed for similarity search.

    Example:
        >>> rag = MemoryRAG(collection_name="my_memories")
        >>> rag.store("Python is a programming language", metadata={"type": "fact"})
        >>> results = rag.recall("What is Python?", top_k=1)
        >>> print(results[0]["content"])
        'Python is a programming language'
    """

    def __init__(
        self,
        collection_name: str = "kagura_memory",
        persist_dir: Optional[Path] = None,
    ) -> None:
        """Initialize RAG memory.

        Args:
            collection_name: Name for the vector collection
            persist_dir: Directory for persistent storage

        Raises:
            ImportError: If ChromaDB is not installed
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(f"MemoryRAG init: collection={collection_name}, dir={persist_dir}")

        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB not installed. Install with: pip install chromadb"
            )

        persist_dir = persist_dir or get_cache_dir() / "chromadb"
        persist_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"MemoryRAG: Creating ChromaDB client at {persist_dir}")

        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        logger.debug("MemoryRAG: ChromaDB client created")

        logger.debug(f"MemoryRAG: Getting/creating collection '{collection_name}'")
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )
        logger.debug(f"MemoryRAG: Collection '{collection_name}' ready")

    def store(
        self,
        content: str,
        user_id: str,
        metadata: Optional[dict[str, Any]] = None,
        agent_name: Optional[str] = None,
    ) -> str:
        """Store memory with embedding.

        Args:
            content: Content to store
            user_id: User identifier (memory owner)
            metadata: Optional metadata
            agent_name: Optional agent name for scoping

        Returns:
            Content hash (unique ID)
        """
        # Generate unique ID from content hash + user_id for uniqueness
        unique_str = f"{user_id}:{content}"
        content_hash = hashlib.sha256(unique_str.encode()).hexdigest()[:16]

        full_metadata = metadata or {}
        full_metadata["user_id"] = user_id
        if agent_name:
            full_metadata["agent_name"] = agent_name

        self.collection.add(
            ids=[content_hash],
            documents=[content],
            metadatas=[full_metadata] if full_metadata else None,
        )

        return content_hash

    def recall(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        agent_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Semantic search for memories using vector similarity.

        Performs cosine similarity search in the vector space to find
        the most semantically similar memories to the query.

        Args:
            query: Search query (will be embedded automatically by ChromaDB)
            user_id: User identifier (filter by memory owner)
            top_k: Number of results to return (sorted by similarity)
            agent_name: Optional agent name filter (for agent-scoped search)

        Returns:
            List of memory dictionaries, each containing:
            - content: Original memory text
            - distance: Cosine distance (lower = more similar)
            - metadata: Optional metadata dict

        Note:
            ChromaDB handles query embedding internally using the default
            sentence-transformers model. Distance range: 0.0 (identical)
            to 2.0 (opposite).

        Example:
            >>> rag.store("Python is a programming language", user_id="jfk")
            >>> results = rag.recall("What is Python?", user_id="jfk", top_k=1)
            >>> print(results[0]["content"])
            'Python is a programming language'
        """
        # Build metadata filter for user and agent scoping
        # ChromaDB requires $and for multiple conditions
        where: "Where | None" = None
        if agent_name:
            where = {"$and": [{"user_id": user_id}, {"agent_name": agent_name}]}
        else:
            where = {"user_id": user_id}

        # Query ChromaDB collection
        # Returns: {"documents": [[...]], "distances": [[...]], "metadatas": [[...]]}
        # Note: Results are nested lists (batch query support)
        results = self.collection.query(
            query_texts=[query], n_results=top_k, where=where
        )

        # Parse and flatten ChromaDB results
        memories = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                memories.append(
                    {
                        "id": results["ids"][0][i],  # ChromaDB content hash
                        "content": doc,
                        "distance": results["distances"][0][i],
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else None
                        ),
                    }
                )

        return memories

    def delete_all(self, agent_name: Optional[str] = None) -> None:
        """Delete all memories.

        Args:
            agent_name: Optional agent name filter (deletes only that agent's memories)
        """
        if agent_name:
            # Delete by agent - query and delete
            results = self.collection.get(where={"agent_name": agent_name})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
        else:
            # Delete entire collection
            self.client.delete_collection(self.collection.name)
            # Recreate collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name, metadata={"hnsw:space": "cosine"}
            )

    def count(self, agent_name: Optional[str] = None) -> int:
        """Count stored memories.

        Args:
            agent_name: Optional agent name filter

        Returns:
            Number of memories
        """
        if agent_name:
            results = self.collection.get(where={"agent_name": agent_name})
            return len(results["ids"])
        else:
            return self.collection.count()

    def __repr__(self) -> str:
        """String representation."""
        return f"MemoryRAG(collection={self.collection.name}, count={self.count()})"
