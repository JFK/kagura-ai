# AI Docs 管理ガイドライン

v3.0開発ドキュメントの管理ルール。

---

## 📂 ディレクトリ構造

### Root（13-15ファイル）- アクティブドキュメントのみ

```
ai_docs/
├── README.md                    # このディレクトリのガイド
│
├── ROADMAP_v3.md                # v3.0ロードマップ
├── V3.0_DEVELOPMENT.md          # v3.0開発ガイド
├── V3.0_PIVOT.md                # v3.0方針転換
├── V3.0_WORK_LOG.md             # v3.0作業ログ（現在進行中）
├── VISION.md                    # プロジェクトビジョン
│
├── coding_standards.md          # コーディング規約
├── architecture.md              # システムアーキテクチャ
├── glossary.md                  # 用語集
├── github_actions_setup.md      # CI/CD設定
├── OPENAI_PRICING.md            # LLM価格（参照用）
```

### rfcs/（アクティブRFCのみ）

```
rfcs/
├── README.md                    # RFC管理ガイド
├── RFC_005_META_AGENT.md        # アクティブRFC
├── RFC_033_CHAT_ENHANCEMENT.md  # アクティブRFC
└── future/                      # 将来実装予定RFC
    ├── RFC_003_*.md
    ├── RFC_004_*.md
    └── ...
```

### archive/（完了・廃止ドキュメント）

```
archive/
├── ROADMAP_v2.5_ARCHIVE.md      # v2.5ロードマップ
├── NEXT_STEPS_v2.5_ARCHIVE.md   # v2.5次ステップ
├── USE_CASES_AND_FUTURE.md      # 古いユースケース
│
├── rfcs/completed/              # 完了RFC（Phase Plans含む）
│   ├── RFC_002_*.md
│   ├── RFC_005_PHASE1_PLAN.md
│   └── ...
│
├── guides/                      # 古いガイド
│   ├── MCP_SETUP_GUIDE.md
│   └── ...
│
├── analysis_old/                # 古い分析レポート
├── old_versions/                # 旧バージョンdocs
└── work_logs/                   # 過去の作業ログ
    └── 2025-10-*.md
```

---

## 📋 ファイル管理ルール

### 1. Root直下に置くもの

**アクティブな開発ドキュメントのみ**:
- ✅ 現在バージョン（v3.0）の開発ドキュメント
- ✅ バージョン非依存の技術ドキュメント（coding_standards等）
- ✅ 現在進行中のwork log（1ファイルのみ）

**置かないもの**:
- ❌ 完了したPhase Plans/Results
- ❌ 旧バージョンのロードマップ
- ❌ 古いwork logs
- ❌ 完了したRFC

### 2. rfcs/直下に置くもの

**アクティブRFCのみ**:
- ✅ 現在実装中のRFC（RFC-005, RFC-033）
- ✅ 次バージョン候補のRFC

**rfcs/future/**:
- ✅ 将来実装予定のRFC
- ✅ v3.1+で検討するRFC

**置かないもの**:
- ❌ 完了したRFC（archive/rfcs/completed/へ）
- ❌ Phase Plans（完了後はarchive/へ）

### 3. archive/に移動するもの

**即座に移動**:
- ✅ PR完了後のPhase Plans/Results
- ✅ Issue完了後のImplementation Plans
- ✅ 完了したRFC仕様書

**定期的に移動（月次）**:
- ✅ 古いwork logs（1週間以上前）
- ✅ 旧バージョンのドキュメント

---

## 🔄 ライフサイクル

### RFCドキュメント

```
1. RFC作成
   rfcs/RFC_XXX_TITLE.md

2. Phase Plan作成（実装中）
   rfcs/RFC_XXX_PHASEXX_PLAN.md

3. PR完了
   → archive/rfcs/completed/RFC_XXX_PHASEXX_PLAN.md

4. RFC完了
   → archive/rfcs/completed/RFC_XXX_TITLE.md
```

### Work Logs

```
1. 日次作成（v3.0進行中）
   V3.0_WORK_LOG.md（rootで継続更新）

2. 他のwork log
   → archive/work_logs/に即移動

3. v3.0完了時
   V3.0_WORK_LOG.md → archive/work_logs/
```

### Version Roadmaps

```
1. アクティブ版
   ROADMAP_v3.md（root）

2. v3.0完了後
   ROADMAP_v3.md → ROADMAP_v3_ARCHIVE.md → archive/

3. v4.0開始
   ROADMAP_v4.md作成（root）
```

---

## ✅ メンテナンス作業

### 週次（毎週金曜）

```bash
# 古いwork logsを移動
git mv ai_docs/work_logs/2025-10-*.md ai_docs/archive/work_logs/

# Root file数確認（15個以下が目標）
ls ai_docs/*.md | wc -l
```

### PR完了時

```bash
# Phase Planをarchiveに移動
git mv ai_docs/rfcs/RFC_XXX_PHASEXX_PLAN.md ai_docs/archive/rfcs/completed/
```

### バージョンリリース時

```bash
# 旧バージョンドキュメントをarchive
git mv ai_docs/ROADMAP_v2.md ai_docs/archive/ROADMAP_v2_ARCHIVE.md
git mv ai_docs/V2.0_*.md ai_docs/archive/old_versions/
```

---

## 🎯 目標

### Rootは常にクリーン

- **13-15ファイル**に維持
- v3.0フォーカス
- すぐ見つかる

### Archive は整理

- カテゴリ別に分類
- 検索可能
- 参照時に便利

### RFCは明確

- アクティブRFC: rfcs/直下（2-3個）
- 将来RFC: rfcs/future/
- 完了RFC: archive/rfcs/completed/

---

## 📝 命名規則

### Work Logs

```
# v3.0進行中（root）
V3.0_WORK_LOG.md

# 日次ログ（即archive）
2025-10-19_feature_name.md → archive/work_logs/

# v3.0完了後
V3.0_WORK_LOG.md → archive/work_logs/
```

### RFC Phase Plans

```
# アクティブ（開発中のみrfcs/）
rfcs/RFC_XXX_PHASEXX_PLAN.md

# 完了後（即移動）
archive/rfcs/completed/RFC_XXX_PHASEXX_PLAN.md
```

### Version Docs

```
# アクティブ（root）
ROADMAP_v3.md
V3.0_DEVELOPMENT.md

# アーカイブ（完了後）
archive/ROADMAP_v3_ARCHIVE.md
archive/old_versions/V3.0_*.md
```

---

## 🚨 禁止事項

- ❌ Root に10個以上のwork logs
- ❌ rfcs/に完了したRFC
- ❌ Root に旧バージョンdocs
- ❌ 2つのarchive階層（`archive/`と`rfcs/archive/`）

---

## ✨ ベストプラクティス

### 1. PR完了時は即清掃

```bash
# PR #XXXマージ後
git mv ai_docs/rfcs/RFC_YYY_PHASE1_PLAN.md ai_docs/archive/rfcs/completed/
```

### 2. Root fileは15個以下

```bash
# チェック
ls ai_docs/*.md | wc -l

# 15個超えたら整理
```

### 3. アクティブRFCは2-3個

```bash
# チェック
ls ai_docs/rfcs/RFC_*.md | wc -l

# 多すぎる場合はfuture/かarchive/へ
```

---

**Last Updated**: 2025-10-19
**Version**: v3.0
