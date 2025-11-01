# Coding Memory - AI Coding Assistant Memory System

**Status:** Phase 1 Complete (v4.1.0)
**Target Users:** AI Coding Assistants (Claude Code, Cursor, GitHub Copilot, etc.)

## Overview

Coding Memory is a specialized memory system for AI coding assistants that maintains context across sessions, learns from error patterns, and tracks project evolution.

### Key Features

✅ **Cross-Session Context** - Remember coding decisions, errors, and patterns across sessions
✅ **Error Pattern Learning** - Automatically suggest solutions based on past resolutions
✅ **Project Structure Understanding** - Maintain comprehensive project context
✅ **Multimodal Support** - Analyze error screenshots and architecture diagrams
✅ **Design Decision Tracking** - Record and retrieve architectural decisions with rationale
✅ **Coding Session Management** - Group related activities with AI-powered summaries

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  CodingMemoryManager                        │
│  (Extends base MemoryManager with coding features)         │
├─────────────────────────────────────────────────────────────┤
│  Scope: user_id + project_id                                │
│                                                              │
│  Storage:                                                    │
│  ├─ Working Memory (active session)                        │
│  ├─ Persistent Memory (SQLite/PostgreSQL)                  │
│  ├─ RAG (ChromaDB) - Semantic search                       │
│  └─ Graph (NetworkX) - Relationships                       │
│                                                              │
│  LLM Integration:                                           │
│  ├─ Session summarization (GPT-4/Claude)                   │
│  ├─ Error pattern analysis                                  │
│  ├─ Solution suggestions                                    │
│  ├─ Preference extraction                                   │
│  └─ Context compression (RFC-024)                          │
│                                                              │
│  Vision Integration:                                        │
│  ├─ Error screenshot analysis                               │
│  ├─ Architecture diagram interpretation                     │
│  └─ Code extraction from images                            │
└─────────────────────────────────────────────────────────────┘
```

## MCP Tools

Kagura provides 8 MCP tools for coding assistants:

### 1. `coding_track_file_change`

Track file modifications with context.

```python
await coding_track_file_change(
    user_id="dev_john",
    project_id="api-service",
    file_path="src/auth.py",
    action="edit",  # create, edit, delete, rename, refactor, test
    diff="+ def validate_token(token: str) -> bool:\n+     ...",
    reason="Add JWT token validation for auth middleware",
    related_files='["src/middleware.py"]',
    line_range="42,57"  # Optional
)
```

### 2. `coding_record_error`

Record errors with optional screenshots.

```python
await coding_record_error(
    user_id="dev_john",
    project_id="api-service",
    error_type="TypeError",
    message="can't compare offset-naive and offset-aware datetimes",
    stack_trace="Traceback:\n  File 'auth.py', line 42...",
    file_path="src/auth.py",
    line_number=42,
    solution="Use datetime.now(timezone.utc) consistently",  # After fixing
    screenshot="/path/to/error_screenshot.png",  # Optional
    tags='["datetime", "timezone"]'
)
```

### 3. `coding_record_decision`

Record design decisions with rationale.

```python
await coding_record_decision(
    user_id="dev_john",
    project_id="api-service",
    decision="Use JWT tokens for authentication",
    rationale="Stateless auth enables horizontal scaling. No session storage needed.",
    alternatives='["Session-based auth", "OAuth only"]',
    impact="Eliminates session store, requires key rotation strategy",
    tags='["architecture", "security"]',
    related_files='["src/auth.py", "src/middleware.py"]',
    confidence=0.9
)
```

### 4. `coding_start_session`

Start a tracked coding session.

```python
session_id = await coding_start_session(
    user_id="dev_john",
    project_id="api-service",
    description="Implement JWT authentication system",
    tags='["feature", "authentication"]'
)
```

### 5. `coding_end_session`

End session with AI-generated summary.

```python
result = await coding_end_session(
    user_id="dev_john",
    project_id="api-service",
    summary=None,  # Let AI generate summary
    success=True
)

print(result['summary'])  # AI-generated comprehensive summary
```

### 6. `coding_search_errors`

Search past errors semantically.

```python
similar_errors = await coding_search_errors(
    user_id="dev_john",
    project_id="api-service",
    query="TypeError comparing datetime objects",
    k=5  # Return top 5 similar errors
)
```

### 7. `coding_get_project_context`

Get comprehensive project context.

```python
context = await coding_get_project_context(
    user_id="dev_john",
    project_id="api-service",
    focus="authentication"  # Optional focus area
)

