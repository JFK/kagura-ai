"""Embedding models with multilingual support and prefix handling.

This module provides embedding functionality with support for:
- E5-series multilingual models (sentence-transformers)
- OpenAI Embeddings API (text-embedding-3-small, text-embedding-3-large)
- Query/passage prefix handling (required for E5)
- Configurable embedding dimensions
- Fallback to default models

Providers:
- sentence-transformers: Local models (E5, all-MiniLM, etc.) - requires RAM
- openai: OpenAI API (text-embedding-3-*) - cloud-friendly, no RAM needed

Based on intfloat/multilingual-e5-large:
https://huggingface.co/intfloat/multilingual-e5-large
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np

from kagura.config.memory_config import EmbeddingConfig

if TYPE_CHECKING:
    from openai import OpenAI
    from sentence_transformers import SentenceTransformer


class Embedder:
    """Base embedder with query/passage prefix support.

    Handles embedding generation with proper prefix handling for E5-series models.
    Supports both local models (sentence-transformers) and OpenAI API.

    Example:
        >>> # Local model
        >>> config = EmbeddingConfig(provider="sentence-transformers", model="intfloat/multilingual-e5-large")
        >>> embedder = Embedder(config)
        >>>
        >>> # OpenAI API
        >>> config = EmbeddingConfig(provider="openai", model="text-embedding-3-small")
        >>> embedder = Embedder(config)
        >>>
        >>> query_emb = embedder.encode_queries(["What is Python?"])
        >>> doc_emb = embedder.encode_passages(["Python is a programming language"])
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize embedder.

        Args:
            config: Embedding configuration (defaults to E5-large local)

        Raises:
            ImportError: If required dependencies are not installed
            ValueError: If OPENAI_API_KEY is not set when using OpenAI provider
        """
        self.config = config or EmbeddingConfig()
        self.model: Optional[SentenceTransformer] = None
        self.openai_client: Optional[OpenAI] = None

        if self.config.provider == "openai":
            # Initialize OpenAI client
            try:
                from openai import OpenAI
                import os

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "OPENAI_API_KEY environment variable not set. "
                        "Required when using EMBEDDING_PROVIDER=openai"
                    )

                self.openai_client = OpenAI(api_key=api_key)
            except ImportError as e:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                ) from e

        else:  # sentence-transformers
            try:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer(self.config.model)
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
            OpenAI models do not use prefixes.
        """
        if self.config.provider == "openai":
            return self._encode_with_openai(texts)

        # sentence-transformers
        if self.config.use_prefix:
            texts = [f"query: {t}" for t in texts]

        return self.model.encode(  # type: ignore
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
            OpenAI models do not use prefixes.
        """
        if self.config.provider == "openai":
            return self._encode_with_openai(texts)

        # sentence-transformers
        if self.config.use_prefix:
            texts = [f"passage: {t}" for t in texts]

        return self.model.encode(  # type: ignore
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

    def _encode_with_openai(self, texts: list[str]) -> np.ndarray:
        """Encode texts using OpenAI Embeddings API.

        Args:
            texts: List of strings to encode

        Returns:
            Numpy array of shape (len(texts), dimension)

        Raises:
            RuntimeError: If OpenAI API call fails
        """
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            response = self.openai_client.embeddings.create(
                model=self.config.model,
                input=texts,
            )

            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]

            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)

            # Normalize if configured
            if self.config.normalize:
                norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
                embeddings_array = embeddings_array / norms

            return embeddings_array

        except Exception as e:
            raise RuntimeError(f"OpenAI embeddings API error: {e}") from e

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Embedder(provider={self.config.provider}, "
            f"model={self.config.model}, "
            f"dim={self.config.dimension}, "
            f"prefix={self.config.use_prefix})"
        )
