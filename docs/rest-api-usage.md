# REST API Usage Guide

**Kagura AI v4.0** - REST API活用ガイド

REST APIは、MCP以外の方法でKaguraメモリーにアクセスするための重要なインターフェースです。

---

## 🎯 REST APIの活用シーン

### 1. カスタムAgent/Toolからの利用

Kaguraの`@agent`や`@tool`から、REST API経由でメモリー操作：

```python
import httpx
from kagura import tool

@tool
async def store_to_kagura(key: str, value: str) -> str:
    """Store data to Kagura Memory via REST API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8080/api/v1/memory",
            json={
                "key": key,
                "value": value,
                "scope": "persistent",
                "tags": ["custom_tool"]
            },
            headers={"X-User-ID": "my_agent"}
        )
        return f"Stored: {response.json()}"
```

**ユースケース**:
- カスタムツールからメモリー保存
- 外部システムとの統合
- 複雑なワークフロー

---

### 2. 他のプログラミング言語からの利用

**Node.js**:
```javascript
// Node.js からKaguraメモリーにアクセス
const axios = require('axios');

async function storeMemory(key, value) {
  const response = await axios.post('http://localhost:8080/api/v1/memory', {
    key: key,
    value: value,
    scope: 'persistent'
  }, {
    headers: {
      'X-User-ID': 'nodejs_client',
      'Authorization': 'Bearer kagura_your_api_key'
    }
  });
  return response.data;
}
```

**Go**:
```go
// Go からKaguraメモリーにアクセス
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

func storeMemory(key, value string) error {
    payload := map[string]interface{}{
        "key": key,
        "value": value,
        "scope": "persistent",
    }

    body, _ := json.Marshal(payload)
    req, _ := http.NewRequest("POST",
        "http://localhost:8080/api/v1/memory",
        bytes.NewBuffer(body))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("X-User-ID", "go_client")

    client := &http.Client{}
    resp, err := client.Do(req)
    return err
}
```

**ユースケース**:
- マルチ言語プロジェクト
- 既存のNode.js/Go/Rustアプリとの統合
- マイクロサービスアーキテクチャ

---

### 3. Web UIフロントエンドからの利用

**React Example**:
```typescript
// React フロントエンドからKagura API
import axios from 'axios';

const KaguraClient = axios.create({
  baseURL: 'http://localhost:8080/api/v1',
  headers: {
    'X-User-ID': 'web_user_123',
    'Authorization': `Bearer ${localStorage.getItem('kagura_api_key')}`
  }
});

// Memory一覧取得
async function fetchMemories() {
  const response = await KaguraClient.get('/memory');
  return response.data;
}

// Semantic検索
async function searchMemories(query: string) {
  const response = await KaguraClient.post('/recall', {
    query: query,
    k: 10
  });
  return response.data.results;
}
```

**Vue Example**:
```vue
<template>
  <div>
    <input v-model="query" @keyup.enter="search" />
    <div v-for="result in results" :key="result.key">
      {{ result.value }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const query = ref('');
const results = ref([]);

async function search() {
  const response = await axios.post(
    'http://localhost:8080/api/v1/recall',
    { query: query.value, k: 5 }
  );
  results.value = response.data.results;
}
</script>
```

**ユースケース**:
- メモリー管理Web UI
- ダッシュボード
- 検索インターフェース
- グラフビジュアライゼーション

---

### 4. Webhook/自動化スクリプトからの利用

**GitHub Webhook**:
```python
# GitHub webhookでcommitをメモリーに保存
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.post("/webhook/github")
async def github_webhook(request: Request):
    payload = await request.json()

    if payload.get("commits"):
        for commit in payload["commits"]:
            # Kagura APIに保存
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8080/api/v1/memory",
                    json={
                        "key": f"commit_{commit['id']}",
                        "value": commit['message'],
                        "scope": "persistent",
                        "tags": ["github", "commit"]
                    },
                    headers={"X-User-ID": "github_bot"}
                )

    return {"status": "ok"}
```

**定期バッチ処理**:
```python
# cronで定期実行してメモリー統計を保存
import httpx
from datetime import datetime

async def daily_memory_snapshot():
    async with httpx.AsyncClient() as client:
        # メトリクス取得
        metrics = await client.get("http://localhost:8080/api/v1/metrics")

        # スナップショット保存
        await client.post(
            "http://localhost:8080/api/v1/memory",
            json={
                "key": f"snapshot_{datetime.now().isoformat()}",
                "value": metrics.json(),
                "scope": "persistent",
                "tags": ["metrics", "snapshot"]
            }
        )
```