print(context)  # Project summary, tech stack, recent changes, decisions, patterns
```

### 8. `coding_analyze_patterns`

Analyze coding patterns and preferences.

```python
patterns = await coding_analyze_patterns(
    user_id="dev_john",
    project_id="api-service"
)

print(patterns)  # Language prefs, library choices, naming conventions, etc.
```

## Usage Example: Typical Session

```python
# 1. Start session
session_id = await coding_start_session(
    user_id="dev_john",
    project_id="kagura-ai",
    description="Implement coding memory system",
    tags='["feature", "memory"]'
)

# 2. Track file changes
await coding_track_file_change(
    user_id="dev_john",
    project_id="kagura-ai",
    file_path="src/kagura/core/memory/coding_memory.py",
    action="create",
    diff="New file: CodingMemoryManager class",
    reason="Create coding-specialized memory manager"
)

# 3. Record errors (if any)
await coding_record_error(
    user_id="dev_john",
    project_id="kagura-ai",
    error_type="ImportError",
    message="No module named 'litellm'",
    stack_trace="...",
    file_path="src/kagura/llm/coding_analyzer.py",
    line_number=8,
    solution="Added litellm to dependencies"
)

# 4. Record design decisions
await coding_record_decision(
    user_id="dev_john",
    project_id="kagura-ai",
    decision="Use LiteLLM for model abstraction",
    rationale="Unified interface for OpenAI, Anthropic, Google models",
    alternatives='["Direct API calls", "LangChain"]',
    impact="Easy model switching, better error handling"
)

# 5. End session with AI summary
result = await coding_end_session(
    user_id="dev_john",
    project_id="kagura-ai",
    success=True
)

print(f"Session completed in {result['duration_minutes']} minutes")
print(f"Summary:\n{result['summary']}")
```

## Prompt Engineering

Coding Memory uses carefully crafted prompts for high-quality LLM outputs:

### Session Summary Prompt
- **Few-shot examples** for consistency
- **Structured output** (markdown with clear sections)
- **Chain-of-thought** reasoning for decisions
- **Actionable recommendations**

### Error Pattern Analysis Prompt
- **Pattern recognition** focus
- **Root cause analysis** beyond symptoms
- **Prevention strategies** with code examples
- **Quick fix** step-by-step instructions

### Solution Suggestion Prompt
- **Case-based reasoning** from past errors
- **Confidence scoring** (high/medium/low)
- **Alternative approaches** when applicable
- **Debugging tips** if solution fails

See `src/kagura/llm/prompts.py` for complete prompt templates.

## Configuration

Add to your `kagura.toml`:

```toml
[coding_memory]
enabled = true
llm_provider = "openai"  # or "anthropic", "google"
llm_model = "gpt-4-turbo-preview"
vision_model = "gpt-4-vision-preview"
max_session_duration_hours = 24
auto_summarize_on_end = true
enable_pattern_learning = true

[coding_memory.costs]
max_monthly_budget_usd = 500.0  # Optional cost limit
warn_at_percentage = 80.0
```

## Integration with Claude Code

1. **Add to Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {
        "USER_ID": "dev_john",
        "PROJECT_ID": "my-project"
      }
    }
  }
}
```

2. **Use tools in Claude Code**:

```
User: I'm getting a TypeError when comparing datetimes
Claude: Let me check if we've seen this before...
[calls coding_search_errors]
Claude: You've encountered this 3 times before! The solution is to use datetime.now(timezone.utc) consistently. Should I apply that fix?

User: Yes, and start tracking this session
Claude: [calls coding_start_session]
Session started! I'll track all changes.

[After fixing...]
User: Fixed! End the session
Claude: [calls coding_end_session]
Session summary: Resolved datetime comparison TypeError (recurring pattern). Applied UTC timezone fix in src/auth.py. Recommend adding pre-commit hook to catch this pattern in future.
```

## Cost Considerations

"富豪仕様" (Premium Configuration) - Cost estimates:

| Operation | Model | Cost (approx) |
|-----------|-------|---------------|
| Session summary | GPT-4 | $0.10-0.30 |
| Error analysis | GPT-4 | $0.05-0.15 |
| Screenshot analysis | GPT-4 Vision | $0.01-0.05 |
| Pattern extraction | GPT-4 | $0.20-0.50 |

