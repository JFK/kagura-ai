# MCP Setup Guide - MCPメモリーサーバーとClaude設定ガイド

**最終更新**: 2025-10-04
**対象バージョン**: Kagura AI v2.0.0+
**関連RFC**: RFC-007 (MCP Integration)

---

## 📖 目次

1. [MCPとは](#mcpとは)
2. [MCPメモリーサーバーの設定](#mcpメモリーサーバーの設定)
3. [Claude Code MCP設定](#claude-code-mcp設定)
4. [Kagura AI との統合](#kagura-ai-との統合)
5. [トラブルシューティング](#トラブルシューティング)
6. [ベストプラクティス](#ベストプラクティス)

---

## MCPとは

**Model Context Protocol (MCP)** は、Anthropicが開発したAIアプリケーションと外部ツール間の標準通信プロトコルです。

### 主な機能
- **Tools**: AI が利用可能な関数・コマンド
- **Resources**: AI がアクセスできるファイル・データ
- **Prompts**: 再利用可能なプロンプトテンプレート
- **Sampling**: LLM 呼び出しの委譲

### 対応アプリケーション
- **Claude Code** (Claude CLI)
- **Claude Desktop**
- **Cline** (VS Code拡張)
- **Zed** エディタ
- その他のMCP対応ツール

---

## MCPメモリーサーバーの設定

### 1. MCPメモリーサーバーのインストール

MCPメモリーサーバーは、会話履歴やコンテキストを永続化するMCPサーバーです。

```bash
# Node.js環境で実行
npm install -g @modelcontextprotocol/server-memory

# または npx で直接実行（インストール不要）
npx @modelcontextprotocol/server-memory
```

### 2. メモリーサーバーの設定ファイル

Claude Code や Claude Desktop で使用する場合、設定ファイルを編集します。

#### macOS / Linux の場合

**Claude Code**:
```json
// ~/.config/claude-code/mcp.json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    }
  }
}
```

**Claude Desktop**:
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
// ~/.config/Claude/claude_desktop_config.json (Linux)
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    }
  }
}
```

#### Windows の場合

```json
// %APPDATA%\Claude\claude_desktop_config.json
{
  "mcpServers": {
    "memory": {
      "command": "npx.cmd",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    }
  }
}
```

### 3. メモリーサーバーの機能

メモリーサーバーをインストールすると、以下のツールが利用可能になります：

| ツール名 | 説明 |
|---------|------|
| `memory_store` | 情報を保存 |
| `memory_retrieve` | 情報を取得 |
| `memory_search` | 情報を検索 |
| `memory_delete` | 情報を削除 |

**使用例**:
```
User: 明日のミーティングは10時からと記憶して

Claude: [memory_store を使用]
記憶しました：明日のミーティングは10時からです。

---

User: 明日の予定は？

Claude: [memory_retrieve を使用]
明日は10時からミーティングがあります。
```

### 4. 永続化ストレージの設定

デフォルトでは、メモリはプロセス再起動で消えます。永続化するには：

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory",
        "--storage-path",
        "~/.claude/memory.json"
      ]
    }
  }
}
```

---

## Claude Code MCP設定

### 1. Claude Code のインストール

```bash
# Homebrew (macOS/Linux)
brew install anthropics/claude/claude

# または直接ダウンロード
# https://github.com/anthropics/claude-code
```

### 2. MCP設定ファイルの場所

```bash
# macOS / Linux
~/.config/claude-code/mcp.json

# Windows
%APPDATA%\claude-code\mcp.json
```

### 3. 基本設定テンプレート

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/directory"
      ]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

### 4. よく使うMCPサーバー

#### Filesystem サーバー

特定のディレクトリへのファイルアクセスを許可：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/projects",
        "/Users/username/documents"
      ]
    }
  }
}
```

#### Brave Search サーバー

Web検索機能を追加：

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "BSA..."
      }
    }
  }
}
```

**Brave API Key取得方法**:
1. https://brave.com/search/api/ にアクセス
2. アカウント作成・ログイン
3. API キーを取得

#### GitHub サーバー

GitHub リポジトリ操作：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
```

### 5. 環境変数の管理

APIキーをハードコードせず、環境変数で管理：

**macOS / Linux**:
```bash
# ~/.zshrc or ~/.bashrc
export BRAVE_API_KEY="BSA..."
export GITHUB_TOKEN="ghp_..."
```

**MCP設定**:
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    }
  }
}
```

---

## Kagura AI との統合

