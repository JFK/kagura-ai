# Kagura AI v3.0 - Vision Document

**Date**: 2025-10-17
**Status**: Active
**Version**: 3.0

---

## 🎯 Vision

**Kagura AI is a Python-first AI agent framework focused on personal assistant use cases.**

We believe AI should be accessible, practical, and useful in everyday life—not just in enterprise environments. Kagura AI empowers individuals to build, customize, and use AI agents for their daily needs, from morning news briefings to recipe suggestions to event planning.

---

## 🌟 Core Principles

### 1. Personal-First, Not Enterprise-First
- **Target User**: Individuals using AI for personal productivity and daily life
- **Use Cases**: News summarization, recipe search, weather updates, event finding, personal note-taking
- **Not Focused On**: Enterprise workflows, complex orchestration, A/B testing, plugin marketplaces

### 2. Conversation-Driven Development
- **Chat as the Primary Interface**: `kagura chat` is the main way users interact with AI
- **Meta Agent**: Users can generate new agents **during chat** conversations
- **Validation Flow**: Test in chat → Export as SDK → Share as examples

### 3. SDK-First Architecture
- **Easy Import**: `from kagura import agent`
- **Minimal Boilerplate**: One decorator to create an agent
- **Type Safety**: Full type hint support with strict mode
- **Lazy Loading**: Fast startup, load modules on demand

### 4. Memory & Personalization
- **Long-Term Memory**: RAG-based semantic search for conversation history
- **Personal Notes**: Store recipes, documents, preferences
- **Context Compression**: Smart context management to stay within token limits
- **Learning Over Time**: Agents adapt to user preferences

### 5. Simplicity Over Features
- **Remove Complexity**: Delete enterprise-focused features (multi-agent orchestration, workflow engines)
- **Focus on Core**: Chat, MCP, Memory, Tools, Routing
- **Lightweight**: Fast startup, minimal dependencies for core features

---

## 🏗️ Architecture Philosophy

### Three Layers

