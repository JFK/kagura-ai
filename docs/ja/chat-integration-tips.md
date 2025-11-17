# チャット統合のヒントとベストプラクティス

> **ChatGPT、Claude Chat、その他のAIプラットフォームでKagura AIを最大限に活用する**

このガイドは、Remote MCP (Model Context Protocol) を使用してチャットベースのAIプラットフォームと統合する際に、Kagura AIを最大限に活用するためのものです。

---

## 📋 概要

### Kagura AIとは?

Kagura AIは、Claude、ChatGPT、Gemini、そしてすべてのAIエージェント間で会話とナレッジを**共有できる**、**ユニバーサルメモリープラットフォーム**です。

**主な機能**:
- 🧠 **ユニバーサルメモリー**: すべてのAIプラットフォーム間で情報を保存・呼び出し
- 🔍 **スマート検索**: ベクトル埋め込み + BM25によるセマンティック検索
- 📊 **ナレッジグラフ**: メモリー間の関係を追跡
- 🌐 **Web統合**: Web、YouTube、arXivを直接検索
- 🎨 **マルチモーダル**: 画像、PDF、音声のインデックス化と検索
- 💻 **コーディングサポート**: ファイル変更、エラー、設計決定を追跡

### Remote MCP vs Local MCP

| 機能 | Remote MCP | Local MCP |
|---------|------------|-----------|
| **プラットフォーム** | ChatGPT、Claude Chat、Gemini | Claude Desktop、Claude Code、Cursor |
| **トランスポート** | HTTP/SSE | stdio |
| **ファイルアクセス** | ❌ なし | ✅ あり |
| **メモリーツール** | ✅ 全て (49/56) | ✅ 全て (56/56) |
| **セキュリティ** | API Key必須 | ローカルのみ |

**このガイドはRemote MCP** (ChatGPT、Claude Chatなど) に焦点を当てています。

---

## ⚡ クイックスタート

### Step 1: Kagura Remote MCPサーバーを起動

```bash
# Kaguraをインストール
pip install kagura-ai[full]

# Remote MCPサーバーを起動
docker compose -f docker-compose.prod.yml up -d

# または開発モード
uvicorn kagura.api.server:app --host 0.0.0.0 --port 8080
```

### Step 2: AIプラットフォームを設定

**ChatGPT** (MCP over HTTP/SSE経由):
1. ChatGPT設定 → ツール を開く
2. MCPサーバーを追加: `https://your-domain.com/mcp`
3. API Keyを追加 (オプション、本番環境では推奨)

**Claude Chat** (将来サポート予定):
- Anthropicは2026年にClaude Chat向けMCPサポートを発表

参照: [MCP over HTTP/SSE セットアップガイド](./mcp-http-setup.md)

### Step 3: 試してみよう!

AIチャットで以下のプロンプトを試してください:

```
"こんにちは! memory_stats を実行してKaguraのステータスを表示できますか?"

"私のお気に入りのプログラミング言語はPythonであることを覚えておいて"

"Python 3.13のリリースノートをWebで検索して"

"私の好みについて何を覚えていますか?"
```

---

## 🧰 Remote MCPツール (49/56)

### ✅ 利用可能なツール

#### メモリーツール (13ツール)

| ツール | 説明 | 使用例 |
|------|-------------|---------------|
| `memory_store` | 情報を保存 | "Xを覚えておいて" |
| `memory_recall` | キーで取得 | "Yについて何と言いましたか?" |
| `memory_search` | セマンティック検索 | "Zに関するメモリーを検索" |
| `memory_list` | 全メモリーをリスト | "何を覚えていますか?" |
| `memory_delete` | 情報を忘れる | "Xについて忘れて" |
| `memory_feedback` | 有用/古いとマーク | 自動 |
| `memory_fetch` | 特定のメモリーを取得 | 内部使用 |
| `memory_search_ids` | IDのみで検索 | 低トークン検索 |
| `memory_stats` | メモリー統計を取得 | "メモリー統計を表示" |
| `memory_get_related` | 関連メモリーを取得 | グラフトラバーサル |
| `memory_get_user_pattern` | ユーザーパターンを分析 | "私の興味は何?" |
| `memory_record_interaction` | インタラクションを追跡 | 自動 |

