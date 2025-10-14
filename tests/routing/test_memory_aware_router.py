"""Tests for MemoryAwareRouter."""

import pytest

from kagura.core.memory import MemoryManager
from kagura.routing import MemoryAwareRouter, NoAgentFoundError


# ===== Test Agents (Mock functions, not real agents) =====


async def translator_agent(query: str) -> str:
    """Mock translator agent."""
    return f"Translated: {query}"


async def code_reviewer_agent(query: str) -> str:
    """Mock code reviewer agent."""
    return f"Reviewed: {query}"


async def calculator_agent(query: str) -> str:
    """Mock calculator agent."""
    return f"Calculated: {query}"


# ===== Initialization Tests =====


def test_memory_aware_router_initialization():
    """Test MemoryAwareRouter initialization."""
    memory = MemoryManager(agent_name="test_agent")
    router = MemoryAwareRouter(
        memory=memory, context_window=5, use_semantic_context=False
    )

    assert router.memory is memory
    assert router.context_window == 5
    assert router.use_semantic_context is False
    assert router.context_analyzer is not None


def test_memory_aware_router_default_params():
    """Test MemoryAwareRouter with default parameters."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory)

    assert router.context_window == 5
    assert router.use_semantic_context is True
    assert router.strategy == "intent"
    assert router.confidence_threshold == 0.3


# ===== Registration Tests =====


def test_register_agent():
    """Test agent registration."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory)

    router.register(translator_agent, intents=["translate", "翻訳"])

    agents = router.list_agents()
    assert "translator_agent" in agents


def test_register_multiple_agents():
    """Test registering multiple agents."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory)

    router.register(translator_agent, intents=["translate"])
    router.register(code_reviewer_agent, intents=["review", "check"])
    router.register(calculator_agent, intents=["calculate", "compute"])

    agents = router.list_agents()
    assert len(agents) == 3
    assert "translator_agent" in agents
    assert "code_reviewer_agent" in agents
    assert "calculator_agent" in agents


# ===== Basic Routing Tests =====


@pytest.mark.asyncio
async def test_route_simple_query():
    """Test routing a simple query without context."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate", "翻訳"])

    result = await router.route("Translate hello to French")

    assert "Translated:" in result
    assert "hello" in result.lower()


@pytest.mark.asyncio
async def test_route_with_agent_selection():
    """Test router selects correct agent."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate"])
    router.register(code_reviewer_agent, intents=["review", "check"])

    # Test translator selection
    result1 = await router.route("Translate this to Spanish")
    assert "Translated:" in result1

    # Test code reviewer selection
    result2 = await router.route("Check this code for bugs")
    assert "Reviewed:" in result2


@pytest.mark.asyncio
async def test_route_no_agent_found():
    """Test routing when no agent matches."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate"])

    with pytest.raises(NoAgentFoundError):
        await router.route("Show me the weather")


# ===== Context-Aware Routing Tests =====


@pytest.mark.asyncio
async def test_route_with_context_detection():
    """Test context detection in queries."""
    memory = MemoryManager(enable_compression=False)
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate"])

    # First query (no context needed)
    await router.route("Translate 'hello' to French")

    # Second query (context-dependent)
    result = await router.route("What about Spanish?")

    # Should still route to translator
    assert "Translated:" in result


@pytest.mark.asyncio
async def test_route_stores_conversation():
    """Test that routing stores conversation in memory."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate"])

    # Execute query
    await router.route("Translate hello")

    # Check memory
    messages = memory.get_context()
    assert len(messages) >= 2  # User message + assistant response

    # Check user message
    user_msgs = [m for m in messages if m.role == "user"]
    assert len(user_msgs) >= 1
    assert "hello" in user_msgs[-1].content.lower()

    # Check assistant message
    assistant_msgs = [m for m in messages if m.role == "assistant"]
    assert len(assistant_msgs) >= 1
    assert "Translated:" in assistant_msgs[-1].content


@pytest.mark.asyncio
async def test_route_with_pronoun_query():
    """Test routing with pronoun-based context query."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(code_reviewer_agent, intents=["review", "check"])

    # First query
    await router.route("Review my Python code")

    # Context-dependent query
    result = await router.route("Can you check it again?")

    assert "Reviewed:" in result


@pytest.mark.asyncio
async def test_route_with_implicit_reference():
    """Test routing with implicit reference query."""
    memory = MemoryManager(enable_compression=False)
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate"])

    # First query
    await router.route("Translate 'good morning' to French")

    # Context-dependent query with implicit reference
    result = await router.route("Do it again")

    assert "Translated:" in result


