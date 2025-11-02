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
                "rank-bm25 not installed. Install with: pip install rank-bm25"
            )

        self.corpus: list[list[str]] = []
        self.bm25: Optional["BM25Okapi"] = None
        self.doc_ids: list[str] = []
        self.doc_metadata: list[dict[str, Any]] = []

    def index_documents(self, documents: list[dict[str, Any]]) -> None:
        """Index documents for BM25 search (replaces existing index).

        Args:
            documents: List of documents with 'id' and 'content' fields

        Example:
            >>> searcher.index_documents([
            ...     {"id": "doc1", "content": "Python tutorial"},
            ...     {"id": "doc2", "content": "FastAPI guide"},
            ... ])
        """
        self.clear()
        self.add_documents(documents)

    def add_documents(self, documents: list[dict[str, Any]]) -> None:
        """Add multiple documents to the index."""
        updated = False
        for doc in documents:
            updated |= self._add_document_internal(doc)
        if updated:
            self._rebuild_index()

    def add_document(self, document: dict[str, Any]) -> None:
        """Add or update a single document in the index.

        Args:
            document: Document with at minimum an 'id' field
        """
        updated = self._add_document_internal(document)
        if updated:
            self._rebuild_index()

    def _add_document_internal(self, document: dict[str, Any]) -> bool:
        """Internal helper to add/update document without rebuilding index."""
        doc_id = document.get("id")
        if not doc_id:
            raise ValueError("document must include an 'id' field")

        content = document.get("content", "")
        tokens = self._tokenize(content)

        # Update if exists
        if doc_id in self.doc_ids:
            idx = self.doc_ids.index(doc_id)
            self.corpus[idx] = tokens
            self.doc_metadata[idx] = document
            return True

        # Add new
        self.doc_ids.append(doc_id)
        self.corpus.append(tokens)
        self.doc_metadata.append(document)
        return True

    def remove_document(self, doc_id: str) -> None:
        """Remove a document from the index by ID."""
        if doc_id in self.doc_ids:
            idx = self.doc_ids.index(doc_id)
            del self.doc_ids[idx]
            del self.corpus[idx]
            del self.doc_metadata[idx]
            self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild BM25 index from current corpus."""
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
        else:
            self.bm25 = None

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

            doc = self.doc_metadata[idx]
            result = {
                "id": self.doc_ids[idx],
                "key": doc.get("key", self.doc_ids[idx]),
                "value": doc.get("value", doc.get("content", "")),
                "content": doc.get("content", ""),
                "scope": doc.get("scope", "persistent"),
                "tags": doc.get("tags", []),
                "score": score,
                "rank": rank,
                "metadata": doc.get("metadata", {}),
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
