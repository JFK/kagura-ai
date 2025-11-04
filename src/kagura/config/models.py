"""Default model names for Kagura AI.

Centralized model name constants to avoid hardcoding across the codebase.
"""

# Embedding Models
DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
"""Default embedding model for semantic search (1024-dim, multilingual)."""

DEFAULT_EMBEDDING_MODEL_DIMENSION = 1024
"""Embedding dimension for default model."""

# Reranking Models
DEFAULT_RERANKING_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
"""Default cross-encoder reranking model (~80 MB)."""

# Model Aliases
EMBEDDING_MODELS = {
    "e5-large": "intfloat/multilingual-e5-large",  # 1024-dim, best quality
    "e5-base": "intfloat/multilingual-e5-base",  # 768-dim, faster
    "e5-small": "intfloat/multilingual-e5-small",  # 384-dim, fastest
}

RERANKING_MODELS = {
    "ms-marco-mini": "cross-encoder/ms-marco-MiniLM-L-6-v2",  # Default
    "ms-marco-base": "cross-encoder/ms-marco-MiniLM-L-12-v2",  # Larger, slower
}
