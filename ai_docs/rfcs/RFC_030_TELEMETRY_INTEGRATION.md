# RFC-030: Telemetry Integration & Observability Enhancement

**ステータス**: Draft
**作成日**: 2025-10-15
**優先度**: ⭐️ High
**関連Issue**: TBD
**依存RFC**: RFC-021 (Agent Observability Dashboard)

---

## 📋 概要

### 問題

現在のKagura AIには**Telemetry機能が部分的にしか実装されておらず、実際には動作していません**。具体的には：

1. **@agentデコレータにTelemetryが統合されていない**
   - `TelemetryCollector`と`EventStore`は実装済み
   - しかし、`@agent`デコレータと統合されていない
   - 結果: `@agent`を使ったコードは一切telemetryに記録されない
   - `kagura monitor`コマンドを実行してもデータが0件

2. **DB選択の柔軟性不足**
   - 現在SQLite固定（`~/.kagura/telemetry.db`）
   - 他のバックエンド（PostgreSQL、MongoDB等）をサポートしていない
   - エンタープライズ環境で使いにくい

3. **セットアップの自動化不足**
   - `kagura init`コマンドが存在しない
   - ユーザーが手動で`.kagura/`ディレクトリを作成する必要がある
   - 初回実行時のUX悪化

4. **データ収集の非一貫性**
   - LLM呼び出し、tool呼び出し、メモリ操作が個別に記録されない
   - エージェント実行の全体像が把握できない

### 解決策

以下の4つのPhaseで段階的に実装：

1. **Phase 1: @agent統合** - `@agent`デコレータに自動Telemetry記録
2. **Phase 2: DB抽象化** - SQLite/PostgreSQL/MongoDB対応
3. **Phase 3: kagura init** - セットアップコマンド実装
4. **Phase 4: Dashboard拡張** - リアルタイム分析機能

---

## 🎯 目標

### 成功指標

1. **自動記録**
   - ✅ `@agent`デコレータ使用時に自動的にtelemetry記録
   - ✅ ユーザーコード変更不要
   - ✅ すべてのLLM呼び出し、tool呼び出し、メモリ操作を記録

2. **データ可視化**
   - ✅ `kagura monitor`でリアルタイムダッシュボード表示
   - ✅ コスト分析、パフォーマンス分析可能
   - ✅ エラートレース機能

3. **柔軟性**
   - ✅ 複数のDBバックエンド対応（SQLite/PostgreSQL/MongoDB）
   - ✅ 環境変数でバックエンド切り替え可能
   - ✅ カスタムストレージ実装可能

4. **UX向上**
   - ✅ `kagura init`コマンドで簡単セットアップ
   - ✅ 初回実行時の自動初期化
   - ✅ エラーメッセージの改善

---

## 🏗️ アーキテクチャ

### 現在の実装状況

```
✅ 実装済み（未統合）:
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ TelemetryCollector│    │    EventStore    │    │    Dashboard     │
│                  │    │                  │    │                  │
│ - track_execution│    │ - save_execution │    │ - show_live      │
│ - record_llm_call│    │ - get_executions │    │ - show_list      │
│ - record_tool    │    │ - get_stats      │    │ - show_stats     │
└──────────────────┘    └──────────────────┘    └──────────────────┘

❌ 問題: @agentデコレータと接続されていない
         ↓
┌──────────────────┐
│  @agent decorator│  ← Telemetryと統合されていない！
│                  │
│ - memory管理     │
│ - LLM呼び出し    │
│ - tool実行       │
└──────────────────┘
```

### Phase 1完了後の構成

```
┌─────────────────────────────────────────────────────────┐
│                    @agent decorator                      │
│  (自動的にTelemetryを統合)                               │
└───────────────────────┬─────────────────────────────────┘
                        │ 自動記録
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼────────┐  ┌───▼───────────┐  ┌──────▼──────┐
│ Telemetry      │  │ EventStore    │  │ Dashboard   │
│ Instrumentation│  │               │  │             │
│                │  │ - SQLite      │  │ - Live      │
│ - track_exec   │  │ - PostgreSQL  │  │ - Stats     │
│ - record_llm   │  │ - MongoDB     │  │ - Cost      │
│ - record_tool  │  │               │  │ - Trace     │
└────────────────┘  └───────────────┘  └─────────────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  StorageAdapter   │
        │  (抽象化層)       │
        └───────────────────┘
```

---

## 📦 Phase 1: @agent統合 (Week 1)

### 目標

- `@agent`デコレータに自動Telemetry記録を統合
- ユーザーコード変更不要
- 既存テスト全パス

### 実装内容

#### 1.1 @agentデコレータの拡張

