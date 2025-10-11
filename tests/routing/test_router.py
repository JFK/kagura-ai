"""Tests for agent routing system."""

import pytest

from kagura.routing import (
    AgentNotRegisteredError,
    AgentRouter,
    InvalidRouterStrategyError,
    NoAgentFoundError,
)


# Test agents (simple async functions, not using @agent decorator)
async def code_reviewer(code: str) -> str:
    """Review code quality."""
    return f"Code review: {code}"


async def translator(text: str, target_lang: str = "en") -> str:
    """Translate text."""
    return f"Translation to {target_lang}: {text}"


async def data_analyzer(data: str) -> str:
    """Analyze data."""
    return f"Analysis: {data}"


async def fallback_agent(input: str) -> str:
    """Fallback handler."""
    return f"Fallback: {input}"


class TestAgentRouterInitialization:
    """Tests for AgentRouter initialization."""

    def test_default_initialization(self):
        """Test creating router with default settings."""
        router = AgentRouter()
        assert router.strategy == "intent"
        assert router.fallback_agent is None
        assert router.confidence_threshold == 0.3

    def test_custom_initialization(self):
        """Test creating router with custom settings."""
        router = AgentRouter(
            strategy="intent",
            fallback_agent=fallback_agent,
            confidence_threshold=0.5,
        )
        assert router.strategy == "intent"
        assert router.fallback_agent == fallback_agent
        assert router.confidence_threshold == 0.5

    def test_invalid_strategy(self):
        """Test that invalid strategy raises error."""
        with pytest.raises(InvalidRouterStrategyError) as exc_info:
            AgentRouter(strategy="invalid")

        assert "invalid" in str(exc_info.value)
        assert "intent" in str(exc_info.value)


class TestAgentRegistration:
    """Tests for agent registration."""

    def test_register_agent_with_intents(self):
        """Test registering agent with intents."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review", "check", "analyze"],
            description="Reviews code quality",
        )

        agents = router.list_agents()
        assert "code_reviewer" in agents

    def test_register_agent_with_custom_name(self):
        """Test registering agent with custom name."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review"],
            name="custom_reviewer",
        )

        agents = router.list_agents()
        assert "custom_reviewer" in agents
        assert "code_reviewer" not in agents

    def test_register_multiple_agents(self):
        """Test registering multiple agents."""
        router = AgentRouter()

        router.register(code_reviewer, intents=["review"])
        router.register(translator, intents=["translate"])
        router.register(data_analyzer, intents=["analyze"])

        agents = router.list_agents()
        assert len(agents) == 3
        assert "code_reviewer" in agents
        assert "translator" in agents
        assert "data_analyzer" in agents

    def test_register_agent_without_intents(self):
        """Test registering agent without intents."""
        router = AgentRouter()
        router.register(code_reviewer)

        agents = router.list_agents()
        assert "code_reviewer" in agents


class TestGetAgentInfo:
    """Tests for get_agent_info method."""

    def test_get_agent_info(self):
        """Test getting agent information."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review", "check"],
            description="Code quality reviewer",
        )

        info = router.get_agent_info("code_reviewer")
        assert info["name"] == "code_reviewer"
        assert info["intents"] == ["review", "check"]
        assert info["description"] == "Code quality reviewer"

    def test_get_agent_info_not_registered(self):
        """Test getting info for unregistered agent."""
        router = AgentRouter()

        with pytest.raises(AgentNotRegisteredError) as exc_info:
            router.get_agent_info("nonexistent")

        assert "nonexistent" in str(exc_info.value)


class TestIntentMatching:
    """Tests for intent-based matching."""

    def test_exact_keyword_match(self):
        """Test exact keyword matching."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review", "check", "analyze"],
        )

        matches = router.get_matched_agents("Please review this code")
        assert len(matches) == 1
        assert matches[0][0] == code_reviewer
        assert matches[0][1] > 0

    def test_case_insensitive_matching(self):
        """Test case-insensitive matching."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review"],
        )

        matches = router.get_matched_agents("PLEASE REVIEW THIS")
        assert len(matches) == 1
        assert matches[0][0] == code_reviewer

    def test_multiple_intent_matches(self):
        """Test matching with multiple intents."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review", "check", "analyze"],
        )

        # Match 2 out of 3 intents - new scoring uses best match
        # "review" and "check" both match with 0.8 score (exact single word)
        matches = router.get_matched_agents("review and check code")
        assert len(matches) == 1
        score = matches[0][1]
        assert score == 0.8  # Best match score from matching intents

    def test_no_match(self):
        """Test when no agent matches."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review"],
        )

        matches = router.get_matched_agents("translate this text")
        assert len(matches) == 0

    def test_partial_word_match(self):
        """Test partial word matching."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review"],
        )

        # "review" is substring of "reviewer"
        matches = router.get_matched_agents("code reviewer needed")
        assert len(matches) == 1
        assert matches[0][0] == code_reviewer


