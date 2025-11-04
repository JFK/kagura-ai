# Kagura AI - ユニバーサルAIメモリープラットフォーム

<p align="center">
  <img src="https://raw.githubusercontent.com/JFK/kagura-ai/main/docs/assets/kagura-logo.svg" alt="Kagura AI Logo" width="400">
</p>

<p align="center">
  <strong>あなたのメモリーを所有し、すべてのAIで共有する</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://pypi.org/project/kagura-ai/"><img src="https://img.shields.io/pypi/pyversions/kagura-ai.svg" alt="Python versions"></a>
  <a href="https://pypi.org/project/kagura-ai/"><img src="https://img.shields.io/pypi/v/kagura-ai.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/kagura-ai/"><img src="https://img.shields.io/pypi/dm/kagura-ai.svg" alt="Downloads"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/protocol-MCP-blue.svg" alt="MCP"></a>
  <img src="https://img.shields.io/badge/status-stable-green.svg" alt="Status">

**Kagura** は、あなたの**コンテキストと記憶**を、Claude/ChatGPT/Gemini/各種AIエージェントから**横断参照**できるようにする、オープンソースの **MCP対応メモリ基盤**です。

[English README](README.md) | 日本語

---

## 💡 課題

あなたのAI会話は**プラットフォーム間で分散**しています。

```
朝: ChatGPTが1日の計画を手伝う
昼: Claude Desktopでコードを書く
夜: Geminiがドキュメントを分析
```

**でも、AIはお互いを覚えていない。** 毎回ゼロから。

プラットフォームを切り替える = **最初からやり直し**。

---

## ✨ 解決策

**Kagura**: すべてのAIを**つなぐ**ユニバーサルメモリーレイヤー。

```
┌──────────────────────────────────┐
│   すべてのAIプラットフォーム     │
│   Claude • ChatGPT • Gemini      │
│   Cursor • Cline • Custom Agents │
└────────────┬─────────────────────┘
             │ (MCPプロトコル)
     ┌───────▼────────────────┐
     │   Kagura Memory Hub    │
     │   統一されたメモリー   │
     └───────┬────────────────┘
             │
    ┌────────▼─────────┐
    │  あなたのデータ  │
    │  (ローカル/クラウド) │
    └──────────────────┘
```

**すべてのAI**に以下へのアクセスを提供：
- ✅ ナレッジベース
- ✅ 会話履歴
- ✅ コーディングパターン（「Vibe Coding」）
- ✅ 学習の軌跡

**1つのメモリー。すべてのAI。**

---

## 🎯 なぜKagura?

### 個人向け
- 🔒 **プライバシー第一**: ローカル保存、セルフホスト、またはクラウド（選択可能）
- 🚫 **ベンダーロックインなし**: いつでも完全なデータエクスポート
- 🧠 **スマート検索**: ベクトル検索 + ナレッジグラフ
- 📊 **インサイト**: 学習パターンの可視化

### 開発者向け
- 💻 **「Vibe Coding」メモリー**: コーディングパターン追跡、GitHub統合
- 🔌 **MCP-native**: Claude Desktop、Cursor、Cline等で動作
- 🛠️ **拡張可能**: Python SDKでカスタムコネクター
- 📦 **本番環境対応**: Docker、API、完全なテストカバレッジ

### チーム向け（v4.2予定）
- 👥 **共有ナレッジ**: チーム全体のメモリー
- 🔐 **エンタープライズ機能**: SSO、BYOK、監査ログ
- 📈 **分析**: チームのAI利用パターン追跡

---

## ✅ v4.0 ステータス - Phase A/B/C 完了

**現在**: v4.0.0 (安定版に向けて) - ユニバーサルAIメモリープラットフォーム

**動作中の機能**:
- ✅ REST API (FastAPI + OpenAPI)
- ✅ Docker Compose setup (PostgreSQL + pgvector, Redis)
- ✅ MCP Tools v1.0 (31ツール)
- ✅ GraphMemory (NetworkXベースのナレッジグラフ)
- ✅ MCP Tool Management (`kagura mcp doctor`, `kagura mcp tools`, `kagura mcp install`)
- ✅ **NEW**: MCP over HTTP/SSE (ChatGPT Connector対応)
- ✅ **NEW**: API Key認証とCLI管理
- ✅ **NEW**: ツールアクセス制御（リモートセキュリティフィルタ）
- ✅ **NEW**: メモリーエクスポート/インポート（JSONL形式）
- ✅ **NEW**: Caddyリバースプロキシを使った本番Docker setup