# ===== Context Window Tests =====


@pytest.mark.asyncio
async def test_context_window_limit():
    """Test context window limits number of messages considered."""
    memory = MemoryManager()
    router = MemoryAwareRouter(
        memory=memory, context_window=2, use_semantic_context=False
    )

    router.register(translator_agent, intents=["translate"])

    # Add multiple queries to exceed context window
    for i in range(5):
        await router.route(f"Translate message {i}")

    # Context should only have last 2*2 messages (user + assistant pairs)
    messages = memory.get_context()
    # We've made 5 queries, each generating 2 messages (user + assistant)
    # So total is 10 messages, but we only retrieve context_window (2) for routing
    assert len(messages) == 10


# ===== Conversation Summary Tests =====


def test_get_conversation_summary_empty():
    """Test conversation summary with no history."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory)

    summary = router.get_conversation_summary()
    assert summary == "No conversation history"


@pytest.mark.asyncio
async def test_get_conversation_summary():
    """Test conversation summary with messages."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate"])

    # Add some conversation
    await router.route("Translate hello")
    await router.route("Translate goodbye")

    summary = router.get_conversation_summary()

    assert "User:" in summary
    assert "Assistant:" in summary
    assert "hello" in summary.lower()


def test_get_conversation_summary_truncation():
    """Test conversation summary truncates long messages."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory)

    # Add long message
    long_message = "A" * 200
    memory.add_message("user", long_message)

    summary = router.get_conversation_summary()

    # Should be truncated with "..."
    assert "..." in summary
    assert len(summary) < len(long_message) + 50


# ===== Clear Context Tests =====


@pytest.mark.asyncio
async def test_clear_context():
    """Test clearing conversation context."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate"])

    # Add conversation
    await router.route("Translate hello")

    # Verify context exists
    assert len(memory.get_context()) > 0

    # Clear context
    router.clear_context()

    # Verify context is cleared
    assert len(memory.get_context()) == 0


# ===== Error Handling Tests =====


@pytest.mark.asyncio
async def test_route_error_stored_in_memory():
    """Test that routing errors are stored in memory."""
    memory = MemoryManager()
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    # No agents registered
    try:
        await router.route("This will fail")
    except NoAgentFoundError:
        pass

    # Check that error was stored
    messages = memory.get_context()
    assistant_msgs = [m for m in messages if m.role == "assistant"]

    assert len(assistant_msgs) > 0
    assert "Error:" in assistant_msgs[-1].content


# ===== Integration Tests =====


@pytest.mark.asyncio
async def test_full_conversation_flow():
    """Test full conversation flow with context."""
    memory = MemoryManager(enable_compression=False)
    router = MemoryAwareRouter(memory=memory, use_semantic_context=False)

    router.register(translator_agent, intents=["translate", "翻訳"])
    router.register(code_reviewer_agent, intents=["review", "check"])

    # Initial translation request
    result1 = await router.route("Translate 'hello' to French")
    assert "Translated:" in result1

    # Context-dependent follow-up
    result2 = await router.route("What about Spanish?")
    assert "Translated:" in result2

    # Switch to code review
    result3 = await router.route("Review this Python code")
    assert "Reviewed:" in result3

    # Context-dependent follow-up for code review
    result4 = await router.route("Check it again")
    assert "Reviewed:" in result4

    # Verify all messages stored
    messages = memory.get_context()
    assert len(messages) == 8  # 4 queries * 2 messages each


@pytest.mark.asyncio
async def test_fallback_agent():
    """Test fallback agent when no match found."""

    async def fallback(query: str) -> str:
        """Mock fallback handler."""
        return f"Fallback: {query}"

    memory = MemoryManager()
    router = MemoryAwareRouter(
        memory=memory, fallback_agent=fallback, use_semantic_context=False
    )

    router.register(translator_agent, intents=["translate"])

    # Query that doesn't match translator
    result = await router.route("Show me the weather")

    assert "Fallback:" in result


# ===== RAG Integration Tests =====


@pytest.mark.asyncio
async def test_route_with_rag_disabled():
    """Test routing with RAG disabled."""
    memory = MemoryManager(enable_rag=False)
    router = MemoryAwareRouter(memory=memory, use_semantic_context=True)

    router.register(translator_agent, intents=["translate"])

    # Should work even with use_semantic_context=True but RAG disabled
    result = await router.route("Translate hello")
    assert "Translated:" in result
