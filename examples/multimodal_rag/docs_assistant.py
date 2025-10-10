"""Multimodal RAG Documentation Assistant Example

This example demonstrates how to create a documentation assistant that can search
across text files, images, PDFs, audio, and video using Kagura AI 2.0's
Multimodal RAG capabilities.

Prerequisites:
    pip install kagura-ai[multimodal]
    export GOOGLE_API_KEY="your-gemini-api-key"

Directory Structure:
    sample_docs/
    ├── README.md          # Project overview
    ├── api/
    │   └── authentication.md
    ├── guides/
    │   ├── getting-started.md
    │   └── advanced.md
    └── diagrams/
        └── architecture.png
"""

import asyncio
from pathlib import Path

from kagura import agent


@agent(
    model="gpt-4o-mini",
    temperature=0.7,
    enable_multimodal_rag=True,
    rag_directory=Path(__file__).parent / "sample_docs",
)
async def docs_assistant(query: str, rag) -> str:
    """You are a helpful documentation assistant.

    First, search the documentation using: rag.query("{{ query }}", n_results=3)
    Then provide a comprehensive answer based on the search results.

    If no relevant information is found, say so clearly and suggest
    what documentation might be missing.

    Question: {{ query }}
    """
    pass


async def main():
    """Run the multimodal RAG documentation assistant with example queries."""
    print("=== Multimodal RAG Documentation Assistant ===\n")
    print("Building knowledge base from sample_docs/...")
    print("(This may take a moment on first run)\n")

    # Example 1: Basic documentation query
    print("1. Basic Documentation Query")
    print("-" * 50)
    query1 = "How do I get started with this project?"
    print(f"Query: {query1}")
    response1 = await docs_assistant(query1)
    print(f"Answer: {response1}\n")

    # Example 2: API-specific question
    print("2. API-Specific Question")
    print("-" * 50)
    query2 = "How does authentication work?"
    print(f"Query: {query2}")
    response2 = await docs_assistant(query2)
    print(f"Answer: {response2}\n")

    # Example 3: Architecture question (may reference diagrams)
    print("3. Architecture Question")
    print("-" * 50)
    query3 = "What is the system architecture?"
    print(f"Query: {query3}")
    response3 = await docs_assistant(query3)
    print(f"Answer: {response3}\n")

    # Example 4: Advanced feature question
    print("4. Advanced Feature Question")
    print("-" * 50)
    query4 = "Tell me about advanced configuration options"
    print(f"Query: {query4}")
    response4 = await docs_assistant(query4)
    print(f"Answer: {response4}\n")

    # Example 5: Query with no results
    print("5. Missing Information Query")
    print("-" * 50)
    query5 = "How do I deploy to Kubernetes?"
    print(f"Query: {query5}")
    response5 = await docs_assistant(query5)
    print(f"Answer: {response5}\n")

    print("=" * 50)
    print("Example complete!")
    print("\nTip: The RAG index is cached, so subsequent runs will be faster.")
    print("Try modifying sample_docs/ and re-running to see incremental updates.")


if __name__ == "__main__":
    asyncio.run(main())