**最近完了**:
- ✅ **Phase A**: MCP-First Foundation ([Issue #364](https://github.com/JFK/kagura-ai/issues/364))
- ✅ **Phase B**: GraphMemory - ユーザーパターン分析 ([Issue #345](https://github.com/JFK/kagura-ai/issues/345))
- ✅ **Phase C**: Remote MCP Server + Export/Import ([Issue #378](https://github.com/JFK/kagura-ai/issues/378))
  - Week 1-2: Remote MCP Server (HTTP/SSE、認証、セキュリティ)
  - Week 3: Memory Export/Import (JSONLバックアップ/移行)
  - Week 4: 本番デプロイメント & ドキュメント

**次の予定**:
- 🔄 **v4.0.0 stable release** (Q1 2026): 最終テストとドキュメント
- 🔄 **Phase D** (Q2 2026): Multimodal MVP (画像、音声、動画)
- 🔄 **Phase E** (Q3 2026): Consumer App (iOS/Android/Desktop)
- 🔄 **Phase F** (Q4 2026): Cloud SaaS + Enterprise機能

---

## 🚀 クイックスタート

### オプション1: v4.0 Docker（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai

# サービス起動
docker compose up -d

# 確認
curl http://localhost:8080/api/v1/health
```

**API Docs**: http://localhost:8080/docs

### オプション2: Claude Desktopと統合（v4.0.0）

```bash
# Kaguraインストール
pip install kagura-ai[full]

# Claude Desktopを自動設定
kagura mcp install

# MCPサーバー起動
kagura mcp serve
```

**参照**: [MCP Setup Guide](docs/mcp-setup.md)

### オプション3: セルフホスト本番環境（v4.0.0）⭐ NEW

```bash
# クローンと設定
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
cp .env.example .env
nano .env  # DOMAINとPOSTGRES_PASSWORDを設定

# 本番サービス起動
docker compose -f docker-compose.prod.yml up -d

# API key生成
docker compose -f docker-compose.prod.yml exec api \
  kagura api create-key --name "production"

# HTTPSでアクセス
curl https://your-domain.com/api/v1/health
```

**参照**: [Self-Hosting Guide](docs/self-hosting.md)

### オプション4: ChatGPT Connector（v4.0.0）⭐ NEW

ChatGPTをKaguraメモリーに接続：

1. Kagura APIを起動（ローカルまたはリモート）
2. ChatGPTでDeveloper Modeを有効化
3. コネクターを追加：
   - **URL**: `https://your-domain.com/mcp`
   - **Auth**: Bearer token (オプション)

**参照**: [MCP over HTTP/SSE Guide](docs/mcp-http-setup.md)

---

## 🧩 主要機能（v4.0）

### 1. **ユニバーサルメモリーAPI**（✅ Phase A完了）

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(user_id="jfk", agent_name="global")

# 保存
memory.persistent.store(
    key="python_best_practices",
    value="関数シグネチャには必ず型ヒントを使う",
    user_id="jfk",
    metadata={"tags": ["python", "coding"], "importance": 0.9}
)

# 検索（セマンティック）
results = await memory.rag.search(
    query="Pythonの関数はどう書くべき？",
    k=5
)
```

**MCPツール**:
- `memory_store` - メモリー保存
- `memory_recall` - セマンティック検索
- `memory_search` - 全文検索 + セマンティック

---

### 2. **GraphMemory - ナレッジグラフ**（✅ Phase B完了）

```python
# AIとの交流を記録
await memory.graph.record_interaction(
    user_id="jfk",
    query="非同期関数の書き方は？",
    response="async def を使って...",
    metadata={"topic": "python", "skill": "intermediate"}
)

# ユーザーパターン分析
pattern = await memory.graph.analyze_user_pattern(user_id="jfk")
# → {"topics": {"python": 45, "docker": 20}, "learning_trajectory": [...]}
```

**MCPツール**:
- `memory_record_interaction` - 交流記録
- `memory_get_user_pattern` - パターン分析
- `memory_get_related` - 関連メモリー取得

---

### 3. **Remote MCP Server**（✅ Phase C完了）⭐ NEW

**ChatGPT Connectorサポート**:
```
ChatGPT → HTTP/SSE → Kagura API (/mcp) → Memory
```

**セキュリティ機能**:
- ✅ API Key認証（SHA256ハッシュ）
- ✅ ツールフィルタリング（file操作、shell実行をリモートでブロック）
- ✅ user_id分離
- ✅ Automatic HTTPS (Caddy + Let's Encrypt)

**CLIコマンド**:
```bash
# API Key管理
kagura api create-key --name "my-key"
kagura api list-keys
kagura api revoke-key --name "my-key"

# リモート接続
kagura mcp connect --api-base https://my-server.com --api-key xxx
kagura mcp test-remote
```

---

### 4. **メモリーエクスポート/インポート**（✅ Phase C完了）⭐ NEW

```bash
# バックアップ
kagura memory export --output ./backup

# 復元
kagura memory import --input ./backup
```

**JSONL形式**: 人間が読める、完全なデータポータビリティ

**用途**:
- バックアップ
- マシン移行
- GDPRデータエクスポート
- プラットフォーム間移行

---

## 📚 ドキュメント

- [Getting Started](docs/getting-started.md) - 10分セットアップ
- [MCP Setup (Claude Desktop)](docs/mcp-setup.md)
- [MCP over HTTP/SSE (ChatGPT)](docs/mcp-http-setup.md)
- [Self-Hosting Guide](docs/self-hosting.md) - 本番デプロイメント
- [Memory Export/Import](docs/memory-export.md)
- [API Reference](docs/api-reference.md)
- [Architecture](docs/architecture.md)

---

## 🛠️ 利用可能なツール（MCP）

**メモリー** (6ツール):
- memory_store, memory_recall, memory_search
- memory_list, memory_delete, memory_feedback

**グラフ** (3ツール):
- memory_record_interaction
- memory_get_related
- memory_get_user_pattern

**Web/API** (10+ツール):
- web_search, web_scrape
- youtube_summarize, get_youtube_transcript
- brave_web_search, fact_check_claim

**ファイル操作** (ローカルのみ):
- file_read, file_write, dir_list

**システム**:
- shell_exec (ローカルのみ)
- telemetry_stats, telemetry_cost

---

## 🔐 セキュリティ

### ローカル vs リモート

**ローカル** (`kagura mcp serve` - Claude Desktop):
- ✅ 全31ツール利用可能
- ✅ ファイル操作、Shell実行可能
- ✅ 完全な機能

**リモート** (`/mcp` HTTP/SSE - ChatGPT Connector):
- ✅ 24の安全なツールのみ
- ❌ ファイル操作ブロック（セキュリティ）
- ❌ Shell実行ブロック（セキュリティ）
- ✅ API Key認証

---

## 📊 開発状況

**Phase完了**:
- ✅ **Phase A** (Oct 2025): MCP-First Foundation
- ✅ **Phase B** (Oct 2025): GraphMemory
- ✅ **Phase C** (Oct 2025): Remote MCP Server + Export/Import

**統計**:
- 📝 +6,100 lines (Phase C)
- 🧪 1,451+ tests passing
- 📚 5 new documentation guides
- 🐳 Production Docker setup

**品質**:
- ✅ Type-safe (pyright strict)
- ✅ 90%+ test coverage
- ✅ Production-ready
- ✅ Security-hardened

---

## 💬 コミュニティ

- [GitHub](https://github.com/JFK/kagura-ai) - ソースコード & Issues
- [PyPI](https://pypi.org/project/kagura-ai/) - パッケージダウンロード
- [Examples](https://github.com/JFK/kagura-ai/tree/main/examples) - 使用例
- [Discussions](https://github.com/JFK/kagura-ai/discussions) - ディスカッション

---

## 🔗 関連リンク

- [Documentation](https://www.kagura-ai.com/) - 完全ドキュメント
- [MCP Protocol](https://modelcontextprotocol.io/) - Model Context Protocol
- [Roadmap](ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md) - 実装ロードマップ

---

**ライセンス**: Apache 2.0
**バージョン**: 4.0.0 (Phase C Complete)
**ステータス**: Beta - v4.0.0 stable準備中

**すべてのAIのためのユニバーサルメモリーで構築 ❤️**
