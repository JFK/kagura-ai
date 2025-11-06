"""Cross-Encoder reranking for semantic search results.

Improves precision of search results by re-scoring with a cross-encoder model.
Uses a two-stage retrieval approach:
1. Retrieve K candidates with fast bi-encoder (vector search)
2. Rerank top-k with accurate but slower cross-encoder

Default model: BAAI/bge-reranker-v2-m3 (Apache 2.0)
- Multilingual optimized (English, Chinese, Japanese)
- +5-8% precision improvement over ms-marco-MiniLM-L-6-v2
- Automatic fallback to ms-marco if BGE unavailable

References:
- BGE reranker: https://huggingface.co/BAAI/bge-reranker-v2-m3
- MS MARCO: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2

Example:
    >>> reranker = MemoryReranker()
    >>> candidates = [
    ...     {"content": "Python is a programming language", "distance": 0.3},
    ...     {"content": "Java is also a language", "distance": 0.4},
    ... ]
    >>> reranked = reranker.rerank("What is Python?", candidates, top_k=1)
    >>> print(reranked[0]["content"])
    'Python is a programming language'
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from kagura.config.memory_config import RerankConfig

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder


def is_reranker_available(
    model_name: str = "BAAI/bge-reranker-v2-m3",
    check_fallback: bool = True,
) -> bool:
    """Check if reranker model is available (installed and cached).

    Uses huggingface_hub API to properly detect cached models,
    respecting HF_HOME and other environment variables.

    Args:
        model_name: Model identifier to check (default: BGE-reranker-v2-m3)
        check_fallback: If True and primary model not found, check fallback ms-marco model

    Returns:
        True if model (or fallback) is ready to use without download, False otherwise
    """
    def _check_model_cache(name: str) -> bool:
        """Helper to check if a specific model is cached."""
        try:
            # Check sentence-transformers installation
            import sentence_transformers  # noqa: F401

            # Use huggingface_hub to check cache (respects HF_HOME, etc.)
            try:
                from huggingface_hub import try_to_load_from_cache
                from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE

                # Check for config.json (main model file)
                cache_path = try_to_load_from_cache(
                    name, "config.json", cache_dir=HUGGINGFACE_HUB_CACHE
                )

                # If not None and not _CACHED_NO_EXIST, model is cached
                return cache_path is not None and cache_path != "_CACHED_NO_EXIST"
            except ImportError:
                # Fallback to directory check if huggingface_hub not available
                cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
                if not cache_dir.exists():
                    return False

                model_slug = name.replace("/", "--")
                model_dirs = list(cache_dir.glob(f"models--{model_slug}*"))
                return len(model_dirs) > 0

        except ImportError:
            return False

    # Check primary model
    if _check_model_cache(model_name):
        return True

    # Check fallback model if requested
    if check_fallback:
        fallback_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        if model_name != fallback_model:
            return _check_model_cache(fallback_model)

    return False


class MemoryReranker:
    """Cross-encoder reranker for memory search results.

    Reranks search candidates using a cross-encoder model for improved
    precision. Cross-encoders are more accurate than bi-encoders but slower,
    so they're best used on a small set of top candidates.

    Attributes:
        config: Reranking configuration
        model: Cross-encoder model instance
    """

    def __init__(
        self,
        config: Optional[RerankConfig] = None,
    ):
        """Initialize reranker with automatic fallback.

        Tries to load the configured model (default: BGE-reranker-v2-m3).
        Falls back to ms-marco-MiniLM-L-6-v2 if the primary model is unavailable.

        Args:
            config: RerankConfig instance (defaults to BGE-reranker-v2-m3)

        Raises:
            ImportError: If sentence-transformers is not installed
            Exception: If both primary and fallback models fail to load
        """
        import logging

        logger = logging.getLogger(__name__)

        self.config = config or RerankConfig()
        original_model = self.config.model
        logger.debug(f"MemoryReranker init: model={self.config.model}")

        try:
            logger.debug("MemoryReranker: Importing sentence_transformers...")
            from sentence_transformers import CrossEncoder

            logger.debug("MemoryReranker: sentence_transformers imported")

            # Try loading the configured model
            try:
                logger.debug(f"MemoryReranker: Loading CrossEncoder '{self.config.model}'")
                logger.debug("Note: First run may download model from Hugging Face (slow)")
                self.model: CrossEncoder = CrossEncoder(self.config.model)
                logger.debug("MemoryReranker: CrossEncoder model loaded successfully")
            except Exception as e:
                # Fallback to ms-marco if primary model fails
                fallback_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
                if self.config.model != fallback_model:
                    logger.warning(
                        f"Failed to load primary reranker model '{self.config.model}': {e}. "
                        f"Falling back to '{fallback_model}'..."
                    )
                    try:
                        self.model = CrossEncoder(fallback_model)
                        self.config.model = fallback_model  # Update config to reflect actual model
                        logger.info(f"MemoryReranker: Fallback model '{fallback_model}' loaded successfully")
                    except Exception as fallback_error:
                        raise RuntimeError(
                            f"Failed to load both primary model '{original_model}' and "
                            f"fallback model '{fallback_model}'. "
                            "Ensure you have internet connection for first-time model download."
                        ) from fallback_error
                else:
                    # Primary model is already the fallback, no more fallbacks available
                    raise RuntimeError(
                        f"Failed to load reranker model '{self.config.model}': {e}"
                    ) from e
        except ImportError as e:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            ) from e

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Rerank candidates by query-document relevance.

        Args:
            query: Search query
            candidates: List of candidate documents with 'content' field
            top_k: Number of results to return (defaults to config.top_k)

        Returns:
            Reranked list of candidates with 'rerank_score' field added

        Example:
            >>> reranker.rerank(
            ...     "Python async",
            ...     [{"content": "asyncio tutorial"}, {"content": "Java threads"}],
            ...     top_k=1
            ... )
        """
        if not candidates:
            return []

        top_k = top_k or self.config.top_k

        # Prepare [query, doc] pairs
        pairs = [[query, c.get("content", "")] for c in candidates]

        # Batch prediction with cross-encoder
        scores = self.model.predict(
            pairs, batch_size=self.config.batch_size, show_progress_bar=False
        )

        # Add rerank scores to candidates
        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        # Sort by rerank score (higher is better)
        reranked = sorted(
            candidates, key=lambda x: x.get("rerank_score", -float("inf")), reverse=True
        )

        return reranked[:top_k]

    def rerank_batch(
        self,
        queries: list[str],
        candidates_list: list[list[dict[str, Any]]],
        top_k: Optional[int] = None,
    ) -> list[list[dict[str, Any]]]:
        """Rerank multiple query-candidates pairs efficiently.

        Args:
            queries: List of search queries
            candidates_list: List of candidate lists (one per query)
            top_k: Number of results per query

        Returns:
            List of reranked candidate lists

        Note:
            All reranking is done in a single batched call for efficiency.
        """
        if len(queries) != len(candidates_list):
            raise ValueError("queries and candidates_list must have same length")

        if not queries:
            return []

        top_k = top_k or self.config.top_k

        # Flatten all [query, doc] pairs for batched prediction
        all_pairs: list[list[str]] = []
        pair_counts: list[int] = []  # Track how many pairs per query

        for query, candidates in zip(queries, candidates_list):
            query_pairs = [[query, c.get("content", "")] for c in candidates]
            all_pairs.extend(query_pairs)
            pair_counts.append(len(query_pairs))

        # Batch predict all at once
        all_scores = self.model.predict(
            all_pairs, batch_size=self.config.batch_size, show_progress_bar=False
        )

        # Split scores back to per-query groups
        results: list[list[dict[str, Any]]] = []
        score_idx = 0

        for candidates, count in zip(candidates_list, pair_counts):
            # Get scores for this query's candidates
            query_scores = all_scores[score_idx : score_idx + count]
            score_idx += count

            # Add rerank scores
            for candidate, score in zip(candidates, query_scores):
                candidate["rerank_score"] = float(score)

            # Sort and take top-k
            reranked = sorted(
                candidates,
                key=lambda x: x.get("rerank_score", -float("inf")),
                reverse=True,
            )
            results.append(reranked[:top_k])

        return results

    def score_pair(self, query: str, document: str) -> float:
        """Score a single query-document pair.

        Args:
            query: Search query
            document: Document text

        Returns:
            Relevance score (higher is better, typically -10 to +10)

        Example:
            >>> score = reranker.score_pair("Python", "Python is a language")
            >>> print(f"Relevance: {score:.2f}")
        """
        score = self.model.predict([[query, document]], show_progress_bar=False)[0]
        return float(score)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MemoryReranker(model={self.config.model}, "
            f"batch_size={self.config.batch_size})"
        )
