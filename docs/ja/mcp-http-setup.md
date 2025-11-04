# MCP over HTTP/SSEセットアップガイド

**Kagura AI v4.0.0** - Universal AI Memory Platform

このガイドでは、MCP (Model Context Protocol)を使用して、HTTP/SSEトランスポート経由でKagura Memoryに接続する方法を説明します。

---

## 📋 概要

Kagura AIは、MCPプロトコルを実装する`/mcp`のHTTP/SSEエンドポイントを提供し、以下を可能にします:

- **ChatGPT Connectors**: ChatGPTをKaguraメモリーに接続
- **その他のHTTPベースのMCPクライアント**: HTTPトランスポートをサポートする任意のMCPクライアント
- **リモートアクセス**: どこからでもKaguraメモリーにアクセス

**サポートされる操作**:
- GET `/mcp` - SSEストリーミング (サーバー → クライアントメッセージ)
- POST `/mcp` - JSON-RPCリクエスト (クライアント → サーバーメッセージ)
- DELETE `/mcp` - セッション終了

---

## 🚀 クイックスタート

### 1. Kagura APIサーバーの起動

```bash
# API extrasを含めてKaguraをインストール
pip install kagura-ai[api]

# APIサーバーを起動
uvicorn kagura.api.server:app --host 0.0.0.0 --port 8000
```

`/mcp`エンドポイントは`http://localhost:8000/mcp`で利用可能になります。

---

### 2. ChatGPTに接続 (開発者モード)

**注意**: ChatGPT Connectorサポートは現在開発者プレビュー中です。

#### ステップ1: 開発者モードを有効化

1. ChatGPT設定を開く
2. **Settings → Connectors → Advanced → Developer Mode**に移動
3. Developer Modeを有効化

#### ステップ2: Kaguraコネクターを追加

以下の設定でカスタムコネクターを追加します:

```json
{
  "name": "Kagura Memory",
  "url": "http://localhost:8000/mcp",
  "description": "Universal AI Memory Platform",
  "authentication": "none"
}
```

**リモートアクセスの場合** (ngrokを使用):

```bash
# ローカルサーバーを公開
ngrok http 8000

# ChatGPTでngrok URLを使用
# 例: https://abc123.ngrok.app/mcp
```

#### ステップ3: 接続をテスト

ChatGPTで試してみてください:

```
"Remember: I prefer Python for backend development"
"What do you know about my preferences?"
```

KaguraはすべてのAIプラットフォームで設定を保存し、呼び出します!

---

## 🔧 高度な設定

### API認証 (Phase C Task 2 ✅)

Kagura APIは、安全なリモートアクセスのためにAPIキー認証をサポートしています。

#### APIキーの生成

```bash
# 新しいAPIキーを作成
kagura api create-key --name "chatgpt-connector"

# 出力:
# ✓ API key created successfully!
# ⚠️  Save this key securely - it won't be shown again:
#
#   kagura_abc123xyz789...
```

**⚠️ 重要**: APIキーは作成時に一度だけ表示されます。安全に保存してください!

#### リクエストでAPIキーを使用

```bash
# HTTPリクエストで使用
curl -H "Authorization: Bearer kagura_abc123xyz789..." \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     http://localhost:8000/mcp
```

#### APIキーの管理

```bash
# すべてのAPIキーをリスト
kagura api list-keys

# 特定のユーザーのキーをリスト
kagura api list-keys --user-id user_alice

# キーを失効 (監査履歴を保持)
kagura api revoke-key --name "old-key"

# キーを完全に削除
kagura api delete-key --name "unused-key"
```

#### APIキーオプション

```bash
# 有効期限付きのキーを作成 (90日)
kagura api create-key --name "temp-key" --expires 90

# 特定のユーザー向けのキーを作成
kagura api create-key --name "alice-key" --user-id user_alice
```

---

### ツールアクセス制御 (Phase C Task 3 ✅)

Kaguraは、HTTP/SSE経由でリモートアクセスされた場合、危険なツールを自動的にフィルタリングします。

#### 安全なツールと危険なツール

**✅ リモートアクセスで安全** (`/mcp`経由で許可):
- **メモリーツール**: `memory_store`, `memory_recall`, `memory_search`など
- **Web/APIツール**: `web_search`, `brave_web_search`, `youtube_summarize`など
- **マルチモーダルツール**: `multimodal_index`, `multimodal_search`
- **テレメトリツール**: `telemetry_stats`, `telemetry_cost`

**⛔ 危険 - ローカルのみ** (`/mcp`経由でブロック):
- **ファイル操作**: `file_read`, `file_write`, `dir_list`
- **シェル実行**: `shell_exec`
- **ローカルアプリ実行**: `media_open_audio`, `media_open_image`, `media_open_video`

#### ツールフィルタリングの理由

ファイル操作やシェルコマンドへのリモートアクセスは以下を可能にします:
- 機密ファイルの読み取り (`/etc/passwd`, APIキーなど)
- 悪意のあるファイルの書き込み
- サーバー上での任意のコマンド実行

**解決策**: `/mcp`エンドポイントは危険なツールを自動的にフィルタリングします。

#### ツール権限の確認

```bash
# 利用可能なすべてのツールをリスト (HTTP/SSE経由)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# file_read, shell_execなどはリストに表示されません
```

#### ローカルとリモートのコンテキスト