```python
# src/kagura/core/decorators.py

from kagura.observability import get_global_telemetry

def agent(
    fn: Callable[P, Awaitable[T]] | None = None,
    *,
    # ... existing parameters ...
    enable_telemetry: bool = True,  # NEW
    **kwargs: Any,
):
    """Agent decorator with automatic telemetry

    Args:
        enable_telemetry: Enable automatic telemetry recording (default: True)
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # ... existing code ...

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs_inner: P.kwargs) -> T:
            # Enable telemetry if requested
            if enable_telemetry:
                telemetry = get_global_telemetry()
                collector = telemetry.get_collector()

                # Track execution
                async with collector.track_execution(
                    func.__name__,
                    **bound.arguments  # Agent arguments
                ):
                    # ... existing agent logic ...

                    # Record LLM call (after call_llm)
                    if hasattr(response, '_usage'):
                        collector.record_llm_call(
                            model=llm_config.model,
                            prompt_tokens=response._usage.get('prompt_tokens', 0),
                            completion_tokens=response._usage.get('completion_tokens', 0),
                            duration=llm_duration,
                            cost=calculate_cost(response._usage, llm_config.model)
                        )

                    # Record tool calls (if tools were used)
                    if hasattr(response, '_tool_calls'):
                        for tool_call in response._tool_calls:
                            collector.record_tool_call(
                                tool_name=tool_call['name'],
                                duration=tool_call.get('duration', 0.0),
                                kwargs=tool_call.get('arguments', {})
                            )

                    # Record memory operations (if memory enabled)
                    if enable_memory and has_memory_param:
                        collector.record_metric('memory_enabled', True)
                        collector.record_metric('max_messages', max_messages)

                    return result
            else:
                # No telemetry
                # ... existing agent logic without telemetry ...
                return result

        return wrapper

    return decorator if fn is None else decorator(fn)
```

#### 1.2 LLMレスポンスへのメタデータ追加

```python
# src/kagura/core/llm.py

async def call_llm(
    prompt: str,
    config: LLMConfig,
    tool_functions: Optional[list[Callable]] = None,
    **kwargs: Any,
) -> str:
    """Call LLM with telemetry support"""
    import time
    start_time = time.time()

    # ... existing LLM call logic ...

    response_text = response.choices[0].message.content

    # Attach usage metadata for telemetry
    if hasattr(response, 'usage') and response.usage:
        response_text._usage = {  # type: ignore
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
        }

    # Attach duration
    response_text._duration = time.time() - start_time  # type: ignore

    # Attach tool calls if any
    if tool_functions and hasattr(response.choices[0].message, 'tool_calls'):
        response_text._tool_calls = [  # type: ignore
            {
                'name': tc.function.name,
                'arguments': json.loads(tc.function.arguments),
                'duration': 0.0  # Will be measured by tool executor
            }
            for tc in response.choices[0].message.tool_calls
        ]

    return response_text
```

#### 1.3 コスト計算関数

```python
# src/kagura/observability/pricing.py

def calculate_cost(usage: dict[str, int], model: str) -> float:
    """Calculate LLM API cost based on usage

    Args:
        usage: Dict with prompt_tokens, completion_tokens
        model: Model name (e.g., "gpt-4o-mini")

    Returns:
        Cost in USD
    """
    # Pricing as of 2025 (per 1M tokens)
    pricing = {
        "gpt-4o-mini": {
            "prompt": 0.15,      # $0.15 / 1M tokens
            "completion": 0.60   # $0.60 / 1M tokens
        },
        "gpt-4o": {
            "prompt": 2.50,
            "completion": 10.00
        },
        "gpt-4-turbo": {
            "prompt": 10.00,
            "completion": 30.00
        },
        "claude-3-5-sonnet-20241022": {
            "prompt": 3.00,
            "completion": 15.00
        },
        "claude-3-opus-20240229": {
            "prompt": 15.00,
            "completion": 75.00
        },
        "gemini-1.5-pro": {
            "prompt": 1.25,
            "completion": 5.00
        },
        "gemini-1.5-flash": {
            "prompt": 0.075,
            "completion": 0.30
        },
    }

    # Default pricing for unknown models
    default = {"prompt": 1.0, "completion": 3.0}

    model_pricing = pricing.get(model, default)

    prompt_cost = (usage.get('prompt_tokens', 0) / 1_000_000) * model_pricing['prompt']
    completion_cost = (usage.get('completion_tokens', 0) / 1_000_000) * model_pricing['completion']

    return prompt_cost + completion_cost
```

### テスト

