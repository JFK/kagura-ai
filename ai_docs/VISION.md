# Kagura AI v3.0 - Vision Document

**Date**: 2025-10-17
**Status**: Active
**Version**: 3.0

---

## 🎯 Vision

**Kagura AI is a personal AI assistant you can use today, and a Python SDK you can extend tomorrow.**

We believe AI should be accessible, practical, and useful in everyday life—not just in enterprise environments. Kagura AI serves two audiences:

1. **Personal Users**: Get instant AI assistance for daily tasks (news, weather, recipes, web research)
2. **Developers**: Build custom AI agents with one Python decorator (`@agent`)

Whether you `pip install kagura-ai && kagura chat` to start chatting, or `from kagura import agent` to build your own tools, Kagura AI adapts to your needs.

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

### 6. Dual Identity: Tool & SDK
- **As a Tool**: `kagura chat` - instant personal assistant, no coding required
- **As an SDK**: `@agent` decorator - build custom agents in minutes with full type safety
- **Seamless Flow**: Test agents in chat → Export to code → Share with community
- **Both First-Class**: Not "SDK with a CLI bolt-on", but "Tool + SDK by design"
- **Choose Your Path**: Use built-in tools, or extend with Python—your choice

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

## 🚀 Current State: v2.7.2 (2025-10-18)

### Already Available ✅

**For Personal Users (No Coding Required)**:
- **Chat Interface**: Claude Code-like experience with 8 built-in tools
- **Web Search**: Brave Search with automatic caching (70% faster on repeat queries)
- **YouTube Analysis**: Transcript extraction + metadata for any video
- **Multimodal Files**: Analyze images, PDFs, audio, video files
- **Smart Search**: Results cached automatically for instant repeat queries
- **Runtime Flexibility**: Switch models mid-conversation (`/model gpt-5-mini`)
- **Session Management**: Save/load conversations, clear history

**For Developers (SDK Users)**:
- **@agent Decorator**: One line to create an AI agent with full type safety
- **Hybrid LLM Backend**: OpenAI SDK (fast) + LiteLLM (multi-provider)
- **Memory & RAG**: ChromaDB-powered semantic search for conversation history
- **MCP Integration**: 15 built-in tools exposed via Model Context Protocol
- **Automatic Telemetry**: Track tokens, costs, performance automatically
- **Testing Framework**: Mock LLM calls, parallel test execution (24-80% faster)
- **Type Safety**: Pyright strict mode with 0 errors across 1,300+ tests

**Performance & Quality**:
- ✅ CLI startup: 0.5s (98.7% faster than v2.4)
- ✅ Search caching: 70% response time reduction
- ✅ 1,300+ tests passing (>90% coverage)
- ✅ Production-ready stability

---

## 🔜 Coming in v3.0: Personal Assistant Focus

### What's Being Added

1. **Dedicated Personal Tools** (NEW)
   - `daily_news()` - Morning news briefing
   - `weather_forecast()` - Weather updates
   - `search_recipes()` - Recipe suggestions with ingredients
   - `find_events()` - Event search by location and date

2. **Enhanced Meta Agent** (Extension of RFC-005)
   - `/create agent` command directly in chat
   - Auto-save generated agents to `~/.kagura/agents/`
   - Auto-registration with AgentRouter
   - Example: "Create an agent that summarizes morning news"

3. **Chat Statistics** (NEW)
   - `/stats` - Real-time token/cost breakdown
   - `/stats summary` - AI-generated session insights
   - `/stats export` - Export to JSON/CSV for analysis

4. **Documentation Refresh**
   - Personal use case focus (not enterprise)
   - 5-minute quickstart guide
   - Real-world examples (daily briefing, recipe search, event finder)

### What's Being Simplified

- **Focus Shift**: Enterprise → Personal daily use
- **Documentation**: Rewritten for individual users first, developers second
- **Examples**: Practical personal workflows instead of abstract patterns
- **Architecture**: Keep what works, remove complexity that doesn't serve personal use

---

## 📊 Success Metrics

### Technical Metrics (v2.7.2 Status)
- ✅ **Test coverage > 90%** - Achieved (1,300+ tests, >90% coverage)
- ✅ **Type safety** - Achieved (Pyright strict, 0 errors)
- ✅ **Startup time < 1s** - Achieved (0.5s, 98.7% improvement)
- ✅ **Memory footprint** - Achieved (lazy loading, minimal dependencies)
- ✅ **Search performance** - Achieved (70% faster with caching)

### User Metrics (v3.0 Goals)
- 🔲 Time to first chat: < 5 minutes (`pip install && kagura chat`)
- 🔲 Personal tool usage: Daily news/weather/recipes work out-of-box
- 🔲 Agent creation: < 2 minutes with enhanced `/create agent`
- 🔲 Documentation clarity: New user creates custom agent in < 30 minutes

### Community Metrics (v3.0+ Goals)
- 🔲 100+ users trying personal assistant features
- 🔲 50+ custom agents shared in community
- 🔲 10+ real-world personal workflows in `examples/`
- 🔲 Positive feedback on simplicity and daily usefulness

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
