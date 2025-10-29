# Memory System - Implementation Guide

**Quick Reference for Memory Module Development**

## Overview

Kagura AI v4.0+ provides a **Temperature-based Memory Hierarchy** for high-context conversations.

**For detailed design documentation, see**: [`ai_docs/MEMORY_TEMPERATURE_HIERARCHY.md`](../../../ai_docs/MEMORY_TEMPERATURE_HIERARCHY.md)

---

## Architecture (Quick Reference)

### 4-Tier System

```
Tier 1: Working Memory    - Python dict       - <1ms   - Session
Tier 2: Context Memory    - In-memory list    - <1ms   - Session
Tier 3: Persistent Memory - SQLite            - <10ms  - User-scoped
Tier 4: Semantic Search   - ChromaDB/Qdrant   - <100ms - Vector search
Bonus:  Graph Memory      - NetworkX          - <10ms  - Relationships
```

### Temperature Tiers (Tier 3 Stratification)

```
🔥 Hot Memory (Score 0.8+)   - Recent/frequent access → Always in context
🌡️ Warm Memory (Score 0.5-0.8) - Moderate access → RAG-selected
❄️ Cool Memory (Score 0.2-0.5) - Low access → Semantic search only
🧊 Cold Memory (Score 0.0-0.2) - Long-term unused → Archive candidate
   └─ ⭐ importance >= 0.7 → Protected (never archived)
```

---

## Key Modules

### Core Components

| Module | Path | Purpose |
|--------|------|---------|
| MemoryManager | `manager.py` | Main interface |
| RecallScorer | `recall_scorer.py` | Multi-dimensional scoring (246 lines) |
| PersistentMemory | `persistent.py` | SQLite backend (Tier 3) |
| MemoryRAG | `rag.py` | ChromaDB/Qdrant integration (Tier 4) |
| ContextMemory | `context.py` | Session memory (Tier 2) |
| WorkingMemory | `working.py` | Immediate context (Tier 1) |

### Temperature Implementation (v4.0.1+)

| Module | Path | Purpose | Status |
|--------|------|---------|--------|
| Temperature Engine | `temperature.py` | Tier classification | 🔜 Phase 1 |
| Hebbian Learner | `hebbian.py` | Auto-importance update | 🔜 Phase 1 |
| Memory Protection | `protection.py` | Important memory guard | 🔜 Phase 1 |
| Memory Curator | `curator.py` | Smart agent | 🔜 Phase 2 |
| MD Manager | `md_manager.py` | Markdown export/import | 🔜 Phase 2 |

---

## Quick Implementation Guide

### 1. RecallScorer Integration (Phase 1)

```python
# In manager.py recall() method
from .recall_scorer import RecallScorer

scorer = RecallScorer()
for memory in candidates:
    memory.score = scorer.calculate_score(memory, query)
    memory.temperature = assign_temperature(memory.score)
```

### 2. Hebbian Learning (Phase 1)

```python
# In hebbian.py (new file)
LEARNING_RATE = 0.05

def on_memory_recall(memory: Memory):
    memory.access_count += 1
    memory.last_accessed_at = datetime.utcnow()
    memory.importance = min(1.0, memory.importance + LEARNING_RATE)
    return memory
```

### 3. Important Memory Protection (Phase 1)

```python
# In protection.py (new file)
MIN_IMPORTANCE_FOR_RETENTION = 0.7

def should_archive(memory: Memory) -> bool:
    if memory.importance >= MIN_IMPORTANCE_FOR_RETENTION:
        return False  # Protected
    return days_since_access(memory) > 90 and memory.importance < 0.2
```

---

## Configuration

### Memory Config

**File**: `src/kagura/config/memory_config.py`

Key settings:
- `IMPORTANCE_THRESHOLD`: 0.7 (permanent retention)
- `HEBBIAN_LEARNING_RATE`: 0.05
- `ARCHIVE_GRACE_PERIOD_DAYS`: 30
- `COLD_MEMORY_THRESHOLD_DAYS`: 90

---

## Testing

```bash
# Run memory tests
pytest tests/core/memory/ -v

# Specific modules
pytest tests/core/memory/test_recall_scorer.py
pytest tests/core/memory/test_persistent.py
pytest tests/core/memory/test_temperature.py  # Phase 1
```

---

## Related Documentation

### Design & Strategy
- **[MEMORY_TEMPERATURE_HIERARCHY.md](../../../ai_docs/MEMORY_TEMPERATURE_HIERARCHY.md)** - Full design (1,100 lines)
- **[MEMORY_STRATEGY.md](../../../ai_docs/MEMORY_STRATEGY.md)** - v4.0 Memory Strategy
- **[ARCHITECTURE.md](../../../ai_docs/ARCHITECTURE.md)** - System architecture

### Issues
- **[#453](https://github.com/JFK/kagura-ai/issues/453)** - Temperature-based Hierarchy (this design)
- **[#429](https://github.com/JFK/kagura-ai/issues/429)** - Smart Forgetting & Auto-maintenance
- **[#430](https://github.com/JFK/kagura-ai/issues/430)** - Auto-save & Auto-recall
- **[#397](https://github.com/JFK/kagura-ai/issues/397)** - Memory Curator

---

**Last Updated**: 2025-10-29
**Implementation Status**: Phase 1 pending (Issue #429)
**Full Design**: See `ai_docs/MEMORY_TEMPERATURE_HIERARCHY.md`
