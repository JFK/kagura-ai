"""Message trimming strategies for context compression"""

from typing import Any, Literal

from .token_counter import TokenCounter

TrimStrategy = Literal["last", "first", "middle", "smart"]


class MessageTrimmer:
    """Trim messages to fit within token limits

    Provides 4 strategies for intelligent message trimming:
    - last: Keep most recent messages (FIFO)
    - first: Keep oldest messages (LIFO)
    - middle: Keep beginning and end, remove middle
    - smart: Score-based importance trimming

    Example:
        >>> from kagura.core.compression import TokenCounter, MessageTrimmer
        >>> counter = TokenCounter(model="gpt-5-mini")
        >>> trimmer = MessageTrimmer(counter)
        >>> messages = [
        ...     {"role": "system", "content": "You are helpful."},
        ...     {"role": "user", "content": "Hello!"},
        ...     {"role": "assistant", "content": "Hi there!"}
        ... ]
        >>> trimmed = trimmer.trim(messages, max_tokens=100, strategy="smart")
        >>> assert len(trimmed) <= len(messages)
    """

    def __init__(self, token_counter: TokenCounter):
        """Initialize trimmer

        Args:
            token_counter: TokenCounter instance for token counting
        """
        self.counter = token_counter

    def trim(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        strategy: TrimStrategy = "smart",
        preserve_system: bool = True,
    ) -> list[dict[str, Any]]:
        """Trim messages to fit within token limit

        Args:
            messages: Message list to trim
            max_tokens: Maximum tokens allowed
            strategy: Trimming strategy ("last", "first", "middle", "smart")
            preserve_system: Always keep system message if present

        Returns:
            Trimmed message list

        Raises:
            ValueError: If strategy is unknown

        Example:
            >>> trimmer = MessageTrimmer(TokenCounter())
            >>> messages = [{"role": "user", "content": "Test"}] * 100
            >>> trimmed = trimmer.trim(messages, max_tokens=500)
            >>> assert len(trimmed) < len(messages)
        """
        if not messages:
            return []

        if strategy == "last":
            return self._trim_last(messages, max_tokens, preserve_system)
        elif strategy == "first":
            return self._trim_first(messages, max_tokens, preserve_system)
        elif strategy == "middle":
            return self._trim_middle(messages, max_tokens, preserve_system)
        elif strategy == "smart":
            return self._trim_smart(messages, max_tokens, preserve_system)
        else:
            raise ValueError(f"Unknown trimming strategy: {strategy}")

    def _trim_last(
        self, messages: list[dict[str, Any]], max_tokens: int, preserve_system: bool
    ) -> list[dict[str, Any]]:
        """Keep most recent messages (FIFO)

        Args:
            messages: Message list
            max_tokens: Maximum tokens
            preserve_system: Keep system message

        Returns:
            Trimmed messages with most recent kept
        """
        # Extract system message if present
        system_msg = None
        working_messages = messages

        if preserve_system and messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            working_messages = messages[1:]

        if not working_messages:
            return [system_msg] if system_msg else []

        # Reserve tokens for system message if present
        available_tokens = max_tokens
        if system_msg:
            system_tokens = self.counter.count_tokens_messages([system_msg])
            available_tokens = max(0, max_tokens - system_tokens)

        # Start from end, accumulate until limit
        trimmed = []
        current_tokens = 0

        for msg in reversed(working_messages):
            msg_tokens = self.counter.count_tokens_messages([msg])

            if current_tokens + msg_tokens > available_tokens:
                break

            trimmed.insert(0, msg)
            current_tokens += msg_tokens

        # Re-add system message at the beginning
        if system_msg:
            trimmed.insert(0, system_msg)

        return trimmed

    def _trim_first(
        self, messages: list[dict[str, Any]], max_tokens: int, preserve_system: bool
    ) -> list[dict[str, Any]]:
        """Keep oldest messages (LIFO)

        Args:
            messages: Message list
            max_tokens: Maximum tokens
            preserve_system: Keep system message

        Returns:
            Trimmed messages with oldest kept
        """
        # Extract system message if present
        system_msg = None
        working_messages = messages

        if preserve_system and messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            working_messages = messages[1:]

        if not working_messages:
            return [system_msg] if system_msg else []

        # Reserve tokens for system message if present
        available_tokens = max_tokens
        if system_msg:
            system_tokens = self.counter.count_tokens_messages([system_msg])
            available_tokens = max(0, max_tokens - system_tokens)

        # Start from beginning, accumulate until limit
        trimmed = []
        current_tokens = 0

        for msg in working_messages:
            msg_tokens = self.counter.count_tokens_messages([msg])

            if current_tokens + msg_tokens > available_tokens:
                break

            trimmed.append(msg)
            current_tokens += msg_tokens

        # Re-add system message at the beginning
        if system_msg:
            trimmed.insert(0, system_msg)

        return trimmed

    def _trim_middle(
        self, messages: list[dict[str, Any]], max_tokens: int, preserve_system: bool
    ) -> list[dict[str, Any]]:
        """Keep beginning and end, remove middle

        Allocates half of tokens to beginning messages and half to end messages.

        Args:
            messages: Message list
            max_tokens: Maximum tokens
            preserve_system: Keep system message

        Returns:
            Trimmed messages with beginning and end kept
        """
        # Extract system message if present
        system_msg = None
        working_messages = messages

        if preserve_system and messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            working_messages = messages[1:]

        if not working_messages:
            return [system_msg] if system_msg else []

        # Reserve tokens for system message if present
        available_tokens = max_tokens
        if system_msg:
            system_tokens = self.counter.count_tokens_messages([system_msg])
            available_tokens = max(0, max_tokens - system_tokens)

        # Allocate half tokens to beginning, half to end
        half_tokens = available_tokens // 2

        # Get beginning messages
        beginning = []
        current_tokens = 0

        for msg in working_messages:
            msg_tokens = self.counter.count_tokens_messages([msg])

            if current_tokens + msg_tokens > half_tokens:
                break

            beginning.append(msg)
            current_tokens += msg_tokens

        # Get ending messages
        ending = []
        current_tokens = 0

        for msg in reversed(working_messages):
            msg_tokens = self.counter.count_tokens_messages([msg])

            if current_tokens + msg_tokens > half_tokens:
                break

            ending.insert(0, msg)
            current_tokens += msg_tokens

        # Combine (avoid duplicates)
        trimmed = beginning.copy()

        for msg in ending:
            if msg not in trimmed:
                trimmed.append(msg)

        # Re-add system message at the beginning
        if system_msg:
            trimmed.insert(0, system_msg)

        return trimmed

    def _trim_smart(
        self, messages: list[dict[str, Any]], max_tokens: int, preserve_system: bool
    ) -> list[dict[str, Any]]:
        """Smart trimming: preserve important messages

        Priority:
        1. System message (always)
        2. Recent messages (last 5)
        3. Messages with important keywords
        4. Longer messages (likely more important)

        Args:
            messages: Message list
            max_tokens: Maximum tokens
            preserve_system: Keep system message

        Returns:
            Trimmed messages with important messages kept
        """
        # Extract system message if present
        system_msg = None
        working_messages = messages

        if preserve_system and messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            working_messages = messages[1:]

        if not working_messages:
            return [system_msg] if system_msg else []

        # Reserve tokens for system message if present
        available_tokens = max_tokens
        if system_msg:
            system_tokens = self.counter.count_tokens_messages([system_msg])
            available_tokens = max(0, max_tokens - system_tokens)

        # Score messages by importance
        scored = []
        total_messages = len(working_messages)

        for i, msg in enumerate(working_messages):
            score = self._score_message(msg, i, total_messages)
            scored.append((score, msg))

        # Sort by score (descending - highest score first)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Accumulate messages until token limit
        selected = []
        current_tokens = 0

        for score, msg in scored:
            msg_tokens = self.counter.count_tokens_messages([msg])

            if current_tokens + msg_tokens > available_tokens:
                continue

            selected.append(msg)
            current_tokens += msg_tokens

        # Re-sort by original order to maintain conversation flow
        selected.sort(key=lambda m: working_messages.index(m))

        # Re-add system message at the beginning
        if system_msg:
            selected.insert(0, system_msg)

        return selected

    def _score_message(self, msg: dict[str, Any], index: int, total: int) -> float:
        """Score message importance

        Args:
            msg: Message to score
            index: Message index in original list
            total: Total number of messages

        Returns:
            Importance score (0.0 - 10.0)
        """
        score = 0.0

        # Recency score (last 5 messages get bonus)
        if index >= total - 5:
            score += 5.0

        # Length score (longer = more important, up to 2.0)
        content = msg.get("content", "")
        score += min(len(content) / 500, 2.0)

        # Important keywords
        important_keywords = [
            "error",
            "important",
            "critical",
            "remember",
            "note",
            "user preference",
            "setting",
            "config",
            "decided",
            "agreed",
            "confirmed",
            "warning",
            "urgent",
            "must",
            "required",
            "preference",
            "prefer",
        ]

        content_lower = content.lower()
        for keyword in important_keywords:
            if keyword in content_lower:
                score += 1.0

        # Role bonus (user/assistant more important than function)
        if msg.get("role") in ["user", "assistant"]:
            score += 1.0

        return score
