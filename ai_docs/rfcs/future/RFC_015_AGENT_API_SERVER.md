# RFC-015: Agent API Server - HTTP API for Kagura AI

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: #86
- **優先度**: High

## 概要

Kagura AIに**HTTP API Server**を追加し、Python以外の言語やノーコードツールからもエージェントを利用できるようにします。

### 目標
- REST API経由でエージェント登録・実行
- Python非依存のクライアント対応（JavaScript、Go、cURL等）
- Web UI統合（RFC-005 Meta Agentと連携）
- RFC-008（Plugin Marketplace）との統合

### 非目標
- Python-First哲学の放棄（コアはPythonのまま、APIは拡張）
- 完全なSaaS化（Phase 1はセルフホスト前提）
- 既存APIの破壊的変更

## モチベーション

### 現在の課題

1. **Pythonエンジニア限定**
   - Kagura AIを使うにはPythonが必須
   - JavaScript、Go、Rust等の開発者が利用できない
   - 非エンジニアは完全に利用不可

2. **他ツールとの統合困難**
   - Zapier、Make.com等のノーコードツールと統合できない
   - Webアプリケーションからの呼び出しが煩雑
   - マイクロサービスアーキテクチャに組み込めない

3. **スケーラビリティ限界**
   - 各ユーザーがローカル実行必須
   - リソース効率が悪い（同じエージェントを複数人が重複実行）
   - 負荷分散・オートスケールができない

### 解決するユースケース

**ケース1: JavaScript開発者**
```javascript
// Pythonコード不要
const response = await fetch('http://localhost:8000/api/agents/translate', {
  method: 'POST',
  body: JSON.stringify({ text: 'Hello', lang: 'ja' })
});
const result = await response.json();
console.log(result.output); // "こんにちは"
```

**ケース2: ノーコードツール統合**
```
Zapier Workflow:
1. Trigger: 新規メール受信
2. Action: Kagura API → summarize_email
3. Action: Slackに要約を投稿
```

**ケース3: 企業内共有サーバー**
```
データサイエンスチーム → Kagura API Server → 社内全員が利用
（全員がPythonを書く必要なし）
```

### なぜ今実装すべきか

- RFC-005（Meta Agent）でUI必要
- RFC-008（Marketplace）でエージェント配布にAPI必須
- LangChain/LangGraphはAPI Serverが弱い（差別化要因）

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         Clients (多様なプラットフォーム)      │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐   │
│  │ Web UI  │  │   cURL  │  │JavaScript│   │
│  └─────────┘  └─────────┘  └──────────┘   │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐   │
│  │   Go    │  │  Zapier │  │  Slack   │   │
│  └─────────┘  └─────────┘  └──────────┘   │
└──────────────────┬──────────────────────────┘
                   │ HTTP/WebSocket
                   ▼
┌─────────────────────────────────────────────┐
│         Kagura API Server (FastAPI)         │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  REST API Endpoints                  │  │
│  │  - POST /api/agents/register         │  │
│  │  - POST /api/agents/{name}/execute   │  │
│  │  - GET  /api/agents                  │  │
│  │  - DELETE /api/agents/{name}         │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  WebSocket (Streaming)               │  │
│  │  - WS /api/agents/{name}/stream      │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Authentication & Authorization      │  │
│  │  - JWT Token                         │  │
│  │  - API Key                           │  │
│  └──────────────────────────────────────┘  │
└──────────────────┬──────────────────────────┘
                   │ Python API
                   ▼
┌─────────────────────────────────────────────┐
│         Kagura AI Core (Python)             │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  @agent decorator                    │  │
│  │  Prompt Template Engine              │  │
│  │  Type-based Parser                   │  │
│  │  CodeExecutor (Sandboxed)            │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### API設計

#### 1. エージェント登録

**POST /api/agents/register**

```json
{
  "name": "translate",
  "code": "@agent\nasync def translate(text: str, lang: str = 'ja') -> str:\n    '''Translate to {{ lang }}: {{ text }}'''\n    pass",
  "description": "Translate text to specified language",
  "public": false
}
```

**レスポンス**:
```json
{
  "id": "agent_abc123",
  "name": "translate",
  "status": "registered",
  "created_at": "2025-10-04T10:00:00Z"
}
```

#### 2. エージェント実行

**POST /api/agents/{name}/execute**

