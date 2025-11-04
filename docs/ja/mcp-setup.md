# MCPセットアップガイド - Claude Desktop統合

> **2分でKaguraをClaude Desktopに接続**

このガイドでは、Model Context Protocol (MCP)を使用して、KaguraのユニバーサルメモリーシステムをClaude Desktopに統合する方法を説明します。

---

## 📋 前提条件

- Kagura AI v4.0+がインストール済み
- Claude Desktop (MCPをサポート)

---

## ⚡ 自動セットアップ (推奨)

Kaguraは自動的にClaude Desktopを設定できます:

```bash
# Kagura MCPサーバーをClaude Desktopにインストール
kagura mcp install
```

**出力**:
```
✅ Successfully installed!

Configuration:
  Server name: kagura-memory
  Command: kagura mcp serve
  Config file: ~/.config/claude/claude_desktop_config.json

Next steps:
  1. Restart Claude Desktop
  2. Start a new conversation
  3. Try: 'Remember that I prefer Python'
```

**これだけです!** KaguraがClaude Desktopに接続されました。

---

## 🔧 手動セットアップ (代替方法)

自動セットアップが機能しない場合は、設定ファイルを手動で編集できます。

### ステップ1: Claude Desktop設定ファイルの場所

**macOS/Linux**:
```
~/.config/claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### ステップ2: 設定の編集

`mcpServers`セクションにKaguraを追加します:

```json
{
  "mcpServers": {
    "kagura-memory": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

**完全な例**:
```json
{
  "mcpServers": {
    "kagura-memory": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {}
    },
    "other-server": {
      "command": "other-command",
      "args": ["serve"]
    }
  }
}
```

### ステップ3: Claude Desktopの再起動

Claude Desktopを閉じて再度開き、変更を適用します。

---

## ✅ 統合の確認

### 方法1: Claudeに質問する

Claude Desktopで新しい会話を開始して試してみてください:

> **あなた**: "Remember that I prefer Python over JavaScript for backend projects"

Claudeは`memory_store`ツールを使用してこれを保存します。

> **あなた**: "What programming languages do I prefer?"

Claudeは`memory_recall`または`memory_search`を使用して情報を取得します。

### 方法2: 診断を確認

```bash
kagura mcp doctor
```

次の表示を確認してください:
```
Claude Desktop │ ✅ configured │ Kagura MCP server configured
```

---

## 🧠 利用可能なメモリーツール

統合が完了すると、Claudeは以下のメモリーツールにアクセスできます:

### コアツール

| ツール | 目的 | 使用例 |
|------|---------|---------|
| **memory_store** | 情報を保存 | "Xを覚えて" |
| **memory_recall** | キーで取得 | "Yについて何を言った?" |
| **memory_search** | セマンティック検索 | "Zについてのメモリーを検索" |
| **memory_list** | すべてのメモリーをリスト | "私について何を覚えている?" |
| **memory_feedback** | 有用/古いとマーク | 自動 |
| **memory_delete** | 情報を削除 | "Xについて忘れて" |

### メモリースコープ

- **working**: 一時的、セッションのみ (デフォルト)
- **persistent**: ディスクに保存、再起動後も保持

### 使用例

**永続的なメモリーを保存**:
> "Remember that my favorite Python library is FastAPI. This is important and should be persistent."

**メモリーを検索**:
> "What do you know about my coding preferences?"

**フィードバック** (自動):
> Claudeは、質問に答えるのに役立った場合、自動的にメモリーを"useful"としてマークします。

**削除**:
> "Forget about my old JavaScript preference"

---

## 🔍 トラブルシューティング

### Claude DesktopがKaguraツールを認識しない

**確認1**: インストールを確認
```bash
kagura mcp doctor
```

**確認2**: Claude Desktopを再起動
- Claude Desktopを完全に終了
- 再度開く
- 新しい会話を開始

**確認3**: ログを確認
```bash
# Claude Desktopログ (macOS)
tail -f ~/Library/Logs/Claude/mcp*.log
```

### "kagura command not found"

**解決方法**: 設定でフルパスを使用

```json
{
  "mcpServers": {
    "kagura-memory": {
      "command": "/full/path/to/kagura",
      "args": ["mcp", "serve"]
    }
  }
}
```

フルパスを確認:
```bash
which kagura
# 出力: /home/user/.local/bin/kagura
```

### メモリーが会話をまたいで保持されない

**原因**: `scope="working"` (デフォルト)を使用

**解決方法**: 明示的に`scope="persistent"`を使用

またはClaudeに伝えます:
> "Remember this **permanently**: I prefer Python"

---

## 🚫 アンインストール

Claude DesktopからKaguraを削除するには:

```bash
kagura mcp uninstall
```

これにより設定は削除されますが、**保存されたメモリーは削除されません**。

---

## 🔗 関連

- [Getting Started](./getting-started.md) - インストールガイド
- [API Reference](./api-reference.md) - REST APIドキュメント
- [Architecture](./architecture.md) - システム設計

---

**バージョン**: 4.0.0a
**最終更新**: 2025-10-26
