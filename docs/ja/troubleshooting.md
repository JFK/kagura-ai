# トラブルシューティングガイド

> **Kagura AIの一般的な問題と解決策**

このガイドは、Kagura AI統合に関する一般的な問題の診断と修正を支援します。

---

## 🔍 クイック診断

### ステップ1: Doctorコマンドを実行

```bash
kagura mcp doctor
```

**期待される出力**:
```
Kagura MCP Diagnostics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Python version: 3.11.5
✅ Kagura installed: 4.0.0
✅ MCP server: Configured
✅ Database: Connected (342 memories)
✅ Vector store: Healthy (ChromaDB)

Configuration:
  Data dir: ~/.local/share/kagura
  Cache dir: ~/.cache/kagura
  Config dir: ~/.config/kagura
```

### ステップ2: サーバーステータスを確認

**ローカルMCP（Claude Desktop/Code）**:
```bash
# Claude Code
claude mcp list

# Kaguraログを確認
kagura mcp log --tail
```

**リモートMCP（ChatGPT）**:
```bash
# APIヘルスチェック
curl http://localhost:8080/api/v1/health

# MCPエンドポイントを確認
curl http://localhost:8080/mcp

# ログを確認
docker compose logs -f api
```

---

## 🚨 一般的な問題

### 問題 0: "No result received from client-side tool execution"

**症状**:
- MCPツールがハングしてタイムアウトする
- エラー: "No result received from client-side tool execution"
- メモリーツールの初回使用時に発生

**根本原因**:
初回実行時に埋め込みモデル（約500MB）をダウンロードするため、30〜60秒かかります。MCPクライアントがタイムアウトします。

**解決策**: 埋め込みモデルを事前ダウンロード

```bash
# MCPメモリーツール使用前に一度だけ実行
kagura memory setup
```

**出力**:
```
Kagura Memory Setup

Downloading embeddings model: intfloat/multilingual-e5-large
(~500MB, may take 30-60 seconds)

✓ Model downloaded successfully!

  Model: intfloat/multilingual-e5-large
  Dimension: 1024

MCP memory tools are now ready to use!
```

**セットアップ後**: MCPメモリーツールが即座に動作（タイムアウトなし）。

**代替案**: Claude Codeのターミナルで最初の会話中にセットアップを実行。

---

### 問題1: MCPサーバーが接続できない

**症状**:
- ClaudeがKaguraツールを認識しない
- 「サーバーが応答しません」エラー
- ツールリストが空

**診断**:

```bash
# Claude Code
claude mcp list
# 表示されるべき内容: kagura: ✓ Connected

# 接続されていない場合、ログを確認
kagura mcp log
```

**解決策**:

#### 解決策A: MCPサーバーを再起動（ローカル）

```bash
# Claude Desktop
# 1. Claude Desktopを完全に終了
# 2. Claude Desktopを再起動
# 3. 新しい会話を開始

# Claude Code
# 1. サーバーを削除して再追加
claude mcp remove kagura
claude mcp add --transport stdio kagura -- kagura mcp serve

# 2. 確認
claude mcp list
```

#### 解決策B: コマンドパスを確認

**問題**: `kagura: command not found`

```bash
# kaguraのパスを見つける
which kagura
# 出力: /home/user/.local/bin/kagura

# 設定でフルパスを使用
claude mcp add --transport stdio kagura -- /home/user/.local/bin/kagura mcp serve
```

#### 解決策C: パーミッションを確認

```bash
# kaguraが実行可能であることを確認
chmod +x $(which kagura)

# Python環境を確認
python --version  # 3.11以上である必要があります
pip show kagura-ai  # バージョン4.0.0以上を表示する必要があります
```

---

### 問題2: メモリーが保持されない

**症状**:
- 会話終了後にメモリーが消える
- 次のセッションで「メモリーが見つかりません」
- 進捗が失われる

**診断**:

```bash
# メモリー統計を確認
kagura mcp tools  # Claudeで実行: "Show memory stats"

# データベースを確認
ls -lh ~/.local/share/kagura/memory.db
```

**解決策**:

#### 解決策A: 永続的なスコープを使用

