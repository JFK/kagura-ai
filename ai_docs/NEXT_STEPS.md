# Kagura AI 2.0 - 次の開発ステップ

## 📊 現在の状態 (2025-10-03 更新)

### ✅ 完了済み
- ✅ Core engine (@agent decorator, prompt template, type parsing)
- ✅ Code execution (CodeExecutor, code agent)
- ✅ CLI framework & REPL (.env support, readline history)
- ✅ Integration tests (152 tests, 92% coverage)
- ✅ Documentation (MkDocs, 日英対応)
- ✅ Examples (4+ エージェント実装例)
- ✅ GitHub Issue Templates (Claude Code最適化済み)
- ✅ GitHub Actions (CI/CD, 自動テスト)
- ✅ **Beta Release (v2.0.0-beta.1)** - PyPI公開完了 🎉

### 📦 現在のバージョン
- **`2.0.0-beta.1`** (PyPI公開済み)
- インストール: `pip install kagura-ai==2.0.0b1`
- PyPI: https://pypi.org/project/kagura-ai/2.0.0b1/
- GitHub Release: https://github.com/JFK/kagura-ai/releases/tag/v2.0.0-beta.1

### 🧪 テスト状況
- ✅ CIパス (152 passed, 1 skipped)
- ✅ カバレッジ 92%
- ⚠️ 1テストスキップ中 (`test_infinite_loop_timeout` - pytest-asyncio cleanup issue)

---

## 🎯 次の優先タスク

### Phase 1: Beta安定化 (今週〜来週)

#### タスク1: テストカバレッジ向上（92% → 95%+）

**優先度**: 🟡 中

**内容**:
- 残り3%のカバレッジ向上
- スキップ中のテスト修正
- エッジケースの追加テスト

**Issue**: 作成予定

#### タスク2: Beta版フィードバック収集

**優先度**: 🟡 中

**内容**:
- GitHub Discussionsの設定
- Issueテンプレートにbeta-feedbackラベル追加
- READMEにフィードバック募集セクション追加

**Issue**: 作成予定

---

### Phase 2: 次期機能検討 (来週〜)

#### RFC #61: Memory & Workflow Features

**関連Issue**: https://github.com/JFK/kagura-ai/issues/61
**ステータス**: コミュニティフィードバック募集中
**対象バージョン**: v2.1.0 - v2.2.0

**提案機能**:
1. **メモリ機能**
   - `@memory.session` - セッション管理
   - `@memory.vector` - ベクトルDB統合

2. **ワークフロー機能**
   - `@workflow.chain` - 逐次実行
   - `@workflow.parallel` - 並列実行
   - `@workflow.stateful` - 状態管理（Pydanticベース）

3. **プラグインシステム**
   - `@tool` デコレータ
   - ツール自動選択

4. **パフォーマンス最適化**
   - `@cache` - レスポンスキャッシュ
   - `@batch` - バッチング
   - ストリーミング対応

**参考**: LangGraphの設計を参考にしつつ、Kagura AIのシンプルさを維持

#### RFC #62: Multimodal RAG Chat with Google Workspace

**関連Issue**: https://github.com/JFK/kagura-ai/issues/62
**ステータス**: コミュニティフィードバック募集中
**対象バージョン**: v2.1.0 - v2.2.0
**詳細ドキュメント**: `ai_docs/RFC_002_MULTIMODAL_RAG.md`

**提案機能**:
1. **マルチモーダル対応**
   - Gemini 1.5 Flash/Pro統合
   - 画像・音声・動画・PDF認識
   - `kagura chat` コマンド

2. **Google Workspace連携**
   - Google Drive API統合
   - Google Calendar API統合
   - Gmail API統合

3. **ハイブリッドツールシステム**
   - Kagura独自 `@tool` デコレータ（コア）
   - MCP互換レイヤー（オプション）

4. **日本語完全対応**
   - 日本語ネイティブな会話
   - 文字起こし・要約

**技術スタック**:
- Gemini 1.5 Flash/Pro (マルチモーダルAPI)
- Google Workspace APIs
- ChromaDB (ベクトルDB)
- MCP (Model Context Protocol) - オプション

---

### Phase 3: 正式版リリース準備 (1-2ヶ月後)

#### v2.0.0正式版リリース

**完了条件**:
- Beta版での重大バグ0件
- コミュニティフィードバック反映
- テストカバレッジ95%+
- ドキュメント完備

**目標時期**: 2025年11月中旬〜12月

---

## 📋 廃止予定のセクション（Phase 1は完了済み）