```json
{
  "text": "Hello World",
  "lang": "ja"
}
```

**レスポンス**:
```json
{
  "output": "こんにちは、世界",
  "execution_id": "exec_xyz789",
  "duration_ms": 1234,
  "cost": {
    "input_tokens": 50,
    "output_tokens": 20,
    "total_usd": 0.0012
  }
}
```

#### 3. ストリーミング実行

**WebSocket /api/agents/{name}/stream**

```javascript
const ws = new WebSocket('ws://localhost:8000/api/agents/translate/stream');

ws.send(JSON.stringify({ text: 'Hello', lang: 'ja' }));

ws.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  console.log(chunk.delta); // ストリーミング出力
};
```

#### 4. エージェント一覧

**GET /api/agents**

**レスポンス**:
```json
{
  "agents": [
    {
      "name": "translate",
      "description": "Translate text",
      "public": true,
      "usage_count": 1234
    },
    {
      "name": "summarize",
      "description": "Summarize text",
      "public": true,
      "usage_count": 567
    }
  ]
}
```

### 実装例

#### FastAPI Server

```python
# src/kagura/api/server.py
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from kagura import agent
import inspect

app = FastAPI(title="Kagura AI API Server")

# エージェントレジストリ
agent_registry = {}

class AgentRegistration(BaseModel):
    name: str
    code: str
    description: str = ""
    public: bool = False

class AgentExecution(BaseModel):
    params: dict

@app.post("/api/agents/register")
async def register_agent(reg: AgentRegistration):
    """エージェントをコードから登録"""
    try:
        # セキュリティ: AST検証
        validate_code(reg.code)

        # 動的にエージェント関数を作成
        namespace = {}
        exec(reg.code, namespace)

        # @agentデコレータ付き関数を取得
        agent_func = next(
            (v for v in namespace.values()
             if inspect.isfunction(v) and hasattr(v, '_is_agent')),
            None
        )

        if not agent_func:
            raise HTTPException(400, "No @agent decorated function found")

        # レジストリに登録
        agent_registry[reg.name] = {
            "func": agent_func,
            "description": reg.description,
            "public": reg.public
        }

        return {
            "id": f"agent_{reg.name}",
            "name": reg.name,
            "status": "registered"
        }
    except Exception as e:
        raise HTTPException(400, f"Registration failed: {e}")

@app.post("/api/agents/{name}/execute")
async def execute_agent(name: str, execution: AgentExecution):
    """エージェント実行"""
    if name not in agent_registry:
        raise HTTPException(404, f"Agent '{name}' not found")

    agent_func = agent_registry[name]["func"]

    try:
        result = await agent_func(**execution.params)
        return {
            "output": result,
            "execution_id": f"exec_{name}_123",
            "duration_ms": 1234
        }
    except Exception as e:
        raise HTTPException(500, f"Execution failed: {e}")

@app.get("/api/agents")
async def list_agents():
    """エージェント一覧"""
    return {
        "agents": [
            {
                "name": name,
                "description": info["description"],
                "public": info["public"]
            }
            for name, info in agent_registry.items()
        ]
    }

@app.websocket("/api/agents/{name}/stream")
async def stream_agent(websocket: WebSocket, name: str):
    """ストリーミング実行"""
    await websocket.accept()

    if name not in agent_registry:
        await websocket.send_json({"error": f"Agent '{name}' not found"})
        await websocket.close()
        return

    try:
        data = await websocket.receive_json()
        agent_func = agent_registry[name]["func"]

        # ストリーミング実行（要実装）
        result = await agent_func(**data)

        await websocket.send_json({"output": result, "done": True})
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
```

### CLIコマンド

```bash
# API Server起動
$ kagura api start --host 0.0.0.0 --port 8000

Kagura API Server started at http://0.0.0.0:8000
Docs: http://0.0.0.0:8000/docs

# エージェント登録（CLIから）
$ kagura api register --file my_agent.py --name translate

✓ Agent 'translate' registered

# サーバー停止
$ kagura api stop
```

### Web UI統合（RFC-005連携）

```
Web UI (http://localhost:8000/ui/)
├─ Agent Builder
│  └─ 自然言語 → Meta Agent → コード生成 → 登録
│
├─ Agent Executor
│  ├─ エージェント選択
│  ├─ パラメータ入力（フォーム）
│  └─ 実行 → 結果表示
│
├─ Marketplace（RFC-008連携）
│  ├─ コミュニティエージェント検索
│  ├─ ワンクリックインストール
│  └─ レビュー・評価
│
└─ Dashboard
   ├─ 実行履歴
   ├─ コスト分析
   └─ パフォーマンス統計
```

