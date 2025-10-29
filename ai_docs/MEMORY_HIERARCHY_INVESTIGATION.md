# Memory Management & Hierarchy Investigation - Kagura AI v4.0

**Investigation Date**: October 29, 2025  
**Codebase**: kagura-ai (v4.0 Phase C Complete)  
**Focus**: Memory hierarchy, priority mechanisms, and escalation systems

---

## Executive Summary

Kagura AI v4.0 has a sophisticated 4-tier memory system with emerging importance/priority mechanisms but lacks a comprehensive hierarchical escalation system. The codebase shows strong architectural foundations for a memory hierarchy but needs design and implementation work on:

1. **Hot/Cold Tier Management** - Temperature-based memory classification
2. **Automatic Escalation** - Moving memories between tiers based on importance
3. **Retention Policies** - Tier-specific rules for preservation and archival
4. **Priority-based Access** - Hot vs. Cold retrieval strategies

---

## 1. Issue #429 - Smart Forgetting & Auto-maintenance

**Status**: OPEN  
**Priority**: High  
**Target**: v4.0.0

### Current Implementation Status

**Implemented**:
- ✅ `RecallScorer` - Multi-dimensional scoring (Phase 1 Complete)
  - Semantic similarity (0.3 weight)
  - Recency decay (0.2 weight)
  - Access frequency (0.15 weight)
  - Graph distance (0.15 weight)
  - Importance/priority (0.2 weight)
- ✅ `access_count` and `last_accessed_at` tracking in SQLite schema
- ✅ Importance field in API models (0.0-1.0)
- ✅ Metadata support for tags and custom attributes
- ✅ GraphMemory integration (Phase B Complete)

**Not Implemented**:
- ❌ `auto_forget_low_score_memories()` method
- ❌ Automatic importance updates based on usage (Hebbian learning)
- ❌ `MemoryMaintenanceTask` background service
- ❌ Grace period enforcement for auto-deletion
- ❌ Integration of RecallScorer into recall() method

### Key Code Location

**RecallScorer Implementation**:  
`/home/jfk/works/kagura-ai/src/kagura/core/memory/recall_scorer.py` (246 lines)

```python
def compute_score(
    self,
    semantic_sim: float,          # 0.0-1.0
    created_at: datetime,
    last_accessed: Optional[datetime] = None,
    access_count: int = 0,
    graph_distance: Optional[int] = None,
    importance: float = 0.5,      # User-assigned or auto-updated
) -> float:
    """Returns composite score (0.0-1.0, higher is better)"""
```

**Configuration**:  
`/home/jfk/works/kagura-ai/src/kagura/config/memory_config.py`

```python
class RecallScorerConfig(BaseModel):
    weights: dict[str, float] = {
        "semantic_similarity": 0.30,
        "recency": 0.20,
        "access_frequency": 0.15,
        "graph_distance": 0.15,
        "importance": 0.20,
    }
    recency_decay_days: int = 30
    frequency_saturation: int = 100
```

---

## 2. Related Memory Issues Overview

### Open Issues (High Priority)

| Issue | Title | Status | Target | Relates To |
|-------|-------|--------|--------|-----------|
| #429 | Smart Forgetting & Auto-maintenance | OPEN | v4.0.0 | Hierarchy |
| #430 | Auto-save & Auto-recall Intelligence | OPEN | v4.0.0 | Escalation |
| #397 | Memory Curator - AI-Driven Memory Management | OPEN | v4.1.0-v4.3.0 | Future |
| #441 | Smart memory summarization with in-tool LLM | OPEN | v4.1.0 | Optimization |
| #411 | Enhance memory_stats with unused tracking | OPEN | v4.1.0 | Cleanup |
| #435 | Hybrid storage with Redis caching | OPEN | v4.0.0+ | Hot/Cold |
| #437 | Migrate RAG from ChromaDB to Qdrant | OPEN | v4.0.0+ | Scaling |
| #438 | Redis-backed distributed caching | OPEN | v4.0.0+ | Hot/Cold |

### Closed (Recently Completed)

| Issue | Title | Status | Date |
|-------|-------|--------|------|
| #382 | Add user_id to all memory ops | CLOSED | 2025-10-26 |
| #345 | GraphDB integration for relationships | CLOSED | 2025-10-26 |
| #418 | Memory accuracy improvements Phase 1 | CLOSED | 2025-10-27 |
| #396 | Add memory_stats analysis tool | CLOSED | 2025-10-27 |