#### Web検索ツール (5ツール)

| ツール | 説明 |
|------|-------------|
| `brave_web_search` | 一般的なWeb検索 |
| `brave_image_search` | 画像検索 |
| `brave_video_search` | 動画検索 |
| `brave_news_search` | ニュース検索 |
| `web_scrape` | Webページをスクレイピング |

**注**: `BRAVE_API_KEY` 環境変数が必要

#### アカデミック検索 (1ツール)

| ツール | 説明 |
|------|-------------|
| `arxiv_search` | arXivで学術論文を検索 |

#### YouTubeツール (4ツール)

| ツール | 説明 | 例 |
|------|-------------|---------|
| `get_youtube_transcript` | 動画の文字起こしを取得 | "この動画を文字起こしして" |
| `get_youtube_metadata` | 動画情報を取得 | "動画の詳細を取得" |
| `youtube_summarize` | 動画を要約 | "このYouTube動画を要約して" |
| `youtube_fact_check` | 主張を検証 | "この動画の主張を事実確認して" |

#### マルチモーダルツール (2ツール)

| ツール | 説明 | 注意 |
|------|-------------|------|
| `multimodal_index` | 画像/PDF/音声をインデックス化 | Gemini API必須 |
| `multimodal_search` | インデックス化されたコンテンツを検索 | Gemini API必須 |

