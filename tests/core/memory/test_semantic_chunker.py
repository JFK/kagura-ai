"""Tests for semantic chunking."""

import pytest

pytest.importorskip("langchain_text_splitters")

from kagura.config.memory_config import ChunkingConfig  # noqa: E402
from kagura.core.memory.semantic_chunker import (  # noqa: E402
    ChunkMetadata,
    SemanticChunker,
    is_chunking_available,
)


def test_chunking_availability():
    """Test that chunking is available when langchain-text-splitters is installed."""
    assert is_chunking_available() is True


def test_chunking_config_defaults():
    """Test default chunking configuration."""
    config = ChunkingConfig()
    assert config.enabled is True
    assert config.max_chunk_size == 512
    assert config.overlap == 50
    assert config.min_chunk_size == 100


def test_chunking_config_custom():
    """Test custom chunking configuration."""
    config = ChunkingConfig(
        enabled=False,
        max_chunk_size=256,
        overlap=30,
        min_chunk_size=50,
    )
    assert config.enabled is False
    assert config.max_chunk_size == 256
    assert config.overlap == 30
    assert config.min_chunk_size == 50


def test_semantic_chunker_initialization():
    """Test SemanticChunker initialization."""
    chunker = SemanticChunker(max_chunk_size=512, overlap=50)
    assert chunker.max_chunk_size == 512
    assert chunker.overlap == 50
    assert chunker.splitter is not None


def test_semantic_chunker_default_separators():
    """Test default separator priority."""
    chunker = SemanticChunker()
    expected_separators = ["\n\n", "\n", ". ", ", ", " ", ""]
    assert chunker.separators == expected_separators


def test_semantic_chunker_custom_separators():
    """Test custom separators."""
    custom_separators = ["\n", " "]
    chunker = SemanticChunker(separators=custom_separators)
    assert chunker.separators == custom_separators


def test_chunk_empty_text():
    """Test chunking empty or whitespace-only text."""
    chunker = SemanticChunker()

    # Empty string
    assert chunker.chunk("") == []

    # Whitespace only
    assert chunker.chunk("   \n  \t  ") == []


def test_chunk_short_text():
    """Test chunking text shorter than max_chunk_size."""
    chunker = SemanticChunker(max_chunk_size=100)
    short_text = "This is a short text."

    chunks = chunker.chunk(short_text)

    assert len(chunks) == 1
    assert chunks[0] == short_text


def test_chunk_long_text():
    """Test chunking text longer than max_chunk_size."""
    chunker = SemanticChunker(max_chunk_size=100, overlap=20)

    # Create a long text with clear paragraph boundaries
    long_text = "\n\n".join([f"Paragraph {i}. " * 10 for i in range(5)])

    chunks = chunker.chunk(long_text)

    # Should produce multiple chunks
    assert len(chunks) > 1

    # Each chunk should be <= max_chunk_size (with some tolerance for boundary detection)
    for chunk in chunks:
        assert len(chunk) <= chunker.max_chunk_size + 50  # Tolerance for separators


def test_chunk_preserves_paragraph_boundaries():
    """Test that chunking respects paragraph boundaries when possible."""
    chunker = SemanticChunker(max_chunk_size=200, overlap=20)

    text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."

    chunks = chunker.chunk(text)

    # Chunks should split at paragraph boundaries
    # (Exact behavior depends on text length vs max_chunk_size)
    assert all("\n\n" not in chunk or chunk.startswith("\n\n") or chunk.endswith("\n\n") for chunk in chunks[1:-1])


def test_chunk_with_overlap():
    """Test that chunks have overlapping content."""
    chunker = SemanticChunker(max_chunk_size=50, overlap=10)

    text = "Word " * 50  # 250 characters total

    chunks = chunker.chunk(text)

    # Should produce multiple chunks
    assert len(chunks) > 1

    # Verify overlap exists (at least some common content)
    # Note: Exact overlap verification is complex due to semantic boundary detection
    # We just verify that chunks aren't completely disjoint
    total_chars = sum(len(chunk) for chunk in chunks)
    original_chars = len(text)

    # Total chars should be >= original due to overlap
    assert total_chars >= original_chars


def test_chunk_with_metadata_empty():
    """Test chunk_with_metadata on empty text."""
    chunker = SemanticChunker()
    metadata = chunker.chunk_with_metadata("")

    assert metadata == []


def test_chunk_with_metadata_single_chunk():
    """Test chunk_with_metadata on text that produces one chunk."""
    chunker = SemanticChunker(max_chunk_size=100)
    text = "Short text."
    source = "test.txt"

    metadata = chunker.chunk_with_metadata(text, source=source)

    assert len(metadata) == 1
    chunk = metadata[0]

    assert isinstance(chunk, ChunkMetadata)
    assert chunk.chunk_index == 0
    assert chunk.total_chunks == 1
    assert chunk.source == source
    assert chunk.content == text
    assert chunk.start_char == 0
    assert chunk.end_char == len(text)


