"""Coding-specialized memory manager.

Extends the base MemoryManager with coding-specific features:
- Project-scoped memory (user_id + project_id)
- File change tracking
- Error pattern learning
- Design decision recording
- Coding session management
- LLM-powered analysis and summarization
- Approval workflows for expensive operations
- Cost estimation and tracking
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from kagura.config.memory_config import MemorySystemConfig
from kagura.core.compression import CompressionPolicy
from kagura.core.memory.coding_dependency import DependencyAnalyzer
from kagura.core.memory.github_recorder import GitHubRecordConfig, GitHubRecorder
from kagura.core.memory.interaction_tracker import InteractionTracker
from kagura.core.memory.manager import MemoryManager
from kagura.core.memory.memory_abstractor import MemoryAbstractor
from kagura.core.memory.models.coding import (
    CodingPattern,
    CodingSession,
    DesignDecision,
    ErrorRecord,
    FileChangeRecord,
    ProjectContext,
)
from kagura.llm.coding_analyzer import CodingAnalyzer
from kagura.llm.vision import VisionAnalyzer

logger = logging.getLogger(__name__)


class UserCancelledError(Exception):
    """Raised when user cancels an operation."""

    pass


class CodingMemoryManager(MemoryManager):
    """Coding-specialized memory manager.

    Extends MemoryManager with coding-specific features for AI coding assistants.
    Maintains project-scoped memory (user_id + project_id) and tracks:
    - File modifications with context
    - Errors and their solutions
    - Design decisions and rationale
    - Coding sessions
    - Learned patterns and preferences

    Attributes:
        project_id: Project identifier for scope isolation
        coding_analyzer: LLM-powered coding context analyzer
        vision_analyzer: Vision-capable analyzer for screenshots/diagrams
        current_session_id: ID of active coding session (None if no active session)
    """

    def __init__(
        self,
        user_id: str,
        project_id: str,
        agent_name: str | None = None,
        persist_dir: Path | None = None,
        max_messages: int = 100,
        enable_rag: bool | None = None,
        enable_graph: bool = True,
        enable_compression: bool = True,
        compression_policy: CompressionPolicy | None = None,
        model: str | None = None,
        vision_model: str | None = None,
        auto_approve: bool = False,
        cost_threshold: float = 0.10,
        memory_config: MemorySystemConfig | None = None,
        enable_github_recording: bool = True,
        enable_interaction_tracking: bool = True,
        enable_memory_abstraction: bool = True,
        abstraction_level1_model: str = "gpt-5-mini",
        abstraction_level2_model: str = "gpt-5",
    ) -> None:
        """Initialize coding memory manager.

        Args:
            user_id: User identifier (developer)
            project_id: Project identifier for scope isolation
            agent_name: Optional agent name
            persist_dir: Directory for persistent storage
            max_messages: Maximum messages in context
            enable_rag: Enable RAG (vector search)
            enable_graph: Enable graph memory for relationships
            enable_compression: Enable context compression
            compression_policy: Compression configuration
            model: LLM model for analysis (None = use environment default)
                Recommended models:
                - Fast: "gpt-5-mini", "gemini/gemini-2.0-flash-exp"
                - Balanced: "gpt-5", "gemini/gemini-2.5-flash"
                - Premium: "claude-sonnet-4-5", "gemini/gemini-2.5-pro"
            vision_model: Vision model for image analysis
                (None = gemini-2.0-flash-exp default)
                Recommended:
                - Google: "gemini/gemini-2.0-flash-exp" (DEFAULT, free, excellent)
                - Google: "gemini/gemini-2.5-flash" (production, $0.075/1M)
                - OpenAI: "gpt-4o" (alternative, $2.50/1M)
            auto_approve: Skip approval prompts (default: False)
            cost_threshold: Ask approval if operation costs > this (USD, default: 0.10)
            memory_config: Memory system configuration
            enable_github_recording: Enable GitHub Issue recording (default: True)
            enable_interaction_tracking: Enable interaction tracking (default: True)
            enable_memory_abstraction: Enable memory abstraction (default: True)
            abstraction_level1_model: LLM for level 1 abstraction (default: gpt-5-mini)
            abstraction_level2_model: LLM for level 2 abstraction (default: gpt-5)
        """
        # Initialize base memory manager with user_id
        super().__init__(
            user_id=user_id,
            agent_name=agent_name,
            persist_dir=persist_dir,
            max_messages=max_messages,
            enable_rag=enable_rag,
            enable_graph=enable_graph,
            enable_compression=enable_compression,
            compression_policy=compression_policy,
            model=model or "gpt-4o-mini",  # Default if None
            memory_config=memory_config,
        )

        self.project_id = project_id
        # Auto-detect active session from working memory (v4.0.9 cache fix)
        self.current_session_id: str | None = self._detect_active_session()  # type: ignore[attr-defined]

        # Initialize LLM analyzers
        # Note: CodingAnalyzer and VisionAnalyzer now accept None and use env defaults
        self.coding_analyzer = CodingAnalyzer(
            model=model if model else None,
            vision_model=vision_model if vision_model else None,
        )
        self.vision_analyzer = VisionAnalyzer(
            model=vision_model if vision_model else None
        )

        # Initialize dependency analyzer (Phase 2)
        self.dependency_analyzer: DependencyAnalyzer | None = None
        if persist_dir:
            # Use persist_dir parent as project root
            project_root = persist_dir.parent
            self.dependency_analyzer = DependencyAnalyzer(project_root)

        # Cost tracking
        self.total_cost = 0.0
        self.total_tokens = 0

        # Approval settings
        self.auto_approve = auto_approve
        self.cost_threshold = cost_threshold

        # Instance-level lock for session management (prevents race conditions)
        self._session_lock = asyncio.Lock()

        # v4.0.7: Initialize new components for Issue #493
        # InteractionTracker for hybrid buffering
        self.interaction_tracker: InteractionTracker | None = None
        if enable_interaction_tracking:
            self.interaction_tracker = InteractionTracker(
                importance_threshold=8.0,
                flush_interval_seconds=300,  # 5 minutes
                flush_count_threshold=10,
            )

        # GitHubRecorder for external recording
        self.github_recorder: GitHubRecorder | None = None
        if enable_github_recording:
            github_config = GitHubRecordConfig(
                repo=None,  # Auto-detect
                auto_detect_issue=True,
                enabled=True,
            )
            self.github_recorder = GitHubRecorder(config=github_config)

        # MemoryAbstractor for 2-level abstraction
        self.memory_abstractor: MemoryAbstractor | None = None
        if enable_memory_abstraction:
            self.memory_abstractor = MemoryAbstractor(
                level1_model=abstraction_level1_model,
                level2_model=abstraction_level2_model,
                enable_level2=True,
            )

        logger.info(
            f"CodingMemoryManager initialized: user={user_id}, project={project_id}, "
            f"interaction_tracking={enable_interaction_tracking}, "
            f"github_recording={enable_github_recording}, "
            f"abstraction={enable_memory_abstraction}"
        )

    def _make_key(self, key: str) -> str:
        """Create project-scoped key.

        Args:
            key: Base key

        Returns:
            Scoped key in format: project:{project_id}:{key}
        """
        return f"project:{self.project_id}:{key}"

    def _ensure_graph_node(
        self, node_id: str, node_type: str, data: dict[str, Any]
    ) -> None:
        """Ensure graph node exists (create if not exists).

        Helper to avoid duplicated node existence checks throughout the code.

        Args:
            node_id: Unique node identifier
            node_type: Node type
            data: Node data dictionary
        """
        if not self.graph:
            return

        if not self.graph.graph.has_node(node_id):
            self.graph.add_node(node_id=node_id, node_type=node_type, data=data)


    async def _get_session_records(
        self,
        session_id: str,
        record_type: str,
        record_class: type,
    ) -> list:
        """Generic method to get session records by type.

        Extracted common pattern from _get_session_file_changes/errors/decisions.

        Args:
            session_id: Session ID
            record_type: Type prefix (e.g., "file_change", "error", "decision")
            record_class: Record class for validation

        Returns:
            List of records associated with session
        """
        import json

        records = []

        # Query persistent storage by session_id (primary method)
        pattern = f"project:{self.project_id}:{record_type}:%"
        all_records = self.persistent.search(
            query=pattern, user_id=self.user_id, limit=1000
        )

        for record_data in all_records:
            try:
                value_str = record_data.get("value", "{}")
                data = (
                    json.loads(value_str) if isinstance(value_str, str) else value_str
                )
                if data.get("session_id") == session_id:
                    records.append(record_class(**data))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

        # Fallback: Use graph if available and no records found
        if not records and self.graph and self.graph.graph.has_node(session_id):
            for _, dst_id, edge_data in self.graph.graph.out_edges(  # type: ignore[misc]
                session_id, data=True
            ):
                # Map record_type to node ID prefix
                prefix_map = {
                    "file_change": "change_",
                    "error": "error_",
                    "decision": "decision_",
                }
                prefix = prefix_map.get(record_type, f"{record_type}_")
                if dst_id.startswith(prefix):
                    key = self._make_key(f"{record_type}:{dst_id}")
                    data = self.persistent.recall(key=key, user_id=self.user_id)
                    if data:
                        records.append(record_class(**data))

        return records

    async def _get_session_file_changes(
        self, session_id: str
    ) -> list[FileChangeRecord]:
        """Get file changes for session.

        Args:
            session_id: Session ID

        Returns:
            List of file changes associated with session
        """
        return await self._get_session_records(
            session_id=session_id,
            record_type="file_change",
            record_class=FileChangeRecord,
        )

    async def _get_session_errors(self, session_id: str) -> list[ErrorRecord]:
        """Get errors for session.

        Args:
            session_id: Session ID

        Returns:
            List of errors associated with session
        """
        return await self._get_session_records(
            session_id=session_id, record_type="error", record_class=ErrorRecord
        )

    async def _get_session_decisions(self, session_id: str) -> list[DesignDecision]:
        """Get decisions for session.

        Args:
            session_id: Session ID

        Returns:
            List of decisions associated with session
        """
        return await self._get_session_records(
            session_id=session_id, record_type="decision", record_class=DesignDecision
        )

    async def _get_recent_file_changes(self, limit: int = 30) -> list[FileChangeRecord]:
        """Get recent file changes.

        Args:
            limit: Maximum number of changes to return

        Returns:
            List of recent file changes, sorted by timestamp (newest first)
        """
        # Method 1: Use RAG if available
        if self.persistent_rag:
            results = self.persistent_rag.recall(
                query="recent file changes in project",
                user_id=self.user_id,
                top_k=limit * 2,  # Get more candidates
                agent_name=self.agent_name,
            )

            file_changes = []
            for result in results:
                metadata = result.get("metadata", {})
                if metadata.get("type") == "file_change":
                    if metadata.get("project_id") == self.project_id:
                        # Get entity ID from metadata (Fix #2)
                        change_id = metadata.get("change_id")
                        if not change_id:
                            # Fallback to ChromaDB ID
                            change_id = result.get("id", "")

                        if change_id and change_id.startswith("change_"):
                            key = self._make_key(f"file_change:{change_id}")
                            data = self.persistent.recall(key=key, user_id=self.user_id)
                            if data:
                                file_changes.append(FileChangeRecord(**data))

            # Sort by timestamp and limit
            file_changes.sort(key=lambda x: x.timestamp, reverse=True)
            return file_changes[:limit]

        return []

    async def _get_recent_decisions(self, limit: int = 20) -> list[DesignDecision]:
        """Get recent decisions.

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of recent decisions, sorted by timestamp (newest first)
        """
        # Use RAG if available
        if self.persistent_rag:
            results = self.persistent_rag.recall(
                query="design decisions",
                user_id=self.user_id,
                top_k=limit * 2,
                agent_name=self.agent_name,
            )

            decisions = []
            for result in results:
                metadata = result.get("metadata", {})
                if metadata.get("type") == "decision":
                    if metadata.get("project_id") == self.project_id:
                        # Get entity ID from metadata (Fix #2)
                        decision_id = metadata.get("decision_id")
                        if not decision_id:
                            # Fallback to ChromaDB ID
                            decision_id = result.get("id", "")

                        if decision_id and decision_id.startswith("decision_"):
                            key = self._make_key(f"decision:{decision_id}")
                            data = self.persistent.recall(key=key, user_id=self.user_id)
                            if data:
                                decisions.append(DesignDecision(**data))

            decisions.sort(key=lambda x: x.timestamp, reverse=True)
            return decisions[:limit]

        return []

    async def _get_coding_patterns(self) -> list[CodingPattern]:
        """Get identified coding patterns.

        Returns:
            List of identified coding patterns
        """
        # Patterns would be stored separately after analysis
        # For now, return empty list (patterns are generated on-demand)
        # Future: Store analyzed patterns in persistent storage
        return []

    # Approval and Cost Estimation Methods

    async def _ask_approval(
        self,
        prompt: str,
        timeout: float = 60.0,
        default: bool = True,
    ) -> bool:
        """Ask user for approval with Rich UI.

        Args:
            prompt: Question to ask user
            timeout: Timeout in seconds (default: 60.0)
            default: Default value if timeout/error (default: True)

        Returns:
            True if approved, False if rejected

        Example:
            >>> approved = await memory._ask_approval(
            ...     "Generate expensive summary for $0.50?"
            ... )
            >>> if not approved:
            ...     raise UserCancelledError("Operation cancelled")
        """
        # Skip if auto_approve is enabled
        if self.auto_approve:
            logger.info(f"Auto-approved: {prompt}")
            return True

        try:
            from rich.console import Console
            from rich.panel import Panel

            console = Console()

            # Show prompt in panel
            console.print(
                Panel(
                    prompt,
                    title="[bold yellow]⚠️  Approval Required[/]",
                    border_style="yellow",
                )
            )

            # Ask for input
            console.print("[yellow]Approve? [Y/n]:[/] ", end="")

            # Use asyncio to get input with timeout
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, input),
                timeout=timeout,
            )

            result = response.strip().lower() in ("", "y", "yes")
            if not result:
                console.print("[yellow]❌ Operation cancelled by user[/]")
            return result

        except asyncio.TimeoutError:
            logger.warning(f"Approval timeout - using default ({default})")
            print(f"\n[dim]Timeout - using default ({default})[/]")
            return default

        except (EOFError, KeyboardInterrupt):
            logger.info("Approval cancelled by user (EOF/KeyboardInterrupt)")
            print("\n[yellow]❌ Cancelled[/]")
            return False

        except Exception as e:
            logger.error(f"Approval error: {e}")
            print(f"\n[red]Error: {e}[/]")
            return default

    def _estimate_llm_cost(
        self,
        input_tokens: int,
        output_tokens: int = 1500,
        model: str | None = None,
    ) -> float:
        """Estimate LLM API cost.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Expected output tokens (default: 1500)
            model: Model name (default: self.coding_analyzer.model)

        Returns:
            Estimated cost in USD

        Example:
            >>> cost = memory._estimate_llm_cost(
            ...     input_tokens=5000,
            ...     output_tokens=2000,
            ...     model="gpt-4"
            ... )
            >>> print(f"Estimated cost: ${cost:.2f}")
            Estimated cost: $0.35
        """
        try:
            from kagura.observability.pricing import calculate_cost

            usage = {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
            }

            model_name = model or self.coding_analyzer.model
            cost = calculate_cost(usage, model_name)

            return cost

        except Exception as e:
            logger.warning(f"Cost estimation failed: {e}")
            # Return conservative estimate
            return (input_tokens + output_tokens) / 1000 * 0.03  # ~$0.03 per 1K tokens

    async def _ask_approval_with_cost(
        self,
        operation: str,
        estimated_cost: float,
        details: str | None = None,
    ) -> bool:
        """Ask approval with cost information.

        Args:
            operation: Operation name (e.g., "Generate session summary")
            estimated_cost: Estimated cost in USD
            details: Additional details to show

        Returns:
            True if approved, False if rejected

        Example:
            >>> approved = await memory._ask_approval_with_cost(
            ...     operation="Generate session summary",
            ...     estimated_cost=0.25,
            ...     details="5000 tokens input, GPT-4"
            ... )
        """
        # Skip if below cost threshold
        if estimated_cost < self.cost_threshold:
            logger.info(
                f"{operation}: ${estimated_cost:.2f} < "
                f"threshold ${self.cost_threshold:.2f}, auto-approved"
            )
            return True

        # Build prompt
        prompt = f"{operation}\n\n"
        prompt += f"[bold]Estimated Cost:[/] ${estimated_cost:.2f}"

        if details:
            prompt += f"\n[dim]{details}[/]"

        return await self._ask_approval(prompt)

