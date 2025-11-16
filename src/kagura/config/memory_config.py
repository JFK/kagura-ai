"""Memory system configuration.

Centralized configuration for memory components:
- Embedding models (E5-series multilingual, OpenAI API)
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

import os
from typing import Literal, Optional

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Embedding model configuration.

    Attributes:
        provider: Embedding provider (openai or sentence-transformers)
        model: Model identifier (HuggingFace model or OpenAI model name)
        dimension: Embedding dimension (auto-detected for OpenAI models)
        use_prefix: Use query:/passage: prefixes (required for E5-series)
        max_tokens: Maximum sequence length
        normalize: Normalize embeddings to unit vectors
    """

    provider: Literal["openai", "sentence-transformers"] = Field(
        default="sentence-transformers",
        description="Embedding provider (openai for API, sentence-transformers for local)",
    )
    model: str = Field(
        default="intfloat/multilingual-e5-large",
        description="Model identifier (e.g., 'text-embedding-3-small' for OpenAI, 'intfloat/multilingual-e5-large' for local)",
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

    def model_post_init(self, __context) -> None:
        """Post-initialization: read from environment variables."""
        # Read EMBEDDING_PROVIDER
        env_provider = os.getenv("EMBEDDING_PROVIDER")
        if env_provider and env_provider in ["openai", "sentence-transformers"]:
            self.provider = env_provider  # type: ignore

        # Read EMBEDDING_MODEL
        env_model = os.getenv("EMBEDDING_MODEL")
        if env_model:
            self.model = env_model

        # Auto-configure dimension for OpenAI models
        if self.provider == "openai":
            if "text-embedding-3-small" in self.model:
                self.dimension = 1536
            elif "text-embedding-3-large" in self.model:
                self.dimension = 3072
            elif "text-embedding-ada-002" in self.model:
                self.dimension = 1536
            # Disable E5-style prefixes for OpenAI
            self.use_prefix = False


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
        default=False,  # Conservative default: avoid crashes in offline/restricted envs
        description=(
            "Enable reranking (requires sentence-transformers, slow first run). "
            "Recommended for +10-15% precision, but may fail in offline environments. "
            "Enable with: config.rerank.enabled = True or KAGURA_ENABLE_RERANKING=true"
        ),
    )
    model: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        description=(
            "Cross-Encoder model identifier. Default: BAAI/bge-reranker-v2-m3 "
            "(Apache 2.0, multilingual optimized for EN/ZH/JA, +5-8% precision vs ms-marco). "
            "Falls back to cross-encoder/ms-marco-MiniLM-L-6-v2 if unavailable."
        ),
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


class ChunkingConfig(BaseModel):
    """Semantic chunking configuration for long documents.

    Splits long texts into semantically coherent chunks while preserving context.
    Improves RAG precision for documents longer than embedding model context window.

    Attributes:
        enabled: Enable semantic chunking for long documents
        max_chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
        min_chunk_size: Minimum characters for chunking (shorter texts stored as-is)
    """

    enabled: bool = Field(
        default=True,  # Enabled by default for all users
        description=(
            "Enable semantic chunking for documents longer than max_chunk_size. "
            "Preserves semantic boundaries (paragraphs, sentences) instead of "
            "splitting at fixed positions. Improves precision for long documents."
        ),
    )
    max_chunk_size: int = Field(
        default=512,
        description="Maximum characters per chunk (typical embedding model context)",
        ge=100,
        le=4096,
    )
    overlap: int = Field(
        default=50,
        description="Number of overlapping characters between chunks for context retention",
        ge=0,
        le=500,
    )
    min_chunk_size: int = Field(
        default=100,
        description=(
            "Minimum document size (in characters) to trigger chunking. "
            "Documents shorter than this are stored as single chunks."
        ),
        ge=50,
        le=1000,
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
        enable_time_decay: Apply exponential time decay to search results (v4.0.11)
        time_decay_days: Time constant for exponential decay in days (v4.0.11)
            At this value, memories decay by ~63% (1 - 1/e), not 50%
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
    enable_time_decay: bool = Field(
        default=True,
        description="Apply exponential time decay boost to search results (v4.0.11)",
    )
    time_decay_days: float = Field(
        default=30.0,
        description="Half-life for time decay in days (v4.0.11)",
        ge=1.0,
    )


class BM25Config(BaseModel):
    """BM25 keyword search configuration.

    Attributes:
        k1: Term frequency saturation parameter (default: 1.2, optimized for short texts)
        b: Length normalization parameter (default: 0.4, reduced for memory entries)
    """

    k1: float = Field(
        default=1.2,
        description="Term frequency saturation (1.2-2.0, lower for short texts)",
        ge=0.0,
        le=3.0,
    )
    b: float = Field(
        default=0.4,
        description="Length normalization (0.0-1.0, lower for short texts)",
        ge=0.0,
        le=1.0,
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
        bm25: BM25 algorithm parameters
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
    bm25: BM25Config = Field(
        default_factory=BM25Config, description="BM25 parameters (v4.0.11)"
    )


class MemorySystemConfig(BaseModel):
    """Overall memory system configuration.

    Example:
        >>> config = MemorySystemConfig()
        >>> config.embedding.model
        'intfloat/multilingual-e5-large'
        >>> config.rerank.enabled
        True
        >>> config.chunking.enabled
        True
        >>> config.chunking.max_chunk_size
        512
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
    chunking: ChunkingConfig = Field(
        default_factory=ChunkingConfig,
        description="Semantic chunking configuration (Issue #527)",
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

        # Check reranking config (env var + pyproject.toml + .env)
        from kagura.config.project import get_reranking_enabled

        # IMPORTANT: Respect explicit rerank config (Issue #548)
        # Only auto-enable if 'rerank' parameter was explicitly provided by user
        # This allows CLI lightweight config to disable reranker
        if "rerank" in self.__pydantic_fields_set__:
            # User explicitly configured rerank, respect their choice
            return

        # Auto-enable if model is cached (smart default for existing users)
        if get_reranking_enabled():
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
