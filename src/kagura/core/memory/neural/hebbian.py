"""Hebbian learning update mechanism.

Implements the "cells that fire together, wire together" principle for
dynamically strengthening associations between co-activated memory nodes.

Formula:
    Δw_ij ← η · (a_i · C_i) · (a_j · C_j) - λ · w_ij

Where:
    - η: learning rate
    - a_i, a_j: activation strengths of nodes i and j
    - C_i, C_j: confidence/trust scores (poisoning defense)
    - λ: L2 decay coefficient (prevents weight explosion)
    - w_ij: current edge weight

References:
    - Hopfield Networks is All You Need (arXiv:2008.02217)
    - Hebbian Learning principles
"""

import logging
from collections import defaultdict
from datetime import datetime

from kagura.core.graph.memory import GraphMemory

from .config import NeuralMemoryConfig
from .models import ActivationState, HebbianUpdate, NeuralMemoryNode

logger = logging.getLogger(__name__)


class HebbianLearner:
    """Hebbian learning update manager.

    Handles batch updates of edge weights based on co-activation patterns,
    with trust-based modulation and gradient clipping for security.
    """

    def __init__(
        self,
        graph: GraphMemory,
        config: NeuralMemoryConfig,
    ) -> None:
        """Initialize Hebbian learner.

        Args:
            graph: Graph memory instance to update
            config: Neural memory configuration
        """
        self.graph = graph
        self.config = config
        self._update_queue: dict[str, list[HebbianUpdate]] = defaultdict(list)

    def queue_update(
        self,
        user_id: str,
        activations: list[ActivationState],
        nodes: dict[str, NeuralMemoryNode],
    ) -> None:
        """Queue Hebbian updates for co-activated nodes.

        Args:
            user_id: User ID (for sharding)
            activations: List of activated nodes in this retrieval
            nodes: Map of node_id -> NeuralMemoryNode (for confidence scores)
        """
        # Extract co-activation pairs (for logging/debugging)
        # active_ids = [a.node_id for a in activations]  # Unused, kept for clarity

        for i, act_i in enumerate(activations):
            for act_j in activations[i + 1 :]:  # Avoid duplicates
                node_i = nodes.get(act_i.node_id)
                node_j = nodes.get(act_j.node_id)

                if not node_i or not node_j:
                    continue

                # Calculate Δw with trust modulation
                delta_w = self._calculate_delta_weight(
                    activation_i=act_i.activation,
                    activation_j=act_j.activation,
                    confidence_i=node_i.confidence
                    if self.config.enable_trust_modulation
                    else 1.0,
                    confidence_j=node_j.confidence
                    if self.config.enable_trust_modulation
                    else 1.0,
                    current_weight=self._get_current_weight(
                        user_id, act_i.node_id, act_j.node_id
                    ),
                )

                # Queue bidirectional updates (undirected graph)
                self._update_queue[user_id].append(
                    HebbianUpdate(
                        user_id=user_id,
                        src_id=act_i.node_id,
                        dst_id=act_j.node_id,
                        delta_weight=delta_w,
                    )
                )
                self._update_queue[user_id].append(
                    HebbianUpdate(
                        user_id=user_id,
                        src_id=act_j.node_id,
                        dst_id=act_i.node_id,
                        delta_weight=delta_w,
                    )
                )

        logger.debug(
            f"Queued {len(self._update_queue[user_id])} Hebbian updates "
            f"for user {user_id}"
        )

    def apply_updates(self, user_id: str) -> int:
        """Apply all queued updates for a user (with gradient clipping).

        Args:
            user_id: User ID

        Returns:
            Number of edges updated
        """
        if user_id not in self._update_queue:
            return 0

        updates = self._update_queue[user_id]
        if not updates:
            return 0

        # Group updates by edge (src, dst) and sum deltas
        edge_deltas: dict[tuple[str, str], float] = defaultdict(float)
        for update in updates:
            edge_deltas[(update.src_id, update.dst_id)] += update.delta_weight

        # Apply gradient clipping (DP-SGD style)
        if self.config.gradient_clipping > 0:
            edge_deltas = self._clip_gradients(edge_deltas)

        # Apply updates to graph
        edges_updated = 0
        for (src_id, dst_id), delta_w in edge_deltas.items():
            new_weight = self._apply_update_to_edge(user_id, src_id, dst_id, delta_w)
            if new_weight is not None:
                edges_updated += 1

        # Clear queue
        self._update_queue[user_id].clear()

        logger.info(f"Applied {edges_updated} Hebbian updates for user {user_id}")
        return edges_updated

    def _calculate_delta_weight(
        self,
        activation_i: float,
        activation_j: float,
        confidence_i: float,
        confidence_j: float,
        current_weight: float,
    ) -> float:
        """Calculate Hebbian weight update.

        Formula:
            Δw = η · (a_i · C_i) · (a_j · C_j) - λ · w

        Args:
            activation_i: Activation of node i [0, 1]
            activation_j: Activation of node j [0, 1]
            confidence_i: Confidence of node i [0, 1]
            confidence_j: Confidence of node j [0, 1]
            current_weight: Current edge weight

        Returns:
            Weight delta (can be negative if decay dominates)
        """
        # Hebbian term: strengthening based on co-activation
        hebbian_term = (
            self.config.learning_rate
            * (activation_i * confidence_i)
            * (activation_j * confidence_j)
        )

        # Decay term: regularization to prevent weight explosion
        decay_term = self.config.decay_lambda * current_weight

        delta_w = hebbian_term - decay_term

        return delta_w

    def _get_current_weight(self, user_id: str, src_id: str, dst_id: str) -> float:
        """Get current edge weight from graph.

        Args:
            user_id: User ID
            src_id: Source node ID
            dst_id: Destination node ID

        Returns:
            Current weight (0.0 if edge doesn't exist)
        """
        # Query graph for edge data
        # Note: GraphMemory uses NetworkX internally
        try:
            edge_data = self.graph.graph.get_edge_data(src_id, dst_id)
            if edge_data:
                return edge_data.get("weight", 0.0)
        except Exception as e:
            logger.debug(f"Edge ({src_id}, {dst_id}) not found: {e}")

        return 0.0

    def _apply_update_to_edge(
        self, user_id: str, src_id: str, dst_id: str, delta_w: float
    ) -> float | None:
        """Apply weight update to graph edge.

        Args:
            user_id: User ID
            src_id: Source node ID
            dst_id: Destination node ID
            delta_w: Weight delta to apply

        Returns:
            New weight value, or None if update failed
        """
        current_weight = self._get_current_weight(user_id, src_id, dst_id)
        new_weight = current_weight + delta_w

        # Clip to [0, weight_max]
        new_weight = max(0.0, min(new_weight, self.config.weight_max))

        # Prune if below threshold
        if new_weight < self.config.prune_threshold:
            # Remove edge
            try:
                if self.graph.graph.has_edge(src_id, dst_id):
                    self.graph.graph.remove_edge(src_id, dst_id)
                    logger.debug(
                        f"Pruned edge ({src_id}, {dst_id}) (weight={new_weight:.4f})"
                    )
                return 0.0
            except Exception as e:
                logger.error(f"Failed to remove edge ({src_id}, {dst_id}): {e}")
                return None

        # Update or create edge
        try:
            if self.graph.graph.has_edge(src_id, dst_id):
                # Update existing edge
                self.graph.graph[src_id][dst_id]["weight"] = new_weight
                self.graph.graph[src_id][dst_id]["last_updated"] = datetime.utcnow()
            else:
                # Create new edge (using 'learned_from')
                # This is the closest existing edge type
                self.graph.add_edge(
                    src_id=src_id,
                    dst_id=dst_id,
                    rel_type="learned_from",  # Use existing edge type for compatibility
                    weight=new_weight,
                    metadata={
                        "created_by": "hebbian_learning",
                        "neural_association": True,
                    },
                    confidence=1.0,
                )

            logger.debug(
                f"Updated edge ({src_id}, {dst_id}): "
                f"{current_weight:.4f} -> {new_weight:.4f} (Δ={delta_w:.4f})"
            )
            return new_weight

        except Exception as e:
            logger.error(f"Failed to update edge ({src_id}, {dst_id}): {e}")
            return None

    def _clip_gradients(
        self, edge_deltas: dict[tuple[str, str], float]
    ) -> dict[tuple[str, str], float]:
        """Clip gradients to prevent poisoning attacks.

        Limits the total weight change per node to prevent a single
        malicious interaction from dominating the graph.

        Args:
            edge_deltas: Map of (src, dst) -> delta_w

        Returns:
            Clipped edge deltas
        """
        # Calculate total delta per node (outgoing edges)
        node_total_deltas: dict[str, float] = defaultdict(float)
        for (src_id, _), delta_w in edge_deltas.items():
            node_total_deltas[src_id] += abs(delta_w)

        # Clip if any node exceeds threshold
        clipped_deltas = {}
        for (src_id, dst_id), delta_w in edge_deltas.items():
            total_delta = node_total_deltas[src_id]
            if total_delta > self.config.gradient_clipping:
                # Scale down proportionally
                scale = self.config.gradient_clipping / total_delta
                clipped_deltas[(src_id, dst_id)] = delta_w * scale
                logger.debug(
                    f"Clipped gradient for node {src_id}: "
                    f"{delta_w:.4f} -> {delta_w * scale:.4f}"
                )
            else:
                clipped_deltas[(src_id, dst_id)] = delta_w

        return clipped_deltas

    def prune_weak_edges(self, user_id: str, node_id: str) -> int:
        """Prune weak outgoing edges from a node (keep top-M).

        Args:
            user_id: User ID
            node_id: Node to prune

        Returns:
            Number of edges removed
        """
        # Get all outgoing edges
        try:
            outgoing = list(self.graph.graph.successors(node_id))
        except Exception:
            return 0

        if len(outgoing) <= self.config.top_m_edges:
            return 0  # No pruning needed

        # Sort by weight (descending)
        edge_weights = [
            (dst_id, self.graph.graph[node_id][dst_id].get("weight", 0.0))
            for dst_id in outgoing
        ]
        edge_weights.sort(key=lambda x: x[1], reverse=True)

        # Remove weakest edges
        to_remove = edge_weights[self.config.top_m_edges :]
        removed_count = 0
        for dst_id, weight in to_remove:
            try:
                self.graph.graph.remove_edge(node_id, dst_id)
                removed_count += 1
                logger.debug(
                    f"Pruned weak edge ({node_id}, {dst_id}) (weight={weight:.4f})"
                )
            except Exception as e:
                logger.error(f"Failed to prune edge ({node_id}, {dst_id}): {e}")

        return removed_count
