"""BM25 keyword search for memory retrieval.

Provides traditional keyword-based search using BM25 algorithm,
complementing semantic search for hybrid retrieval.
"""

import logging
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


class BM25Search:
    """BM25 keyword search implementation.

    Uses Okapi BM25 algorithm for keyword-based ranking without external dependencies.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """Initialize BM25 search.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus: list[dict[str, Any]] = []
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.doc_len: list[int] = []

    def tokenize(self, text: str) -> list[str]:
        """Simple tokenization.

        Args:
            text: Text to tokenize

        Returns:
            List of lowercase tokens
        """
        # Simple tokenization (can be enhanced with nltk/spacy)
        import re

        # Remove punctuation, lowercase, split
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()

        # Remove stopwords (basic list)
        stopwords = {
            "the",
            "is",
            "at",
            "which",
            "on",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "with",
            "to",
            "for",
            "of",
            "as",
            "by",
        }
        tokens = [t for t in tokens if t not in stopwords and len(t) > 1]

        return tokens

    def build_index(self, documents: list[dict[str, Any]]) -> None:
        """Build BM25 index from documents.

        Args:
            documents: List of documents with 'id' and 'content' fields
        """
        self.corpus = documents
        self.corpus_size = len(documents)

        if self.corpus_size == 0:
            logger.warning("BM25: Empty corpus, index not built")
            return

        # Tokenize all documents
        tokenized_corpus = []
        doc_freqs: dict[str, int] = {}

        for doc in documents:
            content = doc.get("content", "") or doc.get("value", "")
            tokens = self.tokenize(str(content))
            tokenized_corpus.append(tokens)
            self.doc_len.append(len(tokens))

            # Count document frequency
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freqs[token] = doc_freqs.get(token, 0) + 1

        # Calculate average document length
        self.avgdl = sum(self.doc_len) / self.corpus_size if self.corpus_size > 0 else 0

        # Calculate IDF
        self.doc_freqs = doc_freqs
        for token, freq in doc_freqs.items():
            self.idf[token] = self._calculate_idf(freq)

        self.tokenized_corpus = tokenized_corpus

        logger.info(
            f"BM25 index built: {self.corpus_size} docs, "
            f"avgdl={self.avgdl:.1f}, vocab={len(self.idf)}"
        )

    def _calculate_idf(self, doc_freq: int) -> float:
        """Calculate IDF score.

        Args:
            doc_freq: Number of documents containing the term

        Returns:
            IDF score
        """
        import math

        # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
        idf = math.log((self.corpus_size - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
        return idf

    def search(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """Search using BM25 ranking.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Top-k documents ranked by BM25 score
        """
        if not self.corpus:
            logger.warning("BM25: Corpus is empty, returning no results")
            return []

        query_tokens = self.tokenize(query)

        if not query_tokens:
            logger.warning(f"BM25: Query '{query}' produced no tokens")
            return []

        # Calculate BM25 scores for all documents
        scores = []
        for idx, (doc, tokens) in enumerate(zip(self.corpus, self.tokenized_corpus)):
            score = self._calculate_bm25_score(query_tokens, tokens, idx)
            scores.append((score, idx, doc))

        # Sort by score (descending)
        scores.sort(reverse=True, key=lambda x: x[0])

        # Return top-k with scores
        results = []
        for score, idx, doc in scores[:k]:
            if score > 0:  # Only return documents with non-zero score
                result = doc.copy()
                result["bm25_score"] = score
                results.append(result)

        logger.info(f"BM25 search: query='{query}', found={len(results)}/{k}")
        return results

    def _calculate_bm25_score(
        self, query_tokens: list[str], doc_tokens: list[str], doc_idx: int
    ) -> float:
        """Calculate BM25 score for a document.

        Args:
            query_tokens: Tokenized query
            doc_tokens: Tokenized document
            doc_idx: Document index

        Returns:
            BM25 score
        """
        score = 0.0
        doc_len = self.doc_len[doc_idx]

        # Term frequency in document
        term_freqs = Counter(doc_tokens)

        for token in query_tokens:
            if token not in self.idf:
                continue

            tf = term_freqs.get(token, 0)
            idf = self.idf[token]

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))

            score += idf * (numerator / denominator)

        return score