### 1. Kagura MCP サーバー設定（v2.1.0+）

**注意**: この機能は v2.1.0 以降で利用可能です（RFC-007実装後）。

```bash
# Kagura AI をMCP対応でインストール
pip install kagura-ai[mcp]

# または既存環境に追加
pip install mcp jsonschema
```

### 2. Kagura MCPサーバーの起動

```bash
# デフォルト設定で起動
kagura mcp serve

# カスタム設定で起動
kagura mcp serve --config ~/.kagura/mcp.toml
```

### 3. Claude Code に Kagura を追加

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {
        "KAGURA_MODEL": "gpt-4o-mini",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

### 4. Kagura 設定ファイル

`~/.kagura/mcp.toml`:

```toml
[mcp]
# MCPサーバー設定
enabled = true
auto_discover = true

# エージェント自動検出パス
agent_paths = [
    "~/.kagura/agents",
    "~/projects/my_agents"
]

# デフォルトLLM
[llm]
default_model = "gpt-4o-mini"
temperature = 0.7

# MCPクライアント設定（外部ツール呼び出し）
[mcp.client]
enabled = true

# 外部MCPツール
[[mcp.client.tools]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "~/projects"]

[[mcp.client.tools]]
name = "brave_search"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-brave-search"]
env = { BRAVE_API_KEY = "${BRAVE_API_KEY}" }
```

### 5. カスタムエージェントのMCP公開

```python
# ~/.kagura/agents/my_agents.py
from kagura import agent

@agent(model="gpt-4o-mini")
async def analyze_code(code: str, language: str = "python") -> dict:
    """
    Analyze code quality and provide suggestions.

    Args:
        code: Source code to analyze
        language: Programming language

    Returns:
        Analysis results with quality score and suggestions
    """
    return f"Analyze this {language} code:\n{code}"

@agent(model="gpt-4o-mini")
async def translate_text(text: str, target_lang: str = "English") -> str:
    """
    Translate text to target language.

    Args:
        text: Text to translate
        target_lang: Target language

    Returns:
        Translated text
    """
    return f"Translate to {target_lang}: {text}"
```

**Claude Code から使用**:
```
User: このコードを分析して

Claude: Kaguraのcode analyzerを使います
[kagura_analyze_code を実行]

結果:
- 品質スコア: 7/10
- 提案:
  1. 型ヒントを追加
  2. 関数を分割
  3. エラーハンドリング追加
```

---

## トラブルシューティング

### 問題1: MCPサーバーが起動しない

**症状**:
```
Error: MCP server 'memory' failed to start
```

**解決方法**:
```bash
# 1. Node.js がインストールされているか確認
node --version  # v18+ 必須

# 2. npx でパッケージを手動実行してエラー確認
npx @modelcontextprotocol/server-memory

# 3. キャッシュクリア
npm cache clean --force
```

### 問題2: 環境変数が読み込まれない

**症状**:
```
Error: BRAVE_API_KEY is not defined
```

**解決方法**:
```bash
# 1. シェル設定ファイルを確認
cat ~/.zshrc  # または ~/.bashrc

# 2. 環境変数をエクスポート
export BRAVE_API_KEY="your-key-here"

# 3. シェル再起動
source ~/.zshrc

# 4. Claude Code を再起動
```

### 問題3: Kagura MCPサーバーが見つからない

**症状**:
```
Error: command 'kagura' not found
```

**解決方法**:
```bash
# 1. Kagura がインストールされているか確認
pip show kagura-ai

# 2. パスを確認
which kagura

# 3. MCP設定でフルパス指定
{
  "command": "/path/to/venv/bin/kagura",
  "args": ["mcp", "serve"]
}
```

### 問題4: ツールが利用できない

**症状**:
```
User: Web検索して
Claude: 検索機能は利用できません
```

**解決方法**:
```bash
# 1. MCP設定ファイルを確認
cat ~/.config/claude-code/mcp.json

# 2. サーバーが起動しているか確認
# Claude Code のログを確認

# 3. サーバーを手動起動してテスト
npx @modelcontextprotocol/server-brave-search

# 4. Claude Code を再起動
```

### 問題5: メモリが保存されない

**症状**:
```
User: 記憶した内容を教えて
Claude: 記憶がありません
```

**解決方法**:
```json
// ストレージパスを明示的に指定
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory",
        "--storage-path",
        "/absolute/path/to/memory.json"
      ]
    }
  }
}
```

---

## ベストプラクティス

### 1. セキュリティ

#### APIキーの管理

**❌ 悪い例**:
```json
{
  "env": {
    "BRAVE_API_KEY": "BSA1234567890abcdef"
  }
}
```

**✅ 良い例**:
```bash
# ~/.zshrc
export BRAVE_API_KEY="BSA1234567890abcdef"
```

```json
{
  "env": {
    "BRAVE_API_KEY": "${BRAVE_API_KEY}"
  }
}
```

#### ファイルシステムアクセスの制限

**❌ 悪い例**:
```json
{
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/"]
}
```

**✅ 良い例**:
```json
{
  "args": [
    "-y",
    "@modelcontextprotocol/server-filesystem",
    "~/projects",
    "~/documents/work"
  ]
}
```

### 2. パフォーマンス

#### サーバーの起動時間短縮

**グローバルインストール**（頻繁に使う場合）:
```bash
npm install -g @modelcontextprotocol/server-memory
npm install -g @modelcontextprotocol/server-filesystem
```

```json
{
  "mcpServers": {
    "memory": {
      "command": "mcp-server-memory"
    }
  }
}
```

### 3. 設定管理

#### 設定ファイルのバージョン管理

```bash
# 設定をGitで管理（APIキーは除く）
cp ~/.config/claude-code/mcp.json ~/dotfiles/claude-mcp.json

# .gitignore に追加
echo "mcp.json" >> .gitignore

# テンプレート作成
cp mcp.json mcp.json.template
# APIキー部分を "${ENV_VAR}" に置換
```

#### 環境別設定

**開発環境**:
```json
// ~/.config/claude-code/mcp.dev.json
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve", "--debug"],
      "env": {
        "KAGURA_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

**本番環境**:
```json
// ~/.config/claude-code/mcp.json
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {
        "KAGURA_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 4. モニタリング

#### ログの確認

**Claude Code**:
```bash
# Claude Code のログディレクトリ
~/.cache/claude-code/logs/

# 最新ログを確認
tail -f ~/.cache/claude-code/logs/mcp.log
```

**Kagura MCP Server**:
```bash
# Kagura のログ
tail -f ~/.kagura/logs/mcp.log
```

### 5. デバッグ

#### MCP接続のテスト

```bash
# MCPサーバーを手動起動してテスト
kagura mcp serve --debug

# 別ターミナルでクライアント接続テスト
kagura mcp test-connection
```

#### ツール一覧の確認

```bash
# Claude Code内で
/mcp list-tools

# 期待される出力:
# - memory_store
# - memory_retrieve
# - kagura_analyze_code
# - kagura_translate_text
```

---

## 応用例

### 例1: 開発ワークフロー

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/projects"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

**使用例**:
```
User: プロジェクトのコードを分析して、改善提案をGitHub Issueに作成して

Claude:
1. [filesystem] コードファイルを読み取り
2. [kagura_analyze_code] コード分析実行
3. [github] Issue作成

完了しました！Issue #123 を作成しました。
```

### 例2: リサーチワークフロー

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    },
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"]
    }
  }
}
```

**使用例**:
```
User: Pythonの最新トレンドを調べて、まとめをメモリーに保存して

