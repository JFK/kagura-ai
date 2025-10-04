# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-10-04

### Added

- **REPL Tab Completion**
  - Tab completion for REPL commands (`/e` + Tab → `/exit`)
  - Tab completion for Python keywords (`def`, `class`, `import`, etc.)
  - Tab completion for built-in functions (`print`, `len`, `range`, etc.)
  - Completion list with cursor navigation (↑↓ keys)
  - Complete-while-typing with real-time suggestions
  - Support for all commands: `/help`, `/agents`, `/model`, `/temp`, `/exit`, `/clear`

- **Smart Enter Key Handling**
  - **Enter**: Auto-detect incomplete code and add newline, or execute if complete
  - **Alt+Enter**: Always insert newline for explicit multiline input
  - Automatic detection of incomplete code (ending with `:`, unclosed brackets, etc.)
  - Commands starting with `/` execute immediately

### Changed

- Enhanced REPL user experience with prompt_toolkit features
- Multiline input now natively supported by PromptSession
- Welcome message updated with keyboard shortcuts guide
- Fixed version.py to correctly display 2.0.1

## [2.0.0] - 2025-10-04

### Added

- **REPL Enhancements** ([#72](https://github.com/JFK/kagura-ai/issues/72))
  - Protected prompt (`>>>` cannot be deleted with backspace)
  - Multiline input with automatic detection
    - Detects incomplete code (ending with `:`)
    - Detects unclosed brackets/parentheses
    - Smart syntax checking with `compile()`
  - Syntax highlighting with Pygments
  - History file moved to `~/.kagura/repl_history`
  - Auto-suggestion from history (Ctrl+R search)
  - Integrated prompt_toolkit (>=3.0.52) and pygments (>=2.19.2)

- **RFC-015: Agent API Server** (Planned for v2.6.0)
  - Specification for FastAPI-based HTTP API server
  - REST API + WebSocket streaming design
  - JWT/API Key authentication
  - Integration with RFC-005 (Meta Agent) and RFC-008 (Marketplace)

### Changed

- **Documentation Updates**
  - Created `ai_docs/rfcs/` directory for all RFC specifications
  - Updated `UNIFIED_ROADMAP.md` with v2.6.0, v2.7.0, v2.8.0+ milestones
  - Updated `glossary.md` with RFC-015 and new version roadmap
  - Added RFC-015 to `ai_docs/README.md` RFC table

### Fixed

- Prompt editing issue in REPL (backspace no longer deletes `>>>`)
- Multiline paste support in REPL
- History search functionality

## [2.0.0-beta.1] - 2025-10-03

### Added

- **REPL Improvements** ([#56](https://github.com/JFK/kagura-ai/issues/56), [#57](https://github.com/JFK/kagura-ai/pull/57))
  - `.env` file auto-loading with python-dotenv
  - readline history support (`~/.kagura_history`)
  - Persistent command history across REPL sessions (up to 1000 commands)
  - Created `.env.example` template file

### Changed

- **Documentation** ([#54](https://github.com/JFK/kagura-ai/pull/54))
  - Fixed broken links in README.md and documentation
  - Updated relative paths to absolute GitHub URLs
  - Enhanced REPL tutorial with environment setup guide

### Fixed

- Fixed migration guide link (removed as file was deleted)
- Fixed relative paths in docs/index.md and docs/en/quickstart.md

### Internal

- **Test Coverage Analysis** ([#55](https://github.com/JFK/kagura-ai/issues/55))
  - Analyzed test coverage: 93% (506 lines, 36 missing)
  - Documented coverage analysis in `ai_docs/analysis/55-coverage-analysis.md`
  - Determined 93% coverage is sufficient for beta release

- **AI Docs Cleanup**
  - Removed duplicate documentation files (HOW_TO_START.md, SETUP_GUIDE.md, issues/)
  - Created NEXT_STEPS.md with development roadmap
  - Simplified ai_docs/README.md for Issue-Driven AI Development

## [2.0.0-alpha.1] - 2025-09-30

### Added

- **Core Framework**
  - `@agent` decorator for converting functions to AI agents
  - Jinja2 template engine for dynamic prompts
  - Type-based response parsing (str, int, list, dict, Pydantic models)
  - LiteLLM integration for multi-LLM support

- **Code Execution**
  - Safe code executor with AST validation
  - `execute_code` agent for code generation and execution
  - Security constraints (import restrictions, timeout protection)

- **CLI & REPL**
  - Interactive REPL with command support
  - `/help`, `/agents`, `/model`, `/temp`, `/exit`, `/clear` commands
  - Async/await support in REPL
  - Multi-line input support

- **Documentation**
  - MkDocs documentation site
  - Quick Start guide
  - API Reference
  - Tutorials (01-04)
  - Code examples

- **Testing**
  - Comprehensive test suite (93% coverage)
  - Unit tests for core modules
  - Integration tests for workflows
  - CLI integration tests

- **CI/CD**
  - GitHub Actions workflows for testing
  - Automatic test runs on push/PR
  - pyright type checking
  - pytest with coverage reporting

### Breaking Changes

This is a **complete rewrite** from Kagura AI 1.x:

- **No YAML Configuration**: Agents are now defined purely in Python
- **No Legacy API**: All 1.x APIs are removed
- **Python 3.11+ Required**: Minimum Python version increased
- **New Decorator-Based API**: Use `@agent` instead of YAML config files

**Migration from 1.x is not supported.** This is a new framework with a different philosophy.

## [1.x] - Legacy

Legacy versions (1.0.0 - 1.x.x) are no longer maintained. Please migrate to 2.0.0+ for new projects.

[2.0.1]: https://github.com/JFK/kagura-ai/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/JFK/kagura-ai/compare/v2.0.0-beta.1...v2.0.0
[2.0.0-beta.1]: https://github.com/JFK/kagura-ai/compare/v2.0.0-alpha.1...v2.0.0-beta.1
[2.0.0-alpha.1]: https://github.com/JFK/kagura-ai/releases/tag/v2.0.0-alpha.1
