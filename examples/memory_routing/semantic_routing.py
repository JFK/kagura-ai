"""Semantic Routing with RAG Example

This example demonstrates semantic routing with RAG-enabled memory
for enhanced context understanding through vector similarity search.
"""

import asyncio
from kagura import agent
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager


# Define specialized agents
@agent(model="gpt-4o-mini")
async def python_expert(question: str) -> str:
    """Answer Python programming question: {{ question }}"""
    pass


@agent(model="gpt-4o-mini")
async def javascript_expert(question: str) -> str:
    """Answer JavaScript programming question: {{ question }}"""
    pass


@agent(model="gpt-4o-mini")
async def devops_expert(question: str) -> str:
    """Answer DevOps question: {{ question }}"""
    pass


@agent(model="gpt-4o-mini")
async def database_expert(question: str) -> str:
    """Answer database question: {{ question }}"""
    pass


async def main():
    """Demonstrate semantic routing with RAG."""
    print("=== Semantic Routing with RAG ===\n")

    # Initialize memory with RAG enabled
    memory = MemoryManager(
        agent_name="semantic_router",
        enable_rag=True  # Enable vector-based semantic search
    )

    router = MemoryAwareRouter(memory=memory, context_window=10)

    # Register specialized agents
    router.register(python_expert, intents=["python", "py"])
    router.register(javascript_expert, intents=["javascript", "js"])
    router.register(devops_expert, intents=["devops", "docker", "kubernetes"])
    router.register(database_expert, intents=["database", "sql"])

    # Example 1: Build knowledge base
    print("1. Building Knowledge Base")
    print("-" * 50)

    knowledge = [
        "Python is great for data science and machine learning",
        "JavaScript is the language of the web",
        "Docker containers simplify deployment",
        "PostgreSQL is a powerful relational database",
    ]

    print("Storing knowledge in RAG memory...")
    for fact in knowledge:
        memory.rag.store(fact)

    print(f"✓ Stored {len(knowledge)} facts in vector database\n")

    # Example 2: Semantic query matching
    print("2. Semantic Query Matching")
    print("-" * 50)

    query = "What's good for machine learning?"
    result = await router.route(query)

    print(f"Query: {query}")
    print(f"Semantic match: Python (via RAG)")
    print(f"Routed to: python_expert")
    print(f"Result: {result}\n")

    # Example 3: Semantic similarity routing
    print("3. Semantic Similarity Routing")
    print("-" * 50)

    queries = [
        ("Tell me about containerization", "Semantically similar to Docker"),
        ("What should I use for web development?", "Semantically similar to JavaScript"),
        ("Best database for analytics", "Semantically similar to PostgreSQL"),
    ]

    for query, explanation in queries:
        result = await router.route(query)
        print(f"Query: {query}")
        print(f"  {explanation}")
        print(f"Result: {result}\n")

    # Example 4: Semantic search in conversation history
    print("4. Semantic Search in History")
    print("-" * 50)

    # Have some conversations
    await router.route("How do I use list comprehensions in Python?")
    await router.route("What are JavaScript promises?")
    await router.route("How do I set up a Docker container?")

    print("Had 3 conversations about different topics")

    # Semantic search for relevant past conversation
    if memory.rag:
        results = memory.rag.recall("Tell me about async programming", top_k=2)
        print(f"\nSemantic search for 'async programming':")
        print(f"Found {len(results)} relevant past conversations:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['content'][:60]}...")
            print(f"     Similarity: {1 - result['distance']/2:.1%}")

    print()

    # Example 5: Context enhancement with RAG
    print("5. Context Enhancement with RAG")
    print("-" * 50)

    # Store domain knowledge
    memory.rag.store("Python has async/await for asynchronous programming")
    memory.rag.store("JavaScript uses async/await syntax similar to Python")

    # Query that benefits from RAG context
    result = await router.route("Compare async patterns")
    print(f"Query: Compare async patterns")
    print(f"RAG retrieves: Relevant async knowledge from both languages")
    print(f"Enhanced context helps router choose appropriate agent")
    print(f"Result: {result}\n")

    # Example 6: Multi-language context
    print("6. Multi-Language Context Understanding")
    print("-" * 50)

    # Store Python-specific knowledge
    memory.rag.store("Python decorators are powerful for metaprogramming")
    memory.rag.store("Python type hints improve code quality")

    # Store JavaScript-specific knowledge
    memory.rag.store("JavaScript closures enable data privacy")
    memory.rag.store("JavaScript prototypal inheritance is unique")

    # Queries that leverage semantic understanding
    queries = [
        "Tell me about metaprogramming features",
        "How can I ensure data privacy?",
        "What about type checking?",
    ]

    for query in queries:
        result = await router.route(query)
        print(f"Query: {query}")
        print(f"Result: {result}\n")

    # Example 7: Semantic disambiguation
    print("7. Semantic Disambiguation")
    print("-" * 50)

    # Ambiguous term that appears in multiple contexts
    memory.rag.store("Python lists are dynamic arrays")
    memory.rag.store("SQL lists tables in a database")

    query = "How do I work with lists?"
    print(f"Query: {query}")
    print(f"Ambiguous: 'lists' could mean Python lists or SQL tables")

    result = await router.route(query)
    print(f"RAG helps router decide based on semantic context")
    print(f"Result: {result}\n")

    # Example 8: Topic clustering
    print("8. Topic Clustering with RAG")
    print("-" * 50)

    # Store multiple related facts
    python_facts = [
        "NumPy is essential for numerical computing in Python",
        "Pandas simplifies data manipulation in Python",
        "Matplotlib creates visualizations in Python",
    ]

    for fact in python_facts:
        memory.rag.store(fact)

    query = "What tools are good for data analysis?"
    print(f"Query: {query}")
    print(f"RAG retrieves cluster of related Python data science tools")

    result = await router.route(query)
    print(f"Result: {result}\n")

    # Example 9: Cross-domain semantic linking
    print("9. Cross-Domain Semantic Linking")
    print("-" * 50)

    # Store facts that link domains
    memory.rag.store("Python scripts can be containerized with Docker")
    memory.rag.store("PostgreSQL pairs well with Python for data apps")

    query = "How do I deploy a data application?"
    print(f"Query: {query}")
    print(f"Requires knowledge spanning: Python, DevOps, Database")

    result = await router.route(query)
    print(f"RAG helps understand cross-domain relationships")
    print(f"Result: {result}\n")

    # Example 10: Semantic memory inspection
    print("10. Inspecting Semantic Memory")
    print("-" * 50)

    if memory.rag:
        total_memories = memory.rag.count()
        print(f"Total semantic memories: {total_memories}")

        # Search for specific topic
        search_results = memory.rag.recall("Docker deployment", top_k=3)
        print(f"\nTop 3 memories related to 'Docker deployment':")
        for i, result in enumerate(search_results, 1):
            print(f"  {i}. {result['content']}")
            print(f"     Distance: {result['distance']:.3f}")

    print()


