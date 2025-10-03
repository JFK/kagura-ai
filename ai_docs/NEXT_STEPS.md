# Kagura AI 2.0 - 次の開発ステップ

## 📊 現在の状態 (2025-10-03)

### ✅ 完了済み
- ✅ Core engine (@agent decorator, prompt template, type parsing)
- ✅ Code execution (CodeExecutor, code agent)
- ✅ CLI framework & REPL
- ✅ Integration tests
- ✅ Documentation (MkDocs)
- ✅ Examples
- ✅ GitHub Issue Templates (Claude Code最適化済み)
- ✅ GitHub Actions (CI/CD)

### 📦 現在のバージョン
- `2.0.0-alpha.1`

### 🧪 テスト状況
- ✅ CIパス (全テスト完了)
- ⚠️ 1テストスキップ中 (`test_infinite_loop_timeout` - pytest-asyncio cleanup issue)

---

## 🎯 次の優先タスク

### Phase 1: ドキュメント・品質改善 (Week 1-2)

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
