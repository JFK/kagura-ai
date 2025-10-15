# Changelog

All notable changes to Kagura AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
