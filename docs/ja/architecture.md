# アーキテクチャ - Kagura v4.0

> **Universal AI Memory Platform - システム設計**

このドキュメントは、Phase C完了後のKagura v4.0のアーキテクチャを説明します。

---

## 🏗️ 高レベル概要

```
┌─────────────────────────────────────────────────────────────────┐
│                  AIプラットフォーム（MCPクライアント）              │
│      Claude Desktop • ChatGPT • Gemini • Cursor • Cline         │
└──────┬────────────────────────────────────────────────┬─────────┘
       │ stdio（ローカル）              HTTP/SSE（リモート）│
       │                                                   │
┌──────▼─────────────┐                    ┌──────────────▼────────┐
│  MCPサーバー       │                    │  MCP over HTTP/SSE    │
│  （ローカル）      │                    │  （/mcpエンドポイント）│
│                    │                    │                       │
│  全31ツール ✅     │                    │  24安全ツールのみ     │
│  ファイル操作 ✅   │                    │  ファイル操作 ❌      │
│  シェル実行 ✅     │                    │  シェル実行 ❌        │
└──────┬─────────────┘                    └──────────────┬────────┘
       │                                                   │
       │              内部Python API                       │
       └───────────────────────┬───────────────────────────┘
                               │
          ┌────────────────────▼─────────────────────┐
          │         メモリーマネージャー             │
          │   (src/kagura/core/memory/manager.py)    │
          │                                          │
          │  ┌──────────┬───────────┬─────────────┐ │
          │  │ Working  │ Context   │ Persistent  │ │
          │  │ Memory   │ Memory    │ Memory      │ │
          │  │(In-Mem)  │(Messages) │(SQLite)     │ │
          │  └──────────┴───────────┴─────────────┘ │
          │                                          │
          │  ┌────────────────────────────────────┐ │
          │  │  RAG (ChromaDB)                    │ │
          │  │  • Working RAG                     │ │
          │  │  • Persistent RAG                  │ │
          │  │  • セマンティック検索              │ │
          │  └────────────────────────────────────┘ │
          │                                          │
          │  ┌────────────────────────────────────┐ │
          │  │  グラフメモリー (NetworkX)         │ │
          │  │  • 関係性                          │ │
          │  │  • インタラクション履歴            │ │
          │  │  • ユーザーパターン                │ │
          │  └────────────────────────────────────┘ │
          └────────────────┬─────────────────────────┘
                           │
                  ┌────────▼────────┐
                  │    ストレージ   │
                  │  • SQLite       │
                  │  • ChromaDB     │
                  │  • Pickleファイル│
                  └─────────────────┘
```

---

## 🆕 Phase Cアーキテクチャ（リモートMCPサーバー）

### リモートアクセスフロー

```
ChatGPT                         あなたのサーバー
┌─────────┐                     ┌──────────────┐
│ ChatGPT │  HTTPS/SSE          │    Caddy     │
│Connector├────────────────────►│ (Port 443)   │
└─────────┘                     └──────┬───────┘
                                       │
                               ┌───────▼───────┐
                               │  Kagura API   │
                               │  (Port 8000)  │
                               │               │
                               │  /mcp         │◄─ HTTP/SSE
                               │  /api/v1/*    │◄─ REST
                               └───────┬───────┘
                                       │
                              ┌────────▼────────┐
                              │メモリーマネージャー│
                              │  + グラフ       │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │ PostgreSQL      │
                              │ + pgvector      │
                              └─────────────────┘
```

### セキュリティレイヤー

```
1. APIキー認証
   ├─ SHA256ハッシュストレージ
   ├─ オプショナルな有効期限
   └─ 監査証跡（last_used_at）

2. ツールアクセス制御
   ├─ ローカルコンテキスト: 全31ツール ✅
   ├─ リモートコンテキスト: 24安全ツールのみ
   └─ 危険なツールをフィルタリング:
      • file_read, file_write
      • shell_exec
      • media_open_*

3. ネットワークセキュリティ
   ├─ Caddyリバースプロキシ
   ├─ 自動HTTPS（Let's Encrypt）
   ├─ CORS設定
   └─ セキュリティヘッダー（HSTS、XSS）
```

---

## 📦 コンポーネント詳細

### 1. MCPサーバー (src/kagura/mcp/)

