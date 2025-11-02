# MCPセットアップガイド - Claude Code統合

> **2分でKaguraをClaude Codeに接続**

このガイドでは、Model Context Protocol (MCP)を使用して、KaguraのユニバーサルメモリーとClaude Code（Anthropic公式CLI）を統合する方法を説明します。

---

## 📋 前提条件

- Kagura AI v4.0+がインストールされていること
- Claude Code CLI（Anthropic公式CLIツール）

---

## ⚡ クイックセットアップ

### ステップ1: Kaguraをインストール

```bash
# 全依存関係を含めてインストール
pip install kagura-ai[full]

# またはソースからインストール
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --all-extras
```

### ステップ2: Claude CodeにMCPサーバーを追加

```bash
# KaguraをMCPサーバーとして追加
claude mcp add --transport stdio kagura -- kagura mcp serve
```

**出力**:
```
Added stdio MCP server kagura with command: kagura mcp serve to local config
File modified: /home/user/.claude.json
```

### ステップ3: 接続を確認

```bash
# MCPサーバーのステータスを確認
claude mcp list
```

**期待される出力**:
```
Checking MCP server health...

kagura: kagura mcp serve - ✓ Connected
```

**完了！** KaguraがClaude Codeに接続されました。

---

## 🧠 利用可能なツール

統合が完了すると、Claude Codeは以下のカテゴリーに分類された **31個のMCPツール** にアクセスできます:

### コアメモリーツール (4)

| ツール | 目的 | 使用例 |
|------|---------|---------------|
| `memory_store` | 情報を保存 | "私はPythonを好むことを覚えておいて" |
| `memory_recall` | キーで取得 | "私のPython好みは何？" |
| `memory_search` | セマンティック検索 | "コーディングに関するメモリーを検索" |
| `memory_delete` | メモリーを削除 | "Xについて忘れて" |

### ナレッジグラフツール (3)

| ツール | 目的 |
|------|---------|
| `graph_add_node` | 概念を追加 |
| `graph_link` | メモリーを接続 |
| `graph_query` | マルチホップトラバーサル |

### 検索ツール (6)

| ツール | 目的 |
|------|---------|
| `search_memories` | ハイブリッド検索（BM25 + ベクトル） |
| `search_brave` | Brave API経由のWeb検索 |
| `search_arxiv` | 学術論文 |
| ... | ... |

### コーディングツール (14)

| ツール | 目的 |
|------|---------|
| `coding_store_file_change` | ファイル変更を追跡 |
| `coding_store_error` | エラーを記録 |
| `coding_store_design_decision` | 設計決定を文書化 |
| `coding_summary` | AI駆動のセッションサマリー |
| ... | ... |

### GitHubツール (6)

| ツール | 目的 |
|------|---------|
| `github_shell_exec` | 安全なシェル実行 |
| `github_issue_*` | Issue操作 |
| `github_pr_*` | PR管理 |

**完全なリスト**: `kagura mcp tools`を実行して、全31ツールを確認できます。

---

## 🎯 使用例

### 基本的なメモリー操作

**メモリーを保存**:
```
ユーザー: バックエンドプロジェクトではJavaScriptよりPythonを好むことを覚えておいて
Claude: [memory_storeツールを使用]
```

**メモリーを呼び出し**:
```
ユーザー: 私が好むプログラミング言語は何？
Claude: [memory_recall/searchを使用して情報を取得]
```

### ナレッジグラフ

**関連するメモリーをリンク**:
```
ユーザー: 私のPython好みとFastAPIの知識を接続して
Claude: [graph_linkを使用して関係を作成]
```

**関連する概念を検索**:
```
ユーザー: 私のコーディング好みに関連するものは何？
Claude: [graph_queryを使用してマルチホップトラバーサル]
```

### コーディングセッション

**ファイル変更を追跡**:
```
Claude: [ファイル編集時にcoding_store_file_changeを自動使用]
```

**セッションをサマライズ**:
```
ユーザー: 今日達成したことをまとめて
Claude: [coding_summaryを使用してセッション履歴を分析]
```

---

## 🔧 高度な設定

### リモートモード（安全なツールのみ）

リモートKagura APIに接続する場合:

```bash
# リモート接続を設定
kagura mcp connect

# リモートMCPサーバーを追加
claude mcp add --transport stdio kagura-remote -- kagura mcp serve --remote
```

### カスタムサーバー名

```bash
# カスタム名を使用
claude mcp add --transport stdio my-kagura -- kagura mcp serve --name my-kagura
```

### 環境変数

オプション機能用のAPIキーを追加:

```bash
# 環境変数と共に追加
claude mcp add --transport stdio kagura \
  --env OPENAI_API_KEY=sk-... \
  --env BRAVE_API_KEY=... \
  -- kagura mcp serve
```

---

## 🔍 トラブルシューティング

### "kagura command not found"

**解決策**: フルパスを使用

```bash
# kaguraのパスを検索
which kagura
# 出力: /home/user/.local/bin/kagura

# フルパスで追加
claude mcp add --transport stdio kagura -- /home/user/.local/bin/kagura mcp serve
```

### 設定を確認

**現在の設定を表示**:
```bash
claude mcp get kagura
```

**ログを確認**:
```bash
# Kagura MCPサーバーログ
kagura mcp log
```

### 削除して再追加

```bash
# 削除
claude mcp remove kagura

# 再追加
claude mcp add --transport stdio kagura -- kagura mcp serve
```

---

## 📊 監視

### ツール使用統計を表示

```bash
kagura mcp stats
```

**出力例**:
```
MCP Tool Usage Statistics
─────────────────────────────────────────────────
Total calls: 156

Top tools:
  memory_store: 45 calls
  memory_search: 32 calls
  coding_store_file_change: 28 calls
  graph_link: 15 calls
```

### サーバーログを表示

```bash
# リアルタイムログ
kagura mcp log --tail

# 最新100行
kagura mcp log --lines 100
```

---

## 🚫 アンインストール

Claude CodeからKaguraを削除するには:

```bash
claude mcp remove kagura
```

これにより設定は削除されますが、**保存されたメモリーは削除されません**。

メモリーを削除する場合:
```bash
# まずエクスポート（バックアップ）
kagura memory export --output=./backup

# 全メモリーをクリア
rm -rf ~/.local/share/kagura/
rm -rf ~/.cache/kagura/
```

---

## 🔗 関連ドキュメント

- [MCPセットアップ (Claude Desktop)](./mcp-setup.md) - Claude Desktop統合
- [MCP over HTTP/SSE](./mcp-http-setup.md) - リモートMCPセットアップ
- [はじめに](./getting-started.md) - インストールガイド
- [APIリファレンス](./api-reference.md) - REST APIドキュメント

---

## 📚 追加リソース

### Claude Codeドキュメント
- [Claude Code公式ドキュメント](https://docs.claude.com/en/docs/claude-code)
- [MCPプロトコル](https://modelcontextprotocol.io/)

### Kaguraドキュメント
- [GitHubリポジトリ](https://github.com/JFK/kagura-ai)
- [PyPIパッケージ](https://pypi.org/project/kagura-ai/)

---

**バージョン**: 4.0.0
**最終更新**: 2025-11-02
