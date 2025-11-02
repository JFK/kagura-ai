# ChatGPT + Kagura AI ワークフロー例

> **Kagura AIとChatGPTを使用した実践的なワークフロー**

このガイドは、Remote MCPを介してKagura AIをChatGPTと統合するための実世界のワークフロー例を提供します。

---

## 📋 セットアップ

### 前提条件

1. **Kagura Remote MCPサーバー** が実行中
2. **ChatGPT** がMCP接続で設定済み
3. **API Keys** (オプション): Brave Search、Gemini

参照: [MCP over HTTP/SSE セットアップガイド](../mcp-http-setup.md)

---

## 🎯 ワークフロー1: プロジェクト管理

**ユースケース**: 複数の会話でプロジェクトタスク、会議メモ、決定事項を追跡

### セッション例1: 朝の計画

```
ユーザー: "kagura-ai v4.0 ドキュメント用の新しいプロジェクト追跡セッションを開始して"

ChatGPT: [coding_start_sessionを使用]

ユーザー: "tags=['documentation', 'v4.0']でこれらの優先事項を覚えて:
       1. チャット統合のヒント
       2. ワークフロー例
       3. トラブルシューティングガイド"

ChatGPT: [scope="persistent"でmemory_storeを使用]

ユーザー: "プロジェクトの締切を2025年11月15日に設定。これは重要です。"

ChatGPT: [memory_storeを使用]
```

### セッション例2: 午後の作業

```
ユーザー: "私のドキュメントの優先事項は何ですか?"

ChatGPT: [tags=['documentation', 'v4.0']でmemory_searchを使用]
         "あなたの優先事項は:
          1. チャット統合のヒント
          2. ワークフロー例
          3. トラブルシューティングガイド"

ユーザー: "チャット統合のヒントドキュメントを完成させました。これを記録して。"

ChatGPT: [coding_track_file_changeを使用]

ユーザー: "技術ドキュメントの作成のベストプラクティスをWebで検索"

ChatGPT: [brave_web_searchを使用]
```

### セッション例3: 夕方のレビュー

```
ユーザー: "私のプロジェクトの締切は?"

ChatGPT: [memory_recallを使用]
         "あなたの締切は2025年11月15日です"

ユーザー: "コーディングセッションを終了して要約を生成"

ChatGPT: [coding_end_sessionを使用]
         "要約: チャット統合のヒントを完成 (370行)。
          コスト: 埋め込みに$0.15。残り: ワークフロー例、
          トラブルシューティングガイド。"
```

### メリット

- ✅ **永続的メモリー**: タスクは会話を超えて存続
- ✅ **クロスプラットフォーム**: 任意のChatGPTセッションからアクセス
- ✅ **AI要約**: コスト追跡付きの自動セッション要約
- ✅ **検索可能**: タグ、キーワード、またはセマンティック検索でタスクを検索

---

## 📚 ワークフロー2: 学習と研究ノート

**ユースケース**: YouTube動画、Web記事、論文から個人的なナレッジベースを構築

### 例: FastAPIを学ぶ

```
ユーザー: "FastAPIを学んでいます。これを追跡開始して。"

ChatGPT: [coding_start_sessionを使用]

ユーザー: "YouTubeで'FastAPI tutorial for beginners'を検索"

ChatGPT: [brave_video_searchを使用]
         "見つかりました: 'FastAPI Tutorial - Build a REST API in 15 Minutes'
          URL: https://www.youtube.com/watch?v=xxxxx"

ユーザー: "この動画を要約して: https://www.youtube.com/watch?v=xxxxx"

ChatGPT: [youtube_summarizeを使用]
         "要約: FastAPIの基本をカバー、ルーティング、
          Pydanticモデル、自動ドキュメント、非同期サポート..."

ユーザー: "tags=['fastapi', 'tutorial', 'learning']でこの要約を覚えて。
       これは将来の参照のために重要です。"

ChatGPT: [scope="persistent"でmemory_storeを使用]

ユーザー: "API パフォーマンス最適化に関する論文をarXivで検索"

ChatGPT: [arxiv_searchを使用]

ユーザー: "tags=['fastapi', 'performance', 'research']でトップ3の論文を覚えて"

ChatGPT: [memory_storeを使用]

ユーザー: "FastAPIとDjangoのパフォーマンスベンチマークをWebで検索"

ChatGPT: [brave_web_searchを使用]

ユーザー: "tags=['fastapi', 'django', 'comparison']でこの比較を保存:
       FastAPI: 非同期ワークロードで3倍高速、より良い型安全性
       Django: より多くのバッテリー同梱、大きなエコシステム"

ChatGPT: [memory_storeを使用]
```