**stdioトランスポート**（ローカル）:
- **ファイル**: `src/kagura/cli/mcp.py`
- **コマンド**: `kagura mcp serve`
- **コンテキスト**: `local`（全ツール利用可能）
- **クライアント**: Claude Desktop、Cursor、Cline

**HTTP/SSEトランスポート**（リモート）:
- **ファイル**: `src/kagura/api/routes/mcp_transport.py`
- **エンドポイント**: `/mcp`
- **コンテキスト**: `remote`（安全なツールのみ）
- **クライアント**: ChatGPTコネクタ、ウェブブラウザ

**ツールパーミッション**:
- **ファイル**: `src/kagura/mcp/permissions.py`
- **ロジック**: `is_tool_allowed(tool_name, context)`
- **デフォルト**: 未知のツールを拒否（フェイルセーフ）

---

### 2. メモリーマネージャー (src/kagura/core/memory/)

**コンポーネント**:
- `manager.py` - メインコーディネーター
- `working.py` - インメモリー一時ストレージ
- `persistent.py` - SQLiteベースの長期ストレージ
- `rag.py` - ChromaDBベクトル検索
- `export.py` - JSONLエクスポート/インポート

**ストレージスコープ**:
- **Working**: セッションのみ、使用後にクリア
- **Persistent**: 再起動後も存続、SQLiteストレージ
- **両方**: セマンティック検索のためRAGにインデックス

---

### 3. グラフメモリー (src/kagura/core/graph/)

**実装**: NetworkXベース

**ノードタイプ**:
- `user` - ユーザープロファイル
- `topic` - ディスカッショントピック
- `memory` - メモリー参照
- `interaction` - AI-ユーザーインタラクション

**エッジタイプ**:
- `related_to` - 関連メモリー
- `depends_on` - 依存関係
- `learned_from` - 学習関係
- `works_on` - ユーザーアクティビティ

**ストレージ**: Pickleファイル (`~/.local/share/kagura/graph.pkl`)

---

### 4. REST API (src/kagura/api/)

**フレームワーク**: FastAPI

**エンドポイント**:
- `/api/v1/memory` - メモリーCRUD
- `/api/v1/recall` - セマンティック検索
- `/api/v1/search` - 全文検索
- `/api/v1/graph/*` - グラフ操作
- `/api/v1/health` - ヘルスチェック
- `/api/v1/metrics` - システムメトリクス
- `/mcp` - MCP over HTTP/SSE ⭐ 新機能

**認証**:
- **ファイル**: `src/kagura/api/auth.py`
- **メソッド**: Bearerトークン（APIキー）
- **ストレージ**: SQLite (`~/.local/share/kagura/api_keys.db`)
- **ハッシング**: SHA256

---

## 🔄 データフロー

### メモリー保存フロー

```
1. MCPクライアント（Claude/ChatGPT）
   └─► MCPツール呼び出し: memory_store(...)

2. MCPサーバー（stdioまたはHTTP/SSE）
   └─► tool_registryにルーティング

3. 組み込みツール (src/kagura/mcp/builtin/memory.py)
   └─► MemoryManager.store()を呼び出し

4. メモリーマネージャー
   ├─► Persistent メモリー（SQLite）
   └─► RAG インデックス（ChromaDB）

5. ストレージ
   ├─► SQLite（persistent）
   └─► ChromaDB（ベクトル）
```

### メモリー呼び出しフロー

```
1. MCPツール呼び出し: memory_recall(query="Python tips", k=5)

2. メモリーマネージャー
   └─► RAGをクエリ（ベクトル類似度）

3. RAG検索
   ├─► クエリを埋め込み（text-embedding-3-small）
   ├─► ChromaDBコレクションを検索
   └─► トップk結果を返す

4. クライアントに返す
   └─► スコア付きでフォーマットされた結果
```

---

## 🔐 セキュリティアーキテクチャ

### 認証フロー

```
1. クライアントリクエスト
   └─► Authorization: Bearer kagura_abc123...

2. APIゲートウェイ（/mcpまたは/api/v1/*）
   └─► Bearerトークンを抽出

3. APIキーマネージャー (src/kagura/api/auth.py)
   ├─► 提供されたキーをハッシュ（SHA256）
   ├─► api_keys.dbをクエリ
   ├─► 有効期限と無効化をチェック
   └─► user_idを抽出

4. リクエスト処理
   └─► メモリー操作に認証されたuser_idを使用
```

