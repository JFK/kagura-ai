"""Keyword Routing - Route queries by keywords

This example demonstrates:
- Using KeywordRouter for rule-based routing
- Defining keyword patterns for different agents
- Fallback handling
"""

import asyncio
from kagura import agent
from kagura.core.routing import KeywordRouter


# Define specialized agents
@agent
async def weather_agent(query: str) -> str:
    """
    Weather specialist. Query: {{ query }}
    Provide weather information or forecast.
    """
    pass


@agent
async def math_agent(query: str) -> str:
    """
    Math specialist. Query: {{ query }}
    Solve mathematical problems or explain concepts.
    """
    pass


@agent
async def general_agent(query: str) -> str:
    """
    General assistant. Query: {{ query }}
    Answer general questions helpfully.
    """
    pass


async def main():
    print("Keyword Routing Demo")
    print("-" * 50)

    # Create router with keyword patterns
    router = KeywordRouter(
        routes={
            "weather": weather_agent,
            "math": math_agent,
            "general": general_agent
        },
        patterns={
            "weather": ["weather", "temperature", "rain", "forecast", "sunny"],
            "math": ["calculate", "math", "equation", "solve", "number"]
        },
        default_route="general"  # Fallback
    )

    # Test queries
    queries = [
        "What's the weather like today?",
        "Calculate 15 * 23",
        "Tell me a joke",
        "Will it rain tomorrow?",
        "Solve the equation x + 5 = 10"
    ]

    for query in queries:
        # Route query to appropriate agent
        selected_agent = router.route(query)
        response = await selected_agent(query)

        print(f"\nQuery: {query}")
        print(f"Routed to: {selected_agent.__name__}")
        print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
