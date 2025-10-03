# [SETUP-001] Clean up legacy code and close old issues

## 🎯 目的

Kagura AI 2.0開発のための環境整備。既存のレガシーコードを整理し、新規開発のためのクリーンな状態を作る。

## 📑 出力契約(Claude必読)

- すべてMarkdownで出力
- 各ステップ終了時に作業ログを記録
- エラー/不明点は質問節で停止(自己判断で進めない)

## 📂 スコープ境界

**許可パス**:
- `.github/ISSUE_TEMPLATE/` (既存Issueクローズのみ)
- `src/kagura/` → `src/kagura_legacy/` (移動)
- ブランチ作成
- `pyproject.toml` (バージョン更新のみ)

**禁止パス**:
- `ai_docs/` (変更不可)
- `.github/workflows/` (CI設定変更不可)
- `tests/` (まだ触らない)

## 🛡️ 安全弁

- **Draft PR**で作成すること
- ブランチ名: `feature/SETUP-001-cleanup`
- 既存コードは削除せず移動のみ

## 📋 Claude Code用タスク定義

### ステップ1: 既存Issueのクローズ

1. GitHub CLI で既存Issue (#1-8) をクローズ
   ```bash
   gh issue close 1 -c "Superseded by Kagura AI 2.0 redesign (see ai_docs/DEVELOPMENT_ROADMAP.md)"
   gh issue close 5 -c "Superseded by Kagura AI 2.0 redesign (see ai_docs/DEVELOPMENT_ROADMAP.md)"
   gh issue close 6 -c "Superseded by Kagura AI 2.0 redesign (see ai_docs/DEVELOPMENT_ROADMAP.md)"
   gh issue close 7 -c "Superseded by Kagura AI 2.0 redesign (see ai_docs/DEVELOPMENT_ROADMAP.md)"
   gh issue close 8 -c "Superseded by Kagura AI 2.0 redesign (see ai_docs/DEVELOPMENT_ROADMAP.md)"
   ```

### ステップ2: ブランチ作成

2. 開発ブランチを作成
   ```bash
   git checkout -b feature/SETUP-001-cleanup
   ```

### ステップ3: レガシーコードの移動

3. 既存のsrc/kaguraをlegacyに移動
   ```bash
   mv src/kagura src/kagura_legacy
   ```

4. 新しいディレクトリ構造を作成
   ```bash
   mkdir -p src/kagura
   ```

5. 最小限の`src/kagura/__init__.py`を作成
   ```python
   """
   Kagura AI 2.0 - Python-First AI Agent Framework

   Example:
       from kagura import agent

       @agent
       async def hello(name: str) -> str:
           '''Say hello to {{ name }}'''
           pass

       result = await hello("World")
   """
   __version__ = "2.0.0-alpha.1"
   ```

### ステップ4: pyproject.tomlの更新

6. `pyproject.toml`のバージョンを更新
   ```toml
   [project]
   name = "kagura-ai"
   version = "2.0.0-alpha.1"
   description = "Python-First AI Agent Framework with Code Execution"
   ```

7. 変更をコミット
   ```bash
   git add src/kagura src/kagura_legacy pyproject.toml
   git commit -m "chore(setup): prepare for v2.0 development (#SETUP-001)

   - Move legacy code to src/kagura_legacy/
   - Create new src/kagura/ structure
   - Update version to 2.0.0-alpha.1"
   ```

### ステップ5: Draft PR作成

8. Draft PRを作成
   ```bash
   gh pr create --draft --title "[SETUP-001] Clean up legacy code and close old issues" \
     --body "## Summary

   Prepare repository for Kagura AI 2.0 development:

   - ✅ Closed legacy issues (#1, #5, #6, #7, #8)
   - ✅ Moved existing code to \`src/kagura_legacy/\`
   - ✅ Created new \`src/kagura/\` structure
   - ✅ Updated version to 2.0.0-alpha.1

   ## Next Steps

   - Issue #SETUP-002: Create minimal project structure

   ## Related

   - See: \`ai_docs/DEVELOPMENT_ROADMAP.md\`"
   ```

### ステップ6: 作業ログ記録

9. このIssueに作業ログをコメント
   ```markdown
   ## 作業ログ

   ### 実施内容
   - 既存Issue 5件をクローズ
   - レガシーコード移動: src/kagura → src/kagura_legacy
   - 新ディレクトリ作成: src/kagura
   - pyproject.toml更新: version → 2.0.0-alpha.1

   ### 変更ファイル数
   - 移動: ~34 files (全てのPythonファイル)
   - 新規作成: 1 file (src/kagura/__init__.py)
   - 更新: 1 file (pyproject.toml)

   ### 発見した問題点
   - なし

   ### 次のステップ
   - Issue #SETUP-002: プロジェクト構造の作成
   ```

## 🧾 コミット規約

```
chore(setup): <変更内容> (#SETUP-001)
```

例:
```
chore(setup): move legacy code to kagura_legacy (#SETUP-001)
chore(setup): update version to 2.0.0-alpha.1 (#SETUP-001)
```

## ⚠️ 制約・注意事項

- [ ] レガシーコードは**削除せず移動**のみ
- [ ] 既存のCIは壊さない(pyproject.tomlの変更は最小限)
- [ ] ai_docs/は変更しない
- [ ] tests/はまだ触らない

## 📚 参考資料

- `ai_docs/DEVELOPMENT_ROADMAP.md` - 開発ロードマップ
- `ai_docs/coding_standards.md` - コーディング規約

## ✅ 完了条件

- [ ] 既存Issue (#1, #5, #6, #7, #8) 全てクローズ
- [ ] レガシーコード移動完了 (src/kagura → src/kagura_legacy)
- [ ] 新しいsrc/kagura/__init__.py作成
- [ ] pyproject.toml version更新 (2.0.0-alpha.1)
- [ ] ブランチ `feature/SETUP-001-cleanup` 作成
- [ ] Draft PR作成完了
- [ ] 作業ログ記録完了
- [ ] `uv sync` が成功(エラーなし)