### ツールフィルタリング（リモートコンテキスト）

```
1. create_mcp_server(context="remote")

2. handle_list_tools()
   ├─► 登録された全ツールを取得（合計31）
   ├─► TOOL_PERMISSIONSでフィルタリング
   └─► 安全なツールのみを返す（24）

3. クライアントが見るもの:
   ✅ memory_*ツール
   ✅ web_*ツール
   ❌ file_*ツール（ブロック）
   ❌ shell_exec（ブロック）
```

---

## 💾 データモデル

### メモリーレコード

```python
{
    "key": str,                  # 一意の識別子
    "value": Any,                # 保存データ（JSONシリアライズ可能）
    "user_id": str,              # オーナー（v4.0+）
    "agent_name": str,           # エージェントスコープ
    "scope": "working|persistent",
    "tags": List[str],           # カテゴリー化
    "importance": float,         # 0.0-1.0
    "created_at": datetime,
    "updated_at": datetime,
    "metadata": Dict[str, Any]   # 追加メタデータ
}
```

### グラフノード

```python
{
    "id": str,                   # ノード識別子
    "type": str,                 # ノードタイプ（user、topic、memory、interaction）
    "data": Dict[str, Any],      # ノード属性
}
```

### グラフエッジ

```python
{
    "src": str,                  # ソースノードID
    "dst": str,                  # デスティネーションノードID
    "type": str,                 # 関係タイプ
    "weight": float,             # 0.0-1.0
}
```

---

## 📊 デプロイメントアーキテクチャ

### ローカル開発

```
開発者マシン
├── SQLite (~/.local/share/kagura/memory.db)
├── ChromaDB (~/.local/share/kagura/chromadb/)
├── グラフpickle (~/.local/share/kagura/graph.pkl)
└── APIキー (~/.local/share/kagura/api_keys.db)
```

### 本番デプロイメント

```
Dockerスタック (docker-compose.prod.yml)

┌─────────────────────────────────────────┐
│            Caddy (Port 443)             │
│     自動HTTPS、リバースプロキシ        │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│       Kagura API (Port 8000)            │
│    FastAPI + MCP over HTTP/SSE          │
└──────┬──────────────────────┬───────────┘
       │                      │
┌──────▼──────────┐   ┌──────▼──────────┐
│   PostgreSQL    │   │     Redis       │
│   + pgvector    │   │   (キャッシング)│
└─────────────────┘   └─────────────────┘

ボリューム:
├── postgres_data  - データベース永続化
├── redis_data     - Redis永続化
├── kagura_data    - メモリーエクスポートなど
└── caddy_data     - SSL証明書
```

---

## 🔄 エクスポート/インポートシステム

### エクスポート形式（JSONL）

```
backup/
├── memories.jsonl      # 全メモリーレコード
├── graph.jsonl         # グラフノード & エッジ
└── metadata.json       # エクスポートメタデータ
```

**レコード例**:
```jsonl
{"type":"memory","scope":"persistent","key":"python_tips","value":"Use type hints","user_id":"jfk","agent_name":"global","tags":["python"],"importance":0.8,"exported_at":"2025-10-27T10:00:00Z"}
```

---

## 📐 設計原則

### 1. MCP-First

すべての機能をまずMCPツール経由で公開し、その後REST API。

### 2. 最初からマルチユーザー

すべての操作は`user_id`でスコープ（Phase Cの基盤）。

### 3. デフォルトでセキュア

リモートアクセスは安全性のために自動的にフィルタリング。

### 4. データポータビリティ

人間が読めるJSONL形式での完全なエクスポート/インポート。

### 5. フェイルセーフ

リモートコンテキストでは未知のツールをデフォルトで拒否。

---

## 🔗 関連ドキュメント

- [はじめに](getting-started.md)
- [MCPセットアップガイド](mcp-setup.md)
- [MCP over HTTP/SSE](mcp-http-setup.md)
- [セルフホスティングガイド](self-hosting.md)
- [APIリファレンス](api-reference.md)

---

**最終更新**: 2025-10-27
**バージョン**: 4.0.0
**フェーズ**: C完了
