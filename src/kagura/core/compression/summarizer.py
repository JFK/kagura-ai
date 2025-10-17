"""Context summarization for conversation history compression"""

from typing import Any, Optional

from kagura.core.llm import LLMConfig, call_llm

from .token_counter import TokenCounter


class ContextSummarizer:
    """Summarize conversation history to reduce tokens

    Provides 3 methods for intelligent summarization:
    - Recursive: Recursively summarize to target token count
    - Hierarchical: Create multi-level summaries (brief/detailed/full)
    - Event-preserving: Preserve key events while summarizing routine messages

    Example:
        >>> from kagura.core.compression import TokenCounter, ContextSummarizer
        >>> counter = TokenCounter(model="gpt-5-mini")
        >>> summarizer = ContextSummarizer(counter)
        >>> messages = [
        ...     {"role": "user", "content": "Long conversation..."},
        ...     {"role": "assistant", "content": "Response..."}
        ... ]
        >>> summary = await summarizer.summarize_recursive(messages, target_tokens=500)
    """

    def __init__(
        self, token_counter: TokenCounter, llm_config: Optional[LLMConfig] = None
    ):
        """Initialize summarizer

        Args:
            token_counter: TokenCounter instance for token counting
            llm_config: LLM configuration for summarization (default: gpt-4o-mini)
        """
        self.counter = token_counter
        self.llm_config = llm_config or LLMConfig(
            model="gpt-5-mini",
            temperature=0.3,  # Low temperature for consistent summaries
        )

    async def summarize_recursive(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> str:
        """Recursively summarize conversation history to target token count

        Uses a recursive approach: if summary is still too long, split into chunks,
        summarize each chunk, and recursively summarize the combined chunk summaries.

        Args:
            messages: Message history to summarize
            target_tokens: Target token count for the summary

        Returns:
            Summary text (or original text if already under target)

        Example:
            >>> summary = await summarizer.summarize_recursive(
            ...     messages, target_tokens=500
            ... )
            >>> assert len(summary) < original_length
        """
        if not messages:
            return ""

        # Convert messages to text
        conversation = self._messages_to_text(messages)

        # Check if already under target
        current_tokens = self.counter.count_tokens(conversation)
        if current_tokens <= target_tokens:
            return conversation

        # Summarize
        summary_prompt = (
            f"""Summarize the following conversation concisely while preserving """
            f"""all important information, decisions, user preferences, and context:

{conversation}

Summary:"""
        )

        summary = await call_llm(summary_prompt, self.llm_config)

        # Convert to string if LLMResponse
        summary_str = str(summary)

        # Check if summary is small enough
        summary_tokens = self.counter.count_tokens(summary_str)
        if summary_tokens <= target_tokens:
            return summary_str

        # If still too large, recursively summarize
        # Split into chunks and summarize each
        chunks = self._split_into_chunks(conversation, target_tokens)
        chunk_summaries = []

        for chunk in chunks:
            chunk_summary = await self._summarize_chunk(chunk)
            chunk_summaries.append(chunk_summary)

        # Combine chunk summaries
        combined = "\n\n".join(chunk_summaries)

        # Recursively summarize the combined summaries
        return await self.summarize_recursive(
            [{"role": "user", "content": combined}], target_tokens
        )

    async def summarize_hierarchical(
        self, messages: list[dict[str, Any]], levels: int = 3
    ) -> dict[str, str]:
        """Create hierarchical summary at multiple levels

        Generates summaries at different compression ratios:
        - brief: 10% of original (quick overview)
        - detailed: 30% of original (moderate detail)
        - full: 70% of original (nearly complete)

        Args:
            messages: Message history to summarize
            levels: Number of summary levels (default: 3)

        Returns:
            Dict with keys "brief", "detailed", "full"

        Example:
            >>> summaries = await summarizer.summarize_hierarchical(messages)
            >>> print(summaries["brief"])  # Shortest summary
            >>> print(summaries["detailed"])  # Medium summary
            >>> print(summaries["full"])  # Longest summary
        """
        if not messages:
            return {"brief": "", "detailed": "", "full": ""}

        conversation = self._messages_to_text(messages)
        current_tokens = self.counter.count_tokens(conversation)

        summaries = {}

        # Level 1: Brief (10% of original)
        target_brief = max(int(current_tokens * 0.1), 100)
        summaries["brief"] = await self.summarize_recursive(messages, target_brief)

        # Level 2: Detailed (30% of original)
        target_detailed = max(int(current_tokens * 0.3), 300)
        summaries["detailed"] = await self.summarize_recursive(
            messages, target_detailed
        )

        # Level 3: Full (original or 70% if too long)
        if current_tokens > 5000:
            target_full = int(current_tokens * 0.7)
            summaries["full"] = await self.summarize_recursive(messages, target_full)
        else:
            summaries["full"] = conversation

        return summaries

    async def compress_preserve_events(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Compress while preserving key events

        Strategy:
        1. Identify key events (decisions, errors, preferences)
        2. Summarize routine messages
        3. Keep key events verbatim

        This preserves important information while achieving significant compression.

        Args:
            messages: Message history
            target_tokens: Target token count

        Returns:
            Compressed message list (summary + key events)

        Example:
            >>> compressed = await summarizer.compress_preserve_events(
            ...     messages, target_tokens=1000
            ... )
            >>> # Key events are preserved, routine messages are summarized
        """
        if not messages:
            return []

        # Separate key events from routine messages
        key_events = []
        routine = []

        for msg in messages:
            if self._is_key_event(msg):
                key_events.append(msg)
            else:
                routine.append(msg)

        # Calculate token budget
        key_event_tokens = self.counter.count_tokens_messages(key_events)
        remaining_tokens = target_tokens - key_event_tokens

        if remaining_tokens < 100:
            # Not enough space, must summarize everything
            summary = await self.summarize_recursive(messages, target_tokens)
            return [{"role": "system", "content": f"[Summary] {summary}"}]

        # Summarize routine messages
        if routine:
            routine_summary = await self.summarize_recursive(routine, remaining_tokens)
            summary_msg = {
                "role": "system",
                "content": f"[Previous conversation summary] {routine_summary}",
            }
        else:
            summary_msg = None

        # Reconstruct message list
        compressed = []
        if summary_msg:
            compressed.append(summary_msg)
        compressed.extend(key_events)

        return compressed

    def _is_key_event(self, msg: dict[str, Any]) -> bool:
        """Check if message is a key event

        Key events are identified by important keywords that indicate:
        - Errors or problems
        - Important decisions or agreements
        - User preferences or settings
        - Things to remember

        Args:
            msg: Message to check

        Returns:
            True if message is a key event
        """
        content = msg.get("content", "").lower()

        key_indicators = [
            "error",
            "exception",
            "failed",
            "important",
            "critical",
            "urgent",
            "decided",
            "agreed",
            "confirmed",
            "preference",
            "setting",
            "config",
            "remember",
            "note",
            "save",
        ]

        return any(indicator in content for indicator in key_indicators)

    def _messages_to_text(self, messages: list[dict[str, Any]]) -> str:
        """Convert message list to readable text

        Args:
            messages: Message list in OpenAI format

        Returns:
            Formatted text representation
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role.upper()}: {content}")
        return "\n\n".join(lines)

    async def _summarize_chunk(self, chunk: str) -> str:
        """Summarize a single chunk of text

        Args:
            chunk: Text chunk to summarize

        Returns:
            Summary of the chunk
        """
        prompt = f"""Summarize this conversation segment concisely:

{chunk}

Summary:"""

        result = await call_llm(prompt, self.llm_config)
        return str(result)

    def _split_into_chunks(self, text: str, target_tokens: int) -> list[str]:
        """Split text into chunks of approximately target token size

        Uses sentence boundaries to avoid splitting mid-sentence.

        Args:
            text: Text to split
            target_tokens: Target tokens per chunk

        Returns:
            List of text chunks
        """
        # Simple split by sentences (periods followed by space)
        sentences = text.split(". ")
        chunks = []
        current_chunk = []
        current_tokens = 0

        for i, sentence in enumerate(sentences):
            sentence_tokens = self.counter.count_tokens(sentence)

            if current_tokens + sentence_tokens > target_tokens and current_chunk:
                # Chunk is full, save it and start new chunk
                # Re-add ". " between sentences except for last sentence in chunk
                chunks.append(". ".join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                # Add to current chunk
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append(". ".join(current_chunk))

        return chunks
