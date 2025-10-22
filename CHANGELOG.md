# Changelog

## [Unreleased]

## [3.0.7] - 2025-10-22

### Added
- **Memory**: Persistent memory now supports RAG (semantic) search (#340, #353)
  - Dual RAG system: separate ChromaDB collections for working and persistent memory
  - Auto-indexing when storing persistent data with `remember()`
  - New `scope` parameter for `recall_semantic()` and `memory_search()` ("working", "persistent", "all")
  - Semantic search for user preferences, facts, and long-term knowledge
  - Resolves #337 (memory_search now finds memory_store data in persistent scope)
  - 9 new integration tests for persistent RAG functionality

### Fixed
- **MCP**: Fixed telemetry agent_name conflict in memory tools (#344, #349)
  - Memory tools (memory_store, memory_recall, memory_search) now work correctly with telemetry tracking
  - Removed duplicate agent_name parameter when calling track_execution()
  - No impact on other tools (they don't have agent_name parameter)
- **Tests**: Fixed integration test failures in preset agents (#335, #350)
  - Tests now handle both str and LLMResponse return types
  - Updated 5 tests for agents with `-> str` annotation (TranslateAgent, CodeReviewAgent, SummarizeAgent)
  - Tests align with v3.0.2 behavior where `-> str` returns plain strings
- **CI**: Re-enabled type checking in test workflow (#328, #351)
  - Fixed pyrightconfig.json to include entire src/kagura directory
  - Updated pyright to 1.1.406 (from 1.1.390)
  - CI type checking now completes in ~2 minutes (previously timed out at 2min)
  - Type safety restored in CI pipeline

### Changed
- **Documentation**: Updated for recent core changes (#329, #352)
  - CHANGELOG.md updated with all recent fixes
  - V3.0_DEVELOPMENT.md enhanced with integration test patterns and CI best practices
  - Added WORK_LOG_2025-10-22.md for historical context
- **MCP**: Memory tools now always enable RAG for both working and persistent scopes (#353)
  - Better user experience with consistent semantic search availability
  - Resolves "RAG unavailable" messages when storing persistent data

## [3.0.6] - 2025-10-21

### Changed
- **MCP**: Removed debug logging from memory tools for cleaner production output (#336)
- **Testing**: Improved memory tools test suite with 8 comprehensive tests

### Known Issues
- **memory_search**: Does not search data from memory_store (#337)
  - memory_store saves to WorkingMemory (in-memory dict)
  - memory_search searches MemoryRAG (vector DB)
  - Use memory_recall() to retrieve data stored with memory_store()
  - Full RAG integration planned for future release

## [3.0.5] - 2025-10-21

### Fixed
- **MCP**: Fixed working memory persistence across MCP tool calls (#333)
  - Added global cache for MemoryManager instances
  - Working memory now properly shared across memory_store/memory_recall/memory_search
  - Each agent_name maintains a single MemoryManager instance
  - Fixed critical bug where stored data was immediately lost after tool call

## [3.0.4] - 2025-10-21

### Fixed
- **MCP**: Fixed `brave_news_search` HttpUrl JSON serialization error (#333)
  - Converted all result fields to strings before JSON serialization
  - News search now returns valid JSON instead of serialization error

## [3.0.3] - 2025-10-21

### Fixed
- **MCP**: Fixed parameter type conversion issues in MCP tools (#333)
  - `brave_news_search`: count parameter now accepts string input
  - `memory_search`: k parameter now accepts string input
  - `multimodal_search`: k parameter now accepts string input
  - `memory_recall`: Returns helpful message instead of empty string when key not found

## [3.0.2] - 2025-10-21

### Fixed
- **MCP**: Fixed async tools returning coroutine objects instead of actual results via MCP server (#327)
  - Web search (brave_web_search, brave_news_search)
  - YouTube tools (get_youtube_transcript, get_youtube_metadata)
  - Memory tools (memory_store, memory_recall, memory_search)
  - Fact checking (fact_check_claim)
  - Shell execution (shell_exec)
- **Core**: `@agent` decorator now returns `str` content instead of `LLMResponse` object when return type is `-> str` (#326, #325)
- **Core**: Replaced `isinstance(response, LLMResponse)` with `hasattr` checks to avoid circular import issues (#326, #325)
- **Tests**: Added comprehensive tests for personal tools (daily_news, weather_forecast, search_recipes, find_events) (#326)
- **CI**: Temporarily disabled type checking due to timeout issues in CI environment (tracked in #328)

### Changed
- **Testing**: Improved LLMMock to properly handle `LLMResponse` objects
- **Code Quality**: Resolved TODO comments and improved type validation in tool decorator (#325)

## [3.0.1] - 2025-10-19

### Fixed
- **Critical**: Telemetry JSON serialization with MemoryManager (#322)
- **Critical**: Code execution LLMResponse handling (#323)
- Examples: 25+ updated to v3.0 API (#322)
- Tests: 11 integration tests fixed (#323)

### Added
- SDK Integration examples (FastAPI, Streamlit, etc.) (#319)
- Personal Tools examples (news, weather, recipes, events) (#319)
- Multimodal test data (sample.jpg, sample.pdf) (#323)

### Changed
- Examples reorganized 01-09 (#319)
- Examples working rate: 37% → 83%
- Integration tests: 17 failed → 3 failed

## [3.0.0] - 2025-10-19

### Added
- SDK-first positioning
- Personal tools (news, weather, recipes, events)
- Tool registry system

### Changed
- Examples completely reorganized
- Documentation refreshed

---

See git history for earlier versions.
