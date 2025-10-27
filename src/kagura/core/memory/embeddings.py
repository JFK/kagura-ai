"""Embedding models with multilingual support and prefix handling.

This module provides embedding functionality with support for:
- E5-series multilingual models
- Query/passage prefix handling (required for E5)
- Configurable embedding dimensions
- Fallback to default models

Based on intfloat/multilingual-e5-large:
https://huggingface.co/intfloat/multilingual-e5-large
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np

from kagura.config.memory_config import EmbeddingConfig

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class Embedder:
    """Base embedder with query/passage prefix support.

    Handles embedding generation with proper prefix handling for E5-series models.
    Falls back gracefully if sentence-transformers is not available.

    Example:
        >>> config = EmbeddingConfig(model="intfloat/multilingual-e5-large")
        >>> embedder = Embedder(config)
        >>> query_emb = embedder.encode_queries(["What is Python?"])
        >>> doc_emb = embedder.encode_passages(["Python is a programming language"])
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize embedder.

        Args:
            config: Embedding configuration (defaults to E5-large)

        Raises:
            ImportError: If sentence-transformers is not installed
        """
        self.config = config or EmbeddingConfig()

        try:
            from sentence_transformers import SentenceTransformer

            self.model: SentenceTransformer = SentenceTransformer(self.config.model)
        except ImportError as e:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            ) from e

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        """Encode queries with 'query: ' prefix.

        Args:
            texts: List of query strings

        Returns:
            Numpy array of shape (len(texts), dimension)

        Note:
            E5-series models REQUIRE the 'query: ' prefix for queries.
            Omitting it significantly degrades performance.
        """
        if self.config.use_prefix:
            texts = [f"query: {t}" for t in texts]

        return self.model.encode(
            texts,
            normalize_embeddings=self.config.normalize,
            show_progress_bar=False,
        )

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        """Encode passages/documents with 'passage: ' prefix.

        Args:
            texts: List of document/passage strings

        Returns:
            Numpy array of shape (len(texts), dimension)

        Note:
            E5-series models REQUIRE the 'passage: ' prefix for documents.
            Omitting it significantly degrades performance.
        """
        if self.config.use_prefix:
            texts = [f"passage: {t}" for t in texts]

        return self.model.encode(
            texts,
            normalize_embeddings=self.config.normalize,
            show_progress_bar=False,
        )

    def encode(self, texts: list[str], is_query: bool = False) -> np.ndarray:
        """Encode texts with appropriate prefix.

        Args:
            texts: List of strings to encode
            is_query: If True, use 'query: ' prefix; else use 'passage: '

        Returns:
            Numpy array of shape (len(texts), dimension)

        Example:
            >>> embedder.encode(["Python tutorial"], is_query=True)
            >>> embedder.encode(["Python is a language"], is_query=False)
        """
        if is_query:
            return self.encode_queries(texts)
        else:
            return self.encode_passages(texts)

    @property
    def dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Embedding dimension
        """
        return self.config.dimension

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Embedder(model={self.config.model}, "
            f"dim={self.config.dimension}, "
            f"prefix={self.config.use_prefix})"
        )
