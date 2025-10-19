# RFC-018: Memory Management System - エージェント記憶システム

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-09
- **関連Issue**: #85
- **優先度**: High

## 概要

Kagura AIエージェントに高度なメモリー管理システムを導入し、長期記憶、作業記憶、コンテキスト管理を統合します。

### 目標
- **Persistent Memory**: 永続化された長期記憶（DB/ファイル）
- **Working Memory**: エージェント実行中の一時記憶
- **Context Memory**: 会話履歴・セッション管理
- **Memory RAG**: ベクトルDB検索による記憶検索
- **MCP Memory統合**: MCPプロトコルでの記憶共有

### 非目標
- ユーザー個人情報の自動収集（プライバシー違反）
- 無制限なメモリー保存（ストレージコスト）

## モチベーション

### 現在の課題
1. エージェントは実行ごとに記憶をリセット
2. 過去の実行結果を活用できない
3. コンテキストウィンドウに制約がある
4. エージェント間で情報共有できない

### 解決するユースケース
- **学習するエージェント**: 過去の実行から学習し、パフォーマンス向上
- **パーソナルアシスタント**: ユーザーの好み、習慣を記憶
- **長期プロジェクト**: 数週間〜数ヶ月の進捗を追跡
- **チームコラボレーション**: 複数エージェントでの情報共有
- **コンテキスト拡張**: 大規模ドキュメントのRAG検索

### なぜ今実装すべきか
- RFC-003（Personal Assistant）の基盤技術
- RFC-007（MCP Integration）での記憶共有に必要
- v2.0.0のコア機能完成後の自然な拡張

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         Agent Execution Layer               │
│                                             │
│  @agent                                     │
│  async def my_agent(query: str):            │
│      memory = agent.memory                  │
│      context = memory.recall(query)         │
│      ...                                    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│       Memory Management Layer               │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  MemoryManager                      │   │
│  │  - Store                            │   │
│  │  - Recall                           │   │
│  │  - Update                           │   │
│  │  - Forget (pruning)                 │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│  ┌──────────────┴──────────────────────┐   │
│  │                                      │   │
│  ▼                                      ▼   │
│  ┌────────────────┐  ┌────────────────┐   │
│  │ Working Memory │  │Persistent Memory│   │
│  │ (Runtime)      │  │ (Storage)      │   │
│  │ - Session      │  │ - SQLite       │   │
│  │ - Context      │  │ - JSON         │   │
│  │ - Temporary    │  │ - Vector DB    │   │
│  └────────────────┘  └────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Memory RAG                         │   │
│  │  - Embedding generation             │   │
│  │  - Vector search                    │   │
│  │  - Semantic recall                  │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│       Storage Backend                       │
│  - SQLite (structured data)                 │
│  - ChromaDB/Qdrant (vector embeddings)      │
│  - File system (JSON/YAML)                  │
└─────────────────────────────────────────────┘
```

### メモリータイプ

#### 1. Working Memory（作業記憶）

実行中の一時記憶。エージェント実行終了時に破棄。

```python
# src/kagura/core/memory/working.py
from typing import Any, Dict
from datetime import datetime

class WorkingMemory:
    """Temporary memory during agent execution"""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._access_log: Dict[str, datetime] = {}

    def set(self, key: str, value: Any):
        """Store temporary data"""
        self._data[key] = value
        self._access_log[key] = datetime.now()

    def get(self, key: str) -> Any:
        """Retrieve temporary data"""
        self._access_log[key] = datetime.now()
        return self._data.get(key)

    def clear(self):
        """Clear all temporary data"""
        self._data.clear()
        self._access_log.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export for persistence"""
        return {
            "data": self._data.copy(),
            "access_log": {
                k: v.isoformat()
                for k, v in self._access_log.items()
            }
        }
```

#### 2. Context Memory（コンテキスト記憶）

会話履歴、セッション情報。

```python
# src/kagura/core/memory/context.py
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime
    metadata: Optional[dict] = None

class ContextMemory:
    """Conversation history and session context"""

    def __init__(self, max_messages: int = 100):
        self._messages: List[Message] = []
        self._max_messages = max_messages
        self._session_id: Optional[str] = None

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ):
        """Add message to context"""
        msg = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self._messages.append(msg)

        # Prune old messages
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages:]

    def get_messages(
        self,
        last_n: Optional[int] = None,
        role: Optional[str] = None
    ) -> List[Message]:
        """Retrieve messages"""
        messages = self._messages

        if role:
            messages = [m for m in messages if m.role == role]

        if last_n:
            messages = messages[-last_n:]

        return messages

    def clear(self):
        """Clear context"""
        self._messages.clear()

    def to_llm_format(self) -> List[dict]:
        """Convert to LLM API format"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self._messages
        ]