---

## 3. Current Memory Architecture (4-Tier)

### Tier 1: Working Memory (In-Memory, Hot)
```
Location: src/kagura/core/memory/working.py
Storage: Python dict (ephemeral)
Scope: Session-scoped
Features:
  - Instant access (<1ms)
  - Zero persistence
  - Automatic cleanup on session end
  - Used for: Temporary calculations, context variables
```

### Tier 2: Context Memory (In-Memory, Warm)
```
Location: src/kagura/core/memory/context.py
Storage: Message list (in-memory)
Features:
  - Conversation history
  - Automatic summarization
  - Configurable max messages
  - Used for: Recent conversation context
```

### Tier 3: Persistent Memory (SQLite, Cold)
```
Location: src/kagura/core/memory/persistent.py
Storage: SQLite database (~500KB per 1000 entries)
Features:
  - Long-term storage
  - user_id scoped (Phase C complete)
  - Indexed queries (key, agent, user)
  - Metadata: importance, tags, custom
  - Access tracking: access_count, last_accessed_at
  - Schema: id, key, value, user_id, agent_name, 
            created_at, updated_at, metadata, 
            access_count, last_accessed_at
```

### Tier 4: Semantic Search (ChromaDB/Qdrant, Warm)
```
Location: src/kagura/core/memory/rag.py
Storage: Vector embeddings
Features:
  - Semantic similarity search
  - E5-Large embeddings (1024-dim)
  - Working + Persistent RAG (dual collections)
  - Supports hybrid search (vector + lexical)
```

### Bonus Tier: Graph Relationships (NetworkX, Metadata)
```
Location: src/kagura/core/graph/memory.py
Storage: JSON file (~2MB per 10K nodes)
Features:
  - Typed nodes: memory, user, topic, interaction
  - Weighted edges: related_to, depends_on, learned_from
  - Temporal validity: valid_from/valid_until
  - Confidence scores (0.0-1.0)
  - Pattern analysis for user interactions
```

---

## 4. Existing Importance/Priority Mechanisms

### A. RecallScorer (Primary)

**Multi-dimensional scoring** inspired by DNC/NTM:

1. **Semantic Similarity** (weight: 0.30)
   - Cosine distance to query embedding
   - Range: 0.0-1.0

2. **Recency** (weight: 0.20)
   - Exponential decay: `exp(-days_elapsed / decay_days)`
   - Default: 30-day decay (63% decay after 30 days)
   - Formula: `s_recency = e^(-t/τ)` where τ=30

3. **Access Frequency** (weight: 0.15)
   - Log-scaled: `log(1 + count) / log(1 + saturation)`
   - Saturation at 100 accesses
   - Prevents frequency from dominating score

4. **Graph Distance** (weight: 0.15)
   - Inverse distance: `1 / (1 + distance)`
   - Closer nodes score higher
   - None if not in graph → 0.0

5. **Importance** (weight: 0.20)
   - User-assigned (0.0-1.0)
   - Currently static, not auto-updated
   - **GAP**: No Hebbian learning yet

### B. Access Tracking

**Database columns**:
```sql
access_count INTEGER DEFAULT 0        -- Incremented on recall()
last_accessed_at TIMESTAMP            -- Updated on recall()
```

**Current limitation**: Tracking exists but `recall()` method doesn't automatically update importance based on access patterns.

### C. Metadata & Tags System

**MemoryCreate model** (API):
```python
tags: list[str]                    # Categorical tags
importance: float (0.0-1.0)        # Priority indicator
metadata: dict[str, Any]           # Custom attributes
```

**Example metadata**:
```json
{
  "type": "auto_saved_decision",
  "source": "auto_saver",
  "category": "config_change",
  "tags": ["decision", "important", "user_preference"],
  "importance": 0.9,
  "auto_save_confidence": 0.85
}
```

### D. Graph-Based Importance

**Graph Memory advantages**:
- **Node centrality** - Well-connected memories are more important
- **Temporal validity** - Edges have `valid_from`/`valid_until`
- **Confidence scoring** - Edges have `confidence` (0.0-1.0)
- **Evidence tracking** - `source` field for relationship provenance

