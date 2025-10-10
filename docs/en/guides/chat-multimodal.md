# Multimodal RAG Chat Guide

This guide explains how to use Kagura AI's multimodal RAG (Retrieval-Augmented Generation) feature with the `kagura chat` command.

## Overview

Multimodal RAG allows you to:
- Index and search across multiple file types (text, images, PDFs, audio, video)
- Chat with your entire project directory
- Get AI responses grounded in your local files
- Automatically process and understand visual content, documents, and more

## Prerequisites

### Installation

Install Kagura AI with multimodal support:

```bash
pip install kagura-ai[multimodal]
```

This installs:
- `google-generativeai` - Gemini API for multimodal processing
- `chromadb` - Vector database for semantic search
- `pillow` - Image processing

### API Key Setup

Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey) and set it:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file in your project:

```bash
GEMINI_API_KEY=your-api-key-here
```

## Quick Start

### Basic Usage

Start multimodal chat with a directory:

```bash
kagura chat --enable-multimodal --dir ./my-project
```

This will:
1. Scan `./my-project` recursively
2. Process all supported files using Gemini
3. Build a vector index with ChromaDB
4. Start an interactive chat session

### Example Session

```bash
$ kagura chat --enable-multimodal --dir ./docs

Initializing multimodal RAG for: ./docs
✓ Indexed 42 files from ./docs

Type your message to chat with AI, or use commands:
  /help      - Show help
  /exit      - Exit chat

[You] > What's in the architecture diagram?

Searching indexed files...
💬 Generating response...

[AI]
The architecture diagram (architecture.png) shows a 3-tier system:

1. **Frontend Layer**: React application with TypeScript
2. **API Layer**: FastAPI backend with REST endpoints
3. **Data Layer**: PostgreSQL database with SQLAlchemy ORM

The frontend communicates with the API via HTTP requests, and the API
connects to the database using connection pooling for performance.

[You] > Can you show me the authentication flow?

[AI]
Based on the auth.py file and the sequence diagram, the authentication
flow works as follows:

1. User submits credentials to /api/auth/login
2. Backend validates credentials against database
3. JWT token is generated with user claims
4. Token is returned to client
5. Client includes token in Authorization header for subsequent requests
6. Backend validates token on each request using middleware

The implementation uses bcrypt for password hashing and PyJWT for token
management. Token expiry is set to 24 hours by default.
```

## Supported File Types

Kagura AI processes different file types using appropriate methods:

### Text Files (Direct Indexing)
- **Markdown**: `.md`, `.markdown`
- **Code**: `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, etc.
- **Documentation**: `.txt`, `.rst`, `.adoc`
- **Data**: `.json`, `.yaml`, `.toml`, `.xml`, `.csv`

Text files are read directly and indexed without API calls.

### Images (Gemini Vision)
- **Formats**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`
- **Use Cases**: Diagrams, screenshots, charts, mockups

Gemini analyzes images and generates descriptive text for indexing.

### PDFs (Gemini Analysis)
- **Format**: `.pdf`
- **Use Cases**: Documentation, reports, papers

Gemini extracts and analyzes PDF content, including text and images.

### Audio (Gemini Transcription)
- **Formats**: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`
- **Use Cases**: Meeting recordings, interviews, voice notes

Gemini transcribes audio to text for searchability.

### Video (Gemini Analysis)
- **Formats**: `.mp4`, `.mov`, `.avi`, `.webm`
- **Use Cases**: Tutorials, presentations, demos

Gemini analyzes video frames and audio to generate descriptions.

## Advanced Usage

### Programmatic API

Use multimodal RAG in your Python code:

```python
from pathlib import Path
from kagura import agent
from kagura.core.memory import MultimodalRAG

# Initialize RAG
rag = MultimodalRAG(
    directory=Path("./project"),
    collection_name="my_project",
    persist_dir=Path("./.kagura/rag")
)

# Build index (async)
import asyncio
stats = asyncio.run(rag.build_index())
print(f"Indexed {stats['total_files']} files")

# Query the index
results = rag.query("authentication implementation", n_results=3)
for result in results:
    print(f"Found in: {result['metadata']['file_path']}")
    print(f"Content: {result['content'][:200]}...")
```

### Agent Integration

Create an agent with multimodal RAG:

```python
from kagura import agent
from kagura.core.memory import MultimodalRAG
from pathlib import Path

@agent(
    model="gemini/gemini-1.5-flash",
    enable_multimodal_rag=True,
    rag_directory=Path("./docs")
)
async def docs_assistant(query: str, rag: MultimodalRAG) -> str:
    """Answer questions about the documentation.

    Query: {{ query }}

    Use rag.query() to search relevant documentation.
    """
    # The agent automatically has access to the RAG instance
    # and can search through all indexed content
    pass

# Use the agent
response = await docs_assistant("How do I configure authentication?")
print(response)
```

### Incremental Updates

Update the index when files change:

```python
# Initial build
await rag.build_index()

# Later, after files are modified
stats = await rag.incremental_update()
print(f"Updated {stats['total_files']} new/modified files")
```

### File Type Filtering

Search only specific file types:

```python
from kagura.loaders.file_types import FileType

# Search only images
image_results = rag.query("architecture diagram", file_type=FileType.IMAGE)

