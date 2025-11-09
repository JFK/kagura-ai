# Coding Memory Module

**Coding-specialized memory manager for AI coding assistants**

## Overview

The `coding` module provides project-scoped memory management specifically designed for AI-powered coding workflows. It extends the base `MemoryManager` with features for tracking development sessions, file changes, errors, design decisions, and more.

## Phase 3 Refactoring Status

### Current State (PR #618-1 - Foundation)

**Structure:**
```
core/memory/coding/
├── __init__.py         # Public API facade
├── manager.py          # CodingMemoryManager implementation (2,116 lines)
└── README.md           # This file
```

**Status:** ✅ Foundation established
- Moved entire implementation from `coding_memory.py` into `coding/` subpackage
- Maintained 100% backward compatibility (old import paths still work)
- All tests passing (5/5 RAG tests, MCP tools tests)
- Type checking: 0 errors

### Future PRs (Planned)

**PR #618-2: Isolated Features**
- Extract `file_tracker.py` (~200 lines)
- Extract `error_recorder.py` (~250 lines)
- Extract `decision_recorder.py` (~150 lines)

**PR #618-3: Analyzers**
- Extract `analyzers.py` (~300 lines)
  - Pattern analysis
  - Dependency analysis
  - Project context

**PR #618-4: Session Management**
- Extract `session_manager.py` (~350 lines)
  - Session lifecycle (start/resume/end)
  - Auto-save and detection

**PR #618-5: GitHub Integration**
- Extract `github_integration.py` (~250 lines)
  - Issue linking
  - PR description generation

**Final Target:**
```
core/memory/coding/
├── __init__.py                # Public API facade (~100 lines)
├── manager.py                 # Core manager (~400 lines)
├── session_manager.py         # Session lifecycle (~350 lines)
├── file_tracker.py            # File change tracking (~200 lines)
├── error_recorder.py          # Error recording & search (~250 lines)
├── decision_recorder.py       # Design decision tracking (~150 lines)
├── github_integration.py      # GitHub integration (~250 lines)
├── analyzers.py               # Analysis & context (~300 lines)
└── README.md                  # Documentation
```

## Usage

### Import Paths (Both Work)

```python
# New preferred path
from kagura.core.memory.coding import CodingMemoryManager

# Legacy path (still supported)
from kagura.core.memory.coding_memory import CodingMemoryManager
```

### Basic Usage

```python
from kagura.core.memory.coding import CodingMemoryManager

# Initialize
memory = CodingMemoryManager(
    user_id="developer@example.com",
    project_id="my-project",
)

# Start coding session
session_id = await memory.start_coding_session(
    description="Implement user authentication feature",
    tags=["feature", "auth"],
)

# Track file changes
change_id = await memory.track_file_change(
    file_path="src/auth.py",
    action="create",
    diff="+ def authenticate(user, password): ...",
    reason="Initial authentication implementation",
)

# Record errors (for learning)
error_id = await memory.record_error(
    error_type="TypeError",
    message="'NoneType' object is not callable",
    stack_trace="...",
    file_path="src/auth.py",
    line_number=42,
    solution="Added null check before function call",
)

# Record design decisions
decision_id = await memory.record_decision(
    decision="Use JWT tokens for session management",
    rationale="Stateless, scalable, industry standard",
    alternatives=["Session cookies", "API keys"],
)

# End session
summary = await memory.end_coding_session(
    success=True,
    save_to_github=True,  # Post summary to linked GitHub Issue
)
```

### GitHub Integration

```python
# Link session to GitHub Issue
await memory.link_session_to_github_issue(issue_number=123)

# Generate PR description from session
pr_description = await memory.generate_pr_description()
```

### Search & Analysis

```python
# Search similar errors
similar_errors = await memory.search_similar_errors(
    query="TypeError None not callable",
    k=5,
)

# Get project context
context = await memory.get_project_context(focus="authentication")

# Analyze coding patterns
patterns = await memory.analyze_coding_patterns()
```

## Architecture

### Key Components

1. **CodingMemoryManager** - Main class, extends `MemoryManager`
   - Inherits: working memory, persistent memory, RAG, graph memory
   - Adds: coding-specific tracking and analysis

2. **CodingAnalyzer** - LLM-powered code analysis
   - Session summarization
   - Pattern extraction
   - Context generation

3. **VisionAnalyzer** - Multimodal analysis
   - Screenshot analysis for error reports
   - Diagram understanding

4. **DependencyAnalyzer** - Static analysis
   - File dependency tracking
   - Refactoring impact analysis

5. **GitHubRecorder** - External integration
   - GitHub Issue commenting
   - Automatic linking

6. **InteractionTracker** - AI-User interactions
   - Hybrid buffering
   - Importance classification

7. **MemoryAbstractor** - Context compression
   - 2-level abstraction
   - Cost-efficient summarization

### Data Models

All models are defined in `core/memory/models/coding.py`:

- **CodingSession** - Development session metadata
- **FileChangeRecord** - File modification tracking
- **ErrorRecord** - Error and solution storage
- **DesignDecision** - Architectural choices with rationale
- **ProjectContext** - Aggregated project state
- **CodingPattern** - Learned preferences and patterns

## Development

### Running Tests

```bash
# Coding memory RAG tests
pytest tests/core/memory/test_coding_memory_rag.py -v

# MCP coding tools integration
pytest tests/mcp/builtin/test_coding_tools.py -v

# End-to-end tests
pytest tests/integration/test_coding_e2e.py -v

# All coding-related tests
pytest tests/ -k "coding" -v
```

### Type Checking

```bash
pyright src/kagura/core/memory/coding/ --level error
```

### Code Quality

```bash
ruff check src/kagura/core/memory/coding/
ruff format src/kagura/core/memory/coding/
```

## Backward Compatibility

**100% backward compatible** - All existing code continues to work:

```python
# Old code (still works)
from kagura.core.memory.coding_memory import CodingMemoryManager

# New code (preferred)
from kagura.core.memory.coding import CodingMemoryManager

# Both import the exact same class
```

**No breaking changes** - All public methods and attributes remain identical.

## Contributing

When adding new features to `CodingMemoryManager`:

1. **Determine the right module** based on future structure:
   - Session-related → `session_manager.py` (when created)
   - File tracking → `file_tracker.py` (when created)
   - Error handling → `error_recorder.py` (when created)
   - Analysis → `analyzers.py` (when created)

2. **For now (PR #618-1)**: Add to `manager.py` (will be refactored in future PRs)

3. **Add tests**: Every new method needs corresponding tests

4. **Update models**: If adding new data types, update `models/coding.py`

5. **Document**: Add docstrings (Google format) with examples

## See Also

- `core/memory/models/coding.py` - Data models
- `mcp/tools/coding/` - MCP tool wrappers
- `llm/coding_analyzer.py` - LLM analysis logic
- `ai_docs/ARCHITECTURE.md` - Overall architecture
- `ai_docs/MEMORY_STRATEGY.md` - Memory system design

## License

Part of Kagura AI - MIT License
