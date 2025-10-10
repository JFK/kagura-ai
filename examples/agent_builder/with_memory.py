"""AgentBuilder with Memory Example

This example demonstrates how to create agents with different memory configurations
using AgentBuilder's fluent API.
"""

import asyncio
from pathlib import Path
from kagura import AgentBuilder


async def main():
    """Demonstrate AgentBuilder with memory integration."""
    print("=== AgentBuilder with Memory ===\n")

    # Example 1: Basic memory (context only)
    print("1. Basic Memory (Conversation Context)")
    basic_memory_agent = (
        AgentBuilder("context_agent")
        .with_model("gpt-4o-mini")
        .with_memory(
            type="context",
            max_messages=50
        )
        .build()
    )

    # First conversation
    response1 = await basic_memory_agent("My name is Alice")
    print(f"Agent: {response1}")

    # Follow-up (should remember name)
    response2 = await basic_memory_agent("What's my name?")
    print(f"Agent: {response2}\n")

    # Example 2: Persistent memory
    print("2. Persistent Memory (Long-term Storage)")
    persistent_agent = (
        AgentBuilder("assistant")
        .with_model("gpt-4o-mini")
        .with_memory(
            type="persistent",
            persist_dir=Path.home() / ".kagura" / "examples",
            max_messages=100
        )
        .build()
    )

    response = await persistent_agent("Remember: My favorite color is blue")
    print(f"Agent: {response}")

    # Later sessions can recall this information
    response = await persistent_agent("What's my favorite color?")
    print(f"Agent: {response}\n")

    # Example 3: RAG-enabled memory (Semantic search)
    print("3. RAG-Enabled Memory (Semantic Search)")
    rag_agent = (
        AgentBuilder("knowledge_agent")
        .with_model("gpt-4o-mini")
        .with_memory(
            type="persistent",
            enable_rag=True,
            max_messages=100
        )
        .build()
    )

    # Store multiple facts
    await rag_agent("Python is a high-level programming language")
    await rag_agent("JavaScript is used for web development")
    await rag_agent("Rust focuses on memory safety")

    # Semantic search (finds relevant information)
    response = await rag_agent("Tell me about programming languages for systems")
    print(f"Agent: {response}\n")

    # Example 4: Session-based memory
    print("4. Session-Based Memory")
    session_agent = (
        AgentBuilder("session_agent")
        .with_model("gpt-4o-mini")
        .with_memory(
            type="persistent",
            max_messages=50
        )
        .with_session_id("user_123_session_1")
        .build()
    )

    response = await session_agent("Start of session 1")
    print(f"Agent: {response}")

    # Save session
    if hasattr(session_agent, 'memory') and session_agent.memory:
        session_agent.memory.save_session("example_session")
        print("Session saved!\n")

    # Example 5: Memory with custom configuration
    print("5. Custom Memory Configuration")
    custom_agent = (
        AgentBuilder("custom_memory_agent")
        .with_model("gpt-4o-mini")
        .with_memory(
            type="persistent",
            enable_rag=True,
            persist_dir=Path("./agent_data"),
            max_messages=200
        )
        .with_context(
            temperature=0.7,
            max_tokens=1000
        )
        .build()
    )

    response = await custom_agent("This agent has custom memory settings")
    print(f"Agent: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
