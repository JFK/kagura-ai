"""Memory abstraction layer for external records and context.

Implements 2-level abstraction:
- Level 1: External record abstraction (lightweight LLM: gpt-5-mini)
- Level 2: Context abstraction (powerful LLM: gpt-5 / claude / gemini)
"""

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AbstractionLevel(str):
    """Abstraction level classification."""

    LEVEL_0_RAW = "raw"  # Raw data (no abstraction)
    LEVEL_1_SUMMARY = "summary"  # Summary + keywords
    LEVEL_2_CONCEPT = "concept"  # Patterns + concepts


class AbstractedMemory(BaseModel):
    """Abstracted memory record.

    Attributes:
        original_id: ID of original record
        abstraction_level: Level of abstraction (0, 1, or 2)
        summary: Human-readable summary
        keywords: Extracted keywords/tags
        concepts: High-level concepts (level 2 only)
        patterns: Learned patterns (level 2 only)
        reference: Link to original source (GitHub, file path, etc.)
        metadata: Additional context
    """

    original_id: str
    abstraction_level: Literal["raw", "summary", "concept"]
    summary: str
    keywords: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    reference: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryAbstractor:
    """Abstract raw memories into searchable concepts.

    Two abstraction levels:
    1. External record → summary + keywords (lightweight LLM)
    2. Context → patterns + concepts (powerful LLM)

    Configurable LLM models for cost/quality trade-off.

    Attributes:
        level1_model: Model for level 1 abstraction (default: gpt-5-mini)
        level2_model: Model for level 2 abstraction (default: gpt-5)
        enable_level2: Enable expensive level 2 abstraction
        total_cost: Total LLM cost for all abstractions (USD)
        total_tokens: Total tokens used for LLM operations
        level1_cost: Cost for level 1 abstractions only (USD)
        level2_cost: Cost for level 2 abstractions only (USD)
    """

    def __init__(
        self,
        level1_model: str = "gpt-5-mini",
        level2_model: str = "gpt-5",
        enable_level2: bool = True,
    ) -> None:
        """Initialize memory abstractor.

        Args:
            level1_model: LLM for level 1 (external record) abstraction
                Recommended: gpt-5-mini, gemini-2.0-flash-exp (fast, cheap)
            level2_model: LLM for level 2 (context) abstraction
                Recommended: gpt-5, claude-sonnet-4-5, gemini-2.5-pro (slow, expensive)
            enable_level2: Enable level 2 abstraction (default: True)
        """
        self.level1_model = level1_model
        self.level2_model = level2_model
        self.enable_level2 = enable_level2

        # Cost tracking for LLM operations
        self.total_cost = 0.0
        self.total_tokens = 0
        self.level1_cost = 0.0
        self.level2_cost = 0.0

        logger.info(
            f"MemoryAbstractor initialized: "
            f"level1={level1_model}, level2={level2_model}, "
            f"enable_level2={enable_level2}"
        )

    async def abstract_external_record(
        self,
        record_id: str,
        raw_content: str,
        reference: str | None = None,
        llm_client: Any | None = None,
    ) -> AbstractedMemory:
        """Abstract external record (Level 1: Summary + Keywords).

        Uses lightweight LLM for cost efficiency.

        Args:
            record_id: Original record ID
            raw_content: Raw content (GitHub comment, file content, etc.)
            reference: Link to original (GitHub URL, file path)
            llm_client: LLM client for abstraction (optional)

        Returns:
            Level 1 abstracted memory

        Example:
            >>> abstracted = await abstractor.abstract_external_record(
            ...     record_id="gh_comment_123",
            ...     raw_content="Tried datetime.now()...",
            ...     reference="https://github.com/org/repo/issues/42#comment-123"
            ... )
        """
        if llm_client:
            try:
                result = await self._llm_abstract_level1(raw_content, llm_client)

                # Track cost if available
                if hasattr(llm_client, "last_cost"):
                    cost = llm_client.last_cost
                    self.total_cost += cost
                    self.level1_cost += cost
                if hasattr(llm_client, "last_tokens"):
                    self.total_tokens += llm_client.last_tokens

                return AbstractedMemory(
                    original_id=record_id,
                    abstraction_level="summary",
                    summary=result["summary"],
                    keywords=result["keywords"],
                    reference=reference,
                )
            except Exception as e:
                logger.warning(f"LLM level 1 abstraction failed: {e}")

        # Fallback: simple extraction
        return self._fallback_level1(record_id, raw_content, reference)

    async def _llm_abstract_level1(
        self, content: str, llm_client: Any
    ) -> dict[str, Any]:
        """Use LLM to abstract external record (level 1).

        Args:
            content: Raw content
            llm_client: LLM client instance

        Returns:
            Dict with 'summary' and 'keywords'
        """
        prompt = f"""Analyze the following external record and extract:
1. A concise summary (1-2 sentences)
2. Important keywords (5-10 words)

Content:
{content[:1000]}

Return JSON:
{{
  "summary": "...",
  "keywords": ["keyword1", "keyword2", ...]
}}
"""

        # Call LLM (implementation depends on llm_client interface)
        response = await llm_client.generate(
            prompt=prompt,
            model=self.level1_model,
            response_format="json",
        )

        # Parse response
        return json.loads(response)

    def _fallback_level1(
        self, record_id: str, content: str, reference: str | None
    ) -> AbstractedMemory:
        """Fallback level 1 abstraction without LLM.

        Args:
            record_id: Record ID
            content: Raw content
            reference: Reference link

        Returns:
            Simple abstracted memory
        """
        # Simple summary: first 200 chars
        summary = content[:200] + ("..." if len(content) > 200 else "")

        # Simple keyword extraction: words > 5 chars, frequent
        words = content.lower().split()
        keywords = list(set([w for w in words if len(w) > 5]))[:10]

        return AbstractedMemory(
            original_id=record_id,
            abstraction_level="summary",
            summary=summary,
            keywords=keywords,
            reference=reference,
        )

    async def abstract_context(
        self,
        context_id: str,
        interactions: list[Any],
        existing_abstractions: list[AbstractedMemory] | None = None,
        llm_client: Any | None = None,
    ) -> AbstractedMemory:
        """Abstract context from interactions (Level 2: Patterns + Concepts).

        Uses powerful LLM for high-quality abstraction.

        Args:
            context_id: Context identifier (e.g., session_id)
            interactions: List of InteractionRecord instances
            existing_abstractions: Previously abstracted memories (level 1)
            llm_client: LLM client for abstraction (optional)

        Returns:
            Level 2 abstracted memory

        Example:
            >>> abstracted = await abstractor.abstract_context(
            ...     context_id="session_xyz",
            ...     interactions=[interaction1, interaction2, ...]
            ... )
        """
        if not self.enable_level2:
            logger.debug("Level 2 abstraction disabled")
            # Return level 1 equivalent
            return await self._downgrade_to_level1(context_id, interactions)

        if llm_client:
            try:
                result = await self._llm_abstract_level2(
                    interactions, existing_abstractions or [], llm_client
                )

                # Track cost if available
                if hasattr(llm_client, "last_cost"):
                    cost = llm_client.last_cost
                    self.total_cost += cost
                    self.level2_cost += cost
                if hasattr(llm_client, "last_tokens"):
                    self.total_tokens += llm_client.last_tokens

                return AbstractedMemory(
                    original_id=context_id,
                    abstraction_level="concept",
                    summary=result["summary"],
                    keywords=result["keywords"],
                    concepts=result["concepts"],
                    patterns=result["patterns"],
                    metadata={"interaction_count": len(interactions)},
                )
            except Exception as e:
                logger.warning(f"LLM level 2 abstraction failed: {e}")

        # Fallback: aggregate level 1
        return await self._downgrade_to_level1(context_id, interactions)

    async def _llm_abstract_level2(
        self,
        interactions: list[Any],
        existing_abstractions: list[AbstractedMemory],
        llm_client: Any,
    ) -> dict[str, Any]:
        """Use powerful LLM to abstract context (level 2).

        Args:
            interactions: List of interactions
            existing_abstractions: Previous abstractions
            llm_client: LLM client

        Returns:
            Dict with 'summary', 'keywords', 'concepts', 'patterns'
        """
        # Prepare context
        interaction_text = "\n\n".join(
            [
                f"Q: {i.user_query}\nA: {i.ai_response}"
                for i in interactions[:20]  # Limit to 20
            ]
        )

        abstraction_text = "\n".join(
            [f"- {a.summary}" for a in existing_abstractions[:10]]  # Limit to 10
        )

        prompt = f"""Analyze this coding session and extract high-level insights:

**Interactions:**
{interaction_text[:3000]}

**Previous Knowledge:**
{abstraction_text[:1000]}

Extract:
1. Summary: What was accomplished? (2-3 sentences)
2. Keywords: Technical terms and concepts (5-10 words)
3. Concepts: High-level programming concepts learned (3-5 concepts)
4. Patterns: Reusable patterns or lessons (2-4 patterns)

Return JSON:
{{
  "summary": "...",
  "keywords": ["keyword1", ...],
  "concepts": ["concept1", ...],
  "patterns": ["pattern1", ...]
}}
"""

        # Call LLM
        response = await llm_client.generate(
            prompt=prompt,
            model=self.level2_model,
            response_format="json",
        )

        # Parse response
        return json.loads(response)

    async def _downgrade_to_level1(
        self, context_id: str, interactions: list[Any]
    ) -> AbstractedMemory:
        """Downgrade to level 1 when level 2 is disabled/failed.

        Args:
            context_id: Context ID
            interactions: List of interactions

        Returns:
            Level 1 equivalent abstraction
        """
        # Aggregate interaction types
        by_type: dict[str, int] = {}
        for i in interactions:
            itype = getattr(i, "interaction_type", "unknown")
            by_type[itype] = by_type.get(itype, 0) + 1

        # Format with proper pluralization
        type_descriptions = [
            f"{count} {itype}{'s' if count != 1 else ''}"
            for itype, count in by_type.items()
        ]
        interaction_word = "interaction" + ("s" if len(interactions) != 1 else "")
        summary = f"Session with {len(interactions)} {interaction_word}: " + ", ".join(
            type_descriptions
        )

        keywords = list(by_type.keys())

        return AbstractedMemory(
            original_id=context_id,
            abstraction_level="summary",
            summary=summary,
            keywords=keywords,
            metadata={"downgraded_from_level2": True},
        )
