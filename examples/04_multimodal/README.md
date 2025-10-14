# 04_multimodal - Multimodal RAG

This directory contains examples demonstrating multimodal document processing and retrieval.

## Overview

Kagura AI's MultimodalRAG system enables:
- **Image Analysis** - Vision model integration (GPT-4 Vision, Gemini Vision)
- **PDF Processing** - Extract text and images from PDFs
- **Multimodal RAG** - Index and search across text, images, and documents
- **Document Q&A** - Answer questions about complex documents

## Supported Formats

```
┌─────────────────┐
│  Input Sources  │
├─────────────────┤
│ • Images (.png, │
│   .jpg, .webp)  │
│ • PDFs (.pdf)   │
│ • Text (.txt,   │
│   .md, .json)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MultimodalRAG   │
│ - Extract       │
│ - Embed         │
│ - Index         │
│ - Search        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Query Response  │
└─────────────────┘
```

## Examples

### 1. image_analysis.py - Vision Model Integration
**Demonstrates:**
- Using vision-capable models
- Image description and analysis
- Multi-image comparison
- Visual question answering

```python
from pathlib import Path
from kagura import agent, LLMConfig

# Use vision-capable model
vision_config = LLMConfig(
    model="gpt-4-vision-preview",  # or "gemini-pro-vision"
    temperature=0.7
)

@agent(config=vision_config)
async def image_analyzer(image_path: str, question: str) -> str:
    """
    Analyze the image at {{ image_path }} and answer: {{ question }}

    Provide detailed observations.
    """
    pass

# Analyze image
result = await image_analyzer(
    "screenshot.png",
    "What UI elements are visible?"
)
```

**Key Concepts:**
- Vision-capable models (GPT-4V, Gemini Vision)
- Image input handling
- Visual reasoning
- Best for: UI analysis, diagram understanding

**Use Cases:**
- Screenshot analysis
- Diagram interpretation
- UI/UX review
- Visual content moderation
- Chart/graph analysis

**Supported Models:**
- `gpt-4-vision-preview` (OpenAI)
- `gpt-4o` (OpenAI, multimodal)
- `gemini-pro-vision` (Google)
- `claude-3-opus` (Anthropic, vision)

---

### 2. pdf_processing.py - PDF Analysis
**Demonstrates:**
- Extracting text from PDFs
- Processing multi-page documents
- Handling embedded images
- Structured data extraction

```python
from pathlib import Path
from kagura import agent
from kagura.loaders import PDFLoader

@agent
async def pdf_analyzer(pdf_path: str, query: str) -> str:
    """
    Analyze PDF at {{ pdf_path }} and answer: {{ query }}

    Extract relevant information from the document.
    """
    pass

# Load and analyze PDF
loader = PDFLoader(Path("document.pdf"))
pages = loader.load()

result = await pdf_analyzer(
    "research_paper.pdf",
    "What are the main findings?"
)
```

**Key Concepts:**
- PDF text extraction
- Page-by-page processing
- Image extraction from PDFs
- Best for: Document analysis

**Use Cases:**
- Research paper analysis
- Contract review
- Report summarization
- Invoice processing
- Academic paper Q&A

**Supported Features:**
- Text extraction (all pages)
- Image extraction (embedded)
- Table detection
- Multi-page context

---

### 3. multimodal_rag.py - Multimodal Search
**Demonstrates:**
- MultimodalRAG setup and indexing
- Semantic search across multiple formats
- Document embedding
- Relevance-based retrieval

```python
from pathlib import Path
from kagura import agent
from kagura.core.memory import MultimodalRAG

# Initialize RAG with document directory
rag = MultimodalRAG(
    directory=Path("./docs"),
    collection_name="knowledge_base",
    cache_size_mb=100
)

@agent(enable_multimodal_rag=True, rag_directory=Path("./docs"))
async def docs_assistant(query: str, rag: MultimodalRAG) -> str:
    """
    Answer {{ query }} using the documentation.

    Use rag.query() to search relevant content.
    """
    # Search semantically
    results = await rag.recall_semantic(query, k=5)

    # Format context
    context = "\n".join([r["content"] for r in results])

    return f"Based on docs:\n{context}"

# Query documents
answer = await docs_assistant("How do I configure the agent?")
```

**Key Concepts:**
- Directory-based indexing
- Multi-format support (text, images, PDFs)
- Vector embeddings
- Semantic search
- Best for: Knowledge retrieval

**Use Cases:**
- Documentation Q&A
- Code repository search
- Research knowledge base
- Technical support
- Internal wikis

