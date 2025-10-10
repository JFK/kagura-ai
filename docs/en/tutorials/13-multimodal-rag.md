# Tutorial 13: Multimodal RAG - Search Images, Audio, Videos & PDFs

Learn how to create AI agents that can search and understand multimodal content (images, audio, video, PDFs) from your directories using Retrieval-Augmented Generation (RAG).

## Prerequisites

- Python 3.11 or higher
- Kagura AI installed with multimodal support: `pip install kagura-ai[multimodal]`
- Google API key (for Gemini API)
- ChromaDB installed (included with multimodal extra)

## Goal

By the end of this tutorial, you will:
- Understand what Multimodal RAG is and why it's useful
- Set up a directory for multimodal content indexing
- Create agents that can search across text, images, audio, videos, and PDFs
- Build a documentation assistant that understands diagrams and screenshots

## What is Multimodal RAG?

**RAG (Retrieval-Augmented Generation)** enhances AI agents by giving them access to external knowledge. **Multimodal RAG** extends this to work with:

- **Images** (PNG, JPG, GIF, WEBP)
- **Audio** (MP3, WAV, M4A)
- **Video** (MP4, MOV, AVI)
- **PDFs** (documents with text and images)
- **Text files** (MD, TXT, Python code, etc.)

Instead of just searching text, your agent can:
- Find relevant diagrams and screenshots
- Transcribe and search audio recordings
- Extract information from video content
- Process PDF documentation

## Step 1: Set Up Your Environment

Set your Google API key (required for processing multimodal content):

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

Install Kagura AI with multimodal support:

```bash
pip install kagura-ai[multimodal]
```

This installs:
- `google-generativeai` - For Gemini API (multimodal processing)
- `chromadb` - Vector database for semantic search
- `python-frontmatter` - For markdown with metadata

## Step 2: Prepare Your Content Directory

Create a project directory with mixed content:

```bash
mkdir my_project
cd my_project

# Create some documentation
echo "# Authentication\nOur app uses OAuth 2.0" > auth.md

# Create a docs folder
mkdir docs
echo "User guide content here" > docs/guide.txt

# Add some images (diagrams, screenshots, etc.)
mkdir images
# Add your actual images here
```

Your directory structure:
```
my_project/
├── auth.md           # Text documentation
├── docs/
│   └── guide.txt     # More docs
└── images/
    ├── diagram.png   # Architecture diagram
    └── screenshot.jpg # UI screenshot
```

## Step 3: Create Your First RAG Agent

Create `rag_agent.py`:

```python
import asyncio
from pathlib import Path
from kagura import agent


@agent(
    enable_multimodal_rag=True,
    rag_directory=Path("./my_project")
)
async def docs_assistant(query: str, rag) -> str:
    '''Answer the question: {{ query }}

    Use rag.query(query) to search documentation.
    Include relevant details from the search results.'''
    pass


async def main():
    # First call: Builds index (may take a moment)
    result = await docs_assistant("How does authentication work?")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

**Let's break this down:**

1. `enable_multimodal_rag=True` - Enables RAG functionality
2. `rag_directory=Path("./my_project")` - Directory to index
3. `rag` parameter - Auto-injected MultimodalRAG instance
4. `rag.query(query)` - Search for relevant content

## Step 4: Run Your RAG Agent

Execute the script:

```bash
python rag_agent.py
```

**First run:**
```
Building index from /path/to/my_project
Index built: 5 files (3 text, 2 multimodal)
Our app uses OAuth 2.0 for authentication...
```

**Subsequent runs:** Much faster (uses cached index)

🎉 Your agent can now search across all your documentation!

## How It Works: Behind the Scenes

### Index Building

When you first call the agent:

1. **Directory Scanning**: Recursively scans `my_project/`
2. **File Type Detection**: Identifies text, images, audio, video, PDFs
3. **Content Processing**:
   - **Text files**: Read directly
   - **Images**: Analyzed with Gemini Vision API (describes content)
   - **Audio**: Transcribed to text
   - **Video**: Frames extracted and analyzed
   - **PDFs**: Text and images extracted
4. **Vector Indexing**: Stores in ChromaDB for semantic search
5. **Caching**: Results cached for faster subsequent access

### Query Time

When you search:

1. **Semantic Search**: Finds relevant content using vector similarity
2. **Context Injection**: Results available to the agent
3. **LLM Response**: Agent synthesizes answer using search results

## Step 5: Advanced Usage - Manual Search

You can manually control the search and response:

```python
@agent(
    enable_multimodal_rag=True,
    rag_directory=Path("./my_project")
)
async def smart_assistant(query: str, rag) -> str:
    '''You are a helpful documentation assistant.

    First, search for relevant information using: rag.query("{{ query }}", n_results=3)
    Then answer based on the search results: {{ query }}

    If no relevant results found, say "I couldn't find information about that."'''
    pass
