# GraphMemory Backend Architecture

Issue #554 - Cloud-Native Infrastructure Migration (PostgreSQL + Redis + Qdrant)

## 概要

GraphMemoryのストレージバックエンドを抽象化し、JSON File / PostgreSQLを選択可能にします。

---

## アーキテクチャ

### Backend Abstraction Layer

```
GraphMemory (公開API)
    ↓
GraphBackend (抽象インターフェース)
    ↓
    ├── JSONBackend (デフォルト、ローカルファイル)
    └── PostgresBackend (本番環境、Cloud SQL)
```

### ファイル構成

```
src/kagura/core/graph/
├── memory.py              # GraphMemory (公開API、Facade)
├── backends/
│   ├── __init__.py        # Backend抽象化レイヤー
│   ├── base.py            # GraphBackend (ABC)
│   ├── json_backend.py    # JSON File backend
│   └── postgres_backend.py # PostgreSQL backend
```

---

## Backend Interface (ABC)

```python
# backends/base.py
from abc import ABC, abstractmethod
import networkx as nx

class GraphBackend(ABC):
    \"\"\"Abstract base class for GraphMemory storage backends.\"\"\"

    @abstractmethod
    def save(self, graph: nx.DiGraph) -> None:
        \"\"\"Save graph to backend.\"\"\"
        pass

    @abstractmethod
    def load(self) -> nx.DiGraph:
        \"\"\"Load graph from backend.\"\"\"
        pass

    @abstractmethod
    def exists(self) -> bool:
        \"\"\"Check if graph exists in backend.\"\"\"
        pass

    @abstractmethod
    def delete(self) -> None:
        \"\"\"Delete graph from backend.\"\"\"
        pass
```

---

## JSON Backend (現在の実装)

### 実装

```python
# backends/json_backend.py
from pathlib import Path
import json
import networkx as nx
from .base import GraphBackend

class JSONBackend(GraphBackend):
    \"\"\"JSON file-based backend (デフォルト).\"\"\"

    def __init__(self, persist_path: Path):
        self.persist_path = persist_path

    def save(self, graph: nx.DiGraph) -> None:
        \"\"\"Save graph to JSON file.\"\"\"
        data = nx.node_link_data(graph, edges="links")
        with open(self.persist_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> nx.DiGraph:
        \"\"\"Load graph from JSON file.\"\"\"
        with open(self.persist_path) as f:
            data = json.load(f)
        return nx.node_link_graph(data, edges="links")

    def exists(self) -> bool:
        return self.persist_path.exists()

    def delete(self) -> None:
        if self.exists():
            self.persist_path.unlink()
```

---

## PostgreSQL Backend (新規実装)

### データモデル

#### Option 1: Single JSONB Column (シンプル)

```sql
CREATE TABLE graph_memory (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    graph_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_graph_memory_user ON graph_memory(user_id);
```

**メリット**:
- シンプルな実装
- NetworkXのJSON形式をそのまま保存
- 移行が容易

**デメリット**:
- 大規模グラフでパフォーマンス問題
- ノード/エッジ単位のクエリが困難

#### Option 2: Normalized Tables (拡張性)

```sql
CREATE TABLE graph_nodes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    node_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, node_id)
);

CREATE TABLE graph_edges (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    src_id VARCHAR(255) NOT NULL,
    dst_id VARCHAR(255) NOT NULL,
    rel_type VARCHAR(50) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    edge_data JSONB,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, src_id, dst_id, rel_type)
);

CREATE INDEX idx_nodes_user ON graph_nodes(user_id);
CREATE INDEX idx_nodes_type ON graph_nodes(node_type);
CREATE INDEX idx_edges_user ON graph_edges(user_id);
CREATE INDEX idx_edges_src ON graph_edges(src_id);
CREATE INDEX idx_edges_dst ON graph_edges(dst_id);
CREATE INDEX idx_edges_type ON graph_edges(rel_type);
```

**メリット**:
- 大規模グラフに対応
- 効率的なクエリ（ノード/エッジ単位）
- インデックス最適化

**デメリット**:
- 実装が複雑
- NetworkX ↔ PostgreSQL変換コスト

### 推奨: Option 1 (JSONB)から開始

