# Kagura AI v3.0 - Vision Document

**Date**: 2025-10-19
**Status**: Active
**Version**: 3.0

---

## 🎯 Vision

**Kagura AI is a Python-First AI Agent SDK - build production AI in one decorator.**

We believe AI development should be simple, type-safe, and production-ready. Kagura AI serves developers who want to:

1. **Integrate AI into apps**: One `@agent` decorator, full type safety
2. **Build quickly**: No config files, just Python
3. **Ship to production**: Built-in memory, tools, testing

Whether you're building a FastAPI endpoint, data pipeline, or automation script, Kagura AI makes AI integration trivial.

**Bonus**: Want to try without code? Run `kagura chat` for instant experimentation.

---

## 🌟 Core Principles

### 1. SDK-First, Chat as Bonus

**Primary**: Python SDK for developers
- Integrate into FastAPI, Streamlit, data pipelines
- Type-safe, testable, production-ready
- `from kagura import agent` - that's it

**Secondary**: Interactive Chat for exploration
- Try SDK features without writing code
- Prototype ideas quickly
- Claude Code-like experience

**Why**: GitHub audience = engineers seeking SDK solutions

### 2. One Decorator Philosophy

```python
@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''
```

No configuration files. No complex setup. Just Python.

### 3. Full Type Safety

- **pyright strict mode**: Zero tolerance for type errors
- **Pydantic integration**: Structured output with validation
- **IDE support**: Full autocomplete, type checking

### 4. Production-Ready Out of the Box

- **Memory**: 3-tier system (Context/Persistent/RAG)
- **Tools**: Web search, file ops, code exec built-in
- **Testing**: AgentTestCase with semantic assertions
- **Observability**: Cost tracking, performance monitoring

### 5. Simplicity & Focus

**Keep**:
- Core: @agent, @tool, @workflow
- Memory: MemoryManager, MemoryRAG
- Tools: Built-in tools (web, file, code)
- Chat: Interactive experimentation
- MCP: Claude Desktop integration

**Avoid**:
- Complex orchestration (keep simple workflows)
- Enterprise features (multi-tenant, dashboards)
- Plugin systems (keep focused)

---

## 🎯 Target Audience

### Primary: Python Developers

**Use Cases**:
- Web API endpoints (FastAPI, Flask)
- Data enrichment pipelines
- Automation scripts
- Internal tools

**Needs**:
- Type safety
- Easy integration
- Production-ready
- Testable

### Secondary: Experimenters

**Use Cases**:
- Prototyping AI ideas
- Learning AI agent patterns
- Quick experiments

**Needs**:
- No code required
- Instant feedback
- Feature-rich

---

## 🚀 v3.0 Goals

### Documentation
- ✅ SDK-first README
- ✅ Real-world integration examples
- ✅ Chat as bonus feature

### Developer Experience
- ✅ Simplified CLAUDE.md
- ✅ Clean ai_docs/
- ✅ Type-safe everywhere

### Quality
- ✅ 1,300+ tests
- ✅ 90%+ coverage
- ✅ Zero pyright errors

---

## 🌸 Philosophy

"Kagura (神楽)" embodies harmony and creativity - principles at the heart of this SDK:

- **Harmony**: Simple API that works with Python's natural patterns
- **Creativity**: Enable developers to build AI solutions quickly
- **Craftsmanship**: Quality over quantity, type safety over flexibility

---

## 📊 Success Metrics

### Technical
- ✅ One-line agent creation
- ✅ Full type safety (pyright strict)
- ✅ 90%+ test coverage
- ✅ Production-ready

### Adoption
- 🎯 Developers choose Kagura for SDK integration
- 🎯 "Best Python AI SDK" reputation
- 🎯 Active GitHub community

---

**Built with ❤️ for developers who value type safety and simplicity**

---

**Last Updated**: 2025-10-19
