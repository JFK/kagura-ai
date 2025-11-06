"""Vector-based semantic memory search using ChromaDB.

This module provides RAG (Retrieval-Augmented Generation) capabilities
for semantic memory search using vector embeddings.

Features:
- Semantic chunking for long documents (v4.1.0+)
- Automatic chunk management with parent_id linking
- Backward compatible API (transparent chunking)
"""

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from kagura.config.paths import get_cache_dir

if TYPE_CHECKING:
    from kagura.config.memory_config import ChunkingConfig
    from kagura.core.memory.semantic_chunker import SemanticChunker

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
        chunking_config: Optional["ChunkingConfig"] = None,
    ) -> None:
        """Initialize RAG memory with optional semantic chunking.

        Args:
            collection_name: Name for the vector collection
            persist_dir: Directory for persistent storage
            chunking_config: Semantic chunking configuration (v4.1.0+)
                            If None, chunking is disabled

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

        # Semantic chunking support (lazy-loaded)
        self._chunker: Optional["SemanticChunker"] = None
        self._chunking_config = chunking_config
        logger.debug(
            f"MemoryRAG: Chunking {'enabled' if chunking_config and chunking_config.enabled else 'disabled'}"
        )

    @property
    def chunker(self) -> Optional["SemanticChunker"]:
        """Lazy-load semantic chunker only when needed.

        Returns:
            SemanticChunker instance if chunking is enabled and available,
            None otherwise

        Note:
            Automatically disables chunking if langchain-text-splitters not installed.
        """
        if self._chunker is None and self._chunking_config and self._chunking_config.enabled:
            import logging

            logger = logging.getLogger(__name__)

            try:
                from kagura.core.memory.semantic_chunker import SemanticChunker

                self._chunker = SemanticChunker(
                    max_chunk_size=self._chunking_config.max_chunk_size,
                    overlap=self._chunking_config.overlap,
                )
                logger.debug(
                    f"MemoryRAG: SemanticChunker initialized "
                    f"(max_chunk_size={self._chunking_config.max_chunk_size}, "
                    f"overlap={self._chunking_config.overlap})"
                )
            except ImportError:
                logger.warning(
                    "langchain-text-splitters not installed, chunking disabled. "
                    "Install with: pip install langchain-text-splitters"
                )
                # Disable to avoid repeated import attempts
                self._chunking_config.enabled = False

        return self._chunker

    def store(
        self,
        content: str,
        user_id: str,
        metadata: Optional[dict[str, Any]] = None,
        agent_name: Optional[str] = None,
    ) -> str:
        """Store memory with optional automatic semantic chunking.

        For long documents (>= min_chunk_size), automatically splits into
        semantically coherent chunks for improved RAG precision.

        Args:
            content: Content to store (automatically chunked if enabled and long)
            user_id: User identifier (memory owner)
            metadata: Optional metadata (preserved across all chunks)
            agent_name: Optional agent name for scoping

        Returns:
            Parent document ID (string)

            Use this ID to:
            - Track the logical document in your application
            - Delete all chunks: collection.delete(where={"parent_id": id})
            - Reconstruct: collection.get(where={"parent_id": id})

        Note:
            Chunking is transparent to most use cases:
            - recall() naturally finds relevant chunks
            - Chunks include overlap for context preservation
            - Original metadata preserved in all chunks
            - If content < min_chunk_size, stored as single document (backward compat)

        Example:
            >>> # Short text - stored as single document
            >>> id1 = rag.store("Short text", user_id="jfk")
            >>> # Long text - automatically chunked
            >>> id2 = rag.store("Very long document..." * 100, user_id="jfk")
        """
        import logging

        logger = logging.getLogger(__name__)

        # Generate parent ID (stable identifier for the whole document)
        # Use first 100 chars for stability across similar content
        unique_str = f"{user_id}:{content[:100] if len(content) > 100 else content}"
        parent_id = hashlib.sha256(unique_str.encode()).hexdigest()[:16]

        # Prepare base metadata (applied to all chunks or single document)
        base_metadata = metadata or {}
        base_metadata["user_id"] = user_id
        if agent_name:
            base_metadata["agent_name"] = agent_name

        # Determine if chunking should be applied
        should_chunk = (
            self._chunking_config
            and self._chunking_config.enabled
            and len(content) >= self._chunking_config.min_chunk_size
            and self.chunker is not None  # Lazy-loaded, None if import failed
        )

        if not should_chunk:
            # Original behavior: store as single document
            logger.debug("Storing as single document (chunking disabled or content too short)")
            self.collection.add(
                ids=[parent_id],
                documents=[content],
                metadatas=[base_metadata] if base_metadata else None,
            )
            return parent_id

        # NEW: Chunk the content for improved precision
        # Type guard: should_chunk=True guarantees these are not None
        assert self._chunking_config is not None
        assert self.chunker is not None

        logger.debug(
            f"Chunking content ({len(content)} chars) with "
            f"max_chunk_size={self._chunking_config.max_chunk_size}"
        )

        chunks_with_metadata = self.chunker.chunk_with_metadata(
            text=content, source=base_metadata.get("file_path", "unknown")
        )

        # Prepare batch data for ChromaDB
        chunk_ids = []
        chunk_docs = []
        chunk_metadatas = []

        for chunk_meta in chunks_with_metadata:
            # Generate chunk-specific ID: parent_id + index
            chunk_id = f"{parent_id}_chunk_{chunk_meta.chunk_index:03d}"
            chunk_ids.append(chunk_id)
            chunk_docs.append(chunk_meta.content)

            # Enrich metadata with chunk information
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update(
                {
                    "parent_id": parent_id,
                    "chunk_index": chunk_meta.chunk_index,
                    "total_chunks": chunk_meta.total_chunks,
                    "is_chunk": True,
                    "chunk_source": chunk_meta.source,
                    "start_char": chunk_meta.start_char,
                    "end_char": chunk_meta.end_char,
                }
            )
            chunk_metadatas.append(chunk_metadata)

        # Batch insert all chunks to ChromaDB
        logger.debug(
            f"Storing {len(chunk_ids)} chunks (parent_id={parent_id}, "
            f"avg_chunk_size={len(content) // len(chunk_ids)} chars)"
        )

        self.collection.add(
            ids=chunk_ids, documents=chunk_docs, metadatas=chunk_metadatas
        )

        return parent_id

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
