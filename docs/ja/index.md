---
title: Kagura AI - Universal AI Memory Platform
description: あなたのメモリーを所有し、すべてのAIで活用。Claude、ChatGPT、Gemini、そしてすべてのAIプラットフォーム向けのMCP-nativeメモリー。
keywords:
  - Universal Memory
  - AI Memory
  - MCP Protocol
  - ChatGPT Connector
  - Claude Desktop
  - Self-hosted AI
  - Memory Platform
author: Fumikazu Kiyota
robots: index, follow
og_title: Kagura AI - Universal AI Memory Platform
og_type: website
og_url: https://www.kagura-ai.com
og_description: あなたのメモリーを所有し、すべてのAIで活用。すべてのAIプラットフォーム向けのMCP-nativeユニバーサルメモリー。
og_image: assets/kagura-logo.svg
twitter_card: summary_large_image
twitter_site: "@kagura_ai"
twitter_creator: "@JFK"
---

# Kagura AI

![Kagura AI Logo](assets/kagura-logo.svg)

**Universal AI Memory Platform**

> あなたのメモリーを所有し、すべてのAIで活用。

Claude Desktop、ChatGPT、Gemini、そしてすべてのAIプラットフォームを共有コンテキストとメモリーで接続する、MCP-nativeメモリーインフラストラクチャ。

---

## Kagura AI v4.0とは？

すべてのAIがあなたの好み、コンテキスト、履歴を全プラットフォームで記憶できるようにする、ユニバーサルメモリーレイヤーです。

```
朝: ChatGPTがあなたの一日の計画を支援
     ↓ (あなたの好みを記憶)

午後: Claude Desktopがあなたとコードを書く
      ↓ (あなたのコーディングスタイルを知っている)

夕方: Geminiがあなたのドキュメントを分析
      ↓ (あなたのプロジェクトコンテキストを思い出す)
```

**1つのメモリー。すべてのAI。**

---

## なぜKagura AIなのか？

### 個人向け

- 🔒 **プライバシー第一**: ローカルストレージまたはセルフホスト
- 🚫 **ベンダーロックインなし**: いつでも完全なデータエクスポート
- 🧠 **スマートな呼び出し**: ベクトル検索 + ナレッジグラフ
- 🌐 **ユニバーサル**: Claude、ChatGPT、Gemini、Cursor、Clineで動作

### 開発者向け

- 💻 **MCP-native**: Model Context Protocol経由の31ツール
- 🔌 **簡単な統合**: Claude Desktop向けの `kagura mcp install`
- 🛠️ **REST API**: OpenAPI付きFastAPIサーバー
- 📦 **本番環境対応**: Docker、認証、モニタリング

### チーム向け（近日公開）

- 👥 **共有知識**: チーム全体のメモリー
- 🔐 **エンタープライズ機能**: SSO、BYOK、監査ログ
- 📈 **分析**: チームのAI使用パターンを追跡

---

## コア機能

### 1. Universal Memory

一度保存すれば、どのAIからでもアクセス:

```python
# MCPツール経由（Claude Desktop、ChatGPT などで動作）
memory_store(
    user_id="jfk",
    agent_name="global",
    key="coding_style",
    value="Always use type hints in Python",
    scope="persistent",
    tags='["python", "best-practices"]'
)
```

### 2. MCP統合

**Claude Desktop**（ローカル、31個の全ツール）:
```bash
kagura mcp install  # 自動設定
# 利用可能なすべてのツール: メモリー、ファイル、ウェブ、シェル など
```

**ChatGPTコネクタ**（リモート、24個の安全なツール）:
```bash
docker compose up -d
# ChatGPTを http://localhost:8000/mcp に接続
# 安全なツールのみ（ファイル操作なし、シェルなし）
```

### 3. ナレッジグラフ

関係性とパターンを追跡:
- AI-ユーザーインタラクション履歴
- メモリーの関係性
- 学習パターン分析
- トピッククラスタリング

### 4. 完全なデータポータビリティ

```bash
# すべてをエクスポート
kagura memory export --output ./backup

# どこへでもインポート
kagura memory import --input ./backup
```

---

## クイックスタート

### オプション1: Claude Desktopユーザー

```bash
pip install kagura-ai[full]
kagura mcp install
# Claude Desktopを再起動 - 完了！
```

[Claude Desktopセットアップ →](mcp-setup.md)

### オプション2: ChatGPTユーザー

```bash
docker compose up -d
# ChatGPTコネクタを設定: http://localhost:8000/mcp
```

[ChatGPTコネクタセットアップ →](mcp-http-setup.md)

### オプション3: セルフホスト本番環境

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
cp .env.example .env  # DOMAIN、POSTGRES_PASSWORDを設定
docker compose -f docker-compose.prod.yml up -d
```

[セルフホスティングガイド →](self-hosting.md)

---

## 利用可能なツール（MCP）

**メモリー**（6ツール）:
- memory_store, memory_recall, memory_search
- memory_list, memory_delete, memory_feedback

**グラフ**（3ツール）:
- memory_record_interaction
- memory_get_related
- memory_get_user_pattern

**ウェブ/API**（10以上のツール）:
- web_search, web_scrape
- youtube_summarize, get_youtube_transcript
- brave_web_search, fact_check_claim

**ファイル操作**（ローカルのみ）:
- file_read, file_write, dir_list

**システム**:
- shell_exec（ローカルのみ）
- telemetry_stats, telemetry_cost

---

## ドキュメント

- [はじめに](getting-started.md) - 10分セットアップ
- [APIリファレンス](api-reference.md) - REST API + MCPツール
- [アーキテクチャ](architecture.md) - システム設計
- [セルフホスティング](self-hosting.md) - 本番デプロイメント
- [メモリーエクスポート/インポート](memory-export.md) - バックアップガイド

---

## コミュニティ

- [GitHub](https://github.com/JFK/kagura-ai) - ソースコード & Issues
- [PyPI](https://pypi.org/project/kagura-ai/) - パッケージダウンロード
- [サンプル](https://github.com/JFK/kagura-ai/tree/main/examples) - 使用例

---

## ステータス: v4.0.0（Phase C完了）

**最近完了**:
- ✅ Phase A: MCP-First Foundation
- ✅ Phase B: Graph Memory
- ✅ Phase C: Remote MCP Server + Export/Import

**機能**:
- ✅ 31個のMCPツール
- ✅ REST API（FastAPI）
- ✅ MCP over HTTP/SSE（ChatGPTコネクタ）
- ✅ APIキー認証
- ✅ メモリーエクスポート/インポート（JSONL）
- ✅ 本番環境Docker設定

**次の予定**: v4.0.0安定版リリース

---

**ユニバーサルAIメモリーのために ❤️ を込めて構築**
