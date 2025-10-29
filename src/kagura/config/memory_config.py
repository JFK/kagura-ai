"""Memory system configuration.

Centralized configuration for memory components:
- Embedding models (E5-series multilingual)
- Reranking (Cross-Encoder)
- Recall scoring weights
- Overall memory system settings

Example:
    >>> config = MemorySystemConfig()
    >>> config.embedding.model
    'intfloat/multilingual-e5-large'
    >>> config.rerank.enabled
    True
"""

from typing import Optional

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Embedding model configuration.

    Attributes:
        model: HuggingFace model identifier
        dimension: Embedding dimension (1024 for E5-large, 768 for E5-base)
        use_prefix: Use query:/passage: prefixes (required for E5-series)
        max_tokens: Maximum sequence length
        normalize: Normalize embeddings to unit vectors
    """

    model: str = Field(
        default="intfloat/multilingual-e5-large",
        description="HuggingFace model identifier",
    )
    dimension: int = Field(default=1024, description="Embedding dimension", ge=1)
    use_prefix: bool = Field(
        default=True,
        description="Use query:/passage: prefixes (required for E5-series)",
    )
    max_tokens: int = Field(default=512, description="Maximum sequence length", ge=1)
    normalize: bool = Field(
        default=True, description="Normalize embeddings to unit vectors"
    )


class RerankConfig(BaseModel):
    """Cross-Encoder reranking configuration.

    Attributes:
        enabled: Enable reranking (recommended for better precision)
        model: Cross-Encoder model identifier
        candidates_k: Number of candidates to retrieve before reranking
        top_k: Number of final results after reranking
        batch_size: Batch size for reranking (memory vs speed tradeoff)
    """

    enabled: bool = Field(
        default=False,
        description="Enable reranking (requires sentence-transformers, slow first run)",
    )
    model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-Encoder model identifier",
    )
    candidates_k: int = Field(
        default=100,
        description="Number of candidates to retrieve before reranking",
        ge=1,
    )
    top_k: int = Field(
        default=20, description="Number of final results after reranking", ge=1
    )
    batch_size: int = Field(
        default=32, description="Batch size for reranking", ge=1, le=256
    )


class RecallScorerConfig(BaseModel):
    """Multi-dimensional recall scoring configuration.

    Inspired by DNC/NTM, uses weighted combination of:
    - Semantic similarity (cosine distance)
    - Recency (time decay)
    - Access frequency (usage count)
    - Graph distance (relationship proximity)
    - Importance (user-assigned weight)

    Attributes:
        weights: Weight for each scoring dimension (should sum to ~1.0)
        recency_decay_days: Days until memory importance decays by ~63% (exp decay)
        frequency_saturation: Access count at which frequency score saturates
    """

    weights: dict[str, float] = Field(
        default={
            "semantic_similarity": 0.30,
            "recency": 0.20,
            "access_frequency": 0.15,
            "graph_distance": 0.15,
            "importance": 0.20,
        },
        description="Weight for each scoring dimension",
    )
    recency_decay_days: int = Field(
        default=30, description="Days until memory decays by ~63%", ge=1
    )
    frequency_saturation: int = Field(
        default=100, description="Access count saturation point", ge=1
    )


class HybridSearchConfig(BaseModel):
    """Hybrid search configuration (vector + lexical).

    Combines vector search (semantic) with lexical search (keyword) using
    Reciprocal Rank Fusion (RRF) for improved precision and recall.

    Attributes:
        enabled: Enable hybrid search (RRF fusion)
        rrf_k: RRF constant (typical: 60, from original SIGIR 2009 paper)
        lexical_weight: Weight for lexical search results (0.0-1.0)
        vector_weight: Weight for vector search results (0.0-1.0)
        candidates_k: Number of candidates from each search method
        min_lexical_score: Minimum BM25 score threshold
    """

    enabled: bool = Field(default=True, description="Enable hybrid search (v4.0.0a0)")
    rrf_k: int = Field(default=60, description="RRF constant", ge=1)
    lexical_weight: float = Field(
        default=0.5, description="Weight for lexical results", ge=0.0, le=1.0
    )
    vector_weight: float = Field(
        default=0.5, description="Weight for vector results", ge=0.0, le=1.0
    )
    candidates_k: int = Field(
        default=100,
        description="Number of candidates from each search method",
        ge=1,
    )
    min_lexical_score: float = Field(
        default=0.0, description="Minimum BM25 score threshold", ge=0.0
    )


class MemorySystemConfig(BaseModel):
    """Overall memory system configuration.

    Example:
        >>> config = MemorySystemConfig()
        >>> config.embedding.model
        'intfloat/multilingual-e5-large'
        >>> config.rerank.enabled
        True
        >>> config.recall_scorer.weights["semantic_similarity"]
        0.3
    """

    embedding: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig, description="Embedding configuration"
    )
    rerank: RerankConfig = Field(
        default_factory=RerankConfig, description="Reranking configuration"
    )
    recall_scorer: RecallScorerConfig = Field(
        default_factory=RecallScorerConfig, description="Recall scoring configuration"
    )
    hybrid_search: HybridSearchConfig = Field(
        default_factory=HybridSearchConfig,
        description="Hybrid search configuration (Phase 2)",
    )

    # Global settings
    enable_access_tracking: bool = Field(
        default=True, description="Track memory access for frequency-based scoring"
    )
    enable_graph_scoring: bool = Field(
        default=True, description="Use graph distance in recall scoring"
    )

    def model_post_init(self, __context) -> None:
        """Post-initialization hook to apply environment variables"""
        import os

        # Check environment variable for reranking
        if os.environ.get("KAGURA_ENABLE_RERANKING", "").lower() == "true":
            self.rerank.enabled = True

    @classmethod
    def from_dict(cls, config_dict: dict) -> "MemorySystemConfig":
        """Create config from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            MemorySystemConfig instance
        """
        return cls(**config_dict)

    def to_dict(self) -> dict:
        """Convert config to dictionary.

        Returns:
            Configuration dictionary
        """
        return self.model_dump()


# Default global instance
DEFAULT_CONFIG = MemorySystemConfig()


def get_default_config() -> MemorySystemConfig:
    """Get default memory system configuration.

    Returns:
        Default MemorySystemConfig instance
    """
    return DEFAULT_CONFIG


def load_config(config_path: Optional[str] = None) -> MemorySystemConfig:
    """Load memory system configuration from file.

    Args:
        config_path: Path to configuration file (JSON/YAML)
            If None, returns default configuration

    Returns:
        MemorySystemConfig instance

    Example:
        >>> config = load_config("memory_config.json")
    """
    if config_path is None:
        return get_default_config()

    # TODO: Implement file loading (JSON/YAML)
    # For now, return default
    return get_default_config()
