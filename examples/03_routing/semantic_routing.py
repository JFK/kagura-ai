"""Semantic Routing - Route queries by meaning

This example demonstrates:
- Using AgentRouter with semantic strategy for intent-based routing
- Vector embeddings for semantic matching
- More intelligent query routing
"""

import asyncio

from kagura import agent
from kagura.routing import AgentRouter


# Define specialized agents
@agent
async def technical_support(query: str) -> str:
    """
    Technical support specialist.
    Query: {{ query }}

    Help with technical issues, bugs, and troubleshooting.
    """
    pass


@agent
async def sales_agent(query: str) -> str:
    """
    Sales representative.
    Query: {{ query }}

    Help with pricing, features, and purchasing.
    """
    pass


@agent
async def documentation_agent(query: str) -> str:
    """
    Documentation specialist.
    Query: {{ query }}

    Explain features and how to use the product.
    """
    pass


async def main():
    print("Semantic Routing Demo")
    print("-" * 50)
    print("Note: Requires semantic-router and OPENAI_API_KEY for embeddings\n")

    # Create router with semantic strategy
    router = AgentRouter(
        strategy="semantic",
        confidence_threshold=0.3,
        encoder="openai"
    )

    # Register agents with sample queries for semantic matching
    router.register(
        technical_support,
        samples=[
            "My app crashed",
            "I'm getting an error message",
            "This feature isn't working",
            "The application keeps freezing"
        ],
        description="Technical support specialist"
    )
    router.register(
        sales_agent,
        samples=[
            "How much does it cost?",
            "What plans do you offer?",
            "Can I upgrade my subscription?",
            "What's the pricing for enterprise?"
        ],
        description="Sales representative"
    )
    router.register(
        documentation_agent,
        samples=[
            "How do I use this feature?",
            "What is the API?",
            "Show me examples",
            "Can you explain how to integrate this?"
        ],
        description="Documentation specialist"
    )

    # Test queries (semantic matching)
    queries = [
        "The application keeps freezing",  # Support
        "What's the pricing for enterprise?",  # Sales
        "Can you explain how to integrate this?",  # Docs
        "I encountered a bug in the login",  # Support
        "Is there a free trial available?"  # Sales
    ]

    for query in queries:
        # Route based on semantic similarity
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
