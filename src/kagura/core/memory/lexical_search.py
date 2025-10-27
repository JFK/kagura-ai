"""Lexical (keyword-based) search using BM25 algorithm.

Provides exact and partial keyword matching to complement vector search.
Particularly effective for:
- Exact keyword matches
- Proper nouns (names, places)
- Technical terms and code
- Japanese text with kanji variants

Uses BM25 (Best Matching 25) algorithm, the standard for text retrieval.

Example:
    >>> searcher = BM25Searcher()
    >>> searcher.index_documents([
    ...     {"id": "doc1", "content": "Python is a programming language"},
    ...     {"id": "doc2", "content": "FastAPI is a Python web framework"},
    ... ])
    >>> results = searcher.search("Python", k=10)
"""

from typing import Any, Optional

try:
    from rank_bm25 import BM25Okapi

    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False


class BM25Searcher:
    """BM25-based lexical search for keyword matching.

    Provides traditional information retrieval using BM25 scoring.
    Best used in combination with vector search (hybrid search).

    Attributes:
        corpus: List of tokenized documents
        bm25: BM25Okapi instance for scoring
        doc_ids: Document IDs corresponding to corpus
        doc_metadata: Metadata for each document
    """

    def __init__(self):
        """Initialize BM25 searcher.

        Raises:
            ImportError: If rank-bm25 is not installed
        """
        if not BM25_AVAILABLE:
            raise ImportError(
                "rank-bm25 not installed. "
                "Install with: pip install rank-bm25"
            )

        self.corpus: list[list[str]] = []
        self.bm25: Optional["BM25Okapi"] = None
        self.doc_ids: list[str] = []
        self.doc_metadata: list[dict[str, Any]] = []

    def index_documents(self, documents: list[dict[str, Any]]) -> None:
        """Index documents for BM25 search.

        Args:
            documents: List of documents with 'id' and 'content' fields

        Example:
            >>> searcher.index_documents([
            ...     {"id": "doc1", "content": "Python tutorial"},
            ...     {"id": "doc2", "content": "FastAPI guide"},
            ... ])
        """
        self.corpus = []
        self.doc_ids = []
        self.doc_metadata = []

        for doc in documents:
            content = doc.get("content", "")
            # Simple tokenization (split by whitespace)
            # TODO: Use better tokenizer for Japanese (e.g., MeCab, Sudachi)
            tokens = self._tokenize(content)

            self.corpus.append(tokens)
            self.doc_ids.append(doc["id"])
            self.doc_metadata.append(doc)

        # Build BM25 index
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)

    def search(
        self,
        query: str,
        k: int = 10,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search documents using BM25 scoring.

        Args:
            query: Search query
            k: Number of results to return
            min_score: Minimum BM25 score threshold (default: 0.0)

        Returns:
            List of results with id, content, score, and rank

        Example:
            >>> results = searcher.search("Python async", k=5)
            >>> print(results[0])
            {'id': 'doc1', 'content': '...', 'score': 2.5, 'rank': 1}
        """
        if not self.bm25 or not self.corpus:
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:k]

        # Build results
        results = []
        for rank, idx in enumerate(top_indices, start=1):
            score = float(scores[idx])

            # Filter by minimum score
            if score < min_score:
                continue

            result = {
                "id": self.doc_ids[idx],
                "content": self.doc_metadata[idx].get("content", ""),
                "score": score,
                "rank": rank,
                "metadata": self.doc_metadata[idx],
            }
            results.append(result)

        return results

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words.

        Simple whitespace tokenization for now.
        TODO: Use proper tokenizers for better results:
        - English: NLTK, spaCy
        - Japanese: MeCab, Sudachi
        - Multilingual: SentencePiece

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Lowercase and split by whitespace
        return text.lower().split()

    def count(self) -> int:
        """Get number of indexed documents.

        Returns:
            Number of documents
        """
        return len(self.doc_ids)

    def clear(self) -> None:
        """Clear all indexed documents."""
        self.corpus = []
        self.bm25 = None
        self.doc_ids = []
        self.doc_metadata = []

    def __repr__(self) -> str:
        """String representation."""
        return f"BM25Searcher(documents={self.count()})"