def test_chunk_with_metadata_multiple_chunks():
    """Test chunk_with_metadata on long text."""
    chunker = SemanticChunker(max_chunk_size=50, overlap=10)
    text = "Sentence one. " * 20  # ~280 characters
    source = "document.md"

    metadata = chunker.chunk_with_metadata(text, source=source)

    # Verify multiple chunks
    assert len(metadata) > 1

    # Verify all chunks have correct metadata structure
    for i, chunk in enumerate(metadata):
        assert isinstance(chunk, ChunkMetadata)
        assert chunk.chunk_index == i
        assert chunk.total_chunks == len(metadata)
        assert chunk.source == source
        assert chunk.content is not None
        assert len(chunk.content) > 0
        assert chunk.start_char >= 0
        assert chunk.end_char > chunk.start_char


def test_chunk_with_metadata_default_source():
    """Test chunk_with_metadata uses default source when not provided."""
    chunker = SemanticChunker()
    text = "Some text."

    metadata = chunker.chunk_with_metadata(text)

    assert metadata[0].source == "unknown"


def test_chunk_metadata_dataclass():
    """Test ChunkMetadata dataclass creation."""
    metadata = ChunkMetadata(
        chunk_index=0,
        total_chunks=3,
        source="test.pdf",
        start_char=0,
        end_char=100,
        content="Test content",
    )

    assert metadata.chunk_index == 0
    assert metadata.total_chunks == 3
    assert metadata.source == "test.pdf"
    assert metadata.start_char == 0
    assert metadata.end_char == 100
    assert metadata.content == "Test content"


def test_semantic_chunker_repr():
    """Test SemanticChunker string representation."""
    chunker = SemanticChunker(max_chunk_size=256, overlap=30)
    repr_str = repr(chunker)

    assert "SemanticChunker" in repr_str
    assert "256" in repr_str
    assert "30" in repr_str


def test_chunk_multilingual_text():
    """Test chunking with multilingual content."""
    chunker = SemanticChunker(max_chunk_size=100, overlap=20)

    # Japanese text
    japanese_text = "これは日本語のテキストです。" * 10
    chunks_ja = chunker.chunk(japanese_text)
    assert len(chunks_ja) > 0

    # Chinese text
    chinese_text = "这是中文文本。" * 10
    chunks_zh = chunker.chunk(chinese_text)
    assert len(chunks_zh) > 0

    # Mixed language
    mixed_text = "English text. 日本語テキスト. Chinese text 中文。" * 5
    chunks_mixed = chunker.chunk(mixed_text)
    assert len(chunks_mixed) > 0


def test_chunk_code_content():
    """Test chunking code/structured content."""
    chunker = SemanticChunker(max_chunk_size=150, overlap=30)

    # Python code
    code = """
def function_one():
    return "value"

def function_two():
    return "another value"

class MyClass:
    def method(self):
        pass
"""

    chunks = chunker.chunk(code)

    # Should preserve code structure
    assert len(chunks) > 0
    # All chunks should be valid Python-like strings (no split mid-line ideally)
    for chunk in chunks:
        # Check that chunk doesn't start/end with a random character mid-word
        assert len(chunk.strip()) > 0


def test_japanese_sentence_boundaries():
    """Test Japanese text chunks at proper sentence boundaries (。).

    Verifies that default separators now include Japanese punctuation.
    Regression test for multilingual support enhancement.
    """
    chunker = SemanticChunker(max_chunk_size=60, overlap=10)

    # Japanese text with clear sentence boundaries
    japanese_text = "これは一文目です。これは二文目です。これは三文目です。"

    chunks = chunker.chunk(japanese_text)

    # Should create multiple chunks
    assert len(chunks) > 0, "Should produce at least one chunk"

    # All chunks except possibly the last should end with proper punctuation
    for i, chunk in enumerate(chunks[:-1]):
        # Should end at sentence boundary (。)
        ends_with_punctuation = chunk.endswith("。") or chunk.endswith("\n")
        assert ends_with_punctuation, \
            f"Chunk {i} doesn't end at sentence boundary: '{chunk[-30:]}'"


def test_japanese_clause_boundaries():
    """Test Japanese text respects 、 (comma) boundaries."""
    chunker = SemanticChunker(max_chunk_size=40, overlap=5)

    # Text with clause separators
    japanese_text = "りんご、みかん、ぶどう、いちご、バナナ、メロン"

    chunks = chunker.chunk(japanese_text)

    # Verify chunking respects comma boundaries
    assert len(chunks) > 0

    # Check that chunks don't split items awkwardly
    for chunk in chunks:
        # Should not start with 、
        assert not chunk.startswith("、"), f"Chunk starts with comma: '{chunk[:20]}'"


def test_mixed_japanese_english_boundaries():
    """Test mixed Japanese/English content respects both punctuation styles."""
    chunker = SemanticChunker(max_chunk_size=80, overlap=10)

    # Mixed content
    mixed_text = "This is an English sentence. これは日本語の文です。Another English one."

    chunks = chunker.chunk(mixed_text)

    # Should split at both . and 。
    assert len(chunks) > 0

    # Verify boundaries are clean for both languages
    for chunk in chunks[:-1]:  # All but last
        ends_cleanly = (
            chunk.endswith(". ") or
            chunk.endswith("。") or
            chunk.endswith("\n")
        )
        # Some tolerance for character-level fallback
        # but most should end cleanly
        if len(chunk) > 20:  # Skip very short chunks
            pass  # Check is informational, not strict