**問題**: デフォルトの`scope="working"`（一時的）を使用している

**修正**: 明示的に永続ストレージをリクエスト

```
❌ "Remember that I prefer Python"
✅ "Remember PERMANENTLY: I prefer Python"
✅ "Save this with scope='persistent': I prefer Python"
```

**プロンプト内で**:
```python
memory_store(
    key="python_preference",
    value="FastAPI over Django",
    scope="persistent"  # ← 重要!
)
```

#### 解決策B: user_idを確認

**問題**: 各セッションで異なる`user_id`を使用している

```
# セッション1
"Remember for user_id='john': I prefer Python"

# セッション2（異なるuser_id！）
"What do I prefer?"  # デフォルトのuser_idを使用 → 結果なし
```

**修正**: 一貫した`user_id`を使用:

```
# 常に同じuser_idを指定
"For user_id='john': What programming languages do I prefer?"
```

---

### 問題3: ファイル操作が機能しない（リモートMCP）

**症状**:
- "file_read not found"
- "ファイルにアクセスできません"
- アップロードが機能しない

**診断**:

これはリモートMCP（ChatGPT、Claude Chat）における**期待される動作**です。

**理由**: リモートMCPはHTTP/SSE経由で実行され、セキュリティ上の理由から直接ファイルシステムアクセスを持ちません。

**解決策**:

#### 解決策A: ファイル操作にはローカルMCPを使用

Claude DesktopまたはClaude Codeに切り替え:

```bash
# Claude Desktop
kagura mcp install

# Claude Code
claude mcp add --transport stdio kagura -- kagura mcp serve
```

これで以下が使用できます:
- `file_read`
- `file_write`
- `dir_list`
- `media_open_*`

#### 解決策B: コンテンツをコピー/ペースト（リモートMCP）

リモートMCPを使用する必要がある場合:

```
# "Read config.py"の代わりに
# → ファイルの内容をチャットにコピー/ペースト

ユーザー: "これがconfig.pyの内容です:
      [内容をペースト]

      この設定を分析してください"
```

#### 解決策C: v4.1ファイルアップロードを待つ

**将来**: マルチモーダルアップロードAPIはv4.1で計画されています

