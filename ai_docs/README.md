# AI Docs

このディレクトリは、Claude Codeがタスクを実行する際に参照するドキュメントを格納します。

---

## 📂 ディレクトリ構成

```
ai_docs/
├── README.md                  # このファイル
├── UNIFIED_ROADMAP.md         # 統合開発ロードマップ（v2.0.0〜v2.5.0+）⭐️
├── DEVELOPMENT_ROADMAP.md     # v2.0.0詳細ロードマップ
├── NEXT_STEPS.md              # 次のアクション（優先タスク）
├── architecture.md            # システムアーキテクチャ概要
├── coding_standards.md        # コーディング規約
├── glossary.md                # 用語集・略語集
│
├── rfcs/                      # RFC（Request for Comments）
│   ├── RFC_002_MULTIMODAL_RAG.md
│   ├── RFC_003_PERSONAL_ASSISTANT.md
│   ├── RFC_004_VOICE_FIRST_INTERFACE.md
│   ├── RFC_005_META_AGENT.md
│   ├── RFC_006_LIVE_CODING.md
│   ├── RFC_007_MCP_INTEGRATION.md
│   ├── RFC_008_PLUGIN_MARKETPLACE.md
│   ├── RFC_009_MULTI_AGENT_ORCHESTRATION.md
│   ├── RFC_010_OBSERVABILITY.md
│   ├── RFC_011_SCHEDULED_AUTOMATION.md
│   ├── RFC_012_COMMANDS_AND_HOOKS.md
│   ├── RFC_013_OAUTH2_AUTH.md
│   ├── RFC_014_WEB_INTEGRATION.md
│   └── RFC_015_AGENT_API_SERVER.md
│
├── analysis/                  # 調査レポート
├── suggestions/               # Claudeからの技術的提案
└── fixes/                     # バグ修正の詳細記録
```

---

## 🚨 Claude Code必読ルール

### 作業前の必須確認（必ず読むこと）

1. **`UNIFIED_ROADMAP.md`** ⭐️ - 全体ロードマップを確認
   - v2.0.0〜v2.5.0+の計画
   - RFC優先順位（Very High/High/Medium）
   - 現在のバージョン確認

2. **`NEXT_STEPS.md`** - 今すぐやるべきことを確認
   - 優先アクション（1-2週間）
   - 短期・中期・長期目標
   - よくある質問

3. **`DEVELOPMENT_ROADMAP.md`** - v2.0.0詳細計画
   - Phase 0〜5の詳細
   - Issue作成テンプレート

4. **`coding_standards.md`** - コーディング規約
   - 命名規則
   - 型ヒント規約
   - ドキュメンテーション

5. **対象Issueの内容**（完全理解）

6. **該当するRFC**（機能実装時）
   - `rfcs/RFC_XXX_*.md`

### 作業中の原則

- すべての変更は**Draft PR**で作成
- 不明点があれば**必ず質問**して停止（推測で進めない）
- コミットは**Conventional Commits**形式
- 10ファイル/500行超える場合は分割コミット
- **TDD（テスト駆動開発）**: 実装前にテストを書く

### 禁止事項（NEVER）

- ❌ 推測での実装（不明点は必ず質問）
- ❌ mainブランチへの直接コミット
- ❌ テストなしでのコード変更
- ❌ レガシーコード（`src/kagura_legacy/`）の変更
- ❌ `examples/`、`docs/`の変更（Phase 4まで）

---

## 📋 コミットメッセージ形式

Conventional Commitsに従う：

```
<type>(<scope>): <subject> (#issue-number)

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Type
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `docs`: ドキュメント
- `chore`: ビルド、設定変更

### Scope
- `core`: コアエンジン
- `executor`: コード実行
- `cli`: CLI
- `agents`: エージェント
- `ai_docs`: 開発ドキュメント

### 例
```
feat(core): implement @agent decorator (#20)
fix(executor): prevent import bypass (#21)
test(cli): add REPL command tests (#27)
docs(rfcs): add RFC-007 MCP Integration (#67)
```

---

## 🎯 作業完了時のチェックリスト

- [ ] 型チェック（pyright）がパス
- [ ] 全テストがパス（pytest）
- [ ] リント（ruff）がパス
- [ ] カバレッジ90%以上
- [ ] Draft PR作成
- [ ] Issueにコメントで進捗報告

---

## 📚 ドキュメント参照ガイド

### v2.0.0実装中（現在）
1. `NEXT_STEPS.md` - 今すぐやること
2. `DEVELOPMENT_ROADMAP.md` - v2.0.0詳細
3. `coding_standards.md` - コーディング規約

### v2.1.0以降の計画確認
1. `UNIFIED_ROADMAP.md` - 全体ロードマップ
2. `rfcs/RFC_007_MCP_INTEGRATION.md` - MCP統合（Very High）
3. `rfcs/RFC_006_LIVE_CODING.md` - Chat REPL（High）

### 技術仕様確認
1. `architecture.md` - システムアーキテクチャ
2. `glossary.md` - 用語集

---

## 📝 ファイル命名規則

Issue番号を含むファイル名で管理：

- `analysis/123-feature-investigation.md`
- `suggestions/456-performance-optimization.md`
- `fixes/789-auth-bug-fix.md`

---

## 🗂️ RFCディレクトリ

`rfcs/`配下に全てのRFC（Request for Comments）を格納：

| RFC | タイトル | 優先度 | バージョン |
|-----|---------|--------|-----------|
| 002 | Multimodal RAG | - | v2.2.0 |
| 003 | Personal Assistant | - | v2.3.0 |
| 004 | Voice First Interface | Medium | v2.5.0+ |
| 005 | Meta Agent | High | v2.4.0 |
| 006 | Live Coding | High | v2.1.0/v2.5.0 |
| 007 | MCP Integration | **Very High** | v2.1.0 |
| 008 | Plugin Marketplace | High | v2.4.0 |
| 009 | Multi-Agent Orchestration | Medium-High | v2.4.0 |
| 010 | Observability | Medium | v2.5.0+ |
| 011 | Scheduled Automation | Medium | v2.5.0+ |
| 012 | Commands & Hooks | High | v2.1.0 |
| 013 | OAuth2 Auth | Medium-High | v2.3.0 |
| 014 | Web Integration | High | v2.2.0 |
| 015 | Agent API Server | High | v2.6.0 |

詳細は`UNIFIED_ROADMAP.md`を参照。

---

## 🔗 関連リンク

- [CLAUDE.md](../CLAUDE.md) - Claude Code開発ガイド（プロジェクトルート）
- [README.md](../README.md) - プロジェクト紹介
- [pyproject.toml](../pyproject.toml) - プロジェクト設定

---

**このドキュメントを読んでから作業を開始してください。不明点があれば必ず質問してください！**
