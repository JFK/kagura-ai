# Kagura AI 用語集 - v4.0

**Last Updated**: 2025-10-27
**Version**: v4.0

Kagura AI v4.0で使用される用語・略語の定義集。

---

## コア概念

### Universal Memory
v4.0の中核概念。すべてのAIプラットフォーム（Claude、ChatGPT、Gemini等）で共有できるメモリー・コンテキスト。

**特徴**:
- プラットフォーム横断
- ローカル/セルフホスト/クラウド対応
- MCP-native

### MCP (Model Context Protocol)
Anthropic提唱のプロトコル。AIとツールの標準的な連携方式。

**Kagura v4.0での役割**:
- 主要インターフェース（MCP-First）
- Claude Desktop、ChatGPT、Cursor等で利用可能
- stdio transport（ローカル）とHTTP/SSE transport（リモート）

### MCP-First
v4.0の設計哲学。すべての機能をまずMCPツールとして公開し、その後REST APIで補完。

**変更点**:
- v3.0: SDK-First（Python統合がメイン）
- v4.0: MCP-First（プラットフォーム横断がメイン）

---

## メモリーシステム

### user_id
v4.0で導入されたユーザー識別子。全てのメモリー操作で必須。

**目的**: マルチユーザーサポート、データ分離、リモートアクセスの基盤

### agent_name
メモリーのスコープを定義する識別子。

**使い分け**:
- `"global"` - 全スレッド共有（ユーザー設定等）
- `"thread_xxx"` - スレッド固有（会話コンテキスト等）

### Working Memory
セッション中のみ有効な一時メモリー。In-memory辞書。

### Persistent Memory
SQLiteに保存される永続メモリー。再起動後も保持。

### Graph Memory
NetworkXベースの知識グラフ。メモリー間の関係性、AIとユーザーのインタラクション履歴を記録。

**Phase B** (Oct 2025) で実装。

### Memory Scope
メモリーの保存先：`"working"` (一時) or `"persistent"` (永続)

---

## Remote MCP Server (Phase C)

### HTTP/SSE Transport
MCP over HTTP/Server-Sent Eventsによるリモートアクセス。

**Endpoint**: `/mcp`

**用途**: ChatGPT Connector、リモートアクセス

### Local Context vs Remote Context
ツールアクセス制御の2つのコンテキスト。

**Local** (`kagura mcp serve`):
- 全31ツール利用可能
- File操作、Shell実行可能
- Claude Desktop、stdio接続

**Remote** (`/mcp` HTTP/SSE):
- 24の安全なツールのみ
- File操作、Shell実行はブロック
- ChatGPT Connector、HTTP接続

### Tool Permissions
ツールごとのアクセス制御設定。

**File**: `src/kagura/mcp/permissions.py`

**分類**:
- `remote: true` - リモートアクセス可（memory_*, web_*等）
- `remote: false` - ローカルのみ（file_*, shell_exec等）

### API Key
リモートアクセス用の認証トークン。

**形式**: `kagura_<random_32_bytes>`

**保存**: SHA256ハッシュでSQLiteに保存

**管理**: `kagura api create-key`, `list-keys`, `revoke-key`

---

## Export/Import (Phase C Week 3)

### JSONL Format
JSON Lines形式。1行1レコードの人間可読フォーマット。

**用途**: メモリーのバックアップ、マイグレーション、GDPR対応

**ファイル**:
- `memories.jsonl` - メモリーレコード
- `graph.jsonl` - グラフノード・エッジ
- `metadata.json` - エクスポートメタデータ

### MemoryExporter / MemoryImporter
Export/Import機能のコアクラス。

**CLI**: `kagura memory export`, `kagura memory import`

### Roundtrip Validation
Export → Import で100%データ保全が保証されること。

---

## Production Deployment (Phase C Week 4)

### docker-compose.prod.yml
本番環境用のDocker Compose設定。

**スタック**:
- PostgreSQL + pgvector
- Redis
- Kagura API
- Caddy (reverse proxy)

### Caddy
Go製のリバースプロキシ。Let's Encryptによる自動HTTPS取得。

**特徴**:
- 設定ファイルがシンプル（Caddyfile）
- HTTP/2、HTTP/3対応
- SSE streaming対応

### Health Check
サービス正常性確認。

**Endpoint**: `/api/v1/health`

**Docker**: `healthcheck` directive

---

## 技術用語

### FastAPI
Python Web framework。Kagura API serverの実装に使用。

**特徴**:
- 自動OpenAPI生成
- 非同期サポート
- 型ヒントベース

### StreamableHTTPServerTransport
MCP SDKのHTTP/SSE transport実装クラス。

**用途**: `/mcp` endpointの実装

### SQLite
軽量なRDBMS。Persistent Memory、API Key保存に使用。

**ファイル**:
- `~/.kagura/memory.db` - メモリー
- `~/.kagura/api_keys.db` - API keys

### ChromaDB
ベクトルデータベース。Memory RAG、セマンティック検索に使用。

