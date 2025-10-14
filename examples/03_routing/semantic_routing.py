"""Semantic Routing - Route queries by meaning

This example demonstrates:
- Using SemanticRouter for intent-based routing
- Vector embeddings for semantic matching
- More intelligent query routing
"""

import asyncio
from kagura import agent
from kagura.core.routing import SemanticRouter


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

    # Create router with example queries for each route
    router = SemanticRouter(
        routes={
            "support": technical_support,
            "sales": sales_agent,
            "docs": documentation_agent
        },
        examples={
            "support": [
                "My app crashed",
                "I'm getting an error message",
                "This feature isn't working"
            ],
            "sales": [
                "How much does it cost?",
                "What plans do you offer?",
                "Can I upgrade my subscription?"
            ],
            "docs": [
                "How do I use this feature?",
                "What is the API?",
                "Show me examples"
            ]
        }
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
        selected_agent = await router.route(query)
        response = await selected_agent(query)

        print(f"\nQuery: {query}")
        print(f"Routed to: {selected_agent.__name__}")
        print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
