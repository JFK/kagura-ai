"""AgentBuilder Presets Example

This example demonstrates how to configure AgentBuilder with preset-like
configurations for common agent types.
"""

import asyncio
from kagura import AgentBuilder


async def main():
    """Demonstrate AgentBuilder preset configurations."""
    print("=== AgentBuilder Presets ===\n")

    # Example 1: Quick preset (minimal configuration - fast, concise responses)
    print("1. Quick Preset - Fast Agent")
    quick_agent = (
        AgentBuilder("quick_responder")
        .with_model("gpt-4o-mini")
        .with_context(temperature=0.3, max_tokens=100)  # Fast, concise
        .build()
    )

    response = await quick_agent("Say hello!")
    print(f"Agent: {response}\n")

    # Example 2: Conversational preset (with memory)
    print("2. Conversational Preset - Chat Agent")
    chat_agent = (
        AgentBuilder("chatbot")
        .with_model("gpt-4o-mini")
        .with_memory(type="context", max_messages=50)  # Enable conversation memory
        .with_context(temperature=0.7, max_tokens=300)  # Balanced, conversational
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
        .with_model("gpt-4o-mini")
        .with_memory(type="context", max_messages=100)  # Large context for research
        .with_tools([search_web])
        .with_context(temperature=0.4, max_tokens=800)  # Factual, detailed
        .build()
    )

    response = await research_agent("Research the latest Python frameworks")
    print(f"Agent: {response}\n")

    # Example 4: Creative preset (high temperature)
    print("4. Creative Preset - Story Generator")
    creative_agent = (
        AgentBuilder("storyteller")
        .with_model("gpt-4o-mini")
        .with_context(temperature=1.2, max_tokens=1000)  # Highly creative
        .build()
    )

    response = await creative_agent("Write a short story about a robot learning to paint")
    print(f"Agent: {response}\n")

    # Example 5: Analytical preset (low temperature)
    print("5. Analytical Preset - Data Analyzer")
    analytical_agent = (
        AgentBuilder("analyzer")
        .with_model("gpt-4o-mini")
        .with_context(temperature=0.1, max_tokens=1000)  # Precise, analytical
        .build()
    )

    response = await analytical_agent("Analyze the pros and cons of microservices architecture")
    print(f"Agent: {response}\n")

    # Example 6: Custom configuration with combined settings
    print("6. Custom Configuration - Combined Settings")
    custom_agent = (
        AgentBuilder("custom_chatbot")
        .with_model("gpt-4o")  # Premium model
        .with_memory(type="context", max_messages=50)  # Conversational memory
        .with_context(temperature=0.8, max_tokens=500)  # Custom settings
        .build()
    )

    response = await custom_agent("Tell me something interesting about AI")
    print(f"Agent: {response}\n")

    # Example 7: Comparing configurations
    print("7. Configuration Comparison - Same Query, Different Styles")

    query = "Explain what machine learning is"

    # Quick (minimal)
    quick = (
        AgentBuilder("quick")
        .with_model("gpt-4o-mini")
        .with_context(temperature=0.3, max_tokens=150)
        .build()
    )
    print("Quick configuration:")
    print(f"  {await quick(query)}\n")

    # Analytical (detailed)
    analytical = (
        AgentBuilder("analytical")
        .with_model("gpt-4o-mini")
        .with_context(temperature=0.1, max_tokens=1000)
        .build()
    )
    print("Analytical configuration:")
    print(f"  {await analytical(query)}\n")

    # Creative (engaging)
    creative = (
        AgentBuilder("creative")
        .with_model("gpt-4o-mini")
        .with_context(temperature=1.2, max_tokens=800)
        .build()
    )
    print("Creative configuration:")
    print(f"  {await creative(query)}\n")


if __name__ == "__main__":
    asyncio.run(main())