## 実装計画

### Phase 1: API Server基本機能 (v2.6.0)
- [ ] FastAPIサーバー実装
- [ ] エージェント登録API
- [ ] エージェント実行API
- [ ] 一覧・削除API
- [ ] `kagura api start` コマンド

### Phase 2: セキュリティ・認証 (v2.6.0)
- [ ] JWT認証
- [ ] API Key認証
- [ ] レート制限
- [ ] サンドボックス強化

### Phase 3: ストリーミング (v2.7.0)
- [ ] WebSocket統合
- [ ] ストリーミング実行
- [ ] リアルタイムログ

### Phase 4: Web UI (v2.7.0)
- [ ] React/Vue.jsフロントエンド
- [ ] Agent Builder UI
- [ ] Executor UI
- [ ] Dashboard

### Phase 5: Marketplace統合 (v2.8.0)
- [ ] RFC-008連携
- [ ] プラグインインストールAPI
- [ ] コミュニティエージェント共有

### Phase 6: SaaS化オプション (v2.8.0+)
- [ ] マルチテナント対応
- [ ] 従量課金システム
- [ ] エンタープライズ機能（SSO、監査ログ）

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
api = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",  # JWT
    "passlib[bcrypt]>=1.7.4",
]

ui = [
    # フロントエンドは別リポジトリ（kagura-ui）
]
```

### セキュリティ考慮事項

1. **コード実行の制限**
   - AST検証（危険な構文を拒否）
   - Import制限（os、sys、subprocess禁止）
   - Dockerサンドボックス（Phase 2）

2. **認証・認可**
   - JWT Token（短期）
   - API Key（長期）
   - ユーザーごとのエージェント分離

3. **レート制限**
   - IP単位: 100リクエスト/分
   - ユーザー単位: 1000リクエスト/時

4. **監査ログ**
   - 全API呼び出しを記録
   - エージェント実行履歴
   - コスト追跡

### 設定

`~/.kagura/api_config.toml`:

```toml
[api]
host = "0.0.0.0"
port = 8000
workers = 4

[api.auth]
jwt_secret = "${JWT_SECRET}"
jwt_expire_minutes = 60
require_auth = true

[api.security]
enable_sandbox = true
max_execution_time = 300  # 5 minutes
rate_limit_per_minute = 100

[api.cors]
allow_origins = ["http://localhost:3000"]
allow_credentials = true
```

## テスト戦略

```python
# tests/api/test_server.py
from fastapi.testclient import TestClient
from kagura.api.server import app

client = TestClient(app)

def test_register_agent():
    response = client.post("/api/agents/register", json={
        "name": "test_agent",
        "code": "@agent\nasync def test(x: int) -> int:\n    '''{{ x }} + 1'''\n    pass"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "test_agent"

def test_execute_agent():
    # 事前にエージェント登録
    client.post("/api/agents/register", json={...})

    response = client.post("/api/agents/test_agent/execute", json={
        "params": {"x": 5}
    })
    assert response.status_code == 200
    assert response.json()["output"] == 6
```

## マイグレーション

既存ユーザーへの影響なし。API Serverはオプション：

```bash
# 従来通りPythonで直接使用
from kagura import agent

@agent
async def my_agent(x: str) -> str:
    '''{{ x }}'''
    pass

# またはAPI Server経由で使用
# kagura api start
# curl -X POST http://localhost:8000/api/agents/my_agent/execute
```

## ドキュメント

### 必要なドキュメント
1. API Server Setup Guide
2. REST API Reference（OpenAPI/Swagger自動生成）
3. Web UI User Guide
4. Authentication Tutorial
5. Deployment Guide（Docker、Kubernetes）

## 参考資料

- [FastAPI](https://fastapi.tiangolo.com/)
- [LangServe](https://github.com/langchain-ai/langserve) - LangChain API Server
- [OpenAI API](https://platform.openai.com/docs/api-reference)

## 改訂履歴

- 2025-10-04: 初版作成

---

**このRFCはv2.6.0以降で実装予定です。Python-Firstの哲学は維持しつつ、より広いユーザー層にリーチします。**
