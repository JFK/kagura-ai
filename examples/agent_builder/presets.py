"""AgentBuilder Presets Example

This example demonstrates how to use AgentBuilder's built-in presets
for quickly creating common agent types.
"""

import asyncio
from kagura import AgentBuilder


async def main():
    """Demonstrate AgentBuilder presets."""
    print("=== AgentBuilder Presets ===\n")

    # Example 1: Quick preset (minimal configuration)
    print("1. Quick Preset - Fast Agent")
    quick_agent = (
        AgentBuilder("quick_responder")
        .with_preset("quick")
        .build()
    )

    response = await quick_agent("Say hello!")
    print(f"Agent: {response}\n")

    # Example 2: Conversational preset (with memory)
    print("2. Conversational Preset - Chat Agent")
    chat_agent = (
        AgentBuilder("chatbot")
        .with_preset("conversational")
        .build()
    )

    response1 = await chat_agent("Hi! I'm interested in learning Python")
    print(f"Agent: {response1}")

    response2 = await chat_agent("What should I start with?")
    print(f"Agent: {response2}\n")

    # Example 3: Research preset (with tools and memory)
    print("3. Research Preset - Knowledge Agent")

    def search_web(query: str) -> str:
        """Mock web search."""
        return f"Search results for: {query}"

    research_agent = (
        AgentBuilder("researcher")
        .with_preset("research")
        .with_tools([search_web])
        .build()
    )

    response = await research_agent("Research the latest Python frameworks")
    print(f"Agent: {response}\n")

    # Example 4: Creative preset (high temperature)
    print("4. Creative Preset - Story Generator")
    creative_agent = (
        AgentBuilder("storyteller")
        .with_preset("creative")
        .build()
    )

    response = await creative_agent("Write a short story about a robot learning to paint")
    print(f"Agent: {response}\n")

    # Example 5: Analytical preset (low temperature)
    print("5. Analytical Preset - Data Analyzer")
    analytical_agent = (
        AgentBuilder("analyzer")
        .with_preset("analytical")
        .build()
    )

    response = await analytical_agent("Analyze the pros and cons of microservices architecture")
    print(f"Agent: {response}\n")

    # Example 6: Custom preset with overrides
    print("6. Preset with Custom Overrides")
    custom_agent = (
        AgentBuilder("custom_chatbot")
        .with_preset("conversational")  # Start with conversational preset
        .with_model("gpt-4o")  # Override model
        .with_context(temperature=0.8)  # Override temperature
        .build()
    )

    response = await custom_agent("Tell me something interesting about AI")
    print(f"Agent: {response}\n")

    # Example 7: Comparing presets
    print("7. Preset Comparison - Same Query, Different Styles")

    query = "Explain what machine learning is"

    # Quick (minimal)
    quick = (
        AgentBuilder("quick")
        .with_preset("quick")
        .build()
    )
    print("Quick preset:")
    print(f"  {await quick(query)}\n")

    # Analytical (detailed)
    analytical = (
        AgentBuilder("analytical")
        .with_preset("analytical")
        .build()
    )
    print("Analytical preset:")
    print(f"  {await analytical(query)}\n")

    # Creative (engaging)
    creative = (
        AgentBuilder("creative")
        .with_preset("creative")
        .build()
    )
    print("Creative preset:")
    print(f"  {await creative(query)}\n")


if __name__ == "__main__":
    asyncio.run(main())
