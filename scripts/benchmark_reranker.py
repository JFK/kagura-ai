#!/usr/bin/env python3
"""Benchmark reranker models: BGE-reranker-v2-m3 vs ms-marco-MiniLM-L-6-v2.

Measures:
- Precision: MRR (Mean Reciprocal Rank), nDCG@10
- Latency: Average reranking time for 100 candidates
- Model comparison: BGE vs ms-marco

Usage:
    python scripts/benchmark_reranker.py
"""

from __future__ import annotations

import time
from typing import Any

# Golden dataset: query-document pairs for testing
# Format: (query, relevant_docs, irrelevant_docs)
GOLDEN_DATASET = [
    # Coding queries
    (
        "How to implement memory search in Python?",
        [
            "Python memory search implementation using ChromaDB",
            "Vector search with sentence transformers in Python",
            "RAG system implementation guide for Python developers",
        ],
        [
            "Java memory management best practices",
            "JavaScript array search methods",
            "C++ STL map operations",
        ],
    ),
    (
        "What is cross-encoder reranking?",
        [
            "Cross-encoder reranking improves search precision by scoring query-document pairs",
            "Two-stage retrieval: bi-encoder for candidates, cross-encoder for reranking",
            "MS MARCO cross-encoder models for semantic search",
        ],
        [
            "BERT encoder architecture explained",
            "Natural language processing basics",
            "TF-IDF vs BM25 comparison",
        ],
    ),
    (
        "How to use async/await in Python?",
        [
            "Python asyncio tutorial for asynchronous programming",
            "async def and await keywords in Python 3.11",
            "FastAPI async endpoint implementation guide",
        ],
        [
            "JavaScript Promise.then() vs async/await",
            "Node.js event loop explained",
            "Go goroutines concurrency patterns",
        ],
    ),
    # Documentation queries
    (
        "What are the benefits of RAG systems?",
        [
            "RAG (Retrieval Augmented Generation) combines retrieval with LLMs for accurate responses",
            "Benefits of RAG: reduces hallucinations, provides citations, scales with knowledge base",
            "RAG vs fine-tuning: when to use retrieval over training",
        ],
        [
            "GPT-4 capabilities overview",
            "Fine-tuning BERT for classification",
            "Vector database comparison guide",
        ],
    ),
    (
        "How to configure ChromaDB?",
        [
            "ChromaDB configuration: collection creation, metadata filtering, distance metrics",
            "ChromaDB Python client setup and initialization",
            "Setting up persistent storage for ChromaDB embeddings",
        ],
        [
            "PostgreSQL database configuration",
            "MongoDB replica set setup",
            "Redis cache configuration options",
        ],
    ),
    # General knowledge
    (
        "What is machine learning?",
        [
            "Machine learning is a subset of AI that learns from data without explicit programming",
            "ML algorithms: supervised learning, unsupervised learning, reinforcement learning",
            "Machine learning applications in real-world systems",
        ],
        [
            "Deep learning neural networks explained",
            "Statistics fundamentals for data science",
            "Linear algebra for ML engineers",
        ],
    ),
    (
        "How does semantic search work?",
        [
            "Semantic search uses embeddings to find conceptually similar documents",
            "Bi-encoder architecture: encode query and documents separately, compute similarity",
            "Sentence transformers for semantic search implementation",
        ],
        [
            "Full-text search with Elasticsearch",
            "SQL LIKE operator for pattern matching",
            "Regular expressions tutorial",
        ],
    ),
    # Multilingual queries (testing BGE's multilingual strength)
    (
        "日本語の自然言語処理",
        [
            "日本語NLPのための形態素解析ツール MeCab",
            "BERT日本語モデルによるテキスト分類",
            "日本語ベクトル検索の実装方法",
        ],
        [
            "English NLP with spaCy",
            "Chinese word segmentation techniques",
            "Korean tokenization with KoNLPy",
        ],
    ),
    (
        "中文语义搜索实现",
        [
            "中文文本向量化与语义检索",
            "BERT中文模型在搜索中的应用",
            "中文分词与语义相似度计算",
        ],
        [
            "English semantic search with FAISS",
            "Japanese text similarity comparison",
            "Spanish language models overview",
        ],
    ),
    (
        "Python testing best practices",
        [
            "pytest fixtures and parametrization guide",
            "Test-driven development with Python unittest",
            "Mock objects and dependency injection in Python tests",
        ],
        [
            "Java JUnit testing framework",
            "JavaScript Jest testing library",
            "Ruby RSpec behavior-driven development",
        ],
    ),
]