```

#### 3. Persistent Memory（永続記憶）

長期記憶。DB/ファイルに保存。

```python
# src/kagura/core/memory/persistent.py
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import sqlite3
from datetime import datetime

class PersistentMemory:
    """Long-term persistent memory"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".kagura" / "memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    agent_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_key ON memories(key)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent ON memories(agent_name)
            """)

    def store(
        self,
        key: str,
        value: Any,
        agent_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Store persistent memory"""
        value_json = json.dumps(value)
        metadata_json = json.dumps(metadata) if metadata else None

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memories
                (key, value, agent_name, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (key, value_json, agent_name, datetime.now(), metadata_json))

    def recall(
        self,
        key: str,
        agent_name: Optional[str] = None
    ) -> Optional[Any]:
        """Retrieve persistent memory"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT value FROM memories
                WHERE key = ? AND (agent_name = ? OR agent_name IS NULL)
                ORDER BY updated_at DESC
                LIMIT 1
            """, (key, agent_name))

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])

        return None

    def search(
        self,
        query: str,
        agent_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by key pattern"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT key, value, created_at, metadata
                FROM memories
                WHERE key LIKE ? AND (agent_name = ? OR agent_name IS NULL)
                ORDER BY updated_at DESC
                LIMIT ?
            """, (f"%{query}%", agent_name, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "key": row[0],
                    "value": json.loads(row[1]),
                    "created_at": row[2],
                    "metadata": json.loads(row[3]) if row[3] else None
                })

            return results

    def forget(self, key: str, agent_name: Optional[str] = None):
        """Delete memory"""
        with sqlite3.connect(self.db_path) as conn:
            if agent_name:
                conn.execute(
                    "DELETE FROM memories WHERE key = ? AND agent_name = ?",
                    (key, agent_name)
                )
            else:
                conn.execute("DELETE FROM memories WHERE key = ?", (key,))

    def prune(self, older_than_days: int = 90):
        """Remove old memories"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM memories
                WHERE updated_at < datetime('now', '-' || ? || ' days')
            """, (older_than_days,))
```

#### 4. Memory RAG（記憶検索）

ベクトルDBを使った意味検索。

```python
# src/kagura/core/memory/rag.py
from typing import List, Dict, Any, Optional
import hashlib
from pathlib import Path

# ChromaDB (lightweight, local vector DB)
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

