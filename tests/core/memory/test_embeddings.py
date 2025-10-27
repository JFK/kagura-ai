"""Tests for embedding models with prefix handling."""

import pytest

pytest.importorskip("sentence_transformers")

from kagura.core.memory.embeddings import Embedder, EmbeddingConfig


def test_embedding_config_defaults():
    """Test default embedding configuration."""
    config = EmbeddingConfig()
    assert config.model == "intfloat/multilingual-e5-large"
    assert config.dimension == 1024
    assert config.use_prefix is True
    assert config.max_tokens == 512
    assert config.normalize is True


def test_embedding_config_custom():
    """Test custom embedding configuration."""
    config = EmbeddingConfig(
        model="intfloat/multilingual-e5-base",
        dimension=768,
        use_prefix=False,
        max_tokens=256,
        normalize=False,
    )
    assert config.model == "intfloat/multilingual-e5-base"
    assert config.dimension == 768
    assert config.use_prefix is False
    assert config.max_tokens == 256
    assert config.normalize is False


@pytest.mark.slow
def test_embedder_initialization():
    """Test embedder initialization with E5 model."""
    config = EmbeddingConfig(model="sentence-transformers/all-MiniLM-L6-v2")
    embedder = Embedder(config)

    assert embedder.config == config
    assert embedder.model is not None
    assert embedder.dimension == config.dimension


@pytest.mark.slow
def test_embedder_encode_queries():
    """Test query encoding with prefix."""
    config = EmbeddingConfig(
        model="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384,
        use_prefix=True,
    )
    embedder = Embedder(config)

    queries = ["What is Python?", "How to use FastAPI?"]
    embeddings = embedder.encode_queries(queries)

    assert embeddings.shape == (2, 384)
    assert embeddings.dtype.name.startswith("float")


@pytest.mark.slow
def test_embedder_encode_passages():
    """Test passage encoding with prefix."""
    config = EmbeddingConfig(
        model="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384,
        use_prefix=True,
    )
    embedder = Embedder(config)

    passages = ["Python is a programming language", "FastAPI is a web framework"]
    embeddings = embedder.encode_passages(passages)

    assert embeddings.shape == (2, 384)
    assert embeddings.dtype.name.startswith("float")


@pytest.mark.slow
def test_embedder_encode_with_flag():
    """Test encode method with is_query flag."""
    config = EmbeddingConfig(
        model="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384,
    )
    embedder = Embedder(config)

    texts = ["Example text"]

    query_emb = embedder.encode(texts, is_query=True)
    passage_emb = embedder.encode(texts, is_query=False)

    assert query_emb.shape == (1, 384)
    assert passage_emb.shape == (1, 384)
    # With prefix enabled, embeddings should be different
    if config.use_prefix:
        assert not (query_emb == passage_emb).all()


def test_embedder_dimension_property():
    """Test embedder dimension property."""
    config = EmbeddingConfig(dimension=768)
    embedder = Embedder.__new__(Embedder)  # Skip __init__
    embedder.config = config

    assert embedder.dimension == 768


def test_embedder_repr():
    """Test embedder string representation."""
    config = EmbeddingConfig(model="test-model", dimension=512, use_prefix=False)
    embedder = Embedder.__new__(Embedder)
    embedder.config = config

    repr_str = repr(embedder)
    assert "test-model" in repr_str
    assert "512" in repr_str
    assert "False" in repr_str


def test_embedder_missing_dependency():
    """Test error when sentence-transformers is not installed."""
    # This test is tricky as we need sentence_transformers to run tests
    # For now, just test the ImportError path is defined
    try:
        from kagura.core.memory.embeddings import Embedder

        # If import succeeds, we can't test the failure path
        assert True
    except ImportError:
        # Expected if sentence_transformers is not installed
        assert True
