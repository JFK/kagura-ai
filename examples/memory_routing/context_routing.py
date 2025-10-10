"""Context-Aware Routing Example

This example demonstrates memory-aware routing that maintains conversation
context and automatically routes to appropriate agents.
"""

import asyncio
from kagura import agent
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager


# Define specialized agents
@agent(model="gpt-4o-mini")
async def translator(text: str, target_language: str) -> str:
    """Translate "{{ text }}" to {{ target_language }}"""
    pass


@agent(model="gpt-4o-mini")
async def calculator(expression: str) -> str:
    """Calculate: {{ expression }}"""
    pass


@agent(model="gpt-4o-mini")
async def summarizer(text: str) -> str:
    """Summarize: {{ text }}"""
    pass


@agent(model="gpt-4o-mini")
async def general_assistant(query: str) -> str:
    """Answer: {{ query }}"""
    pass


async def main():
    """Demonstrate context-aware routing."""
    print("=== Context-Aware Routing Example ===\n")

    # Initialize memory and router
    memory = MemoryManager(agent_name="router_demo")
    router = MemoryAwareRouter(memory=memory, context_window=5)

    # Register agents with intents
    router.register(translator, intents=["translate", "translation"])
    router.register(calculator, intents=["calculate", "math", "compute"])
    router.register(summarizer, intents=["summarize", "summary"])
    router.register(general_assistant, intents=["general"])  # Fallback

    # Example 1: Basic routing without context
    print("1. Basic Routing")
    print("-" * 50)

    result = await router.route("Translate 'hello' to French")
    print(f"Query: Translate 'hello' to French")
    print(f"Routed to: translator")
    print(f"Result: {result}\n")

    result = await router.route("What is 25 * 4?")
    print(f"Query: What is 25 * 4?")
    print(f"Routed to: calculator")
    print(f"Result: {result}\n")

    # Example 2: Context-dependent routing
    print("2. Context-Dependent Routing")
    print("-" * 50)

    # First query establishes context
    result1 = await router.route("Translate 'hello' to French")
    print(f"Query 1: Translate 'hello' to French")
    print(f"Result 1: {result1}")

    # Follow-up query uses context
    result2 = await router.route("What about Spanish?")
    print(f"\nQuery 2: What about Spanish?")
    print(f"Context used: Previous translation request")
    print(f"Result 2: {result2}\n")

    # Example 3: Multi-turn conversation
    print("3. Multi-Turn Conversation with Context")
    print("-" * 50)

    conversation = [
        ("Calculate 100 + 50", "Initial calculation"),
        ("Multiply that by 2", "Uses previous result"),
        ("What about dividing by 3?", "Continues calculation context"),
    ]

    for query, description in conversation:
        result = await router.route(query)
        print(f"Query: {query}")
        print(f"  ({description})")
        print(f"Result: {result}\n")

    # Example 4: Context switching
    print("4. Context Switching")
    print("-" * 50)

    # Translation context
    await router.route("Translate 'good morning' to Japanese")
    print("Established: Translation context")

    # Switch to calculation context
    result = await router.route("Calculate 2 + 2")
    print(f"\nSwitched to: Calculation context")
    print(f"Result: {result}")

    # Back to translation (but specific)
    result = await router.route("Translate 'thank you' to German")
    print(f"\nBack to: Translation (explicit)")
    print(f"Result: {result}\n")

    # Example 5: Pronoun resolution
    print("5. Pronoun Resolution")
    print("-" * 50)

    # Set up context
    await router.route("What is machine learning?")
    print("Context: Asked about machine learning")

    # Query with pronouns
    result = await router.route("Can you explain it in simpler terms?")
    print(f"\nQuery with pronoun: Can you explain it in simpler terms?")
    print(f"Router resolves 'it' to 'machine learning'")
    print(f"Result: {result}\n")

    # Example 6: Demonstrative pronouns
    print("6. Demonstrative Pronouns")
    print("-" * 50)

    # First query
    await router.route("Summarize this: Python is a programming language")
    print("Query: Summarize this: Python is a programming language")

    # Follow-up with 'that'
    result = await router.route("What about that?")
    print(f"\nFollow-up: What about that?")
    print(f"Router uses context to understand 'that'")
    print(f"Result: {result}\n")

    # Example 7: Context window limit
    print("7. Context Window Behavior")
    print("-" * 50)

    # Fill context window with multiple queries
    for i in range(7):
        await router.route(f"Calculate {i} + 1")

    print(f"Sent 7 calculation queries")
    print(f"Context window size: {router.context_window}")
    print(f"Only last {router.context_window} queries are kept in context\n")

    # Example 8: Viewing context
    print("8. Inspecting Conversation Context")
    print("-" * 50)

    # Get recent context
    context = memory.get_context(last_n=3)
    print(f"Last {len(context)} messages in context:")
    for i, msg in enumerate(context, 1):
        print(f"  {i}. [{msg.role}]: {msg.content[:50]}...")

    print()

    # Example 9: Context-aware fallback
    print("9. Context-Aware Fallback")
    print("-" * 50)

    # Ambiguous query without clear intent
    result = await router.route("Tell me more")
    print(f"Ambiguous query: Tell me more")
    print(f"Router uses conversation context to understand request")
    print(f"Result: {result}\n")

    # Example 10: Clearing context
    print("10. Clearing Context")
    print("-" * 50)

    print("Before clear:")
    print(f"  Context messages: {len(memory.get_context())}")

    memory.clear_all()
    print("\nAfter clear:")
    print(f"  Context messages: {len(memory.get_context())}")
    print(f"  Fresh start for new conversation\n")


async def advanced_patterns():
    """Demonstrate advanced context-aware routing patterns."""
    print("\n" + "=" * 60)
    print("=== Advanced Context Patterns ===\n")

    memory = MemoryManager(agent_name="advanced_demo")
    router = MemoryAwareRouter(memory=memory, context_window=10)

    # Register agents
    router.register(translator, intents=["translate"])
    router.register(calculator, intents=["calculate"])
    router.register(general_assistant, intents=["general"])

    # Pattern 1: Context preservation across domains
    print("1. Cross-Domain Context")
    print("-" * 50)

    await router.route("Translate 'hello' to French")
    result = await router.route("What was that translation again?")
    print(f"Query: What was that translation again?")
    print(f"Context preserved across queries")
    print(f"Result: {result}\n")

    # Pattern 2: Nested context
    print("2. Nested Context Handling")
    print("-" * 50)

    await router.route("Calculate 10 * 5")
    await router.route("Actually, make that 10 * 6")
    result = await router.route("And add 100 to that")
    print(f"Query: And add 100 to that")
    print(f"Handles nested corrections and references")
    print(f"Result: {result}\n")

    # Pattern 3: Context with memory persistence
    print("3. Persistent Context")
    print("-" * 50)

    # Save session
    memory.save_session("demo_session")
    print("Session saved with current context")

    # Simulate new session
    new_memory = MemoryManager(agent_name="advanced_demo")
    if new_memory.load_session("demo_session"):
        print("Session loaded successfully")
        print(f"Restored {len(new_memory.get_context())} messages\n")


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())

    # Run advanced patterns
    asyncio.run(advanced_patterns())

    print("=" * 60)
    print("Context-aware routing demo complete! 🎉")