### 後のセッション: ナレッジを思い出す

```
ユーザー: "FastAPIについて何を学びましたか?"

ChatGPT: [query="FastAPI learning"でmemory_searchを使用]
         "あなたが学んだこと:
          1. FastAPIチュートリアル要約 (非同期、Pydantic、自動ドキュメント)
          2. パフォーマンス: 非同期でDjangoより3倍高速
          3. 研究論文: [3つの論文をリスト]"

ユーザー: "'fastapi'でタグ付けされたすべてのメモリーを表示"

ChatGPT: [tags=['fastapi']でmemory_searchを使用]

ユーザー: "FastAPIとDjangoの主な違いは何ですか?"

ChatGPT: [memory_recallを使用]
         "FastAPI: 非同期で3倍高速、より良い型安全性
          Django: より多くのバッテリー同梱、大きなエコシステム"
```

### メリット

- ✅ **ナレッジ保持**: 学んだことを決して忘れない
- ✅ **整理**: 簡単な取得のためのタグ
- ✅ **マルチソース**: YouTube、Web、arXiv、すべて一箇所に
- ✅ **検索可能**: セマンティック検索が関連トピックを見つける

---

## 💻 ワークフロー3: コード開発とエラー追跡

**ユースケース**: コーディングセッション、エラー、将来の参照のためのソリューションを追跡

### 例: Pythonエラーのデバッグ

```
ユーザー: "'データベース接続問題の修正'のためのコーディングセッションを開始"

ChatGPT: [coding_start_sessionを使用]

ユーザー: "このエラーが発生しています:
       psycopg2.OperationalError: could not connect to server:
       Connection refused"

ChatGPT: "過去の類似エラーを検索させてください"
         [coding_search_errorsを使用]

         "2週間前に類似のエラーに遭遇しました。解決策は:
          PostgreSQLが実行中か確認: sudo systemctl start postgresql"

ユーザー: "それで直りました! このソリューションを記録して。"

ChatGPT: [ソリューション付きでcoding_record_errorを使用]

ユーザー: "接続コードにリトライロジックも追加しました"

ChatGPT: "素晴らしい設計決定です。記録させてください。"
         [coding_record_decisionを使用]

ユーザー: "PostgreSQL接続プーリングのベストプラクティスをWebで検索"

ChatGPT: [brave_web_searchを使用]

ユーザー: "tags=['postgresql', 'connection-pooling', 'best-practice']でこれを覚えて:
       本番環境では接続プーリングにpgBouncerを使用。
       最大プールサイズ = (2 × CPUコア) + ディスク数"

ChatGPT: [memory_storeを使用]

ユーザー: "セッションを終了して要約を生成"

ChatGPT: [coding_end_sessionを使用]
         "要約: PostgreSQL接続エラーを修正。リトライロジックを追加。
          接続プーリングのベストプラクティスを研究。
          変更されたファイル: 1 (database.py)
          コスト: $0.08"
```

### 後で: 類似エラーに遭遇

```
ユーザー: "また'Connection refused'エラーが発生しています"

ChatGPT: [coding_search_errorsを使用]
         "以前に見たことがあります! 解決策:
          1. PostgreSQLが実行中か確認
          2. database.pyにリトライロジックを追加しました
          3. プーリングにpgBouncerの使用を検討"

ユーザー: "接続プーリングのベストプラクティスは何でしたか?"

ChatGPT: [memory_searchを使用]
         "あなたが学んだこと: 本番環境でpgBouncerを使用。
          最大プールサイズ = (2 × CPUコア) + ディスク数"
```

### メリット

- ✅ **エラー履歴**: 同じ問題を二度とデバッグしない
- ✅ **ソリューション追跡**: 何が機能したかを覚えている
- ✅ **設計決定**: なぜそのソリューションを選んだかを文書化
- ✅ **パターン学習**: AIがコーディングパターンを分析

