# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-10-09

### Added

- **MCP Integration** ([#75](https://github.com/JFK/kagura-ai/issues/75))
  - Model Context Protocol (MCP) server implementation
  - Direct integration with Claude Desktop
  - `kagura mcp start` command to launch MCP server
  - `kagura mcp config` command for Claude Desktop setup
  - Agent Registry system for dynamic agent discovery
  - JSON Schema generation for tool parameters
  - Full documentation: MCP Integration tutorial and API reference
  - PRs: [#89](https://github.com/JFK/kagura-ai/pull/89), [#90](https://github.com/JFK/kagura-ai/pull/90), [#91](https://github.com/JFK/kagura-ai/pull/91)

- **Shell Integration** ([#76](https://github.com/JFK/kagura-ai/issues/76))
  - Secure shell command execution with AST validation
  - Built-in Git automation agents (`commit`, `push`, `status`, `create_pr`)
  - Built-in file operation agents (`search_files`, `grep_files`)
  - `shell()` function for secure command execution
  - Security constraints: allowed commands whitelist, timeout protection
  - Full documentation: Shell Integration tutorial and API reference
  - PR: [#92](https://github.com/JFK/kagura-ai/pull/92)

- **Memory Management System** ([#84](https://github.com/JFK/kagura-ai/issues/84))
  - Three-tier memory architecture:
    - **Working Memory**: Temporary scratchpad (in-memory)
    - **Context Memory**: Session history (SQLite)
    - **Persistent Memory**: Long-term storage (JSON files)
  - `@agent(enable_memory=True)` decorator parameter
  - `MemoryManager` for centralized memory operations
  - Automatic memory persistence and retrieval
  - Full documentation: Memory Management tutorial and API reference
  - PR: [#94](https://github.com/JFK/kagura-ai/pull/94)

- **Custom Commands & Hooks System** ([#73](https://github.com/JFK/kagura-ai/issues/73))
  - Markdown-based command definitions with YAML frontmatter
  - Jinja2 template rendering for dynamic prompts
  - Inline shell command execution (`!`command``)
  - `kagura run <command>` CLI for executing custom commands
  - Parameter validation and type checking
  - **Hooks System**:
    - PreToolUse hooks for command interception
    - PostToolUse hooks for logging and monitoring
    - Validation hooks for parameter checking
    - Decorator API: `@hook.pre_tool_use()`, `@hook.post_tool_use()`, `@hook.validation()`
  - `CommandLoader` for loading commands from `~/.kagura/commands/`
  - Full documentation: Commands & Hooks guides and API references
  - PRs: [#95](https://github.com/JFK/kagura-ai/pull/95), [#96](https://github.com/JFK/kagura-ai/pull/96), [#97](https://github.com/JFK/kagura-ai/pull/97)

### Changed

- Updated README.md with new features section
- Enhanced documentation structure with MCP, Shell, Memory, and Commands tutorials
- Improved CLI with new commands: `mcp`, `run`

### Documentation

- Added `docs/en/tutorials/06-mcp-integration.md` (400 lines)
- Added `docs/en/tutorials/07-shell-integration.md` (216 lines)
- Added `docs/en/tutorials/08-memory-management.md` (429 lines)
- Added `docs/en/api/mcp.md` (350 lines)
- Added `docs/en/api/shell.md` (289 lines)
- Added `docs/en/api/memory.md` (479 lines)
- Added `docs/en/api/commands.md` (421 lines)
- Added `docs/en/api/hooks.md` (559 lines)
- Added `docs/en/guides/commands-quickstart.md` (418 lines)
- Added `docs/en/guides/hooks-guide.md` (566 lines)

### Tests

- Added 21 MCP tests (100% coverage)
- Added 26 Shell Integration tests (100% coverage)
- Added 66 Memory Management tests (100% coverage)
- Added 72 Commands & Hooks tests (100% coverage)
- **Total**: 340+ tests passing

## [2.0.2] - 2025-10-04

### Fixed

- **REPL Command Completion**
  - Fixed command completion double slash issue (`/` + Tab → `/help` not `//help`)
  - Implemented custom `CommandCompleter` to handle `/commands` correctly

- **REPL Python Code Completion**
  - Fixed prefix matching to complete `pr` → `print` instead of `__repr__`
  - Prioritized common functions (`print`, `len`, `range`, etc.) in completion list
  - Excluded private names starting with underscore from completion candidates
  - Properly handle `__builtins__` dict vs module format

- **REPL Key Bindings**
  - Removed Alt+Enter key binding (user feedback)
  - Simplified to IPython-style: Enter = newline, empty line + Enter = execute
  - Updated welcome message to reflect correct keyboard shortcuts

### Changed

- Tab completion now shows `print` as first candidate when typing `p`
- Completion order: common functions → keywords → other built-ins

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

[2.1.0]: https://github.com/JFK/kagura-ai/compare/v2.0.2...v2.1.0
[2.0.2]: https://github.com/JFK/kagura-ai/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/JFK/kagura-ai/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/JFK/kagura-ai/compare/v2.0.0-beta.1...v2.0.0
[2.0.0-beta.1]: https://github.com/JFK/kagura-ai/compare/v2.0.0-alpha.1...v2.0.0-beta.1
[2.0.0-alpha.1]: https://github.com/JFK/kagura-ai/releases/tag/v2.0.0-alpha.1