```python
# tests/core/test_decorators_telemetry.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from kagura import agent
from kagura.observability import EventStore, set_global_telemetry, Telemetry

@pytest.fixture
def mock_store():
    """In-memory event store for testing"""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)
    set_global_telemetry(telemetry)
    return store

@pytest.mark.asyncio
@patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock)
async def test_agent_records_telemetry(mock_llm, mock_store):
    """Test that @agent automatically records telemetry"""
    mock_llm.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Hello, World!"))],
        usage=MagicMock(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )
    )

    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        pass

    result = await hello("Alice")

    # Check result
    assert "Hello" in result

    # Check telemetry recorded
    executions = mock_store.get_executions()
    assert len(executions) == 1

    execution = executions[0]
    assert execution['agent_name'] == 'hello'
    assert execution['status'] == 'completed'
    assert execution['kwargs']['name'] == 'Alice'

    # Check LLM call recorded
    assert 'llm_calls' in execution['metrics']
    assert execution['metrics']['llm_calls'] == 1
    assert execution['metrics']['total_tokens'] == 15

    # Check cost calculated
    assert 'total_cost' in execution['metrics']
    assert execution['metrics']['total_cost'] > 0

@pytest.mark.asyncio
async def test_agent_telemetry_disabled(mock_store):
    """Test that telemetry can be disabled"""
    @agent(enable_telemetry=False)
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        pass

    result = await hello("Bob")

    # No telemetry recorded
    executions = mock_store.get_executions()
    assert len(executions) == 0

@pytest.mark.asyncio
@patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock)
async def test_agent_records_tool_calls(mock_llm, mock_store):
    """Test that tool calls are recorded"""
    from kagura import tool

    @tool
    def search(query: str) -> str:
        '''Search for query'''
        return f"Results for {query}"

    mock_llm.return_value = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content="Here are the results",
                tool_calls=[
                    MagicMock(
                        function=MagicMock(
                            name='search',
                            arguments='{"query": "AI"}'
                        )
                    )
                ]
            )
        )],
        usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    )

    @agent(tools=[search])
    async def researcher(topic: str) -> str:
        '''Research {{ topic }}'''
        pass

    result = await researcher("AI")

    # Check tool call recorded
    executions = mock_store.get_executions()
    execution = executions[0]

    events = execution['events']
    tool_events = [e for e in events if e['type'] == 'tool_call']
    assert len(tool_events) >= 1
    assert tool_events[0]['data']['tool_name'] == 'search'

@pytest.mark.asyncio
@patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock)
async def test_agent_records_error(mock_llm, mock_store):
    """Test that errors are recorded"""
    mock_llm.side_effect = Exception("API Error")

    @agent
    async def faulty_agent(query: str) -> str:
        '''Process {{ query }}'''
        pass

    with pytest.raises(Exception):
        await faulty_agent("test")

    # Check error recorded
    executions = mock_store.get_executions()
    assert len(executions) == 1

    execution = executions[0]
    assert execution['status'] == 'failed'
    assert 'API Error' in execution['error']

# 20+ more tests...
```

### 完了条件

- [x] `@agent`デコレータにTelemetry統合
- [x] LLM呼び出し自動記録
- [x] Tool呼び出し自動記録
- [x] エラー自動記録
- [x] コスト計算機能
- [x] 20+ tests全パス
- [x] 既存テスト（900+）全パス
- [x] ドキュメント更新

---

## 📦 Phase 2: DB抽象化 (Week 2)

### 目標

- 複数のDBバックエンド対応（SQLite/PostgreSQL/MongoDB）
- 環境変数で切り替え可能
- 既存コード互換性維持

### 実装内容

#### 2.1 StorageAdapter抽象化

```python
# src/kagura/observability/storage/adapter.py

from abc import ABC, abstractmethod
from typing import Any, Optional

class StorageAdapter(ABC):
    """Abstract storage adapter for telemetry data"""

    @abstractmethod
    async def save_execution(self, execution: dict[str, Any]) -> None:
        """Save execution record"""
        pass

    @abstractmethod
    def get_execution(self, execution_id: str) -> Optional[dict[str, Any]]:
        """Get execution by ID"""
        pass

    @abstractmethod
    def get_executions(
        self,
        agent_name: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query execution records"""
        pass

    @abstractmethod
    def get_summary_stats(
        self, agent_name: Optional[str] = None, since: Optional[float] = None
    ) -> dict[str, Any]:
        """Get summary statistics"""
        pass

    @abstractmethod
    def delete_old_executions(self, older_than: float) -> int:
        """Delete old executions"""
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Clear all records"""
        pass
```

#### 2.2 SQLite実装（既存のEventStoreをリファクタ）

```python
# src/kagura/observability/storage/sqlite_adapter.py

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .adapter import StorageAdapter

class SQLiteAdapter(StorageAdapter):
    """SQLite storage adapter"""

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        if db_path is None:
            db_path = Path.home() / ".kagura" / "telemetry.db"
        elif isinstance(db_path, str) and db_path != ":memory:":
            db_path = Path(db_path)

        self.db_path = db_path
        self._memory_conn: Optional[sqlite3.Connection] = None

        if isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if self.db_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:")

        self._init_db()

    # ... existing EventStore implementation ...
```

#### 2.3 PostgreSQL実装

```python
# src/kagura/observability/storage/postgres_adapter.py

import json
from typing import Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .adapter import StorageAdapter

class PostgreSQLAdapter(StorageAdapter):
    """PostgreSQL storage adapter"""

    def __init__(self, connection_string: str) -> None:
        """Initialize PostgreSQL adapter

        Args:
            connection_string: PostgreSQL connection string
                Example: "postgresql://user:password@localhost:5432/kagura"
        """
        self.connection_string = connection_string
        self._init_db()

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)

    def _init_db(self) -> None:
        """Initialize database schema"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS executions (
                        id TEXT PRIMARY KEY,
                        agent_name TEXT NOT NULL,
                        started_at REAL NOT NULL,
                        ended_at REAL,
                        duration REAL,
                        status TEXT,
                        error TEXT,
                        kwargs JSONB,
                        events JSONB,
                        metrics JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_agent_started
                    ON executions(agent_name, started_at DESC)
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_status
                    ON executions(status)
                """)

                conn.commit()
        finally:
            conn.close()

    async def save_execution(self, execution: dict[str, Any]) -> None:
        """Save execution record"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO executions
                    (id, agent_name, started_at, ended_at, duration,
                     status, error, kwargs, events, metrics)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        execution["id"],
                        execution["agent_name"],
                        execution["started_at"],
                        execution.get("ended_at"),
                        execution.get("duration"),
                        execution.get("status"),
                        execution.get("error"),
                        json.dumps(execution.get("kwargs", {})),
                        json.dumps(execution.get("events", [])),
                        json.dumps(execution.get("metrics", {})),
                    ),
                )
                conn.commit()
        finally:
            conn.close()

    # ... other methods ...
```

