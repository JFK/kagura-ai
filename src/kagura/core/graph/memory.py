"""Graph Memory for relationship tracking.

NetworkX-based knowledge graph for memories, users, topics, and interactions.

Issue #345: GraphDB integration for AI-User relationship memory
"""

import pickle
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import networkx as nx


class GraphMemory:
    """NetworkX-based graph memory for tracking relationships.

    Manages a directed graph of memories, users, topics, and interactions
    with typed relationships between them.

    Node Types:
        - memory: Memory nodes (keys from MemoryManager)
        - user: User nodes
        - topic: Topic/category nodes
        - interaction: AI-User interaction history nodes

    Edge Types:
        - related_to: Semantic relationship
        - depends_on: Dependency relationship
        - learned_from: Learning source
        - influences: Influence relationship
        - works_on: Project/task relationship

    Example:
        >>> graph = GraphMemory()
        >>> graph.add_node("mem_001", "memory", {"key": "python_tips"})
        >>> graph.add_node("topic_python", "topic", {"name": "Python"})
        >>> graph.add_edge("mem_001", "topic_python", "related_to", weight=0.9)
        >>> related = graph.get_related("mem_001", depth=2)
    """

    # Type definitions
    NODE_TYPES = ["memory", "user", "topic", "interaction"]
    EDGE_TYPES = ["related_to", "depends_on", "learned_from", "influences", "works_on"]

    def __init__(self, persist_path: Optional[Path] = None):
        """Initialize graph memory.

        Args:
            persist_path: Path to save/load graph (pickle format)
        """
        self.graph = nx.DiGraph()
        self.persist_path = persist_path

        # Load existing graph if path exists
        if persist_path and persist_path.exists():
            self.load()

    def add_node(
        self, node_id: str, node_type: str, data: Optional[dict[str, Any]] = None
    ) -> None:
        """Add node to graph.

        Args:
            node_id: Unique node identifier
            node_type: Node type (memory/user/topic/interaction)
            data: Additional node data

        Raises:
            ValueError: If node_type is invalid
        """
        if node_type not in self.NODE_TYPES:
            raise ValueError(
                f"Invalid node_type: {node_type}. Must be one of {self.NODE_TYPES}"
            )

        node_data = data or {}
        node_data["type"] = node_type
        node_data["created_at"] = datetime.now().isoformat()

        self.graph.add_node(node_id, **node_data)

    def add_edge(
        self,
        src_id: str,
        dst_id: str,
        rel_type: str,
        weight: float = 1.0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add edge between nodes.

        Args:
            src_id: Source node ID
            dst_id: Destination node ID
            rel_type: Relationship type
            weight: Edge weight (0.0-1.0, default 1.0)
            metadata: Additional edge metadata

        Raises:
            ValueError: If rel_type is invalid or nodes don't exist
        """
        if rel_type not in self.EDGE_TYPES:
            raise ValueError(
                f"Invalid rel_type: {rel_type}. Must be one of {self.EDGE_TYPES}"
            )

        if not self.graph.has_node(src_id):
            raise ValueError(f"Source node '{src_id}' does not exist")

        if not self.graph.has_node(dst_id):
            raise ValueError(f"Destination node '{dst_id}' does not exist")

        edge_data = metadata or {}
        edge_data["type"] = rel_type
        edge_data["weight"] = weight
        edge_data["created_at"] = datetime.now().isoformat()

        self.graph.add_edge(src_id, dst_id, **edge_data)

    def query_graph(
        self,
        seed_ids: list[str],
        hops: int = 2,
        rel_filters: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Multi-hop graph traversal from seed nodes.

        Args:
            seed_ids: Starting node IDs
            hops: Number of hops (depth) to traverse
            rel_filters: Filter by relationship types (None = all types)

        Returns:
            Subgraph dict with nodes and edges

        Example:
            >>> result = graph.query_graph(
            ...     seed_ids=["mem_001"],
            ...     hops=2,
            ...     rel_filters=["related_to", "depends_on"]
            ... )
        """
        # Collect nodes within hops
        visited_nodes = set(seed_ids)
        current_layer = set(seed_ids)

        for _ in range(hops):
            next_layer = set()
            for node_id in current_layer:
                if not self.graph.has_node(node_id):
                    continue

                # Get successors (outgoing edges)
                for neighbor in self.graph.successors(node_id):
                    edge_data = self.graph.edges[node_id, neighbor]
                    edge_type = edge_data.get("type")

                    # Filter by relationship type if specified
                    if rel_filters and edge_type not in rel_filters:
                        continue

                    if neighbor not in visited_nodes:
                        visited_nodes.add(neighbor)
                        next_layer.add(neighbor)

                # Get predecessors (incoming edges)
                for neighbor in self.graph.predecessors(node_id):
                    edge_data = self.graph.edges[neighbor, node_id]
                    edge_type = edge_data.get("type")

                    # Filter by relationship type if specified
                    if rel_filters and edge_type not in rel_filters:
                        continue

                    if neighbor not in visited_nodes:
                        visited_nodes.add(neighbor)
                        next_layer.add(neighbor)

            current_layer = next_layer

            if not current_layer:
                break  # No more nodes to explore

        # Build subgraph
        subgraph = self.graph.subgraph(visited_nodes)

        return self._serialize_subgraph(subgraph)

    def get_related(
        self, node_id: str, depth: int = 2, rel_type: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get related nodes by traversal.

        Args:
            node_id: Starting node ID
            depth: Traversal depth (default: 2)
            rel_type: Filter by relationship type (None = all)

        Returns:
            List of related node dicts with metadata

        Example:
            >>> related = graph.get_related("mem_001", depth=2)
        """
        if not self.graph.has_node(node_id):
            return []

        rel_filters = [rel_type] if rel_type else None
        result = self.query_graph([node_id], hops=depth, rel_filters=rel_filters)

        # Exclude the seed node itself
        related_nodes = [
            node for node in result["nodes"] if node["id"] != node_id
        ]

        return related_nodes

    def record_interaction(
        self,
        user_id: str,
        ai_platform: str,
        query: str,
        response: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Record AI-User interaction.

        Args:
            user_id: User identifier
            ai_platform: AI platform name (e.g., "claude", "chatgpt")
            query: User's query
            response: AI's response
            metadata: Additional metadata (e.g., session_id, project)

        Returns:
            Interaction node ID

        Example:
            >>> interaction_id = graph.record_interaction(
            ...     user_id="user_001",
            ...     ai_platform="claude",
            ...     query="How to use FastAPI?",
            ...     response="FastAPI is...",
            ...     metadata={"project": "kagura", "session_id": "sess_123"}
            ... )
        """
        # Create interaction node
        interaction_id = f"interaction_{uuid.uuid4().hex[:8]}"
        interaction_data = {
            "user_id": user_id,
            "ai_platform": ai_platform,
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {}),
        }

        self.add_node(interaction_id, "interaction", interaction_data)

        # Link to user (create user node if doesn't exist)
        if not self.graph.has_node(user_id):
            self.add_node(user_id, "user", {"user_id": user_id})

        self.add_edge(interaction_id, user_id, "learned_from", weight=1.0)

        return interaction_id

    def get_node(self, node_id: str) -> Optional[dict[str, Any]]:
        """Get node data.

        Args:
            node_id: Node ID

        Returns:
            Node data dict or None if not found
        """
        if not self.graph.has_node(node_id):
            return None

        data = dict(self.graph.nodes[node_id])
        data["id"] = node_id
        return data

    def get_edge(self, src_id: str, dst_id: str) -> Optional[dict[str, Any]]:
        """Get edge data.

        Args:
            src_id: Source node ID
            dst_id: Destination node ID

        Returns:
            Edge data dict or None if not found
        """
        if not self.graph.has_edge(src_id, dst_id):
            return None

        data = dict(self.graph.edges[src_id, dst_id])
        data["src"] = src_id
        data["dst"] = dst_id
        return data

    def persist(self) -> None:
        """Save graph to disk (pickle format).

        Raises:
            ValueError: If persist_path is not set
        """
        if not self.persist_path:
            raise ValueError("persist_path not set. Cannot save graph.")

        # Ensure parent directory exists
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)

        # Save graph using pickle
        with open(self.persist_path, "wb") as f:
            pickle.dump(self.graph, f)

    def load(self) -> None:
        """Load graph from disk (pickle format).

        Raises:
            ValueError: If persist_path is not set
            FileNotFoundError: If file doesn't exist
        """
        if not self.persist_path:
            raise ValueError("persist_path not set. Cannot load graph.")

        if not self.persist_path.exists():
            raise FileNotFoundError(f"Graph file not found: {self.persist_path}")

        # Load graph using pickle
        with open(self.persist_path, "rb") as f:
            self.graph = pickle.load(f)

    def stats(self) -> dict[str, Any]:
        """Get graph statistics.

        Returns:
            Stats dict with node/edge counts
        """
        node_counts = {}
        for node_id in self.graph.nodes():
            node_type = self.graph.nodes[node_id].get("type", "unknown")
            node_counts[node_type] = node_counts.get(node_type, 0) + 1

        edge_counts = {}
        for src, dst in self.graph.edges():  # type: ignore[misc]
            edge_type = self.graph.edges[src, dst].get("type", "unknown")
            edge_counts[edge_type] = edge_counts.get(edge_type, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_counts": node_counts,
            "edge_counts": edge_counts,
            "is_connected": nx.is_weakly_connected(self.graph)
            if self.graph.number_of_nodes() > 0
            else False,
        }

    def _serialize_subgraph(self, subgraph: nx.DiGraph) -> dict[str, Any]:
        """Serialize subgraph to dict.

        Args:
            subgraph: NetworkX subgraph

        Returns:
            Dict with nodes and edges lists
        """
        nodes = []
        for node_id in subgraph.nodes():
            node_data = dict(subgraph.nodes[node_id])
            node_data["id"] = node_id
            nodes.append(node_data)

        edges = []
        for src, dst in subgraph.edges():  # type: ignore[misc]
            edge_data = dict(subgraph.edges[src, dst])
            edge_data["src"] = src
            edge_data["dst"] = dst
            edges.append(edge_data)

        return {"nodes": nodes, "edges": edges}

    def get_user_topics(self, user_id: str) -> list[dict[str, Any]]:
        """Get topics associated with a user.

        Args:
            user_id: User identifier

        Returns:
            List of topic nodes associated with the user

        Example:
            >>> topics = graph.get_user_topics("user_001")
            >>> # Returns topic nodes connected via interactions
        """
        if not self.graph.has_node(user_id):
            return []

        topics = []
        # Find all interactions from this user
        for predecessor in self.graph.predecessors(user_id):
            pred_data = self.graph.nodes[predecessor]
            if pred_data.get("type") == "interaction":
                # Find topics connected to this interaction
                for neighbor in self.graph.successors(predecessor):
                    if neighbor == user_id:
                        continue
                    neighbor_data = self.graph.nodes[neighbor]
                    if neighbor_data.get("type") == "topic":
                        topic_dict = dict(neighbor_data)
                        topic_dict["id"] = neighbor
                        topics.append(topic_dict)

        return topics

    def get_user_interactions(
        self, user_id: str, limit: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Get interaction history for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of interactions to return (None = all)

        Returns:
            List of interaction nodes, sorted by timestamp (newest first)

        Example:
            >>> interactions = graph.get_user_interactions("user_001", limit=10)
        """
        if not self.graph.has_node(user_id):
            return []

        interactions = []
        # Find all interactions connected to this user
        for predecessor in self.graph.predecessors(user_id):
            pred_data = self.graph.nodes[predecessor]
            if pred_data.get("type") == "interaction":
                interaction_dict = dict(pred_data)
                interaction_dict["id"] = predecessor
                interactions.append(interaction_dict)

        # Sort by timestamp (newest first)
        interactions.sort(
            key=lambda x: x.get("timestamp", ""), reverse=True
        )

        # Apply limit if specified
        if limit is not None:
            interactions = interactions[:limit]

        return interactions

    def analyze_user_pattern(self, user_id: str) -> dict[str, Any]:
        """Analyze user's interaction patterns and interests.

        Args:
            user_id: User identifier

        Returns:
            Analysis dict with statistics and patterns

        Example:
            >>> pattern = graph.analyze_user_pattern("user_001")
            >>> # Returns: {
            >>> #   "total_interactions": 42,
            >>> #   "topics": ["python", "fastapi"],
            >>> #   "avg_interactions_per_topic": 3.5,
            >>> #   "most_discussed_topic": "python",
            >>> #   "platforms": {"claude": 30, "chatgpt": 12}
            >>> # }
        """
        if not self.graph.has_node(user_id):
            return {
                "total_interactions": 0,
                "topics": [],
                "avg_interactions_per_topic": 0.0,
                "most_discussed_topic": None,
                "platforms": {},
            }

        # Get all interactions
        interactions = self.get_user_interactions(user_id)
        total_interactions = len(interactions)

        # Count platforms
        platforms: dict[str, int] = {}
        for interaction in interactions:
            platform = interaction.get("ai_platform", "unknown")
            platforms[platform] = platforms.get(platform, 0) + 1

        # Get topics
        topics_list = self.get_user_topics(user_id)
        unique_topics = list({t.get("id") for t in topics_list})

        # Calculate average interactions per topic
        avg_interactions_per_topic = (
            total_interactions / len(unique_topics) if unique_topics else 0.0
        )

        # Find most discussed topic (topic with most interactions)
        topic_interaction_count: dict[str, int] = {}
        for topic in topics_list:
            topic_id = topic.get("id", "")
            topic_interaction_count[topic_id] = (
                topic_interaction_count.get(topic_id, 0) + 1
            )

        most_discussed_topic = None
        if topic_interaction_count:
            most_discussed_topic = max(
                topic_interaction_count, key=topic_interaction_count.get  # type: ignore[arg-type]
            )

        return {
            "total_interactions": total_interactions,
            "topics": unique_topics,
            "avg_interactions_per_topic": round(avg_interactions_per_topic, 2),
            "most_discussed_topic": most_discussed_topic,
            "platforms": platforms,
        }

    def clear(self) -> None:
        """Clear all nodes and edges from graph."""
        self.graph.clear()

    def __repr__(self) -> str:
        """String representation."""
        stats = self.stats()
        return (
            f"GraphMemory("
            f"nodes={stats['total_nodes']}, "
            f"edges={stats['total_edges']}, "
            f"types={list(stats['node_counts'].keys())})"
        )
