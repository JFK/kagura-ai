"""Error recording and search module for coding memory.

This module provides error tracking with pattern learning and semantic search
for similar errors. Extracted from manager.py as part of Phase 3.2 refactoring.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kagura.core.memory.coding.manager import CodingMemoryManager

from kagura.core.memory.models.coding import ErrorRecord

logger = logging.getLogger(__name__)


async def record_error(
    self: CodingMemoryManager,
    error_type: str,
    message: str,
    stack_trace: str,
    file_path: str,
    line_number: int,
    solution: str | None = None,
    screenshot: str | None = None,  # Path or base64
    tags: list[str] | None = None,
    similar_error_ids: list[str] | None = None,
) -> str:
    """Record error with optional screenshot.

    Captures error details for pattern learning and future reference.

    Args:
        error_type: Error classification (TypeError, SyntaxError, etc.)
        message: Error message text
        stack_trace: Full stack trace
        file_path: File where error occurred
        line_number: Line number of error
        solution: How error was resolved (optional)
        screenshot: Path to screenshot or base64-encoded image
        tags: Custom categorization tags
        similar_error_ids: IDs of similar past errors (for graph linking)

    Returns:
        Unique ID for this error record

    Example:
        >>> error_id = await coding_mem.record_error(
        ...     error_type="TypeError",
        ...     message="can't compare offset-naive and offset-aware datetimes",
        ...     stack_trace="...",
        ...     file_path="src/auth.py",
        ...     line_number=42,
        ...     solution="Use datetime.now(timezone.utc) consistently"
        ... )
    """
    # Analyze screenshot if provided
    screenshot_path = None
    screenshot_base64 = None
    if screenshot:
        # Determine if path or base64
        if screenshot.startswith("data:image") or len(screenshot) > 500:
            screenshot_base64 = screenshot
        else:
            screenshot_path = screenshot

        # Optional: Extract additional info from screenshot using vision analyzer
        try:
            screen_analysis = await self.vision_analyzer.analyze_error_screenshot(
                screenshot
            )
            # Enhance error info with vision analysis
            if not message and screen_analysis.get("error_message"):
                message = screen_analysis["error_message"]
            logger.info(
                f"Screenshot analysis successful: {screen_analysis['error_type']}"
            )
        except Exception as e:
            logger.warning(f"Screenshot analysis failed: {e}")

    record = ErrorRecord(
        error_type=error_type,
        message=message,
        stack_trace=stack_trace,
        file_path=file_path,
        line_number=line_number,
        solution=solution,
        screenshot_path=screenshot_path,
        screenshot_base64=screenshot_base64,
        tags=tags or [],
        session_id=self.current_session_id,
        resolved=solution is not None,
    )

    # Generate unique ID
    error_id = f"error_{uuid.uuid4().hex[:12]}"

    # Store in persistent memory
    key = self._make_key(f"error:{error_id}")
    self.persistent.store(
        key=key, value=record.model_dump(mode="json"), user_id=self.user_id
    )

    # Add to RAG for semantic search
    if self.rag:
        content_text = (
            f"Error: {error_type}\n"
            f"Message: {message}\n"
            f"File: {file_path}:{line_number}\n"
            f"Solution: {solution or 'Not yet resolved'}"
        )
        self.rag.store(
            content=content_text,
            user_id=self.user_id,
            metadata={
                "type": "error",
                "error_type": error_type,
                "file_path": file_path,
                "resolved": record.resolved,
                "project_id": self.project_id,
                "error_id": error_id,  # Entity ID for retrieval
            },
            agent_name=self.agent_name,
        )

    # Add to graph
    if self.graph:
        self.graph.add_node(
            node_id=error_id,
            node_type="memory",
            data={
                "error_type": error_type,
                "file_path": file_path,
                "line_number": line_number,
                "resolved": record.resolved,
                "project_id": self.project_id,
            },
        )

        # Link to session if active
        if self.current_session_id:
            self.graph.add_edge(
                src_id=self.current_session_id,
                dst_id=error_id,
                rel_type="encountered",
                weight=1.0,
            )

        # Link to similar errors (Phase 2)
        if similar_error_ids:
            for similar_id in similar_error_ids:
                if self.graph.graph.has_node(similar_id):
                    self.graph.add_edge(
                        src_id=error_id,
                        dst_id=similar_id,
                        rel_type="similar_to",
                        weight=0.85,
                    )

        # If solution provided, create solution node and link (Phase 2)
        if solution and self.graph:
            solution_id = f"solution_{uuid.uuid4().hex[:8]}"
            self.graph.add_node(
                node_id=solution_id,
                node_type="solution",
                data={
                    "solution": solution,
                    "error_type": error_type,
                    "project_id": self.project_id,
                },
            )

            # Link error to solution
            self.graph.add_edge(
                src_id=error_id,
                dst_id=solution_id,
                rel_type="solved_by",
                weight=1.0,
            )

    logger.info(f"Recorded error: {error_id} ({error_type})")
    return error_id


async def search_similar_errors(
    self: CodingMemoryManager, query: str, k: int = 5
) -> list[ErrorRecord]:
    """Search past errors semantically.

    Finds similar past errors using semantic search.

    Args:
        query: Error description or message
        k: Number of results

    Returns:
        List of similar error records

    Example:
        >>> similar = await coding_mem.search_similar_errors(
        ...     "TypeError comparing datetimes", k=5
        ... )
        >>> for error in similar:
        ...     print(f"{error.error_type}: {error.solution}")
    """
    if not self.rag:
        logger.warning("RAG not available, returning empty results")
        return []

    results = self.rag.recall(
        query=query,
        user_id=self.user_id,
        top_k=k * 2,  # Get more candidates for filtering
        agent_name=self.agent_name,
    )

    # Retrieve full error records
    errors = []
    for result in results:
        metadata = result.get("metadata", {})

        # Filter by project_id and type
        if metadata.get("project_id") != self.project_id:
            continue
        if metadata.get("type") != "error":
            continue

        # Extract error ID - try metadata first (more reliable), then ChromaDB ID
        error_id = metadata.get("error_id")  # From Fix #2
        if not error_id:
            # Fallback: ChromaDB content hash (older data)
            error_id = result.get("id")

        if error_id:
            # Construct key and retrieve full record
            if error_id.startswith("error_"):
                # Entity ID format
                key = self._make_key(f"error:{error_id}")
            else:
                # ChromaDB hash - skip (can't map back without reverse index)
                continue

            error_data = self.persistent.recall(key=key, user_id=self.user_id)
            if error_data:
                errors.append(ErrorRecord(**error_data))

            # Stop when we have enough
            if len(errors) >= k:
                break

    return errors
