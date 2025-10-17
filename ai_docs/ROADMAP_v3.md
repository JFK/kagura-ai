# Kagura AI v3.0 - Implementation Roadmap

**Date**: 2025-10-18 (Updated)
**Target Release**: Q1 2026
**Tracking Issue**: [#285](https://github.com/JFK/kagura-ai/issues/285)

---

## 📍 From v2.7.2 to v3.0: The Journey

### Current State: v2.7.2 (2025-10-18)

Kagura AI v2.7.2 is already a **production-ready framework** with:

**Core Capabilities**:
- ✅ Claude Code-like chat interface (8 built-in tools)
- ✅ Hybrid LLM backend (OpenAI SDK for gpt-*, LiteLLM for others)
- ✅ Search caching (70% faster, 30-50% cost reduction)
- ✅ Multimodal URL analysis (images, YouTube videos)
- ✅ Memory & RAG (ChromaDB-powered semantic search)
- ✅ MCP integration (15 built-in tools)
- ✅ Automatic telemetry (tokens, costs, performance)
- ✅ 1,300+ tests (>90% coverage), Pyright strict mode

**What's Missing for Personal Assistant Vision?**
- 🔲 **Dedicated personal tools** (news, weather, recipes, events)
- 🔲 **Enhanced Meta Agent** with `/create agent` chat command
- 🔲 **Cost visibility** via `/stats` command in chat
- 🔲 **Personal-first documentation** (currently developer-focused)

**v3.0 is not a rewrite—it's a focus shift with targeted additions.**

---

## 📋 Overview

This roadmap transforms Kagura AI from a "capable framework" to a "personal assistant you'd actually use daily", while maintaining its power as an SDK for developers.

---

## 🎯 Goals

1. **Personal Tools**: Add ready-to-use daily tools (news, weather, recipes, events)
2. **Enhanced Chat UX**: `/stats` for cost tracking, improved Meta Agent integration
3. **Documentation Refresh**: Rewrite for personal assistant first, SDK second
4. **Simplify Examples**: Real-world personal workflows, not abstract patterns
5. **Maintain SDK Excellence**: Keep type safety, testing, developer experience

---

## 📦 Phase 1: Focus Shift & Light Cleanup

**Duration**: 1-2 weeks
**Priority**: ⭐ Medium (most work already done in v2.7.x)
**Status**: 🔄 30% Complete

**Philosophy**: Keep what works, remove only what truly adds complexity for personal users.

### ✅ Already Completed (v2.6.0 - v2.7.2)

- ✅ Agent storage moved to `~/.kagura/agents/` (#261, v2.6.0)
- ✅ Presets consolidated into `src/kagura/agents/` (#269, v2.6.0)
- ✅ Legacy code removed (`src/kagura_legacy/`) (#273, v2.6.0)
- ✅ DuckDuckGo fallback removed (#277, v2.7.0)
- ✅ Default model updated to gpt-5-mini (#267, v2.6.0)
- ✅ `/model` command added for runtime switching (#268, v2.6.0)

### 🔲 Remaining Tasks

#### 1.1 Documentation Focus Shift
- [ ] Mark enterprise RFCs as "future/optional":
  - RFC-009 (Multi-Agent Orchestration)
  - RFC-010 (Deep Observability Dashboard)
  - RFC-015 (Advanced RAG)
  - RFC-011 (A/B Testing)
  - RFC-008 (Plugin Marketplace)
- [ ] Keep functional RFCs:
  - RFC-005 (Meta Agent - v2.5.0 base, v3.0 enhancement)
  - RFC-033 (Chat Enhancement)
  - RFC-034 (Multimodal URL)
  - RFC-035 (Search Caching)

#### 1.2 Code Review (Optional - Defer to v3.1)
- [ ] Review `src/kagura/routing/memory_aware_router.py` - Keep or simplify?
- [ ] Review `src/kagura/core/compression/` Phase 2-4 - Mark as future?
- [ ] Review `src/kagura/agents/` presets - Evaluate personal use relevance

**Decision**: Keep all code for now, evaluate based on actual usage in v3.0.

#### 1.3 pyproject.toml Polish
- [x] Extras structure ✅ (ai, web, auth, mcp - already correct)
- [ ] Update description: "Python-First AI Agent Framework" → "Personal AI Assistant & Python SDK"
- [ ] Add keywords: "personal assistant", "daily tools", "chat"

#### 1.4 AI Docs Cleanup (Low Priority)
- [ ] Archive `UNIFIED_ROADMAP.md` → `UNIFIED_ROADMAP_v2.5.md` (historical reference)
- [ ] Delete or archive `NEXT_STEPS.md`, `NEXT_PLAN_v2.5.0.md` (obsolete)
- [ ] Keep `CONTEXT_ENGINEERING_*.md` as reference (mark as "Advanced - Not v3.0 scope")

### Success Criteria
- ✅ 30% already achieved (v2.6-2.7 cleanup)
- 🔲 Focus shift documented (RFCs marked appropriately)
- 🔲 pyproject.toml updated for personal assistant positioning
- 🔲 No code deletions (keep flexibility)

---

## 🆕 Phase 2: Personal Tools

**Duration**: Week 1-2
**Priority**: ⭐ High
**Status**: 🔄 Planning

### Tasks

#### 2.1 Implement agents/news.py
- [ ] Create `src/kagura/agents/news.py`
- [ ] Implement `daily_news(topic: str = "technology", count: int = 5) -> str`
- [ ] Use `brave_search` tool for news fetching
- [ ] Format results as markdown list
- [ ] Add tests: `tests/agents/test_news.py`

**Implementation**:
```python
from kagura import agent
from kagura.tools import brave_search

@agent(model="gpt-5-mini", tools=[brave_search])
async def daily_news(topic: str = "technology", count: int = 5) -> str:
    """Get today's news on {{ topic }}"""
    ...
```

#### 2.2 Implement agents/weather.py
- [ ] Create `src/kagura/agents/weather.py`
- [ ] Implement `weather_forecast(location: str = "current") -> str`
- [ ] Use `brave_search` for weather information
- [ ] Format results with temperature, conditions, forecast
- [ ] Add tests: `tests/agents/test_weather.py`

#### 2.3 Implement agents/recipes.py
- [ ] Create `src/kagura/agents/recipes.py`
- [ ] Implement `search_recipes(ingredients: str, cuisine: str = "any") -> str`
- [ ] Use `brave_search` for recipe search
- [ ] Format results with title, ingredients, instructions link
- [ ] Add tests: `tests/agents/test_recipes.py`

#### 2.4 Implement agents/events.py
- [ ] Create `src/kagura/agents/events.py`
- [ ] Implement `find_events(location: str, category: str = "any", date: str = "today") -> str`
- [ ] Use `brave_search` for event search
- [ ] Format results with event name, date, location, link
- [ ] Add tests: `tests/agents/test_events.py`

#### 2.5 Update agents/__init__.py
- [ ] Export `daily_news`, `weather_forecast`, `search_recipes`, `find_events`
- [ ] Update `__all__` list
- [ ] Update docstring with personal tools

### Success Criteria
- ✅ 4 new personal tools implemented
- ✅ All tools work with real APIs (Brave Search)
- ✅ Test coverage > 90%
- ✅ Documentation with usage examples

---

## 🤖 Phase 3: Enhanced Meta Agent

**Duration**: 1-2 weeks
**Priority**: ⭐ High
**Status**: 🔄 Planning
**Base**: RFC-005 (Meta Agent v1, implemented in v2.5.0)

**Enhancement Goal**: Make agent creation accessible in chat, not just via `kagura build agent` CLI.

### Background

RFC-005 (v2.5.0) already provides:
- ✅ `SelfImprovingMetaAgent` - Generate agents from descriptions
- ✅ `kagura build agent` CLI command
- ✅ AgentSpec → Python code generation
- ✅ AST validation, error auto-fixing

**What's NEW in v3.0**: Bring this power directly into `kagura chat`.

### Tasks

#### 3.1 Add `/create agent` Chat Command
- [ ] Update `src/kagura/chat/session.py`
- [ ] Add `handle_create_command(self, args: str) -> None`
- [ ] Use existing `SelfImprovingMetaAgent` from RFC-005
- [ ] Display generated code preview in chat
- [ ] Confirm with user before saving
- [ ] Auto-save to `~/.kagura/agents/<agent_name>.py`
- [ ] Auto-register with AgentRouter (already exists in session.py)

**Example Flow**:
```bash
[You] > /create agent that summarizes morning tech news

💬 Generating agent...
✓ Agent created: tech_news_summarizer

Preview:
  @agent(model="gpt-5-mini", tools=[brave_web_search])
  async def tech_news_summarizer(query: str) -> str:
      """Get tech news summary for {{ query }}"""
      ...

Save to ~/.kagura/agents/tech_news_summarizer.py? (y/n)
```

#### 3.2 Add `/reload agents` Command (ALREADY EXISTS?)
- [ ] Check if session.py already has agent reloading
- [ ] If not, add `reload_agents()` method
- [ ] Clear `custom_agents` dict
- [ ] Re-run `_load_custom_agents()`
- [ ] Display newly loaded agents count

#### 3.3 Testing
- [ ] Test `/create agent` command in chat
- [ ] Test save confirmation flow
- [ ] Test auto-registration with router
- [ ] Test `/reload` if new
- [ ] Integration with existing RFC-005 code

### Success Criteria
- ✅ `/create agent` works seamlessly in chat
- ✅ Generated agents save to ~/.kagura/agents/
- ✅ Auto-registration with AgentRouter
- ✅ Users can create custom agents without leaving chat
- ✅ Reuses existing RFC-005 implementation (no duplication)

---

## 📊 Phase 4: Chat Statistics & Cost Visibility

**Duration**: 1 week
**Priority**: ⭐ High
**Status**: 🔄 Planning
**Base**: RFC-030 (Telemetry Integration, v2.5.5 - already collecting data)

**Enhancement Goal**: Surface telemetry data in chat via `/stats` command.

### Background

RFC-030 Phase 1 (v2.5.5) already provides:
- ✅ `LLMResponse` with usage metadata (tokens, cost, duration)
- ✅ Automatic telemetry collection in `@agent` decorator
- ✅ `pricing.py` with accurate cost calculation for 20+ models
- ✅ EventStore (SQLite backend) for telemetry data
- ✅ `kagura monitor` CLI for viewing execution history

**What's NEW in v3.0**: Real-time stats in chat session.

### Tasks

#### 4.1 Implement chat/stats.py
- [ ] Create `src/kagura/chat/stats.py`
- [ ] `SessionStats` class - wrapper around existing telemetry data
- [ ] Query EventStore or track in-memory for current session
- [ ] Methods:
  - `get_summary() -> dict` - Token/cost breakdown
  - `export_json(path: str)` - Export session stats
  - `export_csv(path: str)` - Export for Excel/Sheets

#### 4.2 Integrate into ChatSession
- [ ] Update `src/kagura/chat/session.py`
- [ ] Add `self.stats = SessionStats()` in `__init__`
- [ ] Option 1: Track in-memory (simpler, session-scoped)
- [ ] Option 2: Query EventStore (persistent, cross-session)
- [ ] Capture `LLMResponse.usage` from chat agent calls

#### 4.3 Add `/stats` Command
- [ ] Add `handle_stats_command(self, args: str)` to ChatSession
- [ ] `/stats` - Show current session summary (Rich table)
- [ ] `/stats summary` - AI-generated insights (optional)
- [ ] `/stats export <file>` - Export to JSON or CSV
- [ ] Display: Total tokens, cost, model breakdown, tool usage

#### 4.4 Testing
- [ ] Test SessionStats data collection
- [ ] Test `/stats` Rich table display
- [ ] Test `/stats export` to JSON/CSV
- [ ] Integration test with mock LLM calls

### Success Criteria
- ✅ `/stats` shows accurate token/cost data
- ✅ Export works in both JSON and CSV
- ✅ Reuses RFC-030 telemetry infrastructure (no duplication)
- ✅ Simple, fast, useful for cost-conscious users

---

---

## 🤔 Why v3.0 When v2.7.2 Already Works?

### The Technical Truth

v2.7.2 is technically complete:
- ✅ All core features work
- ✅ Production-ready quality (1,300+ tests, strict typing)
- ✅ Performance optimized (caching, lazy loading)
- ✅ Developers can build anything with the SDK

### The User Experience Gap

But for **personal users** (non-developers), v2.7.2 is:
- ⚠️ **Not obvious**: No dedicated tools for daily needs (news, weather, recipes)
- ⚠️ **SDK-first**: Documentation assumes you'll write code
- ⚠️ **Cost-blind**: No easy way to see how much you're spending in chat
- ⚠️ **Generic**: No examples showing "morning briefing" or "recipe search"

### What v3.0 Adds

1. **Personal Tools** → Immediate usefulness for non-coders
2. **Enhanced Meta Agent** → Create agents without leaving chat
3. **Cost Visibility** → `/stats` shows spending in real-time
4. **Personal-First Docs** → Quickstart assumes you just want a personal assistant

**Technical changes: < 5% of codebase**
**Philosophy shift: 100% focus on personal daily use**

---

## 📚 Phase 5: Documentation

**Duration**: 2-3 weeks
**Priority**: 🔥 Critical (defines v3.0 identity)
**Status**: 🔄 Planning

### Tasks

#### 5.1 Update CLAUDE.md
- [ ] Replace old roadmap references with VISION.md and ROADMAP_v3.md
- [ ] Update architecture diagrams
- [ ] Simplify development guidelines
- [ ] Remove references to deleted RFCs
- [ ] Add Meta Agent development workflow

#### 5.2 Rewrite README.md
- [ ] Focus on personal assistant use cases
- [ ] Quick start: `pip install kagura-ai && kagura chat`
- [ ] 3-4 compelling examples (news, weather, recipes)
- [ ] Link to comprehensive docs
- [ ] Add "Why Kagura AI?" section (simplicity, personalization)

#### 5.3 Rewrite docs/
- [ ] `docs/getting-started.md` - Chat-first tutorial
- [ ] `docs/sdk-guide.md` - @agent decorator, tools, memory
- [ ] `docs/personal-tools.md` - Built-in personal tools
- [ ] `docs/mcp-integration.md` - MCP setup and usage
- [ ] `docs/meta-agent.md` - Generating custom agents
- [ ] `docs/stats-monitoring.md` - /stats and kagura monitor

#### 5.4 Update API Documentation
- [ ] `docs/api/core.md` - @agent, @tool, MemoryManager
- [ ] `docs/api/agents.md` - Built-in agents
- [ ] `docs/api/tools.md` - Built-in tools
- [ ] `docs/api/chat.md` - ChatSession, commands

#### 5.5 Create Tutorial Videos (Future)
- [ ] Screen recording: "First 5 Minutes with Kagura AI"
- [ ] Screen recording: "Creating a Custom Agent"
- [ ] Screen recording: "MCP Integration"

### Success Criteria
- ✅ New user can get started in < 5 minutes
- ✅ All major features documented
- ✅ Real-world examples with code
- ✅ Clear migration guide from v2.x

---

## 🔬 Phase 6: Examples

**Duration**: Week 3
**Priority**: ⭐ Medium
**Status**: 🔄 Planning

### Tasks

#### 6.1 Create examples/personal_assistant/
- [ ] `daily_briefing.py` - Morning news + weather + calendar
- [ ] `recipe_bot.py` - Interactive recipe assistant
- [ ] `event_finder.py` - Find events by location and date
- [ ] `note_taker.py` - Save and search personal notes with RAG

#### 6.2 Clean up examples/real_world/
- [ ] Keep: `simple_chat/`, `code_generator/`
- [ ] Delete or move: enterprise-focused examples
- [ ] Add README.md for each example

#### 6.3 Create examples/data_analysis/ (Future v3.1)
- [ ] `stock_tracker.py` - Track stock prices
- [ ] `expense_analyzer.py` - Analyze personal expenses
- [ ] `notebook_demo.ipynb` - Jupyter integration

### Success Criteria
- ✅ 4+ personal assistant examples
- ✅ All examples work out-of-the-box
- ✅ Clear README with usage instructions
- ✅ Examples showcase real-world use cases

---

## 📋 Testing & Quality Assurance

### Continuous Testing
- [ ] Maintain > 90% test coverage for core modules
- [ ] All tests pass before each phase merge
- [ ] Pyright strict mode compliance
- [ ] Ruff linting with no warnings

### Integration Testing
- [ ] End-to-end chat session test
- [ ] Meta Agent generation test
- [ ] Personal tools integration test
- [ ] MCP integration test

### Performance Testing
- [ ] Startup time < 1 second
- [ ] Memory footprint < 100MB (base install)
- [ ] Chat response time < 3 seconds (without LLM)

---

## 🚀 Release Plan

### Pre-Release Checklist
- [ ] All phases 1-6 completed
- [ ] Documentation review
- [ ] Example validation
- [ ] Community preview (select users)
- [ ] Migration guide from v2.x

### Release Day
- [ ] Tag v3.0.0 in Git
- [ ] Publish to PyPI
- [ ] Update GitHub README
- [ ] Announcement blog post
- [ ] Social media posts

### Post-Release
- [ ] Monitor GitHub Issues
- [ ] Community feedback collection
- [ ] Bug fix releases (v3.0.1, v3.0.2, etc.)
- [ ] Start planning v3.1 (Jupyter integration)

---

## 📊 Success Metrics

### Technical Metrics
- ✅ Codebase size reduced by 30%
- ✅ Test coverage > 90%
- ✅ Startup time < 1 second
- ✅ Zero Pyright strict mode errors

### User Metrics
- ✅ 100+ new users in first month
- ✅ 50+ custom agents shared
- ✅ Average setup time < 5 minutes
- ✅ 90%+ positive feedback

### Community Metrics
- ✅ 10+ community contributions
- ✅ 5+ blog posts/tutorials
- ✅ Active Discord/Slack community

---

## 🔗 Related Documents

- [VISION.md](./VISION.md) - Vision and philosophy
- [CLAUDE.md](../CLAUDE.md) - Development guidelines
- [RFC-003](./rfcs/RFC_003_PERSONAL_ASSISTANT.md) - Personal Assistant spec
- [GitHub Issue #285](https://github.com/JFK/kagura-ai/issues/285) - v3.0 tracking

---

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-10-17 | Initial v3.0 roadmap | Claude Code |

---

**Let's build v3.0 together!** 🚀