class MemoryRAG:
    """Vector-based semantic memory search"""

    def __init__(
        self,
        collection_name: str = "kagura_memory",
        persist_dir: Optional[Path] = None
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")

        persist_dir = persist_dir or Path.home() / ".kagura" / "vector_db"
        persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.Client(Settings(
            persist_directory=str(persist_dir),
            anonymized_telemetry=False
        ))

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None
    ):
        """Store memory with embedding"""
        # Generate unique ID
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        full_metadata = metadata or {}
        if agent_name:
            full_metadata["agent_name"] = agent_name

        self.collection.add(
            ids=[content_hash],
            documents=[content],
            metadatas=[full_metadata] if full_metadata else None
        )

    def recall(
        self,
        query: str,
        top_k: int = 5,
        agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search for memories"""
        where = {"agent_name": agent_name} if agent_name else None

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where
        )

        memories = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "content": doc,
                    "distance": results["distances"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else None
                })

        return memories

    def delete_all(self, agent_name: Optional[str] = None):
        """Delete all memories"""
        if agent_name:
            # Delete by agent
            # ChromaDB doesn't support delete by metadata directly
            # We need to query and delete
            results = self.collection.get(where={"agent_name": agent_name})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
        else:
            # Delete entire collection
            self.client.delete_collection(self.collection.name)
```

### 統合Memory Manager

```python
# src/kagura/core/memory/manager.py
from typing import Any, Dict, List, Optional
from pathlib import Path

from .working import WorkingMemory
from .context import ContextMemory, Message
from .persistent import PersistentMemory
from .rag import MemoryRAG

class MemoryManager:
    """Unified memory management interface"""

    def __init__(
        self,
        agent_name: Optional[str] = None,
        enable_rag: bool = False,
        persist_dir: Optional[Path] = None
    ):
        self.agent_name = agent_name

        # Initialize memory types
        self.working = WorkingMemory()
        self.context = ContextMemory()
        self.persistent = PersistentMemory(
            db_path=persist_dir / "memory.db" if persist_dir else None
        )

        # Optional: RAG
        self.rag: Optional[MemoryRAG] = None
        if enable_rag:
            self.rag = MemoryRAG(
                collection_name=f"kagura_{agent_name}" if agent_name else "kagura_memory",
                persist_dir=persist_dir / "vector_db" if persist_dir else None
            )

    # Working Memory
    def set_temp(self, key: str, value: Any):
        """Store temporary data"""
        self.working.set(key, value)

    def get_temp(self, key: str) -> Any:
        """Get temporary data"""
        return self.working.get(key)

    # Context Memory
    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        """Add message to context"""
        self.context.add_message(role, content, metadata)

    def get_context(self, last_n: Optional[int] = None) -> List[Message]:
        """Get conversation context"""
        return self.context.get_messages(last_n=last_n)

    def get_llm_context(self) -> List[dict]:
        """Get context in LLM API format"""
        return self.context.to_llm_format()

    # Persistent Memory
    def remember(self, key: str, value: Any, metadata: Optional[dict] = None):
        """Store persistent memory"""
        self.persistent.store(key, value, self.agent_name, metadata)

    def recall(self, key: str) -> Optional[Any]:
        """Recall persistent memory"""
        return self.persistent.recall(key, self.agent_name)

    def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search persistent memory"""
        return self.persistent.search(query, self.agent_name, limit)

    def forget(self, key: str):
        """Delete memory"""
        self.persistent.forget(key, self.agent_name)

    # RAG Memory
    def store_semantic(self, content: str, metadata: Optional[dict] = None):
        """Store content for semantic search"""
        if not self.rag:
            raise ValueError("RAG not enabled. Set enable_rag=True")
        self.rag.store(content, metadata, self.agent_name)

    def recall_semantic(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Semantic search for relevant memories"""
        if not self.rag:
            raise ValueError("RAG not enabled. Set enable_rag=True")
        return self.rag.recall(query, top_k, self.agent_name)

    # Session Management
    def save_session(self, session_name: str):
        """Save current session"""
        session_data = {
            "working": self.working.to_dict(),
            "context": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.context.get_messages()
            ]
        }
        self.persistent.store(
            key=f"session:{session_name}",
            value=session_data,
            agent_name=self.agent_name,
            metadata={"type": "session"}
        )

    def load_session(self, session_name: str) -> bool:
        """Load saved session"""
        session_data = self.persistent.recall(
            key=f"session:{session_name}",
            agent_name=self.agent_name
        )

        if not session_data:
            return False

        # Restore context
        self.context.clear()
        for msg_data in session_data.get("context", []):
            self.context.add_message(
                role=msg_data["role"],
                content=msg_data["content"]
            )

        return True

    def clear_all(self):
        """Clear all memory"""
        self.working.clear()
        self.context.clear()
```

### Agent統合

```python
# src/kagura/core/decorators.py (追加)
from kagura.core.memory import MemoryManager

def agent(
    model: str = "gpt-4o-mini",
    enable_memory: bool = False,
    enable_rag: bool = False
):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Memory manager
            if enable_memory:
                memory = MemoryManager(
                    agent_name=func.__name__,
                    enable_rag=enable_rag
                )

                # Inject memory into agent
                kwargs["memory"] = memory

            result = await func(*args, **kwargs)
            return result

        return wrapper
    return decorator
```

### API設計

#### 基本的な使い方

```python
from kagura import agent
from kagura.core.memory import MemoryManager

@agent(model="gpt-4o-mini", enable_memory=True)
async def personal_assistant(query: str, memory: MemoryManager) -> str:
    """
    Personal assistant with memory.

    Args:
        query: User query
        memory: Injected memory manager
    """
    # Add to context
    memory.add_message("user", query)

    # Recall past preferences
    favorite_color = memory.recall("favorite_color")
    if not favorite_color:
        favorite_color = "unknown"

    # Remember new information
    if "my favorite color is" in query.lower():
        color = query.split("my favorite color is")[1].strip()
        memory.remember("favorite_color", color)

    response = f"Your favorite color is {favorite_color}. How can I help?"
    memory.add_message("assistant", response)

    return response
```

#### RAG検索

```python
from kagura import agent
from kagura.core.memory import MemoryManager

@agent(model="gpt-4o-mini", enable_memory=True, enable_rag=True)
async def document_qa(question: str, memory: MemoryManager) -> str:
    """
    Answer questions using stored documents.
    """
    # Semantic search for relevant context
    relevant_docs = memory.recall_semantic(question, top_k=3)

    context = "\n\n".join([doc["content"] for doc in relevant_docs])

    prompt = f"""
    Answer the question based on the following context:

    Context:
    {context}

    Question: {question}
    """

    return prompt  # LLM will process this
```

#### セッション管理

```python
from kagura import agent
from kagura.core.memory import MemoryManager

@agent(model="gpt-4o-mini", enable_memory=True)
async def chat_with_session(
    query: str,
    session_name: str,
    memory: MemoryManager
) -> str:
    """Chat with persistent sessions"""
    # Load previous session
    memory.load_session(session_name)

    # Process query
    memory.add_message("user", query)
    response = f"Processing: {query}"
    memory.add_message("assistant", response)

    # Save session
    memory.save_session(session_name)

    return response
```

## 実装計画

### Phase 1: Core Memory Types (v2.1.0)
- [ ] WorkingMemory実装
- [ ] ContextMemory実装
- [ ] PersistentMemory実装（SQLite）
- [ ] MemoryManager統合

### Phase 2: RAG Integration (v2.2.0)
- [ ] ChromaDB統合
- [ ] MemoryRAG実装
- [ ] Embedding生成
- [ ] セマンティック検索

### Phase 3: Agent Integration (v2.2.0)
- [ ] @agent decorator拡張（enable_memory）
- [ ] Memoryインジェクション
- [ ] セッション管理
- [ ] ドキュメント・サンプル

### Phase 4: MCP Memory (v2.3.0)
- [ ] MCP Memory Protocol実装
- [ ] Claude Codeとの記憶共有
- [ ] Multi-agent memory sharing

### Phase 5: Advanced Features (v2.4.0)
- [ ] Auto-pruning（古い記憶の削除）
- [ ] Memory analytics（記憶使用状況）
- [ ] Export/Import
- [ ] Backup/Restore

## 技術的詳細

### 依存関係

```toml
[project.dependencies]
# SQLiteは標準ライブラリ

[project.optional-dependencies]
memory = [
    "chromadb>=0.4.0",          # Vector DB
    "sentence-transformers>=2.0.0",  # Embeddings (optional)
]
```

### 設定ファイル

`~/.kagura/memory.toml`:

```toml
[memory]
# Enable persistent memory
enabled = true

# Storage directory
storage_dir = "~/.kagura/memory"

# Enable RAG
enable_rag = true

# Context window
max_context_messages = 100

# Auto-pruning
auto_prune = true
prune_older_than_days = 90

[memory.rag]
# Embedding model
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

# Vector DB backend
backend = "chromadb"  # or "qdrant"

# Top K results
default_top_k = 5
```

## テスト戦略

```python
# tests/core/test_memory.py
import pytest
from kagura.core.memory import MemoryManager

@pytest.mark.asyncio
async def test_working_memory():
    memory = MemoryManager()
    memory.set_temp("key", "value")
    assert memory.get_temp("key") == "value"

@pytest.mark.asyncio
async def test_persistent_memory(tmp_path):
    memory = MemoryManager(persist_dir=tmp_path)
    memory.remember("name", "Alice")

    # New instance should recall
    memory2 = MemoryManager(persist_dir=tmp_path)
    assert memory2.recall("name") == "Alice"

@pytest.mark.asyncio
async def test_rag_memory(tmp_path):
    memory = MemoryManager(enable_rag=True, persist_dir=tmp_path)
    memory.store_semantic("Python is a programming language")

    results = memory.recall_semantic("What is Python?", top_k=1)
    assert len(results) > 0
    assert "Python" in results[0]["content"]
```

## セキュリティ考慮事項

1. **データ暗号化**
   - 機密情報の暗号化保存
   - Fernet対称暗号化

2. **アクセス制御**
   - Agent名ベースの分離
   - ユーザー認証（将来）

3. **プライバシー**
   - 個人情報の自動収集禁止
   - GDPR対応（削除権）

## 参考資料

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [MCP Memory Protocol](https://spec.modelcontextprotocol.io/)

## 改訂履歴

- 2025-10-09: 初版作成
