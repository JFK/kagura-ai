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
        """Check if query contains pronouns indicating reference to previous context.

        This method implements smart pronoun detection to avoid false positives
        in imperative commands like "translate this text".

        Strategy:
        1. Detect pronouns (it, this, that, them, etc.)
        2. For ambiguous words ("this"/"that"), distinguish between:
           - Demonstrative adjective: "review this code" → NO context needed
           - Standalone pronoun: "what about this?" → NEEDS context

        Args:
            query: Query text (lowercase)

        Returns:
            True if context-dependent pronouns found

        Examples:
            >>> _has_pronouns("what about it?")        # True
            >>> _has_pronouns("translate this text")   # False (imperative)
            >>> _has_pronouns("check this?")           # True (no noun after)
        """
        # Strip punctuation for clean word matching
        words = query.split()
        clean_words = [word.strip(string.punctuation) for word in words]

        # Create word pairs (current, next) to analyze context
        # e.g., ["review", "this", "code"] → [("review", "this"),
        # ("this", "code"), ("code", "")]
        word_pairs = list(zip(clean_words, clean_words[1:] + [""]))

        # Action verbs indicating imperative commands (not context-dependent)
        # These appear before "this/that" in commands like "translate this text"
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
                # Special handling for "this" and "that" (can be adjective or pronoun)
                if word in ("this", "that"):
                    idx = clean_words.index(word)

                    # Check pattern: [action_verb] [this/that] [noun]
                    # If matches, it's an imperative command → NO context needed
                    if idx > 0 and clean_words[idx - 1] in action_verbs:
                        # Verify there's a following noun (len > 2 is heuristic)
                        # e.g., "translate this text" → skip
                        # but "translate this?" → detect (no noun)
                        if next_word and len(next_word) > 2:
                            # Likely imperative with direct object
                            continue

                # Found a context-dependent pronoun
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
            msg["content"] for msg in conversation_history if msg.get("role") == "user"
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