**Indexing Process:**
1. Scan directory recursively
2. Extract content (text/images/PDFs)
3. Generate embeddings
4. Store in ChromaDB
5. Enable semantic search

---

## Prerequisites

```bash
# Install Kagura AI with multimodal support
pip install kagura-ai[multimodal]

# This includes:
# - chromadb (vector database)
# - pypdf (PDF processing)
# - pillow (image processing)
# - sentence-transformers (embeddings)

# Or install individually
pip install chromadb pypdf pillow sentence-transformers
```

## Running Examples

```bash
# Run any example
python image_analysis.py
python pdf_processing.py
python multimodal_rag.py
```

## Supported File Types

| Type | Extensions | Processing | Use Cases |
|------|-----------|------------|-----------|
| **Images** | .png, .jpg, .jpeg, .webp, .gif | Vision models | Screenshots, diagrams, charts |
| **PDFs** | .pdf | Text + image extraction | Papers, reports, contracts |
| **Text** | .txt, .md, .json | Direct indexing | Documentation, code, configs |
| **Code** | .py, .js, .ts, .java | Syntax-aware | Code search, review |

## Common Patterns

### Pattern 1: Simple Image Analysis
```python
from kagura import agent, LLMConfig

config = LLMConfig(model="gpt-4-vision-preview")

@agent(config=config)
async def analyze_image(image_path: str) -> str:
    """Describe the image at {{ image_path }} in detail."""
    pass

# Analyze
description = await analyze_image("photo.jpg")
print(description)
```

### Pattern 2: PDF Q&A System
```python
from pathlib import Path
from kagura import agent
from kagura.loaders import PDFLoader

# Load PDF
loader = PDFLoader(Path("document.pdf"))
pdf_content = loader.load_as_text()

@agent
async def pdf_qa(question: str) -> str:
    """
    Document content:
    {{ pdf_content }}

    Question: {{ question }}

    Answer based on the document above.
    """
    pass

# Ask questions
answer = await pdf_qa("What is the conclusion?")
```

### Pattern 3: Multimodal Document Search
```python
from pathlib import Path
from kagura.core.memory import MultimodalRAG

# Index directory
rag = MultimodalRAG(
    directory=Path("./knowledge_base"),
    collection_name="docs"
)

# Search across all document types
results = await rag.recall_semantic(
    "authentication flow",
    k=10,
    filter={"type": "technical"}  # Optional filtering
)

for result in results:
    print(f"{result['file']}: {result['content'][:100]}...")
```

### Pattern 4: Vision-Enhanced Agent
```python
from kagura import agent, LLMConfig

vision_config = LLMConfig(model="gpt-4o")  # Multimodal model

@agent(config=vision_config)
async def ui_reviewer(screenshot_path: str) -> dict:
    """
    Review the UI screenshot at {{ screenshot_path }}.

    Analyze:
    - Layout and spacing
    - Color scheme
    - Typography
    - Accessibility
    - User experience

    Return structured feedback.
    """
    pass

# Get UI feedback
feedback = await ui_reviewer("app_screenshot.png")
```

## Best Practices

### 1. Choose the Right Vision Model

✅ **For detailed analysis:**
```python
config = LLMConfig(
    model="gpt-4-vision-preview",  # Best quality
    max_tokens=4096
)
```

✅ **For cost-effective processing:**
```python
config = LLMConfig(
    model="gemini-pro-vision",  # Good balance
    max_tokens=2048
)
```

### 2. Optimize PDF Processing

```python
# ✅ Good: Process page by page for large PDFs
loader = PDFLoader(Path("large.pdf"))
for page_num, page_content in enumerate(loader.load_pages()):
    result = await process_page(page_content)

# ❌ Bad: Load entire PDF into memory
full_text = loader.load_as_text()  # May be huge!
```

### 3. Configure RAG Cache Appropriately

```python
# ✅ Good: Reasonable cache size
rag = MultimodalRAG(
    directory=Path("./docs"),
    cache_size_mb=100  # 100MB cache
)

# ❌ Bad: Too small cache (frequent reloads)
rag = MultimodalRAG(
    directory=Path("./docs"),
    cache_size_mb=10  # Too small for many docs
)
```

### 4. Use Filters for Targeted Search

```python
# ✅ Good: Filter by document type
results = await rag.recall_semantic(
    "API endpoint",
    k=5,
    filter={"type": "api_docs", "version": "v2"}
)

# ❌ Bad: Search everything (noisy results)
results = await rag.recall_semantic("API endpoint", k=5)
```

### 5. Handle Large Documents Efficiently

