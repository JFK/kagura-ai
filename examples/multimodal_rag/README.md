# Multimodal RAG Documentation Assistant Example

This example demonstrates Kagura AI's Multimodal RAG capabilities by creating a documentation assistant that can search across multiple file types.

## What This Example Demonstrates

- **@agent decorator** with `enable_multimodal_rag=True`
- **Directory scanning** and automatic indexing
- **Semantic search** across documentation files
- **RAG query integration** within agent prompts
- **Caching** for faster subsequent runs

## Prerequisites

Install Kagura AI with multimodal support:

```bash
pip install kagura-ai[multimodal]
```

Set your Google API key (required for processing multimodal content):

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

## Directory Structure

```
multimodal_rag/
├── README.md                      # This file
├── docs_assistant.py              # Main example script
└── sample_docs/                   # Sample documentation directory
    ├── README.md                  # Project overview
    ├── api/
    │   └── authentication.md      # API documentation
    ├── guides/
    │   ├── getting-started.md     # Getting started guide
    │   └── advanced.md            # Advanced configuration
    └── diagrams/
        └── architecture.txt       # Architecture diagram (text)
```

## Running the Example

Simply run the Python script:

```bash
python docs_assistant.py
```

**First run**: The script will build an index of all files in `sample_docs/`. This may take a moment as it processes each file and creates embeddings.

**Subsequent runs**: Much faster! The index is cached and reused.

## How It Works

### 1. Agent Definition

```python
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

    Question: {{ query }}
    """
    pass
```

Key parameters:
- `enable_multimodal_rag=True`: Enables RAG functionality
- `rag_directory`: Path to the directory to index
- `rag` parameter: Auto-injected `MultimodalRAG` instance

### 2. Index Building (Automatic)

On first call, the agent automatically:
1. Scans the `sample_docs/` directory recursively
2. Detects file types (text, images, PDFs, etc.)
3. Processes content (extracts text, describes images)
4. Creates semantic embeddings
5. Stores in ChromaDB vector database
6. Caches processed content

### 3. Query Processing

When you call the agent:
1. The LLM sees the prompt with `{{ query }}`
2. The LLM calls `rag.query()` to search documentation
3. Relevant content is retrieved from the vector database
4. The LLM synthesizes an answer using search results

### 4. Caching

The RAG system caches:
- **File content**: Processed content cached in memory (100MB by default)
- **Vector index**: ChromaDB persists to disk (`.kagura/` by default)
- **Embeddings**: No need to re-embed unchanged files

## Example Output

```
=== Multimodal RAG Documentation Assistant ===

Building knowledge base from sample_docs/...
(This may take a moment on first run)

1. Basic Documentation Query
--------------------------------------------------
Query: How do I get started with this project?
Answer: To get started with Sample Project:

1. Install the package: `pip install sample-project`
2. Initialize configuration: `sample-project init`
3. Set up the database: `sample-project db migrate`
4. Start the server: `sample-project serve --reload`

The server will be running at http://localhost:8000. You can then create
an account and start making API requests. See the getting-started guide
for detailed instructions.

2. API-Specific Question
--------------------------------------------------
Query: How does authentication work?
Answer: Sample Project supports two authentication methods:

1. **OAuth 2.0**: For user-facing applications with authorization code flow
2. **API Keys**: For server-to-server communication

For OAuth, you redirect users to `/oauth/authorize`, exchange the code for
a token at `/oauth/token`, and include the access token in the Authorization
header for API requests.

For API keys, you generate a key via POST `/api/v1/api-keys` and include it
in the `X-API-Key` header.

All requests are rate-limited (1000/hour for OAuth, 5000/hour for API keys).
...
```

## Customization

### Change the Document Directory

Edit `docs_assistant.py`:

```python
@agent(
    enable_multimodal_rag=True,
    rag_directory=Path("/path/to/your/docs"),  # Change this
)
```

### Adjust Cache Size

```python
@agent(
    enable_multimodal_rag=True,
    rag_directory=Path("./sample_docs"),
    rag_cache_size_mb=200,  # Increase cache to 200MB
)
```

### Change Number of Results

Modify the prompt to request more results:

```python
async def docs_assistant(query: str, rag) -> str:
    """Search with: rag.query("{{ query }}", n_results=5)  # More results

    Question: {{ query }}
    """
```

### Use Different LLM

```python
@agent(
    model="gpt-4o",  # More powerful model
    enable_multimodal_rag=True,
    rag_directory=Path("./sample_docs"),
)
```

## Adding Your Own Documents

1. **Copy your documents** into `sample_docs/` (or create a new directory)
2. **Supported formats**:
   - Text: `.md`, `.txt`, `.rst`, `.py`, `.js`, `.java`, etc.
   - Images: `.png`, `.jpg`, `.gif`, `.webp` (described by Gemini Vision)
   - PDFs: `.pdf` (text and images extracted)
   - Audio: `.mp3`, `.wav`, `.m4a` (transcribed)
   - Video: `.mp4`, `.mov`, `.avi` (frames analyzed)

3. **Run the script**: Index is rebuilt automatically

## Ignoring Files

Create `.kaguraignore` in the document directory:

```
# .kaguraignore
node_modules/
*.log
.env
__pycache__/
*.pyc
.git/
```

Files matching these patterns won't be indexed.

## Troubleshooting

### "Google API key not found"

Set the environment variable:

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

Get a key at: https://makersuite.google.com/app/apikey

### "ImportError: No module named 'chromadb'"

Install multimodal dependencies:

```bash
pip install kagura-ai[multimodal]
```

### Index build is slow

1. Reduce cache size: `rag_cache_size_mb=50`
2. Exclude large files with `.kaguraignore`
3. Use `max_concurrent=2` in `rag.build_index()`

### Out of memory

1. Reduce cache: `rag_cache_size_mb=50`
2. Process in batches
3. Exclude large video files

## Next Steps

Now that you understand Multimodal RAG:

1. **Try with your own docs**: Replace `sample_docs/` with your documentation
2. **Combine with memory**: Use `enable_memory=True` for conversational RAG
3. **Add tools**: Give your agent additional capabilities beyond search
4. **Deploy**: Use RAG agents in production applications

## Learn More

- [Tutorial 13: Multimodal RAG](../../docs/en/tutorials/13-multimodal-rag.md)
- [MultimodalRAG API Reference](../../docs/en/api/multimodal-rag.md)
- [Kagura AI Documentation](https://docs.kagura-ai.com)

## License

This example is part of Kagura AI and is licensed under the MIT License.