def calculate_mrr(rankings: list[list[int]]) -> float:
    """Calculate Mean Reciprocal Rank.

    Args:
        rankings: List of lists, each containing ranks of relevant documents
                  (rank 1 = first position, 0 = not in results)

    Returns:
        MRR score (0.0 to 1.0)
    """
    reciprocal_ranks = []
    for ranking in rankings:
        if ranking:  # Has relevant documents
            # Find first relevant document's rank
            first_relevant_rank = min([r for r in ranking if r > 0])
            reciprocal_ranks.append(1.0 / first_relevant_rank)
        else:
            reciprocal_ranks.append(0.0)

    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


def calculate_ndcg(rankings: list[list[int]], k: int = 10) -> float:
    """Calculate Normalized Discounted Cumulative Gain at K.

    Args:
        rankings: List of lists, each containing ranks of relevant documents
        k: Cutoff for nDCG@K calculation

    Returns:
        nDCG@K score (0.0 to 1.0)
    """
    import math

    ndcg_scores = []
    for ranking in rankings:
        # DCG: sum of (relevance / log2(rank + 1))
        # For binary relevance: relevant=1, irrelevant=0
        dcg = sum(1.0 / math.log2(rank + 1) for rank in ranking if 0 < rank <= k)

        # IDCG: perfect ranking (all relevant docs at top)
        num_relevant = len([r for r in ranking if r > 0])
        idcg = sum(1.0 / math.log2(i + 2) for i in range(min(num_relevant, k)))

        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcg_scores.append(ndcg)

    return sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0


def benchmark_model(model_name: str) -> dict[str, Any]:
    """Benchmark a single reranker model.

    Args:
        model_name: Model identifier (e.g., "BAAI/bge-reranker-v2-m3")

    Returns:
        Dict with metrics: MRR, nDCG@10, avg_latency_ms
    """
    from kagura.config.memory_config import RerankConfig
    from kagura.core.memory.reranker import MemoryReranker

    print(f"\n{'='*70}")
    print(f"Benchmarking: {model_name}")
    print(f"{'='*70}")

    # Initialize reranker
    config = RerankConfig(model=model_name, candidates_k=100, top_k=10)
    reranker = MemoryReranker(config)

    rankings_list = []
    latencies = []

    for i, (query, relevant_docs, irrelevant_docs) in enumerate(GOLDEN_DATASET, 1):
        # Prepare candidates (mix relevant and irrelevant)
        candidates = [
            {"content": doc, "distance": 0.5} for doc in relevant_docs + irrelevant_docs
        ]

        # Measure latency
        start_time = time.perf_counter()
        reranked = reranker.rerank(query, candidates, top_k=10)
        latency_ms = (time.perf_counter() - start_time) * 1000
        latencies.append(latency_ms)

        # Calculate rankings for relevant documents
        rankings = []
        for rel_doc in relevant_docs:
            try:
                rank = next(
                    idx + 1
                    for idx, r in enumerate(reranked)
                    if r["content"] == rel_doc
                )
                rankings.append(rank)
            except StopIteration:
                rankings.append(0)  # Not in top-k results

        rankings_list.append(rankings)

        # Print progress
        print(f"  Query {i}/{len(GOLDEN_DATASET)}: {latency_ms:.1f}ms | "
              f"Relevant in top-10: {sum(1 for r in rankings if 0 < r <= 10)}/{len(relevant_docs)}")

    # Calculate metrics
    mrr = calculate_mrr(rankings_list)
    ndcg_10 = calculate_ndcg(rankings_list, k=10)
    avg_latency = sum(latencies) / len(latencies)

    print(f"\n📊 Results:")
    print(f"  MRR:            {mrr:.4f}")
    print(f"  nDCG@10:        {ndcg_10:.4f}")
    print(f"  Avg Latency:    {avg_latency:.1f} ms")
    print(f"  Total Latency:  {sum(latencies):.1f} ms")

    return {
        "model": model_name,
        "mrr": mrr,
        "ndcg_10": ndcg_10,
        "avg_latency_ms": avg_latency,
        "total_latency_ms": sum(latencies),
    }


