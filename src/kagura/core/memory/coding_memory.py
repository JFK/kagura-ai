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
from typing import Any, Literal

from kagura.config.memory_config import MemorySystemConfig
from kagura.core.compression import CompressionPolicy
from kagura.core.memory.manager import MemoryManager
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
            vision_model: Vision model for image analysis (None = use gpt-4o)
                Recommended:
                - OpenAI: "gpt-4o"
                - Google: "gemini/gemini-2.0-flash-exp", "gemini/gemini-2.5-flash"
            auto_approve: Skip approval prompts (default: False)
            cost_threshold: Ask approval if operation costs > this (USD, default: 0.10)
            memory_config: Memory system configuration
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
            model=model,
            memory_config=memory_config,
        )

        self.project_id = project_id
        self.current_session_id: str | None = None

        # Initialize LLM analyzers
        # Note: CodingAnalyzer and VisionAnalyzer now accept None and use env defaults
        self.coding_analyzer = CodingAnalyzer(
            model=model if model else None,
            vision_model=vision_model if vision_model else None,
        )
        self.vision_analyzer = VisionAnalyzer(model=vision_model if vision_model else None)

        # Cost tracking
        self.total_cost = 0.0
        self.total_tokens = 0

        # Approval settings
        self.auto_approve = auto_approve
        self.cost_threshold = cost_threshold

        logger.info(
            f"CodingMemoryManager initialized: user={user_id}, project={project_id}"
        )

    def _make_key(self, key: str) -> str:
        """Create project-scoped key.

        Args:
            key: Base key

        Returns:
            Scoped key in format: project:{project_id}:{key}
        """
        return f"project:{self.project_id}:{key}"

    async def track_file_change(
        self,
        file_path: str,
        action: Literal["create", "edit", "delete", "rename", "refactor", "test"],
        diff: str,
        reason: str,
        related_files: list[str] | None = None,
        line_range: tuple[int, int] | None = None,
    ) -> str:
        """Track file modification with context.

        Records file changes with reasoning for cross-session understanding.

        Args:
            file_path: Path to modified file
            action: Type of modification
            diff: Git-style diff or summary of changes
            reason: Why this change was made
            related_files: Other affected/related files
            line_range: Lines affected (start, end)

        Returns:
            Unique ID for this file change record

        Example:
            >>> change_id = await coding_mem.track_file_change(
            ...     file_path="src/auth.py",
            ...     action="edit",
            ...     diff="+ def validate_token(token: str) -> bool:",
            ...     reason="Add token validation for JWT auth",
            ...     related_files=["src/middleware.py"]
            ... )
        """
        record = FileChangeRecord(
            file_path=file_path,
            action=action,
            diff=diff,
            reason=reason,
            related_files=related_files or [],
            session_id=self.current_session_id,
            line_range=line_range,
        )

        # Generate unique ID
        change_id = f"change_{uuid.uuid4().hex[:12]}"

        # Store in persistent memory (user_id scoped)
        key = self._make_key(f"file_change:{change_id}")
        self.persistent.store(
            key=key, value=record.model_dump(mode="json"), user_id=self.user_id
        )

        # Add to RAG if available for semantic search
        if self.persistent_rag:
            content_text = (
                f"File: {file_path}\n"
                f"Action: {action}\n"
                f"Reason: {reason}\n"
                f"Diff: {diff[:500]}"
            )
            self.persistent_rag.store(
                content=content_text,
                user_id=self.user_id,
                metadata={
                    "type": "file_change",
                    "file_path": file_path,
                    "action": action,
                    "project_id": self.project_id,
                    "session_id": self.current_session_id or "",
                },
                agent_name=self.agent_name,
            )

        # Add to graph if available
        if self.graph:
            # Node for file change
            self.graph.add_node(
                node_id=change_id,
                node_type="memory",
                data={
                    "file_path": file_path,
                    "action": action,
                    "reason": reason,
                    "project_id": self.project_id,
                },
            )

            # Link to related files
            for related_file in related_files or []:
                related_key = self._make_key(f"file:{related_file}")
                # Ensure related file node exists
                if not self.graph.graph.has_node(related_key):
                    self.graph.add_node(
                        node_id=related_key,
                        node_type="memory",
                        data={"file_path": related_file},
                    )
                self.graph.add_edge(
                    src_id=change_id,
                    dst_id=related_key,
                    rel_type="related_to",
                    weight=0.8,
                )

            # Link to current session if active
            if self.current_session_id:
                self.graph.add_edge(
                    src_id=self.current_session_id,
                    dst_id=change_id,
                    rel_type="related_to",
                    weight=1.0,
                )

        logger.info(f"Tracked file change: {change_id} ({file_path})")
        return change_id

    async def record_error(
        self,
        error_type: str,
        message: str,
        stack_trace: str,
        file_path: str,
        line_number: int,
        solution: str | None = None,
        screenshot: str | None = None,  # Path or base64
        tags: list[str] | None = None,
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
        self.persistent.store(key=key, value=record.model_dump(mode="json"), user_id=self.user_id)

        # Add to RAG for semantic search
        if self.persistent_rag:
            content_text = (
                f"Error: {error_type}\n"
                f"Message: {message}\n"
                f"File: {file_path}:{line_number}\n"
                f"Solution: {solution or 'Not yet resolved'}"
            )
            self.persistent_rag.store(
                content=content_text,
                user_id=self.user_id,
                metadata={
                    "type": "error",
                    "error_type": error_type,
                    "file_path": file_path,
                    "resolved": record.resolved,
                    "project_id": self.project_id,
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
                    rel_type="related_to",
                    weight=1.0,
                )

        logger.info(f"Recorded error: {error_id} ({error_type})")
        return error_id

    async def record_decision(
        self,
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
        self.persistent.store(key=key, value=record.model_dump(mode="json"), user_id=self.user_id)

        # Add to RAG
        if self.persistent_rag:
            content_text = (
                f"Decision: {decision}\n"
                f"Rationale: {rationale}\n"
                f"Alternatives: {', '.join(alternatives or [])}"
            )
            self.persistent_rag.store(
                content=content_text,
                user_id=self.user_id,
                metadata={
                    "type": "decision",
                    "tags": ",".join(tags or []),  # ChromaDB doesn't support lists
                    "project_id": self.project_id,
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
                    "tags": tags or [],
                    "project_id": self.project_id,
                },
            )

            # Link to session if active
            if self.current_session_id:
                self.graph.add_edge(
                    src_id=self.current_session_id,
                    dst_id=decision_id,
                    rel_type="related_to",
                    weight=1.0,
                )

        logger.info(f"Recorded decision: {decision_id}")
        return decision_id

    async def start_coding_session(
        self, description: str, tags: list[str] | None = None
    ) -> str:
        """Start tracked coding session.

        Initiates a new coding session to group related activities.

        Args:
            description: Brief description of session goals
            tags: Session categorization tags

        Returns:
            Session ID

        Raises:
            RuntimeError: If a session is already active

        Example:
            >>> session_id = await coding_mem.start_coding_session(
            ...     description="Implement JWT authentication system",
            ...     tags=["authentication", "security"]
            ... )
        """
        if self.current_session_id:
            raise RuntimeError(
                f"Session already active: {self.current_session_id}. "
                "End current session before starting a new one."
            )

        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session = CodingSession(
            session_id=session_id,
            user_id=self.user_id,
            project_id=self.project_id,
            description=description,
            start_time=datetime.utcnow(),
            end_time=None,
            tags=tags or [],
            summary=None,
            success=None,
        )

        # Store in working memory (active session)
        self.working.set(f"session:{session_id}", session.model_dump(mode="json"))

        # Store in persistent memory
        key = self._make_key(f"session:{session_id}")
        self.persistent.store(key=key, value=session.model_dump(mode="json"), user_id=self.user_id)

        # Add to graph
        if self.graph:
            self.graph.add_node(
                node_id=session_id,
                node_type="memory",
                data={
                    "description": description,
                    "project_id": self.project_id,
                    "active": True,
                },
            )

        self.current_session_id = session_id
        logger.info(f"Started coding session: {session_id}")
        return session_id

    async def end_coding_session(
        self, summary: str | None = None, success: bool | None = None
    ) -> dict[str, Any]:
        """End coding session and generate summary.

        Ends the active session and optionally generates AI-powered summary.

        Args:
            summary: User-provided summary (if None, auto-generate with LLM)
            success: Whether session objectives were met

        Returns:
            Dictionary with session data and summary

        Raises:
            RuntimeError: If no active session

        Example:
            >>> result = await coding_mem.end_coding_session(
            ...     success=True
            ... )
            >>> print(result['summary'])
            Implemented JWT auth with RS256 signing...
        """
        if not self.current_session_id:
            raise RuntimeError("No active session to end")

        session_id = self.current_session_id

        # Retrieve session from working memory
        session_data = self.working.get(f"session:{session_id}")
        if not session_data:
            raise RuntimeError(f"Session data not found: {session_id}")

        session = CodingSession(**session_data)
        session.end_time = datetime.utcnow()
        session.success = success

        # Retrieve session activities
        file_changes = await self._get_session_file_changes(session_id)
        errors = await self._get_session_errors(session_id)
        decisions = await self._get_session_decisions(session_id)

        session.files_touched = list({fc.file_path for fc in file_changes})
        session.errors_encountered = len(errors)
        session.errors_fixed = sum(1 for e in errors if e.resolved)
        session.decisions_made = len(decisions)

        # Generate summary if not provided
        if summary is None:
            logger.info("Generating AI-powered session summary...")

            # Estimate cost before generating summary
            context_size = (
                len(str(file_changes)) + len(str(errors)) + len(str(decisions)) + 500
            )
            estimated_tokens = self.coding_analyzer.count_tokens(
                str(session_data)[:context_size]
            )
            estimated_cost = self._estimate_llm_cost(
                input_tokens=estimated_tokens,
                output_tokens=1500,  # Expected summary length
            )

            # Ask approval if cost exceeds threshold
            approved = await self._ask_approval_with_cost(
                operation="Generate AI-powered session summary",
                estimated_cost=estimated_cost,
                details=f"Input: ~{estimated_tokens} tokens, Model: {self.coding_analyzer.model}",
            )

            if not approved:
                summary = f"Session ended. {len(file_changes)} files modified, {len(errors)} errors, {len(decisions)} decisions. (AI summary skipped)"
                logger.info("Session summary generation cancelled by user")
            else:
                try:
                    summary = await self.coding_analyzer.summarize_session(
                        session, file_changes, errors, decisions
                    )
                    # Track actual cost (would be updated in analyzer)
                    logger.info(
                        f"Summary generated. Estimated cost: ${estimated_cost:.2f}"
                    )
                except Exception as e:
                    logger.error(f"Summary generation failed: {e}")
                    summary = f"Session ended. {len(file_changes)} files modified, {len(errors)} errors, {len(decisions)} decisions."

        session.summary = summary

        # Update stored session
        key = self._make_key(f"session:{session_id}")
        self.persistent.store(key=key, value=session.model_dump(mode="json"), user_id=self.user_id)

        # Remove from working memory
        self.working.delete(f"session:{session_id}")

        # Update graph (delete and re-add with updated data)
        if self.graph:
            if self.graph.graph.has_node(session_id):
                # Get existing data
                node_data = dict(self.graph.graph.nodes[session_id])
                # Update fields
                node_data["active"] = False
                node_data["success"] = success
                # Remove and re-add
                self.graph.graph.remove_node(session_id)
                self.graph.add_node(
                    node_id=session_id,
                    node_type="memory",
                    data=node_data,
                )

        self.current_session_id = None
        logger.info(f"Ended coding session: {session_id}")

        return {
            "session_id": session_id,
            "duration_minutes": session.duration_minutes,
            "files_touched": session.files_touched,
            "errors_encountered": session.errors_encountered,
            "errors_fixed": session.errors_fixed,
            "decisions_made": session.decisions_made,
            "summary": summary,
            "success": success,
        }

    async def search_similar_errors(self, query: str, k: int = 5) -> list[ErrorRecord]:
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
        if not self.persistent_rag:
            logger.warning("RAG not available, returning empty results")
            return []

        results = self.persistent_rag.recall(
            query=query,
            user_id=self.user_id,
            top_k=k * 2,  # Get more candidates for filtering
            agent_name=self.agent_name,
        )

        # Retrieve full error records
        errors = []
        for result in results[:k]:
            # Filter by project_id and type
            if result.get("metadata", {}).get("project_id") != self.project_id:
                continue
            if result.get("metadata", {}).get("type") != "error":
                continue

            # Extract error ID from result
            # Assuming result has 'id' or we need to extract from metadata
            error_id = result.get("id")
            if error_id:
                key = self._make_key(f"error:{error_id}")
                error_data = self.persistent.recall(key=key, user_id=self.user_id)
                if error_data:
                    errors.append(ErrorRecord(**error_data))

        return errors[:k]

    async def get_project_context(self, focus: str | None = None) -> ProjectContext:
        """Get comprehensive project context.

        Generates AI-powered project context summary.

        Args:
            focus: Optional focus area (e.g., "authentication")

        Returns:
            ProjectContext with structured information

        Example:
            >>> context = await coding_mem.get_project_context(
            ...     focus="authentication"
            ... )
            >>> print(context.summary)
            Python API using FastAPI with JWT authentication...
        """
        # Get recent data
        file_changes = await self._get_recent_file_changes(limit=30)
        decisions = await self._get_recent_decisions(limit=20)
        patterns = await self._get_coding_patterns()

        # Generate context using LLM
        context = await self.coding_analyzer.generate_project_context(
            project_id=self.project_id,
            file_changes=file_changes,
            decisions=decisions,
            patterns=patterns,
            focus=focus,
        )

        return context

    async def analyze_coding_patterns(self) -> dict[str, Any]:
        """Analyze coding patterns and preferences.

        Uses LLM to extract developer's coding style and preferences.

        Returns:
            Dictionary with extracted preferences

        Example:
            >>> patterns = await coding_mem.analyze_coding_patterns()
            >>> print(patterns['language_preferences']['type_annotations'])
            {'style': 'always', 'confidence': 'high'}
        """
        file_changes = await self._get_recent_file_changes(limit=50)
        decisions = await self._get_recent_decisions(limit=30)

        preferences = await self.coding_analyzer.extract_coding_preferences(
            file_changes, decisions
        )

        return preferences

    # Helper methods

    async def _get_session_file_changes(
        self, session_id: str
    ) -> list[FileChangeRecord]:
        """Get file changes for session."""
        # TODO: Implement graph traversal or RAG search
        return []

    async def _get_session_errors(self, session_id: str) -> list[ErrorRecord]:
        """Get errors for session."""
        # TODO: Implement graph traversal or RAG search
        return []

    async def _get_session_decisions(self, session_id: str) -> list[DesignDecision]:
        """Get decisions for session."""
        # TODO: Implement graph traversal or RAG search
        return []

    async def _get_recent_file_changes(self, limit: int = 30) -> list[FileChangeRecord]:
        """Get recent file changes."""
        # TODO: Implement time-based query
        return []

    async def _get_recent_decisions(self, limit: int = 20) -> list[DesignDecision]:
        """Get recent decisions."""
        # TODO: Implement time-based query
        return []

    async def _get_coding_patterns(self) -> list[CodingPattern]:
        """Get identified coding patterns."""
        # TODO: Implement pattern retrieval
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
                f"{operation}: ${estimated_cost:.2f} < threshold ${self.cost_threshold:.2f}, auto-approved"
            )
            return True

        # Build prompt
        prompt = f"{operation}\n\n"
        prompt += f"[bold]Estimated Cost:[/] ${estimated_cost:.2f}"

        if details:
            prompt += f"\n[dim]{details}[/]"

        return await self._ask_approval(prompt)
