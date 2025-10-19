"""Web Search - Search the web using Brave Search

This example demonstrates:
- Integrating web search into agents
- Using Brave Search API
- Answering questions with real-time web data
"""

import asyncio
import os
from kagura import agent, tool


@tool
async def brave_search(query: str, count: int = 5) -> str:
    """Search the web using Brave Search API

    Args:
        query: Search query
        count: Number of results (default: 5)

    Returns:
        Search results as formatted text
    """
    # This would use actual Brave Search API
    # For demo purposes, we'll simulate
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")

    if not api_key:
        return "Error: BRAVE_SEARCH_API_KEY not set"

    # In real implementation:
    # import requests
    # response = requests.get(
    #     "https://api.search.brave.com/res/v1/web/search",
    #     headers={"X-Subscription-Token": api_key},
    #     params={"q": query, "count": count}
    # )
    # results = response.json()

    # Simulated results
    return f"""
Search results for: {query}
1. Wikipedia article about {query}
2. Official documentation for {query}
3. Tutorial: Getting started with {query}
4. Recent news about {query}
5. Community forum discussions on {query}
"""


@agent(tools=[brave_search])
async def search_assistant(question: str) -> str:
    """
    Answer this question using web search: {{ question }}

    Use the brave_search tool to find current information,
    then synthesize a clear answer.
    """
    pass


@agent(tools=[brave_search])
async def fact_checker(claim: str) -> str:
    """
    Fact-check this claim using web search: {{ claim }}

    Search for reliable sources and determine if the claim is:
    - TRUE
    - FALSE
    - PARTIALLY TRUE
    - UNVERIFIED

    Explain your reasoning with sources.
    """
    pass


async def main():
    print("Web Search Demo (Brave Search)")
    print("-" * 50)

    # Check for API key
    if not os.getenv("BRAVE_SEARCH_API_KEY"):
        print("⚠️  BRAVE_SEARCH_API_KEY not set")
        print("Set it with: export BRAVE_SEARCH_API_KEY='your_key'")
        print("Get key at: https://brave.com/search/api/")
        print("\nNote: This example uses simulated search results.")
        print("Some queries may hit 'Maximum tool iterations' due to simulation.")
        print("With real API, results are returned directly.\n")

    # Answer questions using web search
    questions = [
        "What is the current version of Python?",
        "Who won the latest FIFA World Cup?",
        "What are the main features of Rust programming language?"
    ]

    print("=== Question Answering ===")
    for question in questions:
        answer = await search_assistant(question)
        print(f"\nQ: {question}")
        print(f"A: {answer}")

    # Fact checking
    print("\n\n=== Fact Checking ===")
    claims = [
        "Python was created in 1991",
        "The Earth is flat",
        "AI can pass the Turing test"
    ]

    for claim in claims:
        result = await fact_checker(claim)
        print(f"\nClaim: {claim}")
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
