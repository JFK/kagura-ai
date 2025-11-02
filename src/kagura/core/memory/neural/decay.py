"""Forgetting and decay mechanisms for neural memory.

Implements automatic weight decay and selective pruning to prevent
memory bloat and enable graceful forgetting of unused associations.

Biological inspiration: Memories that are not reinforced fade over time,
allowing new information to be learned without interference.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any

import networkx as nx

from kagura.core.graph.memory import GraphMemory

from .config import NeuralMemoryConfig

logger = logging.getLogger(__name__)


class DecayManager:
    """Manages automatic forgetting and weight decay for neural memory."""

    def __init__(
        self,
        graph: GraphMemory,
        config: NeuralMemoryConfig,
    ) -> None:
        """Initialize decay manager.

        Args:
            graph: Graph memory instance
            config: Neural memory configuration
        """
        self.graph = graph
        self.config = config
        self._last_decay_time: datetime | None = None

    def apply_decay(self, user_id: str) -> dict[str, int | float]:
        """Apply exponential decay to all edge weights.

        Formula:
            w_ij(t+Δt) = w_ij(t) · exp(-decay_rate · Δt)

        Args:
            user_id: User ID (for filtering user-specific edges)

        Returns:
            Dict with statistics (edges_decayed, edges_pruned, delta_seconds)
        """
        if not self.config.enable_decay:
            logger.debug("Decay is disabled in configuration")
            return {"edges_decayed": 0, "edges_pruned": 0}

        current_time = datetime.utcnow()

        # Calculate time delta
        if self._last_decay_time:
            delta_seconds = (current_time - self._last_decay_time).total_seconds()
        else:
            # First run - use default interval
            delta_seconds = self.config.decay_background_interval

        if delta_seconds <= 0:
            return {"edges_decayed": 0, "edges_pruned": 0}

        # Apply decay to all edges
        edges_to_remove = []
        edges_decayed = 0

        for src, dst, data in self.graph.graph.edges(data=True):  # type: ignore[misc]
            current_weight = data.get("weight", 0.0) if data else 0.0

            # Calculate decay factor
            # Note: decay_rate is per-second rate
            decay_factor = math.exp(-self.config.decay_rate * delta_seconds)
            new_weight = current_weight * decay_factor

            # Update weight
            if new_weight >= self.config.prune_threshold:
                self.graph.graph[src][dst]["weight"] = new_weight
                self.graph.graph[src][dst]["last_decayed"] = current_time
                edges_decayed += 1
            else:
                # Mark for removal (below threshold)
                edges_to_remove.append((src, dst))

        # Remove weak edges
        for src, dst in edges_to_remove:
            try:
                self.graph.graph.remove_edge(src, dst)
                logger.debug(f"Pruned weak edge ({src}, {dst}) during decay")
            except nx.NetworkXError:
                pass

        self._last_decay_time = current_time

        logger.info(
            f"Applied decay: {edges_decayed} edges decayed, "
            f"{len(edges_to_remove)} edges pruned "
            f"(Δt={delta_seconds:.0f}s)"
        )

        return {
            "edges_decayed": edges_decayed,
            "edges_pruned": len(edges_to_remove),
            "delta_seconds": delta_seconds,
        }

    def prune_weak_edges(self, user_id: str, threshold: float | None = None) -> int:
        """Prune edges below a weight threshold.

        Args:
            user_id: User ID
            threshold: Weight threshold (default: config.prune_threshold)

        Returns:
            Number of edges pruned
        """
        threshold = threshold if threshold is not None else self.config.prune_threshold

        edges_to_remove = []

        for src, dst, data in self.graph.graph.edges(data=True):  # type: ignore[misc]
            weight = data.get("weight", 0.0) if data else 0.0
            if weight < threshold:
                edges_to_remove.append((src, dst))

        for src, dst in edges_to_remove:
            try:
                self.graph.graph.remove_edge(src, dst)
            except nx.NetworkXError:
                pass

        logger.info(
            f"Pruned {len(edges_to_remove)} weak edges (threshold={threshold:.4f})"
        )

        return len(edges_to_remove)

    def prune_old_nodes(
        self, user_id: str, age_days: float, importance_threshold: float = 0.3
    ) -> int:
        """Prune old, low-importance nodes.

        Args:
            user_id: User ID
            age_days: Age threshold in days
            importance_threshold: Importance threshold [0, 1]

        Returns:
            Number of nodes pruned
        """
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(days=age_days)

        nodes_to_remove = []

        for node_id, node_data in self.graph.graph.nodes(data=True):  # type: ignore[misc]
            if not node_data:
                continue

            # Check if this is a memory node (has created_at)
            created_at = node_data.get("created_at")
            if not created_at:
                continue

            # Check age
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            if created_at > cutoff_time:
                continue  # Too recent

            # Check importance
            importance = node_data.get("importance", 0.5)
            if importance >= importance_threshold:
                continue  # Too important

            # Check if it's a long-term memory (protected)
            is_long_term = node_data.get("long_term", False)
            if is_long_term:
                continue  # Protected

            nodes_to_remove.append(node_id)

        # Remove nodes
        for node_id in nodes_to_remove:
            try:
                self.graph.graph.remove_node(node_id)
            except nx.NetworkXError:
                pass

        logger.info(
            f"Pruned {len(nodes_to_remove)} old nodes "
            f"(age>{age_days}d, importance<{importance_threshold:.2f})"
        )

        return len(nodes_to_remove)

    def consolidate_to_long_term(
        self, user_id: str, nodes: list[dict[str, Any]]
    ) -> list[str]:
        """Promote qualifying nodes to long-term memory.

        Criteria (from config):
        - use_count >= consolidation_use_count_min
        - importance >= consolidation_importance_min
        - diversity >= consolidation_diversity_min (TODO: implement diversity metric)

        Args:
            user_id: User ID
            nodes: List of node data dicts

        Returns:
            List of promoted node IDs
        """
        promoted = []

        for node_data in nodes:
            node_id = node_data.get("id")
            if not node_id:
                continue

            # Check if already long-term
            if node_data.get("long_term", False):
                continue

            # Check criteria
            use_count = node_data.get("use_count", 0)
            importance = node_data.get("importance", 0.0)

            if (
                use_count >= self.config.consolidation_use_count_min
                and importance >= self.config.consolidation_importance_min
            ):
                # Promote to long-term
                try:
                    if node_id in self.graph.graph.nodes:
                        self.graph.graph.nodes[node_id]["long_term"] = True
                        self.graph.graph.nodes[node_id]["consolidated_at"] = (
                            datetime.utcnow()
                        )
                        promoted.append(node_id)
                        logger.debug(
                            f"Promoted node {node_id} to long-term "
                            f"(use_count={use_count}, importance={importance:.2f})"
                        )
                except nx.NetworkXError as e:
                    logger.error(f"Failed to promote node {node_id}: {e}")

        logger.info(f"Consolidated {len(promoted)} nodes to long-term memory")

        return promoted

    def get_decay_statistics(self, user_id: str) -> dict[str, Any]:
        """Get statistics about edge weights and decay status.

        Args:
            user_id: User ID

        Returns:
            Dict with statistics
        """
        weights = []
        neural_edges = 0

        for _, _, data in self.graph.graph.edges(data=True):  # type: ignore[misc]
            if data and data.get("type") == "neural_association":
                neural_edges += 1
                weight = data.get("weight", 0.0)
                weights.append(weight)

        if not weights:
            return {
                "total_neural_edges": 0,
                "avg_weight": 0.0,
                "max_weight": 0.0,
                "min_weight": 0.0,
                "below_threshold": 0,
            }

        below_threshold = sum(1 for w in weights if w < self.config.prune_threshold)

        return {
            "total_neural_edges": neural_edges,
            "avg_weight": sum(weights) / len(weights),
            "max_weight": max(weights),
            "min_weight": min(weights),
            "below_threshold": below_threshold,
            "last_decay_time": self._last_decay_time.isoformat()
            if self._last_decay_time
            else None,
        }
