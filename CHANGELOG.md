# Changelog

All notable changes to Kagura AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### ✨ Added

- TBD

---

## [4.2.4] - 2025-11-08

### 🐛 Bug Fixes

#### Memory Chunk Retrieval for Persistent RAG (#597, #598)
- **Fixed**: `get_chunk_metadata()` now searches both working and persistent RAG
- **Fixed**: `get_chunk_context()` now searches both working and persistent RAG
- **Fixed**: `get_full_document()` now searches both working and persistent RAG
- **Issue**: MCP chunk tools returned empty results for documents stored in persistent RAG
- **Solution**: Implemented fallback pattern (try working RAG first, then persistent RAG)
- **Impact**: Chunk retrieval now works correctly for both in-memory and disk-based documents

### 🧪 Testing

#### Chunk Tool Test Coverage (#598)
- **Added**: `tests/mcp/builtin/test_memory_chunks.py`
- **Coverage**: Parameter validation, edge cases, non-existent documents
- **Results**: 6 tests passing, 1 skipped
- **Verification**: Manual testing with real MCP tool calls confirmed all methods working

---

## [4.2.3] - 2025-11-08

### ✨ Added

#### Category-based Tool Filtering (#592)
- **New**: `--categories` option for `kagura mcp serve`
- **Filter**: 74 tools → specific categories only
- **Usage**:
  ```bash
  kagura mcp serve --categories coding,memory,github
  ```
- **Environment variable**: `KAGURA_MCP_CATEGORIES` for persistent config
- **Available categories**: memory (19), coding (21), github (9), brave_search (4), youtube (4), file (4), media (3), multimodal (2), meta (2), observability (2), academic (1), fact_check (1), routing (1), web (1)
- **Orthogonal to permissions**: Works alongside remote/local filtering

#### Enhanced Memory Setup UX (#594)
- **New**: `kagura memory setup` now downloads reranking model automatically
- **New**: `kagura memory install-reranking` command (direct model download)
- **Deprecated**: `kagura mcp install-reranking` (backward compatible with warning)
- **Better UX**: Memory-related commands unified under `memory` group

### 🗑️ Removed

#### Cleanup: Deprecated MCP list command (#593)
- **Removed**: `kagura mcp list` (v3.0 legacy, listed @agent functions)
- **Replacement**: Use `kagura mcp tools` to list MCP tools
- **Impact**: Minimal (command was rarely used, v4.0 is MCP-first)

### ⚡ Performance

#### Test Suite Optimization Phase 1 (#591)
- **Fixture optimization**: Memory cache changed to module-scoped
- **Expected CI speed**: 15min → 8-10min (30-40% reduction)
- **Better dev experience**: Faster local test runs
- **Implementation**: Module-scoped fixture for memory cache (reduces ChromaDB reinitialization)

### 📝 Documentation

- Updated tutorials: `kagura mcp list` → `kagura mcp tools`
- Added category filtering examples in CLI help
- Updated memory setup instructions

---

## [4.2.2] - 2025-11-07

### 🐛 Fixed

#### Critical: MCP Remote Permissions Registration (#Issue TBD)
- **Fixed**: 36 MCP tools (49%) were missing from `TOOL_PERMISSIONS`, causing them to be denied in remote contexts
- **Added**: All 74 tools now registered with proper permissions
  - Memory extended (10 tools): `memory_fetch`, `memory_fuzzy_recall`, `memory_timeline`, etc.
  - Coding memory (18 tools): `coding_start_session`, `coding_track_file_change`, etc.
  - Claude Code (2 tools): `claude_code_save_session`, `claude_code_search_past_work`
  - GitHub safe wrappers (3 tools): `gh_safe_exec`, `gh_pr_create_safe`, `gh_pr_merge_safe`
  - Academic (1 tool): `arxiv_search`
- **Security fix**: Added 6 dangerous tools with `remote: False`
  - `coding_index_source_code`: Reads server filesystem
  - `coding_analyze_file_dependencies`: Reads server filesystem
  - `coding_analyze_refactor_impact`: Reads server filesystem
  - `meta_fix_code_error`: Code generation/execution risk (RCE)
  - `gh_safe_exec`, `gh_pr_create_safe`, `gh_pr_merge_safe`: GitHub write operations