def main() -> None:
    """Run benchmark comparison."""
    print("🚀 Reranker Benchmark: BGE vs MS-MARCO")
    print(f"Dataset size: {len(GOLDEN_DATASET)} queries")
    print("Metrics: MRR, nDCG@10, Latency")

    try:
        # Benchmark BGE reranker
        bge_results = benchmark_model("BAAI/bge-reranker-v2-m3")

        # Benchmark ms-marco for comparison
        msmarco_results = benchmark_model("cross-encoder/ms-marco-MiniLM-L-6-v2")

        # Print comparison
        print(f"\n{'='*70}")
        print("📈 COMPARISON: BGE vs MS-MARCO")
        print(f"{'='*70}")

        # Guard against division by zero
        if msmarco_results["mrr"] != 0:
            mrr_improvement = ((bge_results["mrr"] - msmarco_results["mrr"])
                              / msmarco_results["mrr"] * 100)
        else:
            mrr_improvement = None

        if msmarco_results["ndcg_10"] != 0:
            ndcg_improvement = ((bge_results["ndcg_10"] - msmarco_results["ndcg_10"])
                               / msmarco_results["ndcg_10"] * 100)
        else:
            ndcg_improvement = None

        latency_increase = bge_results["avg_latency_ms"] - msmarco_results["avg_latency_ms"]

        print(f"\nMRR:")
        print(f"  BGE:         {bge_results['mrr']:.4f}")
        print(f"  MS-MARCO:    {msmarco_results['mrr']:.4f}")
        if mrr_improvement is not None:
            print(f"  Improvement: {mrr_improvement:+.1f}%")
        else:
            print("  Improvement: undefined (MS-MARCO MRR is zero)")

        print(f"\nnDCG@10:")
        print(f"  BGE:         {bge_results['ndcg_10']:.4f}")
        print(f"  MS-MARCO:    {msmarco_results['ndcg_10']:.4f}")
        if ndcg_improvement is not None:
            print(f"  Improvement: {ndcg_improvement:+.1f}%")
        else:
            print("  Improvement: undefined (MS-MARCO nDCG@10 is zero)")

        print(f"\nLatency:")
        print(f"  BGE:         {bge_results['avg_latency_ms']:.1f} ms")
        print(f"  MS-MARCO:    {msmarco_results['avg_latency_ms']:.1f} ms")
        if msmarco_results["avg_latency_ms"] != 0:
            latency_pct = latency_increase / msmarco_results["avg_latency_ms"] * 100
            print(f"  Increase:    {latency_increase:+.1f} ms ({latency_pct:+.1f}%)")
        else:
            print(f"  Increase:    {latency_increase:+.1f} ms (undefined %)")

        # Verdict
        print(f"\n{'='*70}")
        print("🎯 VERDICT:")
        print(f"{'='*70}")

        # Handle None values (division by zero cases)
        mrr_imp = mrr_improvement if mrr_improvement is not None else 0.0
        ndcg_imp = ndcg_improvement if ndcg_improvement is not None else 0.0

        if mrr_imp >= 3.0 or ndcg_imp >= 3.0:
            print("✅ BGE reranker provides significant precision improvement!")
            print(f"   Expected gain matches target: +5-8% precision")
        elif mrr_imp >= 1.0 or ndcg_imp >= 1.0:
            print("⚠️  BGE reranker provides modest precision improvement")
            print("   Consider if latency tradeoff is acceptable")
        else:
            print("❌ BGE reranker does not provide expected precision improvement")
            print("   May want to reconsider the upgrade")

        if latency_increase > 100:
            print(f"\n⚠️  Warning: Latency increase is significant (+{latency_increase:.0f}ms)")
            print("   Ensure this is acceptable for your use case")
        elif latency_increase > 50:
            print(f"\n✅ Latency increase is moderate (+{latency_increase:.0f}ms)")
        else:
            print(f"\n✅ Latency increase is minimal (+{latency_increase:.0f}ms)")

    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
