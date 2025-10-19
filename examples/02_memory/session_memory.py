"""Session Memory - Isolated memory per session/user

This example demonstrates:
- Session-scoped memory isolation
- Multiple users with separate contexts
- Memory cleanup and management
"""

import asyncio
from kagura import agent
from kagura.core.memory import MemoryManager, WorkingMemory


# Create separate memory managers for different sessions
session_memories: dict[str, MemoryManager] = {}


def get_session_memory(session_id: str) -> MemoryManager:
    """Get or create memory for a session"""
    if session_id not in session_memories:
        session_memories[session_id] = MemoryManager(
            agent_name=f"session_{session_id}",
            max_messages=50
        )
    return session_memories[session_id]


@agent(enable_memory=True)
async def session_assistant(
    message: str,
    memory_manager: MemoryManager
) -> str:
    """
    You are a helpful assistant with session memory.

    User: {{ message }}

    Remember context within this session only.
    """
    pass


async def simulate_session(session_id: str, messages: list[str]):
    """Simulate a user session"""
    print(f"\n=== Session: {session_id} ===")
    memory = get_session_memory(session_id)

    for msg in messages:
        response = await session_assistant(msg, memory_manager=memory)
        print(f"User: {msg}")
        print(f"Assistant: {response}\n")


async def main():
    print("Session Memory Demo - Isolated contexts per user")
    print("-" * 50)

    # Simulate two different user sessions
    await simulate_session(
        "user_alice",
        [
            "Hi! My name is Alice.",
            "I'm interested in machine learning.",
            "What's my name and interest?"
        ]
    )

    await simulate_session(
        "user_bob",
        [
            "Hello! I'm Bob.",
            "I love playing guitar.",
            "What do you know about me?"
        ]
    )

    # Show that sessions are isolated
    print("\n=== Memory Isolation Test ===")
    alice_memory = get_session_memory("user_alice")
    bob_memory = get_session_memory("user_bob")

    # Alice's assistant shouldn't know about Bob
    response = await session_assistant(
        "Do you know anything about Bob?",
        memory_manager=alice_memory
    )
    print(f"Alice's session asks about Bob: {response}")

    # Show memory stats
    print("\n=== Memory Statistics ===")
    for session_id, memory in session_memories.items():
        stats = await memory.stats()
        print(f"{session_id}: {stats.get('total_memories', 0)} memories")


if __name__ == "__main__":
    asyncio.run(main())