#### 2.4 MongoDB実装

```python
# src/kagura/observability/storage/mongo_adapter.py

from typing import Any, Optional
from pymongo import MongoClient, DESCENDING

from .adapter import StorageAdapter

class MongoDBAdapter(StorageAdapter):
    """MongoDB storage adapter"""

    def __init__(self, connection_string: str, database: str = "kagura") -> None:
        """Initialize MongoDB adapter

        Args:
            connection_string: MongoDB connection string
                Example: "mongodb://localhost:27017/"
            database: Database name
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[database]
        self.collection = self.db["executions"]
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database indexes"""
        self.collection.create_index([("agent_name", 1), ("started_at", DESCENDING)])
        self.collection.create_index([("status", 1)])

    async def save_execution(self, execution: dict[str, Any]) -> None:
        """Save execution record"""
        self.collection.insert_one(execution)

    def get_execution(self, execution_id: str) -> Optional[dict[str, Any]]:
        """Get execution by ID"""
        result = self.collection.find_one({"id": execution_id})
        if result:
            result.pop("_id", None)  # Remove MongoDB internal ID
        return result

    # ... other methods ...
```

#### 2.5 ストレージファクトリ

```python
# src/kagura/observability/storage/factory.py

import os
from typing import Optional
from .adapter import StorageAdapter
from .sqlite_adapter import SQLiteAdapter

def create_storage_adapter(
    backend: Optional[str] = None,
    connection_string: Optional[str] = None
) -> StorageAdapter:
    """Create storage adapter from configuration

    Args:
        backend: Backend type ("sqlite", "postgresql", "mongodb")
            If None, read from KAGURA_TELEMETRY_BACKEND env var
        connection_string: Connection string for the backend
            If None, read from KAGURA_TELEMETRY_CONNECTION env var

    Returns:
        StorageAdapter instance

    Example:
        # SQLite (default)
        adapter = create_storage_adapter()

        # PostgreSQL
        adapter = create_storage_adapter(
            backend="postgresql",
            connection_string="postgresql://localhost/kagura"
        )

        # MongoDB
        adapter = create_storage_adapter(
            backend="mongodb",
            connection_string="mongodb://localhost:27017/"
        )

        # From environment variables
        os.environ["KAGURA_TELEMETRY_BACKEND"] = "postgresql"
        os.environ["KAGURA_TELEMETRY_CONNECTION"] = "postgresql://localhost/kagura"
        adapter = create_storage_adapter()
    """
    # Read from environment if not provided
    if backend is None:
        backend = os.environ.get("KAGURA_TELEMETRY_BACKEND", "sqlite")

    if connection_string is None:
        connection_string = os.environ.get("KAGURA_TELEMETRY_CONNECTION")

    backend = backend.lower()

    if backend == "sqlite":
        from .sqlite_adapter import SQLiteAdapter
        return SQLiteAdapter(connection_string)

    elif backend == "postgresql":
        if not connection_string:
            raise ValueError("PostgreSQL requires connection_string")
        from .postgres_adapter import PostgreSQLAdapter
        return PostgreSQLAdapter(connection_string)

    elif backend == "mongodb":
        if not connection_string:
            raise ValueError("MongoDB requires connection_string")
        from .mongo_adapter import MongoDBAdapter
        return MongoDBAdapter(connection_string)

    else:
        raise ValueError(f"Unknown backend: {backend}")
```

#### 2.6 EventStoreのリファクタ

```python
# src/kagura/observability/store.py

from .storage import create_storage_adapter, StorageAdapter

class EventStore:
    """Event store with pluggable storage backend"""

    def __init__(
        self,
        db_path: Optional[Path | str] = None,
        backend: Optional[str] = None,
        connection_string: Optional[str] = None
    ) -> None:
        """Initialize event store

        Args:
            db_path: Path for SQLite (legacy parameter, kept for compatibility)
            backend: Storage backend ("sqlite", "postgresql", "mongodb")
            connection_string: Connection string for backend
        """
        # Legacy support: if db_path is provided, use SQLite
        if db_path is not None:
            from .storage import SQLiteAdapter
            self.adapter = SQLiteAdapter(db_path)
        else:
            self.adapter = create_storage_adapter(backend, connection_string)

    # Delegate all methods to adapter
    async def save_execution(self, execution: dict[str, Any]) -> None:
        return await self.adapter.save_execution(execution)

    def get_execution(self, execution_id: str) -> Optional[dict[str, Any]]:
        return self.adapter.get_execution(execution_id)

    # ... other methods delegate to self.adapter ...
```

### テスト

