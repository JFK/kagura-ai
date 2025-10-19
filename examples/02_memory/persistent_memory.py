"""Persistent Memory - Long-term memory with file storage

This example demonstrates:
- Using PersistentMemory for long-term storage
- Saving memories to disk
- Retrieving memories across sessions
"""

import asyncio
from pathlib import Path
from kagura import agent
from kagura.core.memory import MemoryManager, PersistentMemory


# Create persistent memory with file storage
storage_path = Path("./memory_storage")
storage_path.mkdir(exist_ok=True)

persistent_memory = MemoryManager(
    agent_name="note_keeper",
    persist_dir=storage_path,
    max_messages=100
)


@agent(enable_memory=True)
async def note_keeper(command: str, memory_manager: MemoryManager) -> str:
    """
    You are a note-keeping assistant with persistent memory.

    User command: {{ command }}

    Commands:
    - "remember [something]" - Store information
    - "recall [topic]" - Retrieve stored information
    - "what do you know about [topic]" - Search knowledge

    Respond naturally and helpfully.
    """
    pass


async def main():
    print("Persistent Memory Demo - Notes saved to disk")
    print("-" * 50)

    # Store some information
    commands = [
        "remember that my birthday is May 15th",
        "remember I like coffee and tea",
        "remember my favorite color is blue"
    ]

    for cmd in commands:
        response = await note_keeper(cmd, memory_manager=persistent_memory)
        print(f"User: {cmd}")
        print(f"Assistant: {response}\n")

    # Retrieve information
    print("\n--- Retrieving Information ---\n")

    queries = [
        "what's my birthday?",
        "what do you know about my preferences?",
        "recall my favorite color"
    ]

    for query in queries:
        response = await note_keeper(query, memory_manager=persistent_memory)
        print(f"User: {query}")
        print(f"Assistant: {response}\n")

    # Show memory stats
    print("\nMemory Statistics:")
    stats = await persistent_memory.stats()
    print(f"  Total memories: {stats.get('total_memories', 0)}")
    print(f"  Storage path: {storage_path.absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