class TestGetMatchedAgents:
    """Tests for get_matched_agents method."""

    def test_top_k_matches(self):
        """Test getting top-k matches."""
        router = AgentRouter()

        router.register(code_reviewer, intents=["review", "code"])
        router.register(translator, intents=["translate"])
        router.register(data_analyzer, intents=["analyze", "data"])

        matches = router.get_matched_agents("review code and analyze data", top_k=2)
        assert len(matches) == 2

        # Should be sorted by score
        assert matches[0][1] >= matches[1][1]

    def test_matches_sorted_by_score(self):
        """Test that matches are sorted by score."""
        router = AgentRouter()

        router.register(code_reviewer, intents=["review"])  # 1 intent
        router.register(translator, intents=["translate", "conversion"])  # 2 intents

        matches = router.get_matched_agents(
            "review and translate", top_k=10
        )  # Both match
        assert len(matches) == 2

        # New scoring: Both agents get 0.8 score (exact single word match)
        # The order may vary, but both should have equal scores
        assert matches[0][1] == 0.8
        assert matches[1][1] == 0.8


class TestRouting:
    """Tests for route method."""

    @pytest.mark.asyncio
    async def test_successful_routing(self):
        """Test successful routing to agent."""
        router = AgentRouter()
        router.register(
            code_reviewer,
            intents=["review", "check"],
        )

        result = await router.route("Please review this code: def foo(): pass")
        assert "Code review" in result

    @pytest.mark.asyncio
    async def test_routing_with_multiple_agents(self):
        """Test routing with multiple registered agents."""
        router = AgentRouter()

        router.register(code_reviewer, intents=["review", "check"])
        router.register(translator, intents=["translate", "翻訳"])

        result1 = await router.route("Check this code")
        assert "Code review" in result1

        result2 = await router.route("Translate this text")
        assert "Translation" in result2

    @pytest.mark.asyncio
    async def test_routing_no_match_no_fallback(self):
        """Test routing when no agent matches and no fallback."""
        router = AgentRouter()
        router.register(code_reviewer, intents=["review"])

        with pytest.raises(NoAgentFoundError) as exc_info:
            await router.route("Translate this text")

        assert "No agent found" in str(exc_info.value)
        assert exc_info.value.user_input == "Translate this text"

    @pytest.mark.asyncio
    async def test_routing_with_fallback(self):
        """Test routing with fallback agent."""
        router = AgentRouter(fallback_agent=fallback_agent)
        router.register(code_reviewer, intents=["review"])

        # No match, should use fallback
        result = await router.route("Translate this text")
        assert "Fallback" in result

    @pytest.mark.asyncio
    async def test_routing_below_threshold_with_fallback(self):
        """Test routing when confidence is below threshold."""
        router = AgentRouter(
            fallback_agent=fallback_agent,
            confidence_threshold=0.9,  # Very high threshold
        )
        router.register(code_reviewer, intents=["review", "check", "analyze"])

        # Matches only 1 out of 3 intents = 0.33 score < 0.9 threshold
        result = await router.route("review this")
        assert "Fallback" in result

    @pytest.mark.asyncio
    async def test_routing_below_threshold_no_fallback(self):
        """Test routing when confidence is below threshold without fallback."""
        router = AgentRouter(confidence_threshold=0.9)
        router.register(code_reviewer, intents=["review", "check", "analyze"])

        with pytest.raises(NoAgentFoundError) as exc_info:
            await router.route("review this")

        assert "Low confidence" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_routing_with_kwargs(self):
        """Test routing with additional keyword arguments."""
        router = AgentRouter()
        router.register(translator, intents=["translate"])

        result = await router.route("Translate 'Hello'", target_lang="ja")
        assert "Translation to ja" in result


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_intents(self):
        """Test agent with empty intents list."""
        router = AgentRouter()
        router.register(code_reviewer, intents=[])

        matches = router.get_matched_agents("review code")
        assert len(matches) == 0

    def test_empty_user_input(self):
        """Test routing with empty user input."""
        router = AgentRouter()
        router.register(code_reviewer, intents=["review"])

        matches = router.get_matched_agents("")
        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_list_agents_empty(self):
        """Test listing agents when none registered."""
        router = AgentRouter()
        agents = router.list_agents()
        assert len(agents) == 0

    def test_unicode_intents(self):
        """Test intents with Unicode characters."""
        router = AgentRouter()
        router.register(
            translator,
            intents=["translate", "翻訳", "번역"],
        )

        # Japanese
        matches = router.get_matched_agents("これを翻訳して")
        assert len(matches) == 1

        # Korean
        matches = router.get_matched_agents("이것을 번역해주세요")
        assert len(matches) == 1


