# Kagura AI: API/MCP/CLI Architecture Refactoring Plan (v4.3.0)

**Issue:** [#714](https://github.com/JFK/kagura-ai/issues/714)
**Target Release:** v4.3.0
**Status:** Phase 1 - Planning & Investigation
**Date:** 2025-11-18

## Executive Summary

Investigation of `kagura/api/`, `kagura/cli/mcp/`, and `kagura/mcp/` revealed critical architectural issues causing **35-40% code duplication** across three layers. This document outlines a systematic refactoring plan to:

- Reduce code duplication from 35-40% to **<10%**
- Consolidate 6 authentication patterns into **1 unified system**
- Extract business logic into reusable **service layer**
- Maintain **100% backward compatibility** (v4.3.0 requirement)

## Problem Statement

### 1. Triple Implementation Pattern (35-40% Duplication)

The same functionality is implemented **three times** with slightly different interfaces:

| Feature | MCP Tool | REST API | CLI Command |
|---------|----------|----------|-------------|
| **Memory storage** | `memory_store()` in `mcp/tools/memory/storage.py` | `POST /api/v1/memory` in `api/routes/memory.py` | `kagura memory store` |
| **Coding sessions** | `coding_start_session()` in `mcp/tools/coding/session.py` | `GET /api/v1/coding/sessions` in `api/routes/coding.py` | `kagura coding sessions` |
| **Health checks** | `telemetry_stats()` in `mcp/builtin/observability.py` | `GET /api/v1/system/doctor` in `api/routes/system.py` | `kagura mcp doctor` |

**Impact:**
- Bug fixes must be applied 3 times
- Behavior diverges over time (inconsistency risk)
- Maintenance burden increases linearly with features

**Example: Memory Manager Instantiation**

Three different patterns for the same operation:

```python
# Pattern 1: MCP Tools (with cache validation)
# mcp/tools/memory/common.py
_memory_cache: dict[str, MemoryManager] = {}

def get_memory_manager(user_id, agent_name, enable_rag=False):
    cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
    if cache_key in _memory_cache:
        cached = _memory_cache[cache_key]
        # Validate cache to prevent stale instances
        required_attrs = ["persistent_rag", "rag", "graph", "persistent"]
        missing_attrs = [a for a in required_attrs if not hasattr(cached, a)]
        if missing_attrs:
            logger.warning(f"Cached MemoryManager missing {missing_attrs}")
            del _memory_cache[cache_key]
        else:
            return cached
    _memory_cache[cache_key] = MemoryManager(user_id, agent_name, enable_rag)
    return _memory_cache[cache_key]

# Pattern 2: API Dependencies (simple cache, different defaults)
# api/dependencies.py
_memory_managers: dict[str, MemoryManager] = {}

def get_memory_manager(user_id: str = Depends(get_user_id)):
    if user_id not in _memory_managers:
        persist_dir = get_data_dir() / "api" / user_id
        _memory_managers[user_id] = MemoryManager(
            user_id=user_id,
            agent_name="api",  # Hardcoded!
            persist_dir=persist_dir,
            enable_rag=True,
            enable_compression=False  # Different default!
        )
    return _memory_managers[user_id]

# Pattern 3: Coding Tools (no cache)
# mcp/tools/coding/common.py
def get_coding_memory(user_id: str, project_id: str):
    # NOTE: No caching! Always fresh instance (v4.0.9 fix)
    return CodingMemoryManager(
        user_id=user_id,
        project_id=project_id,
        enable_rag=True,
        enable_graph=True
    )
```

### 2. Authentication Chaos (6 Different Patterns)

| Module | Purpose | Database | Status |
|--------|---------|----------|--------|
| `api/auth.py::APIKeyManager` | API Key auth (SQLite only) | `api_keys.db` | **DEPRECATED** |
| `auth/api_key_manager.py::APIKeyManagerSQL` | API Key auth (SQLAlchemy) | PostgreSQL/SQLite | **Current** |
| `auth/oauth2.py::OAuth2Manager` | OAuth2 client (3rd party login) | PostgreSQL | Active |
| `auth/oauth2_server.py::OAuth2Server` | OAuth2 server (Issue #674) | PostgreSQL | Active |
| `auth/mcp_auth.py::authenticate_mcp_request()` | MCP transport auth | N/A | Active |
| `api/dependencies.py::get_current_user()` | Session-based auth | Redis | Active |

**Issues:**
1. **Deprecated code not removed:** `api/auth.py` still exists with deprecation warnings
2. **Duplication:** API key verification logic exists in 3 places
3. **Inconsistent patterns:**
   - API routes: `Depends(get_current_user)` (session-based)
   - MCP transport: `authenticate_mcp_request()` (Bearer token)
   - CLI: Neither (direct database access)

### 3. Configuration Fragmentation (3 Different Systems)

| Module | Approach | Use Case |
|--------|----------|----------|
| `mcp/config.py::MCPConfig` | JSON file manipulation | Claude Desktop integration |
| `cli/mcp/config.py` | CLI commands | User-facing commands |
| `api/routes/config.py` | REST API | Web UI configuration |

**Example Inconsistency:**

```python
# mcp/config.py - Direct file manipulation
class MCPConfig:
    def add_to_claude_desktop(self, server_name: str = "kagura-memory"):
        config = self.get_claude_desktop_config()
        config["mcpServers"][server_name] = {...}
        with open(self.claude_config_path, "w") as f:
            json.dump(config, f)

# api/routes/config.py - Environment variable approach
@router.put("/api/v1/config/{key}")
async def update_config(key: str, value: str):
    env_manager.set(key, value)  # Different approach!
```

### 4. Inconsistent Error Handling

| Layer | Pattern | Example |
|-------|---------|---------|
| **MCP Tools** | Return error strings | `return "[ERROR] Failed to ..."` |
| **API Routes** | Raise HTTPException | `raise HTTPException(status_code=400)` |
| **Core Memory** | Raise ValueError/RuntimeError | `raise ValueError("...")` |

**Impact:** Clients must handle errors differently depending on interface.

### 5. Oversized Files

**Files exceeding 500 lines** (v4.3.0 target):

- `api/routes/oauth.py`: **1,037 lines** (OAuth2 server)
- `api/routes/system.py`: **826 lines** (System endpoints + doctor)
- `api/routes/memory.py`: **589 lines** (Memory CRUD + doctor)
- `mcp/tools/coding/source_indexing.py`: **454 lines** (RAG indexing)
- `mcp/tools/coding/session.py`: **434 lines** (Session management)

## Solution Architecture

### Service Layer Pattern

Extract business logic from interface layers (MCP/API/CLI) into reusable services:

```
┌─────────────────────────────────────────────────────────────┐
│                     External Clients                         │
│  (Claude Code, ChatGPT, Cline, Web UI, CLI)                │
└────────────┬─────────────────┬─────────────────┬───────────┘
             │                 │                 │
             │ (stdio)         │ (HTTP/SSE)      │ (CLI)
             ▼                 ▼                 ▼
    ┌────────────────┐ ┌─────────────────┐ ┌────────────┐
    │  MCP Tools     │ │   API Routes    │ │ CLI Cmds   │
    │  (thin layer)  │ │  (thin layer)   │ │ (thin)     │
    └────────┬───────┘ └────────┬────────┘ └──────┬─────┘
             │                  │                  │
             └──────────┬───────┴──────────────────┘
                        │ (all call services)
                        ▼
             ┌──────────────────────┐
             │   Service Layer      │  ← NEW
             │  (business logic)    │
             ├──────────────────────┤
             │ - MemoryService      │
             │ - CodingService      │
             │ - HealthService      │
             │ - AuthService        │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │   Core Memory        │
             │  (data access)       │
             └──────────────────────┘
```

**Benefits:**
- **Single source of truth** for business logic
- **40% code reduction** (eliminate duplication)
- **Easier testing** (mock services, not infrastructure)
- **Consistent behavior** across all interfaces

## Implementation Plan

### Phase 1: Authentication + Service Layer (2-3 weeks)

#### 1.1 Unified Authentication (2-3 days)

**Create:** `src/kagura/auth/unified_auth.py`

```python
class UnifiedAuthManager:
    """Single authentication manager for all interfaces."""

    def __init__(self, db_url: str, redis_url: str | None = None):
        self.api_key_manager = APIKeyManagerSQL(db_url)
        self.oauth2_manager = OAuth2Manager(db_url) if redis_url else None

    async def authenticate(
        self,
        auth_header: str | None,
        session_token: str | None = None,
        allow_anonymous: bool = False
    ) -> AuthResult:
        """Authenticate request using available credentials.

        Priority: OAuth2 > API Key > Session > Anonymous
        """
        # Try OAuth2 token
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user_id = await self._verify_oauth2(token)
            if user_id:
                return AuthResult(user_id=user_id, method="oauth2")

        # Try API key
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
            user_id = await self._verify_api_key(api_key)
            if user_id:
                return AuthResult(user_id=user_id, method="api_key")

        # Try session token
        if session_token:
            user_id = await self._verify_session(session_token)
            if user_id:
                return AuthResult(user_id=user_id, method="session")

        # Anonymous access
        if allow_anonymous:
            return AuthResult(user_id="default_user", method="anonymous")

        # No valid credentials
        raise AuthenticationError("No valid credentials provided")
```

**Update:**
- Remove `api/auth.py` (deprecated)
- Update `api/dependencies.py` to use `UnifiedAuthManager`
- Update `auth/mcp_auth.py` to use `UnifiedAuthManager`
- Update CLI to use `UnifiedAuthManager` for remote operations

**Tests:**
- Unit tests for each auth method
- Integration tests for priority fallback
- Security tests (expired tokens, invalid keys)

#### 1.2 Service Layer Extraction (1-2 weeks)

**Create:** `src/kagura/services/`

**Structure:**
```
services/
├── __init__.py
├── base.py              # BaseService with common utilities
├── memory_service.py    # Memory CRUD operations
├── coding_service.py    # Coding session management
├── health_service.py    # Diagnostics and health checks
└── auth_service.py      # Authentication business logic
```

**Example: MemoryService**

```python
# services/memory_service.py
from typing import Any
from kagura.core.memory import MemoryManager

class MemoryService:
    """Business logic for memory operations."""

    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

    async def store_memory(
        self,
        key: str,
        value: str,
        tags: list[str] | None = None,
        importance: float = 0.5
    ) -> MemoryResult:
        """Store memory with validation.

        Args:
            key: Memory key (unique identifier)
            value: Memory content
            tags: Optional tags for categorization
            importance: Importance score (0.0-1.0)

        Returns:
            MemoryResult with success status and metadata

        Raises:
            ValidationError: If parameters are invalid
            MemoryError: If storage fails
        """
        # Validation
        if not key:
            raise ValidationError("Key is required")
        if not value:
            raise ValidationError("Value is required")
        if importance < 0 or importance > 1:
            raise ValidationError("Importance must be 0-1")

        # Business logic
        metadata = {
            "tags": tags or [],
            "importance": importance,
            "source": "api",  # Can be customized
        }

        try:
            await self.memory.store(key, value, metadata)
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise MemoryError(f"Storage failed: {str(e)}")

        return MemoryResult(key=key, success=True, metadata=metadata)
```

**Usage in MCP Tool:**

```python
# mcp/tools/memory/storage.py
@tool
async def memory_store(
    user_id: str,
    agent_name: str,
    key: str,
    value: str,
    tags: str = "[]",
    importance: str = "0.5"
) -> str:
    """Store memory (MCP tool interface)."""
    try:
        # Get service
        memory_manager = get_memory_manager(user_id, agent_name)
        service = MemoryService(memory_manager)

        # Parse parameters
        tags_list = json.loads(tags)
        importance_float = float(importance)

        # Call service
        result = await service.store_memory(key, value, tags_list, importance_float)

        # Format response for MCP
        return f"[SUCCESS] Memory stored: {result.key}"

    except KaguraError as e:
        return MCPErrorAdapter.to_mcp_response(e)
```

**Usage in API Route:**

```python
# api/routes/memory.py
@router.post("/memory", response_model=MemoryResponse)
async def create_memory(
    request: MemoryCreateRequest,
    user: CurrentUser = Depends(get_current_user)
):
    """Store memory (REST API interface)."""
    try:
        # Get service
        memory_manager = get_memory_manager(user["sub"])
        service = MemoryService(memory_manager)

        # Call service (same as MCP!)
        result = await service.store_memory(
            key=request.key,
            value=request.value,
            tags=request.tags,
            importance=request.importance
        )

        # Format response for API
        return MemoryResponse(**result.dict())

    except KaguraError as e:
        raise APIErrorAdapter.to_http_exception(e)
```

**Usage in CLI:**

```python
# cli/memory/store.py
@click.command()
@click.option("--key", required=True)
@click.option("--value", required=True)
@click.option("--tags", multiple=True)
@click.option("--importance", type=float, default=0.5)
def store(key, value, tags, importance):
    """Store memory (CLI interface)."""
    try:
        # Get service
        memory_manager = get_memory_manager("cli_user", "cli")
        service = MemoryService(memory_manager)

        # Call service (same as MCP and API!)
        result = asyncio.run(
            service.store_memory(key, value, list(tags), importance)
        )

        # Format response for CLI
        console.print(f"[green]✓[/green] Memory stored: {result.key}")

    except KaguraError as e:
        console.print(f"[red]✗[/red] {e.message}", style="bold red")
        raise click.Abort()
```

**Key Points:**
- **Same business logic** across all interfaces
- **Interface-specific formatting** (MCP string, API JSON, CLI Rich)
- **Consistent error handling** (KaguraError → adapter → interface format)

#### Services to Create

1. **MemoryService** (`services/memory_service.py`)
   - `store_memory()` - Store with validation
   - `recall_memory()` - Retrieve with fallback
   - `search_memory()` - Hybrid search
   - `delete_memory()` - Delete with audit
   - `list_memories()` - List with pagination

2. **CodingService** (`services/coding_service.py`)
   - `start_session()` - Session lifecycle
   - `end_session()` - Generate summary
   - `track_file_change()` - File tracking
   - `record_error()` - Error recording
   - `record_decision()` - Decision logging
   - `search_sessions()` - Session search

3. **HealthService** (`services/health_service.py`)
   - `run_diagnostics()` - Full health check
   - `check_memory_system()` - Memory subsystem
   - `check_coding_system()` - Coding subsystem
   - `get_system_info()` - Version, config, stats

4. **AuthService** (`services/auth_service.py`)
   - `create_api_key()` - Generate API key
   - `revoke_api_key()` - Revoke access
   - `verify_key()` - Validate API key
   - `list_user_keys()` - List user's keys

**Update Targets:**
- MCP tools (`mcp/tools/`) → Call services
- API routes (`api/routes/`) → Call services
- CLI commands (`cli/`) → Call services

**Expected Impact:**
- **40% code reduction**
- **Consistent behavior** across interfaces
- **Easier testing** (mock services)
- **Single source of truth** for business logic

### Phase 2: Error Handling + Configuration (1-2 weeks)

#### 2.1 Unified Error Handling (3-5 days)

**Extend:** `src/kagura/utils/common/errors.py`

```python
class KaguraError(Exception):
    """Base exception for all Kagura errors."""

    def __init__(self, message: str, code: str, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class ValidationError(KaguraError):
    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")

class AuthenticationError(KaguraError):
    def __init__(self, message: str):
        super().__init__(message, code="AUTH_FAILED")

class MemoryError(KaguraError):
    def __init__(self, message: str):
        super().__init__(message, code="MEMORY_ERROR")

class CodingError(KaguraError):
    def __init__(self, message: str):
        super().__init__(message, code="CODING_ERROR")

# Error adapters for each interface
class MCPErrorAdapter:
    """Convert KaguraError to MCP tool response format."""

    @staticmethod
    def to_mcp_response(error: KaguraError) -> str:
        return f"[ERROR] {error.code}: {error.message}"

class APIErrorAdapter:
    """Convert KaguraError to HTTP exception."""

    STATUS_MAP = {
        "VALIDATION_ERROR": 400,
        "AUTH_FAILED": 401,
        "NOT_FOUND": 404,
        "MEMORY_ERROR": 500,
        "CODING_ERROR": 500,
    }

    @staticmethod
    def to_http_exception(error: KaguraError) -> HTTPException:
        status = APIErrorAdapter.STATUS_MAP.get(error.code, 500)
        return HTTPException(
            status_code=status,
            detail={
                "code": error.code,
                "message": error.message,
                "details": error.details
            }
        )

class CLIErrorAdapter:
    """Convert KaguraError to CLI formatted message."""

    @staticmethod
    def to_cli_message(error: KaguraError) -> str:
        # Rich console formatting
        from rich.console import Console
        console = Console()
        console.print(f"[red]✗[/red] {error.message}", style="bold red")
        if error.details:
            console.print(f"Details: {error.details}", style="dim")
```

**Migration:**
- Update all service methods to raise `KaguraError` subclasses
- Update MCP tools to use `MCPErrorAdapter`
- Update API routes to use `APIErrorAdapter`
- Update CLI commands to use `CLIErrorAdapter`

#### 2.2 Configuration Consolidation (1 week)

**Extend:** `src/kagura/config/manager.py`

```python
class ConfigManager:
    """Unified configuration management.

    Priority: env > file > database > default
    """

    def __init__(self):
        self.env = EnvManager()  # Environment variables
        self.file = FileConfigManager()  # YAML/JSON files
        self.db = DatabaseConfigManager()  # PostgreSQL

    def get(self, key: str, source: str = "auto") -> Any:
        """Get config value from appropriate source.

        Args:
            key: Configuration key
            source: Source priority ("auto", "env", "file", "db")

        Returns:
            Configuration value
        """
        if source == "auto":
            # Priority: env > file > db > default
            value = self.env.get(key)
            if value is not None:
                return value

            value = self.file.get(key)
            if value is not None:
                return value

            value = self.db.get(key)
            if value is not None:
                return value

            return self._get_default(key)

        elif source == "env":
            return self.env.get(key)
        elif source == "file":
            return self.file.get(key)
        elif source == "db":
            return self.db.get(key)
        else:
            raise ValueError(f"Invalid source: {source}")

    def set(self, key: str, value: Any, persist: bool = True):
        """Set config value.

        Args:
            key: Configuration key
            value: Configuration value
            persist: Whether to persist to database
        """
        # Always set in env (runtime)
        self.env.set(key, value)

        # Optionally persist
        if persist:
            self.db.set(key, value)
```

**Migrate:**
- `mcp/config.py::MCPConfig` → Use `ConfigManager`
- `api/routes/config.py` → Use `ConfigManager`
- `cli/mcp/config.py` → Use `ConfigManager`

#### 2.3 File Size Reduction (ongoing)

**Split Large Files:**

1. **`api/routes/oauth.py` (1,037 lines → 400 lines)**
   - Extract to `api/routes/oauth/server.py` (OAuth2 server)
   - Extract to `api/routes/oauth/client.py` (OAuth2 client)
   - Extract to `api/routes/oauth/models.py` (Request/response models)

2. **`api/routes/system.py` (826 lines → 400 lines)**
   - Extract to `api/routes/system/health.py` (Health checks)
   - Extract to `api/routes/system/info.py` (System info)
   - Extract to `api/routes/system/doctor.py` (Diagnostics)

3. **`api/routes/memory.py` (589 lines → 400 lines)**
   - Extract to `api/routes/memory/crud.py` (CRUD operations)
   - Extract to `api/routes/memory/search.py` (Search endpoints)
   - Extract to `api/routes/memory/doctor.py` (Memory diagnostics)

### Phase 3: Polish + Documentation (1 week)

#### 3.1 Tool Registration Simplification (3-4 days)

**Create:** `src/kagura/mcp/tools/registry.py`

```python
class ToolDefinition(NamedTuple):
    name: str
    func: Callable
    category: str  # Auto-inferred from name prefix
    remote_allowed: bool  # Permission control
    description: str

class UnifiedToolRegistry:
    """Single registration point for all MCP tools."""

    def register_tool(self, definition: ToolDefinition):
        # Register in global tool registry
        tool_registry.register(definition.name, definition.func)

        # Set permissions
        TOOL_PERMISSIONS[definition.name] = {
            "remote": definition.remote_allowed
        }

        # No need for manual category inference
        logger.info(f"Registered tool: {definition.name} ({definition.category})")

# Enhanced @tool decorator
def tool(
    category: str | None = None,
    remote: bool = True,
    description: str | None = None
):
    """Register MCP tool with all metadata in one step.

    Args:
        category: Tool category (auto-inferred if not provided)
        remote: Allow remote access (default: True)
        description: Tool description (auto-extracted from docstring)

    Example:
        @tool(category="memory", remote=True)
        async def memory_store(user_id, key, value):
            '''Store memory.'''
            ...
    """
    def decorator(func: Callable):
        # Auto-infer category from function name prefix
        if category is None:
            inferred_category = func.__name__.split("_")[0]
        else:
            inferred_category = category

        # Auto-extract description from docstring
        if description is None:
            doc = func.__doc__ or ""
            extracted_description = doc.split("\n")[0].strip()
        else:
            extracted_description = description

        # Create definition
        definition = ToolDefinition(
            name=func.__name__,
            func=func,
            category=inferred_category,
            remote_allowed=remote,
            description=extracted_description
        )

        # Register (single step!)
        registry = UnifiedToolRegistry()
        registry.register_tool(definition)

        return func

    return decorator
```

**Migration:**
- Update all `@tool` decorators to include metadata
- Remove manual `TOOL_PERMISSIONS` entries
- Remove manual category inference logic

#### 3.2 Documentation Updates (2-3 days)

**Update:**

1. **`ai_docs/ARCHITECTURE.md`**
   - Add Service Layer Pattern section
   - Update dependency diagrams
   - Document authentication flow

2. **`docs/api-reference.md`**
   - Update API endpoints
   - Add service layer examples
   - Document error response format

3. **`README.md`**
   - Update quick start (unified auth)
   - Add service layer examples
   - Update architecture overview

4. **Create: `ai_docs/MIGRATION_GUIDE_v4.3.0.md`**
   - Document breaking changes (if any)
   - Provide migration examples
   - List deprecated APIs

#### 3.3 Deprecation Cleanup (1-2 days)

**Remove Deprecated Code** (after 2-release warning period):

- `api/auth.py::APIKeyManager` (deprecated in v4.4.0)
- `mcp/builtin/*.py` facade files (deprecated in v4.1.0)
- Old configuration files

**Maintain Backward Compatibility:**

Use Facade pattern for old imports:

```python
# api/auth.py (facade)
import warnings
from kagura.auth.unified_auth import UnifiedAuthManager

def get_api_key_manager():
    warnings.warn(
        "api.auth.get_api_key_manager() is deprecated. "
        "Use auth.unified_auth.UnifiedAuthManager instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return UnifiedAuthManager()
```

## Backward Compatibility Strategy

All refactoring must maintain **100% backward compatibility** (v4.3.0 requirement).

**Strategy:**

1. **Facade Pattern:** Keep old interfaces, delegate to new implementation
2. **Deprecation Warnings:** Mark old code with `DeprecationWarning`
3. **Dual Support Period:** 2 releases before removal (v4.5.0)
4. **Migration Guide:** Document all breaking changes

**Example:**

```python
# Old (deprecated but supported)
from kagura.api.auth import APIKeyManager

def get_api_key_manager():
    warnings.warn("Use auth.unified_auth.UnifiedAuthManager()", DeprecationWarning)
    return UnifiedAuthManager()

# New (recommended)
from kagura.auth.unified_auth import UnifiedAuthManager
auth_manager = UnifiedAuthManager()
```

## Testing Strategy

**Each Phase:**

1. **Unit Tests**
   - Test services in isolation
   - Mock dependencies
   - Cover edge cases

2. **Integration Tests**
   - Test MCP tool → Service → Core
   - Test API route → Service → Core
   - Test CLI command → Service → Core

3. **Regression Tests**
   - Ensure old behavior preserved
   - Test deprecated APIs still work
   - Verify backward compatibility

**Quality Gates:**

- Test coverage: **90%+**
- Type coverage: **100%** (`pyright --strict`)
- Linting: **0 errors** (`ruff check`)
- All tests passing

## Success Metrics

### Current State

- Code duplication: ~35-40%
- Authentication systems: 6 patterns
- Memory manager factories: 3 implementations
- Files >500 lines: 5 files
- Average file size: 285 lines (API routes)

### Target State (v4.3.0)

- Code duplication: **<10%**
- Authentication systems: **1 unified system**
- Memory manager factories: **1 implementation**
- Files >500 lines: **0 files**
- Average file size: **<400 lines**

## Timeline

**Total: 4-6 weeks**

- **Phase 1:** 2-3 weeks (Auth + Service Layer)
- **Phase 2:** 1-2 weeks (Errors + Config + File Split)
- **Phase 3:** 1 week (Tool Registry + Docs + Cleanup)

## Related Issues

- #612 (v4.3.0 Code Quality & Organization)
- #436, #650, #655 (Authentication issues)
- #674 (OAuth2 server implementation)

## Next Steps

1. ✅ Create Issue #714
2. ✅ Create feature branch `714-refactor/api-mcp-cli-unification`
3. ⏳ Document investigation findings (this document)
4. ⏳ Phase 1.1: Implement `auth/unified_auth.py`
5. ⏳ Phase 1.2: Extract service layer
6. Update MCP tools to use services
7. Update API routes to use services
8. Update CLI commands to use services
9. Write comprehensive tests
10. Update documentation

---

**Author:** Claude Code + kiyota
**Date:** 2025-11-18
**Status:** Phase 1 - Planning & Investigation
