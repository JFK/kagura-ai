# Coding Memory - Technical Design Document

**Version:** 1.0
**Status:** Implemented (Phase 1)
**Date:** 2025-01-15
**Issue:** #464

## Executive Summary

Coding Memory is a specialized memory system for AI coding assistants that maintains cross-session context, learns from error patterns, and tracks project evolution. This document details the technical design, architecture, and implementation.

## Goals

### Primary Goals

1. **Cross-Session Context Retention** - AI assistants remember past decisions, errors, and patterns across sessions
2. **Error Pattern Learning** - Automatically identify recurring errors and suggest solutions
3. **Project Structure Understanding** - Maintain comprehensive project context for better suggestions

### Secondary Goals

4. **Multimodal Support** - Analyze error screenshots and architecture diagrams
5. **Design Decision Tracking** - Record and retrieve architectural choices with rationale
6. **Coding Preference Extraction** - Learn developer's style and patterns

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  AI Coding Assistant                        │
│            (Claude Code, Cursor, Copilot, etc.)            │
└──────────────────┬──────────────────────────────────────────┘
                   │ MCP Protocol
                   ▼
┌─────────────────────────────────────────────────────────────┐
│               Kagura MCP Server                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          8 Coding MCP Tools                           │  │
│  │  - coding_track_file_change                          │  │
│  │  - coding_record_error                                │  │
│  │  - coding_record_decision                             │  │
│  │  - coding_start_session                               │  │
│  │  - coding_end_session                                 │  │
│  │  - coding_search_errors                               │  │
│  │  - coding_get_project_context                         │  │
│  │  - coding_analyze_patterns                            │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│            CodingMemoryManager                              │
│  (Extends base MemoryManager)                              │
│                                                              │
│  Scope: user_id + project_id (2-tier hierarchy)            │
│                                                              │
│  Core Features:                                             │
│  ├─ track_file_change()      - File modification tracking  │
│  ├─ record_error()            - Error capture with vision  │
│  ├─ record_decision()         - Design decision logging    │
│  ├─ start_coding_session()    - Session initiation         │
│  ├─ end_coding_session()      - Session summary (LLM)      │
│  ├─ search_similar_errors()   - Semantic error search      │
│  ├─ get_project_context()     - AI-generated context       │
│  └─ analyze_coding_patterns() - Style/preference extraction│
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├──> Working Memory (active session)
                   ├──> Persistent Memory (SQLite/PostgreSQL)
                   ├──> RAG (ChromaDB) - Semantic search
                   └──> Graph (NetworkX) - Relationships
                   │
                   ├──> CodingAnalyzer (LLM integration)
                   └──> VisionAnalyzer (multimodal)
```

### Data Models

#### FileChangeRecord

```python
class FileChangeRecord(BaseModel):
    file_path: str
    action: Literal["create", "edit", "delete", "rename", "refactor", "test"]
    diff: str  # Summary or git-style diff
    reason: str  # WHY this change was made (critical)
    related_files: list[str]
    timestamp: datetime
    session_id: str | None
    line_range: tuple[int, int] | None
```

**Design Rationale:**
- `reason` field is critical - captures intent, not just what changed
- `related_files` enables dependency tracking
- `action` enum ensures consistent categorization
- `line_range` optional but useful for large files

#### ErrorRecord

```python
class ErrorRecord(BaseModel):
    error_type: str  # TypeError, SyntaxError, etc.
    message: str
    stack_trace: str
    file_path: str
    line_number: int
    solution: str | None  # Filled after resolution
    screenshot_path: str | None
    screenshot_base64: str | None
    frequency: int  # How many times this pattern occurred
    timestamp: datetime
    session_id: str | None
    tags: list[str]
    resolved: bool
```

**Design Rationale:**
- Supports both `screenshot_path` and `screenshot_base64` for flexibility
- `frequency` enables pattern detection (recurring errors)
- `solution` field crucial for learning from past resolutions
- `resolved` flag separate from `solution` (solution might exist but not applied yet)

#### DesignDecision

```python
class DesignDecision(BaseModel):
    decision: str  # Brief statement
    rationale: str  # Detailed reasoning
    alternatives: list[str]  # Other options considered
    impact: str  # Expected effect
    tags: list[str]
    related_files: list[str]
    timestamp: datetime
    confidence: float  # 0.0-1.0
    reviewed: bool