class TestSemanticRouting:
    """Tests for semantic routing strategy.

    Note: These tests require OpenAI API key and make actual API calls.
    They are marked as integration tests and will be skipped in CI.
    """

    def test_semantic_router_initialization(self):
        """Test creating router with semantic strategy."""
        router = AgentRouter(strategy="semantic")
        assert router.strategy == "semantic"
        assert router.encoder_type == "openai"

    def test_semantic_router_with_samples(self):
        """Test registering agents with sample queries."""
        router = AgentRouter(strategy="semantic")
        router.register(
            code_reviewer,
            samples=[
                "Can you review this code?",
                "Check my implementation",
                "このコードをレビューして",
            ],
            description="Code reviewer",
        )

        agents = router.list_agents()
        assert "code_reviewer" in agents

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_semantic_routing_execution(self):
        """Test semantic routing with actual queries.

        Requires OPENAI_API_KEY environment variable.
        """
        import os

        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        router = AgentRouter(strategy="semantic", fallback_agent=fallback_agent)

        router.register(
            code_reviewer,
            samples=[
                "review this code",
                "check code quality",
                "analyze my implementation",
            ],
        )

        router.register(
            translator,
            samples=[
                "translate this text",
                "convert to Japanese",
                "翻訳して",
            ],
        )

        # Test semantic matching (similar to training samples)
        result = await router.route("Could you look at my code?")
        assert result is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_semantic_routing_with_fallback(self):
        """Test semantic routing fallback mechanism.

        Requires OPENAI_API_KEY environment variable.
        """
        import os

        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        router = AgentRouter(
            strategy="semantic",
            fallback_agent=fallback_agent,
            confidence_threshold=0.8,
        )

        router.register(
            code_reviewer,
            samples=["review code", "check code"],
        )

        # Unrelated query should use fallback
        result = await router.route("What's the weather today?")
        assert "Fallback" in result

    def test_semantic_router_no_samples(self):
        """Test semantic router with agent that has no samples."""
        router = AgentRouter(strategy="semantic")
        router.register(code_reviewer)  # No samples

        # Should handle gracefully
        agents = router.list_agents()
        assert "code_reviewer" in agents

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_semantic_routing_multiple_agents(self):
        """Test semantic routing with multiple agents.

        Requires OPENAI_API_KEY environment variable.
        """
        import os

        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        router = AgentRouter(strategy="semantic", fallback_agent=fallback_agent)

        router.register(
            code_reviewer,
            samples=[
                "review code",
                "check implementation",
            ],
        )

        router.register(
            translator,
            samples=[
                "translate text",
                "convert language",
            ],
        )

        router.register(
            data_analyzer,
            samples=[
                "analyze data",
                "process dataset",
            ],
        )

        # Should route to appropriate agent
        result = await router.route("Can you help with data analysis?")
        assert result is not None

    def test_semantic_router_cohere_encoder(self):
        """Test semantic router with Cohere encoder."""
        router = AgentRouter(strategy="semantic", encoder="cohere")
        assert router.encoder_type == "cohere"

    @pytest.mark.asyncio
    async def test_semantic_router_graceful_degradation(self):
        """Test graceful degradation when semantic router fails."""
        router = AgentRouter(strategy="semantic", fallback_agent=fallback_agent)

        router.register(
            code_reviewer,
            samples=["review code"],
        )

        # Should use fallback if semantic router fails (e.g., no API key)
        result = await router.route("test query")
        assert result is not None
