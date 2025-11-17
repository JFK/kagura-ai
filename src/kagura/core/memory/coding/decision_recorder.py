"""Design decision recording and tracking module for coding memory.

This module provides design decision tracking with implementation status monitoring.
Extracted from manager.py as part of Phase 3.2 refactoring.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kagura.core.memory.coding.manager import CodingMemoryManager

from kagura.core.memory.models.coding import DesignDecision

logger = logging.getLogger(__name__)


async def record_decision(
    self: CodingMemoryManager,
    decision: str,
    rationale: str,
    alternatives: list[str] | None = None,
    impact: str | None = None,
    tags: list[str] | None = None,
    related_files: list[str] | None = None,
    confidence: float = 0.8,
) -> str:
    """Record design decision.

    Captures architectural and design decisions with rationale.

    Args:
        decision: Brief statement of decision
        rationale: Reasoning behind decision
        alternatives: Other options considered
        impact: Expected project impact
        tags: Categorization tags
        related_files: Files affected by decision
        confidence: Confidence level (0.0-1.0)

    Returns:
        Unique ID for this decision record

    Example:
        >>> decision_id = await coding_mem.record_decision(
        ...     decision="Use JWT tokens for authentication",
        ...     rationale="Stateless auth enables horizontal scaling",
        ...     alternatives=["Session-based auth", "OAuth only"],
        ...     impact="No session storage needed, enables mobile app",
        ...     tags=["architecture", "security"]
        ... )
    """
    record = DesignDecision(
        decision=decision,
        rationale=rationale,
        alternatives=alternatives or [],
        impact=impact or "To be determined",
        tags=tags or [],
        related_files=related_files or [],
        confidence=confidence,
    )

    # Generate unique ID
    decision_id = f"decision_{uuid.uuid4().hex[:12]}"

    # Store in persistent memory
    key = self._make_key(f"decision:{decision_id}")
    self.persistent.store(
        key=key, value=record.model_dump(mode="json"), user_id=self.user_id
    )

    # Add to RAG
    if self.rag:
        content_text = (
            f"Decision: {decision}\n"
            f"Rationale: {rationale}\n"
            f"Alternatives: {', '.join(alternatives or [])}"
        )
        self.rag.store(
            content=content_text,
            user_id=self.user_id,
            metadata={
                "type": "decision",
                "tags": ",".join(tags or []),  # ChromaDB doesn't support lists
                "project_id": self.project_id,
                "decision_id": decision_id,  # Entity ID for retrieval
            },
            agent_name=self.agent_name,
        )

    # Add to graph
    if self.graph:
        self.graph.add_node(
            node_id=decision_id,
            node_type="memory",
            data={
                "decision": decision,
                "rationale": rationale,
                "alternatives": alternatives or [],
                "impact": impact or "To be determined",
                "tags": tags or [],
                "project_id": self.project_id,
                "related_files": related_files or [],
                "confidence": confidence,
            },
        )

        # Link to session if active
        if self.current_session_id:
            self.graph.add_edge(
                src_id=self.current_session_id,
                dst_id=decision_id,
                rel_type="decided",
                weight=1.0,
            )

    logger.info(f"Recorded decision: {decision_id}")
    return decision_id


async def get_decision_implementation_status(
    self: CodingMemoryManager, decision_id: str
) -> dict[str, Any]:
    """Get implementation status for a decision.

    Args:
        decision_id: Decision ID

    Returns:
        Dictionary with implementation status:
            - implemented_files: Files that implement this decision
            - pending_files: Files mentioned but not implemented
            - completion: Percentage (0.0-1.0)

    Example:
        >>> status = await coding_mem.get_decision_implementation_status(
        ...     "decision_xyz"
        ... )
        >>> print(status)
        {
            'implemented_files': ['src/auth.py'],
            'pending_files': ['src/middleware.py'],
            'completion': 0.5
        }
    """
    if not self.graph or not self.graph.graph.has_node(decision_id):
        return {
            "implemented_files": [],
            "pending_files": [],
            "completion": 0.0,
        }

    # Get decision data
    decision_data = self.graph.graph.nodes[decision_id]
    related_files = decision_data.get("data", {}).get("related_files", [])

    # Find file changes that implement this decision
    implemented = []
    for src_id, _, edge_data in self.graph.graph.in_edges(decision_id, data=True):  # type: ignore[misc]
        if edge_data and edge_data.get("type") == "implements":
            # This is a file change implementing the decision
            if self.graph.graph.has_node(src_id):
                change_data = self.graph.graph.nodes[src_id]
                file_path = change_data.get("data", {}).get("file_path")
                if file_path:
                    implemented.append(file_path)

    # Determine pending files
    pending = [f for f in related_files if f not in implemented]

    # Calculate completion
    total = len(related_files) if related_files else 1
    completion = len(implemented) / total if total > 0 else 0.0

    return {
        "implemented_files": implemented,
        "pending_files": pending,
        "completion": completion,
    }
