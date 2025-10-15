# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **RFC-025: Broadlistening Analysis Example** ([#198](https://github.com/JFK/kagura-ai/issues/198), PR [#199](https://github.com/JFK/kagura-ai/pull/199))
  - Real-world example demonstrating production data analysis pipeline
  - **Features**:
    - Opinion extraction from public comments using LLM
    - Hierarchical clustering (UMAP + KMeans)
    - AI-powered cluster labeling
    - **Property-based filtering** (gender, region, age_group, custom attributes)
    - Interactive visualization with Plotly

  - **Files Added**:
    - `examples/pyproject.toml` - Isolated example dependencies
    - `examples/08_real_world/broadlistening_analysis/`:
      - `pipeline.py` (350 lines) - Main workflow combining Kagura + scikit-learn
      - `clustering.py` (200 lines) - UMAP + KMeans utilities
      - `filtering.py` (250 lines) - PropertyFilter class for demographic filtering
      - `visualization.py` (150 lines) - Interactive Plotly visualizations
      - `sample_data.csv` - 30 sample comments with properties
      - `test_pipeline.py` - 11 test cases (100% passing)
      - `README.md` - Comprehensive usage guide

  - **PropertyFilter API**:
    ```python
    # Filter by single property
    filtered = result['filter'].filter(gender="女性")

    # Filter by multiple values (OR)
    filtered = result['filter'].filter(region=["東京都", "大阪府"])

    # Filter by multiple properties (AND)
    filtered = result['filter'].filter(gender="女性", region="東京都")

    # Get property distribution
    dist = filter.get_property_distribution("gender")
    ```

  - **Installation**:
    ```bash
    cd examples && pip install -e ".[broadlistening]"
    python 08_real_world/broadlistening_analysis/pipeline.py sample_data.csv
    ```

  - **Inspired by**: Talk to the City (AI Objectives Institute)
  - **Learning Objectives**: Workflow design, LLM + traditional ML integration, property-based analysis

### Fixed

- **Type Safety in Examples**
  - Fixed `cluster_labeler` return type from `dict[str, str]` to `ClusterLabel` Pydantic model
  - Resolved parsing error: "Unsupported type for parsing: dict[str, str]"
  - All example tests passing (11/11)

### Tests

- Added 11 property filtering tests (100% passing)
- Pipeline tested end-to-end with sample data
- All clusters labeled correctly by AI

## [2.5.0] - 2025-10-14

### Added