- **Cleanup**: Removed orphan permission `brave_local_search` (tool doesn't exist)

### ✅ Added

#### MCP Permissions Testing & CI/CD (#Issue TBD)
- **Test coverage**: Added 2 new test classes with 8 tests
  - `TestToolRegistrationCompleteness`: Ensures all tools are registered
  - `TestNewToolPermissions`: Validates new tool classifications
- **CI/CD check**: Added automatic permissions completeness validation
  - Fails build if any tools are unregistered
  - Detects orphan permissions (registered but don't exist)
  - Runs on every PR to prevent regressions
- **Files changed**:
  - `src/kagura/mcp/permissions.py`: +34 tools, improved reason detection
  - `tests/mcp/test_permissions.py`: +107 lines of tests
  - `.github/workflows/test.yml`: +26 lines of CI checks

### 📊 Impact

- **Coverage**: 38/74 (51%) → 74/74 (100%) registered tools
- **Remote capable**: 28 → 59 tools (+31)
- **Local only**: 10 → 15 tools (+5, security fix)
- **Test coverage**: 100% of permissions now validated (30 tests)

---

## [4.2.0] - 2025-11-07

### ✨ Added

#### Upgraded Reranker to BGE-reranker-v2-m3 (#527 Phase 1)
- **New default model**: `BAAI/bge-reranker-v2-m3` (previously: `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- **Multilingual optimized**: Better performance for English, Chinese, and Japanese queries
- **License**: Apache 2.0 (same as ms-marco)
- **Model size**: ~600MB (vs 90MB for ms-marco)
- **Features**:
  - Automatic fallback to ms-marco if BGE unavailable (offline/restricted environments)
  - Graceful degradation with clear logging
  - Backward compatible - existing setups continue to work
- **Performance**:
  - Precision: Marginal improvement on easy queries, better for complex semantic matching
  - Latency: +400ms on CPU (use GPU or batch processing in production for optimal performance)
  - Multilingual queries see the most benefit
- **Files changed**:
  - `src/kagura/config/memory_config.py` - Updated default model
  - `src/kagura/core/memory/reranker.py` - Added fallback logic
  - `src/kagura/config/project.py` - Removed redundant wrapper (refactoring)
  - `tests/core/memory/test_reranker.py` - Added fallback tests (10/10 passing)
- **Benchmark**: `scripts/benchmark_reranker.py` for comparing BGE vs ms-marco

#### Semantic Chunking for Long Documents (#527 Phase 2)
- **New feature**: Automatic semantic chunking for documents >= 100 characters
- **Enabled by default**: New installs get chunking automatically (opt-out model)
- **Expected precision**: +5-15% for long documents (PDFs, transcripts, code files)
- **Implementation**:
  - Uses LangChain's `RecursiveCharacterTextSplitter` for intelligent boundary detection
  - Respects semantic boundaries: paragraphs > sentences > words
  - Configurable chunk size (default: 512 chars) and overlap (default: 50 chars)
  - Preserves original metadata across all chunks
  - Parent ID linking for chunk reconstruction
- **Files added**:
  - `src/kagura/core/memory/semantic_chunker.py` (NEW - 201 lines)
    - `SemanticChunker` class with lazy-loading
    - `ChunkMetadata` dataclass for position tracking
    - `is_chunking_available()` helper
  - `tests/core/memory/test_semantic_chunker.py` (NEW - 19/19 passing)
  - `tests/core/memory/test_rag_chunking.py` (NEW - 8/8 integration tests)
- **Files modified**:
  - `pyproject.toml` - Added `langchain-text-splitters>=0.0.1` dependency
  - `src/kagura/config/memory_config.py` - Added `ChunkingConfig` class
  - `src/kagura/core/memory/rag.py` - Integrated chunking into `store()` method
  - `src/kagura/core/memory/manager.py` - Pass chunking_config to RAG instances
  - `src/kagura/core/memory/multimodal_rag.py` - Support chunking for PDFs/documents
- **Features**:
  - ✅ Transparent chunking (backward compatible API)
  - ✅ Lazy-loading (graceful degradation if langchain unavailable)
  - ✅ Metadata preservation (original metadata in all chunks)
  - ✅ Parent ID linking (`parent_id`, `chunk_index`, `total_chunks`)
  - ✅ Batch insert for efficiency
  - ✅ Multilingual support validated (EN/ZH/JA)
- **Configuration**:
  ```python
  config = MemorySystemConfig(
      chunking=ChunkingConfig(
          enabled=True,          # Default
          max_chunk_size=512,    # Chars per chunk
          overlap=50,            # Overlap for context
          min_chunk_size=100,    # Skip chunking for short texts
      )
  )
  ```
- **Usage**:
  ```python
  # Automatic - no code changes needed
  manager = MemoryManager(user_id="user", enable_rag=True)
  doc_id = manager.store_semantic("Very long document..." * 100)
  # Automatically chunked, stored as multiple vectors

  results = manager.recall_semantic("specific topic")
  # Finds relevant chunks transparently
  ```
- **Testing**: 42/42 tests passing (22 unit + 8 integration + 10 existing RAG + 3 Japanese tests)

#### CLI Performance Optimization (#527, #548)
- **Extended Issue #548 fix** to all `kagura memory` commands
- **Affected commands**: search, list, export, import, stats, doctor
- **Optimization**: Lightweight MemorySystemConfig (reranker disabled, access_tracking disabled)
- **Speedup**: Target 8-9s → <1s (83-88% improvement)
- **Implementation**: `_get_lightweight_memory_manager()` helper function
- **Testing**: All commands use lightweight config appropriately

### 📌 Known Limitations & Future Work

#### Quick Wins Deferred to Issue #528
The following optimizations were identified but deferred to a follow-up PR:
1. **E5 Prefix Enablement** (+8-12% precision)
   - Use Embedder class with query:/passage: prefixes in ChromaDB
   - Currently using ChromaDB default (all-MiniLM-L6-v2)
2. **RecallScorer Integration** (+5-10% precision)
   - Apply composite scoring in recall_hybrid()
   - Time decay, frequency, importance weighting
3. **Time Decay Code Cleanup**
   - Remove redundant `apply_time_decay()` function
   - Use RecallScorer as single source of truth

**Total Additional Improvement**: +13-22% precision (planned for v4.2.0)

#### Current Embedding Model
- ChromaDB uses default `all-MiniLM-L6-v2` (384 dimensions)
- Custom E5-large embeddings (1024 dimensions) with query:/passage: prefixes planned for Issue #528
- No re-indexing required for existing users (backward compatible)

---

## [4.1.1] - 2025-11-06

### 🚀 Performance

#### CLI Startup Time Optimization (#548)
- **83% faster CLI startup**: Reduced from 13.9s → 2.3s (target: <3s) ✅
- **Root cause**: MemoryReranker (CrossEncoder) initialization taking 6.5s
- **Solution**:
  - Explicitly disable reranker in CLI lightweight config
  - Fixed `MemorySystemConfig.model_post_init()` to respect explicit `rerank.enabled=False`
  - Added `__pydantic_fields_set__` check to detect explicit user configuration
- **Impact**: All coding CLI commands (`sessions`, `decisions`, `errors`) now start instantly
- **Tests**: Added 4 performance regression tests in `tests/performance/test_cli_startup.py`

### 🐛 Fixed

#### ChromaDB DefaultEmbeddingFunction Import (#527)
- **Fixed**: ImportError when using ChromaDB >= 0.4.0
- **Issue**: `DefaultEmbeddingFunction` moved from `chromadb.api.types` to `chromadb.utils.embedding_functions`
- **Solution**: Try new import path first, fallback to old path for backward compatibility
- **Impact**: RAG tests now pass with both old and new ChromaDB versions
- **Files**: `src/kagura/core/memory/rag.py` (2 import locations fixed)

#### MemorySystemConfig Auto-Detection Bug (#548)
- **Critical**: `model_post_init()` was ignoring explicit `rerank.enabled=False` setting
- **Issue**: Auto-enablement (when model cached) would override user's explicit config
- **Fix**: Check `__pydantic_fields_set__` before applying auto-detection
- **Result**: CLI lightweight config now correctly disables reranker

### ✨ Added

#### Enhanced Memory Stats (#411)
- **Unused memory tracking**: Identify memories not accessed in 30/90 days
  - `unused_30days` - Memories not recalled for 30+ days
  - `unused_90days` - Memories not recalled for 90+ days
  - Based on `last_accessed_at` timestamps automatically tracked on recall
- **Storage size calculation**: Show actual disk usage
  - `storage_mb` - Total storage (SQLite + ChromaDB) in megabytes
  - Helps users understand memory footprint
- **Automatic access tracking**: `memory_recall` now tracks usage statistics
  - `access_count` - Number of times memory was recalled
  - `last_accessed_at` - Timestamp of last access
  - Enables data-driven cleanup recommendations

**Example output**:
```json
{
  "analysis": {
    "duplicates": 5,
    "old_90days": 40,
    "unused_30days": 15,
    "unused_90days": 25,
    "storage_mb": 17.8
  },
  "recommendations": [
    "25 memories unused for 90+ days - consider cleanup"
  ]
}
```

#### Interactive API Key Setup Wizard (#555)
- **`kagura config setup`** - Interactive wizard for first-time configuration
  - Guides through API key setup for OpenAI, Anthropic, Google AI, Brave Search
  - Masked password input for security
  - Preserves existing keys from .env file
  - Auto-validation after setup
  - Skip any keys you don't need
- **Better UX**: Zero-friction onboarding for new users

#### MCP Telemetry Reorganization (#555)
- **`kagura mcp telemetry tools`** - MCP tool usage analysis (new location)
  - Better CLI organization (MCP-specific commands under `mcp` group)
  - Identical functionality with CSV/JSON export support
  - Replaces removed `kagura telemetry tools` command

### 🗑️ Removed

#### Deprecated CLI Commands (#555)
- **BREAKING**: Removed `kagura telemetry` command group
  - **Migration**: Use `kagura mcp telemetry tools` instead
  - Old command: `kagura telemetry tools --since 30d`
  - New command: `kagura mcp telemetry tools --since 30d`
- **BREAKING**: Removed `kagura config show` command
  - **Migration**: Use `kagura config list` instead

**Rationale**: Cleaner CLI organization, MCP-specific commands now grouped under `mcp`

#### Auto-detect Project & User (#536)
- **Smart Defaults**: Auto-detect project and user for coding commands
  - Project detection priority: env var → pyproject.toml → git repo name → git directory
  - User detection priority: env var → pyproject.toml → git user.name → default (kiyota)
  - **Zero configuration** for most use cases (works in any git repository)
  - `kagura coding doctor` - New command to check auto-detection status

- **pyproject.toml Support**: Configure via `[tool.kagura]` section
  ```toml
  [tool.kagura]
  project = "your-project"
  user = "your-username"
  enable_reranking = true
  ```

### 🔧 Changed

#### Configuration Loading
- `KAGURA_ENABLE_RERANKING` now loads from pyproject.toml and environment
- Seamless multi-repository workflows (no need to change env vars per repo)
- Backward compatible: Environment variables still work (highest priority)

### 📝 Documentation

- Added auto-detection documentation
- Updated coding command help texts
- Added pyproject.toml configuration examples

---
## [4.0.11] - 2025-11-04

### 🐛 Fixed

#### Intel Mac (x86_64) Installation (#533)
- **Critical**: Fixed installation failure on Intel Mac due to PyTorch compatibility
  - Cap `torch` at `<2.3` (last version with Intel Mac x86_64 wheels)
  - Cap `sentence-transformers` at `<5.2` to ensure compatible torch version
  - Cap `numpy` at `<2.0` for torch 2.2.2 compatibility
  - **Impact**: Eliminates mandatory NVIDIA CUDA dependencies (~12 packages, several GB)
  - **Benefit**: All CPU-only users get smaller installation size
  - **Limitation**: Python 3.13 not supported on Intel Mac (torch 2.2.2 lacks Python 3.13 wheels for macOS x86_64)

### ✨ Added

#### Python 3.13 Support (#532)
- **Official Python 3.13 support** (Linux, Windows, macOS Apple Silicon)
  - Added Python 3.13 classifier to `pyproject.toml`
  - CI now tests Python 3.11, 3.12, and 3.13 in parallel
  - **Note**: Intel Mac (x86_64) users must use Python 3.11 or 3.12 for AI features
  - **Core features** (MCP, CLI, API) work with Python 3.13 on all platforms

#### Auto-detect Project & User (#536, #537)
- **Smart Defaults**: Auto-detect project and user for coding commands
  - Project detection priority: env var → pyproject.toml → git repo name → git directory
  - User detection priority: env var → pyproject.toml → git user.name → default (kiyota)
  - **Zero configuration** for most use cases (works in any git repository)
  - `kagura coding doctor` - New command to check auto-detection status
- **pyproject.toml Support**: Configure via `[tool.kagura]` section
  ```toml
  [tool.kagura]
  project = "your-project"
  user = "your-username"
  enable_reranking = true  # Optional: auto-detects if model is cached
  ```
- **Reranking Auto-enable**: Automatically enables reranking when model is cached (ready to use)
- **Improved Commands**:
  - `memory index`: Now indexes all users by default (not just 'system')
  - `kagura doctor`: Accurate RAG vector counting across all collections
  - `config doctor`: Fixed for gpt-5-mini and reasoning models (#535)

#### RAG Performance Improvements (#525 - Quick Wins)
- **Time-decay boosting**: Recent memories automatically ranked higher
  - `apply_time_decay()` function in `hybrid_search.py`
  - Configurable via `RecallScorerConfig.time_decay_days` (default: 30 days)
  - Expected impact: +3-7% precision improvement
- **BM25Config**: New configuration class for BM25 parameters
  - Optimized for short memory entries (k1=1.2, b=0.4)
  - Integrated into `HybridSearchConfig`

### 🔧 Changed

#### RAG Defaults (#525)
- **BM25 parameters optimized** for short texts
  - k1: 1.5 → 1.2 (reduced term frequency saturation)
  - b: 0.75 → 0.4 (reduced length normalization)
  - Expected impact: +2-5% precision improvement
  - Rationale: Memory entries are typically short (< 100 words)
  - Note: Reranking remains disabled by default for offline compatibility

### 📈 Performance

**Expected Improvement**: +5-12% RAG precision
- BM25 optimization: +2-5%
- Time-decay: +3-7%

### 📝 Documentation

- Updated CHANGELOG for v4.0.11
- Related Issues: #525 (RAG Quick Wins)

---

## [4.0.10] - 2025-11-04

### ✨ Added

#### Tool Usage Analysis (#522)
- `kagura telemetry tools` - Analyze MCP tool usage patterns
- Shows: calls, percentage, success rate, average duration
- Export to CSV/JSON for further analysis
- Categorizes: high/medium/low usage, deprecation candidates

#### Documentation (#521)
- Tool Selection Guide (`docs/en/tool-selection-guide.md`)
- 90/10 rule: Common (10 tools) vs Specialized (59 tools)
- Decision flowcharts for quick tool selection
- Usage patterns and anti-patterns
- Best practices for memory/coding/GitHub workflows

### 🔧 Changed

#### Smart Defaults (#516)
- `memory_store`: `agent_name` defaults to "global" (was required parameter)
- `memory_store`: `scope` defaults to "persistent" (was "working")
- `memory_recall`: `scope` defaults to "persistent" (was "working")
- Parameter reordering: required params first (user_id, key, value)
- **Impact**: Simpler API, safer defaults, backward compatible

#### Tool Description Optimization (#520)
- Optimized 5 high-usage tools (35% reduction)
  - coding_track_file_change: 52 → 17 lines (67%)
  - coding_start_session: 47 → 15 lines (68%)
  - coding_end_session: 63 → 18 lines (71%)
  - memory_store: 58 → 20 lines (66%)
  - memory_search: 50 → 18 lines (64%)
- Total: ~250 lines removed, ~1500 tokens saved per session
- Applied structured format: When/Args/Returns

### 🐛 Fixed

#### Error Messages (#518)
- Improved 5 critical errors with actionable guidance:
  1. RAG not enabled (3 occurrences) - now includes install steps
  2. Lexical search unavailable - includes BM25 explanation
  3. Session already active - lists recovery options
  4. No active session - shows how to start
  5. Session data not found - debugging hints
- Added emoji indicators, tips, step-by-step solutions

### 📝 Documentation

- Updated CHANGELOG for v4.0.10
- Updated version to 4.0.10 in pyproject.toml
- Closed Issues #516, #518, #520, #521, #522
- Closed Issues #515, #517, #519 (determined not needed)

---

## [4.0.9] - 2025-11-03

### ✨ Added

#### CLI Inspection & Management (#501, #504)
- `kagura doctor` - Unified system health check (Python, disk, APIs, memory, MCP)
- `kagura memory list/search/stats` - Memory inspection commands
- `kagura memory index/doctor` - RAG index building and health check
- `kagura init --setup-rag/--setup-reranking/--full` - Interactive setup
- Model constants: `src/kagura/config/models.py`

#### MCP Monitoring (#499)
- `kagura mcp monitor` - Real-time MCP tool dashboard

#### Source Code RAG (#490)
- `coding_index_source_code` - AST-based indexing with 5-line overlap
- `coding_search_source_code` - Semantic code search

#### Claude Code Integration (#491)
- `claude_code_save_session/search_past_work` - Session persistence
- `coding_end_session` - Auto-save to history (default: enabled)
- `coding_resume_session` - Resume ended sessions
- `coding_get_current_session_status` - Check progress
- Auto-save snapshots after each file change

#### Session Enhancements
- Enhanced table: start/end times, duration, active indicators
- Rich panel display for session details
- Session requirement enforcement for tracking tools

### 🔧 Changed

- Session management: Removed global cache → auto-detection
- Activity retrieval: Graph-based → session_id queries
- Search: Upgraded to hybrid search (BM25 + RAG)

### 🗑️ Removed

- `kagura memory segments` - Redundant with `kagura memory stats --breakdown-by all`
  - Use `kagura memory stats` for basic statistics
  - Use `kagura memory stats --breakdown-by user` for per-user breakdown
  - Use `kagura memory stats --breakdown-by all` for full RAG collections breakdown

### 🐛 Fixed

#### Critical Issues
- **Critical**: Session cache synchronization
- **Critical**: Memory index → persistent RAG
- **Critical**: Duration timezone handling
- EventStore/MemoryManager API compatibility

#### CLI Improvements (#509)
- `kagura memory search`: Now uses RAG semantic search instead of SQL LIKE queries
- `kagura memory doctor`: Shows accurate RAG vector counts across all ChromaDB locations
- `kagura memory doctor`: Improved reranking status check (validates installation + model cache)
- `kagura memory doctor`: Guard against UnboundLocalError when MemoryManager initialization fails
- `kagura memory search`: Handle dict-type content values to prevent TypeError
- `kagura memory stats`: Scan all ChromaDB paths for accurate RAG counts (now shows 239 vectors instead of 0)
- `kagura memory stats`: Add `--breakdown-by user/all` for per-user memory and RAG statistics
- `kagura memory stats`: Display RAG collections breakdown

#### Telemetry (#507)
- `@tool` decorator: Add tool_name logging for `kagura mcp monitor` visibility
- Both sync and async tool wrappers now record telemetry events

#### Type Safety & Code Quality
- 25+ pyright type errors fixed
- Unreachable code removed
- IndexError risks eliminated
- No-op operations removed

### 📝 Documentation

- Updated CHANGELOG for v4.0.9 final release
- Updated version to 4.0.9 in pyproject.toml
- Closed Issues #466, #491, #499, #501, #507

---

## [4.0.8] - 2025-11-03

### ✨ Added

- **Coding Memory CLI Commands** (#502)
  - `kagura coding projects`: List all projects with memory counts
  - `kagura coding sessions`: List coding sessions with filters
  - `kagura coding session <ID>`: Show detailed session information
  - `kagura coding decisions`: Browse design decisions
  - `kagura coding decision <ID>`: Show decision details with rationale
  - `kagura coding errors`: List errors with resolution status
  - `kagura coding error <ID>`: Show error details and solution
  - `kagura coding search`: Semantic search across all coding memory
  - Filters: --success, --unresolved, --min-confidence, --tag, --since, --type, --user

- **MCP Live Monitoring** (#499)
  - `kagura mcp monitor`: Live dashboard for MCP tool statistics
  - Real-time tool call counts, success rates, average execution times
  - Filter by tool name pattern (--tool)
  - Configurable refresh interval (--interval)
  - Shows last 5 minutes of activity

### 🐛 Fixed

- **Doctor Command** (#500): Now shows actual memory counts
  - Before: `Persistent: 0, RAG: 0` (always showed 0)
  - After: `Persistent: 471, RAG: 17` (actual counts across all users)
  - Queries all ChromaDB collections (sessions, API, legacy)

### 📝 Documentation

- **CLAUDE.md**: Updated workflow to recommend Kagura Coding Sessions
  - Added section: "過去の作業を参照" with CLI examples
  - Integrated Coding Session into standard workflow
  - Emphasizes using Kagura memory over ephemeral Claude context

### 🧪 Tests

- Type check: 0 errors (pyright)
- Lint: All checks passed (ruff)
- Manual verification: All commands working correctly

---

## [4.0.7] - 2025-11-03

### ✨ Added

- **Coding Memory and General Memory Integration** (#493)
  - `InteractionTracker`: Hybrid buffering strategy for AI-User interactions
    - Immediate: Buffer all interactions in Working Memory
    - High importance (>= 8.0): Async GitHub Issue recording (non-blocking)
    - Periodic: Auto-flush to Persistent Memory (10 interactions or 5 minutes)
    - Session end: Full LLM summary + comprehensive GitHub comment
  - `GitHubRecorder`: 2-stage GitHub Issue integration
    - Stage 1: Immediate high-importance event recording (concise comments)
    - Stage 2: Session-end comprehensive summary (full context)
    - Auto-detects issue number from branch name
    - Uses `gh` CLI for GitHub API access
  - `MemoryAbstractor`: 2-level memory abstraction
    - Level 1: External record → summary + keywords (lightweight LLM: gpt-5-mini)
    - Level 2: Context → patterns + concepts (powerful LLM: gpt-5 / claude / gemini)
    - Configurable LLM models for cost/quality trade-off
  - `CodingMemoryManager` integration: New optional components
    - `enable_github_recording`: Enable/disable GitHub integration
    - `enable_interaction_tracking`: Enable/disable interaction tracking
    - `enable_memory_abstraction`: Enable/disable abstraction
    - Configurable abstraction models: `abstraction_level1_model`, `abstraction_level2_model`

### 🏗️ Architecture

- **4+2 Tier Memory Hierarchy** (Foundation for Issue #493)
  - Layer 1: External Artifacts (GitHub Issues, Docs, Code Comments)
  - Layer 2: External Memory Index (Persistent Memory + RAG)
  - Layer 3: Working Context (Working Memory + RAG)
  - Layer 4: Abstracted Context (Persistent Memory + RAG)
  - Layer 5: Relationship Graph (GraphMemory)
  - Layer 6: Dependency Analysis (AST-based)

### 🎯 Performance

- **Non-blocking Architecture**
  - All external recording operations are async (non-blocking)
  - LLM importance classification runs in background
  - Periodic buffer flushing doesn't block user interactions
  - GitHub API calls use executor pattern to avoid blocking event loop

### ✨ MCP Tools

- **coding_track_interaction**: Track AI-User conversations with importance classification
  - Automatic GitHub recording for high importance (≥8.0)
  - Background LLM classification (non-blocking)
  - Supports all 6 interaction types (question, decision, struggle, discovery, implementation, error_fix)

- **coding_end_session** (extended): Added GitHub integration
  - New parameter: `save_to_github` (default: false)
  - Records comprehensive session summary to GitHub Issue
  - Includes interactions, file changes, decisions, errors

### 🔧 Improvements

- **Cost Monitoring Integration**:
  - InteractionTracker: Tracks LLM cost for importance classification
  - MemoryAbstractor: Tracks level 1 and level 2 abstraction costs separately
  - Integrates with existing `kagura.observability.pricing` system

- **GitHub Operations**:
  - **gh_pr_create_safe**: Now uses `--body-file` for safer PR creation
  - **gh_issue_create_safe**: New function with `--body-file` support
  - **gh_issue_comment**: Uses `--body-file` to avoid special character escaping
  - All operations use temporary markdown files for reliability

### 📝 Implementation Notes

- This release implements **complete Phase 1** for Issue #493
- 57 new tests added and passing
- Issue #491 integration (Claude Code auto-save) planned for v4.1.0
- Full documentation update planned for v4.1.0

### 🧪 Tests

- **57 new tests added** (all passing)
  - InteractionTracker: 16 tests
  - GitHubRecorder: 19 tests
  - MemoryAbstractor: 14 tests
  - MCP tools integration: 8 tests
- Type check (pyright): 0 errors
- Lint (ruff): All checks passed

---

## [4.0.6] - 2025-11-03

### ✨ Added

- **Enhanced Memory Recall Tools** (#496)
  - `memory_search_hybrid`: BM25 keyword + RAG semantic hybrid search with weighted RRF fusion
  - `memory_timeline`: Time-based memory retrieval (last_24h, last_week, date ranges)
  - `memory_fuzzy_recall`: Fuzzy key matching for partial/typo-tolerant recall
  - BM25Search implementation for keyword-based ranking (no LLM dependency)
  - Addresses "記憶はするが、思い出してくれない" user feedback
  - Pattern A architecture: Client-driven with enhanced search toolkit

### 🎯 Improvements

- **Memory Search Quality**
  - Hybrid search combines keyword matching (BM25) and semantic search (RAG)
  - Reciprocal Rank Fusion (RRF) for optimal result ranking
  - Fuzzy key matching with configurable similarity threshold
  - Timeline search with flexible time range specifications
  - All new tools are remote-capable (45 total remote tools)

### 🧪 Tests

- All 35 memory tests pass
- Type check (pyright): 0 errors
- Lint (ruff): All checks passed

---

## [4.0.5] - 2025-11-03

### 🐛 Fixed

- **Coding Memory Tools**: Fixed 3 critical runtime errors (#494)
  - `coding_record_decision`: Handle string confidence values (format error fix)
  - `coding_track_file_change`: Normalize action synonyms (`add`→`create`, `modify`→`edit`, etc.)
  - `coding_get_project_context`: Add template-based fallback when LLM fails
  - All errors now handled gracefully with helpful messages

### ✨ Added

- **Remote-Capable Tool Indicator** (#492)
  - `kagura mcp tools` now shows "Remote" column (✓/✗ indicators)
  - New filters: `--remote-only`, `--local-only`, `--category <name>`
  - Tool classification: 42 remote-capable, 14 local-only
  - Helps API Key permission design and remote MCP server usage
  - Created `tool_classification.py` for centralized tool metadata

### 🧪 Tests

- Added `test_action_synonym_mapping` for action normalization
- All 29 coding memory tests pass
- Type check (pyright): 0 errors
- Lint (ruff): All checks passed

---

## [4.0.4] - 2025-11-03

### ✨ Added

- **`kagura memory setup` Command**: Pre-download embeddings to avoid MCP timeout (#485)
  - Auto-detects provider based on OPENAI_API_KEY
  - OpenAI API support: Uses `text-embedding-3-large` (no download, instant)
  - Local model support: Downloads `intfloat/multilingual-e5-large` (~500MB)
  - Options: `--provider openai|local`, `--model <model-name>`
  - Prevents "No result received from client-side tool execution" error
  - Usage: `kagura memory setup` (run once before using MCP memory tools)

### 🐛 Fixed

- **MCP memory_store Tool**: Improved error handling and user feedback
  - Added try-catch for initialization errors (embeddings download timeouts, etc.)
  - Returns clear error messages instead of silent failures
  - Added initialization notice when downloading embeddings model
  - Helps diagnose "No result received from client-side tool execution" errors

### 📝 Documentation

- **Troubleshooting Guide** (EN/JA): Added "No result received" error solution
  - Clear instructions to run `kagura memory setup` before first use
  - Explains root cause (embeddings download timeout)
  - Documents both OpenAI API and local model options

---

## [4.0.2] - 2025-11-02

**Complete release** with both wheel and sdist. Identical functionality to v4.0.0.

### 🐛 Fixed

- **PyPI Release**: Complete package upload with both distribution files
  - Previous v4.0.0 had only `.whl` file (sdist upload failed)
  - v4.0.2 includes both `kagura_ai-4.0.2-py3-none-any.whl` and `kagura_ai-4.0.2.tar.gz`
  - No functional changes from v4.0.0

---

## [4.0.0] - 2025-11-02

**Note**: Package name changed from `kagura-ai` to `kagura_ai` for PyPI compatibility. Users can still install with `pip install kagura-ai` (PyPI normalizes names).

**Note**: v4.0.0 PyPI release was incomplete (missing sdist). Use v4.0.2 instead.

### 🔧 Package Changes

- **Package Name**: Changed from `kagura-ai` to `kagura_ai` in `pyproject.toml`
  - Resolves PyPI sdist filename requirement (must use underscores)
  - Updated `src/kagura/version.py` to use `kagura_ai`
  - Installation: `pip install kagura-ai` still works (PyPI normalizes)



### ✨ Added

- **MCP Tools Fixes & Enhancements** (#468, #469)
  - **Critical**: Enabled 7 previously inaccessible tools (GitHub 6 + Academic 1)
  - **GitHub tools**: Direct execution via ShellExecutor (no LLM intermediary)
  - **Multimodal**: Japanese language support (`language="ja"` parameter)
  - **API Port**: Unified to 8000 (uvicorn standard)
  - **Claude Desktop**: Windows/macOS/Linux path detection
  - **Dependencies**: Added psutil for brave-search-python-client
  - **Shell Execution**: Code generation mode (returns implementation, not execution)
  - **MCP Tool Count**: Accurate 56 tools (15 Memory + 15 Coding + 6 GitHub + 5 Brave + 4 YouTube + 11 others)

- **Neural Memory Network** (#348) - 8 commits, 2,471 lines
  - **Hebbian Learning-based adaptive memory** with graph neural architecture
  - **Activation spreading**: 1-3 hop propagation with exponential decay
  - **Co-activation tracking**: Automatic association discovery through usage patterns
  - **Unified scoring**: 6-signal composite (semantic + graph + temporal + importance + trust - redundancy)
  - **Forgetting mechanism**: Exponential weight decay, weak edge pruning, long-term consolidation
  - **Security**: GDPR-compliant user sharding, trust-modulated learning, DP-SGD gradient clipping
  - **Research-backed**: Implements Hopfield Networks, kNN-LM, RETRO, Memorizing Transformers
  - **Formula**: `Δw_ij ← η·(a_i·C_i)·(a_j·C_j) - λ·w_ij` (trust-modulated Hebbian rule)
  - **Testing**: 101 tests, 80% coverage, ruff/pyright compliant
  - **Files**: `src/kagura/core/memory/neural/` (8 files: config, models, hebbian, activation, scoring, decay, co_activation, engine, utils)

- **GitHub CLI & Safe Shell Execution** (#348) - 1 commit, 1,138 lines
  - **6 MCP GitHub Tools**:
    - `github_exec(command, force)`: General gh executor with safety
    - `github_issue_view(number)`: Formatted issue viewing
    - `github_pr_view(number)`: Formatted PR viewing
    - `github_issue_list(state, limit)`: Issue listing
    - `github_pr_create(title, body, draft, force)`: Safe PR creation
    - `github_pr_merge(number, squash, force)`: Safe PR merging
  - **3 GitHub Agents**: `gh_safe_exec`, `gh_issue_view_safe`, `gh_pr_view_safe`, `gh_pr_create_safe`, `gh_pr_merge_safe`, `gh_issue_list_safe`
  - **2 Shell Agents**: `shell_safe_exec`, `cd_and_exec`
  - **Command Safety System**: 4-level danger classification (HIGH, MEDIUM, LOW, SAFE)
  - **Automatic danger detection**: Pattern-based + optional LLM analysis
  - **Confirmation prompts**: Required for MEDIUM/HIGH danger commands
  - **Risk explanations**: Detailed risk descriptions and safe alternatives
  - **Working directory support**: `working_dir` parameter for all shell operations
  - **Permission control**: Read operations remote-safe, write operations local-only
  - **Testing**: 22 tests for safety system, 100% coverage on danger detection
  - **Files**: `src/kagura/core/shell_safety.py`, `src/kagura/builtin/github_agent.py`, `src/kagura/builtin/shell_agent.py`, `src/kagura/mcp/builtin/github.py`

- **Coding-Specialized Memory System** (#464, #466)
  - **11 MCP Tools** for AI coding assistants (Claude Code, Cursor, etc.)
    - Phase 1 (8 tools): File tracking, error recording, sessions, cost tracking
    - Phase 2 (3 tools): Dependency analysis, refactoring impact, safe order suggestion
  - **Project-scoped memory**: `user_id + project_id` hierarchy
  - **AI-powered features**:
    - Session summaries with LLM (GPT-5, Gemini, Claude)
    - Error pattern detection and solution suggestions
    - Coding preference extraction
    - Vision AI for screenshot analysis
  - **Plan Mode & Approval Workflows**:
    - Cost estimation before expensive operations
    - Rich UI approval prompts with timeout
    - Configurable cost thresholds (default: $0.10)
    - Auto-approve mode for batch operations
  - **Automatic Dependency Graph** (AST-based):
    - Parse Python imports automatically
    - Build dependency graph
    - Detect circular dependencies
    - Calculate import depth
    - Reverse dependency tracking
  - **Refactoring Intelligence**:
    - Cross-file impact analysis (risk: low/medium/high)
    - Safe refactoring order (topological sort)
    - Affected files identification
  - **Graph Relationships**:
    - Error → solution linking (`solved_by`)
    - Decision → implementation tracking (`implements`)
    - File → file dependencies (`imports`, `affects`)
    - Session activity tracking (`includes`, `encountered`, `made`)
  - **Multi-Provider Support**:
    - OpenAI: gpt-5-mini, gpt-5, gpt-4o
    - Google: gemini-2.0-flash-exp, gemini-2.5-flash, gemini-2.5-pro
    - Anthropic: claude-sonnet-4-5
  - **Prompt Engineering** (Claude Official Guidelines):
    - XML tags for structure (`<role>`, `<task>`, `<thinking>`)
    - Chain-of-thought reasoning prompts
    - Few-shot examples with structured outputs
  - **Cost Tracking**:
    - Real-time cost monitoring via `observability.pricing`
    - Per-call and cumulative tracking
    - Budget estimates: $3-200/month depending on provider
  - **Data Models**: 6 Pydantic models (FileChangeRecord, ErrorRecord, DesignDecision, CodingSession, CodingPattern, ProjectContext)
  - **Testing**: 43 tests (models, MCP tools, E2E, dependency analysis)
  - **Documentation**: Complete user guide + technical design document

### 🔒 Security

- **Fixed X-User-ID Header Trust Vulnerability** (#436)
  - Removed trust of X-User-ID header to prevent user impersonation attacks
  - Now only trusts user_id from verified API keys
  - Added KAGURA_REQUIRE_AUTH environment variable for production mode
  - Added 6 security tests for impersonation prevention
  - **Breaking Change**: Clients using X-User-ID must migrate to API key authentication

### ✨ Added

- **XDG Base Directory Compliance** (#439)
  - Platform-specific directory management following XDG specification
  - New `config/paths.py` module with get_cache_dir(), get_data_dir(), get_config_dir()
  - Environment variable override support (KAGURA_*_DIR)
  - Cross-platform: Linux (XDG), macOS (XDG), Windows (AppData)
  - **Directory structure**:
    - Cache: ~/.cache/kagura/ (deletable)
    - Data: ~/.local/share/kagura/ (persistent)
    - Config: ~/.config/kagura/ (user-editable)
  - **Breaking Change**: Path changes - existing ~/.kagura data requires manual migration

- **Progressive Disclosure for Memory Search** (#432 Phase 2)
  - `memory_search_ids`: Browse search results with ID + 50-char previews (~80% token reduction)
  - `memory_fetch`: Fetch full content by key after browsing
  - Two-step workflow for efficient token usage

- **Memory Accuracy Improvements (Phases 1 & 2)**: Enhanced memory search precision (#418)

  **Phase 1: Embeddings & Reranking**
  - **E5 Multilingual Embeddings**: Switch from all-MiniLM-L6-v2 to intfloat/multilingual-e5-large
    - 1024-dim embeddings supporting 100+ languages (including Japanese)
    - Query/passage prefix handling for optimal E5 performance
    - New `embeddings.py` module with `Embedder` class
  - **Cross-Encoder Reranking**: Two-stage retrieval for improved precision
    - Fast bi-encoder retrieval (K candidates) + accurate cross-encoder reranking (top k)
    - MS-MARCO MiniLM-L-6-v2 cross-encoder model
    - New `reranker.py` module with `MemoryReranker` class
    - Expected 10-15% improvement in top-result precision
  - **Multi-Dimensional Recall Scoring**: DNC/NTM-inspired composite scoring
    - Combines semantic similarity, recency, access frequency, graph distance, and importance
    - Configurable weights and decay parameters
    - New `recall_scorer.py` module with `RecallScorer` class
  - **Access Tracking**: Frequency-based memory usage tracking
    - Added `access_count` and `last_accessed_at` columns to memories table
    - Automatic access recording in `persistent.py`
  - **Memory Reindexing**: CLI command for embedding model migration
    - `kagura memory reindex` with batch processing and progress display
    - Dry-run mode for safe testing
    - GPU acceleration support
  - **Memory Configuration**: Centralized config with Pydantic models
    - New `memory_config.py` with `MemorySystemConfig`, `EmbeddingConfig`, `RerankConfig`, `RecallScorerConfig`
    - Type-safe configuration management

  **Phase 2: Hybrid Search**
  - **BM25 Lexical Search**: Keyword-based matching to complement vector search
    - New `lexical_search.py` with `BM25Searcher` class
    - BM25Okapi algorithm for traditional information retrieval
    - Effective for proper nouns, technical terms, Japanese kanji variants
  - **RRF Fusion**: Reciprocal Rank Fusion (SIGIR'09) for combining results
    - New `hybrid_search.py` with `rrf_fusion()` function
    - Combines vector (semantic) + lexical (keyword) results
    - Standard k=60 constant, weighted variants available
  - **Hybrid Recall**: 3-stage retrieval pipeline
    - `recall_hybrid()` method in MemoryManager
    - Vector search → Lexical search → RRF fusion → Cross-encoder reranking
    - Expected +10-15% for Japanese, +20-30% for exact keywords
  - **Updated Config**: `HybridSearchConfig` (enabled by default)
    - Configurable RRF constant, weights, candidates_k
    - Auto-initialization of BM25Searcher

  **Phase 3: Temporal GraphMemory**
  - **Temporal Edge Attributes**: Time-aware knowledge graph
    - `valid_from`: Start of validity period (defaults to now)
    - `valid_until`: End of validity period (None = still valid)
    - `source`: Evidence/source URL for relationships
    - `confidence`: Confidence score (0.0-1.0)
  - **Temporal Validation**: `is_edge_valid_at(timestamp)` method
    - Check edge validity at any point in time
    - Filter edges based on temporal bounds
    - Timezone-aware datetime handling
  - **Edge Invalidation**: `invalidate_edge()` for contradiction handling
    - Mark edges as superseded
    - Automatic `valid_until` setting
    - `invalidated` flag for audit trail
  - **Temporal Graph Queries**: `query_graph_temporal()` method
    - Multi-hop traversal with temporal filtering
    - Query current state or historical state
    - Only follows edges valid at specified timestamp
  - **Use Cases**:
    - Contradiction handling (old vs new facts)
    - Historical reasoning ("What was true in 2015?")
    - Evidence-based knowledge management
  - **Tests**: 6 new tests for temporal features
    - Temporal edge creation, validation, invalidation
    - Historical query scenarios
  - **Backward Compatible**: All new parameters optional

  **New MemoryManager methods**:
    - `recall_semantic_with_rerank()` - Semantic search with optional reranking
    - `recall_hybrid()` - Hybrid search with vector + lexical + RRF + reranking

  **Tests**: Comprehensive test coverage for Phase 1
    - `test_embeddings.py` - E5 prefix handling
    - `test_reranker.py` - Batch reranking
    - `test_recall_scorer.py` - Multi-dimensional scoring

  **Dependencies Added**:
    - `sentence-transformers>=2.2.0` - Embeddings & reranking
    - `rank-bm25>=0.2.2` - BM25 lexical search

- **Brave Image Search**: Search for images via Brave Search API (#399)
  - `brave_image_search` MCP tool
  - Parameters: query, count (1-200), safesearch (off/moderate/strict)
  - Returns: JSON with image URLs, thumbnails, titles, sources
  - Use case: Visual content discovery, illustrations, photo search

- **Brave Video Search**: Search for videos via Brave Search API (#399)
  - `brave_video_search` MCP tool
  - Parameters: query, count (1-50), safesearch
  - Returns: JSON with video URLs, thumbnails, duration, creator, views
  - Use case: Tutorial videos, demonstrations, educational content

- **arXiv Academic Search**: Search academic papers on arXiv (#399)
  - `arxiv_search` MCP tool in new `academic.py` module
  - Parameters: query, max_results (1-20), category (cs.AI, cs.LG, etc.)
  - Returns: JSON with title, authors, abstract, PDF URL, publication date
  - New dependency: `arxiv==2.2.0`
  - Use case: Research papers, scientific literature, latest preprints
  - Supported categories: cs.AI, cs.LG, cs.CL, cs.CV, physics, math, stat, q-bio

- **MCP Tool Count**: Expanded from 31 to 34 tools

- **MCP over HTTP/SSE**: New `/mcp` endpoint for ChatGPT Connectors (#378, Phase C Task 1)
  - GET `/mcp` - SSE streaming (server → client messages)
  - POST `/mcp` - JSON-RPC requests (client → server messages)
  - DELETE `/mcp` - Session termination
  - Uses MCP SDK's `StreamableHTTPServerTransport` for protocol handling
  - Auto-registers all built-in MCP tools (memory, graph, etc.)
  - Background task manages MCP server lifecycle
  - Documentation: `docs/mcp-http-setup.md`

- **API Key Authentication**: Secure authentication for remote access (#378, Phase C Task 2)
  - `APIKeyManager` for key generation, validation, and management
  - SQLite-based storage with SHA256 hashing
  - CLI commands: `kagura api create-key`, `list-keys`, `revoke-key`, `delete-key`
  - `/mcp` endpoint authentication via `Authorization: Bearer <key>` header
  - Support for key expiration and audit trails
  - Optional authentication (falls back to `default_user`)
  - User ID extraction from validated API keys

- **Tool Access Control**: Security filtering for remote MCP access (#378, Phase C Task 3)
  - Permission system in `src/kagura/mcp/permissions.py`
  - Local vs. remote context distinction
  - Dangerous tools (file ops, shell exec, local apps) blocked remotely
  - Safe tools (memory, web, API) allowed remotely
  - Automatic filtering in `create_mcp_server(context="remote")`
  - Fail-safe: unknown tools denied by default
  - Comprehensive test coverage (28 tests)

- **MCP Remote Connection CLI**: Commands for remote configuration (#378, Phase C Task 4)
  - `kagura mcp connect` - Configure remote API connection
  - `kagura mcp test-remote` - Test remote connectivity and authentication
  - `kagura mcp serve --remote` - Remote mode placeholder (future)
  - Config storage in `~/.kagura/remote-config.json`
  - Connection diagnostics with health checks
  - 7 new CLI tests

- **Memory Export/Import**: JSONL-based backup and migration (#378, Week 3)
  - `MemoryExporter` for exporting memories and graph data
  - `MemoryImporter` for importing from backup
  - JSONL format for human-readable exports
  - CLI commands: `kagura memory export`, `kagura memory import`
  - Support for working memory, persistent memory, and graph data
  - Metadata tracking (exported_at, user_id, stats)
  - 6 tests with roundtrip validation

- **Production Deployment**: Docker setup for self-hosting (#378, Week 4)
  - `docker-compose.prod.yml` for production deployment
  - Caddy reverse proxy with automatic HTTPS
  - PostgreSQL + Redis + Kagura API stack
  - Health checks and auto-restart
  - Deployment guide: `docs/self-hosting.md`
  - Environment configuration: `.env.example` updated
  - Integration test suite (9 tests)

### 🔄 Changed

- **GraphMemory Persistence: Pickle → JSON** (#433)
  - Replaced pickle.dump/load with NetworkX node_link_data/node_link_graph
  - File format: graph.pkl → graph.json (human-readable, git-friendly)
  - Added edges="links" parameter for NetworkX 3.6+ compatibility
  - **Security**: Eliminates arbitrary code execution risk from pickle
  - **Cloud-safe**: Multi-instance compatible file format
  - **Breaking Change**: Existing graph.pkl files require manual recreation

- **MCP Tool Token Optimization** (#432 Phase 1 & 2)
  - **memory_search**: Reduced default k from 5 to 3 (40% fewer results)
  - **memory_search**: Added mode parameter ("summary" | "full")
    - Summary mode: ~200 tokens (80% reduction)
    - Full mode: ~1000 tokens (backward compatible default)
  - **memory_list**: Reduced default limit from 50 to 10 (80% reduction)
  - **memory_store**: Compact output format (67% reduction)
    - Before: 4 lines, ~150 tokens
    - After: 1 line, ~50 tokens ("✓ Stored: key (persistent, global, RAG✓)")
  - **Overall token reduction**: ~60-70% across memory tools

- **GraphMemory**: Made `ai_platform` parameter optional in `record_interaction` (#381)
  - New signature: `record_interaction(user_id, query, response, metadata)`
  - `ai_platform` moved to metadata (optional)
  - MCP tool: `ai_platform` parameter now optional with default=""
  - REST API: `InteractionCreate.ai_platform` is now `str | None`
  - Backward compatible: `analyze_user_pattern` supports both old and new formats
  - Rationale: Aligns with v4.0 Universal Memory principle ("Own your memory, bring it to every AI")

### ⚠️ BREAKING CHANGES

- **Removed `web_search` MCP tool** (#393)
  - The legacy `web_search` tool has been removed from MCP tools
  - **Migration**: Use `brave_web_search` instead
  - `brave_web_search` provides better features:
    - Search result caching
    - Better parameter names (`count` instead of `max_results`)
    - More detailed documentation
  - Additional Brave Search tools available:
    - `brave_local_search` - Businesses/places
    - `brave_news_search` - News articles
    - `brave_image_search` - Images
    - `brave_video_search` - Videos
  - Updated: `src/kagura/mcp/permissions.py`, `docs/api-reference.md`, tests

---

## [4.0.0] - 2025-10-26

### 🎯 Universal Memory Foundation (Issue #382)

**Major Change**: Added `user_id` to all memory operations for true multi-user support.

**Rationale**: Phase C (Remote MCP Server) requires multi-user support. Memory must be scoped by user to enable remote deployment with proper data isolation.

### ⚠️ BREAKING CHANGES

#### MCP Tools API Changes

All memory MCP tools now require `user_id` as the **first parameter**:

**Before v4.0.0**:
```python
memory_store(agent_name="my_agent", key="lang", value="ja")
memory_recall(agent_name="my_agent", key="lang")
```

**After v4.0.0**:
```python
memory_store(user_id="user_jfk", agent_name="my_agent", key="lang", value="ja")
memory_recall(user_id="user_jfk", agent_name="my_agent", key="lang")
```

**Affected Tools** (#382):
- `memory_store(user_id, agent_name, ...)`
- `memory_recall(user_id, agent_name, ...)`
- `memory_search(user_id, agent_name, ...)`
- `memory_list(user_id, agent_name, ...)`
- `memory_feedback(user_id, agent_name, ...)`
- `memory_delete(user_id, agent_name, ...)`
- `memory_get_related(user_id, agent_name, ...)`

#### Python API Changes

`MemoryManager` now requires `user_id`:

**Before v4.0.0**:
```python
manager = MemoryManager(agent_name="test")
```

**After v4.0.0**:
```python
manager = MemoryManager(user_id="user_jfk", agent_name="test")
```

#### REST API Changes

**New**: `X-User-ID` header support

```bash
# With explicit user_id
curl -H "X-User-ID: user_jfk" -X POST .../api/v1/memory

# Without header (uses "default_user")
curl -X POST .../api/v1/memory
```

### ✨ Added

- **Universal Memory**: `user_id` parameter added to all memory operations (#382)
- **Database**: `user_id` column with auto-migration for existing data (#382)
- **REST API**: `X-User-ID` header support with `default_user` fallback (#382)
- **Multi-User**: Per-user MemoryManager instances with isolated storage (#382)
- **Documentation**: Migration guide for v4.0.0 (#382)

### 🔄 Changed

- **MemoryManager**: `user_id` is now required (first positional parameter) (#382)
- **PersistentMemory**: All methods accept `user_id` parameter (#382)
- **MemoryRAG**: User-scoped vector collections (#382)
- **Cache Key Format**: `{user_id}:{agent_name}:rag={bool}` (#382)

### 🗑️ Removed

- **Personal Tools**: Removed v3.0 legacy personal assistant tools (#373)
  - Deleted: `news.py`, `weather.py`, `recipes.py`, `events.py`, `personal_assistant.py`
  - Deleted: `examples/09_personal_tools/` directory
  - Deleted: `tests/agents/test_personal_tools.py` (39 tests)
  - Rationale: v4.0 is MCP-first. Personal tools don't align with Universal Memory Platform strategy

- **SDK Examples**: Removed v3.0 SDK integration examples (#374)
  - Deleted: `examples/08_sdk_integration/` directory (FastAPI, Streamlit, data pipeline, email automation)
  - Updated: `examples/README.md` - Removed section 08 and SDK references
  - Rationale: v4.0 focuses on MCP tools and REST API, not Python SDK integration patterns

### 🐛 Fixed

- **GraphMemory**: Fixed `memory_get_related` type conversion error when `depth` parameter is sent as string by MCP clients (#379)
- **GraphMemory**: Topic extraction now working - `record_interaction` creates topic nodes and edges from metadata (#379)

### ✨ Improved

- **MCP Tools**: Enhanced docstrings with 🔍 USE WHEN, 💡 EXAMPLE, and 📊 RETURNS sections for better LLM understanding (#379, #382)
- **GraphMemory**: `record_interaction` now automatically creates topic nodes when `"topic"` is in metadata (#379)
- **GraphMemory**: User→Topic edges created for pattern analysis (#379)

### 🧪 Tests

- Updated 100+ tests for `user_id` support (#382)
- Added `X-User-ID` header tests for REST API (#382)
- Added user isolation tests (multi-user memory separation) (#382)
- Added `test_get_related_with_string_depth` - MCP protocol compatibility test (#379)
- Added `test_record_interaction_with_topic` - Topic extraction validation (#379)

---

## [4.0.0a0] - 2025-10-26

### 🎯 Strategic Pivot

**From**: Python-First AI Agent SDK (v3.0)
**To**: Universal AI Memory & Context Platform (v4.0)

**Vision**: Make Kagura the de facto standard for AI Memory Management across all platforms via MCP.

**See**: [V4.0 Strategic Pivot](./ai_docs/V4.0_STRATEGIC_PIVOT.md)

### ✨ Added

#### REST API (Phase A)
- FastAPI-based REST API server (`src/kagura/api/`)
  - Memory CRUD endpoints (`POST/GET/PUT/DELETE /api/v1/memory`)
  - Search endpoint (`POST /api/v1/search`)
  - Semantic recall endpoint (`POST /api/v1/recall`)
  - Health check (`GET /api/v1/health`)
  - System metrics (`GET /api/v1/metrics`)
- Pydantic request/response models
- OpenAPI 3.1 specification (`docs/api/reference.yaml`)
- Dependency injection for MemoryManager
- ChromaDB metadata encoding/decoding for list/dict values

#### MCP Tools v1.0 (Phase A)
- `memory_feedback` - Provide quality feedback (Hebbian-like learning)
- `memory_delete` - Delete with audit logging (GDPR-compliant)
- Updated `memory_store` - Support for tags/importance/metadata (v4.0 format)
- Existing tools: `memory_recall`, `memory_search`, `memory_list` (28 tools total)

#### MCP Tool Management (Phase A, Issue #331)
- `kagura mcp tools` - List all MCP tools (28 tools, categorized)
- `kagura mcp doctor` - Comprehensive diagnostics
  - API Server health check
  - Memory Manager status
  - Claude Desktop configuration check
  - Storage usage monitoring
- `kagura mcp install` - Auto-configure Claude Desktop
- `kagura mcp uninstall` - Remove Claude Desktop configuration
- MCP config management (`src/kagura/mcp/config.py`)
- MCP diagnostics (`src/kagura/mcp/diagnostics.py`)

#### GraphMemory Integration (Phase B, Issue #345)
- **GraphMemory Core** (`src/kagura/core/graph/memory.py`)
  - NetworkX-based knowledge graph for relationships
  - Node types: memory, user, topic, interaction
  - Edge types: related_to, depends_on, learned_from, influences, works_on
  - Multi-hop graph traversal with relationship filtering
  - User pattern analysis methods:
    - `get_user_topics()` - Get topics associated with a user
    - `get_user_interactions()` - Get user interaction history
    - `analyze_user_pattern()` - Analyze patterns (topics, platforms, frequency)
  - Graph persistence (pickle format)
  - Auto-load on initialization

- **MCP Tools for Graph** (3 new tools)
  - `memory_get_related(node_id, depth, rel_type)` - Get related nodes via graph traversal
  - `memory_record_interaction(user_id, ai_platform, query, response, metadata)` - Record AI-User interactions
  - `memory_get_user_pattern(user_id)` - Analyze user interaction patterns

- **REST API for Graph** (3 new endpoints)
  - `POST /api/v1/graph/interactions` - Record AI-User interaction
  - `GET /api/v1/graph/{node_id}/related` - Get related nodes (supports depth, rel_type filtering)
  - `GET /api/v1/graph/users/{user_id}/pattern` - Analyze user patterns
  - Pydantic models for type-safe requests/responses
  - OpenAPI documentation support

- **MemoryManager Integration**
  - `enable_graph=True` by default (auto-enables GraphMemory)
  - Auto-detects NetworkX availability (graceful degradation)
  - Graph persistence path: `{persist_dir}/graph.pkl`
  - Integrated with existing 3-tier memory system

- **Dependencies**
  - Added `networkx>=3.0` to `ai` extras (~1.5MB)

#### Docker & Infrastructure
- Docker Compose setup (PostgreSQL + pgvector, Redis, API server)
- Dockerfile for API server
- `.dockerignore` for efficient builds
- Makefile targets (`build_docs`, `serve_docs`, etc.)

#### Documentation
- Getting Started guide (`docs/getting-started.md`)
- MCP Setup guide (`docs/mcp-setup.md`)
- API Reference (`docs/api-reference.md`)
- Architecture documentation (`docs/architecture.md`)
- Redocly API documentation workflow (`.github/workflows/api-docs.yml`)
- V4.0 strategy documents (5 files in `ai_docs/`)

### 🔧 Changed

- **README.md**: Updated to v4.0 positioning
  - "Universal AI Memory Platform" messaging
  - MCP-first approach
  - Roadmap updated (v4.0 → v4.2)
- **pyproject.toml**:
  - Version: 3.0.8 → 4.0.0a0
  - Description: Memory platform focus
  - Keywords: memory, mcp, context, knowledge-graph
  - Dependencies: Added FastAPI, uvicorn, psycopg2, redis, networkx
- **core/registry.py**: Export `tool_registry` from `tool_registry.py`

### 📝 Documentation

- `ai_docs/V4.0_STRATEGIC_PIVOT.md` - Strategic direction & multimodal plan
- `ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md` - Detailed 8-12 month roadmap
- `ai_docs/V4.0_COMPETITIVE_ANALYSIS.md` - Market analysis (vs Mem0, Rewind AI, etc.)
- `ai_docs/V4.0_README_DRAFT.md` - New README draft
- `ai_docs/V4.0_GITHUB_ISSUE_TEMPLATE.md` - Issue templates

### 🐛 Fixed

- ChromaDB metadata constraints for list/dict values
  - Automatic JSON encoding on store
  - Automatic JSON decoding on retrieve
  - Transparent to API users

- **web_search MCP tool** - JSON serialization error (Issue #345)
  - Fixed `SearchResult` dataclass serialization
  - Added `asdict()` conversion before JSON serialization
  - Added `ensure_ascii=False` for proper Japanese character support
  - Added comprehensive unit tests (5 tests) to prevent regression

### ⚠️ Breaking Changes

- **Memory Embeddings Migration (#418)**: Embedding model changed from all-MiniLM-L6-v2 to multilingual-e5-large
  - **Action Required**: Re-index all memories with new model
  - Command: `kagura memory reindex --model intfloat/multilingual-e5-large`
  - Impact: Existing semantic search results will change
  - Reason: Improved multilingual support (100+ languages including Japanese) and 1024-dim embeddings
  - **Database Schema**: Added `access_count` and `last_accessed_at` columns to memories table (auto-migrated)

Note: v4.0 is developed on separate branch (`364-featv40-phase-a-mcp-first-foundation`)

v3.0 remains stable on `main` branch.

### 🧪 Tests

**GraphMemory & MCP Tools** (Issue #345):
- GraphMemory unit tests: 40 tests (100% coverage)
  - Node/edge operations, graph queries, persistence
  - User pattern analysis, interaction recording
- MCP Tools integration tests: 27 tests
  - memory graph tools: 9 tests
  - web_search: 5 tests (dataclass serialization validation)
  - file_ops: 17 tests (file I/O, permissions, encoding)
  - routing: 5 tests (placeholder validation)
- **Total**: 76 tests added, all passing
- Type-safe (pyright strict), lint-clean (ruff)

### 🚧 In Progress

#### Phase B (Remaining for v4.0.0 stable)
- Memory consolidation (short → long-term)
- Export/Import (JSONL format)
- Multimodal database schema

#### Phase C (Coming in v4.1.0)
- Self-hosted API with authentication
- Multimodal MVP (attachments + derived texts)
- Connectors (GitHub, Calendar, Files)
- Consumer App (Flutter)
- Remote MCP Server support (Issue #368)

### 📊 Statistics

**Phase A + B Metrics**:
- **Files changed**: 45+ (Phase A: 30, Phase B: 15)
- **Lines added**: 7,331+ (Phase A: 5,000, Phase B: 2,331)
- **New modules**: 8 (Phase A: 7, Phase B: 1 graph module)
- **API endpoints**: 13 (Phase A: 10, Phase B: 3 graph endpoints)
- **MCP tools**: 31 (Phase A: 28, Phase B: +3 graph tools)
- **CLI commands**: 6 (4 new)
- **Documentation pages**: 7
- **Tests**: 76+ GraphMemory/MCP tests

**Git Stats**:
- **Commits**: 11 (Phase A: 6, Phase B: 5)
- **PRs**: #366 (Phase A, merged), #367 (Phase B, merged)
- **Issues**: #364 (Phase A), #345 (Phase B, closed), #368 (Remote MCP Server)

---

## [3.0.8] - 2025-10-23

### Fixed
- Memory telemetry type error (Issue #360, #361)

### Improved
- MCP tool descriptions for better LLM decision making

---

## Earlier Versions

See git history for v3.0.0 - v3.0.7 changes.

---

**For complete details, see**:
- [V4.0 Implementation Roadmap](./ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md)
- [GitHub Releases](https://github.com/JFK/kagura-ai/releases)
- [Pull Requests](https://github.com/JFK/kagura-ai/pulls)