async def advanced_rag_patterns():
    """Demonstrate advanced RAG patterns."""
    print("\n" + "=" * 60)
    print("=== Advanced RAG Patterns ===\n")

    memory = MemoryManager(agent_name="advanced_rag", enable_rag=True)
    router = MemoryAwareRouter(memory=memory)

    # Register agents
    router.register(python_expert, intents=["python"])
    router.register(devops_expert, intents=["devops"])

    # Pattern 1: Temporal context with RAG
    print("1. Temporal Context with RAG")
    print("-" * 50)

    # Store time-sensitive information
    memory.rag.store(
        "Python 3.12 introduced improved error messages",
        metadata={"version": "3.12", "year": 2023}
    )

    query = "What's new in recent Python versions?"
    result = await router.route(query)
    print(f"Query: {query}")
    print(f"RAG retrieves version-specific information")
    print(f"Result: {result}\n")

    # Pattern 2: Hierarchical knowledge
    print("2. Hierarchical Knowledge Organization")
    print("-" * 50)

    # Store hierarchical knowledge
    hierarchy = [
        "Programming languages include Python, JavaScript, Java",
        "Python is good for data science, web development, automation",
        "Data science with Python uses NumPy, Pandas, Scikit-learn",
    ]

    for knowledge in hierarchy:
        memory.rag.store(knowledge)

    query = "What should I learn for data science?"
    result = await router.route(query)
    print(f"Query: {query}")
    print(f"RAG traverses knowledge hierarchy")
    print(f"Result: {result}\n")

    # Pattern 3: RAG-enhanced agent selection
    print("3. RAG-Enhanced Agent Selection")
    print("-" * 50)

    # Store agent capabilities
    memory.rag.store("Python expert knows about ML, data science, web")
    memory.rag.store("DevOps expert knows about Docker, Kubernetes, CI/CD")

    query = "Help me set up continuous integration"
    print(f"Query: {query}")
    print(f"RAG helps router select most appropriate expert")

    result = await router.route(query)
    print(f"Result: {result}\n")

    # Pattern 4: Memory cleanup
    print("4. Semantic Memory Management")
    print("-" * 50)

    print(f"Memories before cleanup: {memory.rag.count()}")

    # Demonstrate cleanup (be careful in production!)
    # memory.rag.delete_all()  # Uncomment to clear all

    print(f"You can clear semantic memory with: memory.rag.delete_all()")
    print(f"Or delete specific agent memories: memory.rag.delete_all(agent_name='...')\n")


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())

    # Run advanced patterns
    asyncio.run(advanced_rag_patterns())

    print("=" * 60)
    print("Semantic routing with RAG demo complete! 🎉")
    print("\nNote: RAG requires ChromaDB: pip install chromadb")
