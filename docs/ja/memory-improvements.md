# メモリー精度改善(v4.0.0a0)

このドキュメントでは the memory accuracy improvements implemented in Kagura AI v4.0.0a0, consisting of three phases.

## 概要

メモリーシステムは以下で大幅に強化されました:
- **Phase 1**: E5 multilingual embeddings, cross-encoder reranking, multi-dimensional recall scoring
- **Phase 2**: Hybrid search (vector + lexical) with RRF fusion
- **Phase 3**: Temporal graph for time-aware knowledge management

**期待される精度改善**: +40-60% overall

---

## フェーズ1: 基盤(埋め込み&再ランキング)

### 1.1 E5 Multilingual Embeddings

**Problem**: Previous model (`all-MiniLM-L6-v2`) only supports English.

**Solution**: Switch to `intfloat/multilingual-e5-large`
- **Languages**: 100+ languages including Japanese, Chinese, Korean
- **Dimensions**: 1024 (vs 384 previously)
- **Prefix handling**: Automatic `query:`/`passage:` prefixes

**Migration Required**:
```bash
kagura memory reindex --model intfloat/multilingual-e5-large
```

**Configuration**:
```python
from kagura.config.memory_config import EmbeddingConfig

config = EmbeddingConfig(
    model="intfloat/multilingual-e5-large",
    dimension=1024,
    use_prefix=True  # Required for E5 models
)
```

### 1.2 Cross-Encoder Reranking

**Two-stage retrieval** for improved precision:
1. **Fast bi-encoder** retrieval (100 candidates)
2. **Accurate cross-encoder** reranking (top 20)

**Usage**:
```python
from kagura.core.memory import MemoryManager

manager = MemoryManager(user_id="user_jfk", agent_name="global")

# With reranking (recommended)
results = manager.recall_semantic_with_rerank(
    query="Pythonの非同期処理について",
    top_k=20,
    candidates_k=100,
    enable_rerank=True
)
```

**Expected improvement**: +10-15% in top-result precision

### 1.3 Multi-Dimensional Recall Scoring

Inspired by **DNC/NTM** (Differentiable Neural Computer), combines:
- **Semantic similarity** (30%) - Content-based addressing
- **Recency** (20%) - Temporal decay
- **Access frequency** (15%) - Usage-based weighting
- **Graph distance** (15%) - Relational proximity
- **Importance** (20%) - User-assigned priority

**Formula**:
```
score = w_semantic * sim + w_recency * exp(-days/30) +
        w_frequency * log(count) + w_graph * 1/(1+dist) +
        w_importance * importance
```

**Configuration**:
```python
from kagura.config.memory_config import RecallScorerConfig

config = RecallScorerConfig(
    weights={
        "semantic_similarity": 0.30,
        "recency": 0.20,
        "access_frequency": 0.15,
        "graph_distance": 0.15,
        "importance": 0.20
    },
    recency_decay_days=30,
    frequency_saturation=100
)
```

---

## フェーズ2: ハイブリッド検索(ベクトル+字句)

### 2.1 BM25 Lexical Search

Traditional keyword-based search using **BM25Okapi** algorithm.

**Strengths**:
- Exact keyword matches
- Proper nouns (SnapDish, Kagura AI)
- Technical terms (asyncio, pytest)
- Japanese kanji variants

**Usage**:
```python
from kagura.core.memory.lexical_search import BM25Searcher

searcher = BM25Searcher()
searcher.index_documents([
    {"id": "doc1", "content": "Python is a programming language"},
    {"id": "doc2", "content": "FastAPI is a Python framework"},
])

results = searcher.search("Python", k=10)
```

### 2.2 RRF (Reciprocal Rank Fusion)

Combines vector + lexical results using SIGIR'09 algorithm.

**Formula**:
```
RRF(d) = Σ_s 1 / (k + rank_s(d))
```
where k=60 is the standard constant.

**Usage**:
```python
from kagura.core.memory.hybrid_search import rrf_fusion

vector_results = [{"id": "doc1", "rank": 1}, ...]
lexical_results = [{"id": "doc2", "rank": 1}, ...]

fused = rrf_fusion(vector_results, lexical_results, k=60)
```

### 2.3 Hybrid Recall

**Three-stage retrieval pipeline**:
1. Vector search (semantic)
2. Lexical search (keyword)
3. RRF fusion → Cross-encoder reranking

**Usage**:
```python
# Maximum precision (recommended for production)
results = manager.recall_hybrid(
    query="Pythonの非同期処理",
    top_k=20,
    candidates_k=100,
    enable_rerank=True
)
```

**Expected improvement**:
- Japanese queries: +10-15%
- Exact keyword matches: +20-30%

---

## フェーズ3: テンポラルGraphMemory

### 3.1 Time-Aware Knowledge Graph

Handles temporal relationships and contradictions.

**New edge attributes**:
- `valid_from`: Start of validity
- `valid_until`: End of validity (None = still valid)
- `source`: Evidence URL
- `confidence`: Confidence score (0.0-1.0)