```python
# tests/observability/storage/test_adapters.py

import pytest
from kagura.observability.storage import (
    create_storage_adapter,
    SQLiteAdapter,
    PostgreSQLAdapter,
    MongoDBAdapter
)

@pytest.mark.parametrize("adapter_class", [
    SQLiteAdapter,
    # PostgreSQLAdapter,  # Requires PostgreSQL server
    # MongoDBAdapter,     # Requires MongoDB server
])
@pytest.mark.asyncio
async def test_adapter_save_and_get(adapter_class):
    """Test save and get operations"""
    adapter = adapter_class(":memory:") if adapter_class == SQLiteAdapter else adapter_class("test_connection")

    execution = {
        "id": "exec_123",
        "agent_name": "test_agent",
        "started_at": 1000.0,
        "ended_at": 1005.0,
        "duration": 5.0,
        "status": "completed",
        "kwargs": {"query": "test"},
        "events": [],
        "metrics": {"llm_calls": 1}
    }

    await adapter.save_execution(execution)

    retrieved = adapter.get_execution("exec_123")
    assert retrieved is not None
    assert retrieved["agent_name"] == "test_agent"
    assert retrieved["status"] == "completed"

def test_factory_sqlite():
    """Test factory creates SQLite adapter"""
    adapter = create_storage_adapter(backend="sqlite")
    assert isinstance(adapter, SQLiteAdapter)

def test_factory_from_env(monkeypatch):
    """Test factory reads from environment"""
    monkeypatch.setenv("KAGURA_TELEMETRY_BACKEND", "sqlite")
    adapter = create_storage_adapter()
    assert isinstance(adapter, SQLiteAdapter)

# 30+ more tests...
```

### 完了条件

- [ ] StorageAdapter抽象化
- [ ] SQLiteAdapter実装（既存コードリファクタ）
- [ ] PostgreSQLAdapter実装
- [ ] MongoDBAdapter実装
- [ ] ストレージファクトリ実装
- [ ] 環境変数サポート
- [ ] 30+ tests全パス
- [ ] ドキュメント更新

---

## 📦 Phase 3: kagura init (Week 3)

### 目標

- `kagura init`コマンドで簡単セットアップ
- `.env`ファイル生成
- DBマイグレーション
- 初回実行時の自動初期化

### 実装内容

#### 3.1 kagura initコマンド

```python
# src/kagura/cli/init.py

import click
from pathlib import Path
import os

@click.command()
@click.option("--backend", type=click.Choice(["sqlite", "postgresql", "mongodb"]), default="sqlite", help="Storage backend")
@click.option("--connection", type=str, default=None, help="Database connection string")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
def init(backend: str, connection: str | None, force: bool) -> None:
    """Initialize Kagura configuration

    Examples:
        # SQLite (default)
        kagura init

        # PostgreSQL
        kagura init --backend postgresql --connection "postgresql://localhost/kagura"

        # MongoDB
        kagura init --backend mongodb --connection "mongodb://localhost:27017/"
    """
    kagura_dir = Path.home() / ".kagura"
    env_file = kagura_dir / ".env"

    # Create directory
    kagura_dir.mkdir(exist_ok=True)
    click.echo(f"✓ Created {kagura_dir}")

    # Check if .env exists
    if env_file.exists() and not force:
        click.echo(f"⚠ Configuration already exists at {env_file}")
        click.echo("  Use --force to overwrite")
        return

    # Create .env file
    env_content = f"""# Kagura AI Configuration
# Auto-generated by: kagura init

# Telemetry Storage Backend
KAGURA_TELEMETRY_BACKEND={backend}
"""

    if connection:
        env_content += f"\n# Database Connection\nKAGURA_TELEMETRY_CONNECTION={connection}\n"

    env_file.write_text(env_content)
    click.echo(f"✓ Created {env_file}")

    # Initialize database
    click.echo(f"\nInitializing {backend} database...")
    try:
        from kagura.observability.storage import create_storage_adapter
        adapter = create_storage_adapter(backend=backend, connection_string=connection)
        click.echo(f"✓ Database initialized")
    except Exception as e:
        click.echo(f"✗ Database initialization failed: {e}", err=True)
        return

    # Success message
    click.echo("\n✓ Kagura initialization complete!")
    click.echo("\nNext steps:")
    click.echo("  1. Set environment variables (optional):")
    click.echo(f"     export KAGURA_TELEMETRY_BACKEND={backend}")
    if connection:
        click.echo(f"     export KAGURA_TELEMETRY_CONNECTION={connection}")
    click.echo("  2. Run your agent:")
    click.echo("     python your_agent.py")
    click.echo("  3. Monitor telemetry:")
    click.echo("     kagura monitor")
```

#### 3.2 自動初期化

```python
# src/kagura/observability/instrumentation.py

def get_global_telemetry() -> Telemetry:
    """Get or create global telemetry instance

    Automatically initializes on first access
    """
    global _global_telemetry
    if _global_telemetry is None:
        # Check if initialized
        kagura_dir = Path.home() / ".kagura"
        if not kagura_dir.exists():
            # Auto-initialize with SQLite
            kagura_dir.mkdir(exist_ok=True)
            click.echo("ℹ Initializing Kagura (first run)...")
            click.echo(f"  Run 'kagura init' for advanced configuration")

        _global_telemetry = Telemetry()
    return _global_telemetry
```

### テスト