**Monthly estimate:** 100 sessions × $0.50 avg = **~$50-100/month**

To reduce costs:
- Use GPT-3.5-turbo for simple summaries
- Cache frequently accessed contexts
- Batch multiple analyses together

## Multimodal Features

### Error Screenshot Analysis

```python
await coding_record_error(
    user_id="dev_john",
    project_id="api-service",
    error_type="Unknown",  # Vision AI will detect
    message="See screenshot",
    stack_trace="",
    file_path="unknown",
    line_number=0,
    screenshot="/path/to/screenshot.png"  # Vision AI extracts: error type, message, location, code context
)
```

Vision AI automatically extracts:
- Error type and message
- File path and line number
- Stack trace key frames
- Visible code context
- Suggested root cause

### Architecture Diagram Analysis

```python
from kagura.llm.vision import VisionAnalyzer

vision = VisionAnalyzer()
arch_info = await vision.analyze_architecture_diagram("docs/architecture.png")

print(arch_info['components'])  # ['API Gateway', 'Auth Service', 'Database']
print(arch_info['architecture_pattern'])  # 'Microservices'
```

## Best Practices

### 1. Always Provide Reason for Changes

❌ **Bad:**
```python
diff="Added function",
reason="Update"
```

✅ **Good:**
```python
diff="+ def validate_token(token: str) -> bool:\n+     return jwt.decode(...)",
reason="Add JWT validation to support stateless auth. Needed for mobile app integration."
```

### 2. Record Errors Immediately

Record errors when they occur, then update with solution after fixing:

```python
# When error occurs
error_id = await coding_record_error(...)

# After fixing (update with solution)
error = await memory.recall(error_id)
error.solution = "Fixed by using timezone-aware datetimes"
error.resolved = True
await memory.store(error_id, error)
```

### 3. Use Sessions for Coherent Work

Group related changes into sessions:

```python
# Good: Feature implementation session
await coding_start_session(
    description="Implement rate limiting for API endpoints",
    tags=["feature", "security", "performance"]
)
# ... all changes tracked automatically ...
await coding_end_session()

# Also good: Debugging session
await coding_start_session(
    description="Debug memory leak in background task",
    tags=["bugfix", "performance"]
)
```

### 4. Leverage Semantic Search

Use natural language queries to find relevant past errors:

```python
# Instead of exact keywords, use descriptions
await coding_search_errors(
    query="problem with async database queries not working",
    k=5
)
# Finds errors related to async/await, database operations, even if wording differs
```

## Troubleshooting

### "No similar errors found"

- Need more historical data (record errors as you encounter them)
- RAG might not be enabled (check `enable_rag=True`)
- Check project_id scope (errors are project-specific)

### "Insufficient data for pattern analysis"

- Requires 10+ file changes for basic analysis
- 30+ changes recommended for detailed insights
- Continue coding and tracking activities

### "Session already active" error

- Only one session can be active at a time
- End current session before starting new one:

```python
await coding_end_session(...)  # End current
await coding_start_session(...)  # Start new
```

## Roadmap

**Phase 2: Graph Integration** (Issue #464)
- Automatic dependency graph from imports
- Error → solution relationship tracking
- Design decision → implementation links

**Phase 3: API & CLI**
- REST API endpoints for non-MCP clients
- CLI commands (`kagura coding start`, `kagura coding analyze-patterns`)
- Export/import functionality

**Phase 4: Advanced Features**
- Cross-file refactoring recommendations
- Proactive error prevention suggestions
- Team-level pattern aggregation
- Custom pattern definition

## See Also

- [CODING_MEMORY_DESIGN.md](../ai_docs/CODING_MEMORY_DESIGN.md) - Technical design
- [RFC-024: Context Compression](../ai_docs/archive/rfcs/completed/RFC_024_CONTEXT_COMPRESSION.md)
- [Issue #464](https://github.com/JFK/kagura-ai/issues/464) - Phase 1 implementation
- [prompts.py](../src/kagura/llm/prompts.py) - Prompt engineering

---

**Contributing:** This is a new feature! Please report issues or suggest improvements at [GitHub Issues](https://github.com/JFK/kagura-ai/issues).
