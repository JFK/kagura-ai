"""Qdrant-based backend for RAG (Retrieval-Augmented Generation).

Issue #554 - Cloud-Native Infrastructure Migration (Phase 3)

Production-ready vector database backend using Qdrant.
Supports both local Qdrant (Docker) and Qdrant Cloud with singleton pattern.
"""

import hashlib
import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Singleton Qdrant client cache (shared across all instances)
_qdrant_client_cache: dict[str, Any] = {}


class QdrantRAG:
    """Qdrant-based RAG backend for semantic memory search.

    Production alternative to ChromaDB with better scalability and performance.
    Uses singleton pattern for Qdrant client connection pooling.

    Args:
        qdrant_url: Qdrant server URL (e.g., http://localhost:6333)
        collection_name: Collection name for vector storage (default: "kagura_memory")
        embedding_function: Callable that generates embeddings
        embedding_dim: Embedding vector dimension (default: 1024 for E5-large)

    Example:
        >>> # Local Qdrant (Docker)
        >>> rag = QdrantRAG(qdrant_url="http://localhost:6333")
        >>>
        >>> # Qdrant Cloud
        >>> rag = QdrantRAG(
        ...     qdrant_url="https://xyz.qdrant.io",
        ...     api_key="your-api-key"
        ... )
        >>>
        >>> # Add documents
        >>> rag.add_documents(["Python is great", "I love AI"])
        >>>
        >>> # Search
        >>> results = rag.search("programming language", k=5)

    Note:
        Multiple instances with the same qdrant_url will share a single client
        (and connection pool) for efficiency.
    """

    def __init__(
        self,
        qdrant_url: str,
        collection_name: str = "kagura_memory",
        embedding_function: Optional[Any] = None,
        embedding_dim: int = 1024,  # E5-large default
        api_key: Optional[str] = None,
    ):
        """Initialize Qdrant RAG backend.

        Args:
            qdrant_url: Qdrant server URL
            collection_name: Collection name
            embedding_function: Embedding function (uses E5-large if None)
            embedding_dim: Embedding dimension
            api_key: Qdrant Cloud API key (optional)

        Raises:
            ImportError: If qdrant-client not installed
            ConnectionError: If unable to connect to Qdrant
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.api_key = api_key

        # Get or create shared Qdrant client (singleton pattern)
        self.client = self._get_or_create_qdrant_client(qdrant_url, api_key)

        # Setup embedding function
        if embedding_function:
            self.embedding_function = embedding_function
        else:
            # Use default E5-large embedder
            from kagura.config.memory_config import EmbeddingConfig
            from kagura.core.memory.embeddings import Embedder

            config = EmbeddingConfig()
            self.embedder = Embedder(config)

        # Initialize collection
        self._ensure_collection()

        logger.info(
            f"Initialized QdrantRAG "
            f"(collection={collection_name}, dim={embedding_dim})"
        )

    @staticmethod
    def _get_or_create_qdrant_client(qdrant_url: str, api_key: Optional[str] = None) -> Any:
        """Get or create Qdrant client (singleton pattern).

        Reuses existing client if already created for the same qdrant_url.
        This shares connection pool across all RAG instances.

        Args:
            qdrant_url: Qdrant server URL
            api_key: Optional API key for Qdrant Cloud

        Returns:
            QdrantClient instance (cached)

        Raises:
            ImportError: If qdrant-client not installed
            ConnectionError: If unable to connect to Qdrant
        """
        global _qdrant_client_cache

        # Use centralized resource manager for Qdrant client
        from kagura.core.resources import get_rag_client

        try:
            logger.debug(f"Acquiring Qdrant client for {qdrant_url}")
            client = get_rag_client(backend="qdrant")

            # Test connection
            client.get_collections()

            return client
        except ImportError:
            raise ImportError(
                "qdrant-client not installed. Install with: pip install qdrant-client"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Qdrant: {e}") from e

    def _ensure_collection(self) -> None:
        """Ensure collection exists with proper configuration.

        Creates collection if it doesn't exist.
        """
        from qdrant_client.models import Distance, VectorParams

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.debug(f"Qdrant collection exists: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise

    def add_documents(
        self,
        documents: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
        ids: Optional[list[str]] = None,
    ) -> list[str]:
        """Add documents to Qdrant collection.

        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs (auto-generated if None)

        Returns:
            List of document IDs

        Example:
            >>> rag = QdrantRAG(qdrant_url="http://localhost:6333")
            >>> ids = rag.add_documents(
            ...     ["Python is great", "I love AI"],
            ...     metadatas=[{"source": "doc1"}, {"source": "doc2"}]
            ... )
            >>> print(ids)  # ['doc_abc123', 'doc_def456']
        """
        from qdrant_client.models import PointStruct

        # Generate IDs if not provided (use UUID strings for Qdrant)
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Generate embeddings
        if hasattr(self, "embedder"):
            # Use Kagura Embedder (E5-large)
            embeddings = self.embedder.encode_passages(documents).tolist()
        elif self.embedding_function:
            # Use custom embedding function
            embeddings = self.embedding_function(documents)
        else:
            raise ValueError("No embedding function available")

        # Prepare metadatas
        if metadatas is None:
            metadatas = [{} for _ in documents]

        # Add text to metadata and filter None values
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            meta["text"] = doc
            meta["doc_id"] = ids[i]
            # Remove None values (Qdrant doesn't accept None in metadata)
            for key in list(meta.keys()):
                if meta[key] is None:
                    del meta[key]

        # Create points
        points = [
            PointStruct(
                id=doc_id,
                vector=embedding,
                payload=metadata,
            )
            for doc_id, embedding, metadata in zip(ids, embeddings, metadatas)
        ]

        # Upsert to Qdrant
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(f"Added {len(documents)} documents to Qdrant")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

        return ids

    def search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict[str, Any] | Any] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar documents.

        Args:
            query: Search query text
            k: Number of results to return
            filter: Optional metadata filter (dict or qdrant_client.models.Filter)

        Returns:
            List of dicts with 'text', 'score', 'metadata'

        Example:
            >>> results = rag.search("Python programming", k=3)
            >>> for result in results:
            ...     print(f"{result['score']:.3f}: {result['text']}")
        """
        # Generate query embedding
        if hasattr(self, "embedder"):
            query_embedding = self.embedder.encode_queries([query])[0].tolist()
        elif self.embedding_function and hasattr(self.embedding_function, "embed_query"):
            query_embedding = self.embedding_function.embed_query([query])[0]
        else:
            raise ValueError("No embedding function available for queries")

        # Search Qdrant
        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                query_filter=filter,  # type: ignore[arg-type]
            )

            # Format results
            results = []
            for hit in search_results:
                results.append({
                    "id": hit.id,
                    "text": hit.payload.get("text", ""),  # type: ignore[union-attr]
                    "score": hit.score,
                    "metadata": {
                        k: v
                        for k, v in hit.payload.items()  # type: ignore[union-attr]
                        if k not in ["text", "doc_id"]
                    },
                })

            logger.debug(f"Qdrant search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise

    def recall(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        agent_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Semantic search for memories (MemoryRAG-compatible interface).

        Wraps search() method to provide MemoryRAG-compatible interface
        for use with MemoryManager.recall_semantic().

        Args:
            query: Search query text
            user_id: User identifier (filter by memory owner)
            top_k: Number of results to return
            agent_name: Optional agent name filter

        Returns:
            List of memory dictionaries with:
            - content: Original memory text
            - distance: Similarity distance (lower = more similar)
            - metadata: Memory metadata dict

        Example:
            >>> rag = QdrantRAG(qdrant_url="http://localhost:6333")
            >>> results = rag.recall("Python programming", user_id="jfk", top_k=5)
            >>> print(results[0]["content"])
        """
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        # Build Qdrant Filter object (proper structure)
        conditions: list[Any] = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        if agent_name:
            conditions.append(
                FieldCondition(key="agent_name", match=MatchValue(value=agent_name))
            )

        qdrant_filter: Any = Filter(must=conditions)

        # Use existing search() method with proper Filter
        search_results = self.search(query, k=top_k, filter=qdrant_filter)

        # Convert to MemoryRAG-compatible format
        memories = []
        for result in search_results:
            memories.append({
                "id": str(result["id"]),
                "content": result["text"],
                "distance": 1.0 - result["score"],  # Convert score to distance
                "metadata": result["metadata"],
            })

        return memories

    def get_chunk_metadata(
        self, parent_id: str, chunk_index: Optional[int] = None, user_id: Optional[str] = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Get metadata for chunk(s) (stub implementation).

        Args:
            parent_id: Parent document ID
            chunk_index: Optional specific chunk index
            user_id: Optional user filter

        Returns:
            Chunk metadata dict or list of metadata dicts

        Note:
            Full implementation pending. For now, returns empty result.
            See MemoryRAG.get_chunk_metadata() for reference implementation.
        """
        logger.warning("QdrantRAG.get_chunk_metadata() not fully implemented yet")
        return {} if chunk_index is not None else []

    def get_chunk_context(
        self,
        parent_id: str,
        chunk_index: int,
        context_size: int = 1,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get neighboring chunks (stub implementation).

        Args:
            parent_id: Parent document ID
            chunk_index: Target chunk index
            context_size: Number of chunks before/after
            user_id: Optional user filter

        Returns:
            List of chunk dicts

        Note:
            Full implementation pending. For now, returns empty list.
            See MemoryRAG.get_chunk_context() for reference implementation.
        """
        logger.warning("QdrantRAG.get_chunk_context() not fully implemented yet")
        return []

    def get_full_document(
        self, parent_id: str, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Reconstruct complete document from chunks (stub implementation).

        Args:
            parent_id: Parent document ID
            user_id: Optional user filter

        Returns:
            Dict with full_text and metadata

        Note:
            Full implementation pending. For now, returns empty result.
            See MemoryRAG.get_full_document() for reference implementation.
        """
        logger.warning("QdrantRAG.get_full_document() not fully implemented yet")
        return {"full_text": "", "metadata": {}, "chunks": []}

    def delete_collection(self) -> None:
        """Delete entire collection.

        Warning:
            This deletes all documents in the collection!
        """
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise

    def store(
        self,
        content: str,
        user_id: str,
        metadata: Optional[dict[str, Any]] = None,
        agent_name: Optional[str] = None,
    ) -> str:
        """Store memory content with metadata.

        Wrapper around add_documents() to match MemoryRAG interface.
        Used by MemoryManager.remember() for unified API.

        Args:
            content: Content to store
            user_id: User identifier (memory owner)
            metadata: Optional metadata dict
            agent_name: Optional agent name for scoping

        Returns:
            Document ID (stable UUID based on user_id and content)

        Example:
            >>> rag = QdrantRAG(qdrant_url="http://localhost:6333")
            >>> doc_id = rag.store(
            ...     content="Python is great",
            ...     user_id="jfk",
            ...     metadata={"type": "fact"},
            ...     agent_name="coding-memory"
            ... )
        """
        # Generate stable document ID as UUID (Qdrant requirement)
        # Use hash to create deterministic UUID from content
        prefix_content = content[:100] if len(content) > 100 else content
        unique_str = f"{user_id}:{prefix_content}"
        hash_bytes = hashlib.sha256(unique_str.encode()).digest()[:16]
        doc_id = str(uuid.UUID(bytes=hash_bytes))

        # Prepare metadata
        full_metadata = metadata.copy() if metadata else {}
        full_metadata["user_id"] = user_id
        if agent_name:
            full_metadata["agent_name"] = agent_name

        # Remove None values (Qdrant doesn't accept None in metadata)
        full_metadata = {k: v for k, v in full_metadata.items() if v is not None}

        # Store via add_documents
        self.add_documents(
            documents=[content],
            metadatas=[full_metadata],
            ids=[doc_id],
        )

        logger.debug(f"Stored document {doc_id} for user {user_id}")
        return doc_id

    def count(self) -> int:
        """Get number of documents in collection.

        Returns:
            Number of documents
        """
        try:
            collection_info = self.client.get_collection(
                collection_name=self.collection_name
            )
            return collection_info.points_count
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return -1

    def close(self) -> None:
        """Close Qdrant connection.

        Note:
            Due to singleton pattern, this doesn't actually close the shared client.
            Connection will be closed when Python exits.
        """
        logger.debug("QdrantRAG.close() called (singleton client remains active)")