Claude:
1. [brave_search] "Python trends 2025" で検索
2. [kagura_summarize] 検索結果を要約
3. [memory_store] 要約を保存

保存しました！「Pythonトレンド2025」として記憶しています。
```

---

## 参考リンク

### 公式ドキュメント
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Claude Code Documentation](https://docs.claude.com/claude-code)

### MCPサーバーリスト
- [@modelcontextprotocol/server-memory](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
- [@modelcontextprotocol/server-filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- [@modelcontextprotocol/server-brave-search](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search)
- [@modelcontextprotocol/server-github](https://github.com/modelcontextprotocol/servers/tree/main/src/github)

### Kagura AI
- [Kagura AI RFC-007: MCP Integration](./rfcs/RFC_007_MCP_INTEGRATION.md)
- [Kagura AI Unified Roadmap](./UNIFIED_ROADMAP.md)

---

## 改訂履歴

- **2025-10-04**: 初版作成
  - MCPメモリーサーバー設定
  - Claude Code MCP設定
  - Kagura AI統合（v2.1.0対応予定）
  - トラブルシューティング
  - ベストプラクティス

---

**次のステップ**:
1. メモリーサーバーをインストール
2. Claude Code MCP設定を追加
3. Brave Search API キーを取得
4. 実際に使ってみる！

**質問・フィードバック**: [GitHub Issues](https://github.com/JFK/kagura-ai/issues)
