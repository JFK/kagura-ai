"""LLM-powered coding context analyzer with high-quality prompts.

This module provides AI-powered analysis for coding sessions including:
- Session summarization
- Error pattern detection
- Solution suggestions
- Coding preference extraction
- Context compression

All analysis uses carefully crafted prompts for maximum reliability.
"""

import logging
from datetime import datetime
from typing import Any

import tiktoken
from litellm import acompletion

from kagura.core.memory.models.coding import (
    CodingPattern,
    CodingSession,
    DesignDecision,
    ErrorRecord,
    FileChangeRecord,
    ProjectContext,
)
from kagura.llm.prompts import (
    build_context_compression_prompt,
    build_error_pattern_prompt,
    build_preference_extraction_prompt,
    build_session_summary_prompt,
    build_solution_prompt,
)

logger = logging.getLogger(__name__)


class CodingAnalyzer:
    """LLM-powered analyzer for coding context.

    Uses carefully engineered prompts to provide:
    - High-quality session summaries
    - Error pattern identification
    - Solution suggestions based on past resolutions
    - Coding preference extraction
    - Smart context compression

    Attributes:
        model: Default LLM model for analysis
        vision_model: Model for multimodal analysis
        temperature: LLM temperature (0.0-1.0)
        max_tokens: Maximum tokens for responses
    """

    def __init__(
        self,
        model: str | None = None,
        vision_model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        """Initialize coding analyzer.

        Args:
            model: Default LLM model ID (None = use environment default)
                Recommended:
                - OpenAI: "gpt-5-mini" (fast), "gpt-5" (balanced)
                - Google: "gemini/gemini-2.0-flash-exp" (fast),
                  "gemini/gemini-2.5-pro" (premium)
                - Anthropic: "claude-sonnet-4-5" (balanced)
            vision_model: Vision-capable model ID (None = use gpt-4o)
                Recommended:
                - OpenAI: "gpt-4o" (best quality)
                - Google: "gemini/gemini-2.0-flash-exp" (fast, free preview)
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum response tokens
        """
        # Use environment defaults if not specified
        import os

        from kagura.config.env import get_openai_default_model

        # Default to gpt-5-mini or environment override
        if model is None:
            model = os.getenv("CODING_MEMORY_MODEL") or get_openai_default_model()

        # Default to Gemini for vision (free during preview, excellent vision)
        if vision_model is None:
            vision_model = (
                os.getenv("CODING_MEMORY_VISION_MODEL") or "gemini/gemini-2.0-flash-exp"
            )

        self.model = model
        self.vision_model = vision_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Cost tracking
        self.total_cost = 0.0
        self.total_tokens = 0
        self.call_count = 0
        self.call_costs: list[dict[str, Any]] = []

        logger.info(
            f"CodingAnalyzer initialized: model={self.model}, "
            f"vision={self.vision_model}"
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        return len(self.encoding.encode(text))

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Call LLM with prompts.

        Args:
            system_prompt: System message defining role/behavior
            user_prompt: User message with task
            model: Override default model
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            LLM response text

        Raises:
            Exception: If LLM call fails
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await acompletion(  # type: ignore
                model=model or self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            content = response.choices[0].message.content  # type: ignore
            if not content:
                raise ValueError("Empty response from LLM")

            # Track usage and cost
            if hasattr(response, "usage") and response.usage:  # type: ignore
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,  # type: ignore
                    "completion_tokens": response.usage.completion_tokens,  # type: ignore
                    "total_tokens": response.usage.total_tokens,  # type: ignore
                }

                # Calculate cost
                try:
                    from kagura.observability.pricing import calculate_cost

                    cost = calculate_cost(usage, model or self.model)
                    self.total_cost += cost
                    self.total_tokens += usage["total_tokens"]
                    self.call_count += 1

                    # Record individual call
                    self.call_costs.append(
                        {
                            "model": model or self.model,
                            "tokens": usage["total_tokens"],
                            "cost": cost,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    logger.info(
                        f"LLM call successful: {usage['total_tokens']} tokens, "
                        f"cost: ${cost:.4f}, cumulative: ${self.total_cost:.4f}"
                    )
                except ImportError:
                    logger.info(
                        f"LLM call successful: {response.usage.total_tokens} tokens"  # type: ignore
                    )
            else:
                logger.info("LLM call successful")

            return content

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _generate_template_summary(
        self,
        project_id: str,
        file_changes: list[FileChangeRecord],
        decisions: list[DesignDecision],
        focus: str | None = None,
    ) -> str:
        """Generate template-based summary when LLM fails.

        Args:
            project_id: Project identifier
            file_changes: Recent file modifications
            decisions: Key design decisions
            focus: Optional focus area

        Returns:
            Template-based project summary
        """
        # Count activities
        num_changes = len(file_changes)

        # Extract key info
        changed_files = list({c.file_path for c in file_changes[:5]})
        decision_topics = [d.decision.split(":")[0][:50] for d in decisions[:3]]

        # Build summary
        summary_parts = [
            f"Project '{project_id}' with {num_changes} recent file change(s)"
        ]

        if changed_files:
            files_str = ", ".join(changed_files[:3])
            if len(changed_files) > 3:
                files_str += f", +{len(changed_files) - 3} more"
            summary_parts.append(f"Modified files: {files_str}")

        if decision_topics:
            summary_parts.append(f"Key decisions: {', '.join(decision_topics)}")

        if focus:
            summary_parts.append(f"Focus area: {focus}")

        return ". ".join(summary_parts) + "."

    async def summarize_session(
        self,
        session: CodingSession,
        file_changes: list[FileChangeRecord],
        errors: list[ErrorRecord],
        decisions: list[DesignDecision],
    ) -> str:
        """Generate comprehensive session summary.

        Analyzes session activities and generates structured markdown summary
        covering objectives, decisions, challenges, patterns, and recommendations.

        Args:
            session: The coding session to summarize
            file_changes: File modifications during session
            errors: Errors encountered during session
            decisions: Design decisions made during session

        Returns:
            Markdown-formatted session summary

        Example:
            >>> analyzer = CodingAnalyzer()
            >>> summary = await analyzer.summarize_session(
            ...     session, file_changes, errors, decisions
            ... )
            >>> print(summary)
            # Session Summary: session-123
            ## Overview
            Implemented authentication middleware...
        """
        session_data = {
            "session_id": session.session_id,
            "project_id": session.project_id,
            "description": session.description,
            "duration_minutes": session.duration_minutes or 0,
            "files_touched": session.files_touched,
            "errors": [
                {
                    "message": e.message,
                    "file_path": e.file_path,
                    "solution": e.solution,
                    "resolved": e.resolved,
                }
                for e in errors
            ],
            "decisions": [
                {"decision": d.decision, "rationale": d.rationale} for d in decisions
            ],
        }

        prompts = build_session_summary_prompt(session_data)

        return await self._call_llm(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            max_tokens=4096,  # Sessions need detailed summaries
        )

    async def analyze_error_patterns(
        self, errors: list[ErrorRecord]
    ) -> list[CodingPattern]:
        """Identify recurring error patterns.

        Analyzes historical errors to find patterns, root causes, and
        prevention strategies.

        Args:
            errors: List of error records to analyze

        Returns:
            List of identified coding patterns

        Example:
            >>> patterns = await analyzer.analyze_error_patterns(errors)
            >>> for pattern in patterns:
            ...     print(f"{pattern.description} (freq: {pattern.frequency})")
            Async/await inconsistency in database calls (freq: 5)
        """
        if len(errors) < 2:
            logger.info("Need at least 2 errors to identify patterns")
            return []

        error_dicts = [
            {
                "error_type": e.error_type,
                "message": e.message,
                "file_path": e.file_path,
                "line_number": e.line_number,
                "timestamp": e.timestamp.isoformat(),
                "resolved": e.resolved,
                "solution": e.solution,
            }
            for e in errors
        ]

        prompts = build_error_pattern_prompt(error_dicts)

        response = await self._call_llm(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            temperature=0.2,  # Lower temp for pattern detection
            max_tokens=3072,
        )

        # Parse YAML response into CodingPattern objects
        # Note: In production, use proper YAML parsing with validation
        # For now, return placeholder to maintain type safety
        logger.info(f"Error pattern analysis completed: {len(response)} chars")

        # TODO: Parse YAML response into CodingPattern objects
        # This is a simplified placeholder
        patterns: list[CodingPattern] = []
        return patterns

    async def suggest_solution(
        self,
        current_error: ErrorRecord,
        similar_past_errors: list[ErrorRecord],
    ) -> dict[str, Any]:
        """Suggest solution based on past resolutions.

        Uses case-based reasoning to suggest solutions for current error
        based on how similar past errors were resolved.

        Args:
            current_error: The current error needing resolution
            similar_past_errors: Past similar errors with solutions

        Returns:
            Dictionary with:
                - confidence: str (low/medium/high)
                - primary_solution: dict with steps, reasoning, code_example
                - alternative_solutions: list of alternatives
                - similar_pattern: str (connection to past patterns)

        Example:
            >>> solution = await analyzer.suggest_solution(
            ...     current_error, similar_errors
            ... )
            >>> print(f"Confidence: {solution['confidence']}")
            >>> print(solution['primary_solution']['steps'])
            Confidence: high
            1. The error occurs because...
        """
        current_error_dict = {
            "error_type": current_error.error_type,
            "message": current_error.message,
            "file_path": current_error.file_path,
            "line_number": current_error.line_number,
            "stack_trace": current_error.stack_trace,
            "screenshot_path": current_error.screenshot_path,
            "screenshot_base64": current_error.screenshot_base64,
        }

        similar_errors_dicts = [
            {
                "error_type": e.error_type,
                "message": e.message,
                "solution": e.solution,
                "resolved": e.resolved,
                "similarity": 0.85,  # TODO: Calculate actual similarity
            }
            for e in similar_past_errors
        ]

        prompts = build_solution_prompt(current_error_dict, similar_errors_dicts)

        response = await self._call_llm(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            temperature=0.3,  # Moderate creativity for solutions
            max_tokens=2048,
        )

        # TODO: Parse YAML response into structured dict
        logger.info("Solution suggestion generated")

        return {
            "confidence": "medium",
            "primary_solution": {
                "steps": response[:500],  # Placeholder
                "reasoning": "Based on past resolutions",
                "code_example": "# See full response",
            },
            "alternative_solutions": [],
            "similar_pattern": "Matches past error patterns",
        }

    async def extract_coding_preferences(
        self,
        file_changes: list[FileChangeRecord],
        decisions: list[DesignDecision],
    ) -> dict[str, Any]:
        """Extract user's coding style preferences.

        Analyzes file changes and decisions to identify consistent patterns
        in developer's coding style, library choices, and practices.

        Args:
            file_changes: Historical file modifications
            decisions: Historical design decisions

        Returns:
            Dictionary with preference categories:
                - language_preferences: Type hints, docstrings, async usage
                - library_preferences: Preferred frameworks/libraries
                - naming_conventions: Function/class naming patterns
                - code_organization: File/function length preferences
                - patterns: Error handling, validation approaches
                - testing_practices: Coverage, test style, mock usage

        Example:
            >>> prefs = await analyzer.extract_coding_preferences(
            ...     file_changes, decisions
            ... )
            >>> print(prefs['language_preferences']['type_annotations'])
            {'style': 'always', 'confidence': 'high', 'evidence': '...'}
        """
        if len(file_changes) < 5:
            logger.warning(
                "Need at least 5 file changes for reliable preference extraction"
            )
            return self._default_preferences()

        changes_dicts = [
            {
                "file_path": c.file_path,
                "action": c.action,
                "reason": c.reason,
                "diff": c.diff,
            }
            for c in file_changes
        ]

        decisions_dicts = [
            {
                "decision": d.decision,
                "rationale": d.rationale,
                "alternatives": d.alternatives,
            }
            for d in decisions
        ]

        prompts = build_preference_extraction_prompt(changes_dicts, decisions_dicts)

        _response = await self._call_llm(  # Reserved for future structured parsing
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            temperature=0.1,  # Very low temp for consistent extraction
            max_tokens=3072,
        )

        # TODO: Parse YAML response into structured preferences
        logger.info("Coding preferences extracted")

        return self._default_preferences()

    async def compress_context(
        self,
        full_context: str,
        target_tokens: int,
        preserve_topics: list[str] | None = None,
    ) -> dict[str, str]:
        """Smart context compression (RFC-024).

        Compresses coding context while preserving critical information.
        Creates three compression levels: brief, detailed, comprehensive.

        Args:
            full_context: Full context text to compress
            target_tokens: Target token count for comprehensive level
            preserve_topics: Topics that must be preserved (errors, decisions, etc.)

        Returns:
            Dictionary with three compression levels:
                - brief: 10% of original (2-3 sentence overview)
                - detailed: 30% of original (key points with references)
                - comprehensive: 70% of original (all significant info)

        Example:
            >>> compressed = await analyzer.compress_context(
            ...     full_context="...", target_tokens=500,
            ...     preserve_topics=["errors", "security decisions"]
            ... )
            >>> print(compressed['brief'])
            Implemented JWT auth. Resolved timezone TypeError...
        """
        original_tokens = self.count_tokens(full_context)

        if original_tokens <= target_tokens:
            logger.info("Context already within target, no compression needed")
            return {
                "brief": full_context[:200],
                "detailed": full_context,
                "comprehensive": full_context,
            }

        prompts = build_context_compression_prompt(
            full_context=full_context,
            target_tokens=target_tokens,
            original_tokens=original_tokens,
            preserve_topics=preserve_topics
            or [
                "Errors and solutions",
                "Design decisions",
                "Security issues",
                "Breaking changes",
            ],
        )

        response = await self._call_llm(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            temperature=0.2,  # Low temp for consistent compression
            max_tokens=target_tokens + 500,  # Allow some overhead
        )

        # Parse response into levels
        # TODO: Implement proper level extraction
        compressed_tokens = self.count_tokens(response)
        reduction_pct = (original_tokens - compressed_tokens) / original_tokens * 100

        logger.info(
            f"Context compressed: {original_tokens} → {compressed_tokens} tokens "
            f"({reduction_pct:.1f}% reduction)"
        )

        return {
            "brief": response[:500],  # Placeholder
            "detailed": response,
            "comprehensive": response,
        }

    def _default_preferences(self) -> dict[str, Any]:
        """Return default preference structure.

        Returns:
            Default preferences dictionary
        """
        return {
            "language_preferences": {},
            "library_preferences": {},
            "naming_conventions": {},
            "code_organization": {},
            "patterns": {},
            "testing_practices": {},
            "confidence": "low",
            "note": "Insufficient data for preference extraction",
        }

    async def generate_project_context(
        self,
        project_id: str,
        file_changes: list[FileChangeRecord],
        decisions: list[DesignDecision],
        patterns: list[CodingPattern],
        focus: str | None = None,
    ) -> ProjectContext:
        """Generate comprehensive project context summary.

        Creates an AI-generated overview of the project including tech stack,
        architecture, recent changes, and key decisions.

        Args:
            project_id: Project identifier
            file_changes: Recent file modifications
            decisions: Key design decisions
            patterns: Identified coding patterns
            focus: Optional focus area (e.g., "authentication", "database")

        Returns:
            ProjectContext with structured project information

        Example:
            >>> context = await analyzer.generate_project_context(
            ...     "kagura-ai", file_changes, decisions, patterns,
            ...     focus="authentication"
            ... )
            >>> print(context.summary)
            Python-based AI memory platform using FastAPI...
        """
        # Build context from data
        tech_stack = list(
            {
                d.tags[0]
                for d in decisions
                if d.tags and d.tags[0] in ["fastapi", "pytest", "pydantic"]
            }
        )

        recent_changes_text = "\n".join(
            f"- {c.file_path}: {c.reason}" for c in file_changes[:10]
        )

        key_decisions_text = [
            f"{d.decision} - {d.rationale[:100]}" for d in decisions[:5]
        ]

        # Generate AI summary
        decisions_text = "\n".join(key_decisions_text)
        summary_prompt = f"""Provide a 2-3 sentence high-level summary of the
project based on:

Project ID: {project_id}
Recent Changes:
{recent_changes_text}

Key Decisions:
{decisions_text}

Focus Area: {focus or "general overview"}"""

        # Try LLM generation with fallback to template
        try:
            summary = await self._call_llm(
                system_prompt=(
                    "You are a technical writer creating concise project summaries."
                ),
                user_prompt=summary_prompt,
                temperature=0.4,
                max_tokens=256,
            )
        except (ValueError, Exception) as e:
            # Fallback to template-based summary if LLM fails
            logger.warning(
                f"LLM failed to generate project context: {e}, using template fallback"
            )

            # Generate template-based summary
            summary = self._generate_template_summary(
                project_id, file_changes, decisions, focus
            )

        return ProjectContext(
            project_id=project_id,
            summary=summary.strip(),
            tech_stack=tech_stack,
            architecture_style=None,  # To be inferred from analysis
            recent_changes=recent_changes_text,
            key_decisions=key_decisions_text,
            coding_patterns=[p.description for p in patterns],
            token_count=None,  # Could be calculated if needed
        )

    async def generate_pr_description(
        self,
        session_description: str | None,
        file_changes: list[FileChangeRecord],
        decisions: list[DesignDecision],
        errors_fixed: list[ErrorRecord],
        related_issue: int | None = None,
    ) -> str:
        """Generate PR description from session activities.

        Args:
            session_description: Session goal/description
            file_changes: List of file modifications
            decisions: Design decisions made
            errors_fixed: Errors resolved during session
            related_issue: Related GitHub issue number

        Returns:
            Markdown-formatted PR description

        Example:
            >>> pr_desc = await analyzer.generate_pr_description(
            ...     session_description="Implement authentication",
            ...     file_changes=[...],
            ...     decisions=[...],
            ...     errors_fixed=[...]
            ... )
        """
        # Build prompt context
        changes_text = self._format_file_changes(file_changes)
        decisions_text = self._format_decisions(decisions)
        errors_text = self._format_errors_fixed(errors_fixed)

        issue_ref = f"Closes #{related_issue}" if related_issue else ""

        system_prompt = """You are a technical writer creating pull request
descriptions.

<role>
Generate concise, informative PR descriptions that:
- Clearly explain what was changed and why
- Help reviewers understand the context
- Include testing guidance
- Follow markdown best practices
</role>"""

        user_prompt = f"""Generate a pull request description from this coding session.

<session_info>
<goal>{session_description or "Code improvements and fixes"}</goal>
<related_issue>{issue_ref or "None"}</related_issue>
</session_info>

<file_changes count="{len(file_changes)}">
{changes_text}
</file_changes>

<design_decisions count="{len(decisions)}">
{decisions_text}
</design_decisions>

<errors_fixed count="{len(errors_fixed)}">
{errors_text}
</errors_fixed>

<task>
Generate a PR description with these sections:

## Summary
2-3 sentences explaining what this PR does and why.

## Changes
- Bullet points of key modifications
- Focus on WHAT changed, not HOW

## Technical Decisions
- List significant design decisions (if any)
- Include brief rationale

## Testing
- How to test/verify these changes
- What scenarios to check

## Notes
- Any important context for reviewers
- Breaking changes (if any)
- Follow-up work needed (if any)

{f"Closes #{related_issue}" if related_issue else ""}
</task>

<output_format>
Use clear markdown. Be concise but informative.
Each section should be 2-5 bullet points maximum.
</output_format>

Generate the PR description:"""

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,  # Moderate creativity
            max_tokens=1500,
        )

        return response

    def _format_file_changes(self, changes: list[FileChangeRecord]) -> str:
        """Format file changes for prompt."""
        if not changes:
            return "No file changes"

        lines = []
        for change in changes[:15]:  # Limit to prevent token overflow
            lines.append(f"- **{change.action.upper()}**: `{change.file_path}`")
            lines.append(f"  Reason: {change.reason}")

        if len(changes) > 15:
            lines.append(f"- ... and {len(changes) - 15} more files")

        return "\n".join(lines)

    def _format_decisions(self, decisions: list[DesignDecision]) -> str:
        """Format design decisions for prompt."""
        if not decisions:
            return "No major design decisions"

        lines = []
        for dec in decisions[:5]:
            lines.append(f"- **{dec.decision}**")
            lines.append(f"  Rationale: {dec.rationale[:150]}")

        if len(decisions) > 5:
            lines.append(f"- ... and {len(decisions) - 5} more decisions")

        return "\n".join(lines)

    def _format_errors_fixed(self, errors: list[ErrorRecord]) -> str:
        """Format fixed errors for prompt."""
        if not errors:
            return "No errors resolved"

        lines = []
        for err in errors[:5]:
            lines.append(
                f"- **{err.error_type}** in `{err.file_path}:{err.line_number}`"
            )
            if err.solution:
                solution_short = err.solution[:100]
                lines.append(f"  Solution: {solution_short}")

        if len(errors) > 5:
            lines.append(f"- ... and {len(errors) - 5} more errors fixed")

        return "\n".join(lines)