**Not implemented**: Graph centrality NOT integrated into RecallScorer yet (Issue #429 mentions this TODO).

---

## 5. Gaps in Current Implementation

### Gap 1: No Hot/Cold Tier System

**Missing**:
- ❌ "Hot" tier for frequently-accessed memories
- ❌ "Cold" tier for archived/infrequently-used memories
- ❌ Automatic tier promotion/demotion
- ❌ Tier-specific retention policies

**Impact**: 
- All persistent memories treated equally in SQLite
- No optimization for hot-path vs. cold-path access
- No archival/compression mechanism

### Gap 2: No Automatic Escalation

**Missing**:
- ❌ Score-based memory promotion (e.g., low-score → archival)
- ❌ Access-frequency-based escalation (hot memories → cache)
- ❌ Time-based escalation (time-sensitive memories → hot)
- ❌ Configurable escalation thresholds

**Impact**:
- Issue #429 explicitly mentions this as unimplemented
- No automatic "forgetting" of low-score memories
- No grace period enforcement before deletion

### Gap 3: No Retention Policies

**Missing**:
- ❌ Per-tier retention rules
- ❌ Automatic archival based on age/score
- ❌ Category-based retention (e.g., decisions kept forever)
- ❌ Cleanup policies

**Impact**:
- Database growth unbounded
- No mechanism to prune old memories
- Manual pruning only (Issue #429: `prune()` method exists but not auto-invoked)

### Gap 4: Incomplete Importance Auto-Update

**Missing**:
- ❌ Hebbian learning (usage → importance increase)
- ❌ Decay (non-usage → importance decrease)
- ❌ Integration of RecallScorer into `recall()` method
- ❌ Automatic importance adjustment based on graph context

**Current State**:
```python
# RecallScorer exists and computes scores
score = recall_scorer.compute_score(
    semantic_sim=0.85,
    created_at=datetime.now() - timedelta(days=7),
    last_accessed=datetime.now() - timedelta(days=1),
    access_count=5,
    graph_distance=2,
    importance=0.8  # ← STATIC, not auto-updated
)

# But recall() doesn't update importance based on score
def recall(self, key: str, user_id: str) -> Optional[Any]:
    # Updates access_count and last_accessed_at
    # ← But does NOT update importance field
    pass
```

### Gap 5: No Redis Caching Layer

**Missing** (Issues #435, #438):
- ❌ Redis for hot-memory caching
- ❌ Cache coherence with SQLite
- ❌ LRU eviction for cache overflow
- ❌ Distributed caching for cloud deployments

**Current State**:
- Direct SQLite access for all persistent queries
- No intermediate cache layer
- No distinction between in-memory working and long-lived hot

### Gap 6: No Automatic Maintenance Task

**Missing**:
- ❌ `MemoryMaintenanceTask` (mentioned in Issue #429)
- ❌ Background job for periodic cleanup
- ❌ Scheduled archival/deletion
- ❌ Graph optimization

**Proposed in Issue #429**:
```python
class MemoryMaintenanceTask:
    async def _run_maintenance(self):
        # 1. Auto-forgetting low-score memories
        deleted = await self.memory.auto_forget_low_score_memories()
        # 2. Graph cleanup
        # 3. RAG index optimization
```

---

## 6. Recommendations for Memory Hierarchy Design

### Recommendation 1: Implement Tiered Temperature Model

**Design**: Add temperature-based tiers to Persistent Memory

```
Level      Name         Retention    Access Speed   Example
─────────────────────────────────────────────────────────
4 (Hot)    Hot Cache    Hours        <1ms (Redis)   Frequently used configs
3 (Warm)   Active       Days         <10ms (SQLite) Current project info
2 (Cool)   Archive      Months       <100ms (slow)  Old decisions
1 (Cold)   Frozen       Years        Offline        Historical data
```

**Implementation**:
- Add `temperature: Literal["hot", "warm", "cool", "cold"]` to metadata
- Move hot memories to Redis (Issue #435)
- Archive cool/cold to separate SQLite table or file
- Configure retention per temperature

### Recommendation 2: Auto-Escalation Based on Importance Score

**Design**: Automatic tier promotion/demotion

```python
async def auto_escalate_by_score(user_id: str):
    """Promote/demote memories based on recall score"""
    
    thresholds = {
        "cold_to_cool": 0.3,    # Score 0.3+ → archival
        "cool_to_warm": 0.5,    # Score 0.5+ → active
        "warm_to_hot": 0.8,     # Score 0.8+ → cache
    }
    
    for memory in all_memories(user_id):
        score = recall_scorer.compute_score(...)
        current_temp = memory.get("temperature", "warm")
        
        # Promotion
        if score >= 0.8 and current_temp != "hot":
            promote_to_hot(memory)  # → Redis
        elif score >= 0.5 and current_temp in ["cool", "cold"]:
            promote_to_warm(memory)  # → Active SQLite
        
        # Demotion
        elif score < 0.3 and current_temp != "cold":
            demote_to_cold(memory)  # → Archive
```

### Recommendation 3: Grace Period for Deletion

**Design**: Configurable retention before auto-deletion

```python
class DeletionPolicy(BaseModel):
    """Tier-specific deletion rules"""
    
    grace_period_days: int = 30      # Minimum retention
    score_threshold: float = 0.2     # Delete if score < 0.2
    age_threshold_days: int = 365    # Delete if older than 1 year
    prevent_categories: list[str] = ["decision", "important"]
```

**Logic**:
- Never auto-delete within grace period
- Never auto-delete important categories (override score)
- Delete only if: `(score < threshold) AND (age > grace_period)`

### Recommendation 4: Hebbian Learning for Importance

**Design**: Auto-update importance based on usage

```python
async def update_importance_on_access(
    key: str,
    user_id: str,
    semantic_score: float
):
    """Increase importance if memory is useful (Hebbian)"""
    
    memory = persistent.recall(key, user_id, include_metadata=True)
    old_importance = memory.metadata.get("importance", 0.5)
    
    # Increase importance if semantically relevant
    if semantic_score > 0.7:
        new_importance = old_importance * 0.9 + 0.1  # Increase by ~10%
    else:
        new_importance = old_importance * 0.95  # Slight decay
    
    memory.metadata["importance"] = min(1.0, new_importance)
    persistent.store(key, memory.value, user_id, metadata=memory.metadata)
```

### Recommendation 5: Redis Caching Strategy

**Design**: Three-level cache for hot memories

```
Working Memory (Dict, <1ms, session-scoped)
    ↓
Hot Cache (Redis, <1ms, user-scoped)
    ├─ LRU size: 10MB per user
    ├─ TTL: 7 days
    └─ Sync with SQLite on eviction
    
Persistent Memory (SQLite, <10ms, cold)
    ├─ All memories indexed
    └─ Fallback if cache miss
```

**Implementation**:
```python
class HybridMemoryManager:
    def __init__(self):
        self.working = WorkingMemory()     # Session
        self.hot_cache = RedisCache()      # Hot tier
        self.persistent = SQLiteMemory()   # Cold tier
    
    async def recall(self, key: str, user_id: str):
        # Level 1: Redis hot cache
        if value := await self.hot_cache.get(key, user_id):
            return value
        
        # Level 2: SQLite persistent
        if value := self.persistent.recall(key, user_id):
            # Promote to cache if hot
            if await should_cache(key, user_id):
                await self.hot_cache.set(key, value, user_id)
            return value
        
        return None
```

### Recommendation 6: Automated Maintenance Service

**Design**: Background task for cleanup and optimization

```python
class MemoryMaintenanceService:
    """Daily/hourly memory management"""
    
    async def run_maintenance(self):
        # 1. Auto-escalate by score (10-15 min)
        await self.auto_escalate_by_score()
        
        # 2. Archive cold memories (5-10 min)
        await self.archive_old_memories()
        
        # 3. Clean up deleted memories (2-3 min)
        await self.hard_delete_expired()
        
        # 4. Optimize graph (5 min)
        await self.optimize_graph()
        
        # 5. Rebuild lexical indexes (2 min)
        await self.rebuild_lexical_index()

    # Configurable schedule
    interval_hours = 24
    run_at_time = "02:00"  # 2 AM UTC
```

---

## 7. Memory Hierarchy Implementation Roadmap

### Phase 1: Foundation (v4.0.1, 1-2 weeks)

**Objective**: Implement RecallScorer integration and basic tiering

**Tasks**:
1. Integrate RecallScorer into `recall()` method
   - Update importance automatically on access
   - Track usage for Hebbian learning
   
2. Add temperature metadata field to memories
   - Default: "warm" for all existing memories
   - Backward compatible
   
3. Implement auto_forget_low_score_memories()
   - Issue #429 Phase 1
   - With grace period enforcement
   
4. Create MemoryMaintenanceTask
   - Background service (async)
   - Configurable schedule

**Estimated Effort**: 80 hours

---

### Phase 2: Escalation (v4.1.0, 2-3 weeks)

**Objective**: Automatic tier promotion/demotion

**Tasks**:
1. Implement auto_escalate_by_score()
   - Score thresholds per tier
   - Atomic tier transitions
   
2. Add retention policies
   - Per-temperature rules
   - Category-based exceptions
   
3. Archive system
   - Archive SQLite table
   - Compression of old memories
   
4. Tests & documentation
   - 90%+ coverage
   - User guide

**Estimated Effort**: 120 hours

---

### Phase 3: Hot Caching (v4.2.0, 2-3 weeks)

**Objective**: Redis integration for hot memories

**Tasks**:
1. Redis layer (Issue #435, #438)
   - Connect to Redis
   - LRU cache management
   
2. Cache coherence
   - Sync strategies
   - Invalidation logic
   
3. Fallback strategies
   - Redis unavailable handling
   - Graceful degradation
   
4. Distributed caching
   - Multi-node support
   - Replication

**Estimated Effort**: 100 hours

---

### Phase 4: AI-Driven Curation (v4.3.0, Ongoing)

**Objective**: Memory Curator Agent (Issue #397)

**Tasks**:
1. Analyze & propose (v4.1.0 foundation)
2. Auto-consolidate (v4.2.0 with user approval)
3. AI-driven importance (LLM-based)
4. Feedback loops (improve with usage)

**Estimated Effort**: 150+ hours (ongoing)

---

## 8. References

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `src/kagura/core/memory/recall_scorer.py` | Multi-dim scoring engine | 246 |
| `src/kagura/core/memory/persistent.py` | SQLite persistent layer | 400+ |
| `src/kagura/core/memory/manager.py` | Unified memory interface | 600+ |
| `src/kagura/config/memory_config.py` | Configuration & defaults | 232 |
| `src/kagura/core/graph/memory.py` | Graph relationships | 300+ |

### Related Issues

- **#429**: Smart Forgetting & Auto-maintenance (RecallScorer integration, auto-delete)
- **#430**: Auto-save & Auto-recall Intelligence (auto-detection, auto-suggest)
- **#397**: Memory Curator (AI-driven management, Phase D+)
- **#435**: Redis caching for hot memories
- **#438**: Distributed Redis caching
- **#441**: Smart memory summarization
- **#411**: Unused memory tracking

### Strategy Documents

- `ai_docs/MEMORY_STRATEGY.md` - 1042 lines, comprehensive strategy
- `ai_docs/ARCHITECTURE.md` - 692 lines, system design
- `ai_docs/CODING_STANDARDS.md` - Development guidelines

---

## 9. Summary Table: Current vs. Ideal State

| Feature | Current | Gap | Issue | Target |
|---------|---------|-----|-------|--------|
| Multi-dim Scoring | ✅ RecallScorer | Not used in recall() | #429 | v4.0.1 |
| Importance Field | ✅ Metadata | Static value | #429 | v4.0.1 |
| Access Tracking | ✅ Columns exist | Not auto-updated | #429 | v4.0.1 |
| Temperature Tiers | ❌ None | Need 4-tier design | Design | v4.1.0 |
| Auto-escalation | ❌ None | Need score-based | Design | v4.1.0 |
| Retention Policy | ❌ None | Need config | Design | v4.1.0 |
| Hot Cache (Redis) | ❌ None | Separate issue | #435 | v4.2.0 |
| Graph Integration | ✅ NetworkX | Not in scoring | #429 | v4.0.1 |
| Maintenance Task | ❌ None | Mentioned in #429 | Design | v4.0.1 |
| AI Curation | ❌ None | Phase D concept | #397 | v4.3.0+ |

---

**Report Generated**: October 29, 2025  
**Status**: Investigation Complete  
**Confidence Level**: High (80%+)

