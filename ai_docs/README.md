# AI Development Docs

Kagura AI v3.0開発用のドキュメント。Claude Codeが参照します。

---

## 📂 ディレクトリ構成

```
ai_docs/
├── README.md                    # このファイル
│
├── V3.0_DEVELOPMENT.md          # v3.0開発ガイド ⭐️
├── V3.0_PIVOT.md                # v3.0方針転換
├── V3.0_WORK_LOG.md             # v3.0作業ログ
├── ROADMAP_v3.md                # v3.0ロードマップ
├── VISION.md                    # プロジェクトビジョン
│
├── coding_standards.md          # コーディング規約
├── architecture.md              # システムアーキテクチャ
├── glossary.md                  # 用語集
├── github_actions_setup.md      # CI/CD設定
├── OPENAI_PRICING.md            # LLM価格情報
│
├── rfcs/                        # RFC仕様書
│   ├── README.md
│   ├── RFC_005_META_AGENT.md
│   ├── RFC_033_CHAT_ENHANCEMENT.md
│   ├── RFC_034_URL_MULTIMODAL_ANALYSIS.md
│   ├── archive/completed/       # 完了RFC
│   └── future/                  # 将来RFC
│
├── archive/                     # アーカイブ
│   ├── guides/                  # 古いガイド
│   ├── analysis_old/            # 古い分析
│   ├── completed/               # 完了RFC Plans
│   ├── old_versions/            # 旧バージョンdocs
│   └── work_logs/               # 過去のログ
│
└── work_logs/                   # 作業ログ
    └── 2025-10-*.md
```

---

## 🚨 Claude Code必読

### 作業前の必須確認

1. **V3.0_DEVELOPMENT.md** ⭐️ - v3.0開発ガイド
2. **ROADMAP_v3.md** - v3.0ロードマップ
3. **V3.0_PIVOT.md** - v3.0方針（SDK-first）
4. **coding_standards.md** - コーディング規約
5. **対象Issueの内容**（完全理解）

### v3.0開発原則

**SDK軸**:
- Python開発者がアプリに組み込むSDK
- 型安全、テスト可能、Production-ready

**Chat（ボーナス）**:
- SDK機能を手軽に試せる
- プロトタイピング・実験用

### 禁止事項

- ❌ mainブランチへの直接コミット
- ❌ テストなしでのコード変更
- ❌ 推測での実装（不明点は質問）

---

## 📋 主要ドキュメント

### v3.0開発（最重要）

- **V3.0_DEVELOPMENT.md**: v3.0実践ガイド
- **ROADMAP_v3.md**: v3.0ロードマップ
- **V3.0_PIVOT.md**: SDK-first方針転換
- **V3.0_WORK_LOG.md**: v3.0作業ログ

### プロジェクト基盤

- **VISION.md**: プロジェクトビジョン
- **coding_standards.md**: コーディング規約
- **architecture.md**: システム設計
- **glossary.md**: 用語集

### アーカイブ（参考用）

- **ROADMAP_v2.5_ARCHIVE.md**: v2.5ロードマップ
- **NEXT_STEPS_v2.5_ARCHIVE.md**: v2.5次ステップ
- **archive/**: 完了RFC、旧版docs

---

## 📚 RFC管理

### アクティブRFC（v3.0）

- **RFC-005**: Meta Agent
- **RFC-033**: Chat Enhancement
- **RFC-034**: URL Multimodal Analysis

### 完了RFC

`rfcs/archive/completed/`参照
- RFC-002, 006, 007, 012, 013, 014, 016〜022, 024, 027〜032

### 将来RFC

`rfcs/future/`参照
- RFC-003, 004, 008〜011, 015, 023, 025, 026, 029, 036

---

## 🔄 ファイルライフサイクル

### RFC Phase Plan

1. RFC作成: `rfcs/RFC_XXX.md`
2. Phase Plan: `rfcs/RFC_XXX_PHASEXX_PLAN.md`
3. PR完了後: `archive/completed/`へ移動
4. Main RFC: `rfcs/`に永続保持

### Work Log

1. 日次: `WORK_LOG_YYYY-MM-DD.md`
2. 週次: `archive/work_logs/`へ移動
3. 最新: rootに1つのみ

---

## ✅ メンテナンスルール

### Rootに保持（15ファイル程度）

- v3.0開発docs（4個）
- プロジェクト基盤（5個）
- 技術ガイド（3個）
- 最新ログ（1個）
- アーカイブ参照（2個）

### Archive行き

- 完了RFC Plans/Results
- 旧バージョンdocs
- 古いwork logs
- 古いanalysis/guides

---

**Last Updated**: 2025-10-19 (v3.0)
**Maintained By**: Claude Code + Human developers