Phase 1ではOption 1を実装し、将来的にOption 2への移行を検討。

### 実装（スケルトン）

```python
# backends/postgres_backend.py
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import networkx as nx
from .base import GraphBackend

Base = declarative_base()

class GraphModel(Base):
    __tablename__ = \"graph_memory\"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False)
    graph_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PostgresBackend(GraphBackend):
    \"\"\"PostgreSQL-based backend (本番環境).\"\"\"

    def __init__(self, database_url: str, user_id: str = \"global\"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.user_id = user_id

    def save(self, graph: nx.DiGraph) -> None:
        \"\"\"Save graph to PostgreSQL.\"\"\"
        data = nx.node_link_data(graph, edges=\"links\")

        # Upsert (update or insert)
        existing = self.session.query(GraphModel).filter_by(user_id=self.user_id).first()
        if existing:
            existing.graph_data = data
        else:
            new_graph = GraphModel(user_id=self.user_id, graph_data=data)
            self.session.add(new_graph)

        self.session.commit()

    def load(self) -> nx.DiGraph:
        \"\"\"Load graph from PostgreSQL.\"\"\"
        result = self.session.query(GraphModel).filter_by(user_id=self.user_id).first()
        if not result:
            return nx.DiGraph()

        return nx.node_link_graph(result.graph_data, edges=\"links\")

    def exists(self) -> bool:
        return self.session.query(GraphModel).filter_by(user_id=self.user_id).first() is not None

    def delete(self) -> None:
        self.session.query(GraphModel).filter_by(user_id=self.user_id).delete()
        self.session.commit()
```

---

## GraphMemory統合

### 使用例

```python
# デフォルト (JSON Backend)
graph = GraphMemory(persist_path=Path(\"graph.json\"))

# PostgreSQL Backend
from kagura.core.graph.backends import PostgresBackend
backend = PostgresBackend(database_url=os.getenv(\"DATABASE_URL\"))
graph = GraphMemory(backend=backend)

# 環境変数ベース（推奨）
graph = GraphMemory()  # 自動的にGRAPH_BACKEND環境変数を読み取る
```

### GraphMemory変更（提案）

```python
# memory.py
class GraphMemory:
    def __init__(
        self,
        persist_path: Optional[Path] = None,
        backend: Optional[GraphBackend] = None,
        backend_type: Literal[\"json\", \"postgres\"] = \"json\"
    ):
        # Backend選択ロジック
        if backend:
            self.backend = backend
        elif backend_type == \"postgres\":
            from .backends import PostgresBackend
            self.backend = PostgresBackend(os.getenv(\"DATABASE_URL\"))
        else:
            from .backends import JSONBackend
            self.backend = JSONBackend(persist_path or Path(\"graph.json\"))

        # 既存グラフロード
        if self.backend.exists():
            self.graph = self.backend.load()
        else:
            self.graph = nx.DiGraph()

    def save(self) -> None:
        \"\"\"Save graph to backend.\"\"\"
        self.backend.save(self.graph)

    # add_node, add_edge等は変更なし
```

---

## Migration Strategy

### Step 1: JSONBackend実装（リファクタリング）
- 既存のload()ロジックをJSONBackendに移動
- GraphMemoryはBackendを使用するように変更

### Step 2: PostgresBackend実装
- Option 1 (JSONB)で実装
- Tests作成

### Step 3: Migration Tool
```bash
# JSON → PostgreSQL移行
kagura memory migrate --from json --to postgres

# PostgreSQL → JSON export
kagura memory export --backend postgres --output graph.json
```

### Step 4: 環境変数サポート
```bash
# .env
GRAPH_BACKEND=postgres
DATABASE_URL=postgresql://...
```

---

## 次のステップ

1. [ ] `backends/base.py` - Abstract base class実装
2. [ ] `backends/json_backend.py` - JSON backend実装
3. [ ] `backends/postgres_backend.py` - PostgreSQL backend実装
4. [ ] `memory.py` - Backend統合
5. [ ] Migration tool実装
6. [ ] Tests作成
7. [ ] Documentation更新

---

**Status**: 設計完了、実装準備中
**Next Session**: Backend実装開始
**Related**: Issue #554
