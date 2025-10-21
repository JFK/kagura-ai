# Changelog

## [Unreleased]

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
