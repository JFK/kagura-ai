# Kagura AI

![Kagura AI Logo](https://www.kagura-ai.com/assets/kagura-logo.svg)

![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)
![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)
![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)
![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

Kagura AI は、AI マルチエージェントの構築とオーケストレーションに特化した軽量なオープンソースフレームワークです。日本の伝統芸能「神楽（かぐら）」の名にちなみ、調和、つながり、そして敬意という精神を取り入れながら、YAMLベースの簡潔な設定で高度な AI エージェントシステムの実現を可能にします。

---

## なぜ Kagura AI なのか？

**Kagura AI** という名前は、神楽の持つ調和、つながり、バランスの原理を反映しています。これらの価値観を取り入れることで、Kagura AI は協調性、革新性、倫理的な設計を重視する責任ある AI システムの創造を目指しています。

- **調和**: 神楽が音楽、舞、儀式を一つの演目として融合させるように、多様な技術を統合的なワークフローへと結びつけます。
- **つながり**: 神楽が人、自然、神聖なるものを結びつけるように、エージェント間のシームレスな通信を実現します。
- **創造性**: 革新的な AI ソリューションと普遍的な原理を組み合わせ、伝統と芸術表現のバランスを体現します。

これらの原理は、柔軟で信頼性が高く、倫理的な AI エージェントの構築とオーケストレーションを実現する Kagura AI の**コア概念**の基盤となっています。

---

## コア概念

### アトミックエージェント
- **タスク特化型の操作**: アトミックエージェントは、高度に特化された個別タスクを効率的かつ独立して処理するように設計されています。
- **モジュール性と疎結合**: マイクロサービスのように、スタンドアロンユニットとして動作し、または他のエージェントと緩やかに結合して統合されます。
- **柔軟性**: 関数、ツール、外部 API との連携が可能で、より大規模なワークフローにシームレスに統合できます。

### オーケストレーションフレームワーク
- **マルチエージェントの連携**: 複数のアトミックエージェントを組み合わせて、複雑な多段階ワークフローを実行します。
- **動的ルーティング**: 高度なタスクオーケストレーションのための条件分岐とフロー制御をサポートします。
- **協調機能**: 個々のエージェントの自律性を維持しながら、統合されたシステムとして機能します。

### 状態とレスポンスの管理
- **型安全な状態管理**: Pydantic モデルを使用してワークフロー全体でのデータの整合性と一貫性を確保します。
- **レスポンスのカスタマイズ**: モジュール化されたレスポンスにより、要件の変更に迅速に対応できます。
- **デバッグと透明性**: 一元化された状態管理により、エラーの追跡が容易になり、システム全体の信頼性が向上します。

---

## 主な機能

- **アトミックエージェント設計**: 単独または
ワークフローの一部として実行される、高度に特化したタスク固有のエージェント
- **ワークフローオーケストレーション**: 動的ルーティングによる複雑な多段階プロセスの調整
- **状態とレスポンスの管理**: 型安全な状態とカスタマイズ可能なレスポンスによるデータの安全性とモジュール性の確保
- **YAML ベースの設定**: 人間が読みやすい形式でのエージェントとワークフローの定義
- **マルチ LLM サポート**: [LiteLLM](https://github.com/BerriAI/litellm) を通じて OpenAI、Anthropic、Ollama、Google などとシームレスに連携
- **拡張性**: ドメイン固有のタスク用のカスタムツール、フック、プラグインの追加が可能
- **多言語サポート**: 複数言語のネイティブサポート
- **Redis 統合**: エージェント用のオプションの永続メモリ

---

## インストール

### GitHub からのインストール
```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
poetry install
```

### PyPI からのインストール
```bash
pip install kagura-ai
```

---

## クイックスタート

Kagura AI は YAML ファイルを使用してエージェントの作成を簡素化します。以下はエージェントの設定例です。

### エージェント設定例
```yaml
# ~/.config/kagura/agents/my_agent/agent.yml
llm:
  model: openai/gpt-4o-mini # 例: ollama/qwen2.5:14b (LiteLLM provider/model)
  max_tokens: 4096
description:
  - language: ja
    text: "シンプルな要約エージェント"
instructions:
  - language: ja
    text: "入力テキストを要約します"
prompt:
  - language: ja
    template: |
      以下のテキストを要約してください: {TEXT}
response_fields:
  - summary
```

---

## 使用方法

### CLI コマンド
- [WIP] `kagura create`: AI エージェントのテンプレートを対話的に生成
- `kagura --help`: 利用可能なコマンドを表示

```bash
# エージェントテンプレートの生成例
kagura create
> What is the purpose of this agent? Document summarization
# 目的に応じたエージェント設定が ~/.config/kagura/agents/ に生成されます

---

## 高度な使用方法

### アトミックエージェントと関数の統合
疎結合を活用して、エージェントを関数や外部ツールと効率的に連携させます：

```python
async def process_data(state: StateModel) -> StateModel:
    # カスタムデータ処理ロジック
    return processed_state
```

### マルチエージェントワークフロー
動的ルーティングとエージェント間の状態共有を使用して複雑なワークフローを設計：
```yaml
nodes:
  - name: text_fetcher
  - name: text_summarizer
edges:
  - from: text_fetcher
    to: text_summarizer
```

### Redis 統合
永続メモリを有効化：
```yaml
# ~/.config/kagura/agents/system.yml
redis:
  host: localhost
  port: 6379
```

---

## ロードマップ

- 🌐 **Web API インターフェース**: RESTful API を通じたエージェントの提供
- 🧠 **エージェントメモリ**: エージェント単位での状態やコンテキスト管理機能の強化
- 📚 **エージェント知識ベース**: エージェント単位で参照可能な知識ベースとRAGの統合
- 🐳 **Docker デプロイメント**: Docker コンテナによるセットアップの簡素化

---

## Kagura AI へのコントリビューション

すべてのコントリビューターを歓迎します！経験豊富な開発者でも、オープンソースが初めての方でも、あなたの貢献は重要です。Kagura AI の未来を一緒に形作りましょう。

### コントリビューション方法
- 問題やバグの報告
- 新機能や改善の提案
- コード、ドキュメント、テストの提出
- プルリクエストのレビュー

### コントリビューションの手順
1. [コントリビューションガイド（日本語）](./CONTRIBUTING_JA.md)を読む
2. リポジトリをフォークしてローカルにクローン
3. ブランチを作成し、変更を加えてプルリクエストを提出

---

## ドキュメントとリソース

- [完全なドキュメント](https://www.kagura-ai.com/)
- [クイックスタートチュートリアル](https://www.kagura-ai.com/ja/quickstart/)
- [課題とディスカッション](https://github.com/JFK/kagura-ai/issues)

---

Kagura AI をご覧いただきありがとうございます！調和のとれた、革新的で責任ある AI ソリューションを一緒に構築しましょう。
