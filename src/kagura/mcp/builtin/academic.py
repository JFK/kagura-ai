"""Academic search integration for Kagura AI.

Provides tools for searching academic papers via arXiv API.
"""

from __future__ import annotations

import json
import logging

from kagura import tool

logger = logging.getLogger(__name__)


@tool
async def arxiv_search(
    query: str,
    max_results: int = 5,
    category: str | None = None,
) -> str:
    """Search for academic papers on arXiv.

    Use this tool when:
    - User asks for academic papers or research
    - Need scientific literature on a topic
    - Looking for preprints or latest research
    - User mentions arXiv, papers, or academic search

    Supported categories:
    - cs.AI: Artificial Intelligence
    - cs.LG: Machine Learning
    - cs.CL: Computation and Language (NLP)
    - cs.CV: Computer Vision
    - physics: Physics (all)
    - math: Mathematics (all)
    - stat: Statistics
    - q-bio: Quantitative Biology

    Args:
        query: Search query (title, abstract, author)
        max_results: Number of results to return (default: 5, max: 20)
        category: Optional category filter (e.g., "cs.AI", "cs.LG")

    Returns:
        JSON string with paper results including title, authors,
        abstract, PDF URL, and publication date

    Examples:
        # General search
        query="transformer attention mechanism", max_results=5

        # Category-specific search
        query="deep learning", category="cs.LG", max_results=10

        # Author search
        query="Hinton neural networks", max_results=3
    """
    # Ensure max_results is int
    if isinstance(max_results, str):
        try:
            max_results = int(max_results)
        except ValueError:
            max_results = 5

    # Clamp max_results
    max_results = min(max(1, max_results), 20)

    try:
        import arxiv  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps(
            {
                "error": "arxiv package is required",
                "install": "uv add arxiv",
                "help": "Install with: pip install arxiv",
            },
            indent=2,
        )

    try:
        # Construct search query
        search_query = query
        if category:
            # Add category filter to query
            search_query = f"cat:{category} AND {query}"

        # Create client
        client = arxiv.Client()

        # Execute search
        search = arxiv.Search(
            query=search_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        # Extract results
        results = []
        for paper in client.results(search):
            published_date = paper.published.isoformat() if paper.published else None
            results.append(
                {
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "abstract": paper.summary[:500],  # First 500 chars
                    "pdf_url": paper.pdf_url,
                    "published": published_date,
                    "categories": paper.categories,
                    "arxiv_id": paper.entry_id.split("/")[-1],  # Extract ID
                }
            )

        if not results:
            return json.dumps(
                {"message": f"No papers found for query: {query}", "results": []},
                ensure_ascii=False,
                indent=2,
            )

        return json.dumps(
            {"query": query, "count": len(results), "results": results},
            ensure_ascii=False,
            indent=2,
        )

    except Exception as e:
        logger.error(f"arXiv search error for query '{query}': {str(e)}")
        return json.dumps(
            {"error": f"arXiv search failed: {str(e)}"},
            ensure_ascii=False,
            indent=2,
        )
