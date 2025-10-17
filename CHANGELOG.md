# Changelog

All notable changes to Kagura AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0] - 2025-10-17

### ⚠️ Breaking Changes

1. **Agent Storage Migration** (#261)
   - Custom agents now stored in `~/.kagura/agents/` (was `./agents/`)
   - No backward compatibility
   - Migration: `cp ./agents/*.py ~/.kagura/agents/`

2. **Default Model Changed** (#267)
   - Changed from `gpt-4o-mini` to `gpt-5-mini`
   - Better quality, 67% more expensive
   - Migration: Use `--model gpt-4o-mini` flag if needed

3. **Import Paths Changed** (#269)
   - `kagura.presets` → `kagura.agents`
   - Migration: `from kagura.agents import TranslatorPreset`

4. **API Key Variable** (#273)
   - `BRAVE_API_KEY` removed (use `BRAVE_SEARCH_API_KEY`)
   - No backward compatibility
   - Migration: `export BRAVE_SEARCH_API_KEY="..."`

### Added

- **Runtime Model Switching** (#268): `/model` command in chat
  - Switch models mid-conversation
  - Preserve conversation history
  - Usage: `/model gpt-5`, `/model claude-3.5-sonnet`

- **Unified Agents Package** (#269): All built-in agents in one place
  - 13 agents: Code execution + 12 presets
  - Consistent imports from `kagura.agents`

- **GPT-5 Series Support**: Latest OpenAI models
  - gpt-5, gpt-5-mini, gpt-5-nano
  - Better quality, better pricing than GPT-4

### Changed

- **Default Model**: gpt-4o-mini → gpt-5-mini
  - 2.8x more expensive but significantly better quality
  - GPT-5 generation capabilities
  - Better tool use and reasoning

- **Agent Organization**:
  - `src/kagura/presets/` consolidated into `src/kagura/agents/`
  - `code_agent.py` → `code_execution.py` (consistent naming)
  - `chat/preset.py` → `agents/translate_func.py`

- **Test Structure**:
  - `tests/presets/` → `tests/agents/test_presets.py`
  - Removed `tests/agents_legacy/`, `tests/cli_legacy/`, `tests/core_legacy/`, `tests/integration_legacy/`

### Removed

- `src/kagura/presets/` directory
- `src/kagura_legacy/` directory
- `src/kagura/chat/preset.py`
- `agents/README.md` (project root)
- `BRAVE_API_KEY` backward compatibility
- Empty `Show` file

### Migration Guide

#### 1. Update Agent Storage Location
```bash
# If you have custom agents in ./agents/
mkdir -p ~/.kagura/agents
cp ./agents/*.py ~/.kagura/agents/
rm -rf ./agents  # Optional
```

#### 2. Update Import Paths
```python
# Before
from kagura.presets import TranslatorPreset
from kagura.chat.preset import TranslateAgent

# After
from kagura.agents import TranslatorPreset, TranslateAgent
```

#### 3. Update Environment Variables
```bash
# Before
export BRAVE_API_KEY="BSA..."

# After
export BRAVE_SEARCH_API_KEY="BSA..."
```

#### 4. Adjust for Cost Increase (Optional)
```bash
# If gpt-5-mini is too expensive, use gpt-4o-mini
kagura chat --model gpt-4o-mini

# Or use /model command to switch during chat
[You] > /model gpt-4o-mini
```

### Testing

- ✅ 1,300+ tests passing
- ✅ Pyright: 0 errors
- ✅ Ruff: all checks passed
- ✅ 5 new test files updated

### References

- Agent Storage: PR [#266](https://github.com/JFK/kagura-ai/pull/266), Issue [#261](https://github.com/JFK/kagura-ai/issues/261)
- Presets Consolidation: PR [#270](https://github.com/JFK/kagura-ai/pull/270), Issue [#269](https://github.com/JFK/kagura-ai/issues/269)
- Default Model: PR [#271](https://github.com/JFK/kagura-ai/pull/271), Issue [#267](https://github.com/JFK/kagura-ai/issues/267)
- Model Switching: PR [#272](https://github.com/JFK/kagura-ai/pull/272), Issue [#268](https://github.com/JFK/kagura-ai/issues/268)
- Cleanup: PR [#274](https://github.com/JFK/kagura-ai/pull/274), Issue [#273](https://github.com/JFK/kagura-ai/issues/273)

---

## [2.5.10] - 2025-10-16

### Added
- **Auto-Approve Mode**: Shell commands now execute without manual confirmation (safer, faster)
- **Smart Error Recovery**: Auto-suggests fixes for failed commands with user confirmation dialog

### Fixed
- **Lint Errors**: Fixed line length violations in TUI tools (Issue #252)
- **Duplicate Prevention**: Prevents LLM from repeating failed shell commands (#242)
- **Shell Output**: Display shell output immediately without LLM processing
- **Debug Logging**: Removed debug logs, keeping only duplicate prevention logic

### Performance
- Faster shell command execution with auto-approve mode
- Reduced latency by displaying output immediately

**References**: Issue [#252](https://github.com/JFK/kagura-ai/issues/252), Issue [#242](https://github.com/JFK/kagura-ai/issues/242)

---

## [2.5.9] - 2025-10-16

### Changed
- **Classic UI Default**: Split UI moved to experimental status
- UI improvements and stability enhancements

---

## [2.5.8] - 2025-10-16

### Added
- **2-Column Chat UI**: New split-panel interface
- **Auto-Correction**: Smart command fixing on errors

---

## [2.5.7] - 2025-10-16

### Added
- **Interactive Shell**: Enhanced shell command execution
- **Auto-Correction**: LLM-powered command fixes

---

## [2.5.6] - 2025-10-16

### Added
- **Claude Code-like Chat Experience** (RFC-033 Phase 0): Powerful interactive chat with 8 built-in tools
  - File operations: read/write/search with multimodal support (text, image, PDF, audio, video)
  - Code execution: Safe Python sandbox
  - Web integration: web_search, url_fetch
  - YouTube: transcript extraction, metadata retrieval
  - Natural language interface (removed preset commands)

- **Smart Model Selection** (RFC-034 Phase 1): Task-based model optimization for cost reduction
  - ModelSelector class with 8 task types
  - Prepares for 80% cost savings on search tasks (when GPT-5 available)
  - Configurable model mappings per task type

- **Monitor Enhancements**: Better observability
  - Model name column in execution table
  - Partial ID matching for `kagura monitor trace`
  - Improved UX for telemetry inspection

### Fixed
- **YouTube Transcript**: Better error handling for videos without subtitles
  - Updated to youtube-transcript-api v0.6+ (new API)
  - Helpful error messages with fallback suggestions
  - Specific exception handling (NoTranscriptFound, TranscriptsDisabled)

### Changed
- **CLI Simplification**: `kagura chat` flags reduced (6 → 1)
  - Removed: `--enable-web`, `--enable-multimodal`, `--dir`, `--full`, `--no-routing`
  - All features enabled by default

- **Chat Commands**: Removed preset commands in favor of natural language
  - Removed: `/translate`, `/summarize`, `/review`
  - Use natural language instead (e.g., "Translate this to Japanese")

### Testing
- **New Tests**: 43+ tests added (all passing)
  - 13 ModelSelector tests
  - 13 chat session tool tests
  - 6 YouTube tests
  - 1 video processing test
- **Total Tests**: 1,235+ passing
- **Code Quality**: 0 pyright errors, all ruff checks passed

### Performance
- Multimodal file processing via Gemini
- Video audio extraction with ffmpeg
- Async tool execution

**References**:
- Chat Enhancement: PR [#223](https://github.com/JFK/kagura-ai/pull/223), Issue [#222](https://github.com/JFK/kagura-ai/issues/222), [RFC-033](./ai_docs/rfcs/RFC_033_CHAT_ENHANCEMENT.md)
- YouTube Fix: PR [#231](https://github.com/JFK/kagura-ai/pull/231), Issue [#225](https://github.com/JFK/kagura-ai/issues/225)
- Monitor: PR [#233](https://github.com/JFK/kagura-ai/pull/233), Issue [#226](https://github.com/JFK/kagura-ai/issues/226)
- Model Selection: PR [#235](https://github.com/JFK/kagura-ai/pull/235), Issue [#224](https://github.com/JFK/kagura-ai/issues/224), [RFC-034](./ai_docs/rfcs/RFC_034_SMART_MODEL_SELECTION.md)

---

## [2.5.5] - 2025-10-15

### Added
- **Automatic Telemetry**: @agent decorator now records execution data automatically - RFC-030 Phase 1
  - LLMResponse: Response with usage, model, duration metadata
  - Cost calculation: Accurate pricing for 20+ models
  - TelemetryCollector integration: Automatic recording to EventStore
  - No user code changes required

### Features
- LLM call tracking (tokens, cost, duration)
- Automatic cost calculation per execution
- EventStore integration (SQLite backend)
- `kagura monitor` now shows real data

### Changes
- `call_llm()` returns `LLMResponse` (backward compatible via `__str__` and `__eq__`)
- `@agent` has `enable_telemetry` parameter (default: True)
- Automatic telemetry for all agent executions

### Testing
- 6 new telemetry tests (all passing)
- 1,187 non-integration tests passing
- Pyright: 0 errors
- Ruff: All checks passed

### CI Improvements
- Excluded `tests/integration/` explicitly to avoid unmarked integration tests

**References**: PR [#210](https://github.com/JFK/kagura-ai/pull/210), Issue [#205](https://github.com/JFK/kagura-ai/issues/205), [RFC-030](./ai_docs/rfcs/RFC_030_TELEMETRY_INTEGRATION.md)

---

## [2.5.4] - 2025-10-15

### Added
- **Unified MCP Server**: All Kagura features via single Claude Desktop config - RFC-032
  - MCP server now exposes @tool and @workflow (not just @agent)
  - 15 built-in MCP tools auto-registered on serve

**Built-in MCP Tools** (15 tools):
- Memory: `memory_store`, `memory_recall`, `memory_search`
- Web: `web_search`, `web_scrape`
- File/Shell: `file_read`, `file_write`, `dir_list`, `shell_exec`
- Routing: `route_query`
- Observability: `telemetry_stats`, `telemetry_cost`
- Meta: `meta_create_agent`
- Multimodal: `multimodal_index`, `multimodal_search`

### Changed
- `src/kagura/mcp/server.py`: Extended to support tool_registry and workflow_registry
- `src/kagura/cli/mcp.py`: Auto-import builtin tools on `kagura mcp serve`

### Documentation
- `docs/en/guides/claude-code-mcp-setup.md`: Claude Code integration guide

### Testing
- 5 new MCP integration tests (all passing)
- Total tools registered: 15+ built-in tools

**References**: PR [#209](https://github.com/JFK/kagura-ai/pull/209), Issue [#207](https://github.com/JFK/kagura-ai/issues/207), [RFC-032](./ai_docs/rfcs/RFC_032_MCP_FULL_FEATURE_INTEGRATION.md)

---

## [2.5.3] - 2025-10-15

### Performance
- **CLI Startup**: 98.7% faster (8.8s → 0.1s) - RFC-031
  - Implemented LazyGroup for on-demand command loading
  - Added module-level lazy imports via `__getattr__` (PEP 562)
  - Smart help formatting without loading heavy modules
  - No MCP/Observability imports on `--help`

### Added
- `src/kagura/cli/lazy.py`: LazyGroup implementation (157 lines)
- `docs/en/guides/cli-performance.md`: Performance optimization guide
- 14 new tests for lazy loading behavior
- TYPE_CHECKING imports for better type hints

### Changed
- Refactored `src/kagura/cli/main.py`: LazyGroup with lazy_subcommands
- Updated `src/kagura/__init__.py`: Lazy imports for CLI performance
- Removed version numbers from README.md and docs/index.md
- Updated "Recent Updates" section in README.md

### Testing
- **New Tests**: +14 lazy loading tests (all passing)
- **Existing Tests**: 1,226/1,242 passing (99.2%)
- **Type Checking**: 0 errors (TYPE_CHECKING block resolves all issues)
- **Linting**: All ruff checks passed

### Benchmark Results

| Command | Before | After | Improvement |
|---------|--------|-------|-------------|
| `kagura --help` | 8.8s | 0.11s | 98.7% |
| `kagura version` | 8.8s | 0.11s | 98.7% |
| `kagura chat` | 8.8s+ | 0.5s | 94.3% |

**References**: PR [#208](https://github.com/JFK/kagura-ai/pull/208), Issue [#206](https://github.com/JFK/kagura-ai/issues/206), [RFC-031](./ai_docs/rfcs/RFC_031_CLI_STARTUP_OPTIMIZATION.md)

---

## [2.5.2] - 2025-10-15

### Changed
- **Code Quality**: Migrated to Pydantic v2 ConfigDict pattern (RFC-028)
  - Replaced deprecated `class Config` with `model_config = ConfigDict()`
  - Migrated 3 files with 5 Pydantic model classes
  - Resolved 12 deprecation warnings
  - Pydantic v3 compatibility preparation

### Files Modified
- `src/kagura/meta/spec.py` - AgentSpec model
- `src/kagura/builder/config.py` - 4 builder config models
- `src/kagura/auth/config.py` - AuthConfig model

### Testing
- **Warnings**: 12 Pydantic warnings → 0
- **Tests**: 1,213 passed, 15 skipped (100% pass rate)
- **Type Checking**: 0 errors, 0 warnings
- **Compatibility**: 100% backward compatible, no breaking changes

### Documentation
- RFC-028: Pydantic v2 Config Migration

**References**: PR [#203](https://github.com/JFK/kagura-ai/pull/203), Issue [#202](https://github.com/JFK/kagura-ai/issues/202), [RFC-028](./ai_docs/rfcs/RFC_028_PYDANTIC_V2_MIGRATION.md)

---

## [2.5.1] - 2025-10-15

### Fixed
- **Shell Executor Security Policy** (Critical): Fixed over-restrictive command blocking
  - Changed from simple substring matching to precise command-name matching
  - Command names checked exactly, dangerous patterns checked as substrings  
  - Fixes 4 test failures with paths containing blocked command names
  - **Security**: No weakening - more precise detection, same security level

- **AgentSpec Type Validation** (Medium): Fixed strict type validation for examples
  - Changed `examples` field from `dict[str, str]` to `dict[str, Any]`
  - Accepts numeric and complex types in LLM-generated examples
  - Fixes 1 test failure in meta agent tests

- **TypeVar Usage** (Low): Resolved pyright warning
  - Updated parser signature to use `type[T]` parameter
  - Achieves 0 errors, 0 warnings in strict type checking

### Changed
- **Dependencies**: Upgraded pyright v1.1.390 → v1.1.406
- **Dependencies**: Upgraded typing-extensions 4.12.2 → 4.15.0

### Testing
- **Coverage**: 98.4% → 100% pass rate (1,213/1,213 tests passing)
- **New Tests**: +7 security policy tests for shell executor
- **Quality**: 0 pyright warnings, all ruff checks pass

### Documentation
- RFC-027: Bug Fixes - Shell Executor & Parser Type Safety
- RFC-027 Implementation Plan with detailed rollout strategy

**References**: PR [#201](https://github.com/JFK/kagura-ai/pull/201), Issue [#200](https://github.com/JFK/kagura-ai/issues/200), [RFC-027](./ai_docs/rfcs/RFC_027_BUGFIX_SHELL_AND_PARSER.md)

---

## [2.5.0] - 2025-10-14

### Added
- **Context Compression** (RFC-024 Phase 1): Token management
- **Broadlistening Analysis Example**: Real-world data analysis

### Fixed
- **Performance**: Optimized parallel test execution (60-80% faster)
- **Testing**: 95% mock coverage for external APIs

See git history for changes prior to v2.5.0.
