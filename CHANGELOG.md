# Changelog

All notable changes to Kagura AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
