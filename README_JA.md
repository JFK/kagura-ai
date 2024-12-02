![Kagura AI ロゴ](https://www.kagura-ai.com/assets/kagura-logo.svg)

![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)
![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)
![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)
![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

# Kagura AI

Kagura AI は、日本の伝統芸能 **神楽 (Kagura)** にインスパイアされたオープンソースフレームワークです。
「調和」「つながり」「尊重」を象徴するこのフレームワークは、柔軟でモジュール化されたAIエージェントを効率的に構築・設定・オーケストレーションすることを目指しています。

---

## なぜ Kagura AI なのか？

Kagura AI は、**神楽 (Kagura)** の哲学を体現し、調和やつながり、バランスの原則をデジタルの世界に適用しています。このプロジェクトは、以下の価値を提供します：

- **調和**: 様々なテクノロジーを統合し、効率的なワークフローを実現。
- **つながり**: エージェント間のシームレスなデータ共有を促進。
- **創造性**: 先進的なAIソリューションを伝統的な原則と組み合わせる。

---

## 主な機能

- **YAML ベースの設定**: 人間が読みやすい形式でエージェントやワークフローを定義。
- **マルチ LLM 対応**: OpenAI、Anthropic、Ollama、Google などと簡単に連携。
- **状態管理**: Pydantic ベースの型安全な状態定義。
- **ワークフローのオーケストレーション**: 複雑なワークフローを構築可能。
- **拡張性**: カスタムツールやフック、プラグインを追加して機能を拡張。
- **多言語対応**: 複数言語をネイティブにサポート。
- **Redis 統合**: オプションでエージェントの永続的なメモリを提供。

---

## インストール

### GitHub からインストール
```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
poetry install
```

### PyPI からインストール
```bash
pip install kagura-ai
```

---

## クイックスタート

Kagura AI は、YAML ファイルを使ったエージェントの作成を簡単にします。以下は、エージェント設定の例です。

### エージェント設定例
```yaml
# ~/.config/kagura/agents/my_agent/agent.yml
llm:
  model: openai/gpt-4
  max_tokens: 4096
description:
  - language: ja
    text: "テキストを要約する簡単なエージェントです。"
instructions:
  - language: ja
    text: "入力されたテキストを要約してください。"
prompt:
  - language: ja
    template: |
      次の内容を要約してください: {TEXT}
response_fields:
  - summary
```

---

## 使用方法

### Kagura AI を起動
```bash
kagura
```

### CLI コマンド
- `kagura`: インタラクティブなエージェントインターフェースを起動。
- `kagura create`: 新しいエージェント設定を作成。
- `kagura --help`: 使用可能なコマンドを表示。

---

## 応用機能

### マルチエージェントワークフロー
複雑なワークフローを、動的ルーティングやエージェント間のデータ共有を使って設計可能。
```yaml
workflow:
  agents:
    - name: text_fetcher
    - name: text_summarizer
  edges:
    - from: text_fetcher
      to: text_summarizer
```

### Redis の設定
永続的なメモリを有効化：
```yaml
# ~/.config/kagura/agents/system.yml
redis:
  host: localhost
  port: 6379
```

---

## ロードマップ

- 🌐 **Web API インターフェース**: RESTful API を通じてエージェントを提供。
- 🧠 **メモリ管理**: Redis または類似バックエンドによる永続的なメモリ。
- 📚 **ナレッジ統合**: RAG（検索強化生成）のサポート。
- 🐳 **Docker デプロイ**: Docker コンテナを使った簡単なセットアップ。

---

## Kagura AI に貢献する

Kagura AI プロジェクトでは、経験豊富な開発者から初心者まで、すべてのコントリビューターを歓迎しています。一緒に Kagura AI の未来を築きましょう！

### 貢献方法
- バグや問題の報告。
- 新しい機能や改善案の提案。
- コードやドキュメントの提出。
- テストやレビューの支援。

### コントリビューションのステップ
1. [コントリビューションガイド (日本語)](./CONTRIBUTING_JP.md) または [Contributing Guide (English)](./CONTRIBUTING_EN.md) を確認。
2. リポジトリをフォークし、ローカルにクローン。
3. ブランチを作成して作業を行い、Pull Request を送信。

---

## ドキュメントとリソース

- [公式ウェブサイト](https://www.kagura-ai.com)
- [完全なドキュメント](https://www.kagura-ai.com/docs)
- [クイックスタートガイド](https://www.kagura-ai.com/quickstart)
- [Issue やディスカッション](https://github.com/JFK/kagura-ai/issues)

---

**Kagura AI** の探求にご興味を持っていただき、ありがとうございます！共に調和のとれた革新的で責任ある AI ソリューションを構築していきましょう。
