"""Working Memory - Short-term conversational memory

This example demonstrates:
- Using WorkingMemory for short-term context
- Maintaining conversation history
- Memory-enabled agents
"""

import asyncio
from kagura import agent
from kagura.core.memory import MemoryManager, WorkingMemory


# Create memory manager with working memory
memory = MemoryManager(backend=WorkingMemory())


@agent(enable_memory=True)
async def assistant(query: str, memory_manager: MemoryManager) -> str:
    """
    You are a helpful assistant with memory of our conversation.

    User: {{ query }}

    Use the conversation history to provide contextual responses.
    """
    pass


async def main():
    print("Working Memory Demo - Assistant remembers context")
    print("-" * 50)

    # First interaction
    response1 = await assistant(
        "My name is Alice and I'm learning Python.",
        memory_manager=memory
    )
    print(f"User: My name is Alice and I'm learning Python.")
    print(f"Assistant: {response1}\n")

    # Second interaction - assistant remembers the name
    response2 = await assistant(
        "What's my name?",
        memory_manager=memory
    )
    print(f"User: What's my name?")
    print(f"Assistant: {response2}\n")

    # Third interaction - assistant remembers the topic
    response3 = await assistant(
        "Can you recommend some resources for what I'm learning?",
        memory_manager=memory
    )
    print(f"User: Can you recommend some resources for what I'm learning?")
    print(f"Assistant: {response3}\n")

    # Show memory stats
    print("\nMemory Statistics:")
    stats = await memory.stats()
    print(f"  Total memories: {stats.get('total_memories', 0)}")
    print(f"  Working memory size: {stats.get('working_memory_size', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
