"""Semantic chunking for documents and long texts.

Splits texts into semantically coherent chunks while preserving context.
Uses langchain's RecursiveCharacterTextSplitter for intelligent boundary detection.

Benefits:
- Preserves semantic coherence (doesn't split mid-sentence or mid-thought)
- Better context retention with configurable overlap
- Improves RAG precision for long documents
- Maintains chunk metadata for reconstruction

Example:
    >>> chunker = SemanticChunker(max_chunk_size=512, overlap=50)
    >>> chunks = chunker.chunk("Very long document...")
    >>> print(len(chunks))  # Multiple semantically coherent chunks
    3
    >>> chunks_with_metadata = chunker.chunk_with_metadata("Long text...", source="doc.txt")
    >>> print(chunks_with_metadata[0]["chunk_index"])
    0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    # Type stub for optional dependency
    # Actual import happens at runtime in try-except blocks
    from typing import Any as RecursiveCharacterTextSplitter  # type: ignore


@dataclass
class ChunkMetadata:
    """Metadata for a single chunk.

    Attributes:
        chunk_index: Position of this chunk in the sequence (0-indexed)
        total_chunks: Total number of chunks in the document
        source: Source identifier (file path, URL, etc.)
        start_char: APPROXIMATE character position where this chunk starts
        end_char: APPROXIMATE character position where this chunk ends
        content: The actual chunk text

    Warning:
        start_char and end_char are APPROXIMATIONS when overlap > 0.
        RecursiveCharacterTextSplitter doesn't track original indices,
        so positions are calculated heuristically.

        For accurate document reconstruction:
        - Sort chunks by chunk_index (not by start_char)
        - Concatenate chunk.content in order
        - Do NOT use start_char/end_char for slicing original text
    """

    chunk_index: int
    total_chunks: int
    source: str
    start_char: int
    end_char: int
    content: str


class SemanticChunker:
    """Semantic boundary-aware text chunker for RAG systems.

    Splits long texts into smaller chunks while respecting semantic boundaries
    (paragraphs, sentences, phrases). Uses LangChain's RecursiveCharacterTextSplitter
    with intelligent separators.

    Attributes:
        max_chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
        separators: List of separators in priority order (default: paragraph > sentence > word)
        splitter: RecursiveCharacterTextSplitter instance
    """

    def __init__(
        self,
        max_chunk_size: int = 512,
        overlap: int = 50,
        separators: Optional[list[str]] = None,
    ):
        """Initialize semantic chunker.

        Args:
            max_chunk_size: Maximum characters per chunk (default: 512)
            overlap: Number of characters to overlap between chunks (default: 50)
            separators: Custom separators in priority order
                        (default: ["\n\n", "\n", ". ", " ", ""])

        Raises:
            ImportError: If langchain-text-splitters is not installed
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.separators = separators or [
            "\n\n",  # Paragraph breaks (highest priority)
            "\n",  # Line breaks
            ". ",  # Sentence endings
            ", ",  # Clause separators
            " ",  # Word boundaries
            "",  # Character-level (last resort)
        ]

        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
        except ImportError as e:
            raise ImportError(
                "langchain-text-splitters not installed. "
                "Install with: pip install langchain-text-splitters"
            ) from e

        self.splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(  # type: ignore
            chunk_size=self.max_chunk_size,
            chunk_overlap=self.overlap,
            length_function=len,
            separators=self.separators,
            is_separator_regex=False,
        )

    def chunk(self, text: str) -> list[str]:
        """Split text into semantically coherent chunks.

        Args:
            text: Input text to split

        Returns:
            List of chunk strings

        Example:
            >>> chunker = SemanticChunker(max_chunk_size=100, overlap=20)
            >>> text = "Paragraph 1.\\n\\nParagraph 2.\\n\\nParagraph 3."
            >>> chunks = chunker.chunk(text)
            >>> len(chunks)  # Depends on text length
            2
        """
        if not text or not text.strip():
            return []

        # LangChain's RecursiveCharacterTextSplitter handles the splitting
        chunks = self.splitter.split_text(text)
        return chunks

    def chunk_with_metadata(
        self, text: str, source: str = "unknown"
    ) -> list[ChunkMetadata]:
        """Split text and return chunks with metadata.

        Includes chunk position, source, and character offsets for reconstruction.

        Args:
            text: Input text to split
            source: Source identifier (file path, URL, document ID, etc.)

        Returns:
            List of ChunkMetadata objects with content and metadata

        Example:
            >>> chunker = SemanticChunker()
            >>> chunks = chunker.chunk_with_metadata("Long document...", source="doc.pdf")
            >>> print(chunks[0].chunk_index, chunks[0].source)
            0 doc.pdf
        """
        # Split text into chunks (chunk() handles validation)
        chunk_strings = self.chunk(text)
        if not chunk_strings:
            return []

        total_chunks = len(chunk_strings)

        # Build metadata for each chunk
        chunk_metadata_list = []
        current_pos = 0

        for idx, chunk_content in enumerate(chunk_strings):
            # Find chunk position in original text
            # Note: This is approximate due to overlap
            start_char = current_pos
            end_char = start_char + len(chunk_content)

            chunk_metadata = ChunkMetadata(
                chunk_index=idx,
                total_chunks=total_chunks,
                source=source,
                start_char=start_char,
                end_char=end_char,
                content=chunk_content,
            )
            chunk_metadata_list.append(chunk_metadata)

            # Move position forward (accounting for overlap)
            # Overlap means next chunk starts before current chunk ends
            current_pos += len(chunk_content) - self.overlap

        return chunk_metadata_list

    def __repr__(self) -> str:
        """String representation of chunker."""
        return (
            f"SemanticChunker(max_chunk_size={self.max_chunk_size}, "
            f"overlap={self.overlap}, separators={len(self.separators)})"
        )


def is_chunking_available() -> bool:
    """Check if semantic chunking is available (langchain-text-splitters installed).

    Returns:
        True if langchain-text-splitters is installed, False otherwise
    """
    try:
        import langchain_text_splitters  # type: ignore  # noqa: F401

        return True
    except ImportError:
        return False
