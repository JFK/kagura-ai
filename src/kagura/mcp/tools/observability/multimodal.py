"""Built-in MCP tools for Multimodal RAG

Exposes multimodal indexing and search via MCP.
"""

from __future__ import annotations

import json
from pathlib import Path

from kagura import tool


@tool
async def multimodal_index(
    directory: str, collection_name: str = "default", language: str = "en"
) -> str:
    """Index multimodal files (images, PDFs, audio) with language support.

    Args:
        directory: Directory path to index
        collection_name: RAG collection name
        language: Content language ("en" or "ja") for transcription/analysis

    Returns:
        Indexing status or error

    Example:
        # English content
        multimodal_index("/path/to/docs")

        # Japanese content
        multimodal_index("/path/to/docs", language="ja")
    """
    try:
        from kagura.core.memory import MultimodalRAG

        rag = MultimodalRAG(directory=Path(directory), collection_name=collection_name)

        # Build index with language support
        await rag.build_index(language=language)

        return f"Indexed directory '{directory}' into collection '{collection_name}'"
    except ImportError:
        return (
            "Error: Multimodal RAG requires 'web' extra. "
            "Install with: pip install kagura-ai[web]"
        )
    except Exception as e:
        return f"Error indexing directory: {e}"


@tool
def multimodal_search(
    directory: str,
    query: str,
    collection_name: str = "default",
    k: int = 3,
    language: str = "en",
) -> str:
    """Search multimodal content with language support.

    Args:
        directory: Directory path (required for initialization)
        query: Search query (in English or Japanese)
        collection_name: RAG collection name
        k: Number of results
        language: Query/response language ("en" or "ja")

    Returns:
        JSON string of search results or error

    Example:
        # English search
        multimodal_search("/docs", "authentication flow")

        # Japanese search
        multimodal_search("/docs", "認証の仕組み", language="ja")
    """
    # Ensure k is int (LLM might pass as string)
    if isinstance(k, str):
        try:
            k = int(k)
        except ValueError:
            k = 3  # Default fallback

    try:
        from kagura.core.memory import MultimodalRAG

        rag = MultimodalRAG(directory=Path(directory), collection_name=collection_name)
        results = rag.query(query, n_results=k)

        return json.dumps(results, indent=2)
    except ImportError:
        return json.dumps(
            {
                "error": "Multimodal RAG requires 'web' extra. "
                "Install with: pip install kagura-ai[web]"
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})