参照: [Issue #462](https://github.com/JFK/kagura-ai/issues/462)

---

### 問題4: 検索結果が返されない

**症状**:
- `memory_search`が空を返す
- "メモリーが見つかりません"
- 保存された情報を見つけられない

**診断**:

```
# Claude/ChatGPTで:
"List all my memories"
[memory_listを使用]

"Show memory statistics"
[memory_statsを使用]
```

**解決策**:

#### 解決策A: メモリーの存在を確認

```
"List all memories"

# 空の場合 → まだメモリーが保存されていない
# メモリーがある場合 → 次の解決策に進む
```

#### 解決策B: 正しい検索タイプを使用

**セマンティック検索**（意味ベース）:
```
✅ "Find memories about backend development"
✅ "Search for information on API design"
```

**正確なキー呼び出し**:
```
✅ "Recall memory with key='python_preference'"
```

**誤ったアプローチ**:
```
❌ "Search for exact text 'I prefer FastAPI over Django'"
```

#### 解決策C: フィルターを確認

**問題**: 制限が厳しすぎるフィルター

```python
# 特定しすぎ（結果なし）
memory_search(
    query="FastAPI",
    tags=["python", "web", "api", "backend", "2024"]  # タグが多すぎる
)

# より良い（より多くの結果）
memory_search(
    query="FastAPI",
    tags=["python"]  # タグが少ない
)

# 最良（最も多くの結果）
memory_search(
    query="FastAPI"  # フィルターなし
)
```

#### 解決策D: user_idとagent_nameを確認

```
# 何を検索しているか確認
"Search memories for user_id='john' with agent_name='global'"

# 結果がない場合、異なる組み合わせを試す
"Search all memories regardless of user_id"
```

---

### 問題5: 高額なAPIコスト

**症状**:
- 予期しないOpenAI/Anthropicの請求
- 埋め込みAPIのコストが高すぎる
- トークン使用量の警告

**診断**:

```
# コスト概要を確認
"Show telemetry cost summary"
[telemetry_costを使用]

# ツール使用状況を確認
kagura mcp stats
```

**解決策**:

#### 解決策A: ローカル埋め込みを使用

**問題**: 埋め込みにOpenAI APIを使用している

**修正**: ローカルのsentence-transformersに切り替え

```bash
# AIエクストラをインストール（sentence-transformersを含む）
pip install kagura-ai[ai]

# ローカル埋め込みを使用するように設定
# .envまたは環境変数で:
KAGURA_EMBEDDING_MODEL=local  # E5モデルを使用（無料、ローカル）
```

**コスト比較**:
- OpenAI埋め込み: 1Kトークンあたり$0.0001
- ローカルE5埋め込み: $0（マシン上で実行）

#### 解決策B: 低トークン検索を使用

`memory_search`（完全な内容を返す）の代わりに、`memory_search_ids`を使用:

```python
# 高トークン使用量
memory_search(query="FastAPI", k=10)
# 10個の完全なメモリーを返す → 約5000トークン

# 低トークン使用量
memory_search_ids(query="FastAPI", k=10)
# 10個のID + プレビューを返す → 約500トークン
```

#### 解決策C: 検索頻度を減らす

検索結果をキャッシュ:

```
# 複数回検索する代わりに
"Find memories about Python"  # 検索1
"Find memories about Python"  # 検索2（重複！）

# より良い: 一度検索して、その後参照
"Find memories about Python"  # 一度検索
"Based on those memories, what should I use for backend?"  # 検索なし
```

#### 解決策D: コストを監視

```
# 定期的なコストチェック
"Show me telemetry cost for the last week"

# 予算アラートを設定（将来の機能）
```

---

### 問題6: パフォーマンスが遅い

**症状**:
- 検索に5秒以上かかる
- メモリー操作がタイムアウト
- APIレスポンスが遅い

**診断**:

```bash
# データベースサイズを確認
du -sh ~/.local/share/kagura/

# メモリー数を確認
kagura mcp tools  # その後: "Show memory stats"

# システムリソースを確認
top  # 高いCPU/メモリー使用率を確認
```

**解決策**:

#### 解決策A: 古いメモリーをクリーンアップ

```bash
# まずエクスポート（バックアップ）
kagura memory export --output=./backup

# 古い/未使用のメモリーを削除
# Claude/ChatGPTで:
"Delete memories older than 6 months with usefulness score < 0.3"
```

#### 解決策B: ChromaDBを最適化

```bash
# データベースを圧縮
cd ~/.cache/kagura/chromadb
# ChromaDBは自動圧縮しますが、強制するために再起動できます

# または最初から再構築
kagura memory export --output=./backup
rm -rf ~/.cache/kagura/chromadb
kagura memory import --input=./backup
```

#### 解決策C: 完全一致にはBM25を使用

**セマンティック検索（大規模データセットでは遅い）**:
```python
memory_search(query="FastAPI", mode="vector")  # 10K以上のメモリーでは遅い
```

**BM25字句検索（高速）**:
```python
memory_search(query="FastAPI", mode="bm25")  # 100K以上のメモリーでも高速
```

**ハイブリッド（最良の精度 + 速度）**:
```python
memory_search(query="FastAPI", mode="hybrid")  # バランス
```

---

### 問題7: 認証エラー（リモートMCP）

**症状**:
- "401 Unauthorized"
- "Invalid API key"
- "Authentication required"

**診断**:

```bash
# APIキーが存在するか確認
kagura api list-keys

# 認証をテスト
curl -H "Authorization: Bearer YOUR_KEY" \
     http://localhost:8080/api/v1/health
```

**解決策**:

#### 解決策A: APIキーを作成

```bash
# 新しいAPIキーを生成
kagura api create-key --name "chatgpt-integration"

# 出力:
# Created API key: kg_xxxxxxxxxxxxxxxxxxxxxxxx
# Save this key securely!
```

#### 解決策B: APIキーでMCPを設定

**ChatGPT MCP設定**:
```json
{
  "url": "https://your-domain.com/mcp",
  "headers": {
    "Authorization": "Bearer kg_xxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

#### 解決策C: キーのパーミッションを確認

```bash
# キーの詳細を表示
kagura api get-key kg_xxxxxxxx

# 侵害された場合はローテーション
kagura api rotate-key kg_xxxxxxxx

# 必要に応じて取り消し
kagura api revoke-key kg_xxxxxxxx
```

---

### 問題8: Dockerの問題

**症状**:
- "Cannot connect to Docker daemon"
- コンテナが起動しない
- ポートの競合

**診断**:

```bash
# Dockerステータスを確認
docker ps

# ログを確認
docker compose logs -f

# ポートを確認
lsof -i :8080  # APIポート
lsof -i :5432  # PostgreSQLポート
lsof -i :6379  # Redisポート
```

**解決策**:

#### 解決策A: Dockerを起動

```bash
# Linux
sudo systemctl start docker

# macOS
# Docker Desktopを開く

# 確認
docker ps
```

#### 解決策B: ポート競合を修正

**問題**: ポート8080が既に使用中

```bash
# ポートを使用しているものを見つける
lsof -i :8080

# プロセスを終了
kill -9 <PID>

# またはdocker-compose.ymlでKaguraのポートを変更
ports:
  - "8090:8080"  # 代わりに8090を使用
```

#### 解決策C: Docker環境をリセット

```bash
# すべてのコンテナを停止
docker compose down

# ボリュームを削除（⚠️ データを削除します！）
docker compose down -v

# 再ビルド
docker compose up -d --build

# ヘルスチェック
curl http://localhost:8080/api/v1/health
```

---

## 🔧 高度なトラブルシューティング

### デバッグログを有効化

```bash
# ログレベルを設定
export KAGURA_LOG_LEVEL=DEBUG

# デバッグログでMCPサーバーを起動
kagura mcp serve

# またはAPI用
uvicorn kagura.api.server:app --log-level debug
```

### データベース整合性を確認

```bash
# SQLite整合性チェック
sqlite3 ~/.local/share/kagura/memory.db "PRAGMA integrity_check;"

# 期待される出力: ok
```

### ベクトルインデックスを再構築

```bash
# メモリーをエクスポート
kagura memory export --output=./backup

# ベクトルストアをクリア
rm -rf ~/.cache/kagura/chromadb

# 再インポート（ベクトルを再構築）
kagura memory import --input=./backup
```

### MCPツールを手動でテスト

```bash
# API経由で個々のツールをテスト
curl -X POST http://localhost:8080/api/v1/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "key": "test",
    "value": "test value",
    "scope": "working"
  }'

