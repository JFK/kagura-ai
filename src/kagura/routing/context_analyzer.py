"""Context analysis for memory-aware routing."""

from __future__ import annotations

import re
import string
from typing import Any


class ContextAnalyzer:
    """Analyzes queries to determine if they need conversational context.

    Detects:
    - Pronouns (it, this, that, them, etc.)
    - Implicit references (also, too, again, etc.)
    - Follow-up questions (what about, how about, etc.)

    Example:
        >>> analyzer = ContextAnalyzer()
        >>> analyzer.needs_context("What about this one?")  # True
        >>> analyzer.needs_context("Translate to French")   # False
    """

    # Pronouns that indicate reference to previous context
    PRONOUNS = {
        "it",
        "this",
        "that",
        "these",
        "those",
        "they",
        "them",
        "their",
        "theirs",
        "he",
        "she",
        "his",
        "her",
        "hers",
        "one",
        "ones",
    }

    # Words indicating implicit reference
    IMPLICIT_REFS = {
        "also",
        "too",
        "either",
        "neither",
        "again",
        "another",
        "similar",
        "same",
        "more",
        "additionally",
        "furthermore",
    }

    # Patterns for follow-up questions
    FOLLOWUP_PATTERNS = [
        r"^what about",
        r"^how about",
        r"^and if",
        r"^but what",
        r"^can you also",
        r"^could you also",
        r"^do you also",
        r"^what if",
        r"^and what",
    ]

    def __init__(self) -> None:
        """Initialize context analyzer."""
        self._followup_regex = re.compile(
            "|".join(self.FOLLOWUP_PATTERNS), re.IGNORECASE
        )

    def needs_context(self, query: str) -> bool:
        """Determine if query needs conversational context.

        Args:
            query: User query to analyze

        Returns:
            True if query is context-dependent
        """
        query_lower = query.lower().strip()

        # Check for pronouns
        if self._has_pronouns(query_lower):
            return True

        # Check for implicit references
        if self._has_implicit_reference(query_lower):
            return True

        # Check for follow-up patterns
        if self._is_followup_question(query_lower):
            return True

        return False

    def _has_pronouns(self, query: str) -> bool:
        """Check if query contains pronouns indicating reference.

        Args:
            query: Query text (lowercase)

        Returns:
            True if pronouns found
        """
        # Strip punctuation from words for matching
        words = query.split()
        clean_words = [word.strip(string.punctuation) for word in words]

        # Create word pairs to detect demonstrative adjectives vs pronouns
        # e.g., "this text" (adjective) vs "this?" (pronoun)
        word_pairs = list(zip(clean_words, clean_words[1:] + [""]))

        # Action verbs that indicate imperative commands
        action_verbs = {
            "translate",
            "convert",
            "change",
            "transform",
            "check",
            "review",
            "analyze",
            "fix",
            "debug",
            "test",
            "run",
            "execute",
            "show",
            "display",
            "find",
            "search",
        }

        for word, next_word in word_pairs:
            if word in self.PRONOUNS:
                # For "this" and "that", check if it's part of imperative command
                if word in ("this", "that"):
                    # Check if preceded by an action verb AND followed by a noun
                    # e.g., "review this code", "translate this text"
                    # but NOT "review this?" or "check that?"
                    idx = clean_words.index(word)
                    if idx > 0 and clean_words[idx - 1] in action_verbs:
                        # Only skip if there's a noun following (not punctuation or end)
                        if next_word and len(next_word) > 2:
                            # Likely an imperative command with object
                            continue
                return True

        return False

    def _has_implicit_reference(self, query: str) -> bool:
        """Check if query has implicit references.

        Args:
            query: Query text (lowercase)

        Returns:
            True if implicit references found
        """
        words = query.split()
        clean_words = {word.strip(string.punctuation) for word in words}
        return bool(clean_words & self.IMPLICIT_REFS)

    def _is_followup_question(self, query: str) -> bool:
        """Check if query is a follow-up question.

        Args:
            query: Query text (lowercase)

        Returns:
            True if follow-up pattern detected
        """
        return bool(self._followup_regex.search(query))

    def extract_intent_from_context(
        self, query: str, conversation_history: list[dict[str, Any]]
    ) -> str:
        """Extract intent by analyzing query with conversation history.

        Args:
            query: Current user query
            conversation_history: Recent conversation messages
                Format: [{"role": "user"|"assistant", "content": str}, ...]

        Returns:
            Enhanced query with resolved context
        """
        if not conversation_history:
            return query

        # Get last few user messages for context
        user_messages = [
            msg["content"]
            for msg in conversation_history
            if msg.get("role") == "user"
        ][-3:]  # Last 3 user messages

        # If no context needed, return as-is
        if not self.needs_context(query):
            return query

        # Combine recent context with current query
        if user_messages:
            context_text = " ".join(user_messages[-2:])  # Last 2 messages
            enhanced = f"Previous context: {context_text}\n\nCurrent query: {query}"
            return enhanced

        return query