```
┌─────────────────────────────────────┐
│   User Layer (Personal Assistant)  │
│   - kagura chat                     │
│   - MCP integration                 │
│   - Custom agents (~/.kagura)       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   SDK Layer (Development)           │
│   - @agent decorator                │
│   - Tools & Loaders                 │
│   - Memory + RAG                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Core Layer (Foundation)           │
│   - LLM Integration                 │
│   - Code Executor                   │
│   - Routing Engine                  │
└─────────────────────────────────────┘
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Chat-Centric** | Most users start with chatting, not coding |
| **agents/ Consolidation** | One place for all agents/tools (framework + user) |
| **Memory + RAG** | Critical for personalization and long-term learning |
| **Optional Extras** | `ai`, `web`, `auth`, `mcp` extras for advanced features |
| **Keep monitor CLI** | Useful for debugging and cost analysis |
| **Remove Dashboard** | Web dashboard adds complexity, CLI is sufficient |

---

## 🎨 User Experience Goals

### For End Users (Non-Developers)
- ✅ Start chatting in < 5 minutes (`pip install kagura-ai && kagura chat`)
- ✅ Generate custom agents **in chat** without writing code
- ✅ Agents remember preferences and past conversations
- ✅ Clear cost/token usage visibility (`/stats`)

### For Developers (SDK Users)
- ✅ Intuitive API: `@agent` decorator is all you need
- ✅ Easy tool integration: `tools=[brave_search, youtube_transcript]`
- ✅ Full type safety with Pyright strict mode
- ✅ Comprehensive documentation with real-world examples

### For Power Users (MCP Integration)
- ✅ Control chat via MCP protocol
- ✅ Integrate with other tools (Claude Desktop, Cursor, etc.)
- ✅ Programmatic access to all features

---

## 🚀 What's New in v3.0

### 🆕 New Features

1. **Personal Assistant Tools**
   - `daily_news()` - Morning news briefing
   - `weather_forecast()` - Weather updates
   - `search_recipes()` - Recipe suggestions
   - `find_events()` - Event search

2. **Meta Agent**
   - Generate agents during chat: `/create agent <description>`
   - Auto-save to `~/.kagura/agents/`
   - Auto-register with AgentRouter
   - Example: "Create an agent that summarizes morning news"

3. **Chat Enhancements**
   - `/stats` - Token/cost breakdown
   - `/stats summary` - AI-generated session summary
   - `/stats export` - Export stats to JSON/CSV

### ⚠️ Simplified

- **Observability**: Keep `kagura monitor` CLI, remove web dashboard
- **Context Compression**: Keep Phase 1 (token management), remove Phase 2-4
- **Agents**: Remove enterprise-focused presets, keep practical ones

### ❌ Removed

- RFC-005 (Self-Improving Agent)
- RFC-009 (Multi-Agent Orchestration)
- RFC-010 (Deep Observability Dashboard)
- RFC-015 (Advanced RAG)
- RFC-011 (A/B Testing)
- RFC-008 (Plugin Marketplace)
- RFC-006 (Workflow Engine)

---

## 📊 Success Metrics

### Technical Metrics
- ✅ Test coverage > 90% for core modules
- ✅ Type safety: Pyright strict mode compliance
- ✅ Startup time < 1 second
- ✅ Memory footprint < 100MB (base install)

### User Metrics
- ✅ Time to first chat: < 5 minutes
- ✅ Agent creation time (with Meta Agent): < 2 minutes
- ✅ Documentation clarity: New user can create custom agent in < 30 minutes

### Community Metrics
- ✅ Active users creating custom agents
- ✅ Shared examples in `examples/personal_assistant/`
- ✅ Positive feedback on simplicity and usability

---

## 🗺️ Roadmap

### v3.0 (Foundation) - Q1 2025
- ✅ Architecture restructure
- ✅ Personal assistant tools
- ✅ Meta Agent
- ✅ Chat enhancements (/stats)
- ✅ Documentation rewrite

### v3.1 (Jupyter Integration) - Q2 2025
- 🔲 Notebook execution support
- 🔲 Data analysis examples
- 🔲 Interactive visualizations

### v3.2 (Calendar & Reminders) - Q2-Q3 2025
- 🔲 Google Calendar integration (via OAuth2)
- 🔲 Reminder system
- 🔲 Event notifications

### v4.0 (Voice Interface) - Q4 2025
- 🔲 Whisper integration (speech-to-text)
- 🔲 TTS integration (text-to-speech)
- 🔲 Voice-first workflows

---

## 🤝 Community & Contribution

### Contribution Philosophy
- **Quality Over Quantity**: We value well-tested, documented contributions
- **Personal Use Cases**: Prefer practical, real-world examples
- **Simplicity First**: Additions should not increase complexity for beginners

### How to Contribute
1. **Share Examples**: Personal assistant workflows, custom agents
2. **Improve Documentation**: Real-world use cases, tutorials
3. **Report Issues**: Use GitHub Issues (with clear reproduction steps)
4. **Propose Features**: Aligned with personal assistant vision

### What We Won't Accept
- ❌ Enterprise-only features (workflow engines, A/B testing)
- ❌ Complex orchestration systems
- ❌ Features that increase startup time significantly
- ❌ Features that break simplicity for beginners

---

## 📝 Closing Thoughts

Kagura AI v3.0 is a **return to simplicity**. We're removing enterprise bloat and focusing on what matters: helping individuals use AI in their daily lives.

Our goal is to make AI **accessible, practical, and personal**. Not another framework for data scientists or enterprise engineers, but a tool for anyone who wants a personal AI assistant that actually works.

---

**Let's build a personal AI assistant framework that's actually useful in daily life!** 🚀

---

## 🔗 Related Documents
- [ROADMAP_v3.md](./ROADMAP_v3.md) - Detailed implementation roadmap
- [CLAUDE.md](../CLAUDE.md) - Development guidelines
- [RFC-003](./rfcs/RFC_003_PERSONAL_ASSISTANT.md) - Personal Assistant specification
- [GitHub Issue #285](https://github.com/JFK/kagura-ai/issues/285) - v3.0 tracking issue