# 保存されたか確認
curl http://localhost:8080/api/v1/memory/list
```

---

## 📚 サポートを受ける

### 1. ドキュメントを確認

- [チャット統合のヒント](./chat-integration-tips.md)
- [MCPセットアップガイド](./mcp-setup.md)
- [APIリファレンス](./api-reference.md)
- [アーキテクチャ](./architecture.md)

### 2. 既存の問題を検索

[GitHub Issues](https://github.com/JFK/kagura-ai/issues)

### 3. コミュニティに質問

[GitHub Discussions](https://github.com/JFK/kagura-ai/discussions)

### 4. バグを報告

```bash
# 診断情報を含む新しいissueを作成
kagura mcp doctor > diagnostics.txt

# issueを作成する際にdiagnostics.txtを添付
gh issue create --title "Bug: [問題を記述]" \
                --body "添付のdiagnostics.txtを参照してください"
```

---

## 📊 診断チェックリスト

問題を報告する前に、以下の情報を収集してください:

```bash
# 1. バージョン情報
kagura --version
python --version
pip show kagura-ai

# 2. システム情報
uname -a  # Linux/macOS
cat /etc/os-release  # Linuxディストリビューション

# 3. 診断レポート
kagura mcp doctor

# 4. 最近のログ
kagura mcp log --lines 100

# 5. エラーメッセージ
# 完全なエラーメッセージ + スタックトレースをコピー

# 6. 再現手順
# 問題を引き起こす正確な手順を記述
```

---

**バージョン**: 4.0.0
**最終更新**: 2025-11-02
