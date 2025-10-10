"""Tests for ContextAnalyzer."""

import pytest

from kagura.routing import ContextAnalyzer


def test_context_analyzer_initialization():
    """Test ContextAnalyzer initialization."""
    analyzer = ContextAnalyzer()

    assert analyzer is not None
    assert analyzer._followup_regex is not None


# ===== Pronoun Detection Tests =====


def test_has_pronouns_it():
    """Test pronoun detection for 'it'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("What is it?")
    assert analyzer.needs_context("Can you explain it?")
    assert analyzer.needs_context("How does it work?")


def test_has_pronouns_this_that():
    """Test pronoun detection for 'this' and 'that'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("What about this?")
    assert analyzer.needs_context("How about that?")
    assert analyzer.needs_context("Can you review this?")


def test_has_pronouns_these_those():
    """Test pronoun detection for 'these' and 'those'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("What are these?")
    assert analyzer.needs_context("Can you check those?")


def test_has_pronouns_they_them():
    """Test pronoun detection for 'they' and 'them'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("What do they mean?")
    assert analyzer.needs_context("Can you explain them?")


def test_no_pronouns():
    """Test queries without pronouns."""
    analyzer = ContextAnalyzer()

    assert not analyzer.needs_context("Translate 'hello' to French")
    assert not analyzer.needs_context("What is machine learning?")
    assert not analyzer.needs_context("Review my Python code")


# ===== Implicit Reference Detection Tests =====


def test_has_implicit_reference_also():
    """Test implicit reference detection for 'also'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("Can you also check the syntax?")
    assert analyzer.needs_context("Also translate to Spanish")


def test_has_implicit_reference_too():
    """Test implicit reference detection for 'too'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("Do that too")
    assert analyzer.needs_context("Check the performance too")


def test_has_implicit_reference_again():
    """Test implicit reference detection for 'again'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("Can you do that again?")
    assert analyzer.needs_context("Translate again")


def test_has_implicit_reference_another():
    """Test implicit reference detection for 'another'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("Show me another example")
    assert analyzer.needs_context("Try another approach")


def test_has_implicit_reference_same():
    """Test implicit reference detection for 'same'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("Do the same thing")
    assert analyzer.needs_context("Apply the same logic")


# ===== Follow-up Question Detection Tests =====


def test_is_followup_what_about():
    """Test follow-up detection for 'what about'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("What about the error handling?")
    assert analyzer.needs_context("What about edge cases?")


def test_is_followup_how_about():
    """Test follow-up detection for 'how about'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("How about performance?")
    assert analyzer.needs_context("How about using a different approach?")


def test_is_followup_and_if():
    """Test follow-up detection for 'and if'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("And if the input is invalid?")


def test_is_followup_but_what():
    """Test follow-up detection for 'but what'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("But what about edge cases?")


def test_is_followup_can_you_also():
    """Test follow-up detection for 'can you also'."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("Can you also check the types?")


def test_is_followup_case_insensitive():
    """Test follow-up detection is case-insensitive."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("WHAT ABOUT THIS?")
    assert analyzer.needs_context("How About That?")
    assert analyzer.needs_context("what about edge cases?")


def test_not_followup():
    """Test queries that are not follow-ups."""
    analyzer = ContextAnalyzer()

    assert not analyzer.needs_context("Translate this text to French")
    assert not analyzer.needs_context("Review the following code")


# ===== Combined Detection Tests =====


def test_multiple_indicators():
    """Test queries with multiple context indicators."""
    analyzer = ContextAnalyzer()

    # Pronoun + implicit reference
    assert analyzer.needs_context("Can you also check this?")

    # Follow-up + pronoun
    assert analyzer.needs_context("What about that error?")

    # All three
    assert analyzer.needs_context("What about that? Can you check it too?")


# ===== Extract Intent from Context Tests =====


def test_extract_intent_no_history():
    """Test intent extraction with no conversation history."""
    analyzer = ContextAnalyzer()

    query = "What about this?"
    result = analyzer.extract_intent_from_context(query, [])

    assert result == query


def test_extract_intent_no_context_needed():
    """Test intent extraction when no context needed."""
    analyzer = ContextAnalyzer()

    query = "Translate 'hello' to French"
    history = [
        {"role": "user", "content": "Previous message"},
        {"role": "assistant", "content": "Previous response"},
    ]

    result = analyzer.extract_intent_from_context(query, history)

    # Should return original query since no context indicators
    assert result == query


def test_extract_intent_with_context():
    """Test intent extraction with context-dependent query."""
    analyzer = ContextAnalyzer()

    query = "What about this one?"
    history = [
        {"role": "user", "content": "Translate 'hello' to French"},
        {"role": "assistant", "content": "Bonjour"},
        {"role": "user", "content": "Translate 'goodbye' to Spanish"},
        {"role": "assistant", "content": "Adiós"},
    ]

    result = analyzer.extract_intent_from_context(query, history)

    # Should include context
    assert "Previous context:" in result
    assert "Current query:" in result
    assert query in result


def test_extract_intent_recent_context():
    """Test intent extraction uses recent context only."""
    analyzer = ContextAnalyzer()

    query = "Do it again"
    history = [
        {"role": "user", "content": "Very old message"},
        {"role": "assistant", "content": "Old response"},
        {"role": "user", "content": "Recent message 1"},
        {"role": "assistant", "content": "Recent response 1"},
        {"role": "user", "content": "Recent message 2"},
        {"role": "assistant", "content": "Recent response 2"},
    ]

    result = analyzer.extract_intent_from_context(query, history)

    # Should include recent user messages
    assert "Recent message" in result
    assert "Very old message" not in result


def test_extract_intent_user_messages_only():
    """Test intent extraction filters user messages."""
    analyzer = ContextAnalyzer()

    query = "What about that?"
    history = [
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Assistant response"},
        {"role": "system", "content": "System message"},
    ]

    result = analyzer.extract_intent_from_context(query, history)

    # Should only include user messages in context
    assert "User message" in result
    assert "Assistant response" not in result
    assert "System message" not in result


# ===== Edge Cases =====


def test_empty_query():
    """Test handling of empty query."""
    analyzer = ContextAnalyzer()

    assert not analyzer.needs_context("")
    assert not analyzer.needs_context("   ")


def test_punctuation_handling():
    """Test handling of queries with punctuation."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("What about this?")
    assert analyzer.needs_context("Can you check it!")
    assert analyzer.needs_context("Show me that...")


def test_multi_word_pronouns():
    """Test pronouns in longer queries."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("Can you please explain what this code does?")
    assert analyzer.needs_context("I would like to know more about that topic")


def test_case_sensitivity():
    """Test case-insensitive detection."""
    analyzer = ContextAnalyzer()

    assert analyzer.needs_context("What about THIS?")
    assert analyzer.needs_context("Can you check THAT?")
    assert analyzer.needs_context("DO IT AGAIN")