```

**How this works:**
- The prompt tells the LLM to use `rag.query()`
- The LLM calls it during generation (via tool calling)
- Results are incorporated into the response

## Step 6: Building the Index Explicitly

For large directories, build the index ahead of time:

```python
from pathlib import Path
from kagura.core.memory import MultimodalRAG
import asyncio


async def build_index():
    # Initialize RAG
    rag = MultimodalRAG(
        directory=Path("./my_project"),
        collection_name="my_docs"
    )

    # Build index
    stats = await rag.build_index(max_concurrent=3)

    print(f"Indexed {stats['total_files']} files")
    print(f"  - Text: {stats['text_files']}")
    print(f"  - Multimodal: {stats['multimodal_files']}")
    print(f"  - Failed: {stats['failed_files']}")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")


asyncio.run(build_index())
```

**Output:**
```
Building index from ./my_project
Indexed 15 files
  - Text: 10
  - Multimodal: 5
  - Failed: 0
Cache hit rate: 0.00%
```

## Step 7: Search by File Type

Filter results by content type:

```python
from kagura.loaders.file_types import FileType

# Search only images
results = rag.query("architecture diagram", file_type=FileType.IMAGE)

# Search only text
results = rag.query("authentication", file_type=FileType.TEXT)
```

## Step 8: Incremental Updates

Update the index when files change:

```python
# Add new files to my_project/
# Then update incrementally (faster than full rebuild)
stats = await rag.incremental_update()
print(f"Updated {stats['total_files']} new/modified files")
```

## Configuration Options

### RAG Parameters

```python
@agent(
    enable_multimodal_rag=True,
    rag_directory=Path("./docs"),        # Required
    rag_cache_size_mb=100,                # Cache size (default: 100MB)
    persist_dir=Path("./.kagura")         # ChromaDB storage location
)
async def my_agent(query: str, rag) -> str:
    pass
```

### MultimodalRAG Options

```python
from kagura.core.memory import MultimodalRAG

rag = MultimodalRAG(
    directory=Path("./project"),
    collection_name="my_docs",         # ChromaDB collection name
    persist_dir=Path("./.kagura"),     # Storage directory
    cache_size_mb=100,                 # File cache size
    respect_gitignore=True,            # Honor .gitignore/.kaguraignore
)
```

## Step 9: Gitignore Support

Create `.kaguraignore` to exclude files:

```bash
# .kaguraignore
node_modules/
*.log
.env
__pycache__/
```

Files matching these patterns are automatically excluded from indexing.

## Complete Example: Documentation Assistant

Here's a full example with proper error handling:

```python
import asyncio
from pathlib import Path
from kagura import agent
from kagura.core.memory import MultimodalRAG


@agent(
    model="gpt-4o-mini",
    temperature=0.7,
    enable_multimodal_rag=True,
    rag_directory=Path("./my_project")
)
async def docs_bot(query: str, rag: MultimodalRAG) -> str:
    '''You are a documentation assistant.

    Search relevant documentation: rag.query("{{ query }}", n_results=5)
    Answer based on results: {{ query }}

    If you can't find relevant info, say so clearly.'''
    pass


async def main():
    print("Documentation Assistant")
    print("=" * 40)

    # Build index first (optional, but recommended)
    print("Building knowledge base...")

    queries = [
        "How does authentication work?",
        "Show me the architecture diagram",
        "What's in the user guide?",
    ]

    for query in queries:
        print(f"\nQ: {query}")
        result = await docs_bot(query)
        print(f"A: {result}\n")


if __name__ == "__main__":
    asyncio.run(main())
```

## Use Cases

### 1. Technical Documentation

```python
@agent(enable_multimodal_rag=True, rag_directory=Path("./docs"))
async def tech_support(question: str, rag) -> str:
    '''Answer technical questions using docs, diagrams, and screenshots.
    Question: {{ question }}'''
    pass
