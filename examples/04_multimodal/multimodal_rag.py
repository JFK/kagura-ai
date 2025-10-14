"""Multimodal RAG - Search across text, images, and PDFs

This example demonstrates:
- RAG with multiple content types
- Semantic search across modalities
- Unified knowledge retrieval
"""

import asyncio
from pathlib import Path
from kagura import agent
from kagura.core.memory import MemoryRAG


# Create multimodal RAG
rag = MemoryRAG(agent_name="multimodal_assistant")


@agent
async def multimodal_assistant(query: str, context: list[str]) -> str:
    """
    Answer this query using the provided context:

    Context:
    {% for item in context %}
    - {{ item }}
    {% endfor %}

    Query: {{ query }}

    Provide a comprehensive answer based on all context.
    """
    pass


async def store_multimodal_knowledge():
    """Store knowledge from different sources"""

    # Text knowledge
    text_facts = [
        "Kagura AI is a Python framework for building AI agents",
        "The @agent decorator converts functions into AI agents",
        "Kagura supports memory, routing, and multimodal capabilities"
    ]

    for fact in text_facts:
        await rag.store(
            content=fact,
            metadata={"type": "text", "source": "documentation"}
        )

    # Image descriptions (in real scenario, these would be from vision model)
    image_descriptions = [
        "Architecture diagram showing the flow: User -> Agent -> LLM -> Response",
        "Code example demonstrating the @agent decorator syntax"
    ]

    for desc in image_descriptions:
        await rag.store(
            content=desc,
            metadata={"type": "image", "source": "diagrams"}
        )

    # PDF summaries
    pdf_summaries = [
        "Research paper: 'Agent-Based Programming' discusses design patterns",
        "Tutorial: 'Getting Started with Kagura' covers installation and setup"
    ]

    for summary in pdf_summaries:
        await rag.store(
            content=summary,
            metadata={"type": "pdf", "source": "documents"}
        )

    print("✓ Stored multimodal knowledge")


async def main():
    print("Multimodal RAG Demo")
    print("-" * 50)

    # Store knowledge
    await store_multimodal_knowledge()
    print()

    # Queries that might need different content types
    queries = [
        "How do I create an agent in Kagura?",
        "What does the architecture look like?",
        "Are there any tutorials available?",
        "What are the main features?"
    ]

    for query in queries:
        print(f"\nQuery: {query}")

        # Retrieve relevant content across all modalities
        results = await rag.recall_semantic(query, k=3)

        # Show what was retrieved
        print(f"Retrieved {len(results)} items:")
        for result in results:
            content_type = result.metadata.get("type", "unknown")
            print(f"  [{content_type}] {result.content[:60]}...")

        # Answer using multimodal context
        context = [r.content for r in results]
        answer = await multimodal_assistant(query, context)
        print(f"Answer: {answer}")


if __name__ == "__main__":
    asyncio.run(main())
