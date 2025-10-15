"""Built-in MCP tools for Multimodal RAG

Exposes multimodal indexing and search via MCP.
"""

from __future__ import annotations

import json
from pathlib import Path

from kagura import tool


@tool
async def multimodal_index(directory: str, collection_name: str = "default") -> str:
    """Index multimodal files (images, PDFs, audio)

    Args:
        directory: Directory path to index
        collection_name: RAG collection name

    Returns:
        Indexing status or error
    """
    try:
        from kagura.core.memory import MultimodalRAG

        rag = MultimodalRAG(directory=Path(directory), collection_name=collection_name)

        await rag.build_index()

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
    directory: str, query: str, collection_name: str = "default", k: int = 3
) -> str:
    """Search multimodal content

    Args:
        directory: Directory path (required for initialization)
        query: Search query
        collection_name: RAG collection name
        k: Number of results

    Returns:
        JSON string of search results or error
    """
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