```

**Design Rationale:**
- `alternatives` captures decision-making process
- `confidence` quantifies certainty
- `related_files` links decisions to implementation

#### CodingSession

```python
class CodingSession(BaseModel):
    session_id: str
    user_id: str
    project_id: str
    description: str
    start_time: datetime
    end_time: datetime | None
    files_touched: list[str]
    errors_encountered: int
    errors_fixed: int
    decisions_made: int
    summary: str | None  # AI-generated
    tags: list[str]
    success: bool | None

    @property
    def duration_minutes(self) -> float | None

    @property
    def is_active(self) -> bool
```

**Design Rationale:**
- Tracks statistics for pattern learning
- `summary` AI-generated for comprehensive review
- `success` optional (not all sessions have clear success criteria)
- Properties for convenient duration/status checks

### Memory Scoping

**Scope Hierarchy:** `user_id + project_id`

```python
# Key format
key = f"project:{project_id}:{resource_type}:{resource_id}"

# Examples
"project:kagura-ai:file_change:change_abc123"
"project:kagura-ai:error:error_def456"
"project:kagura-ai:session:session_ghi789"
```

**Rationale:**
- `user_id` handled by base MemoryManager
- `project_id` added at CodingMemoryManager level
- Enables project-isolated memory
- Future: Could extend to `project_id + branch_id` for Git branch scoping

### LLM Integration

#### CodingAnalyzer

**Purpose:** LLM-powered analysis with carefully crafted prompts

**Key Methods:**

1. **`summarize_session()`**
   - Input: Session, file changes, errors, decisions
   - Output: Markdown-formatted comprehensive summary
   - Model: GPT-4 / Claude 3 Opus (high quality)
   - Temperature: 0.3 (consistent but creative)

2. **`analyze_error_patterns()`**
   - Input: List of errors
   - Output: CodingPattern objects
   - Model: GPT-4 (pattern recognition)
   - Temperature: 0.2 (deterministic)

3. **`suggest_solution()`**
   - Input: Current error + similar past errors
   - Output: Solution with confidence + alternatives
   - Model: GPT-4
   - Temperature: 0.3

4. **`extract_coding_preferences()`**
   - Input: File changes + decisions
   - Output: Structured preferences dict
   - Model: GPT-4
   - Temperature: 0.1 (very deterministic)

5. **`compress_context()` (RFC-024)**
   - Input: Full context + target tokens
   - Output: 3 levels (brief, detailed, comprehensive)
   - Model: GPT-4
   - Temperature: 0.2

#### Prompt Engineering

**Core Principles:**

1. **Few-Shot Learning**
   - Include 1-2 examples of desired output
   - Demonstrate format and structure

2. **Structured Output**
   - Request YAML/JSON for machine-parseable results
   - Specify exact schema

3. **Chain-of-Thought**
   - Ask for reasoning before conclusion
   - "Explain your analysis, then provide recommendations"

4. **Role Definition**
   - Clear system prompt defining AI's role
   - "You are an expert software engineering assistant..."

5. **Constraints**
   - Explicit dos and don'ts
   - "Do NOT just describe, provide actionable solutions"

**Example Prompt Structure:**

```
[System]
You are an expert software engineering assistant specializing in...

Your role:
- Analyze coding activities comprehensively
- Extract key technical decisions
- Provide actionable insights

Output requirements:
- Use clear, structured markdown
- Focus on "why" not just "what"
- Include specific examples

[User]
Analyze the following coding session:

## Session Information
...

## Task
Generate a structured summary covering:
1. Session Overview
2. Key Technical Decisions
3. Challenges & Solutions
4. Patterns Observed
5. Recommendations

## Example Output Structure
```markdown
# Session Summary
...
```

