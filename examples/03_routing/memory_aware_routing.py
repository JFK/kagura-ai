"""Memory-Aware Routing - Route with conversation context

This example demonstrates:
- Using MemoryAwareRouter for context-based routing
- Combining memory and routing
- Stateful conversation routing
"""

import asyncio
from kagura import agent
from kagura.core.memory import MemoryManager, WorkingMemory
from kagura.core.routing import MemoryAwareRouter


# Create memory manager
memory = MemoryManager(backend=WorkingMemory())


# Define specialized agents
@agent(enable_memory=True)
async def shopping_assistant(
    query: str,
    memory_manager: MemoryManager
) -> str:
    """
    Shopping assistant with memory.
    Query: {{ query }}

    Help with product selection, cart, and checkout.
    """
    pass


@agent(enable_memory=True)
async def order_tracking(
    query: str,
    memory_manager: MemoryManager
) -> str:
    """
    Order tracking specialist.
    Query: {{ query }}

    Help track orders and delivery status.
    """
    pass


@agent(enable_memory=True)
async def returns_agent(
    query: str,
    memory_manager: MemoryManager
) -> str:
    """
    Returns and refunds specialist.
    Query: {{ query }}

    Help with returns, exchanges, and refunds.
    """
    pass


async def main():
    print("Memory-Aware Routing Demo")
    print("-" * 50)

    # Create memory-aware router
    router = MemoryAwareRouter(
        routes={
            "shopping": shopping_assistant,
            "tracking": order_tracking,
            "returns": returns_agent
        },
        memory_manager=memory,
        intent_examples={
            "shopping": ["buy", "cart", "product", "add"],
            "tracking": ["track", "delivery", "status", "where is"],
            "returns": ["return", "refund", "exchange", "cancel"]
        }
    )

    # Conversation flow
    queries = [
        "I want to buy a laptop",
        "Add it to my cart",  # Context: still shopping
        "Where's my order?",  # Switch to tracking
        "I want to return my previous purchase"  # Switch to returns
    ]

    for query in queries:
        # Route with memory context
        selected_agent = await router.route(query, memory_context=memory)

        # Call agent with memory
        response = await selected_agent(query, memory_manager=memory)

        print(f"\nQuery: {query}")
        print(f"Routed to: {selected_agent.__name__}")
        print(f"Response: {response}")

        # Update memory
        await memory.store(
            content=f"User: {query}\nAssistant: {response}",
            metadata={"agent": selected_agent.__name__}
        )

    # Show routing decisions were context-aware
    print("\n\n=== Memory Statistics ===")
    stats = await memory.stats()
    print(f"Total interactions: {stats.get('total_memories', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
