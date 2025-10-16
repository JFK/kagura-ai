# RFC-026: Preset Expansion for Simplified Integration

**Status**: Draft  
**Created**: 2025-10-14  
**Issue**: [#169](https://github.com/JFK/kagura-ai/issues/169)  
**Priority**: 🥇 High (Tier 1 - User Experience)

---

## 📋 Problem Statement

Kagura AI has 16+ subsystems, but integrating them is complex for new users.

**Current complexity**:
```python
# Too many imports and manual configuration
from kagura.core.memory import MemoryManager
from kagura.routing import MemoryAwareRouter
from kagura.core.compression import CompressionPolicy
from kagura.multimodal import MultimodalRAG

memory = MemoryManager(enable_rag=True, enable_compression=True)
router = MemoryAwareRouter(memory=memory)
# ... 10+ lines of setup
```

---

## 💡 Proposed Solution

Expand `kagura.presets` module with 10+ ready-to-use presets.

**Target simplicity**:
```python
from kagura import presets

# One line, fully configured
agent = presets.ChatGPT()
agent = presets.ResearchAssistant(enable_web=True)
```

---

## 🎯 10+ Presets to Implement

### 1. ChatGPT
OpenAI ChatGPT-like conversational agent

### 2. ResearchAssistant
Web + RAG + Memory for research

### 3. CodeReviewer  
Code analysis + suggestions (existing, enhance)

### 4. Translator
Multi-language translation

### 5. DataAnalyst
Code execution + visualization

### 6. PersonalAssistant
Memory + scheduling + reminders

### 7. ContentWriter
Blog posts, articles, summaries

### 8. TechnicalSupport
Routing + knowledge base

### 9. LearningTutor
Adaptive teaching + memory

### 10. ProjectManager
Task tracking + planning

---

## 📅 Implementation Plan

**Duration**: 1 week

**Day 1-3**: Implement 10 presets (2 hours each)
**Day 4-5**: Tests (30+ tests)
**Day 6**: Documentation + PR

---

## ✅ Success Criteria

- ✅ 10+ presets
- ✅ <5 minute agent creation
- ✅ 80% complexity reduction
- ✅ 30+ tests

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