Now generate the summary:
```

See `src/kagura/llm/prompts.py` for complete templates.

### Vision Integration

#### VisionAnalyzer

**Purpose:** Multimodal analysis for images

**Key Methods:**

1. **`analyze_error_screenshot()`**
   - Extracts: error type, message, file/line, stack trace, code context
   - Model: GPT-4 Vision / Claude 3 Vision
   - Temperature: 0.1 (precise extraction)

2. **`analyze_architecture_diagram()`**
   - Extracts: components, relationships, data flow, tech stack
   - Model: GPT-4 Vision
   - Temperature: 0.3 (interpretation)

3. **`extract_code_from_image()`**
   - OCR + understanding
   - Model: GPT-4 Vision
   - Temperature: 0.0 (exact extraction)

**Image Handling:**
- Supports file paths and base64 encoded
- Automatic base64 encoding for file paths
- Compression before API call (reduce tokens)

### Storage Strategy

#### Working Memory (in-memory)

**Use:** Active session data

```python
self.working.set(f"session:{session_id}", session_data)
```

**Lifecycle:** Cleared when session ends

#### Persistent Memory (SQLite/PostgreSQL)

**Use:** Long-term storage

```python
await self.persistent.store(
    key=f"project:{project_id}:error:{error_id}",
    value=error_data,
    user_id=user_id
)
```

**Schema:**
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,  -- JSON serialized
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key)
);

CREATE INDEX idx_user_key ON memories(user_id, key);
CREATE INDEX idx_created_at ON memories(created_at);
```

#### RAG (ChromaDB)

**Use:** Semantic search

```python
await self.persistent_rag.add_memory(
    memory_id=error_id,
    content=f"Error: {type}\nMessage: {message}...",
    metadata={"type": "error", "project_id": project_id},
    user_id=user_id
)

# Search
results = await self.persistent_rag.search(
    query="TypeError comparing datetimes",
    k=5,
    user_id=user_id,
    filters={"type": "error", "project_id": project_id}
)
```

**Collection Structure:**
- One collection per project: `kagura_{agent_name}_{project_id}_persistent`
- User scoping via metadata filter

#### Graph (NetworkX)

**Use:** Relationship tracking

```python
# Add nodes
self.graph.add_memory_node(
    memory_id=change_id,
    content=f"Edit {file_path}",
    memory_type="file_change",
    metadata={"project_id": project_id}
)

# Link relationships
self.graph.link_memories(
    src_id=session_id,
    dst_id=change_id,
    relation="includes",
    weight=1.0
)
```

**Relationship Types:**
- `includes` - Session includes change/error/decision
- `affects` - File change affects related files
- `related_to` - General relationship
- `resolved_by` - Error resolved by solution

## Implementation Details

### Session Workflow

```
1. User starts session
   ↓
2. coding_start_session()
   ↓
3. Session record created (working + persistent)
   ↓
4. User makes changes
   ↓
5. coding_track_file_change() (multiple calls)
   - Each change linked to session in graph
   ↓
6. User encounters/fixes errors
   ↓
7. coding_record_error() (multiple calls)
   - Each error linked to session
   ↓
8. User makes design decisions
   ↓
9. coding_record_decision() (multiple calls)
   - Each decision linked to session
   ↓
10. User ends session
    ↓
11. coding_end_session()
    ↓
12. System gathers all session activities
    ↓
13. LLM generates comprehensive summary
    ↓
14. Session updated with summary
    ↓
15. Session moved from working → persistent only
```

### Error Search Workflow

```
1. User encounters error
   ↓
2. coding_search_errors(query)
   ↓
3. RAG semantic search (filters: type=error, project_id)
   ↓
4. Top k candidates retrieved
   ↓
5. Full error records fetched from persistent storage
   ↓
6. Return ErrorRecord objects
   ↓
7. (Optional) User calls coding_record_error with solution
   ↓
8. Future searches benefit from new solution
```

### Pattern Learning Workflow

```
1. coding_analyze_patterns()
   ↓
2. Retrieve last N file changes (e.g., 50)
   ↓
3. Retrieve last N decisions (e.g., 30)
   ↓
4. LLM analyzes for patterns:
   - Language preferences (type hints, docstrings)
   - Library choices
   - Naming conventions
   - Code organization preferences
   - Testing practices
   ↓
5. Return structured preferences dict
   ↓
6. AI assistant uses preferences for code generation
```

## Performance Considerations

### Token Usage