**ユースケース**:
- CI/CD統合（テスト結果保存等）
- 監視システム統合
- データパイプライン
- スケジューラー連携

---

### 5. マイクロサービス間通信

**サービスA → Kagura → サービスB**:

```python
# Service A: データをKaguraに保存
async def process_and_store(data):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://kagura-api:8080/api/v1/memory",
            json={
                "key": f"user_{user_id}_preference",
                "value": data,
                "scope": "persistent"
            }
        )

# Service B: Kaguraからデータ取得
async def fetch_user_preference(user_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://kagura-api:8080/api/v1/memory/user_{user_id}_preference"
        )
        return response.json()
```

**ユースケース**:
- マイクロサービス間の状態共有
- セッション管理
- ユーザープリファレンス共有

---

## 📊 REST API vs MCP の使い分け

| シーン | 推奨 | 理由 |
|--------|------|------|
| **Claude Desktop** | MCP (stdio) | ネイティブ統合、全ツール利用可 |
| **ChatGPT Connector** | MCP (HTTP/SSE) | 標準プロトコル、簡単設定 |
| **Python Agent** | REST API | httpx簡単、非同期対応 |
| **Web UI** | REST API | フロントエンドから直接アクセス |
| **他言語** | REST API | 言語非依存、HTTP標準 |
| **Webhook** | REST API | HTTP POST簡単 |
| **バッチ処理** | REST API | curl/httpxで簡単 |

---

## 🛠️ Python SDK例（REST API活用）

```python
# Kagura REST API Client wrapper
import httpx
from typing import Optional, List, Dict, Any

class KaguraClient:
    """Kagura Memory API Client"""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        user_id: str = "default_user"
    ):
        self.base_url = base_url
        self.headers = {"X-User-ID": user_id}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def store(
        self,
        key: str,
        value: str,
        scope: str = "persistent",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Store memory"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/memory",
                json={
                    "key": key,
                    "value": value,
                    "scope": scope,
                    "tags": tags or []
                },
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def recall(
        self,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Semantic search"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/recall",
                json={"query": query, "k": k},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("results", [])

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get memory by key"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/memory/{key}",
                headers=self.headers
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

# Usage
client = KaguraClient(user_id="my_app")
await client.store("pref", "Python")
results = await client.recall("what's my preference?")
```

**ユースケース**:
- FastAPI/Flask アプリからの利用
- データパイプライン
- カスタムAgent

---

## 🌐 REST API の強み

### vs MCP

**REST APIの利点**:
- ✅ **言語非依存** - どんな言語からでもアクセス可
- ✅ **標準的** - HTTP/JSON、全開発者が理解
- ✅ **シンプル** - curl 1行で動作確認
- ✅ **OpenAPI** - 自動ドキュメント生成
- ✅ **Web統合** - フロントエンドから直接アクセス

**MCPの利点**:
- ✅ **標準化** - AIツール連携の標準プロトコル
- ✅ **ネイティブ統合** - Claude Desktop等で自動認識
- ✅ **リッチツール** - 複雑なパラメータ・スキーマ

**結論**: **両方を併用**するのがベストプラクティス

---

## 📝 推奨: REST API活用例をExamplesに追加

以下のサンプルを `examples/` に追加することを推奨：

1. **`examples/09_rest_api/`**
   - `python_client.py` - Python REST client例
   - `fastapi_integration.py` - FastAPIアプリ統合
   - `webhook_example.py` - Webhook統合
   - `batch_processing.py` - バッチ処理例

2. **`examples/10_frontend/`**
   - `react_example/` - React Web UI
   - `vue_example/` - Vue.js例

3. **`examples/11_multi_language/`**
   - `nodejs_client.js` - Node.js client
   - `go_client.go` - Go client
   - `rust_client.rs` - Rust client

---

## 🔗 関連ドキュメント

- [API Reference](api-reference.md) - 全エンドポイント
- [Getting Started](getting-started.md)
- [MCP Setup](mcp-setup.md) - MCP vs REST比較

---

**結論**: REST APIは削除せず、**積極的に活用すべき**重要な機能です。

**Last Updated**: 2025-10-27
**Version**: 4.0.0