### NetworkX
Pythonグラフライブラリ。Graph Memoryの実装に使用。

### Pydantic v2
データバリデーションライブラリ。FastAPI、型パースで使用。

### LiteLLM
複数LLMプロバイダの統一インターフェース。

---

## 開発ツール

### pyright
Microsoft製の型チェッカー。`--strict`モードで100%型安全性。

### ruff
高速Pythonリンター・フォーマッター。

### pytest
テストフレームワーク。非同期テスト対応。

### uv
高速パッケージマネージャ。pip代替。

### Docker Compose
複数コンテナのオーケストレーション。開発・本番環境構築。

---

## プロジェクト固有用語

### Kagura (神楽)
日本の伝統芸能。調和と創造性を象徴。

### MCP-First
v4.0の設計哲学。全機能をMCPツールで提供し、プラットフォーム横断を実現。

**v3.0からの変化**:
- v3.0: SDK-First（Python統合）
- v4.0: MCP-First（プラットフォーム横断）

### Issue-Driven Development
GitHub Issueを起点とした開発フロー。

```
Issue作成 → Branch作成 → 実装 → Draft PR → CI → Merge
```

### Conventional Commits
コミットメッセージ標準形式。

```
<type>(<scope>): <subject> (#issue-number)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type**: feat, fix, refactor, test, docs, chore

---

## CLI Commands (v4.0)

### MCP Management

- `kagura mcp serve` - MCP server起動（stdio、全ツール）
- `kagura mcp install` - Claude Desktop自動設定
- `kagura mcp tools` - 利用可能ツール一覧
- `kagura mcp doctor` - 診断実行
- `kagura mcp connect` - リモート接続設定
- `kagura mcp test-remote` - リモート接続テスト

### API Key Management

- `kagura api create-key` - API key生成
- `kagura api list-keys` - Key一覧
- `kagura api revoke-key` - Key無効化
- `kagura api delete-key` - Key削除

### Memory Management

- `kagura memory export` - JSONL export
- `kagura memory import` - JSONL import

### System

- `kagura --version` - バージョン表示
- `kagura init` - 初期設定（v3.0互換）

---

## Phase（開発フェーズ）

### Phase A (✅ Oct 2025)
MCP-First Foundation - REST API、MCP Tools v1.0

### Phase B (✅ Oct 2025)
GraphMemory - ユーザーパターン分析

### Phase C (✅ Oct 2025)
Remote MCP Server + Export/Import

**Week 1-2**: Remote MCP Server（HTTP/SSE、認証、セキュリティ）
**Week 3**: Memory Export/Import（JSONL）
**Week 4**: Production Deployment（Docker、Caddy）

### Phase D-F (🔜 2026)
Multimodal MVP、Consumer App、Cloud SaaS

---

## 略語

| 略語 | 正式名称 | 説明 |
|------|---------|------|
| **MCP** | Model Context Protocol | AI-ツール連携プロトコル |
| **SSE** | Server-Sent Events | HTTP streaming技術 |
| **JSONL** | JSON Lines | 1行1レコードのJSON形式 |
| **RAG** | Retrieval-Augmented Generation | 検索拡張生成 |
| **LLM** | Large Language Model | 大規模言語モデル |
| **API** | Application Programming Interface | HTTP API |
| **CLI** | Command Line Interface | コマンドライン |
| **GDPR** | General Data Protection Regulation | EU個人データ保護規則 |
| **SHA256** | Secure Hash Algorithm 256 | ハッシュ関数 |
| **SSL/TLS** | Secure Sockets Layer / Transport Layer Security | 暗号化通信 |
| **HTTPS** | HTTP Secure | SSL/TLS over HTTP |
| **CORS** | Cross-Origin Resource Sharing | オリジン間リソース共有 |

---

## ディレクトリ構造

| パス | 説明 |
|------|------|
| `src/kagura/core/` | コアロジック（Memory、Graph） |
| `src/kagura/api/` | REST API（FastAPI） |
| `src/kagura/mcp/` | MCP Server & Tools |
| `src/kagura/cli/` | CLI commands |
| `tests/` | テストコード |
| `docs/` | ユーザードキュメント |
| `ai_docs/` | AI開発ドキュメント（内部用） |
| `examples/` | 使用例 |

---

## 参考資料

### 公式
- [GitHub](https://github.com/JFK/kagura-ai)
- [PyPI](https://pypi.org/project/kagura-ai/)
- [Documentation](https://www.kagura-ai.com/)

### 主要依存ライブラリ
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic v2](https://docs.pydantic.dev/)
- [MCP SDK](https://modelcontextprotocol.io/)
- [NetworkX](https://networkx.org/)
- [ChromaDB](https://www.trychroma.com/)
- [LiteLLM](https://docs.litellm.ai/)

### プロトコル
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [OpenAPI Specification](https://swagger.io/specification/)

---

**Last Updated**: 2025-10-27 (v4.0 - Phase C Complete)