```

### 2. Meeting Notes Search

```python
@agent(enable_multimodal_rag=True, rag_directory=Path("./meetings"))
async def meeting_search(topic: str, rag) -> str:
    '''Search meeting recordings and notes for: {{ topic }}
    Include timestamps and speakers.'''
    pass
```

### 3. Design System Assistant

```python
@agent(enable_multimodal_rag=True, rag_directory=Path("./design_system"))
async def design_helper(component: str, rag) -> str:
    '''Find design specs and screenshots for: {{ component }}'''
    pass
```

## Performance Tips

### 1. Cache Sizing

```python
# For large projects
rag_cache_size_mb=500  # 500MB cache

# For small projects
rag_cache_size_mb=50   # 50MB cache
```

### 2. Concurrency Control

```python
# Build index with controlled concurrency
await rag.build_index(max_concurrent=5)  # Process 5 files at once
```

### 3. Incremental Updates

```python
# Instead of full rebuild
await rag.build_index(force_rebuild=True)  # Slow

# Use incremental update
await rag.incremental_update()             # Fast
```

## Troubleshooting

### Issue: "Google API key not found"

**Solution:** Set the environment variable:
```bash
export GOOGLE_API_KEY="your-key"
```

### Issue: "ImportError: No module named 'chromadb'"

**Solution:** Install with multimodal support:
```bash
pip install kagura-ai[multimodal]
```

### Issue: Index build is slow

**Solutions:**
1. Reduce concurrency: `max_concurrent=2`
2. Exclude large files with `.kaguraignore`
3. Use smaller cache: `rag_cache_size_mb=50`

### Issue: Out of memory

**Solutions:**
1. Reduce cache size: `rag_cache_size_mb=50`
2. Process in batches with `incremental_update()`
3. Exclude large video files

## Key Concepts Learned

### 1. Multimodal RAG

Search and understand multiple content types:
- Text, images, audio, video, PDFs
- Automatic processing with Gemini API
- Semantic vector search with ChromaDB

### 2. @agent Integration

```python
@agent(enable_multimodal_rag=True, rag_directory=Path("./docs"))
async def my_agent(query: str, rag: MultimodalRAG) -> str:
    pass
```

### 3. Directory Scanning

- Recursive scanning with `.gitignore` support
- Automatic file type detection
- Parallel processing for speed

### 4. Caching & Performance

- File content caching (configurable size)
- Incremental updates (only new/modified files)
- Vector index persistence (no re-indexing on restart)

## Next Steps

Now that you understand Multimodal RAG:

1. **Combine with Memory** - Use `enable_memory=True` for conversational RAG
2. **Add Tools** - Combine RAG with custom tools for enhanced capabilities
3. **Deploy** - Use RAG agents in production applications

## Practice Exercises

### Exercise 1: Image Search Agent

Create an agent that searches only images:

```python
from kagura.loaders.file_types import FileType

@agent(enable_multimodal_rag=True, rag_directory=Path("./images"))
async def image_search(query: str, rag) -> str:
    '''Find images matching: {{ query }}
    Use: rag.query(query, file_type=FileType.IMAGE)'''
    pass
```

### Exercise 2: Code Documentation

Index a codebase and answer questions:

```python
@agent(enable_multimodal_rag=True, rag_directory=Path("./src"))
async def code_qa(question: str, rag) -> str:
    '''Answer questions about the codebase: {{ question }}'''
    pass

# Test
print(await code_qa("How does the authentication module work?"))
```

### Exercise 3: Meeting Minutes Bot

Search meeting recordings and notes:

```python
@agent(enable_multimodal_rag=True, rag_directory=Path("./meetings"))
async def meeting_bot(topic: str, rag) -> str:
    '''Summarize discussions about: {{ topic }}
    Include meeting dates and key decisions.'''
    pass
```

## Summary

You learned:
- ✓ What Multimodal RAG is and its benefits
- ✓ How to set up content directories for indexing
- ✓ How to create RAG-enabled agents with `@agent`
- ✓ How to search across text, images, audio, video, PDFs
- ✓ Performance optimization and troubleshooting

Continue exploring with [Tutorial 14: Advanced Memory Management](14-memory-management.md)!