```python
# tests/cli/test_init.py

import pytest
from click.testing import CliRunner
from kagura.cli.init import init
from pathlib import Path

def test_init_sqlite(tmp_path, monkeypatch):
    """Test kagura init with SQLite"""
    monkeypatch.setenv("HOME", str(tmp_path))
    runner = CliRunner()

    result = runner.invoke(init, [])

    assert result.exit_code == 0
    assert "✓ Created" in result.output
    assert "✓ Database initialized" in result.output

    # Check .env created
    env_file = tmp_path / ".kagura" / ".env"
    assert env_file.exists()
    assert "KAGURA_TELEMETRY_BACKEND=sqlite" in env_file.read_text()

def test_init_postgresql(tmp_path, monkeypatch):
    """Test kagura init with PostgreSQL"""
    monkeypatch.setenv("HOME", str(tmp_path))
    runner = CliRunner()

    result = runner.invoke(init, [
        "--backend", "postgresql",
        "--connection", "postgresql://localhost/test"
    ])

    assert result.exit_code == 0

    env_file = tmp_path / ".kagura" / ".env"
    content = env_file.read_text()
    assert "KAGURA_TELEMETRY_BACKEND=postgresql" in content
    assert "KAGURA_TELEMETRY_CONNECTION=postgresql://localhost/test" in content

def test_init_force_overwrite(tmp_path, monkeypatch):
    """Test --force flag"""
    monkeypatch.setenv("HOME", str(tmp_path))
    kagura_dir = tmp_path / ".kagura"
    kagura_dir.mkdir()
    env_file = kagura_dir / ".env"
    env_file.write_text("OLD CONTENT")

    runner = CliRunner()

    # Without --force
    result = runner.invoke(init, [])
    assert "already exists" in result.output

    # With --force
    result = runner.invoke(init, ["--force"])
    assert result.exit_code == 0
    assert "KAGURA_TELEMETRY_BACKEND=sqlite" in env_file.read_text()

# 15+ more tests...
```

### 完了条件

- [ ] `kagura init`コマンド実装
- [ ] `.env`ファイル生成
- [ ] 自動初期化機能
- [ ] 15+ tests全パス
- [ ] ドキュメント更新

---

## 📦 Phase 4: Dashboard拡張 (Week 4)

### 目標

- リアルタイムコスト分析
- エージェント比較機能
- エクスポート機能（CSV/JSON）

### 実装内容

#### 4.1 コスト分析機能

```python
# src/kagura/cli/monitor.py (既存ファイルを拡張)

@monitor.command()
@click.option("--agent", "-a", help="Filter by agent name", type=str, default=None)
@click.option("--since", "-s", help="Since timestamp", type=float, default=None)
@click.option("--db", help="Path to telemetry database", type=click.Path(), default=None)
def cost_analysis(agent: str | None, since: float | None, db: str | None) -> None:
    """Show detailed cost analysis

    Examples:
        kagura monitor cost-analysis                    # Overall cost
        kagura monitor cost-analysis --agent my_agent   # Agent-specific
        kagura monitor cost-analysis --since 1696953600 # Since timestamp
    """
    db_path = Path(db) if db else None
    store = EventStore(db_path)

    executions = store.get_executions(agent_name=agent, since=since)

    # Calculate costs by model
    costs_by_model: dict[str, float] = {}
    total_cost = 0.0

    for exec in executions:
        for event in exec.get('events', []):
            if event['type'] == 'llm_call':
                model = event['data'].get('model', 'unknown')
                cost = event['data'].get('cost', 0.0)
                costs_by_model[model] = costs_by_model.get(model, 0.0) + cost
                total_cost += cost

    # Display
    from rich.console import Console
    from rich.table import Table

    console = Console()

    table = Table(title="Cost Analysis")
    table.add_column("Model", style="cyan")
    table.add_column("Calls", justify="right", style="green")
    table.add_column("Cost", justify="right", style="yellow")

    for model, cost in sorted(costs_by_model.items(), key=lambda x: x[1], reverse=True):
        # Count calls for this model
        calls = sum(1 for e in executions for ev in e.get('events', [])
                   if ev['type'] == 'llm_call' and ev['data'].get('model') == model)
        table.add_row(model, str(calls), f"${cost:.4f}")

    table.add_row("TOTAL", "", f"${total_cost:.4f}", style="bold")

    console.print(table)
```

#### 4.2 エクスポート機能

```python
# src/kagura/cli/monitor.py (既存ファイルを拡張)

@monitor.command()
@click.option("--agent", "-a", help="Filter by agent name", type=str, default=None)
@click.option("--since", "-s", help="Since timestamp", type=float, default=None)
@click.option("--format", "-f", type=click.Choice(["csv", "json"]), default="csv", help="Export format")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file")
@click.option("--db", help="Path to telemetry database", type=click.Path(), default=None)
def export(agent: str | None, since: float | None, format: str, output: str, db: str | None) -> None:
    """Export telemetry data

    Examples:
        kagura monitor export --output data.csv
        kagura monitor export --format json --output data.json
        kagura monitor export --agent my_agent --output agent_data.csv
    """
    import csv
    import json
    from pathlib import Path

    db_path = Path(db) if db else None
    store = EventStore(db_path)

    executions = store.get_executions(agent_name=agent, since=since, limit=10000)

    output_path = Path(output)

    if format == "csv":
        with output_path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'agent_name', 'started_at', 'duration', 'status',
                'llm_calls', 'total_tokens', 'total_cost'
            ])
            writer.writeheader()

            for exec in executions:
                writer.writerow({
                    'id': exec['id'],
                    'agent_name': exec['agent_name'],
                    'started_at': exec['started_at'],
                    'duration': exec.get('duration', 0.0),
                    'status': exec.get('status', 'unknown'),
                    'llm_calls': exec.get('metrics', {}).get('llm_calls', 0),
                    'total_tokens': exec.get('metrics', {}).get('total_tokens', 0),
                    'total_cost': exec.get('metrics', {}).get('total_cost', 0.0),
                })

        click.echo(f"✓ Exported {len(executions)} executions to {output_path}")

    elif format == "json":
        with output_path.open('w') as f:
            json.dump(executions, f, indent=2)

        click.echo(f"✓ Exported {len(executions)} executions to {output_path}")
```