**注**: Remote MCP経由のファイルアップロードはv4.1で提供予定 ([Issue #462](https://github.com/JFK/kagura-ai/issues/462))

#### コーディングツール (14ツール)

| ツール | 説明 |
|------|-------------|
| `coding_start_session` | コーディングセッションを開始 |
| `coding_end_session` | セッション終了 + AI要約 |
| `coding_track_file_change` | ファイル変更を追跡 |
| `coding_record_error` | スタックトレース付きでエラーを記録 |
| `coding_search_errors` | 過去の類似エラーを検索 |
| `coding_record_decision` | 設計決定を記録 |
| `coding_analyze_patterns` | コーディング設定を分析 |
| `coding_analyze_file_dependencies` | ASTベースの依存関係分析 |
| `coding_analyze_refactor_impact` | リファクタリング影響評価 |
| `coding_suggest_refactor_order` | 安全なリファクタリング順序 |
| `coding_get_project_context` | プロジェクト概要を取得 |
| `coding_get_issue_context` | GitHub issue詳細を取得 |
| `coding_link_github_issue` | セッションをissueにリンク |
| `coding_generate_pr_description` | AI生成PR説明 |

#### GitHubツール (6ツール)

| ツール | 説明 |
|------|-------------|
| `github_exec` | 安全なGitHub CLI実行 |
| `github_issue_list` | issueをリスト |
| `github_issue_view` | issue詳細を表示 |
| `github_pr_view` | PR詳細を表示 |
| `github_pr_create` | PRを作成 |
| `github_pr_merge` | PRをマージ |

**注**: `gh` CLIのインストールと認証が必要

#### テレメトリーツール (2ツール)

| ツール | 説明 |
|------|-------------|
| `telemetry_stats` | 使用統計を取得 |
| `telemetry_cost` | コストサマリーを取得 |

#### その他のツール (2ツール)

| ツール | 説明 |
|------|-------------|
| `fact_check_claim` | Web検索を使用して主張を検証 |
| `route_query` | 適切なエージェントにルーティング (プレースホルダー) |

---

### ❌ ローカル専用ツール (7ツール)

これらのツールは**Local MCPでのみ動作**します (Claude Desktop、Claude Code、Cursor):

| ツール | なぜローカル専用? | 代替手段 |
|------|-----------------|-------------|
| `file_read` | 直接ファイルシステムアクセス | コンテンツをコピー&ペースト |
| `file_write` | 直接ファイルシステムアクセス | 出力をコピー&ペースト |
| `dir_list` | 直接ファイルシステムアクセス | 手動でファイルをリスト |
| `shell_exec` | シェルコマンド実行 | GitHub CLIは `github_exec` を使用 |
| `media_open_image` | OSアプリケーションを開く | 該当なし |
| `media_open_audio` | OSアプリケーションを開く | 該当なし |
| `media_open_video` | OSアプリケーションを開く | 該当なし |

**将来**: Remote MCP経由のファイルアップロードはv4.1で計画中 ([Issue #462](https://github.com/JFK/kagura-ai/issues/462))

---

## 💡 推奨ワークフロー

### パターン1: 小さなデータ (コンテキストに保持) 🔵

**いつ使うか**: 現在の会話でのみ必要な少量の情報

**方法**:
```
ユーザー: "Python 3.13は2024年10月7日にリリースされました"
AI: [会話コンテキストに保持、保存なし]
```

**メリット**: 高速、オーバーヘッドなし
**デメリット**: 会話終了後に失われる

---

### パターン2: 重要なデータ (永続的メモリー) ⭐ 推奨

**いつ使うか**: 長期的に覚えておきたい情報

**方法**:
```
ユーザー: "バックエンドプロジェクトではDjangoよりもFastAPIを好むことを覚えておいて。
       これは重要で永続的である必要があります。"

AI: [scope="persistent"でmemory_storeを使用]
```

**後で**:
```
ユーザー: "新しいプロジェクトにはどのバックエンドフレームワークを使うべきですか?"
AI: [memory_recall/searchを使用して設定を取得]
```

**メリット**:
- 会話を超えて存続
- すべてのAIプラットフォームで動作
- セマンティックに検索可能

**デメリット**: 覚えておくための明示的な指示が必要

**ベストプラクティス**:
- "覚えて"、"保存"、"永続化"などのキーワードを使用
- 明示的に: "これは重要です"
- コンテキストを追加: "バックエンドプロジェクト用"

---

### パターン3: 大きなデータ (マルチモーダルRAG) 🚀

**いつ使うか**: 大きなドキュメント、画像、複数ファイル

**方法** (Gemini API必須):
```
ユーザー: "./photosディレクトリ内のすべての画像をインデックス化して"
AI: [multimodal_indexを使用]

ユーザー: "犬が写っている写真を検索して"
AI: [multimodal_searchを使用]
```

**メリット**:
- 大規模なデータセットを処理
- セマンティック画像検索
- 多言語サポート

**デメリット**:
- Gemini APIキーが必要
- Remote MCP経由のファイルアップロードはまだ利用不可 (v4.1で提供予定)

**現在の回避策**: ファイルのインデックス化にはLocal MCP (Claude Desktop) を使用

---

## 📝 プロンプト例 (コピー&ペースト)

### メモリー操作

**保存**:
```
"私のプロジェクトの締切は2025年12月31日であることを覚えておいて。これは重要です。"

"この情報を保存: 私はAcme CorpでPython開発者として働いています"

"私のコーディングスタイルの設定を覚えておいて: 常に型ヒントとdocstringを使用"
```

**検索**:
```
"私のプロジェクトの締切について何を覚えていますか?"

"私のコーディング設定に関連するすべてのメモリーを検索"

"私について何を知っていますか?"

"'python'でタグ付けされたすべてのメモリーを表示"
```

**削除**:
```
"私の古いJavaScriptの設定について忘れて"

"私の前職についてのメモリーを削除"
```

**統計**:
```
"私についてのメモリーはいくつありますか?"

"メモリー統計を表示"

"私の最も一般的なトピックは何ですか?"
```

---

### Web検索

**最新ニュース**:
```
"Pythonの最新バージョンは何ですか? Webを検索して。"

"FastAPIフレームワークに関する最近のニュースを検索"

"Python 3.13のリリースノートを検索"
```

**比較**:
```
"FastAPIとDjangoを比較。長所と短所をWebで検索して。"

"PostgreSQLとMySQLを比較するベンチマークを検索"
```

**画像**:
```
"'ニューラルネットワークアーキテクチャ図'の画像を検索"

"VSCodeテーマのスクリーンショットを検索"
```

---

### YouTube

**要約**:
```
"このYouTube動画を要約して: https://www.youtube.com/watch?v=xxxxx"

"このチュートリアル動画から要点を教えて: [URL]"
```

**ファクトチェック**:
```
"この動画で主張されていることを事実確認して: [URL]"

"[URL]で言及されている統計が正確か検証して"
```

**文字起こし**:
```
"この動画の文字起こしを取得: [URL]"

"このチュートリアルからコード例を抽出: [URL]"
```

---

### コーディング

**セッション開始**:
```
"ユーザー認証の実装のためのコーディングセッションを開始"

"Issue #123での作業の追跡を開始"
```

**変更の追跡**:
```
"auth.pyを修正してOAuth2サポートを追加しました"

"データベース接続のバグを修正したことを記録"
```

**エラーの記録**:
```
"このエラーを記録: [スタックトレースを貼り付け]"

"スクリーンショット付きでこのTypeScriptエラーを記録"
```

**過去のエラーを検索**:
```
"この'Connection refused'エラーを以前見たことがありますか?"

"過去のセッションから類似のデータベースマイグレーションエラーを検索"
```

**セッション終了**:
```
"コーディングセッションを終了して要約を生成"

"セッションを終了してPR説明を作成"
```

---

### GitHub

**Issueのリスト**:
```
"JFK/kagura-aiリポジトリのオープンなissueをリスト"

"'bug'と'priority:high'のラベルが付いたissueを表示"
```

**詳細表示**:
```
"issue #463の詳細を取得"

"PR #472を表示"
```

**安全な実行**:
```
"実行: gh issue list --repo JFK/kagura-ai --state open"

"実行: gh pr view 472"
```

---

## 🌍 クロスプラットフォームメモリー

### user_id管理

**ベストプラクティス**: 個人的なメモリーには常に `user_id` を指定

```python
# ✅ 良い
memory_store(
    user_id="user_jfk",
    key="python_preference",
    value="DjangoよりもFastAPIを好む"
)

# ❌ 悪い (デフォルトユーザーを使用)
memory_store(
    key="python_preference",
    value="DjangoよりもFastAPIを好む"
)
```

**プロンプト例**:
```
"user_id='john_doe'用にこれを覚えて: ダークモードを好みます"
```

---

### agent_nameスコーピング

`agent_name`でメモリースコープを制御:

**グローバルメモリー** (すべての会話で共有):
```python
memory_store(
    agent_name="global",
    key="coding_style",
    value="常に型ヒントを使用"
)
```

**スレッド固有メモリー** (この会話のみ):
```python
memory_store(
    agent_name="thread_abc123",
    key="temp_data",
    value="..."
)
```

**プロンプト例**:
```
"これをグローバルに覚えて: JavaScriptよりもPythonを好む"

"この会話だけのためにこれを覚えて: 現在のプロジェクトは'kagura-ai'"
```

---

### メモリー永続化

**v4.4.0 から**: すべてのメモリーはデフォルトで永続化されます:
```python
memory_store(key="my_data", value="...")  # 常に永続化
```

**プロンプト例**:
```
"これを覚えて: 私のメールアドレスはjohn@example.comです"

"メモリーに保存: 現在のプロジェクトは'kagura-ai'"
```

**注意**: 一時データが必要な場合は、クライアント側の変数を使用するか、使用後に明示的に削除してください:
```
memory_delete(key="temporary_data")
```

---

## ❓ よくある質問 (FAQ)

### Q: なぜファイルを添付できないのですか?

**A**: Remote MCP (ChatGPT、Claude Chat) は現在、ファイルアップロードをサポートしていません。

**回避策**:
1. ファイルの内容をチャットに直接コピー&ペースト
2. ファイル操作にはLocal MCP (Claude Desktop、Claude Code) を使用
3. v4.1のマルチモーダルアップロードAPIを待つ ([Issue #462](https://github.com/JFK/kagura-ai/issues/462))

---

### Q: 会話が終わるとメモリーが消えてしまいます。なぜですか?

**A**: v4.4.0 から、すべてのメモリーは永続化されます。メモリーが消える場合は、以下を確認してください:
- 同じ `user_id` を使用しているか
- 同じ `agent_name` を使用しているか
- メモリーが正しく保存されたか（`memory_search()` で確認）

**解決策**: 明確な保存指示を使用:
```
"これを覚えて: [あなたのデータ]"
"メモリーに保存: [あなたのデータ]"
```

または直接確認:
```
"scope='persistent'でこれを保存: [あなたのデータ]"
```

---

### Q: 異なるAIプラットフォーム間でメモリーを共有するには?

**A**: `user_id`を一貫して使用:

1. **ChatGPT**:
   ```
   "user_id='john'用にこれを保存: Pythonを好む"
   ```

2. **Claude Chat** (同じuser_id):
   ```
   "user_id='john'はどのプログラミング言語を好みますか?"
   ```

両方のAIが同じKaguraメモリーにアクセスします!

---

### Q: 検索結果が不正確です。どうすれば改善できますか?

**A**: より良い検索のためのヒント:

1. **セマンティック検索を使用** (正確なキーワードではなく):
   ```
   ✅ "バックエンド開発に関するメモリーを検索"
   ❌ "'FastAPI Django比較'を検索"
   ```

2. **保存時にタグを追加**:
   ```
   "tags=['python', 'backend', 'framework']でこれを覚えて:
    FastAPIを好む"
   ```

3. **ハイブリッド検索を使用** (BM25 + ベクトル):
   ```
   "ハイブリッド検索を使用して'FastAPI'のメモリーを検索"
   ```

4. **フィードバックを提供**:
   ```
   "メモリー[key]を有用としてマーク"
   "このメモリーは古くなっています"
   ```

---

### Q: どのくらいコストがかかりますか?

**A**: Kagura AIはオープンソースで、セルフホストは無料です。

**コスト**:
- **セルフホスティング**: 無料 (ローカルのChromaDBを使用)
- **クラウドホスティング**: サーバーコスト (AWS、DigitalOceanなど)
- **AI API**:
  - 埋め込み用のOpenAI/Anthropic/Google API (オプション)
  - Brave Search API (オプション、無料層あり)
  - マルチモーダル用のGemini API (オプション)

**コスト追跡**:
```
"テレメトリーコストサマリーを表示"
```

---

### Q: 私のデータはプライベートですか?

**A**: はい! Kaguraは**プライバシー第一**です:

- ✅ **セルフホスト**: データはあなたのもの
- ✅ **ローカルストレージ**: あなたのマシン上のSQLite + ChromaDB
- ✅ **ベンダーロックインなし**: いつでもエクスポート (JSONL形式)
- ✅ **オープンソース**: コードを自分で監査可能

**データのエクスポート**:
```bash
kagura memory export --output=./backup --format=jsonl
```

---

## 🔧 トラブルシューティング

### メモリーが見つからない

**症状**: "Xについてのメモリーがありません"

**原因**:
1. 間違った `user_id`
2. 間違った `agent_name`
3. メモリーが正しく保存されていない

**デバッグ**:
```
"すべてのメモリーをリスト"
"メモリー統計を表示"
"フィルターなしでメモリーを検索"
```

---

### 検索結果が何も返さない

**症状**: `memory_search` が空の結果を返す

**解決策**:
1. **メモリーが存在するか確認**:
   ```
   "すべてのメモリーをリスト"
   ```

2. **異なる検索クエリを試す**:
   ```
   ✅ "コーディングに関するメモリーを検索"
   ❌ "正確なキー'python_coding_style_2024'でメモリーを検索"
   ```

3. **正確なキーには`memory_recall`を使用**:
   ```
   "key='python_preference'でメモリーを呼び出し"
   ```

---

### 高いAPIコスト

**症状**: 埋め込みAPIコストが高い

**解決策**:
1. **ローカル埋め込みを使用** (sentence-transformers):
   ```bash
   # APIコストなし、ローカルで実行
   pip install kagura-ai[ai]
   ```

2. **検索頻度を減らす**:
   - `memory_search`の代わりに`memory_recall` (正確なキー) を使用
   - `memory_search_ids` (低トークンモード) を使用

3. **コストを監視**:
   ```
   "テレメトリーコストサマリーを表示"
   ```

---

### Remote MCP接続が失敗する

**症状**: AIがKaguraに接続できない

**デバッグ**:
1. **サーバーが実行中か確認**:
   ```bash
   curl http://localhost:8080/api/v1/health
   ```

2. **API keyを確認** (認証を使用している場合):
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" \
        http://localhost:8080/api/v1/health
   ```

3. **ログを確認**:
   ```bash
   docker compose logs -f api
   ```

参照: [トラブルシューティングガイド](./troubleshooting.md)

---

## 🚀 上級のヒント

### 1. ナレッジディスカバリーのためのGraphMemory

**関連メモリーをリンク**:
```
"私のPython設定メモリーをFastAPIチュートリアルメモリーとリンク"

"'バックエンド開発'に関するすべてのメモリーをナレッジグラフに接続"
```

**関係を発見**:
```
"私のPython設定に関連するメモリーは何ですか?"

"2ホップ以内で'FastAPI'に接続されているすべての概念を検索"
```

---

### 2. パターン分析

**インタラクションを分析**:
```
"過去のセッションから私のコーディングパターンを分析"

"私の最も一般的なトピックは何ですか?"

"私のインタラクション統計を表示"
```

**インサイトを取得**:
```
"私が最もよく使うプログラミング言語は何ですか?"

"私が最も生産的な時間帯は?"
```

---

### 3. セッションサマリー

**コーディングセッションを追跡**:
```
"Issue #123のコーディングセッションを開始"

[... コードを作業 ...]

"セッションを終了してコスト追跡付きのAI要約を生成"
```

**PR説明を生成**:
```
"現在のコーディングセッションからPR説明を生成"
```

---

### 4. ファクトチェックワークフロー

**主張を検証**:
```
"この主張を事実確認: Python 3.13は3.12より40%高速"

"このYouTube動画の統計を検証: [URL]"
```

**ソースをクロスリファレンス**:
```
"ニューラルネットワーク最適化に関する論文をarXivで検索"

"最近のニュース記事と主張を比較"
```

---

## 🔗 関連ドキュメント

- **セットアップガイド**:
  - [MCP over HTTP/SSE (ChatGPT)](./mcp-http-setup.md)
  - [Claude Desktopセットアップ](./mcp-setup.md)
  - [Claude Codeセットアップ](./mcp-claude-code-setup.md)

- **プラットフォーム固有のワークフロー**:
  - [ChatGPTワークフロー例](./examples/chatgpt-workflow.md)
  - [Claudeワークフロー例](./examples/claude-workflow.md)

- **技術リファレンス**:
  - [REST APIリファレンス](./api-reference.md)
  - [セルフホスティングガイド](./self-hosting.md)
  - [アーキテクチャ概要](./architecture.md)

- **上級トピック**:
  - [メモリーエクスポート/インポート](./memory-export.md)
  - [トラブルシューティングガイド](./troubleshooting.md)

---

## 📚 追加リソース

### 公式リンク
- [GitHubリポジトリ](https://github.com/JFK/kagura-ai)
- [PyPIパッケージ](https://pypi.org/project/kagura-ai/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

### コミュニティ
- [GitHub Issues](https://github.com/JFK/kagura-ai/issues) - バグレポート＆機能リクエスト
- [GitHub Discussions](https://github.com/JFK/kagura-ai/discussions) - Q&A＆コミュニティ

---

**Version**: 4.0.0
**Last updated**: 2025-11-02
