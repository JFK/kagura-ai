"""Neural Memory Engine - main coordinator.

This is the primary interface for the neural memory system, orchestrating
all components: Hebbian learning, activation spreading, scoring, and decay.

Usage:
    engine = NeuralMemoryEngine(graph, rag, config)
    results = await engine.recall(user_id, query_text, top_k=10)
    await engine.store(user_id, text, kind="fact")
"""

import asyncio
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from kagura.core.graph.memory import GraphMemory
from kagura.core.memory.rag import MemoryRAG

from .activation import ActivationSpreader
from .co_activation import CoActivationTracker
from .config import NeuralMemoryConfig
from .decay import DecayManager
from .hebbian import HebbianLearner
from .models import (
    ActivationState,
    MemoryKind,
    NeuralMemoryNode,
    RecallResult,
    SourceKind,
)
from .scoring import UnifiedScorer

logger = logging.getLogger(__name__)


class NeuralMemoryEngine:
    """Neural Memory Network engine.

    Coordinates all neural memory components to provide adaptive,
    association-learning-based memory retrieval.
    """

    def __init__(
        self,
        graph: GraphMemory,
        rag: MemoryRAG,
        config: NeuralMemoryConfig | None = None,
    ) -> None:
        """Initialize neural memory engine.

        Args:
            graph: Graph memory instance
            rag: RAG memory instance (for vector search)
            config: Neural memory configuration (defaults to NeuralMemoryConfig())
        """
        self.graph = graph
        self.rag = rag
        self.config = config or NeuralMemoryConfig()

        # Initialize components
        self.activation_spreader = ActivationSpreader(graph, self.config)
        self.hebbian_learner = HebbianLearner(graph, self.config)
        self.co_activation_tracker = CoActivationTracker(self.config)
        self.decay_manager = DecayManager(graph, self.config)
        self.scorer = UnifiedScorer(self.config, self.activation_spreader)

        # Background task handle
        self._decay_task: asyncio.Task | None = None

        logger.info("NeuralMemoryEngine initialized")

    async def recall(
        self,
        user_id: str,
        query_text: str,
        query_embedding: list[float] | None = None,
        top_k: int = 10,
        enable_mmr: bool = True,
    ) -> list[RecallResult]:
        """Recall memories using neural memory retrieval.

        Workflow:
        1. Primary retrieval (RAG vector search)
        2. Activation spreading (graph association)
        3. Unified scoring (semantic + graph + temporal + trust)
        4. Optional MMR re-ranking (diversity)
        5. Co-activation tracking (for future Hebbian updates)
        6. Hebbian update (async)

        Args:
            user_id: User ID (SISA-compliant sharding)
            query_text: Query text
            query_embedding: Optional pre-computed query embedding
            top_k: Number of results to return
            enable_mmr: Whether to apply MMR diversity re-ranking

        Returns:
            List of RecallResult objects
        """
        # 1. Primary retrieval (RAG)
        candidates_k = self.config.max_candidates_k
        rag_results = await self._primary_retrieval(
            user_id=user_id,
            query_text=query_text,
            query_embedding=query_embedding,
            top_k=candidates_k,
        )

        if not rag_results:
            logger.warning(
                f"No RAG results for user {user_id}, query: {query_text[:50]}"
            )
            return []

        # Extract query embedding (from RAG or provided)
        if query_embedding is None:
            if not rag_results:
                raise ValueError(
                    "No RAG results available and no query embedding provided. "
                    "Cannot perform neural memory recall."
                )
            # TODO: Get embedding from RAG system
            # MemoryRAG should expose embedding function
            # For now, use first result's embedding as proxy (not ideal but safe)
            query_embedding = rag_results[0][0].embedding

        # 2. Get seed nodes for activation spreading
        seed_node_ids = [node.id for node, _ in rag_results[:10]]  # Top 10 as seeds

        # 3. Unified scoring
        scored_results = self.scorer.score_candidates(
            query_embedding=query_embedding,
            candidates=rag_results,
            seed_nodes=seed_node_ids,
            selected_nodes=None,  # First pass, no selection yet
        )

        # 4. Optional MMR re-ranking
        if enable_mmr and len(scored_results) > 1:
            scored_results = self.scorer.mmr_rerank(
                query_embedding=query_embedding,
                results=scored_results,
                lambda_param=0.5,  # Balance relevance and diversity
                top_k=top_k,
            )
        else:
            scored_results = scored_results[:top_k]

        # 5. Track co-activation
        activated_nodes = [
            ActivationState(node_id=result.node.id, activation=result.score)
            for result in scored_results
        ]
        self.co_activation_tracker.record_activation(user_id, activated_nodes)

        # 6. Queue Hebbian updates (async)
        nodes_dict = {result.node.id: result.node for result in scored_results}
        self.hebbian_learner.queue_update(user_id, activated_nodes, nodes_dict)

        # Schedule async update application
        asyncio.create_task(self._apply_hebbian_updates_async(user_id))

        # 7. Update node usage statistics
        for result in scored_results:
            await self._update_node_usage(user_id, result.node)

        logger.info(
            f"Recall complete for user {user_id}: {len(scored_results)} results "
            f"(query: {query_text[:50]})"
        )

        return scored_results

    async def store(
        self,
        user_id: str,
        text: str,
        kind: MemoryKind = MemoryKind.DIALOGUE,
        source: SourceKind = SourceKind.USER,
        importance: float = 0.5,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a new memory in the neural network.

        Args:
            user_id: User ID
            text: Memory content
            kind: Memory type
            source: Information source
            importance: Initial importance score [0, 1]
            confidence: Initial confidence score [0, 1]
            metadata: Additional metadata

        Returns:
            Node ID
        """
        # Generate embedding (via RAG)
        embedding = await self._get_embedding(text)

        # Create neural memory node
        node_id = f"neural_{uuid4().hex[:16]}"
        node = NeuralMemoryNode(
            id=node_id,
            user_id=user_id,
            kind=kind,
            text=text,
            embedding=embedding,
            created_at=datetime.utcnow(),
            importance=importance,
            confidence=confidence,
            source=source,
            meta=metadata or {},
        )

        # Store in graph
        self.graph.add_node(
            node_id=node_id,
            node_type="memory",
            **{
                "user_id": user_id,
                "kind": kind.value,
                "text": text,
                "created_at": node.created_at,
                "importance": importance,
                "confidence": confidence,
                "source": source.value,
                "long_term": False,
            },
        )

        # Store in RAG (vector search)
        self.rag.store(
            content=text,
            user_id=user_id,
            metadata={
                "node_id": node_id,
                "kind": kind.value,
                "source": source.value,
                "importance": importance,
            },
        )

        logger.info(f"Stored neural memory node {node_id} for user {user_id}")

        return node_id

    async def forget(self, user_id: str, node_id: str) -> bool:
        """Forget (delete) a memory node (GDPR compliance).

        Args:
            user_id: User ID
            node_id: Node ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Remove from graph
        try:
            self.graph.graph.remove_node(node_id)
        except Exception as e:
            logger.warning(f"Failed to remove node {node_id} from graph: {e}")
            return False

        # Remove from RAG (TODO: implement delete in MemoryRAG)
        # await self.rag.delete(node_id)

        # Clear from co-activation tracker
        # (This is approximate - we can't easily remove all traces without rebuilding)

        logger.info(f"Forgot memory node {node_id} for user {user_id}")

        return True

    async def consolidate(self, user_id: str) -> dict[str, int | float]:
        """Run consolidation process (short-term → long-term).

        Args:
            user_id: User ID

        Returns:
            Statistics dict
        """
        # Get all nodes for user
        user_nodes = []
        for node_id, node_data in self.graph.graph.nodes(data=True):
            if node_data and node_data.get("user_id") == user_id:
                user_nodes.append({"id": node_id, **node_data})

        # Promote qualifying nodes
        promoted = self.decay_manager.consolidate_to_long_term(user_id, user_nodes)

        # Apply decay
        decay_stats = self.decay_manager.apply_decay(user_id)

        logger.info(
            f"Consolidation complete for user {user_id}: "
            f"{len(promoted)} promoted, {decay_stats['edges_pruned']} edges pruned"
        )

        return {
            "promoted_nodes": len(promoted),
            **decay_stats,
        }

    async def _primary_retrieval(
        self,
        user_id: str,
        query_text: str,
        query_embedding: list[float] | None,
        top_k: int,
    ) -> list[tuple[NeuralMemoryNode, float]]:
        """Primary retrieval using RAG vector search.

        Args:
            user_id: User ID
            query_text: Query text
            query_embedding: Optional embedding
            top_k: Number of results

        Returns:
            List of (NeuralMemoryNode, similarity_score) tuples
        """
        # Query RAG
        rag_results = self.rag.recall(query=query_text, user_id=user_id, top_k=top_k)

        # Convert to NeuralMemoryNode
        results = []
        for rag_item in rag_results:
            node_id = rag_item.get("metadata", {}).get("node_id")
            if not node_id:
                continue

            # Get full node data from graph
            try:
                node_data = self.graph.graph.nodes[node_id]
            except Exception:
                logger.warning(f"Node {node_id} not found in graph")
                continue

            # Reconstruct NeuralMemoryNode
            # (Simplified - in production, would have proper serialization)
            node = NeuralMemoryNode(
                id=node_id,
                user_id=user_id,
                kind=MemoryKind(node_data.get("kind", "dialogue")),
                text=rag_item.get("content", ""),
                embedding=[],  # Not stored in graph
                created_at=node_data.get("created_at", datetime.utcnow()),
                last_used_at=node_data.get("last_used_at"),
                use_count=node_data.get("use_count", 0),
                importance=node_data.get("importance", 0.5),
                confidence=node_data.get("confidence", 1.0),
                source=SourceKind(node_data.get("source", "user")),
                long_term=node_data.get("long_term", False),
                quarantine=node_data.get("quarantine", False),
            )

            # Similarity score (distance -> similarity)
            distance = rag_item.get("distance", 1.0)
            similarity = 1.0 - (distance / 2.0)  # Normalize to [0, 1]

            results.append((node, similarity))

        return results

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text (via RAG).

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # TODO: Expose embedding function from MemoryRAG
        # This is a critical missing integration point
        # MemoryRAG needs to expose its embedding model
        raise NotImplementedError(
            "Embedding generation not yet implemented. "
            "MemoryRAG needs to expose its sentence-transformers embedding function. "
            "Track in issue #348 Phase 2."
        )

    async def _update_node_usage(self, user_id: str, node: NeuralMemoryNode) -> None:
        """Update node usage statistics.

        Args:
            user_id: User ID
            node: Memory node
        """
        try:
            if node.id in self.graph.graph.nodes:
                self.graph.graph.nodes[node.id]["use_count"] = (
                    self.graph.graph.nodes[node.id].get("use_count", 0) + 1
                )
                self.graph.graph.nodes[node.id]["last_used_at"] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to update usage for node {node.id}: {e}")

    async def _apply_hebbian_updates_async(self, user_id: str) -> None:
        """Apply queued Hebbian updates asynchronously.

        Args:
            user_id: User ID
        """
        # Delay before applying
        await asyncio.sleep(self.config.async_update_delay_ms / 1000.0)

        # Apply updates
        edges_updated = self.hebbian_learner.apply_updates(user_id)

        logger.debug(f"Async Hebbian update applied: {edges_updated} edges")

    def start_background_decay(self) -> None:
        """Start background decay task."""
        if self._decay_task and not self._decay_task.done():
            logger.warning("Background decay task already running")
            return

        self._decay_task = asyncio.create_task(self._background_decay_loop())
        logger.info("Started background decay task")

    def stop_background_decay(self) -> None:
        """Stop background decay task."""
        if self._decay_task:
            self._decay_task.cancel()
            logger.info("Stopped background decay task")

    async def _background_decay_loop(self) -> None:
        """Background loop for periodic decay application."""
        while True:
            try:
                await asyncio.sleep(self.config.decay_background_interval)

                # Apply decay for all users (simplified - in production, would batch)
                # user_ids = self._get_all_user_ids()
                # for user_id in user_ids:
                #     self.decay_manager.apply_decay(user_id)

                logger.debug("Background decay cycle completed")

            except asyncio.CancelledError:
                logger.info("Background decay loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background decay loop: {e}", exc_info=True)
