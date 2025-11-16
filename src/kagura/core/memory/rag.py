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

# Document ID generation constants
_CONTENT_HASH_PREFIX_LENGTH = 100  # First N chars for stable hash generation
_DOCUMENT_ID_LENGTH = 16  # Hex characters for document ID (64-bit hash)

# Embedding dimension reference (for documentation and validation)
E5_LARGE_EMBEDDING_DIM = 1024  # intfloat/multilingual-e5-large
DEFAULT_EMBEDDING_DIM = 384  # ChromaDB default (all-MiniLM-L6-v2)
E5_LATENCY_OVERHEAD_MS_MIN = 20  # Minimum additional latency
E5_LATENCY_OVERHEAD_MS_MAX = 50  # Maximum additional latency

if TYPE_CHECKING:
    from kagura.config.memory_config import ChunkingConfig, EmbeddingConfig
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


def _sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Remove None values from metadata dict for ChromaDB compatibility.

    ChromaDB's Rust bindings do not accept None values in metadata.
    This function recursively removes all None values.

    Args:
        metadata: Original metadata dictionary

    Returns:
        Sanitized metadata with None values removed, or None if empty
    """
    if not metadata:
        return None

    sanitized = {k: v for k, v in metadata.items() if v is not None}
    return sanitized if sanitized else None


class ChromaDBEmbeddingFunction:
    """ChromaDB-compatible embedding function using Kagura's Embedder.

    Wraps Embedder class to provide ChromaDB's expected EmbeddingFunction protocol
    with E5-large model and query:/passage: prefix support.

    Implements ChromaDB's EmbeddingFunction protocol:
    - __call__(input) - Embed documents with 'passage:' prefix
    - embed_query(input) - Embed queries with 'query:' prefix
    - name() - Return model identifier
    - default_space, supported_spaces - Vector space configuration
    """

    def __init__(self, embedding_config: "EmbeddingConfig"):
        """Initialize embedding function.

        Args:
            embedding_config: Embedding configuration

        Raises:
            ImportError: If sentence-transformers not installed
        """
        from kagura.core.memory.embeddings import Embedder

        self.embedder = Embedder(embedding_config)
        self.config = embedding_config

    def __call__(self, input: list[str]) -> list[list[float]]:
        """Embed documents with 'passage:' prefix for E5-series models.

        Args:
            input: List of document strings to embed

        Returns:
            List of embedding vectors (list of floats)

        Note:
            Uses 'passage:' prefix as documents are being stored.
            Query time will use 'query:' prefix via embed_query().
        """
        # Embed with 'passage:' prefix for storage
        embeddings_array = self.embedder.encode_passages(input)

        # Convert numpy array to list for ChromaDB
        return embeddings_array.tolist()

    def embed_query(self, input: list[str]) -> list[list[float]]:
        """Embed queries with 'query:' prefix for E5-series models.

        Args:
            input: List of query strings to embed

        Returns:
            List of embedding vectors (list of floats)

        Note:
            E5-series models REQUIRE 'query:' prefix for optimal search performance.
        """
        # Embed with 'query:' prefix for search
        embeddings_array = self.embedder.encode_queries(input)

        # Convert numpy array to list for ChromaDB
        return embeddings_array.tolist()

    def name(self) -> str:
        """Return embedding model identifier.

        Returns:
            Model name (e.g., 'intfloat/multilingual-e5-large')
        """
        return f"kagura-embedder-{self.config.model}"

    @property
    def default_space(self) -> str:
        """Default vector space for this embedding function.

        Returns:
            'cosine' (normalized embeddings use cosine similarity)
        """
        return "cosine"

    @property
    def supported_spaces(self) -> list[str]:
        """Supported vector spaces for this embedding function.

        Returns:
            List of supported spaces (cosine, l2, ip)
        """
        # E5 embeddings work best with cosine similarity
        # But also support L2 and inner product
        return ["cosine", "l2", "ip"]

    def is_legacy(self) -> bool:
        """Indicate this is not a legacy embedding function.

        Returns:
            False (uses modern ChromaDB API)
        """
        return False


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
        embedding_config: Optional["EmbeddingConfig"] = None,
    ) -> None:
        """Initialize RAG memory with optional semantic chunking and custom embeddings.

        Args:
            collection_name: Name for the vector collection
            persist_dir: Directory for persistent storage
            chunking_config: Semantic chunking configuration (v4.1.0+)
                            If None, chunking is disabled
            embedding_config: Embedding configuration (v4.2.0+)
                             If provided, uses E5-large with query:/passage: prefixes
                             If None, uses ChromaDB default (all-MiniLM-L6-v2)

        Raises:
            ImportError: If ChromaDB is not installed

        Note:
            E5-series models REQUIRE query:/passage: prefixes for optimal performance.
            Enabling E5 embeddings improves precision by +8-12% but increases:
            - Storage: {E5_LARGE_EMBEDDING_DIM}-dim vs {DEFAULT_EMBEDDING_DIM}-dim (3x larger)
            - Latency: +{E5_LATENCY_OVERHEAD_MS_MIN}-{E5_LATENCY_OVERHEAD_MS_MAX}ms (larger model)
            Requires re-indexing existing data for full benefit.
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
        logger.debug(f"MemoryRAG: Using ChromaDB client at {persist_dir}")

        # Use centralized resource manager for ChromaDB client
        from kagura.core.resources import get_rag_client

        self.client = get_rag_client(backend="chromadb", path=str(persist_dir))
        logger.debug("MemoryRAG: ChromaDB client acquired from resource manager")

        # Custom embedding function (E5-large with query:/passage: prefixes)
        self._embedding_config = embedding_config

        # Track if we're using custom embeddings or falling back to default
        using_custom_embeddings = False

        if embedding_config:
            # Use custom embedding config if provided
            try:
                embedding_function = ChromaDBEmbeddingFunction(embedding_config)
                using_custom_embeddings = True
                logger.debug(
                    f"MemoryRAG: Using custom embeddings (model={embedding_config.model}, "
                    f"dimension={embedding_config.dimension}, use_prefix={embedding_config.use_prefix})"
                )
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed, falling back to ChromaDB default embeddings. "
                    "Install with: pip install sentence-transformers"
                )
                try:
                    from chromadb.utils.embedding_functions import (  # type: ignore
                        DefaultEmbeddingFunction,
                    )
                except ImportError:
                    # Fallback for older ChromaDB versions (<0.4.0)
                    from chromadb.api.types import (
                        DefaultEmbeddingFunction,  # type: ignore
                    )

                embedding_function = DefaultEmbeddingFunction()  # type: ignore
                # Clear embedding_config since we're using default
                embedding_config = None
        else:
            # Use ChromaDB default (all-MiniLM-L6-v2) when no custom config
            logger.debug("MemoryRAG: Using ChromaDB default embeddings (all-MiniLM-L6-v2)")
            try:
                from chromadb.utils.embedding_functions import (  # type: ignore
                    DefaultEmbeddingFunction,
                )
            except ImportError:
                # Fallback for older ChromaDB versions (<0.4.0)
                from chromadb.api.types import DefaultEmbeddingFunction  # type: ignore

            embedding_function = DefaultEmbeddingFunction()  # type: ignore

        logger.debug(f"MemoryRAG: Getting/creating collection '{collection_name}'")

        # Determine expected embedding dimension based on actual embedding function
        # If we fell back to default due to ImportError, use DEFAULT_EMBEDDING_DIM
        use_custom_dim = embedding_config and using_custom_embeddings
        if use_custom_dim and embedding_config:
            expected_dim = embedding_config.dimension
        else:
            expected_dim = DEFAULT_EMBEDDING_DIM

        # Check if forced recreation is enabled (for CI/testing)
        import os
        force_recreate = os.getenv("KAGURA_FORCE_RECREATE_COLLECTIONS", "").lower() == "true"

        if force_recreate:
            logger.debug(f"MemoryRAG: Force recreation enabled, will delete existing collection '{collection_name}' if exists")

        # Try to get existing collection first (backward compatibility)
        collection_exists = False
        needs_recreation = force_recreate  # Force recreation if env var is set

        if not force_recreate:
            try:
                # IMPORTANT: Pass embedding_function when getting existing collection
                # Otherwise ChromaDB uses the old embedding function saved with the collection
                existing_collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=embedding_function,  # type: ignore
                )
                collection_exists = True

                # Check if dimension matches (avoid InvalidArgumentError)
                # Try to determine actual dimension from existing collection
                try:
                    actual_dim = None

                    # Method 1: Check existing embeddings via peek()
                    peek_result = existing_collection.peek(limit=1)
                    embeddings = peek_result.get("embeddings") if peek_result else None
                    if embeddings is not None and len(embeddings) > 0:
                        actual_dim = len(embeddings[0])

                    # Method 2: Try adding a test embedding to detect mismatch
                    if actual_dim is None:
                        test_id = "__dimension_test__"
                        try:
                            # Create a test embedding with expected dimension
                            test_embedding = [0.0] * expected_dim
                            # Try to add (will fail if dimension mismatches)
                            existing_collection.add(
                                ids=[test_id],
                                embeddings=[test_embedding],
                                metadatas=[{"test": True}],
                            )
                            # If successful, assume correct dimension
                            actual_dim = expected_dim
                        except Exception as add_error:
                            # Failed to add - likely dimension mismatch
                            needs_recreation = True
                            logger.warning(
                                f"MemoryRAG: Collection '{collection_name}' dimension test failed ({add_error}). "
                                "Recreating collection..."
                            )
                        finally:
                            # Always try to clean up test document, even if add failed
                            try:
                                existing_collection.delete(ids=[test_id])
                            except Exception:
                                # Ignore cleanup errors (document may not exist)
                                pass

                    # Compare dimensions if we determined actual_dim
                    if actual_dim is not None and actual_dim != expected_dim:
                        logger.warning(
                            f"MemoryRAG: Collection '{collection_name}' has dimension {actual_dim}, "
                            f"but expected {expected_dim}. Recreating collection..."
                        )
                        needs_recreation = True
                    elif actual_dim is not None:
                        logger.debug(
                            f"MemoryRAG: Using existing collection '{collection_name}' "
                            f"(dimension={actual_dim}, preserves existing embeddings)"
                        )
                except Exception as e:
                    # Could not determine dimension - log warning
                    logger.warning(
                        f"MemoryRAG: Could not verify collection dimension ({e}). "
                        "Collection may have incompatible dimension."
                    )

            except Exception:
                logger.debug(f"MemoryRAG: Collection '{collection_name}' does not exist")

        # Recreate collection if dimension mismatch
        if needs_recreation:
            try:
                self.client.delete_collection(name=collection_name)
                logger.debug(f"MemoryRAG: Deleted collection '{collection_name}' due to dimension mismatch")
                collection_exists = False
            except Exception as e:
                logger.error(f"MemoryRAG: Failed to delete collection: {e}")

        # Create collection if needed
        if not collection_exists or needs_recreation:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=embedding_function,  # type: ignore
            )
            embedding_type = "E5-large" if (embedding_config and embedding_config.use_prefix) else "default"
            logger.debug(
                f"MemoryRAG: Created new collection '{collection_name}' "
                f"(embeddings={embedding_type}, dimension={expected_dim})"
            )
        else:
            self.collection = existing_collection

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
        parent_id = self._generate_document_id(user_id, content)
        base_metadata = self._prepare_base_metadata(metadata, user_id, agent_name)

        if not self._should_chunk(content):
            return self._store_single_document(parent_id, content, base_metadata)

        return self._store_chunked_document(parent_id, content, base_metadata)

    def _generate_document_id(self, user_id: str, content: str) -> str:
        """Generate stable document ID from user_id and content.

        Uses first {_CONTENT_HASH_PREFIX_LENGTH} characters of content
        for stability across similar documents.

        Args:
            user_id: User identifier
            content: Document content

        Returns:
            {_DOCUMENT_ID_LENGTH}-character hex hash (stable identifier)
        """
        prefix_content = (
            content[:_CONTENT_HASH_PREFIX_LENGTH]
            if len(content) > _CONTENT_HASH_PREFIX_LENGTH
            else content
        )
        unique_str = f"{user_id}:{prefix_content}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:_DOCUMENT_ID_LENGTH]

    def _prepare_base_metadata(
        self,
        metadata: Optional[dict[str, Any]],
        user_id: str,
        agent_name: Optional[str],
    ) -> dict[str, Any]:
        """Prepare base metadata for document/chunks.

        Args:
            metadata: User-provided metadata
            user_id: User identifier
            agent_name: Optional agent name

        Returns:
            Metadata dict with user_id and agent_name added

        Note:
            ChromaDB 1.3+ only accepts str, int, float, bool, or None values.
            Lists and dicts are converted to JSON strings.
        """
        import json

        base_metadata = metadata.copy() if metadata else {}

        # Convert lists and dicts to JSON strings (ChromaDB 1.3+ requirement)
        for key, value in list(base_metadata.items()):
            if isinstance(value, (list, dict)):
                base_metadata[key] = json.dumps(value)

        base_metadata["user_id"] = user_id
        if agent_name:
            base_metadata["agent_name"] = agent_name
        return base_metadata

    def _should_chunk(self, content: str) -> bool:
        """Determine if content should be chunked.

        Args:
            content: Document content

        Returns:
            True if content should be chunked, False otherwise
        """
        return bool(
            self._chunking_config
            and self._chunking_config.enabled
            and len(content) >= self._chunking_config.min_chunk_size
            and self.chunker is not None
        )

    def _store_single_document(
        self, doc_id: str, content: str, metadata: dict[str, Any]
    ) -> str:
        """Store content as single document without chunking.

        Args:
            doc_id: Document ID
            content: Document content
            metadata: Document metadata

        Returns:
            Document ID
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(
            "Storing as single document (chunking disabled or content too short)"
        )
        # Sanitize metadata to remove None values (ChromaDB Rust bindings requirement)
        sanitized_metadata = _sanitize_metadata(metadata)
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[sanitized_metadata] if sanitized_metadata else None,
        )
        return doc_id

    def _store_chunked_document(
        self, parent_id: str, content: str, base_metadata: dict[str, Any]
    ) -> str:
        """Store content as multiple semantically coherent chunks.

        Args:
            parent_id: Parent document ID
            content: Document content to chunk
            base_metadata: Base metadata (applied to all chunks)

        Returns:
            Parent document ID
        """
        import logging

        logger = logging.getLogger(__name__)

        # Type narrowing: guaranteed by _should_chunk()
        assert self._chunking_config is not None
        assert self.chunker is not None

        logger.debug(
            f"Chunking content ({len(content)} chars) with "
            f"max_chunk_size={self._chunking_config.max_chunk_size}"
        )

        # Generate chunks with metadata
        chunks_with_metadata = self.chunker.chunk_with_metadata(
            text=content, source=base_metadata.get("file_path", "unknown")
        )

        # Prepare batch data
        chunk_data = self._prepare_chunk_batch(
            parent_id, chunks_with_metadata, base_metadata
        )

        logger.debug(
            f"Storing {len(chunk_data['ids'])} chunks (parent_id={parent_id}, "
            f"avg_chunk_size={len(content) // len(chunk_data['ids'])} chars)"
        )

        # Batch insert to ChromaDB
        self.collection.add(
            ids=chunk_data["ids"],
            documents=chunk_data["documents"],
            metadatas=chunk_data["metadatas"],
        )

        return parent_id

    def _prepare_chunk_batch(
        self,
        parent_id: str,
        chunks_with_metadata: list,
        base_metadata: dict[str, Any],
    ) -> dict[str, list]:
        """Prepare batch data for ChromaDB insertion.

        Args:
            parent_id: Parent document ID
            chunks_with_metadata: List of ChunkMetadata objects
            base_metadata: Base metadata to apply to all chunks

        Returns:
            Dict with ids, documents, and metadatas lists for batch insert
        """
        chunk_ids = []
        chunk_docs = []
        chunk_metadatas = []

        for chunk_meta in chunks_with_metadata:
            # Generate chunk-specific ID
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
            # Sanitize metadata to remove None values (ChromaDB Rust bindings requirement)
            sanitized_chunk_metadata = _sanitize_metadata(chunk_metadata)
            if sanitized_chunk_metadata:  # Only add if not empty after sanitization
                chunk_metadatas.append(sanitized_chunk_metadata)

        return {"ids": chunk_ids, "documents": chunk_docs, "metadatas": chunk_metadatas}

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
        # ChromaDB automatically uses embed_query() if custom embedding function provided
        # This applies 'query:' prefix for E5-series models (defined in ChromaDBEmbeddingFunction)
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

    def _build_chunks_from_results(
        self, results: Any  # GetResult type from ChromaDB
    ) -> list[dict[str, Any]]:
        """Build chunk list from ChromaDB query results.

        Extracts common chunk building logic to reduce duplication.

        Args:
            results: ChromaDB query results dict with ids, documents, metadatas

        Returns:
            List of chunks sorted by chunk_index
        """
        if not results["ids"]:
            return []

        chunks = []
        for i in range(len(results["ids"])):
            metadata = (
                results["metadatas"][i]
                if results["metadatas"] and i < len(results["metadatas"])
                else {}
            )
            chunk_index = metadata.get("chunk_index", 0)

            chunks.append({
                "id": results["ids"][i],
                "content": (
                    results["documents"][i]
                    if results["documents"] and i < len(results["documents"])
                    else ""
                ),
                "metadata": metadata,
                "chunk_index": chunk_index,
            })

        # Sort by chunk_index
        chunks.sort(key=lambda x: x["chunk_index"])
        return chunks

    def _get_chunks_by_parent(
        self, parent_id: str, user_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get all chunks for a parent document, sorted by chunk_index.

        Helper method to reduce duplication in chunk retrieval methods.

        Args:
            parent_id: Parent document ID
            user_id: Optional user filter

        Returns:
            List of chunks sorted by chunk_index
        """
        # Build where clause with proper $and operator if multiple conditions
        if user_id:
            where_clause: dict[str, Any] = {
                "$and": [{"parent_id": parent_id}, {"user_id": user_id}]
            }
        else:
            where_clause = {"parent_id": parent_id}

        results = self.collection.get(where=where_clause)
        return self._build_chunks_from_results(results)

    def _get_chunks_by_parent_in_range(
        self,
        parent_id: str,
        start_idx: int,
        end_idx: int,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get chunks for a parent document within a specific index range.

        More efficient than fetching all chunks when only a subset is needed.

        Args:
            parent_id: Parent document ID
            start_idx: Starting chunk index (inclusive)
            end_idx: Ending chunk index (exclusive)
            user_id: Optional user filter

        Returns:
            List of chunks sorted by chunk_index
        """
        # Build where clause with range filter
        base_conditions = [
            {"parent_id": parent_id},
            {"chunk_index": {"$gte": start_idx}},
            {"chunk_index": {"$lt": end_idx}},
        ]

        if user_id:
            base_conditions.append({"user_id": user_id})

        where_clause: dict[str, Any] = {"$and": base_conditions}

        results = self.collection.get(where=where_clause)
        return self._build_chunks_from_results(results)

    def get_chunk_context(
        self,
        parent_id: str,
        chunk_index: int,
        context_size: int = 1,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get neighboring chunks around a specific chunk.

        Args:
            parent_id: Parent document ID
            chunk_index: Index of the target chunk (0-indexed)
            context_size: Number of chunks before/after to retrieve (default: 1)
            user_id: Optional user filter

        Returns:
            List of chunks sorted by chunk_index, including target chunk and neighbors

        Example:
            >>> # Get chunk 5 with 1 neighbor before/after (chunks 4, 5, 6)
            >>> chunks = rag.get_chunk_context("doc123", 5, context_size=1)
            >>> print(len(chunks))  # 3 chunks
        """
        # Calculate range and use efficient range query
        start_idx = max(0, chunk_index - context_size)
        end_idx = chunk_index + context_size + 1

        return self._get_chunks_by_parent_in_range(parent_id, start_idx, end_idx, user_id)

    def get_full_document(
        self, parent_id: str, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Reconstruct complete document from chunks.

        Args:
            parent_id: Parent document ID
            user_id: Optional user filter

        Returns:
            Dict with:
                - full_content: Reconstructed document (chunks concatenated)
                - chunks: List of individual chunks with metadata
                - parent_id: Parent document ID
                - total_chunks: Total number of chunks

        Example:
            >>> doc = rag.get_full_document("doc123")
            >>> print(doc["full_content"])
            'Complete document text...'
            >>> print(doc["total_chunks"])
            12
        """
        chunks = self._get_chunks_by_parent(parent_id, user_id)

        if not chunks:
            return {
                "full_content": "",
                "chunks": [],
                "parent_id": parent_id,
                "total_chunks": 0,
                "error": "Document not found",
            }

        # Reconstruct full document
        full_content = "".join(c["content"] for c in chunks)

        return {
            "full_content": full_content,
            "chunks": chunks,
            "parent_id": parent_id,
            "total_chunks": len(chunks),
        }

    def get_chunk_metadata(
        self, parent_id: str, chunk_index: Optional[int] = None, user_id: Optional[str] = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Get metadata for chunk(s) without retrieving full content.

        Args:
            parent_id: Parent document ID
            chunk_index: Optional specific chunk index (if None, returns all chunks)
            user_id: Optional user filter

        Returns:
            If chunk_index specified: Single chunk metadata dict
            If chunk_index is None: List of all chunk metadata dicts

        Example:
            >>> # Get metadata for specific chunk
            >>> meta = rag.get_chunk_metadata("doc123", chunk_index=5)
            >>> print(meta["chunk_index"], meta["total_chunks"])
            5 12

            >>> # Get metadata for all chunks
            >>> all_meta = rag.get_chunk_metadata("doc123")
            >>> print(len(all_meta))
            12
        """
        chunks = self._get_chunks_by_parent(parent_id, user_id)

        if not chunks:
            return {} if chunk_index is not None else []

        # Extract metadata only (without content)
        metadata_list = [
            {"id": c["id"], "chunk_index": c["chunk_index"], "metadata": c["metadata"]}
            for c in chunks
        ]

        # Return specific or all
        if chunk_index is not None:
            for item in metadata_list:
                if item["chunk_index"] == chunk_index:
                    return item
            return {}  # Not found

        return metadata_list

    def __repr__(self) -> str:
        """String representation."""
        return f"MemoryRAG(collection={self.collection.name}, count={self.count()})"
