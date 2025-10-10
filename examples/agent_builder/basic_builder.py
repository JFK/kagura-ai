"""Basic AgentBuilder Example

This example demonstrates the basic usage of AgentBuilder's fluent API
to create agents with integrated features.
"""

import asyncio
from kagura import AgentBuilder


async def main():
    """Demonstrate basic AgentBuilder usage."""
    print("=== Basic AgentBuilder Example ===\n")

    # Example 1: Simple agent with just a model
    print("1. Simple Agent")
    simple_agent = (
        AgentBuilder("greeter")
        .with_model("gpt-4o-mini")
        .build()
    )

    response = await simple_agent("Say hello!")
    print(f"Response: {response}\n")

    # Example 2: Agent with custom parameters
    print("2. Agent with Custom Parameters")
    factual_agent = (
        AgentBuilder("fact_checker")
        .with_model("gpt-4o-mini")
        .with_context(
            temperature=0.2,  # More deterministic
            max_tokens=500
        )
        .build()
    )

    response = await factual_agent("What is the capital of France?")
    print(f"Response: {response}\n")

    # Example 3: Creative agent
    print("3. Creative Agent")
    creative_agent = (
        AgentBuilder("storyteller")
        .with_model("gpt-4o-mini")
        .with_context(
            temperature=1.5,  # More creative
            max_tokens=1000
        )
        .build()
    )

    response = await creative_agent("Tell me a short story about a robot")
    print(f"Response: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
