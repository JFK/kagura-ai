# Kagura AI v4.0 はじめに

> **Universal AI Memory Platform - 10分でセットアップ**

Kaguraは、すべてのAIプラットフォーム（Claude、ChatGPT、Gemini など）を共有コンテキストとメモリーで接続する、ユニバーサルメモリーレイヤーです。

---

## 📋 Kagura v4.0とは？

**Kagura v4.0** = **MCP-native Universal Memory**

- **Claude Desktopユーザー向け**: 31個の全ツールを備えたローカルMCPサーバー
- **ChatGPTユーザー向け**: メモリーアクセス可能なHTTP/SSEコネクタ
- **チーム向け**: 認証機能付きセルフホストAPI
- **開発者向け**: REST API + Python SDK

---

## 🚀 クイックスタート（パスを選択）

### パス1: Claude Desktopユーザー（推奨）

**セットアップ時間**: 5分

```bash
# Kaguraをインストール
pip install kagura-ai[full]

# Claude Desktopを自動設定
kagura mcp install

# Claude Desktopを再起動
# これで完了！KaguraがClaudeで利用可能になりました
```

**Claude Desktopで試す**:
```
「覚えておいて: バックエンド開発にはPythonが好きです」
「私の好みについて何か知っていますか？」
```

**参照**: [MCPセットアップガイド](mcp-setup.md)

---

### パス2: ChatGPTコネクタユーザー

**セットアップ時間**: 10分

1. **Kagura APIを起動**:
   ```bash
   # Dockerを使用
   docker compose up -d

   # またはローカル実行
   pip install kagura-ai[api]
   uvicorn kagura.api.server:app --port 8000
   ```

2. **ngrokで公開**（テスト用）:
   ```bash
   ngrok http 8000
   # URLを取得: https://abc123.ngrok.app
   ```

3. **ChatGPTを設定**:
   - 開発者モードを有効化
   - コネクタを追加:
     - URL: `https://abc123.ngrok.app/mcp`
     - 名前: Kagura Memory

**参照**: [MCP over HTTP/SSE ガイド](mcp-http-setup.md)

---

### パス3: セルフホスト本番環境

**セットアップ時間**: 30分

```bash
# リポジトリをクローン
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai

# 設定
cp .env.example .env
nano .env  # DOMAINとPOSTGRES_PASSWORDを設定

# デプロイ
docker compose -f docker-compose.prod.yml up -d

# APIキーを生成
docker compose -f docker-compose.prod.yml exec api \
  kagura api create-key --name "production"

# 確認
curl https://your-domain.com/api/v1/health
```

**参照**: [セルフホスティングガイド](self-hosting.md)

---

## 🧩 主な機能

### 1. Universal Memory

一度保存すれば、どのAIからでもアクセス可能:

```python
# MCPツール経由（Claude Desktop、ChatGPT など）
memory_store(
    user_id="jfk",
    agent_name="global",
    key="coding_style",
    value="Always use type hints in Python",
    scope="persistent",
    tags='["python", "best-practices"]'
)
```

### 2. Graph Memory

関係性とパターンを追跡:

```python
# インタラクションを記録
memory_record_interaction(
    user_id="jfk",
    query="How do I write async functions?",
    response="...",
    metadata={"topic": "python", "skill_level": "intermediate"}
)

# パターンを分析
memory_get_user_pattern(user_id="jfk")
```

### 3. リモートアクセス

どこからでもメモリーにアクセス:

- **ChatGPTコネクタ**: HTTP/SSEトランスポート
- **APIキー**: 安全な認証
- **ツールフィルタリング**: 自動セキュリティ（リモートではファイル操作不可）

### 4. エクスポート/インポート

データを完全に所有:

```bash
# バックアップ
kagura memory export --output ./backup

# 復元
kagura memory import --input ./backup
```

---

## 📚 次のステップ

### Claude Desktopユーザー向け

1. [完全なMCPセットアップ](mcp-setup.md)
2. 組み込みツールを試す: `kagura mcp tools`
3. メモリー操作を探索

### ChatGPTユーザー向け

1. [HTTP/SSEコネクタのセットアップ](mcp-http-setup.md)
2. APIキーを生成: `kagura api create-key`
3. 接続してテスト

### セルフホスター向け

1. [セルフホスティングガイドに従う](self-hosting.md)
2. CaddyでSSL/TLSを設定
3. バックアップを設定

### 開発者向け

1. [REST APIリファレンス](api-reference.md)
2. [アーキテクチャ概要](architecture.md)
3. [メモリーエクスポート/インポート](memory-export.md)

---

## 🔍 利用可能なコマンド

```bash
# MCP管理
kagura mcp serve           # MCPサーバーを起動（Claude Desktop）
kagura mcp install         # Claude Desktopを自動設定
kagura mcp tools           # 利用可能なツールをリスト
kagura mcp doctor          # 診断を実行
kagura mcp connect         # リモート接続を設定
kagura mcp test-remote     # リモートAPIをテスト

# APIキー管理
kagura api create-key      # APIキーを生成
kagura api list-keys       # 全キーをリスト
kagura api revoke-key      # キーを無効化

# メモリー管理
kagura memory export       # JSONLにエクスポート
kagura memory import       # JSONLからインポート

# システム
kagura --version           # バージョンを表示
```

---

## 💬 サポート

- **ドキュメント**: https://kagura-ai.com/docs
- **GitHub Issues**: https://github.com/JFK/kagura-ai/issues
- **Discussions**: https://github.com/JFK/kagura-ai/discussions

---

**バージョン**: 4.0.0
**プロトコル**: MCP (Model Context Protocol)
**ライセンス**: Apache 2.0