```python
# ローカルMCPサーバー (stdio) - すべてのツールが利用可能
kagura mcp serve  # 31個すべてのツールを公開

# リモートHTTP/SSEサーバー - 安全なツールのみ
uvicorn kagura.api.server:app  # 約24個の安全なツールを公開
```

---

### ユーザーIDヘッダー

アクセスするユーザーのメモリーを指定します:

```bash
# ユーザーIDを含むリクエスト
curl -H "X-User-ID: user_alice" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     http://localhost:8000/mcp
```

**デフォルト**: `X-User-ID`ヘッダーが提供されない場合、`default_user`が使用されます。

---

### CORS設定

本番デプロイメントでは、`src/kagura/api/server.py`でCORSを設定します:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.openai.com"],  # オリジンを指定
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

---

## 🧪 エンドポイントのテスト

### 1. ヘルスチェック

```bash
curl http://localhost:8000/
# 期待される結果: {"name":"Kagura Memory API","version":"4.0.0",...}
```

### 2. MCPプロトコルテスト

#### セッションの初期化

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'
```

#### 利用可能なツールのリスト

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

#### メモリーの保存

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "kagura_tool_memory_store",
      "arguments": {
        "user_id": "test_user",
        "agent_name": "global",
        "key": "my_preference",
        "value": "I prefer Python for backend",
        "scope": "persistent",
        "tags": "[\"preferences\"]",
        "importance": 0.8
      }
    }
  }'
```

---

## 🔌 リモート接続管理 (Phase C Task 4 ✅)

Kaguraは、リモートMCP接続を設定およびテストするCLIコマンドを提供します。

### リモート接続の設定

```bash
# リモートKagura APIへの接続を設定
kagura mcp connect \
  --api-base https://my-kagura.example.com \
  --api-key kagura_abc123xyz789...

# カスタムユーザーIDを使用
kagura mcp connect \
  --api-base https://api.kagura.io \
  --api-key kagura_xyz... \
  --user-id user_alice
```

**設定の保存先**: `~/.config/kagura/remote-config.json`

### リモート接続のテスト

```bash
# リモート接続が機能することを確認
kagura mcp test-remote

# 出力:
# Testing Remote MCP Connection
#
# 1. Testing API health...
#    ✓ API server is reachable
#
# 2. Testing /mcp endpoint...
#    ✓ MCP endpoint is accessible
#
# 3. Testing authentication...
#    ✓ API key configured: ***xyz789
#
# ✓ All tests passed!
```

### 使用上の注意

- **`kagura mcp serve --remote`**は将来のリリースで予定 (stdio → HTTPプロキシ)
- 現在は、ChatGPT Connectorから**直接HTTP/SSE**接続を使用してください
- `connect`および`test-remote`コマンドは、リモート認証情報の管理に役立ちます

---

## 🌐 本番デプロイメント

### Docker Compose

```yaml
version: '3.8'

services:
  kagura-api:
    image: kagura-ai:4.0.0
    ports:
      - "8000:8000"
    environment:
      - KAGURA_API_KEY=${KAGURA_API_KEY}
    command: uvicorn kagura.api.server:app --host 0.0.0.0 --port 8000
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - kagura-api
```

### Nginx設定

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    location /mcp {
        proxy_pass http://kagura-api:8000/mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # SSEサポート
        proxy_buffering off;
        proxy_set_header X-Accel-Buffering no;
    }
}
```

---

## 🔍 トラブルシューティング

### 接続が拒否される

**問題**: `/mcp`エンドポイントに接続できない

**解決策**:
1. APIサーバーが実行中であることを確認: `curl http://localhost:8000/`
2. ファイアウォールルールを確認
3. ポート8000が使用されていないことを確認

### 406 Not Acceptable

**問題**: HTTP 406エラーを受信

**原因**: MCPプロトコル用の`Accept`ヘッダーがない

**解決策**: リクエストに適切なMCPヘッダーを含める

### バックグラウンドタスクが起動しない

**問題**: MCPサーバーバックグラウンドタスクの起動に失敗

**原因**: イベントループが利用できない

**解決策**: APIサーバーが完全に起動した後に、`/mcp`への最初のリクエストを行うことを確認

---

## 📚 APIリファレンス

### 利用可能なMCPツール

`/mcp`経由で接続すると、以下のツールが利用可能です:

#### メモリーツール
- `kagura_tool_memory_store` - 情報を保存
- `kagura_tool_memory_recall` - セマンティック検索
- `kagura_tool_memory_search` - 全文検索
- `kagura_tool_memory_list` - すべてのメモリーをリスト
- `kagura_tool_memory_delete` - メモリーを削除

#### グラフツール (有効な場合)
- `kagura_tool_graph_link` - メモリーをリンク
- `kagura_tool_graph_query` - ナレッジグラフをクエリ

完全なツールドキュメントについては、MCPプロトコル経由で`tools/list`を呼び出してください。

---

## 🔗 関連ドキュメント

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Kagura API Reference](./api-reference.md)
- [ChatGPT Connectors Documentation](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt/)
- [Self-Hosting Guide](./self-hosting.md) *(coming soon)*

---

## 💬 サポート

- **Issues**: [GitHub Issues](https://github.com/YourUsername/kagura-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YourUsername/kagura-ai/discussions)

---

**最終更新**: 2025-10-27
**バージョン**: 4.0.0
