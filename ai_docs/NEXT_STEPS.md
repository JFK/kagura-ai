# Kagura AI - Next Steps（次のアクション）

**最終更新**: 2025-10-04
**現在地**: v2.0.0-beta.1 リリース済み、v2.0.0正式版に向けて最終調整

---

## 📍 現在の状況

### ✅ 完了済み
- **v2.0.0-beta.1**: PyPI公開完了（Issue #60）
- **Core Engine**: @agent, Prompt Template, Type Parser（#14, #15, #16）
- **Code Executor**: AST検証、安全実行（#20, #21）
- **CLI & REPL**: Click CLI、基本REPL（#24, #25, #27, #56）
- **テスト**: 統合テスト、カバレッジ95%+（#31, #55）
- **ドキュメント**: README、チュートリアル、サンプル（#32, #33, #34, #45, #54）
- **RFC作成**: 全13個のRFC（002-014）作成完了、Issue作成済み
- **統合ロードマップ**: `UNIFIED_ROADMAP.md`作成完了

### 🚧 進行中
- **Issue #72**: REPL改善（prompt_toolkit、マルチライン貼り付け、履歴）

### 📝 計画済み（RFC）
- **RFC-007 (Very High)**: MCP Integration (#67)
- **RFC-006 (High)**: Live Coding - Chat REPL (#66)
- **RFC-012 (High)**: Commands & Hooks (#73)
- **RFC-002〜005, 008〜011, 013〜014**: 詳細は `UNIFIED_ROADMAP.md` 参照

---

## 🎯 優先アクション（1-2週間）

### 1. v2.0.0 正式版リリース（Week 1）

#### Issue #72: REPL改善を完了
**タスク**:
```bash
# 1. prompt_toolkit統合
- ✅ インストール: `uv add prompt_toolkit`
- ✅ PromptSession実装
- ✅ マルチライン入力対応
- ✅ 履歴機能（~/.kagura/repl_history）
- ✅ 自動補完

# 2. テスト
- ✅ マルチライン貼り付けテスト
- ✅ 履歴機能テスト
- ✅ エッジケーステスト

# 3. ドキュメント更新
- ✅ REPL使用方法の更新
```

**完了条件**:
- `>>>` プロンプトがバックスペースで削除不可
- 複数行コードの貼り付けが正常動作
- 履歴が`Ctrl+R`で検索可能

**見積もり**: 2-3日

---

#### v2.0.0 正式版リリース準備
**タスク**:
```bash
# 1. 最終テスト
pytest --cov=src/kagura --cov-report=html
pyright src/kagura/

# 2. CHANGELOGの更新
# ai_docs/UNIFIED_ROADMAP.md → CHANGELOG.md v2.0.0セクション

# 3. バージョン更新
# pyproject.toml: version = "2.0.0"

# 4. PyPI公開
uv build
uv publish

# 5. GitHub Release
gh release create v2.0.0 \
  --title "Kagura AI v2.0.0 - Core Release" \
  --notes "Full release notes in CHANGELOG.md"
```

**完了条件**:
- ✅ テスト全てパス
- ✅ `pip install kagura-ai==2.0.0` で動作
- ✅ README のサンプル全て動作

**見積もり**: 2-3日

**期限**: Week 1終了まで

---

## 🚀 短期目標（Week 2-6: v2.1.0開発）

### 2. RFC-007: MCP Integration実装開始（Week 2-6）

#### Week 2-3: MCPサーバー実装
**Issue #67のサブタスク**:

```python
# 1. MCP SDK統合
uv add mcp

# 2. KaguraエージェントをMCPツールとして公開
# src/kagura/mcp/server.py
from mcp import Server

@server.list_tools()
async def list_tools():
    """Kaguraエージェント → MCPツール変換"""
    agents = agent_registry.get_all()
    return [
        {
            "name": f"kagura_{agent.name}",
            "description": agent.description,
            "inputSchema": generate_json_schema(agent.signature)
        }
        for agent in agents
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """MCPツール実行"""
    agent = agent_registry.get(name.replace("kagura_", ""))
    return await agent(**arguments)
```

**完了条件**:
- ✅ `kagura mcp start` でMCPサーバー起動
- ✅ Claude Codeから `mcp install kagura-ai` で接続
- ✅ Kaguraエージェントを呼び出し可能

**見積もり**: 2週間

---

#### Week 4-5: MCPクライアント実装
**タスク**:

```python
# Kagura → 外部MCPツール呼び出し
@agent
@mcp.use("fetch", "filesystem")
async def research_agent(topic: str) -> str:
    """
    Research {{ topic }} using web fetch tool
    """
    # 自動的に fetch ツールが利用可能
    pass
```

**完了条件**:
- ✅ `@mcp.use()` デコレータ実装
- ✅ 既存MCPツールを呼び出し可能

**見積もり**: 1.5週間

---

#### Week 6: 統合テスト・ドキュメント
**タスク**:
- Claude Code ⇄ Kagura 双方向統合テスト
- MCPサーバー設定ガイド
- サンプルエージェント作成

**完了条件**:
- ✅ Claude Code内でKaguraエージェント利用可能
- ✅ ドキュメント完備

**見積もり**: 0.5週間

---

### 3. RFC-006: Chat REPL実装（Week 4-6）

**並行実装可能**（MCP実装と同時進行）

```bash
# 対話型チャット
$ kagura chat
You: 今日の天気は？
AI: （Web検索して）東京は晴れ、最高気温25度...

You: /translate こんにちは
AI: Hello

You: /exit
```

**実装内容**:
1. Chat REPL UI（Week 4）
   - セッション管理
   - 履歴表示
2. プリセットコマンド（Week 5）
   - `/translate`, `/summarize`, `/review`
3. ドキュメント（Week 6）

**完了条件**:
- ✅ `kagura chat` で即座に対話開始
- ✅ エージェント定義不要

**見積もり**: 2週間（MCP実装と並行）

---

## 📅 中期目標（Week 7-26: v2.2.0まで）

### Week 7-12: RFC-012 Commands & Hooks (#73)
- Markdownコマンド定義
- PreToolUse / PostToolUse Hooks
- インライン実行 ``!`command` ``

### Week 13-19: RFC-002 Multimodal RAG (#62)
- 画像・音声・PDF処理
- RAG Chat (`kagura chat --dir`)
- Google Workspace連携

### Week 20-26: RFC-014 Web Integration (#75)
- Brave Search API
- BeautifulSoup スクレイピング
- `@web.enable` デコレータ

---

## 🌐 長期目標（Week 27+: v2.3.0以降）

### v2.3.0 (Week 27-34): Personal AI & Auth
- RFC-003: Personal Assistant (#63)
- RFC-013: OAuth2 Auth (#74)

### v2.4.0 (Week 35-42): Meta Agent & Ecosystem
- RFC-005: Meta Agent (#65)
- RFC-008: Plugin Marketplace (#68)
- RFC-009: Multi-Agent Orchestration (#69)

### v2.5.0+ (Week 43+): Advanced Features
- RFC-004: Voice Interface (#64)
- RFC-006: LSP Integration (#66)
- RFC-010: Observability (#70)
- RFC-011: Scheduled Automation (#71)

**詳細**: `ai_docs/UNIFIED_ROADMAP.md` 参照

---

## 🔧 技術的な準備事項

### 開発環境
```bash
# Python 3.11+
python --version

# 依存関係インストール
uv sync

# テスト実行
pytest

# 型チェック
pyright src/kagura/

# リンター
ruff check src/
```

### CI/CD
- GitHub Actions設定済み
- PyPI自動デプロイ設定済み
- Codecov統合済み

---

## 📊 進捗管理

### GitHub Projects
- Milestoneで管理: v2.0.0, v2.1.0, v2.2.0...
- Issueラベル: `enhancement`, `rfc`, `bug`, `documentation`

### 週次レビュー
- 毎週金曜: 進捗確認
- 月次: ロードマップ見直し

---

## ❓ よくある質問

### Q1: v2.0.0正式版はいつリリース？
A: Issue #72完了後、1-2週間以内（Week 1終了目標）

### Q2: RFC実装の優先順位は？
A:
1. RFC-007 (Very High) - MCP Integration
2. RFC-006, 012, 014 (High)
3. RFC-002, 003 (バージョン指定済み)
4. その他（Medium）

### Q3: 途中でRFC追加される？
A: はい。`UNIFIED_ROADMAP.md`を随時更新します。

### Q4: v2.0.0でどの機能が使える？
A:
- ✅ `@agent` デコレータ
- ✅ Jinja2プロンプトテンプレート
- ✅ 型ベースパース（Pydantic対応）
- ✅ 安全なコード実行（CodeExecutor）
- ✅ CLI & REPL

---

## 🎬 今すぐやること

### 明日から着手
1. **Issue #72実装**: prompt_toolkit統合
2. **テスト実行**: REPL改善の動作確認
3. **ドキュメント更新**: REPL使用方法

### 今週中に完了
4. **v2.0.0リリース**: PyPI公開、GitHubリリース

### 来週から
5. **RFC-007着手**: MCP Integration設計・実装開始

---

## 📚 参考リンク

- [UNIFIED_ROADMAP.md](./UNIFIED_ROADMAP.md) - 全体ロードマップ（v2.0.0〜v2.5.0+）
- [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) - v2.0.0詳細
- [coding_standards.md](./coding_standards.md) - コーディング規約
- [GitHub Issues](https://github.com/JFK/kagura-ai/issues) - 全Issue一覧
- [RFC Documents](./rfcs/RFC_*.md) - 各RFC詳細仕様

---

**最優先タスク: Issue #72を今週中に完了させ、v2.0.0正式版をリリースする！**