**Typical session summary:**
- Input: ~2000 tokens (session data)
- Output: ~1500 tokens (summary)
- Total: ~3500 tokens
- Cost: ~$0.15 (GPT-4)

**Pattern analysis:**
- Input: ~5000 tokens (50 changes + 30 decisions)
- Output: ~2000 tokens (preferences)
- Total: ~7000 tokens
- Cost: ~$0.30 (GPT-4)

**Optimization strategies:**
1. **Use cheaper models for simple tasks**
   - GPT-3.5-turbo for basic summaries ($0.02 vs $0.15)
2. **Cache frequently accessed contexts**
   - Project context cached for 1 hour
3. **Batch multiple analyses**
   - Analyze patterns once per day, not per session

### Query Performance

**RAG search:**
- Typical: 10-50ms (vector similarity)
- With filters: 15-60ms
- Top-k retrieval: O(log n) with HNSW index

**Graph traversal:**
- 1-hop: <10ms
- 2-hop: 10-50ms
- 3-hop: 50-200ms

**Persistent storage:**
- SQLite: <5ms per query (indexed)
- PostgreSQL: <10ms per query

## Security Considerations

### Data Privacy

- All data scoped to `user_id`
- Project isolation via `project_id`
- No cross-user data access
- Screenshots stored locally or in user-controlled storage

### LLM API Security

- API keys stored in environment variables
- No sensitive code sent to LLM by default
- User can disable LLM features entirely
- Vision analysis optional (user consent required)

### Access Control

- MCP tool level: All tools require `user_id` + `project_id`
- Storage level: User scoping enforced at persistence layer
- API level: API key authentication (Phase C feature)

## Testing Strategy

### Unit Tests

**Data Models:** (`tests/core/memory/models/test_coding.py`)
- Pydantic validation
- Property methods (duration, is_active)
- Edge cases (negative line numbers, invalid enums)

**CodingMemoryManager:** (`tests/core/memory/test_coding_memory.py`)
- File change tracking
- Error recording (with/without screenshot)
- Decision recording
- Session management
- Search functionality

**CodingAnalyzer:** (`tests/llm/test_coding_analyzer.py`)
- Mock LLM responses
- Prompt generation
- Token counting
- Error handling

**VisionAnalyzer:** (`tests/llm/test_vision.py`)
- Image loading (path vs base64)
- Mock vision API responses
- Error screenshot analysis
- Diagram interpretation

### Integration Tests

**E2E Session Workflow:** (`tests/integration/test_coding_e2e.py`)
1. Start session
2. Track multiple file changes
3. Record errors
4. Record decisions
5. End session
6. Verify summary generated
7. Search for errors
8. Verify RAG and graph updated

**MCP Tools:** (`tests/mcp/builtin/test_coding.py`)
- All 8 tools callable
- JSON parameter parsing
- Error handling
- Return value format

### Prompt Quality Tests

**Output Coherence:**
- Manual review of LLM outputs
- Structured format validation (YAML/JSON parsing)

**Response Time:**
- Monitor LLM latency
- Alert if >30s (indicates issue)

## Future Enhancements

### Phase 2: Graph Integration (Issue #464)

- Automatic dependency graph from `import` statements
- Cross-file refactoring impact analysis
- Error → solution relationship tracking
- Design decision → implementation linking

### Phase 3: API & CLI

- REST API endpoints for non-MCP clients
- CLI commands (`kagura coding start`, etc.)
- Export/import (JSONL format)

### Phase 4: Advanced Features

- Proactive error prevention (suggest fixes before errors occur)
- Cross-project pattern aggregation
- Team-level insights (aggregate across developers)
- Custom pattern definition (user-defined anti-patterns)

## References

- [Issue #464](https://github.com/JFK/kagura-ai/issues/464) - Implementation
- [RFC-024: Context Compression](../ai_docs/archive/rfcs/completed/RFC_024_CONTEXT_COMPRESSION.md)
- [MEMORY_STRATEGY.md](MEMORY_STRATEGY.md) - Overall memory strategy
- [User Guide](../docs/coding-memory.md)
- [Prompt Templates](../src/kagura/llm/prompts.py)

---

**Document Version:** 1.0
**Last Updated:** 2025-01-15
**Authors:** Claude Code + @JFK