# Search only PDFs
pdf_results = rag.query("API documentation", file_type=FileType.PDF)
```

## Configuration

### Directory Scanning

Control which files are indexed:

#### .gitignore Support

Kagura respects `.gitignore` files by default:

```python
rag = MultimodalRAG(
    directory=Path("./project"),
    respect_gitignore=True  # Default: True
)
```

#### .kaguraignore

Create a `.kaguraignore` file for additional exclusions:

```
# .kaguraignore
*.log
*.tmp
node_modules/
.venv/
__pycache__/
```

### Caching

Enable caching to speed up repeated indexing:

```python
rag = MultimodalRAG(
    directory=Path("./project"),
    enable_cache=True,      # Default: True
    cache_size_mb=100       # Cache limit in MB
)
```

### Model Selection

Choose the Gemini model for multimodal processing:

```python
from kagura.loaders.gemini import GeminiLoader

# Use Gemini 1.5 Flash (faster, cheaper)
loader = GeminiLoader(model="gemini-1.5-flash")

# Use Gemini 1.5 Pro (more accurate)
loader = GeminiLoader(model="gemini-1.5-pro")
```

In chat mode:

```bash
# Uses gemini-1.5-flash by default
kagura chat --enable-multimodal --dir ./project

# Specify model via environment variable
export GEMINI_MODEL="gemini-1.5-pro"
kagura chat --enable-multimodal --dir ./project
```

## Best Practices

### 1. Start Small

Test with a small directory first to verify setup:

```bash
kagura chat --enable-multimodal --dir ./docs/getting-started
```

### 2. Organize Your Files

Structure your project for better RAG results:

```
project/
├── docs/           # Documentation
├── src/            # Source code
├── tests/          # Tests
├── diagrams/       # Architecture diagrams
└── specs/          # Specifications (PDFs)
```

### 3. Use Descriptive Filenames

Good filenames improve search relevance:

```
✅ auth-flow-diagram.png
✅ api-documentation.pdf
✅ user-authentication.py

❌ diagram1.png
❌ doc.pdf
❌ utils.py
```

### 4. Keep Files Updated

Run incremental updates regularly:

```python
# In a background task or cron job
await rag.incremental_update()
```

### 5. Monitor API Usage

Gemini API has rate limits and costs. Monitor usage:

```python
stats = await rag.build_index()
print(f"Multimodal files processed: {stats['multimodal_files']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
```

## Troubleshooting

### "ImportError: google-generativeai not installed"

Install multimodal dependencies:

```bash
pip install kagura-ai[multimodal]
```

### "Authentication error: Invalid API key"

Check your API key:

```bash
echo $GEMINI_API_KEY
```

Get a new key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### "Rate limit exceeded"

Gemini API has rate limits. Reduce `max_concurrent`:

```python
await rag.build_index(max_concurrent=1)  # Process 1 file at a time
```

Or enable caching to reduce API calls:

```python
rag = MultimodalRAG(directory=path, enable_cache=True)
```

### No Results Found

Check if files were indexed:

```python
indexed_files = rag.get_indexed_files()
print(f"Indexed {len(indexed_files)} files")
for file in indexed_files[:10]:
    print(f"  - {file}")
```

Try rebuilding the index:

```python
await rag.build_index(force_rebuild=True)
```

## Performance Tips

### 1. Use Gemini 1.5 Flash

Flash model is 3x faster and cheaper than Pro:

```python
loader = GeminiLoader(model="gemini-1.5-flash")
```

### 2. Enable Caching

Cache processed files to avoid re-processing:

```python
rag = MultimodalRAG(
    directory=path,
    enable_cache=True,
    cache_size_mb=500  # Increase for large projects
)
```

### 3. Parallel Processing

Increase concurrency for faster indexing:

```python
await rag.build_index(max_concurrent=5)  # Default: 3
```

### 4. Incremental Updates

Use incremental updates instead of full rebuilds:

```python
# Only processes new/modified files
await rag.incremental_update()
```

## Examples

### Example 1: Documentation Assistant

```python
from kagura import agent
from kagura.core.memory import MultimodalRAG
from pathlib import Path

@agent(
    model="gemini/gemini-1.5-flash",
    enable_multimodal_rag=True,
    rag_directory=Path("./docs")
)
async def docs_bot(question: str, rag: MultimodalRAG) -> str:
    """Answer questions about project documentation.

    User question: {{ question }}
    """
    pass

# Usage
answer = await docs_bot("How do I deploy to production?")
```

### Example 2: Code Review with Diagrams

```python
@agent(
    model="gemini/gemini-1.5-flash",
    enable_multimodal_rag=True,
    rag_directory=Path("./project")
)
async def code_reviewer(file_path: str, rag: MultimodalRAG) -> str:
    """Review code file and check against architecture diagrams.

    File to review: {{ file_path }}

    Search for:
    1. Related architecture diagrams
    2. Design documentation
    3. Similar code patterns
    """
    pass
```

### Example 3: Meeting Notes Search

```python
# Index meeting recordings
rag = MultimodalRAG(
    directory=Path("./meetings"),
    collection_name="meeting_notes"
)
await rag.build_index()

# Search across all meetings
results = rag.query("Q4 roadmap discussion", n_results=5)
for result in results:
    print(f"Meeting: {result['metadata']['file_path']}")
    print(f"Relevant part: {result['content'][:300]}...")
    print()
```

## Next Steps

- [Web Integration Guide](./web-integration.md) - Add web search to your chat
- [Full-Featured Mode](./full-featured-mode.md) - Combine multimodal RAG and web search
- [API Reference](../api/multimodal-rag.md) - Detailed API documentation

## Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Kagura AI Examples](../../examples/)