**Usage**:
```python
from datetime import datetime
from kagura.core.graph import GraphMemory

graph = GraphMemory()

# Add nodes
graph.add_node("person_kiyota", "user")
graph.add_node("company_snapdish", "topic")

# Add temporal relationship
graph.add_edge(
    "person_kiyota",
    "company_snapdish",
    "works_on",
    valid_from=datetime(2016, 1, 1),
    valid_until=None,  # Still valid
    source="https://snapdish.co/about",
    confidence=1.0
)
```

### 3.2 Contradiction Handling

**Invalidate superseded facts**:
```python
# Old fact: "Kiyota works at OldCorp"
graph.add_edge("person_kiyota", "company_old", "works_on")

# New fact contradicts old - invalidate old edge
graph.invalidate_edge("person_kiyota", "company_old")

# Add new relationship
graph.add_edge("person_kiyota", "company_snapdish", "works_on")
```

### 3.3 Historical Reasoning

**Query past state**:
```python
# What was true in 2015?
result = graph.query_graph_temporal(
    seed_ids=["person_kiyota"],
    hops=2,
    timestamp=datetime(2015, 1, 1)
)

# Current state
result_now = graph.query_graph_temporal(["person_kiyota"], hops=2)
```

**Use cases**:
- Time-series fact tracking
- Version history
- Event timelines
- Contradiction resolution

---

## 設定

### 完全な設定例

```python
from kagura.config.memory_config import MemorySystemConfig
from kagura.core.memory import MemoryManager

# Full configuration
config = MemorySystemConfig(
    embedding=EmbeddingConfig(
        model="intfloat/multilingual-e5-large",
        dimension=1024,
        use_prefix=True
    ),
    rerank=RerankConfig(
        enabled=True,
        model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        candidates_k=100,
        top_k=20
    ),
    hybrid_search=HybridSearchConfig(
        enabled=True,
        rrf_k=60,
        candidates_k=100
    ),
    recall_scorer=RecallScorerConfig(
        weights={
            "semantic_similarity": 0.30,
            "recency": 0.20,
            "access_frequency": 0.15,
            "graph_distance": 0.15,
            "importance": 0.20
        }
    )
)

# Use configured memory
manager = MemoryManager(
    user_id="user_jfk",
    agent_name="global",
    memory_config=config
)
```

---

## パフォーマンス比較

| Method | Precision | Speed | Best For |
|--------|-----------|-------|----------|
| `recall_semantic()` | Baseline | Fast | General queries |
| `recall_semantic_with_rerank()` | +10-15% | Medium | Accuracy-critical |
| `recall_hybrid()` | +20-30% | Slower | Production use |

---

## 破壊的変更

### 必須の移行

**Re-index all memories**:
```bash
kagura memory reindex --model intfloat/multilingual-e5-large
```

**Database schema changes** (auto-migrated):
- Added `access_count` column
- Added `last_accessed_at` column

---

## テスト

Run memory tests:
```bash
# All memory tests
pytest tests/core/memory/ -v

# Specific phases
pytest tests/core/memory/test_embeddings.py          # Phase 1
pytest tests/core/memory/test_hybrid_search.py       # Phase 2
pytest tests/core/graph/test_memory.py::TestTemporal # Phase 3
```

---

## 参考文献

### 研究論文

**Phase 1 (Neural Memory)**:
- Graves et al. (2016) - Differentiable Neural Computer
- Graves et al. (2014) - Neural Turing Machine

**Phase 2 (Hybrid Search)**:
- Cormack et al. (SIGIR 2009) - Reciprocal Rank Fusion
- Robertson & Zaragoza (2009) - BM25 scoring

**Phase 3 (Temporal Knowledge)**:
- Microsoft GraphRAG (2024)
- Zep Temporal KG (2024)

### モデル

- **E5 Embeddings**: https://huggingface.co/intfloat/multilingual-e5-large
- **Cross-Encoder**: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2
- **BM25**: https://github.com/dorianbrown/rank_bm25

---

## トラブルシューティング

### Issue: Reindexing takes too long

**Solution**: Use smaller batch size
```bash
kagura memory reindex --batch-size 50
```

### Issue: Out of memory during reindexing

**Solution**: Use E5-base (smaller model)
```bash
kagura memory reindex --model intfloat/multilingual-e5-base --dimension 768
```

### Issue: BM25 not working

**Solution**: Install dependency
```bash
pip install rank-bm25
```

---

## 次のステップ

### 今後の機能拡張 (Post-v4.0.0a0)

- **LLM Query Expansion**: Automatic query variant generation
- **PGroonga Integration**: Better Japanese full-text search
- **MVD (Multi-Vector Doc)**: Multimodal memory support
- **Evaluation Benchmarks**: MIRACL-ja, LoCoMo, RULER

---

**関連Issue**:
- #418 - Memory accuracy improvements (this document)
- #417 - RAG accuracy improvements
- #348 - Neural memory research

**最終更新**: 2025-10-27
