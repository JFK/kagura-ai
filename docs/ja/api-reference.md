# APIリファレンス - Kagura v4.0

> **REST API & MCPツール ドキュメント**

KaguraのREST APIとMCPツールの包括的なリファレンス。

---

## 📚 目次

1. [REST API](#rest-api) - HTTPエンドポイント
2. [MCP over HTTP/SSE](#mcp-over-httpsse) - ChatGPTコネクタ
3. [MCPツール](#mcpツール) - Claude Desktop、stdio
4. [認証](#認証) - APIキー
5. [OpenAPI仕様](#openapi仕様)

---

## 🌐 REST API

**ベースURL**: `http://localhost:8000`（デフォルト）

**インタラクティブドキュメント**: http://localhost:8000/docs

### 認証

**v4.0.0**: オプショナルなAPIキー認証

```bash
# APIキー付き
curl -H "Authorization: Bearer kagura_abc123..." \
     http://localhost:8000/api/v1/memory

# なし（default_userを使用）
curl http://localhost:8000/api/v1/memory
```

**ヘッダー**:
- `Authorization: Bearer <api_key>` - オプショナルなAPIキー
- `X-User-ID: <user_id>` - オプショナルなユーザー識別子

---

## メモリー操作

### POST /api/v1/memory

メモリーを作成または更新。

**リクエスト**:
```json
{
  "key": "python_tips",
  "value": "Always use type hints",
  "scope": "persistent",
  "tags": ["python"],
  "importance": 0.8
}
```

**レスポンス**（201 Created）:
```json
{
  "key": "python_tips",
  "value": "Always use type hints",
  "scope": "persistent",
  "tags": ["python"],
  "importance": 0.8
}
```

### GET /api/v1/memory/{key}

キーでメモリーを取得。

**レスポンス**（200 OK）:
```json
{
  "key": "python_tips",
  "value": "Always use type hints",
  "scope": "persistent"
}
```

### DELETE /api/v1/memory/{key}

メモリーを削除。

**レスポンス**（204 No Content）

---

## 検索 & 呼び出し

### POST /api/v1/recall

RAGを使用したセマンティック検索。

**リクエスト**:
```json
{
  "query": "Python coding tips",
  "k": 5,
  "scope": "all"
}
```

**レスポンス**（200 OK）:
```json
{
  "results": [
    {"key": "python_tips", "value": "...", "score": 0.95}
  ]
}
```

### GET /api/v1/search

全文検索。

**クエリパラメータ**:
- `q`: 検索クエリ
- `limit`: 最大結果数（デフォルト: 10）

---

## グラフ操作

### POST /api/v1/graph/interaction

AI-ユーザーインタラクションを記録。

**リクエスト**:
```json
{
  "user_id": "jfk",
  "query": "How do I use async?",
  "response": "...",
  "metadata": {"topic": "python"}
}
```

### GET /api/v1/graph/pattern/{user_id}

ユーザーパターンを分析。

**レスポンス**:
```json
{
  "user_id": "jfk",
  "total_interactions": 150,
  "topics": {"python": 45, "docker": 20},
  "learning_trajectory": [...]
}
```

---

## システムエンドポイント

### GET /api/v1/health

ヘルスチェック。

**レスポンス**:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### GET /api/v1/metrics

システムメトリクス。

**レスポンス**:
```json
{
  "memories_count": 150,
  "graph_nodes": 87,
  "graph_edges": 42,
  "storage_size_mb": 12.5
}
```

---

## 🔌 MCP over HTTP/SSE

**エンドポイント**: `/mcp`

**プロトコル**: MCP (Model Context Protocol) over HTTP/SSE

**メソッド**:
- `GET /mcp` - SSEストリーミング（サーバー → クライアント）
- `POST /mcp` - JSON-RPCリクエスト（クライアント → サーバー）
- `DELETE /mcp` - セッション終了

**認証**:
```bash
curl -H "Authorization: Bearer kagura_abc123..." \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     http://localhost:8000/mcp
```

**参照**: [MCP over HTTP/SSE ガイド](mcp-http-setup.md)

---

## 🛠️ MCPツール

**利用可能**: Claude Desktop、stdioトランスポート、HTTP/SSE

### リモートMCP vs ローカルMCP

| 機能 | リモートMCP（HTTP/SSE） | ローカルMCP（stdio） |
|---------|----------------------|-------------------|
| **プラットフォーム** | ChatGPT、Claude Chat（将来） | Claude Desktop、Claude Code、Cursor |
| **トランスポート** | ネットワーク経由HTTP/SSE | stdio（stdin/stdout） |
| **ファイルアクセス** | ❌ なし | ✅ あり |
| **利用可能ツール** | 49/56ツール | 56/56ツール（全て） |
| **認証** | APIキー必須 | ローカルのみ（認証なし） |

### リモートMCPツール（49/56）

これらのツールは**リモートとローカルMCPの両方**で動作します:

#### ✅ リモートMCPで利用可能

**メモリーツール**（13）:
- `memory_store`, `memory_recall`, `memory_search`, `memory_list`, `memory_delete`
- `memory_feedback`, `memory_fetch`, `memory_search_ids`, `memory_stats`
- `memory_get_related`, `memory_get_user_pattern`, `memory_record_interaction`

**ウェブ検索**（5）:
- `brave_web_search`, `brave_image_search`, `brave_video_search`, `brave_news_search`
- `web_scrape`

**YouTube**（4）:
- `get_youtube_transcript`, `get_youtube_metadata`, `youtube_summarize`, `youtube_fact_check`

**コーディング**（14）:
- `coding_start_session`, `coding_end_session`, `coding_track_file_change`
- `coding_record_error`, `coding_search_errors`, `coding_record_decision`
- `coding_analyze_patterns`, `coding_analyze_file_dependencies`
- `coding_analyze_refactor_impact`, `coding_suggest_refactor_order`
- `coding_get_project_context`, `coding_get_issue_context`
- `coding_link_github_issue`, `coding_generate_pr_description`

**GitHub**（6）:
- `github_exec`, `github_issue_list`, `github_issue_view`
- `github_pr_view`, `github_pr_create`, `github_pr_merge`

**マルチモーダル**（2）:
- `multimodal_index`, `multimodal_search`

**その他**（5）:
- `arxiv_search`, `fact_check_claim`, `telemetry_stats`, `telemetry_cost`, `route_query`

#### ❌ ローカル専用ツール（7）

これらのツールは**ローカルMCPでのみ動作**（ファイルシステムアクセスが必要）:

- `file_read` - ディスクからファイルを読み取り
- `file_write` - ディスクへファイルを書き込み
- `dir_list` - ディレクトリ内容をリスト
- `shell_exec` - シェルコマンドを実行
- `media_open_image` - OSアプリで画像を開く
- `media_open_audio` - OSアプリで音声を開く
- `media_open_video` - OSアプリで動画を開く

**注意**: リモートMCP用のファイルアップロードはv4.1で予定（[Issue #462](https://github.com/JFK/kagura-ai/issues/462)）

---

### メモリーツール

#### memory_store

メモリーに情報を保存。

**パラメータ**:
- `user_id`（string、必須） - ユーザー識別子
- `agent_name`（string、必須） - エージェント名（スレッド間の場合は"global"）
- `key`（string、必須） - メモリーキー
- `value`（string、必須） - 保存する値
- `scope`（string） - "working"または"persistent"（デフォルト: "working"）
- `tags`（string） - タグのJSON配列（例: '["python"]'）
- `importance`（number） - 0.0-1.0（デフォルト: 0.5）

**例**:
```json
{
  "user_id": "jfk",
  "agent_name": "global",
  "key": "pref_language",
  "value": "Python",
  "scope": "persistent",
  "tags": "[\"preferences\"]",
  "importance": 0.8
}
```

#### memory_recall

メモリーをセマンティックに検索。

**パラメータ**:
- `user_id`（string、必須）
- `agent_name`（string、必須）
- `query`（string、必須） - 検索クエリ
- `k`（number） - 結果数（デフォルト: 5）
- `scope`（string） - "working"、"persistent"、または"all"

#### memory_search

全文 + セマンティック検索。

**パラメータ**:
- `user_id`、`agent_name`（必須）
- `query`（string、必須）
- `limit`（number） - 最大結果数

#### memory_list

すべてのメモリーをリスト。

#### memory_delete

監査ログ付きでメモリーを削除。

#### memory_feedback

メモリーの有用性にフィードバックを提供。

**パラメータ**:
- `user_id`、`agent_name`（必須）
- `node_id`（string） - 評価するメモリー
- `label`（string） - "useful"、"irrelevant"、または"outdated"
- `weight`（number） - -1.0から1.0

### グラフツール

#### memory_record_interaction

AI-ユーザーインタラクションを記録。

**パラメータ**:
- `user_id`（必須）
- `query`、`response`（必須）
- `metadata`（object） - オプショナルなメタデータ

#### memory_get_related

グラフ経由で関連メモリーを取得。

**パラメータ**:
- `user_id`、`agent_name`（必須）
- `key`（string） - 開始メモリー
- `depth`（number） - トラバーサル深度（デフォルト: 2）

#### memory_get_user_pattern

ユーザーのインタラクションパターンを分析。

### ウェブ/APIツール（リモート安全）

- `brave_web_search` - Brave Search統合（非推奨の`web_search`を置き換え）
- `brave_local_search` - ビジネス/場所用Brave Local Search
- `brave_news_search` - Brave News Search
- `brave_image_search` - Brave Image Search
- `brave_video_search` - Brave Video Search
- `web_scrape` - ウェブページをスクレイプ
- `youtube_summarize` - YouTube動画を要約
- `get_youtube_transcript` - 動画のトランスクリプトを取得

### ファイルツール（ローカルのみ）

⛔ セキュリティのため**リモートではブロック**:
- `file_read` - ローカルファイルを読み取り
- `file_write` - ローカルファイルを書き込み
- `dir_list` - ディレクトリ内容をリスト
- `shell_exec` - シェルコマンドを実行

**注意**: これらのツールは、ローカルstdio MCPサーバー（`kagura mcp serve`）経由でのみ利用可能で、HTTP/SSE（`/mcp`エンドポイント）経由では利用できません。

---

## 🔐 認証

### APIキー管理

```bash
# APIキーを作成
kagura api create-key --name "my-key"

# キーをリスト
kagura api list-keys

# キーを無効化
kagura api revoke-key --name "my-key"
```

### APIキーの使用

**REST API**:
```bash
curl -H "Authorization: Bearer kagura_abc123..." \
     http://localhost:8000/api/v1/memory
```

**MCP over HTTP/SSE**:
```bash
curl -H "Authorization: Bearer kagura_abc123..." \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
     http://localhost:8000/mcp
```

**ユーザーID抽出**:
- APIキーは`user_id`に関連付けられます
- 認証済みリクエストは自動的にキーの`user_id`を使用します
- 認証がない場合は`default_user`にフォールバック

---

## 📄 OpenAPI仕様

**インタラクティブドキュメント**: http://localhost:8000/docs

**OpenAPI JSON**: http://localhost:8000/openapi.json

**ダウンロード**:
```bash
curl http://localhost:8000/openapi.json > openapi.json
```

---

## 🔗 関連ドキュメント

- [MCPセットアップガイド](mcp-setup.md) - Claude Desktop
- [MCP over HTTP/SSE](mcp-http-setup.md) - ChatGPTコネクタ
- [セルフホスティングガイド](self-hosting.md) - 本番デプロイメント
- [メモリーエクスポート/インポート](memory-export.md) - バックアップと移行
- [アーキテクチャ](architecture.md) - システム設計

---

**最終更新**: 2025-10-27
**バージョン**: 4.0.0
**APIバージョン**: v1
