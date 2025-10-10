"""Basic Agent Testing Example

This example demonstrates basic agent testing using AgentTestCase
and built-in assertion methods for non-deterministic LLM outputs.
"""

import pytest
from kagura import agent
from kagura.testing import AgentTestCase


# Define test agents
@agent(model="gpt-4o-mini")
async def greeter(name: str) -> str:
    """Greet {{ name }} warmly"""
    pass


@agent(model="gpt-4o-mini")
async def translator(text: str, target_language: str) -> str:
    """Translate "{{ text }}" to {{ target_language }}"""
    pass


@agent(model="gpt-4o-mini")
async def summarizer(text: str) -> str:
    """Summarize the following text in 2-3 sentences: {{ text }}"""
    pass


# Test Class 1: Basic Assertions
class TestGreeterAgent(AgentTestCase):
    """Test the greeter agent with basic assertions."""

    agent = greeter

    @pytest.mark.asyncio
    async def test_greets_with_name(self):
        """Test that agent includes the user's name in greeting."""
        result = await self.agent("Alice")

        # Assert output is not empty
        self.assert_not_empty(result)

        # Assert name is mentioned
        self.assert_contains(result, "Alice")

    @pytest.mark.asyncio
    async def test_different_names(self):
        """Test greeting with different names."""
        names = ["Bob", "Charlie", "Diana"]

        for name in names:
            result = await self.agent(name)
            self.assert_not_empty(result)
            self.assert_contains(result, name)

    @pytest.mark.asyncio
    async def test_output_length(self):
        """Test that greeting has reasonable length."""
        result = await self.agent("Eve")

        # Should be a complete sentence
        self.assert_min_length(result, 10)

        # But not too verbose
        self.assert_max_length(result, 200)


# Test Class 2: Translation Testing
class TestTranslatorAgent(AgentTestCase):
    """Test the translator agent."""

    agent = translator

    @pytest.mark.asyncio
    async def test_translates_to_french(self):
        """Test translation to French."""
        result = await self.agent("Hello", target_language="French")

        self.assert_not_empty(result)
        # French greeting should contain "bonjour" or "salut"
        self.assert_matches_regex(result, r"(?i)(bonjour|salut)")

    @pytest.mark.asyncio
    async def test_translates_to_spanish(self):
        """Test translation to Spanish."""
        result = await self.agent("Hello", target_language="Spanish")

        self.assert_not_empty(result)
        # Spanish greeting should contain "hola"
        self.assert_matches_regex(result, r"(?i)hola")

    @pytest.mark.asyncio
    async def test_preserves_meaning(self):
        """Test that translation preserves core meaning."""
        original = "Good morning"
        result = await self.agent(original, target_language="Japanese")

        # Output should exist and have reasonable length
        self.assert_not_empty(result)
        self.assert_min_length(result, 2)  # At least some characters


# Test Class 3: Summarization Testing
class TestSummarizerAgent(AgentTestCase):
    """Test the summarizer agent."""

    agent = summarizer

    @pytest.mark.asyncio
    async def test_summarizes_short_text(self):
        """Test summarization of short text."""
        text = """
        Python is a high-level programming language known for its simplicity
        and readability. It was created by Guido van Rossum and first released
        in 1991. Python supports multiple programming paradigms including
        procedural, object-oriented, and functional programming.
        """

        result = await self.agent(text)

        # Summary should exist and be shorter than original
        self.assert_not_empty(result)
        assert len(result) < len(text), "Summary should be shorter than original"

    @pytest.mark.asyncio
    async def test_summary_includes_key_info(self):
        """Test that summary includes key information."""
        text = """
        Machine learning is a subset of artificial intelligence that focuses
        on building systems that can learn from data. The key advantage of
        machine learning is that it can automatically identify patterns
        without being explicitly programmed.
        """

        result = await self.agent(text)

        # Should mention core concepts
        self.assert_matches_any(result, [
            r"(?i)machine learning",
            r"(?i)learn.*data",
            r"(?i)pattern"
        ])

    @pytest.mark.asyncio
    async def test_summary_sentence_count(self):
        """Test that summary follows sentence count constraint."""
        text = """
        The Internet of Things (IoT) refers to the network of physical objects
        embedded with sensors, software, and other technologies to connect and
        exchange data with other devices over the internet. IoT devices range
        from ordinary household objects to sophisticated industrial tools.
        The technology has applications in smart homes, healthcare, agriculture,
        and manufacturing.
        """

        result = await self.agent(text)

        # Count sentences (rough estimate)
        sentence_count = result.count('.') + result.count('!') + result.count('?')

        # Should be 2-4 sentences (allowing some flexibility)
        assert 1 <= sentence_count <= 5, f"Expected 2-3 sentences, got {sentence_count}"


# Test Class 4: Error Handling
class TestAgentErrorHandling(AgentTestCase):
    """Test error handling in agents."""

    agent = greeter

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """Test agent handles empty input gracefully."""
        result = await self.agent("")

        # Agent should still produce some output
        self.assert_not_empty(result)

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test agent handles special characters."""
        result = await self.agent("Alice@#$%")

        # Should still work
        self.assert_not_empty(result)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
