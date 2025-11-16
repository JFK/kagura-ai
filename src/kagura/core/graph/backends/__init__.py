"""Graph Memory Backend Abstraction Layer.

Issue #554 - Cloud-Native Infrastructure Migration (PostgreSQL + Redis + Qdrant)

Provides pluggable storage backends for GraphMemory:
- JSONBackend: File-based storage (default, local development)
- PostgresBackend: PostgreSQL JSONB storage (production, cloud)
"""

from .base import GraphBackend
from .json_backend import JSONBackend

__all__ = [
    "GraphBackend",
    "JSONBackend",
]

# PostgresBackend is optional (requires SQLAlchemy)
try:
    from .postgres_backend import PostgresBackend

    __all__.append("PostgresBackend")
except ImportError:
    pass