### ~~Phase 1: ドキュメント・品質改善 (Week 1-2)~~

✅ 完了済み（Issue #54, #55, #56完了）

#### Issue #1: ドキュメントの最終確認と改善

**タイトル**: `[DOC-004] Review and improve documentation for beta release`

**内容**:
```markdown
## 🎯 目的
Beta版リリースに向けたドキュメントの最終確認と改善

## 📂 スコープ境界
**許可パス**:
- `docs/`
- `README.md`
- `examples/*/README.md`
- `mkdocs.yml`

## 📋 Claude Code用タスク定義

### 1. ドキュメントレビュー
- [ ] `docs/index.md` - 最新情報への更新
- [ ] `docs/en/quickstart.md` - 動作確認
- [ ] `docs/en/tutorials/` - 全チュートリアルの検証
- [ ] `README.md` - バッジ追加、クイックスタート改善

### 2. サンプルコードの動作確認
- [ ] `examples/agents/` - 全サンプルの動作確認
- [ ] 各サンプルにRequirements追加

### 3. MkDocsの改善
- [ ] ナビゲーション構造の見直し
- [ ] コードブロックのシンタックスハイライト確認
- [ ] リンク切れチェック

## ✅ 完了条件
- [ ] 全ドキュメントレビュー完了
- [ ] リンク切れなし
- [ ] 全サンプルコード動作確認済み
- [ ] Draft PR作成
```

#### Issue #2: テストカバレッジ向上

**タイトル**: `[TEST-002] Improve test coverage to 95%+`

**内容**:
```markdown
## 🎯 目的
テストカバレッジを95%以上に向上

## 📂 スコープ境界
**許可パス**:
- `tests/`
- `.github/workflows/test.yml` (カバレッジレポート追加)

## 📋 Claude Code用タスク定義

### 1. カバレッジ分析
- [ ] 現在のカバレッジレポート生成
- [ ] カバーされていない箇所を特定
- [ ] 優先度付け (Core > CLI > Agents)

### 2. 不足テストの追加
- [ ] `src/kagura/core/` - エッジケース
- [ ] `src/kagura/cli/` - エラーハンドリング
- [ ] `src/kagura/agents/` - 複雑なシナリオ

### 3. テスト品質改善
- [ ] テストの可読性向上
- [ ] テストのドキュメント追加
- [ ] フィクスチャの整理

## ✅ 完了条件
- [ ] テストカバレッジ95%以上
- [ ] CI にカバレッジレポート追加
- [ ] Draft PR作成
```

---

### Phase 2: Beta版リリース準備 (Week 3-4)

#### Issue #3: Beta版への移行

**タイトル**: `[RELEASE-003] Prepare for beta release (v2.0.0-beta.1)`

**内容**:
```markdown
## 🎯 目的
Beta版リリースの準備

## 📂 スコープ境界
**許可パス**:
- `pyproject.toml`
- `CHANGELOG.md`
- `README.md`
- `.github/workflows/deploy_pypi.yml`

## 📋 Claude Code用タスク定義

### 1. バージョン更新
- [ ] `pyproject.toml` - version = "2.0.0-beta.1"
- [ ] `src/kagura/version.py` - 同期

### 2. CHANGELOG作成
- [ ] `CHANGELOG.md` の作成
- [ ] alpha版からの変更点を記載
- [ ] Breaking Changes の明記

### 3. README最終化
- [ ] インストール方法の確認
- [ ] バッジの更新 (PyPI, CI, Docs)
- [ ] クイックスタートの改善

### 4. PyPI準備
- [ ] `python -m build` でビルド確認
- [ ] TestPyPI へのアップロード確認
- [ ] インストールテスト

## ✅ 完了条件
- [ ] バージョン更新完了
- [ ] CHANGELOG作成
- [ ] TestPyPI で動作確認
- [ ] Draft PR作成
```

#### Issue #4: Beta版リリース

**タイトル**: `[RELEASE-004] Release v2.0.0-beta.1 to PyPI`

**内容**:
```markdown
## 🎯 目的
Beta版のPyPI公開

## 📋 Claude Code用タスク定義

### 1. 最終確認
- [ ] 全テストパス確認
- [ ] ドキュメントビルド確認
- [ ] バージョン番号確認

### 2. Git タグ作成
```bash
git tag -a v2.0.0-beta.1 -m "Release v2.0.0-beta.1"
git push origin v2.0.0-beta.1
```

### 3. GitHub Release作成
- [ ] リリースノート作成
- [ ] CHANGELOG.md からコピー
- [ ] Assets添付 (wheel, tar.gz)

### 4. PyPI公開
- [ ] `uv publish` で公開
- [ ] `pip install kagura-ai==2.0.0-beta.1` で確認

## ✅ 完了条件
- [ ] PyPI公開完了
- [ ] GitHub Release作成
- [ ] インストール・動作確認完了
```

---

### Phase 3: 機能拡張 (Week 5-8)

#### 検討中の機能

1. **メモリ機能** (`[FEAT-001] Add agent memory and context management`)
   - エージェント間でのコンテキスト共有
   - 会話履歴の保持
   - ベクトルDBとの統合 (optional)

2. **ワークフロー機能** (`[FEAT-002] Implement agent workflow orchestration`)
   - 複数エージェントの連携
   - DAG形式のワークフロー定義
   - エラーハンドリング・リトライ

3. **プラグインシステム** (`[FEAT-003] Create plugin system for extensions`)
   - カスタムツールの追加
   - サードパーティ統合
   - プラグインマネージャ

4. **パフォーマンス最適化** (`[PERF-001] Optimize LLM call batching and caching`)
   - LLM呼び出しのバッチング
   - レスポンスキャッシュ
   - ストリーミング対応

---

## 📝 Issue作成手順

### ステップ1: Issue作成

```bash
# GitHub CLIを使用
gh issue create \
  --title "[DOC-004] Review and improve documentation for beta release" \
  --label "documentation,claude-code" \
  --body-file ai_docs/NEXT_STEPS.md
```

または、GitHubのWeb UIから:
1. `Issues` → `New Issue`
2. テンプレート選択: `Claude Code - Development Task`
3. 上記の内容をコピペ

### ステップ2: Claude Codeで実行

```bash
claude code
# プロンプト: "GitHub Issue #XX を読み込んで実行してください"
```

### ステップ3: レビュー・マージ

```bash
# Draft PR確認
gh pr list

# CIステータス確認
gh pr checks [PR番号]

# Ready for reviewに変更
gh pr ready [PR番号]

# マージ
gh pr merge [PR番号] --squash
```

---

## 🎯 マイルストーン

### M1: Beta準備完了 (Week 1-2)
- [ ] Issue #1: ドキュメント改善
- [ ] Issue #2: テストカバレッジ向上

### M2: Beta版リリース (Week 3-4)
- [ ] Issue #3: Beta版準備
- [ ] Issue #4: PyPI公開

### M3: 機能拡張検討 (Week 5-8)
- [ ] コミュニティフィードバック収集
- [ ] 次期バージョンの機能決定
- [ ] RFC発行・議論

---

## 📊 成功指標

### Beta版リリース時
- [ ] PyPI公開完了
- [ ] テストカバレッジ95%以上
- [ ] ドキュメント完備
- [ ] 全サンプルコード動作確認済み
- [ ] CI/CDパイプライン完全動作

### 正式版 (v2.0.0) リリース時
- [ ] Beta版での問題修正完了
- [ ] コミュニティフィードバック反映
- [ ] パフォーマンス最適化完了
- [ ] 10+ Star on GitHub
- [ ] 100+ PyPI downloads

---

## 🚀 今すぐ始める

### 推奨する開始順序

1. **今日**: Issue #1 (ドキュメント改善) を作成・実行
2. **明日**: Issue #2 (テストカバレッジ) を作成・実行
3. **来週**: Issue #3, #4 (Beta版リリース)

### コマンド例

```bash
# Issue #1 作成
gh issue create \
  --title "[DOC-004] Review and improve documentation for beta release" \
  --label "documentation,claude-code" \
  --body "$(cat <<'EOF'
## 🎯 目的
Beta版リリースに向けたドキュメントの最終確認と改善

## 📂 スコープ境界
**許可パス**:
- docs/
- README.md
- examples/*/README.md

## 📋 Claude Code用タスク定義

1. ドキュメントレビュー
2. サンプルコード動作確認
3. MkDocs改善

## ✅ 完了条件
- [ ] 全ドキュメントレビュー完了
- [ ] リンク切れなし
- [ ] Draft PR作成
EOF
)"

# Claude Codeで実行
claude code
# "GitHub Issue #XX を読み込んで実行してください"
```

---

## 参考資料

- [Issue-Driven AI Development実践ガイド](https://qiita.com/kiyotaman/items/87a5a9ddc88db64f78ac)
- [Claude Code公式ドキュメント](https://docs.claude.com/en/docs/claude-code)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