---

## 🎨 ワークフロー4: コンテンツ作成と執筆

**ユースケース**: 永続的メモリーで研究、下書き、コンテンツを洗練

### 例: ブログ投稿を書く

```
ユーザー: "'なぜFastAPIはML APIに最適か'についてブログ投稿を書いています。
       これを追跡開始して。"

ChatGPT: [coding_start_sessionを使用]

ユーザー: "最新のFastAPI採用統計をWebで検索"

ChatGPT: [brave_web_searchを使用]

ユーザー: "tags=['fastapi', 'adoption', 'blog']でこれらの統計を覚えて:
       - GitHub スター 50K+
       - Netflix、Uber、Microsoftで使用
       - 非同期でFlaskより3倍高速"

ChatGPT: [memory_storeを使用]

ユーザー: "MLサービングパフォーマンスに関する研究論文を検索"

ChatGPT: [arxiv_searchを使用]

ユーザー: "本番環境でのFastAPIに関するYouTubeトークを検索"

ChatGPT: [brave_video_searchを使用]

ユーザー: "このトークを要約: [URL]"

ChatGPT: [youtube_summarizeを使用]

ユーザー: "tags=['blog', 'outline']でこのアウトラインを保存:
       1. 導入 (FastAPI採用)
       2. パフォーマンスベンチマーク
       3. ML固有の機能 (Pydantic、非同期)
       4. 本番環境のケーススタディ
       5. 結論"

ChatGPT: [memory_storeを使用]
```

### 次のセッション: 下書きを書く

```
ユーザー: "ブログ投稿のアウトラインを表示"

ChatGPT: [memory_recallを使用]

ユーザー: "収集した統計は何ですか?"

ChatGPT: [tags=['fastapi', 'adoption']でmemory_searchを使用]

ユーザー: "導入を終えました。この変更を追跡して。"

ChatGPT: [coding_track_file_changeを使用]
```

### 最後のセッション: 公開

```
ユーザー: "セッションを終了して執筆ログの要約を生成"

ChatGPT: [coding_end_sessionを使用]
         "ブログ投稿完成: 'なぜFastAPIはML APIに最適か'
          研究: 5つのWebソース、3つの論文、2つのYouTubeトーク
          セクション: 5 (すべて完了)
          コスト: $0.22"

ユーザー: "2025年11月10日に公開することを覚えて"

ChatGPT: [tags=['blog', 'deadline']でmemory_storeを使用]
```

### メリット

- ✅ **研究整理**: すべてのソースが一箇所に
- ✅ **バージョン追跡**: アウトラインと下書きの変更を追跡
- ✅ **クロスセッション**: いつでも作業を再開
- ✅ **AI要約**: 自動進捗要約

---

## 📊 ワークフロー5: データ分析とインサイト

**ユースケース**: 自分のインタラクションパターンと興味を分析

### 例: 自己省察

```
ユーザー: "過去1か月のコーディングパターンを分析"

ChatGPT: [coding_analyze_patternsを使用]
         "あなたのパターン:
          - 主要言語: Python (85%)
          - フレームワーク: FastAPI (60%)、Django (25%)、Flask (15%)
          - 最も一般的なエラー: データベース接続 (12回)
          - ピークコーディング時間: 午前9-11時、午後2-4時
          - 平均セッション: 2.3時間"

ユーザー: "私が最もインタラクションするトピックは何ですか?"

ChatGPT: [memory_get_user_patternを使用]
         "あなたのトップ興味:
          1. バックエンド開発 (FastAPI、Django)
          2. データベース最適化 (PostgreSQL)
          3. API設計
          4. ドキュメント作成
          5. Pythonベストプラクティス"

ユーザー: "メモリー統計を表示"

ChatGPT: [memory_statsを使用]
         "メモリーヘルスレポート:
          - 総メモリー: 342
          - 永続的: 198 (57.8%)
          - ワーキング: 144 (42.2%)
          - トップタグ: python (87)、fastapi (56)、tutorial (42)
          - ストレージ: 2.4 MB
          - 最後のクリーンアップ: 3日前"

ユーザー: "最も有用なメモリーは何ですか?"

ChatGPT: [フィルター付きでmemory_listを使用]
         "トップ評価メモリー (有用性スコアによる):
          1. PostgreSQL接続プーリングのベストプラクティス (0.95)
          2. FastAPI vs Django比較 (0.92)
          3. Python型ヒントガイド (0.88)"
```

