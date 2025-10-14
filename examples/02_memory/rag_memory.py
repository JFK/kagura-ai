"""RAG Memory - Semantic search with vector embeddings

This example demonstrates:
- Using MemoryRAG for semantic search
- Vector-based retrieval
- Finding relevant context by meaning
"""

import asyncio
from kagura import agent
from kagura.core.memory import MemoryRAG


# Create RAG memory for semantic search
rag_memory = MemoryRAG(agent_name="knowledge_assistant")


@agent
async def knowledge_assistant(query: str) -> str:
    """
    You are a knowledgeable assistant with semantic memory.

    Context from memory:
    {% for memory in memories %}
    - {{ memory }}
    {% endfor %}

    User query: {{ query }}

    Use the context to answer the query accurately.
    """
    pass


async def store_knowledge():
    """Store some knowledge in RAG memory"""
    facts = [
        "Python was created by Guido van Rossum in 1991",
        "Python is known for its readable syntax and simplicity",
        "Python supports multiple programming paradigms",
        "JavaScript is primarily used for web development",
        "JavaScript runs in browsers and on Node.js servers",
        "Rust is a systems programming language focused on safety",
        "Rust prevents memory errors at compile time",
        "Go was designed by Google for concurrent programming"
    ]

    for fact in facts:
        await rag_memory.store(
            content=fact,
            metadata={"type": "programming_language_fact"}
        )

    print("Stored knowledge in RAG memory")


async def main():
    print("RAG Memory Demo - Semantic search")
    print("-" * 50)

    # Store knowledge first
    await store_knowledge()
    print()

    # Semantic search queries
    queries = [
        "Tell me about Python's history",
        "What language is good for web browsers?",
        "Which language focuses on memory safety?"
    ]

    for query in queries:
        # Retrieve relevant memories
        memories = await rag_memory.recall_semantic(
            query=query,
            k=2,  # Top 2 most relevant
            filter={"type": "programming_language_fact"}
        )

        # Pass to agent
        response = await knowledge_assistant(
            query,
            memories=[m.content for m in memories]
        )

        print(f"Query: {query}")
        print(f"Retrieved {len(memories)} relevant facts")
        print(f"Response: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
