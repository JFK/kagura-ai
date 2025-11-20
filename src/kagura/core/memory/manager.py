"""Memory manager for unified memory access.

Provides a unified interface to all memory types (context, persistent).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from kagura.config.memory_config import MemorySystemConfig
from kagura.core.compression import CompressionPolicy, ContextManager
from kagura.core.graph import GraphMemory

from .context import ContextMemory, Message
from .hybrid_search import rrf_fusion
from .lexical_search import BM25Searcher
from .persistent import PersistentMemory
from .recall_scorer import RecallScorer
from .reranker import MemoryReranker

if TYPE_CHECKING:
    from .rag import MemoryRAG


class MemoryManager:
    """Unified memory management interface.

    Combines context and persistent memory into a single API.
    """

    def __init__(
        self,
        user_id: str,
        agent_name: Optional[str] = None,
        persist_dir: Optional[Path] = None,
        max_messages: int = 100,
        enable_rag: Optional[bool] = None,
        enable_graph: bool = True,
        enable_compression: bool = True,
        compression_policy: Optional[CompressionPolicy] = None,
        model: str = "gpt-5-mini",
        memory_config: Optional[MemorySystemConfig] = None,
    ) -> None:
        """Initialize memory manager.

        Args:
            user_id: User identifier (memory owner) - REQUIRED.
                Will be normalized to lowercase for consistency.
            agent_name: Optional agent name for scoping
            persist_dir: Directory for persistent storage
            max_messages: Maximum messages in context
            enable_rag: Enable RAG (vector-based semantic search).
                If None (default), automatically enables if chromadb is available.
                Set to True/False to override auto-detection.
            enable_graph: Enable graph memory for relationships (default: True).
                Requires networkx package.
            enable_compression: Enable automatic context compression
            compression_policy: Compression configuration
            model: LLM model name for compression
            memory_config: Memory system configuration (v4.0.0a0+)
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(
            f"MemoryManager init: user={user_id}, agent={agent_name}, rag={enable_rag}"
        )

        # Normalize user_id to lowercase for case-insensitive matching
        self.user_id = user_id.lower()
        self.agent_name = agent_name

        # Load memory configuration (v4.0.0a0+)
        logger.debug("MemoryManager: Loading memory config")
        self.config = memory_config or MemorySystemConfig()

        # Initialize memory types
        logger.debug("MemoryManager: Creating ContextMemory")
        self.context = ContextMemory(max_messages=max_messages)

        db_path = None
        if persist_dir:
            db_path = persist_dir / "memory.db"

        logger.debug(f"MemoryManager: Creating PersistentMemory (db_path={db_path})")
        self.persistent = PersistentMemory(db_path=db_path)
        logger.debug("MemoryManager: PersistentMemory created")

        # Auto-detect chromadb availability if enable_rag is None
        if enable_rag is None:
            try:
                import chromadb  # noqa: F401

                enable_rag = True
            except ImportError:
                enable_rag = False

        # Optional: RAG (Unified)
        self.rag: Optional[MemoryRAG] = None  # Unified RAG (no scope distinction)
        if enable_rag:
            logger.debug("MemoryManager: Initializing RAG (enable_rag=True)")

            # Check if Qdrant is configured
            import os
            qdrant_url = os.getenv("QDRANT_URL")
            use_qdrant = qdrant_url is not None

            if use_qdrant:
                logger.info(f"MemoryManager: Using QdrantRAG backend (QDRANT_URL={qdrant_url})")
                from .backends.qdrant_rag import QdrantRAG

                collection_name = f"kagura_{agent_name}" if agent_name else "kagura_memory"

                # Get embedding dimension from config (supports OpenAI, E5, etc.)
                embedding_dim = self.config.embedding.dimension
                logger.info(f"MemoryManager: Using embedding dimension={embedding_dim} (provider={self.config.embedding.provider})")

                # Unified RAG (Qdrant) - no scope distinction
                logger.debug("MemoryManager: Creating unified QdrantRAG")
                self.rag = QdrantRAG(
                    collection_name=collection_name,
                    qdrant_url=qdrant_url,
                    api_key=os.getenv("QDRANT_API_KEY"),
                    embedding_dim=embedding_dim,
                )
                logger.info("MemoryManager: Unified QdrantRAG created")
            else:
                logger.info("MemoryManager: Using ChromaDB backend (no QDRANT_URL)")
                # Lazy import to avoid ChromaDB initialization on module load
                from .rag import MemoryRAG

                logger.debug("MemoryManager: MemoryRAG imported successfully")
                collection_name = f"kagura_{agent_name}" if agent_name else "kagura_memory"
                vector_dir = persist_dir / "vector_db" if persist_dir else None
                logger.debug(
                    f"MemoryManager: RAG collection={collection_name}, dir={vector_dir}"
                )

                # Unified RAG (with semantic chunking and E5 embeddings support) - no scope distinction
                logger.debug("MemoryManager: Creating unified MemoryRAG with chunking and E5 support")
                self.rag = MemoryRAG(
                    collection_name=collection_name,
                    persist_dir=vector_dir,
                    chunking_config=self.config.chunking if self.config else None,
                    embedding_config=self.config.embedding if self.config else None,
                )
                logger.debug("MemoryManager: Unified MemoryRAG created")
        else:
            logger.debug("MemoryManager: RAG disabled (enable_rag=False)")

        # Optional: Compression
        self.enable_compression = enable_compression
        self.context_manager: Optional[ContextManager] = None
        if enable_compression:
            logger.debug("MemoryManager: Creating ContextManager")
            self.context_manager = ContextManager(
                policy=compression_policy or CompressionPolicy(), model=model
            )
            logger.debug("MemoryManager: ContextManager created")

        # Optional: Graph Memory (Phase B - Issue #345)
        self.graph: Optional[GraphMemory] = None
        if enable_graph:
            try:
                logger.debug("MemoryManager: Creating GraphMemory")
                graph_path = persist_dir / "graph.json" if persist_dir else None
                self.graph = GraphMemory(persist_path=graph_path)
                logger.debug("MemoryManager: GraphMemory created")
            except ImportError:
                # NetworkX not installed, disable graph
                logger.debug("MemoryManager: GraphMemory disabled (no NetworkX)")
                self.graph = None

        # Optional: Reranker (v4.0.0a0 - Issue #418)
        logger.debug(f"MemoryManager: Reranker enabled={self.config.rerank.enabled}")
        self.reranker: Optional[MemoryReranker] = None

        if self.config.rerank.enabled:
            try:
                logger.debug("MemoryManager: Creating MemoryReranker")
                self.reranker = MemoryReranker(self.config.rerank)
                logger.debug("MemoryManager: MemoryReranker created")
            except ImportError:
                # sentence-transformers not installed
                logger.debug("MemoryManager: Reranker disabled (no transformers)")
                self.reranker = None

        # Optional: Recall Scorer (v4.0.0a0 - Issue #418)
        self.recall_scorer: Optional[RecallScorer] = None
        if self.config.enable_access_tracking:
            logger.debug("MemoryManager: Creating RecallScorer")
            self.recall_scorer = RecallScorer(self.config.recall_scorer)
            logger.debug("MemoryManager: RecallScorer created")

        # Optional: BM25 Lexical Searcher (v4.0.0a0 Phase 2 - Issue #418)
        self.lexical_searcher: Optional[BM25Searcher] = None
        if self.config.hybrid_search.enabled:
            try:
                logger.debug("MemoryManager: Creating BM25Searcher")
                self.lexical_searcher = BM25Searcher()
                logger.debug("MemoryManager: Rebuilding lexical index")
                self._rebuild_lexical_index()
                logger.debug("MemoryManager: BM25Searcher created")
            except ImportError:
                # rank-bm25 not installed
                logger.debug("MemoryManager: BM25Searcher disabled (no rank-bm25)")
                self.lexical_searcher = None

        logger.debug("MemoryManager: Initialization complete")

    # Context Memory
    def add_message(
        self, role: str, content: str, metadata: Optional[dict] = None
    ) -> None:
        """Add message to context.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        self.context.add_message(role, content, metadata)

    def get_context(self, last_n: Optional[int] = None) -> list[Message]:
        """Get conversation context.

        Args:
            last_n: Get last N messages only

        Returns:
            List of messages
        """
        return self.context.get_messages(last_n=last_n)

    async def get_llm_context(
        self, last_n: Optional[int] = None, compress: bool = True
    ) -> list[dict]:
        """Get context in LLM API format with optional compression.

        Args:
            last_n: Get last N messages only
            compress: Whether to apply compression (default: True)

        Returns:
            List of message dictionaries (compressed if enabled)

        Example:
            >>> context = await memory.get_llm_context(compress=True)
        """
        messages = self.context.to_llm_format(last_n=last_n)

        if compress and self.context_manager:
            # Apply compression
            messages = await self.context_manager.compress(messages)

        return messages

    def get_usage_stats(self) -> dict[str, Any]:
        """Get context usage statistics.

        Returns:
            Dict with compression stats

        Example:
            >>> stats = memory.get_usage_stats()
            >>> print(f"Usage: {stats['usage_ratio']:.1%}")
        """
        if not self.context_manager:
            return {"compression_enabled": False}

        messages = self.context.to_llm_format()
        usage = self.context_manager.get_usage(messages)

        return {
            "compression_enabled": True,
            "total_tokens": usage.total_tokens,
            "max_tokens": usage.max_tokens,
            "usage_ratio": usage.usage_ratio,
            "should_compress": usage.should_compress,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
        }

    def get_last_message(self, role: Optional[str] = None) -> Optional[Message]:
        """Get the last message.

        Args:
            role: Filter by role

        Returns:
            Last message or None
        """
        return self.context.get_last_message(role=role)

    def set_session_id(self, session_id: str) -> None:
        """Set session ID.

        Args:
            session_id: Session identifier
        """
        self.context.set_session_id(session_id)

    def get_session_id(self) -> Optional[str]:
        """Get session ID.

        Returns:
            Session ID or None
        """
        return self.context.get_session_id()

    # Helper methods for lexical search
    def _stringify_value(self, value: Any) -> str:
        """Convert value to string for indexing and metadata."""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)

    def _prepare_lexical_document(
        self, key: str, value: Any, metadata: Optional[dict]
    ) -> dict[str, Any]:
        """Prepare a document payload for BM25 indexing."""
        metadata_copy = metadata.copy() if metadata else {}
        tags = metadata_copy.get("tags", [])
        value_repr = self._stringify_value(value)

        content_parts = [key]
        if value_repr:
            content_parts.append(value_repr)
        content = ": ".join(content_parts)

        return {
            "id": key,
            "key": key,
            "value": value,
            "content": content,
            "metadata": metadata_copy,
            "scope": "persistent",
            "tags": tags,
        }

    def _rebuild_lexical_index(self) -> None:
        """Rebuild lexical search index from persistent memory."""
        if not self.lexical_searcher:
            return

        memories = self.persistent.fetch_all(self.user_id, self.agent_name)
        documents = [
            self._prepare_lexical_document(
                key=memory["key"],
                value=memory["value"],
                metadata=memory.get("metadata"),
            )
            for memory in memories
        ]

        if documents:
            self.lexical_searcher.index_documents(documents)
        else:
            self.lexical_searcher.clear()

    def _ensure_lexical_index(self) -> None:
        """Ensure lexical index is ready before searching."""
        if self.lexical_searcher and self.lexical_searcher.count() == 0:
            self._rebuild_lexical_index()

    # Persistent Memory
    def remember(self, key: str, value: Any, metadata: Optional[dict] = None) -> None:
        """Store persistent memory.

        Args:
            key: Memory key
            value: Value to store
            metadata: Optional metadata
        """
        # Store in SQLite
        self.persistent.store(key, value, self.user_id, self.agent_name, metadata)

        # Also index in RAG for semantic search
        if self.rag:
            # Create a copy to avoid modifying the original metadata dict
            full_metadata = metadata.copy() if metadata else {}
            value_str = self._stringify_value(value)
            full_metadata.update(
                {
                    "type": "persistent_memory",
                    "key": key,
                    "value": value_str,
                }
            )
            content = f"{key}: {value_str}"
            self.rag.store(
                content, self.user_id, full_metadata, self.agent_name
            )

        # Index for lexical search
        if self.lexical_searcher:
            document = self._prepare_lexical_document(
                key=key,
                value=value,
                metadata=metadata,
            )
            self.lexical_searcher.add_document(document)

        # Add to graph memory for relationship tracking (Issue #707)
        if self.graph:
            node_id = f"memory_{key}"
            node_data = {
                "key": key,
                "user_id": self.user_id,
                "agent_name": self.agent_name,
                "created_at": datetime.now().isoformat(),
            }

            # Add memory node
            self.graph.add_node(node_id, "memory", node_data)

            # Create user node if it doesn't exist
            user_node_id = f"user_{self.user_id}"
            if not self.graph.graph.has_node(user_node_id):
                self.graph.add_node(user_node_id, "user", {"user_id": self.user_id})

            # Link memory to user
            self.graph.add_edge(node_id, user_node_id, "learned_from", weight=1.0)

            # Add topic nodes from tags
            if metadata and "tags" in metadata:
                for tag in metadata["tags"]:
                    topic_id = f"topic_{tag}"
                    if not self.graph.graph.has_node(topic_id):
                        self.graph.add_node(topic_id, "topic", {"name": tag})
                    self.graph.add_edge(node_id, topic_id, "related_to", weight=1.0)

            # Persist to PostgreSQL/JSON backend
            self.graph.persist()

    def recall(
        self,
        key: str,
        *,
        include_metadata: bool = False,
        track_access: bool = False,
    ) -> Optional[Any]:
        """Recall persistent memory.

        Args:
            key: Memory key
            include_metadata: Return metadata along with the value if True
            track_access: Record access statistics if True

        Returns:
            Stored value or (value, metadata) when include_metadata is True.
        """
        return self.persistent.recall(
            key,
            self.user_id,
            self.agent_name,
            track_access=track_access,
            include_metadata=include_metadata,
        )

    def search_memory(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search persistent memory.

        Args:
            query: Search pattern (SQL LIKE pattern)
            limit: Maximum results

        Returns:
            List of memory dictionaries
        """
        return self.persistent.search(query, self.user_id, self.agent_name, limit)

    def forget(self, key: str) -> None:
        """Delete persistent memory.

        Args:
            key: Memory key to delete
        """
        # Delete from SQLite
        self.persistent.forget(key, self.user_id, self.agent_name)

        # Also delete from RAG
        if self.rag:
            # Find and delete RAG entries with matching key in metadata
            where: dict[str, Any] = {"key": key}
            if self.agent_name:
                where["agent_name"] = self.agent_name

            try:
                results = self.rag.collection.get(where=where)  # type: ignore
                if results["ids"]:
                    self.rag.collection.delete(ids=results["ids"])
            except Exception:
                # Silently fail if RAG deletion fails
                pass

        # Delete from lexical search index
        if self.lexical_searcher:
            self.lexical_searcher.remove_document(key)

        # Delete from graph memory (Issue #707)
        if self.graph:
            node_id = f"memory_{key}"
            if self.graph.graph.has_node(node_id):
                self.graph.graph.remove_node(node_id)
                self.graph.persist()

    def prune_old(self, older_than_days: int = 90) -> int:
        """Remove old memories.

        Args:
            older_than_days: Delete memories older than this many days

        Returns:
            Number of deleted memories
        """
        return self.persistent.prune(older_than_days, self.agent_name)

    # Session Management
    def save_session(self, session_name: str) -> None:
        """Save current session.

        Args:
            session_name: Name to save session under
        """
        session_data = {
            "context": self.context.to_dict(),
        }
        self.persistent.store(
            key=f"session:{session_name}",
            value=session_data,
            user_id=self.user_id,
            agent_name=self.agent_name,
            metadata={"type": "session"},
        )

    def load_session(self, session_name: str) -> bool:
        """Load saved session.

        Args:
            session_name: Name of session to load

        Returns:
            True if session was loaded successfully
        """
        session_data = self.persistent.recall(
            key=f"session:{session_name}",
            user_id=self.user_id,
            agent_name=self.agent_name,
        )

        if not session_data:
            return False

        # Restore context
        self.context.clear()
        context_data = session_data.get("context", {})
        if context_data.get("session_id"):
            self.context.set_session_id(context_data["session_id"])

        for msg_data in context_data.get("messages", []):
            self.context.add_message(
                role=msg_data["role"],
                content=msg_data["content"],
                metadata=msg_data.get("metadata"),
            )

        return True

    # RAG Memory
    def store_semantic(self, content: str, metadata: Optional[dict] = None) -> str:
        """Store content for semantic search.

        Args:
            content: Content to store
            metadata: Optional metadata

        Returns:
            Content hash (unique ID)

        Raises:
            ValueError: If RAG is not enabled
        """
        if not self.rag:
            raise ValueError(
                "RAG (semantic search) is not enabled.\n\n"
                "To enable RAG:\n"
                "  1. Install dependencies: pip install kagura-ai[ai]\n"
                "  2. Set enable_rag=True when creating MemoryManager\n"
                "  3. Or use memory_search (auto-enables RAG)\n\n"
                "💡 RAG allows semantic search like 'find conversations about authentication'"
            )
        return self.rag.store(content, self.user_id, metadata, self.agent_name)

    def recall_semantic(
        self, query: str, top_k: int = 5, scope: str = "all"
    ) -> list[dict[str, Any]]:
        """Semantic search for relevant memories.

        Args:
            query: Search query
            top_k: Number of results to return
            scope: Deprecated. Memory scope distinction has been removed.

        Returns:
            List of memory dictionaries with content, distance, and metadata

        Raises:
            ValueError: If RAG is not enabled
        """
        if not self.rag:
            raise ValueError(
                "RAG (semantic search) is not enabled.\n\n"
                "To enable RAG:\n"
                "  1. Install: pip install kagura-ai[ai]\n"
                "  2. Set enable_rag=True when creating MemoryManager\n\n"
                "💡 Semantic search finds memories by meaning, not exact keywords"
            )

        # Search unified RAG
        results = self.rag.recall(query, self.user_id, top_k, self.agent_name)

        return results

    def recall_semantic_with_rerank(
        self,
        query: str,
        top_k: Optional[int] = None,
        candidates_k: Optional[int] = None,
        scope: str = "all",
        enable_rerank: bool = True,
    ) -> list[dict[str, Any]]:
        """Semantic search with optional cross-encoder reranking.

        Two-stage retrieval for improved precision:
        1. Fast bi-encoder retrieval (candidates_k results)
        2. Accurate cross-encoder reranking (top_k final results)

        Args:
            query: Search query
            top_k: Number of final results (defaults to config.rerank.top_k)
            candidates_k: Number of candidates to retrieve before reranking
                (defaults to config.rerank.candidates_k)
            scope: Memory scope ("working", "persistent", "all")
            enable_rerank: If True and reranker available, rerank results

        Returns:
            List of memory dictionaries, reranked if enabled

        Raises:
            ValueError: If RAG is not enabled

        Example:
            >>> # Fast: retrieve 100, rerank to 20
            >>> results = memory.recall_semantic_with_rerank(
            ...     "Python async patterns",
            ...     top_k=20,
            ...     candidates_k=100
            ... )

        Note:
            Reranking improves precision but adds latency. For fast responses,
            set enable_rerank=False or use recall_semantic() directly.
        """
        # Use config defaults if not specified
        final_top_k = top_k or self.config.rerank.top_k
        retrieve_k = candidates_k or self.config.rerank.candidates_k

        # Stage 1: Fast bi-encoder retrieval
        candidates = self.recall_semantic(query, top_k=retrieve_k, scope=scope)

        # Stage 2: Cross-encoder reranking (if enabled and available)
        if enable_rerank and self.reranker and candidates:
            reranked = self.reranker.rerank(query, candidates, top_k=final_top_k)
            return reranked

        # Fallback: return top-k candidates without reranking
        return candidates[:final_top_k]

    def recall_hybrid(
        self,
        query: str,
        top_k: Optional[int] = None,
        candidates_k: Optional[int] = None,
        scope: str = "all",
        enable_rerank: bool = True,
    ) -> list[dict[str, Any]]:
        """Hybrid search combining vector and lexical search with RRF fusion.

        Three-stage retrieval for maximum precision:
        1. Vector search (semantic similarity)
        2. Lexical search (keyword matching with BM25)
        3. RRF fusion + optional cross-encoder reranking

        Args:
            query: Search query
            top_k: Number of final results (defaults to config.rerank.top_k)
            candidates_k: Number of candidates from each search
                (defaults to config.hybrid_search.candidates_k)
            scope: Memory scope ("working", "persistent", "all")
            enable_rerank: If True and reranker available, rerank fused results

        Returns:
            List of memory dictionaries, ranked by hybrid score

        Raises:
            ValueError: If RAG is not enabled or lexical searcher not available

        Example:
            >>> # Hybrid search with reranking
            >>> results = memory.recall_hybrid(
            ...     "Pythonの非同期処理",
            ...     top_k=20,
            ...     candidates_k=100
            ... )

        Note:
            Hybrid search is especially effective for:
            - Japanese text with kanji variants
            - Proper nouns (names, places, brands)
            - Technical terms and code
            - Queries requiring both semantic and exact matching
        """
        self._validate_hybrid_search_requirements()

        # Use config defaults if not specified
        final_top_k = top_k or self.config.rerank.top_k
        retrieve_k = candidates_k or self.config.hybrid_search.candidates_k

        # Retrieve candidates from both search methods
        vector_results, lexical_results = self._retrieve_hybrid_candidates(
            query, scope, retrieve_k
        )

        # Fuse results
        fused_results = self._fuse_search_results(
            vector_results, lexical_results, retrieve_k
        )

        # Stage 4: Cross-encoder reranking (optional)
        if enable_rerank and self.reranker and fused_results:
            fused_results = self.reranker.rerank(query, fused_results, top_k=final_top_k)

        # Apply composite scoring and return
        return self._apply_composite_scoring(fused_results, final_top_k)

    def _retrieve_hybrid_candidates(
        self, query: str, scope: str, retrieve_k: int
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Retrieve candidates from both vector and lexical search.

        Args:
            query: Search query
            scope: Memory scope ("all", "working", "persistent")
            retrieve_k: Number of candidates to retrieve from each search

        Returns:
            Tuple of (vector_results, lexical_results)
        """
        # Stage 1: Vector search (semantic)
        vector_results = self.recall_semantic(query, top_k=retrieve_k, scope=scope)

        # Add rank field for debugging (1-based)
        for rank, result in enumerate(vector_results, start=1):
            result["rank"] = rank

        # Stage 2: Lexical search (keyword)
        # TODO: Auto-index on document store (Issue #581)
        lexical_results: list[dict[str, Any]] = []
        if self.lexical_searcher and self.lexical_searcher.count() > 0:
            lexical_results = self.lexical_searcher.search(
                query,
                k=retrieve_k,
                min_score=self.config.hybrid_search.min_lexical_score,
            )

        return vector_results, lexical_results

    def _fuse_search_results(
        self,
        vector_results: list[dict[str, Any]],
        lexical_results: list[dict[str, Any]],
        retrieve_k: int,
    ) -> list[dict[str, Any]]:
        """Fuse vector and lexical results using RRF.

        Args:
            vector_results: Results from semantic search
            lexical_results: Results from BM25 search
            retrieve_k: Number of results to keep after fusion

        Returns:
            Fused results sorted by RRF score
        """
        # Stage 3: RRF fusion
        if lexical_results:
            # Combine using RRF
            fused_ids_scores = rrf_fusion(
                vector_results,
                lexical_results,
                k=self.config.hybrid_search.rrf_k,
            )

            # Rebuild results from fused IDs
            id_to_doc = {r["id"]: r for r in vector_results}
            id_to_doc.update({r["id"]: r for r in lexical_results})

            fused_results = []
            for doc_id, rrf_score in fused_ids_scores[:retrieve_k]:
                if doc_id in id_to_doc:
                    doc = id_to_doc[doc_id].copy()
                    doc["rrf_score"] = rrf_score
                    fused_results.append(doc)
            return fused_results
        else:
            # Fallback to vector-only if no lexical results
            return vector_results[:retrieve_k]

    def _apply_composite_scoring(
        self, results: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        """Apply RecallScorer composite scoring if enabled.

        Args:
            results: Search results to score
            top_k: Number of final results to return

        Returns:
            Results with composite scores, sorted and limited to top_k
        """
        if not self.recall_scorer or not results:
            return results[:top_k]

        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Applying RecallScorer to {len(results)} results")

        for result in results:
            metadata = result.get("metadata", {})

            # Parse created_at timestamp
            created_at = self._parse_created_at(metadata.get("created_at"))

            # Compute composite score for this result
            result["composite_score"] = self._compute_single_result_score(result, created_at)

        # Re-sort by composite score (higher is better)
        results.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)

        return results[:top_k]

    def _parse_created_at(self, created_at_raw: Any) -> datetime:
        """Parse created_at from various formats to datetime.

        Args:
            created_at_raw: Timestamp (datetime, ISO string, or None)

        Returns:
            Parsed datetime (defaults to current time if unavailable)
        """
        from datetime import datetime

        if isinstance(created_at_raw, str):
            try:
                return datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        elif isinstance(created_at_raw, datetime):
            return created_at_raw

        # Default to current time if unavailable
        return datetime.now()

    def _compute_single_result_score(
        self, result: dict[str, Any], created_at: datetime
    ) -> float:
        """Compute composite score for a single search result.

        Args:
            result: Search result dictionary
            created_at: Parsed creation timestamp

        Returns:
            Composite score (0.0-1.0+)
        """
        import logging

        logger = logging.getLogger(__name__)
        metadata = result.get("metadata", {})

        # Handle lexical-only results (no distance field from BM25)
        distance = result.get("distance")
        if distance is not None:
            semantic_sim = 1.0 - distance
        else:
            # Lexical-only hit - use RRF score as proxy (scaled down)
            rrf_score = result.get("rrf_score", 0.0)
            semantic_sim = rrf_score * 0.5

        try:
            # Type guard: recall_scorer is guaranteed non-None by caller check
            assert self.recall_scorer is not None
            return self.recall_scorer.compute_score(
                semantic_sim=semantic_sim,
                created_at=created_at,
                last_accessed=metadata.get("last_accessed"),
                access_count=metadata.get("access_count", 0),
                graph_distance=None,  # Graph integration in future
                importance=metadata.get("importance", 0.5),
            )
        except Exception as e:
            logger.warning(f"RecallScorer failed for {result.get('id')}: {e}")
            # Fallback to RRF score
            return result.get("rrf_score", 0.0)

    def _validate_hybrid_search_requirements(self) -> None:
        """Validate RAG and lexical searcher are available for hybrid search.

        Raises:
            ValueError: If RAG or lexical searcher not available
        """
        if not self.rag:
            raise ValueError(
                "RAG (semantic search) is not enabled.\n\n"
                "To enable RAG:\n"
                "  1. Install: pip install kagura-ai[ai]\n"
                "  2. Set enable_rag=True when creating MemoryManager\n\n"
                "💡 Semantic search finds memories by meaning, not exact keywords"
            )

        if not self.lexical_searcher:
            raise ValueError(
                "Lexical (keyword) search is not available.\n\n"
                "To enable lexical search:\n"
                "  Install: pip install rank-bm25\n"
                "  Or: pip install kagura-ai[ai] (includes all search features)\n\n"
                "💡 Lexical search uses BM25 algorithm for exact keyword matching"
            )

    def clear_all(self) -> None:
        """Clear all memory (context only).

        Note: Does not clear persistent memory or RAG memory.
        """
        self.context.clear()

    def get_storage_size(self) -> dict[str, float]:
        """Calculate storage size in MB.

        Returns disk usage for SQLite database and ChromaDB vectors.

        Returns:
            Dictionary with sqlite_mb, chromadb_mb, total_mb

        Example:
            >>> memory.get_storage_size()
            {'sqlite_mb': 2.4, 'chromadb_mb': 15.3, 'total_mb': 17.7}

        Note:
            Issue #411 - Storage size estimation for memory_stats
        """
        import os

        sizes = {"sqlite_mb": 0.0, "chromadb_mb": 0.0, "total_mb": 0.0}

        # Calculate SQLite database size
        if self.persistent and hasattr(self.persistent, "db_path"):
            db_path = self.persistent.db_path
            if db_path and os.path.exists(db_path):
                sizes["sqlite_mb"] = os.path.getsize(db_path) / (1024 * 1024)

        # Calculate ChromaDB storage size (if RAG enabled)
        if self.rag:
            # Use getattr to safely access private attribute
            chroma_dir = getattr(self.rag, "_persist_directory", None)
            if chroma_dir and os.path.exists(chroma_dir):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(chroma_dir):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                        except (OSError, FileNotFoundError):
                            pass  # Skip inaccessible files
                sizes["chromadb_mb"] = total_size / (1024 * 1024)

        sizes["total_mb"] = sizes["chromadb_mb"] + sizes["sqlite_mb"]
        return sizes

    def get_chunk_context(
        self,
        parent_id: str,
        chunk_index: int,
        context_size: int = 1,
    ) -> list[dict[str, Any]]:
        """Get neighboring chunks around a specific chunk.

        Args:
            parent_id: Parent document ID
            chunk_index: Index of the target chunk (0-indexed)
            context_size: Number of chunks before/after to retrieve (default: 1)

        Returns:
            List of chunks sorted by chunk_index, including target chunk and neighbors

        Raises:
            ValueError: If RAG is not enabled

        Example:
            >>> chunks = manager.get_chunk_context("doc123", chunk_index=5, context_size=1)
            >>> print(len(chunks))  # Returns chunks 4, 5, 6
        """
        if not self.rag:
            raise ValueError("RAG not enabled. Cannot retrieve chunk context.")

        return self.rag.get_chunk_context(
            parent_id=parent_id,
            chunk_index=chunk_index,
            context_size=context_size,
            user_id=self.user_id,
        )

    def get_full_document(self, parent_id: str) -> dict[str, Any]:
        """Reconstruct complete document from chunks.

        Args:
            parent_id: Parent document ID

        Returns:
            Dict with full_content, chunks, parent_id, total_chunks

        Raises:
            ValueError: If RAG is not enabled

        Example:
            >>> doc = manager.get_full_document("doc123")
            >>> print(doc["full_content"])
            >>> print(doc["total_chunks"])
        """
        if not self.rag:
            raise ValueError("RAG not enabled. Cannot retrieve full document.")

        return self.rag.get_full_document(parent_id=parent_id, user_id=self.user_id)

    def get_chunk_metadata(
        self, parent_id: str, chunk_index: Optional[int] = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Get metadata for chunk(s) without retrieving full content.

        Args:
            parent_id: Parent document ID
            chunk_index: Optional specific chunk index (if None, returns all chunks)

        Returns:
            Single chunk metadata dict or list of all chunk metadata dicts

        Raises:
            ValueError: If RAG is not enabled

        Example:
            >>> meta = manager.get_chunk_metadata("doc123", chunk_index=5)
            >>> all_meta = manager.get_chunk_metadata("doc123")
        """
        if not self.rag:
            raise ValueError("RAG not enabled. Cannot retrieve chunk metadata.")

        return self.rag.get_chunk_metadata(
            parent_id=parent_id, chunk_index=chunk_index, user_id=self.user_id
        )

    def __repr__(self) -> str:
        """String representation."""
        rag_count = self.rag.count(self.agent_name) if self.rag else 0
        return (
            f"MemoryManager("
            f"agent={self.agent_name}, "
            f"context={len(self.context)}, "
            f"persistent={self.persistent.count(self.user_id, self.agent_name)}, "
            f"rag={rag_count})"
        )