- **RFC-024: Context Compression - Phase 1** ([#159](https://github.com/JFK/kagura-ai/issues/159), PR [#193](https://github.com/JFK/kagura-ai/pull/193))
  - Token counting and context monitoring system
  - **New modules**:
    - `TokenCounter` - Multi-model token counting (OpenAI, Claude, Gemini)
    - `ContextMonitor` - Usage tracking and compression triggers
    - `UsageReport` - Detailed token usage analysis
  - **Features**:
    - Accurate token counting for all major LLM providers
    - Context window limit detection (`should_compress` flag)
    - Cost estimation per message
    - Compression recommendations
  - **Tests**: 30 comprehensive tests (100% coverage)

### Changed

- **Dependency Consolidation** ([#173](https://github.com/JFK/kagura-ai/issues/173), PR [#191](https://github.com/JFK/kagura-ai/pull/191))
  - Merged `memory`, `routing` extras into single `ai` extra
  - Merged `multimodal` extra into `web` extra
  - Removed `testing` extra (integrated into `dev`)
  - Renamed `oauth` → `auth` for clarity
  - **New extras structure**:
    - `ai` = Memory + Routing + Context Compression
    - `web` = Multimodal + Web scraping + Search
    - `auth` = OAuth2 authentication
    - `mcp` = Model Context Protocol
    - `full` = All user-facing (ai + web + auth + mcp)
    - `all` = Everything (full + dev + docs)
  - **Migration**: `pip install kagura-ai[memory,routing]` → `pip install kagura-ai[ai]`

### Documentation

- Updated all documentation for v2.5.0 compatibility
- Updated installation guide with new extras structure
- Added Context Compression API reference
- Updated examples README.md with v2.5.0 features

### Tests

- Added 30 context compression tests
- Updated CI to use `--all-extras` for comprehensive testing
- Total project tests: 650+ (all passing)

## [2.4.0] - 2025-10-13

### Added

- **RFC-013: OAuth2 Authentication** ([#74](https://github.com/JFK/kagura-ai/issues/74), PR [#154](https://github.com/JFK/kagura-ai/pull/154))

  **Phase 1: Core OAuth2 Implementation** (2025-10-11)
  - **OAuth2Manager** - Google OAuth2 authentication flow
    - Browser-based login flow with `InstalledAppFlow`
    - Fernet encryption (AES-128) for credential storage
    - Automatic token refresh with Google auth library
    - Secure file permissions (0o600) for credentials and encryption keys
    - `~/.kagura/credentials.json.enc` encrypted storage
    - `~/.kagura/encryption.key` encryption key storage

  - **AuthConfig** - Authentication configuration management
    - Provider-specific scope management
    - Google Generative Language API scopes
    - Extensible for future OAuth2 providers

  - **Custom Exceptions** - Error handling
    - `NotAuthenticatedError` - User not logged in
    - `InvalidCredentialsError` - Corrupted or invalid credentials

  - **CLI Commands** - `kagura auth` command group
    - `kagura auth login --provider google` - Browser login
    - `kagura auth status` - Check authentication status
    - `kagura auth logout` - Remove credentials

  **Phase 2: Integration & Documentation** (2025-10-13)
  - **LLMConfig OAuth2 Integration**
    - `auth_type` parameter: `"api_key"` (default) or `"oauth2"`
    - `oauth_provider` parameter: OAuth2 provider name (e.g., `"google"`)
    - `get_api_key()` method returns OAuth2 token when `auth_type="oauth2"`
    - Seamless LiteLLM integration (OAuth2 token used as API key)
    - Backward compatible with existing API key authentication

  - **User Documentation** (1772 lines total)
    - `docs/en/guides/oauth2-authentication.md` - Setup guide (466 lines)
      - Comparison: OAuth2 vs API Key (when to use each)
      - Google Cloud Console setup instructions
      - Authentication workflow
      - LLMConfig integration examples
      - Troubleshooting guide
      - **Prominent notice**: API Key recommended for most users, OAuth2 for advanced use cases

    - `docs/en/api/auth.md` - API reference (400 lines)
      - `OAuth2Manager` class documentation
      - `AuthConfig` class documentation
      - `NotAuthenticatedError` and `InvalidCredentialsError` documentation
      - LLMConfig OAuth2 integration documentation
      - Code examples and best practices

    - `docs/en/installation.md` - OAuth2 section added
      - Quick start tip emphasizing API Key simplicity
      - Optional OAuth2 dependencies: `pip install kagura-ai[oauth]`
      - Clear guidance on when OAuth2 is needed

    - `mkdocs.yml` - Navigation updated with OAuth2 documentation

  - **Integration Tests**
    - `scripts/test_oauth2.py` - Manual testing script (464 lines)
      - Interactive test suite for OAuth2 functionality
      - Tests: login, status, token, refresh, logout, LLM call, CLI
      - Available flags: `--all`, `--login`, `--status`, `--token`, `--refresh`, `--logout`, `--llm`, `--cli`

    - `tests/integration/test_oauth2_integration.py` - Integration tests (15 tests)
      - Real OAuth2 flow testing (skipped when credentials not available)
      - `@pytest.mark.integration` marker for optional testing
      - Tests: authentication status, token retrieval, encryption, file permissions, LLM calls

    - `ai_docs/OAUTH2_TESTING_GUIDE.md` - Testing guide (442 lines)
      - Comprehensive testing documentation
      - Google Cloud Console setup (step-by-step with screenshots)
      - Manual testing scenarios
      - Integration test execution guide
      - Troubleshooting common issues

### Changed

- **LLMConfig Authentication Enhancement**
  - Added `auth_type` field: `Literal["api_key", "oauth2"]` (default: `"api_key"`)
  - Added `oauth_provider` field: `Optional[str]` for OAuth2 provider name
  - `get_api_key()` method now returns OAuth2 token when `auth_type="oauth2"`
  - Maintains backward compatibility with existing API key authentication
  - Lazy import of `OAuth2Manager` to avoid hard dependency

- **call_llm() OAuth2 Integration**
  - Automatically retrieves OAuth2 token via `config.get_api_key()` when configured
  - Passes token as `api_key` parameter to `litellm.acompletion`
  - No changes required for existing API key users

### Documentation

- **OAuth2 Documentation Package** (1772 lines)
  - User-facing documentation with clear use case guidance
  - API reference with complete OAuth2Manager documentation
  - Testing guide with Google Cloud Console setup
  - Installation guide updated with OAuth2 section
  - **Key message**: API Key recommended for most users, OAuth2 for advanced use cases

### Tests

- **Unit Tests** (54 tests in `tests/auth/`)
  - `test_oauth2_manager.py` - OAuth2Manager tests (29 tests)
  - `test_auth_config.py` - AuthConfig tests (9 tests)
  - `test_exceptions.py` - Exception tests (4 tests)
  - `test_auth_cli.py` - CLI command tests (12 tests)
  - **Coverage**: 100% for auth module

- **LLMConfig Integration Tests** (11 tests in `tests/core/test_llm_oauth2.py`)
  - OAuth2 authentication with LLMConfig
  - OAuth2 token usage in `call_llm()`
  - Error handling (NotAuthenticatedError, missing provider)
  - Mock-based testing (no real OAuth2 flow required)

- **Integration Tests** (15 tests in `tests/integration/test_oauth2_integration.py`)
  - Real OAuth2 flow testing (optional, skipped without credentials)
  - Authentication status, token retrieval, encryption, file permissions
  - LLM calls with OAuth2 token
  - `@pytest.mark.integration` marker

- **Total v2.4.0 Tests**: 65+ tests (54 unit + 11 LLM integration + 15 integration)

### Security

- **Credential Encryption**
  - Fernet encryption (AES-128) for OAuth2 credentials
  - Symmetric key stored separately in `~/.kagura/encryption.key`
  - File permissions: 0o600 (owner read/write only) for both credentials and key
  - Protection against unauthorized access

- **Token Management**
  - Automatic token refresh using Google auth library
  - Timezone-naive UTC datetime handling for expiry
  - No tokens logged or exposed in error messages

### Technical Details

- **Dependencies Added** (optional `[oauth]` extra)
  - `google-auth>=2.25.0` - Google authentication library
  - `google-auth-oauthlib>=1.2.0` - OAuth2 flow
  - `cryptography>=41.0.0` - Credential encryption (Fernet)

- **Files Changed**: +5054 / -26 lines
  - **New files**: 14 (auth module, tests, docs)
  - **Modified files**: 3 (`llm.py`, `installation.md`, `mkdocs.yml`)

- **Technical Learnings**
  - Google auth library uses timezone-naive UTC datetime (`_helpers.utcnow()`)
  - OAuth2 tokens can be used directly as LiteLLM API keys
  - Mock patching must target class definition location, not import location
  - Documentation clarity is crucial for advanced features (API Key vs OAuth2)

### Fixed

- **Documentation Clarity**
  - Added prominent notices that API Key is recommended for most users
  - Clarified OAuth2 is an advanced feature for specific use cases
  - Added comparison tables showing OAuth2 vs API Key trade-offs
  - Emphasized OAuth2 is Google/Gemini only (Claude and OpenAI use API keys)

## [2.3.1] - 2025-10-11

### Fixed

- **Examples Health Check Fixes**
  - **AgentBuilder.with_session_id() implementation** ([#142](https://github.com/JFK/kagura-ai/issues/142), PR [#147](https://github.com/JFK/kagura-ai/pull/147))
    - Added `with_session_id()` method to `AgentBuilder` for memory session isolation
    - Added `session_id` field to `MemoryConfig`
    - Integrated with `MemoryManager.set_session_id()`
    - 25 comprehensive tests (100% coverage)

  - **Conditional workflow import fix** ([#143](https://github.com/JFK/kagura-ai/issues/143), PR [#148](https://github.com/JFK/kagura-ai/pull/148))
    - Removed unused `conditional` import from workflow example
    - Created feature request [#149](https://github.com/JFK/kagura-ai/issues/149) for conditional workflow helpers

  - **JSON parsing improvements** ([#144](https://github.com/JFK/kagura-ai/issues/144), PR [#151](https://github.com/JFK/kagura-ai/pull/151))
    - Fixed `extract_json()` to return longest (outermost) JSON structure
    - Added automatic JSON format instructions for Pydantic model return types
    - Fixed `Task` model field names in data_extractor example
    - Resolved LLM returning schema mixed with data

  - **Mock testing framework fixes** ([#145](https://github.com/JFK/kagura-ai/issues/145), PR [#152](https://github.com/JFK/kagura-ai/pull/152))
    - Updated `LLMMock` to use `litellm.acompletion` (async version)
    - Fixed all mock test paths to use correct litellm API
    - Fixed `test_with_mocks.py` to use `mock_llm()` instead of `mock_llm_response()`
    - All 10 mock tests now passing

  - **Pytest collection warnings** ([#146](https://github.com/JFK/kagura-ai/issues/146), PR [#150](https://github.com/JFK/kagura-ai/pull/150))
    - Added both `__init__` and `setup_method` to `AgentTestCase` for dual usage pattern
    - Fixed pytest collection warnings for test classes
    - All 36 testing module tests passing

### Tests

- All examples health check issues resolved
- 46 total tests passing (10 mock tests + 36 testing module tests)
- 0 pytest collection warnings
- Pyright: 0 errors
- Ruff: All checks passed

## [2.3.0] - 2025-10-11

### Added

- **RFC-002: Multimodal RAG** ([#62](https://github.com/JFK/kagura-ai/issues/62))
  - **Phase 1: Gemini API Integration** (Week 1, [#121](https://github.com/JFK/kagura-ai/issues/121))
    - Gemini 1.5 Flash/Pro support for multimodal processing
    - Image analysis with vision API
    - Audio transcription capabilities
    - Video content analysis
    - PDF document processing
    - Optional dependency: `pip install kagura-ai[multimodal]`

  - **Phase 2: Multimodal Loaders** (Week 2, [#122](https://github.com/JFK/kagura-ai/issues/122))
    - `GeminiLoader` class for multimodal file processing
    - `DirectoryScanner` with parallel file processing
    - File type detection for images, audio, video, PDFs, text
    - `.gitignore` and `.kaguraignore` support
    - File content caching with `LoaderCache`
    - Configurable cache size and TTL

  - **Phase 3: ChromaDB Integration** (Week 3, [#123](https://github.com/JFK/kagura-ai/issues/123))
    - `MultimodalRAG` class extending `MemoryRAG`
    - Automatic directory indexing with `build_index()`
    - Incremental updates with `incremental_update()`
    - Semantic search across all file types
    - File type filtering in queries
    - `@agent` integration with `enable_multimodal_rag=True`
    - Persistent index storage with ChromaDB

- **RFC-014: Web Integration** ([#75](https://github.com/JFK/kagura-ai/issues/75))
  - **Phase 1: Web Search** (Week 4, [#124](https://github.com/JFK/kagura-ai/issues/124))
    - `BraveSearch` class with API integration
    - `DuckDuckGoSearch` as fallback (no API key required)
    - `web_search()` convenience function
    - `SearchResult` dataclass for structured results
    - Automatic fallback from Brave to DuckDuckGo
    - Optional dependency: `pip install kagura-ai[web]`

  - **Phase 2: Web Scraping** (Week 5, [#125](https://github.com/JFK/kagura-ai/issues/125))
    - `WebScraper` class with BeautifulSoup
    - HTML fetching with httpx (async)
    - Text extraction with `fetch_text()`
    - CSS selector-based scraping
    - `robots.txt` compliance with `RobotsTxtChecker`
    - Rate limiting with `RateLimiter`
    - Configurable user agent and delays

- **Full-Featured Chat Mode** (Week 6, [#126](https://github.com/JFK/kagura-ai/issues/126), PR [#138](https://github.com/JFK/kagura-ai/pull/138))
  - `--full` flag for combined multimodal RAG + web search
  - `kagura chat --full --dir <path>` single command
  - Automatic validation (requires `--dir` when using `--full`)
  - Rich progress indicators:
    - 🌐 Web search progress
    - 💬 AI response generation
    - RAG file search status
  - Special "🚀 Full-Featured Mode" banner in UI
  - Tool calling loop implementation for OpenAI-compatible agents
  - Support for both sync and async tool functions

### Documentation

- **User Guides** (PR [#140](https://github.com/JFK/kagura-ai/pull/140))
  - `docs/en/guides/chat-multimodal.md` - Multimodal RAG guide (400+ lines)
    - Setup and installation
    - Supported file types
    - Programmatic API usage
    - Agent integration examples
    - Configuration options
    - Best practices and troubleshooting

  - `docs/en/guides/web-integration.md` - Web integration guide (350+ lines)
    - Web search and scraping
    - Brave Search and DuckDuckGo setup
    - robots.txt compliance
    - Rate limiting best practices
    - Agent integration patterns
    - Ethical scraping guidelines

  - `docs/en/guides/full-featured-mode.md` - Full-featured mode guide (450+ lines)
    - Combined multimodal RAG + web search
    - Use cases and examples
    - Intelligent routing
    - Cost estimation
    - Performance optimization
    - Real-world applications

### Tests

- **Integration Tests** (PR [#139](https://github.com/JFK/kagura-ai/pull/139))
  - 7 multimodal RAG integration tests
  - 9 web integration tests
  - 5 full-featured mode integration tests
  - **Total integration tests**: 34 (up from 13)
  - All tests passing with 100% success rate

### Changed

- Enhanced `@agent` decorator with tool calling loop
  - Renamed internal parameter `tools` → `tool_functions` to avoid conflicts
  - Support for OpenAI-compatible tool calling
  - Iterative tool execution with max 5 iterations
  - Automatic tool result injection back to LLM
  - Support for both sync and async tools

- Improved `kagura chat` command
  - Added `--full` flag for full-featured mode
  - Added `--enable-multimodal` and `--dir` options
  - Added `--enable-web` option
  - Better progress indication with Rich console
  - Validation for required parameters

- Updated integration test mocks
  - Fixed `mock_llm_response` to include `tool_calls=None`
  - Proper `SearchResult` dataclass usage in web tests
  - Improved error messages in test failures

### Fixed

- Tool calling loop implementation
  - Fixed infinite loop when LLM returns empty content with tool calls
  - Added maximum iteration limit (5) to prevent hangs
  - Proper tool result formatting for conversation history

- Parameter naming conflicts
  - Resolved `tools` keyword argument conflict in `call_llm()`
  - Clean separation between Python callables and OpenAI schema

- Integration test stability
  - Fixed DuckDuckGo search mock with proper context manager
  - Fixed memory access in full-featured mode tests
  - Removed problematic CLI tests with asyncio conflicts

## [2.2.0] - 2025-10-10

### Added

- **RFC-018: Memory RAG (Phase 2)** ([#85](https://github.com/JFK/kagura-ai/issues/85), PR [#105](https://github.com/JFK/kagura-ai/pull/105))
  - `MemoryRAG` class for semantic memory retrieval
  - ChromaDB integration for vector search
  - `store_semantic()` and `recall_semantic()` methods
  - Agent-scoped semantic search
  - Optional dependency: `pip install kagura-ai[memory]`
  - 9 comprehensive tests (100% coverage)

- **RFC-019: Unified Agent Builder** ([#87](https://github.com/JFK/kagura-ai/issues/87))
  - **Phase 1: Core Builder** (PR [#111](https://github.com/JFK/kagura-ai/pull/111))
    - `AgentBuilder` class with fluent API pattern
    - Method chaining for easy configuration
    - `AgentConfig`, `MemoryConfig`, `LLMConfig` classes
    - 19 unit tests (100% coverage)

  - **Phase 1.5: Memory + Tools Integration** (PR [#112](https://github.com/JFK/kagura-ai/pull/112))
    - `tools` parameter in `@agent` decorator
    - Automatic tool conversion to LLM format
    - Memory configuration integration
    - 4 integration tests

  - **Phase 2: Hooks + Presets** (PR [#113](https://github.com/JFK/kagura-ai/pull/113))
    - Hooks wrapper for pre/post execution
    - `ChatbotPreset`, `ResearchPreset`, `CodeReviewPreset`
    - 11 preset tests
    - **Total**: 31 tests, 3 built-in presets

- **RFC-022: Agent Testing Framework** (PR [#114](https://github.com/JFK/kagura-ai/pull/114))
  - `AgentTestCase` class for comprehensive agent testing
  - Flexible assertions for non-deterministic LLM responses
    - `assert_contains()`, `assert_any_of()`, `assert_pattern()`
  - Mocking utilities: `mock_llm_response()`, `MockLLMProvider`
  - Performance testing: `Timer` utility
  - Cost tracking: `assert_cost_below()`
  - pytest plugin with `@pytest.mark.agent` marker
  - Optional dependency: `pip install kagura-ai[testing]`
  - 34 tests (32 passed, 2 skipped)

- **RFC-001: Workflow System - Advanced Patterns** ([#61](https://github.com/JFK/kagura-ai/issues/61), PR [#115](https://github.com/JFK/kagura-ai/pull/115))
  - `@workflow.chain` - Sequential execution chains
  - `@workflow.parallel` - Parallel execution helper with `run_parallel()`
  - `@workflow.stateful` - Pydantic-based state graphs (LangGraph-compatible)
  - Multi-agent orchestration support
  - 17 comprehensive tests (100% coverage)

- **RFC-020: Memory-Aware Routing** (PR [#116](https://github.com/JFK/kagura-ai/pull/116))
  - **ContextAnalyzer**: Detects context-dependent queries
    - Pronoun detection (it, this, that, them, etc.)
    - Implicit reference detection (also, too, again, etc.)
    - Follow-up question detection (what about, how about, etc.)
    - Smart filtering to prevent false positives
    - 28 unit tests (100% coverage)

  - **MemoryAwareRouter**: Context-enhanced agent routing
    - Extends `AgentRouter` with conversation history
    - Automatic query enrichment using context
    - `MemoryManager` integration
    - Optional RAG support for semantic context
    - 20 integration tests (100% coverage)
    - **Total routing tests**: 83 (all passing)

- **RFC-021: Agent Observability Dashboard** ([#109](https://github.com/JFK/kagura-ai/issues/109))
  - **Phase 1: Telemetry Collection** (PR [#117](https://github.com/JFK/kagura-ai/pull/117))
    - `EventStore` - SQLite-based event storage
    - `TelemetryCollector` - Metrics collection engine
    - `Telemetry` - Decorator-based instrumentation
    - Track LLM calls, tool calls, memory operations
    - Cost tracking and performance metrics
    - 70 comprehensive tests (100% coverage)

  - **Phase 2: CLI Dashboard** (PR [#118](https://github.com/JFK/kagura-ai/pull/118))
    - `Dashboard` class with Rich TUI visualization
    - Real-time monitoring with auto-refresh
    - **CLI Commands**:
      - `kagura monitor` / `kagura monitor live` - Live dashboard
      - `kagura monitor list` - Execution history with filters
      - `kagura monitor stats` - Statistics summary
      - `kagura monitor trace <id>` - Detailed execution trace
      - `kagura monitor cost` - Cost analysis by agent/date
    - Timeline visualization with event details
    - Monthly cost estimation
    - 37 comprehensive tests (23 dashboard + 14 CLI, 100% coverage)
    - **Total observability tests**: 107

### Changed

- Enhanced `@agent` decorator with `tools` parameter support
- Improved routing system with context awareness
- Updated CLI with `kagura monitor` command group

### Documentation

- Memory RAG integration guide
- Agent Builder tutorial and API reference
- Testing framework guide with examples
- Advanced workflow patterns documentation
- Memory-aware routing guide
- Observability dashboard tutorial

### Tests

- Added 9 Memory RAG tests (100% coverage)
- Added 31 Agent Builder tests (100% coverage)
- Added 34 Agent Testing Framework tests
- Added 17 Advanced Workflow tests (100% coverage)
- Added 48 Memory-Aware Routing tests (100% coverage)
- Added 107 Observability tests (100% coverage)
- **Total v2.2.0 tests**: 246 new tests
- **Total project tests**: 586+ tests passing

### Fixed

- Monitor CLI shortcut support for `kagura monitor` (without subcommand)

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

[2.2.0]: https://github.com/JFK/kagura-ai/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/JFK/kagura-ai/compare/v2.0.2...v2.1.0
[2.0.2]: https://github.com/JFK/kagura-ai/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/JFK/kagura-ai/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/JFK/kagura-ai/compare/v2.0.0-beta.1...v2.0.0
[2.0.0-beta.1]: https://github.com/JFK/kagura-ai/compare/v2.0.0-alpha.1...v2.0.0-beta.1
[2.0.0-alpha.1]: https://github.com/JFK/kagura-ai/releases/tag/v2.0.0-alpha.1
