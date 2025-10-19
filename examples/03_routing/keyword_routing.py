"""Keyword Routing - Route queries by keywords

This example demonstrates:
- Using AgentRouter with intent strategy for rule-based routing
- Defining keyword intents for different agents
- Fallback handling
"""

import asyncio
from kagura import agent
from kagura.routing import AgentRouter


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

    # Create router with intent strategy (keyword-based)
    router = AgentRouter(
        strategy="intent",
        fallback_agent=general_agent,
        confidence_threshold=0.3
    )

    # Register agents with intent keywords
    router.register(
        weather_agent,
        intents=["weather", "temperature", "rain", "forecast", "sunny"],
        description="Weather specialist"
    )
    router.register(
        math_agent,
        intents=["calculate", "math", "equation", "solve", "number"],
        description="Math specialist"
    )
    router.register(
        general_agent,
        intents=["general", "question", "help"],
        description="General assistant"
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
        response = await router.route(query)

        # Get matched agents for display
        matches = router.get_matched_agents(query, top_k=1)
        if matches:
            selected_name = matches[0][0].__name__
            confidence = matches[0][1]
            print(f"\nQuery: {query}")
            print(f"Routed to: {selected_name} (confidence: {confidence:.2f})")
            print(f"Response: {response}")
        else:
            print(f"\nQuery: {query}")
            print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