```python
# ✅ Good: Chunk large documents
from kagura.loaders import TextSplitter

splitter = TextSplitter(chunk_size=1000, overlap=200)
chunks = splitter.split(large_text)

for chunk in chunks:
    await rag.store(chunk, metadata={"source": "doc.pdf"})

# ❌ Bad: Store entire document as one item
await rag.store(entire_document)  # May exceed embedding limits
```

## Advanced Features

### Multi-Image Comparison
```python
@agent(config=vision_config)
async def compare_images(image1: str, image2: str) -> str:
    """
    Compare these two images:
    - Image 1: {{ image1 }}
    - Image 2: {{ image2 }}

    Identify similarities and differences.
    """
    pass

result = await compare_images("before.png", "after.png")
```

### Document Summarization
```python
from kagura import agent
from kagura.loaders import PDFLoader

@agent
async def summarize_pdf(pdf_path: str) -> dict:
    """
    Summarize the PDF at {{ pdf_path }}.

    Extract:
    - Title and authors
    - Main points (3-5 bullets)
    - Key findings
    - Conclusion
    """
    pass

summary = await summarize_pdf("research_paper.pdf")
```

### Hybrid Search (Text + Semantic)
```python
from kagura.core.memory import MultimodalRAG

rag = MultimodalRAG(directory=Path("./docs"))

# Combine keyword and semantic search
results = await rag.hybrid_search(
    query="machine learning",
    k=10,
    keyword_weight=0.3,  # 30% keyword, 70% semantic
    semantic_weight=0.7
)
```

### Image OCR Integration
```python
from PIL import Image
import pytesseract

@agent
async def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using OCR."""
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

# Extract text
text = await extract_text_from_image("scanned_doc.png")
```

## Performance Optimization

### 1. Embedding Model Selection
```python
# Fast embeddings (lower quality)
rag = MultimodalRAG(
    directory=Path("./docs"),
    embedding_model="all-MiniLM-L6-v2"  # Small, fast
)

# High-quality embeddings (slower)
rag = MultimodalRAG(
    directory=Path("./docs"),
    embedding_model="all-mpnet-base-v2"  # Larger, better
)
```

### 2. Batch Processing
```python
import asyncio

# Process multiple PDFs in parallel
pdf_paths = [Path(f"doc{i}.pdf") for i in range(10)]

async def process_pdfs(paths):
    tasks = [analyze_pdf(path) for path in paths]
    results = await asyncio.gather(*tasks)
    return results

results = await process_pdfs(pdf_paths)
```

### 3. Incremental Indexing
```python
# Only index new/modified files
rag = MultimodalRAG(directory=Path("./docs"))

# Check if file is already indexed
if not rag.is_indexed("new_doc.pdf"):
    await rag.index_file("new_doc.pdf")
```

## Troubleshooting

### Issue: Vision model not working
**Solution:** Use a vision-capable model:
```python
# ✅ Correct
config = LLMConfig(model="gpt-4-vision-preview")

# ❌ Wrong (no vision support)
config = LLMConfig(model="gpt-3.5-turbo")
```

### Issue: PDF extraction fails
**Solution:** Install PDF dependencies:
```bash
pip install pypdf pillow
# Or
pip install kagura-ai[multimodal]
```

### Issue: ChromaDB errors
**Solution:** Ensure ChromaDB is installed and directory is writable:
```bash
pip install chromadb
```

```python
# Ensure persist_dir is writable
rag = MultimodalRAG(
    directory=Path("./docs"),
    persist_dir=Path("./chromadb_data")  # Must be writable
)
```

### Issue: Out of memory with large PDFs
**Solution:** Process page by page:
```python
# Instead of loading all pages
loader = PDFLoader(Path("large.pdf"))
for page in loader.load_pages():
    await process_page(page)
```

### Issue: Poor search results
**Solution:** Adjust chunk size and overlap:
```python
from kagura.loaders import TextSplitter

splitter = TextSplitter(
    chunk_size=500,   # Smaller chunks
    overlap=100       # More context overlap
)
```

## Next Steps

After mastering multimodal features, explore:
- [05_web](../05_web/) - Web scraping and search
- [06_advanced](../06_advanced/) - Advanced patterns
- [08_real_world](../08_real_world/) - Production multimodal systems

## Documentation

- [API Reference - MultimodalRAG](../../docs/en/api/multimodal_rag.md)
- [PDF Loader Guide](../../docs/en/guides/pdf_processing.md)
- [Vision Models Guide](../../docs/en/guides/vision_models.md)

---

**Start with `image_analysis.py` to understand vision models, then progress to PDF and RAG examples!**
