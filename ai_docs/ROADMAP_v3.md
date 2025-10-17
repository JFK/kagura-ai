# Kagura AI v3.0 - Implementation Roadmap

**Date**: 2025-10-17
**Target Release**: Q1 2025
**Tracking Issue**: [#285](https://github.com/JFK/kagura-ai/issues/285)

---

## 📋 Overview

This roadmap outlines the detailed implementation plan for Kagura AI v3.0, focusing on transforming the framework into a **Personal Assistant** platform.

---

## 🎯 Goals

1. **Simplify Architecture**: Remove enterprise features, focus on personal use
2. **Enhance Chat Experience**: Add `/stats`, Meta Agent, better UX
3. **Personal Tools**: News, weather, recipes, events
4. **Clean Documentation**: Rewrite for personal assistant use cases
5. **SDK Usability**: Maintain excellent developer experience

---

## 📦 Phase 1: Cleanup & Foundation

**Duration**: Week 1
**Priority**: 🔥 Critical
**Status**: 🔄 Planning

### Tasks

#### 1.1 Delete Unused RFC Files
- [ ] Delete `ai_docs/rfcs/RFC_005_*.md` (Self-Improving Agent)
- [ ] Delete `ai_docs/rfcs/RFC_009_*.md` (Multi-Agent Orchestration)
- [ ] Delete `ai_docs/rfcs/RFC_010_DASHBOARD_*.md` (Web Dashboard)
- [ ] Delete `ai_docs/rfcs/RFC_015_*.md` (Advanced RAG)
- [ ] Delete `ai_docs/rfcs/RFC_011_*.md` (A/B Testing)
- [ ] Delete `ai_docs/rfcs/RFC_008_*.md` (Plugin Marketplace)
- [ ] Delete `ai_docs/rfcs/RFC_006_*.md` (Workflow Engine)

#### 1.2 Delete Unused Code
- [ ] Delete `src/kagura/routing/memory_aware_router.py`
- [ ] Delete `src/kagura/routing/context_analyzer.py`
- [ ] Delete `src/kagura/core/compression/trimmer.py` (Phase 2)
- [ ] Delete `src/kagura/core/compression/summarizer.py` (Phase 3)
- [ ] Update `src/kagura/core/compression/__init__.py`

#### 1.3 Simplify agents/
- [ ] Delete `src/kagura/agents/code_review.py`
- [ ] Delete `src/kagura/agents/content_writer.py`
- [ ] Delete `src/kagura/agents/data_analyst.py`
- [ ] Delete `src/kagura/agents/learning_tutor.py`
- [ ] Delete `src/kagura/agents/project_manager.py`
- [ ] Delete `src/kagura/agents/research.py`
- [ ] Delete `src/kagura/agents/technical_support.py`
- [ ] Keep: `code_execution.py`, `summarizer.py`, `translate_func.py`, `personal_assistant.py`

#### 1.4 Update pyproject.toml
- [ ] Verify `extras_require` structure (already correct)
- [ ] Update description to "Personal AI Assistant Framework"
- [ ] Update classifiers to reflect personal use focus

#### 1.5 Delete Old AI Docs
- [ ] Delete `ai_docs/UNIFIED_ROADMAP.md` (replaced by ROADMAP_v3.md)
- [ ] Delete `ai_docs/NEXT_STEPS.md` (obsolete)
- [ ] Delete `ai_docs/NEXT_PLAN_v2.5.0.md` (obsolete)
- [ ] Delete `ai_docs/CONTEXT_ENGINEERING_*.md` (too complex)

### Success Criteria
- ✅ Codebase reduced by ~30% (delete unused code)
- ✅ All tests pass
- ✅ Pyright strict mode compliance maintained

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

## 🤖 Phase 3: Meta Agent

**Duration**: Week 2
**Priority**: ⭐ High
**Status**: 🔄 Planning

### Tasks

#### 3.1 Implement agents/meta_agent.py
- [ ] Create `src/kagura/agents/meta_agent.py`
- [ ] Implement `meta_agent(description: str) -> str`
- [ ] LLM generates Python code for new agent
- [ ] Validate generated code (AST parse)
- [ ] Save to `~/.kagura/agents/<agent_name>.py`
- [ ] Return success message with usage instructions

**Implementation**:
```python
from kagura import agent
from pathlib import Path

@agent(model="gpt-5-mini", temperature=0.3)
async def meta_agent(description: str) -> str:
    """
    Generate a custom agent based on user description.

    User request: {{ description }}

    Generate Python code for an @agent-decorated function.
    Use this template:
    ```python
    from kagura import agent
    from kagura.tools import ...

    @agent(model="gpt-5-mini", tools=[...])
    async def my_agent(query: str) -> str:
        '''{{ query }}に答える'''
        ...
    ```
    """
    ...
```

#### 3.2 Add /create agent Command
- [ ] Update `src/kagura/chat/session.py`
- [ ] Add `handle_create_command(self, args: str) -> None`
- [ ] Call `meta_agent(args)`
- [ ] Display generated code preview
- [ ] Save and auto-register with AgentRouter

#### 3.3 Add /reload agents Command
- [ ] Update `src/kagura/chat/session.py`
- [ ] Implement `reload_agents(self) -> None`
- [ ] Clear current custom_agents
- [ ] Re-run `_load_custom_agents()`
- [ ] Display newly loaded agents

#### 3.4 Testing
- [ ] Test Meta Agent code generation
- [ ] Test save to `~/.kagura/agents/`
- [ ] Test auto-registration with AgentRouter
- [ ] Test `/create` and `/reload` commands

### Success Criteria
- ✅ Meta Agent generates valid Python code
- ✅ Generated agents save correctly
- ✅ AgentRouter auto-registers new agents
- ✅ `/create` and `/reload` commands work seamlessly

---

## 📊 Phase 4: Chat Enhancements

**Duration**: Week 2
**Priority**: ⭐ High
**Status**: 🔄 Planning

### Tasks

#### 4.1 Implement chat/stats.py
- [ ] Create `src/kagura/chat/stats.py`
- [ ] Implement `SessionStats` class
- [ ] Track LLM calls: model, tokens, cost, duration
- [ ] Track tool calls: tool_name, count, duration
- [ ] Method: `get_summary() -> dict`
- [ ] Method: `export_json(path: str) -> None`
- [ ] Method: `export_csv(path: str) -> None`

**Implementation**:
```python
class SessionStats:
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.llm_calls: list[dict] = []
        self.tool_calls: list[dict] = []

    def track_llm_call(self, model: str, usage: dict, duration: float):
        cost = calculate_cost(usage, model)
        self.llm_calls.append({...})

    def get_summary(self) -> dict:
        # Total tokens, cost, model breakdown
        ...
```

#### 4.2 Integrate Stats into ChatSession
- [ ] Update `src/kagura/chat/session.py`
- [ ] Add `self.stats = SessionStats(self.memory)` in `__init__`
- [ ] Track LLM calls in `chat()` method
- [ ] Capture `LLMResponse.usage` and `LLMResponse.duration`

#### 4.3 Add /stats Command
- [ ] Add `handle_stats_command(self, args: str) -> None`
- [ ] `/stats` - Display current session stats
- [ ] `/stats summary` - AI-generated summary
- [ ] `/stats export <path>` - Export to JSON/CSV
- [ ] Use Rich tables for display

#### 4.4 Implement AI Summary Generation
- [ ] Create summary agent in `chat/stats.py`
- [ ] Input: session stats + conversation history
- [ ] Output: Human-readable summary (topics, tools used, insights)

#### 4.5 Testing
- [ ] Test SessionStats tracking
- [ ] Test `/stats` command display
- [ ] Test `/stats summary` generation
- [ ] Test `/stats export` functionality

### Success Criteria
- ✅ SessionStats accurately tracks all LLM calls
- ✅ `/stats` displays clear token/cost breakdown
- ✅ `/stats summary` provides useful insights
- ✅ Export works in JSON and CSV formats

---

## 📚 Phase 5: Documentation

**Duration**: Week 3
**Priority**: 🔥 Critical
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