### テスト

```python
# tests/cli/test_monitor_extensions.py

import pytest
from click.testing import CliRunner
from kagura.cli.monitor import cost_analysis, export
from kagura.observability import EventStore

@pytest.fixture
def populated_store():
    """Create store with test data"""
    store = EventStore(":memory:")

    # Add test executions
    # ... add test data ...

    return store

def test_cost_analysis(populated_store, monkeypatch):
    """Test cost analysis command"""
    # Mock store
    monkeypatch.setattr("kagura.cli.monitor.EventStore", lambda x: populated_store)

    runner = CliRunner()
    result = runner.invoke(cost_analysis, [])

    assert result.exit_code == 0
    assert "Cost Analysis" in result.output
    assert "$" in result.output  # Cost displayed

def test_export_csv(populated_store, monkeypatch, tmp_path):
    """Test CSV export"""
    import csv

    monkeypatch.setattr("kagura.cli.monitor.EventStore", lambda x: populated_store)

    output_file = tmp_path / "export.csv"
    runner = CliRunner()
    result = runner.invoke(export, ["--format", "csv", "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()

    # Verify CSV content
    with output_file.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0
        assert 'agent_name' in rows[0]

# 20+ more tests...
```

### 完了条件

- [ ] コスト分析機能
- [ ] エクスポート機能（CSV/JSON）
- [ ] エージェント比較機能
- [ ] 20+ tests全パス
- [ ] ドキュメント更新

---

## 📦 Phase 5: Advanced Observability（オプション、RFC-010統合） (Future)

### 目標

RFC-010の高度な機能を実装

### 実装内容

#### 5.1 Webダッシュボード

```python
# src/kagura/observability/web_dashboard.py

import streamlit as st
from kagura.observability import EventStore

def create_dashboard():
    """Create Streamlit dashboard"""
    st.title("Kagura AI Observability Dashboard")

    store = EventStore()

    # Real-time metrics
    st.header("Real-time Metrics")
    stats = store.get_summary_stats()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Executions", stats["total_executions"])
    col2.metric("Success Rate", f"{stats['completed'] / stats['total_executions'] * 100:.1f}%")
    col3.metric("Avg Duration", f"{stats['avg_duration']:.2f}s")

    # Cost graph
    st.header("Cost Over Time")
    executions = store.get_executions(limit=100)

    # Plot cost
    import pandas as pd
    df = pd.DataFrame([
        {
            "timestamp": e["started_at"],
            "cost": e.get("metrics", {}).get("total_cost", 0.0),
            "agent": e["agent_name"]
        }
        for e in executions
    ])

    st.line_chart(df, x="timestamp", y="cost")

    # Agent comparison
    st.header("Agent Comparison")
    # ...
```

**起動**:
```bash
$ kagura dashboard --web
# Opens http://localhost:8501
```

#### 5.2 Prometheus統合

```python
# src/kagura/observability/prometheus_exporter.py

from prometheus_client import Counter, Histogram, start_http_server

# Metrics
agent_executions = Counter('kagura_agent_executions_total', 'Total executions', ['agent_name', 'status'])
agent_latency = Histogram('kagura_agent_latency_seconds', 'Latency', ['agent_name'])
agent_cost = Counter('kagura_agent_cost_usd', 'Cost in USD', ['agent_name', 'model'])

def export_metrics():
    """Export metrics to Prometheus"""
    from kagura.observability import EventStore

    store = EventStore()
    executions = store.get_executions(limit=1000)

    for e in executions:
        agent_executions.labels(
            agent_name=e["agent_name"],
            status=e.get("status", "unknown")
        ).inc()

        if e.get("duration"):
            agent_latency.labels(agent_name=e["agent_name"]).observe(e["duration"])

        if e.get("metrics", {}).get("total_cost"):
            cost = e["metrics"]["total_cost"]
            model = e.get("metrics", {}).get("model", "unknown")
            agent_cost.labels(agent_name=e["agent_name"], model=model).inc(cost)

    # Start HTTP server
    start_http_server(9090)
```

**起動**:
```bash
$ kagura dashboard --prometheus
# Metrics at http://localhost:9090/metrics
```

#### 5.3 アラート機能

```python
# src/kagura/observability/alerts.py

from dataclasses import dataclass
from typing import Callable

@dataclass
class Alert:
    name: str
    condition: Callable[[dict], bool]
    action: Callable[[dict], None]

class AlertManager:
    """Manage alerts for agent executions"""

    def __init__(self):
        self.alerts: list[Alert] = []

    def add_alert(self, alert: Alert):
        """Add alert"""
        self.alerts.append(alert)

    def check_alerts(self, execution: dict):
        """Check all alerts for execution"""
        for alert in self.alerts:
            if alert.condition(execution):
                alert.action(execution)

# Example usage
manager = AlertManager()

# Cost alert
manager.add_alert(Alert(
    name="high_cost",
    condition=lambda e: e.get("metrics", {}).get("total_cost", 0.0) > 1.0,
    action=lambda e: print(f"⚠️ High cost: ${e['metrics']['total_cost']:.2f}")
))

# Error alert
manager.add_alert(Alert(
    name="error",
    condition=lambda e: e.get("status") == "failed",
    action=lambda e: print(f"❌ Error: {e.get('error', 'Unknown')}")
))
```