### メリット

- ✅ **自己認識**: コーディング習慣を理解
- ✅ **興味追跡**: 気にかけているトピックを確認
- ✅ **メモリーヘルス**: メモリー使用を監視・最適化
- ✅ **品質メトリクス**: 最も価値のあるメモリーを特定

---

## 🔄 ワークフロー6: クロスプラットフォーム継続性

**ユースケース**: ChatGPTで作業を開始し、Claude Desktop/Codeで続行

### 朝: ChatGPT (Web)

```
ユーザー: "user_id='john_doe'用に覚えて: 今日のタスクは
       FastAPIプロジェクトにOAuth2認証を実装すること"

ChatGPT: [user_id="john_doe"でmemory_storeを使用]

ユーザー: "OAuth2のベストプラクティスを検索"

ChatGPT: [brave_web_searchを使用]

ユーザー: "tags=['oauth2', 'plan']でこの実装計画を保存:
       1. python-jose、passlibをインストール
       2. ユーザーモデルを作成
       3. トークンエンドポイントを実装
       4. 保護されたルートを追加
       5. テストを書く"

ChatGPT: [memory_storeを使用]
```

### 午後: Claude Desktop (ローカル)

```
ユーザー: "user_id='john_doe'用に今日設定したタスクは何ですか?"

Claude: [user_id="john_doe"でmemory_recallを使用]
        "今日のタスク: FastAPIでOAuth2認証を実装"

ユーザー: "実装計画を表示"

Claude: [tags=['oauth2', 'plan']でmemory_searchを使用]

ユーザー: "現在のauth.pyファイルを読んで"

Claude: [file_readを使用 - Local MCPのみ]

ユーザー: "ステップ1-3を実装しました。user_id='john_doe'用にこれらの変更を追跡"

Claude: [coding_track_file_changeを使用]
```

### 夕方: ChatGPT (モバイル)

```
ユーザー: "user_id='john_doe'がOAuth2で何の進捗をしましたか?"

ChatGPT: [memory_search + coding session historyを使用]
         "ステップ1-3を完了:
          1. ✅ 依存関係をインストール
          2. ✅ ユーザーモデルを作成
          3. ✅ トークンエンドポイントを実装
          残り: 保護されたルート、テスト"
```

### メリット

- ✅ **プラットフォーム独立性**: デバイス間でシームレスに作業
- ✅ **コンテキスト保持**: 現在地を決して失わない
- ✅ **統一メモリー**: 唯一の真実のソース
- ✅ **柔軟なワークフロー**: 各タスクに最適なツールを使用

---

## 💡 プロのヒント

### 1. 一貫したuser_idを使用

プラットフォーム間で常に同じ `user_id` を指定:

```
"user_id='john_doe'用に覚えて: [情報]"
```

### 2. すべてにタグを付ける

タグは取得を簡単にします:

```
"tags=['python', 'best-practice', 'typing']でこれを保存: ..."
```

### 3. 永続性について明示的に

デフォルトに依存しない:

```
"これを永久に覚えて: ..."
"このセッション用に一時的にこれを保存: ..."
```

### 4. セマンティック検索を使用

正確なキーワードを検索しない:

```
✅ "データベース最適化に関するメモリーを検索"
❌ "キー'postgresql_connection_pooling_2024'でメモリーを検索"
```

### 5. フィードバックを提供

Kaguraが何が有用かを学ぶのを助ける:

```
"このメモリーを非常に有用としてマーク"
"この情報は古くなっています"
```

---

## 🔗 関連リソース

- [チャット統合のヒント](../chat-integration-tips.md) - メインガイド
- [Claudeワークフロー例](./claude-workflow.md) - Claude固有のワークフロー
- [MCPセットアップ (ChatGPT)](../mcp-http-setup.md) - セットアップガイド

---

**Version**: 4.0.0
**Last updated**: 2025-11-02