### テスト

```python
# tests/observability/test_web_dashboard.py

def test_dashboard_loads():
    """Test dashboard loads without errors"""
    # Mock Streamlit
    # ...

# tests/observability/test_prometheus.py

def test_prometheus_metrics():
    """Test Prometheus metrics export"""
    # ...

# tests/observability/test_alerts.py

def test_alert_triggers():
    """Test alert triggers on condition"""
    # ...
```

### 完了条件

- [ ] Webダッシュボード（Streamlit）
- [ ] Prometheus統合
- [ ] Grafana連携ガイド
- [ ] アラート機能
- [ ] 15+ tests全パス
- [ ] ドキュメント完成

---

## 📊 成功指標

### 全体完了時

1. **自動記録**
   - ✅ `@agent`デコレータで自動telemetry記録
   - ✅ 100% のLLM呼び出し、tool呼び出しを記録
   - ✅ ユーザーコード変更不要

2. **データ可視化**
   - ✅ `kagura monitor`でリアルタイムダッシュボード
   - ✅ コスト分析、パフォーマンス分析
   - ✅ エラートレース機能

3. **柔軟性**
   - ✅ SQLite/PostgreSQL/MongoDB対応
   - ✅ 環境変数で切り替え可能
   - ✅ カスタムストレージ実装可能

4. **UX向上**
   - ✅ `kagura init`で簡単セットアップ
   - ✅ 初回実行時の自動初期化
   - ✅ エクスポート機能（CSV/JSON）

5. **テスト**
   - ✅ 100+ 新規テスト全パス
   - ✅ 既存テスト（900+）全パス
   - ✅ Pyright 0 errors
   - ✅ Ruff linting全パス

---

## 📝 ドキュメント

### ユーザーガイド

```markdown
# docs/en/guides/telemetry.md

## Telemetry & Observability

Kagura AI automatically records telemetry data for all agent executions.

### Quick Start

```python
from kagura import agent

# Telemetry is enabled by default
@agent
async def my_agent(query: str) -> str:
    '''Process {{ query }}'''
    pass

# Monitor telemetry
# $ kagura monitor
```

### Setup

Initialize Kagura configuration:

```bash
# SQLite (default)
kagura init

# PostgreSQL
kagura init --backend postgresql --connection "postgresql://localhost/kagura"

# MongoDB
kagura init --backend mongodb --connection "mongodb://localhost:27017/"
```

### Monitoring

```bash
# Live dashboard
kagura monitor

# List recent executions
kagura monitor list

# Show statistics
kagura monitor stats

# Cost analysis
kagura monitor cost-analysis

# Export data
kagura monitor export --output data.csv
```

### Disable Telemetry

```python
@agent(enable_telemetry=False)
async def my_agent(query: str) -> str:
    '''Process {{ query }}'''
    pass
```
```

---

## 🚀 実装順序

### Week 1: @agent統合
- Day 1-2: デコレータ拡張、LLMメタデータ追加
- Day 3: コスト計算機能
- Day 4-5: テスト（20+ tests）
- Day 6-7: ドキュメント、PR作成

### Week 2: DB抽象化
- Day 1-2: StorageAdapter抽象化、SQLiteリファクタ
- Day 3: PostgreSQL実装
- Day 4: MongoDB実装
- Day 5: ストレージファクトリ
- Day 6-7: テスト（30+ tests）、PR作成

### Week 3: kagura init
- Day 1-2: initコマンド実装
- Day 3: 自動初期化
- Day 4-5: テスト（15+ tests）
- Day 6-7: ドキュメント、PR作成

### Week 4: Dashboard拡張
- Day 1-2: コスト分析機能
- Day 3: エクスポート機能
- Day 4-5: テスト（20+ tests）
- Day 6-7: 最終ドキュメント、PR作成

---

## 📋 チェックリスト

### Phase 1 完了条件
- [ ] `@agent`デコレータにTelemetry統合
- [ ] LLM呼び出し自動記録
- [ ] Tool呼び出し自動記録
- [ ] コスト計算機能
- [ ] 20+ tests全パス
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

### Phase 2 完了条件
- [ ] StorageAdapter抽象化
- [ ] SQLite/PostgreSQL/MongoDB実装
- [ ] ストレージファクトリ
- [ ] 環境変数サポート
- [ ] 30+ tests全パス
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

### Phase 3 完了条件
- [ ] `kagura init`コマンド実装
- [ ] `.env`ファイル生成
- [ ] 自動初期化機能
- [ ] 15+ tests全パス
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

### Phase 4 完了条件
- [ ] コスト分析機能
- [ ] エクスポート機能
- [ ] 20+ tests全パス
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

---

## 🎓 参考資料

### Observability Best Practices
- [OpenTelemetry](https://opentelemetry.io/)
- [Distributed Tracing](https://www.jaegertracing.io/)
- [Metrics & Logging](https://prometheus.io/)

### Database Adapters
- [SQLite](https://www.sqlite.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [MongoDB](https://www.mongodb.com/)

---

**このRFCにより、Kagura AIは完全なObservability機能を持つProduction-readyフレームワークになります！**
