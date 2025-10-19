# Kagura AI アーキテクチャ

## プロジェクト概要

Kagura AIは、YAML設定ベースのマルチエージェントAIフレームワークです。日本の伝統芸能「神楽」から着想を得て、調和・協調・創造性を重視した設計となっています。

## 技術スタック

### コア技術
- **言語**: Python 3.11+
- **AI統合**: LiteLLM (OpenAI, Anthropic, Ollama, Google等に対応)
- **設定管理**: PyYAML
- **型安全性**: Pydantic v2
- **オーケストレーション**: LangGraph, LangChain
- **メモリ**: Redis (オプション)

### 開発ツール
- **テスト**: pytest, pytest-asyncio, pytest-cov
- **リンター**: ruff, flake8
- **型チェック**: pyright
- **ドキュメント**: MkDocs Material
- **パッケージ管理**: uv

## システムアーキテクチャ

### 全体構成

```
┌─────────────────────────────────────────────┐
│           CLI Interface (Click)             │
│              kagura command                 │
└───────────────┬─────────────────────────────┘
                │
┌───────────────▼─────────────────────────────┐
│          Core Framework Layer               │
│  ┌────────────┐ ┌────────────┐ ┌─────────┐│
│  │   Agent    │ │   Config   │ │  Memory ││
│  │  Manager   │ │  Validator │ │ Manager ││
│  └────────────┘ └────────────┘ └─────────┘│
└─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────┐
│           Agent Types Layer                 │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │ Atomic   │ │  Tool    │ │  Workflow  │ │
│  │  Agent   │ │  Agent   │ │   Agent    │ │
│  └──────────┘ └──────────┘ └────────────┘ │
└─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────┐
│        External Integration Layer           │
│  ┌─────────┐ ┌─────────┐ ┌──────────────┐ │
│  │ LiteLLM │ │  Redis  │ │ Custom Tools │ │
│  └─────────┘ └─────────┘ └──────────────┘ │
└─────────────────────────────────────────────┘
```

### ディレクトリ構造

```
src/kagura/
├── __init__.py
├── cli/                    # CLIインターフェース
│   ├── __main__.py        # エントリーポイント
│   ├── commands/          # コマンド実装
│   └── ui/                # UI関連
├── core/                  # コアフレームワーク
│   ├── agent.py          # エージェント基底クラス
│   ├── config.py         # 設定管理
│   ├── memory.py         # メモリ管理
│   ├── models.py         # Pydanticモデル
│   ├── prompts.py        # プロンプト管理
│   └── utils/            # ユーティリティ
└── agents/               # エージェント実装
    ├── atomic_agent_generator/
    ├── tool_agent_generator/
    └── workflow_agent_generator/
```

## エージェントタイプ

### Atomic Agent
- **目的**: LLMを使用したタスク特化型エージェント
- **特徴**:
  - 独立した状態管理
  - pre/post処理フック対応
  - 型安全な出力 (Pydantic)
  - 構造化データ生成

### Tool Agent
- **目的**: 非LLMデータ処理
- **特徴**:
  - 高速実行
  - API統合
  - データ変換処理
  - 外部サービス連携

### Workflow Agent
- **目的**: マルチエージェントオーケストレーション
- **特徴**:
  - 条件分岐ルーティング
  - エラーリカバリ
  - 進捗監視
  - 状態共有管理

## 設計原則

### 1. YAML-First Configuration
- エージェント定義は全てYAMLで記述
- コードとロジックの分離
- 設定の再利用性向上

### 2. Type Safety
- Pydanticによる厳格な型検証
- 実行時エラーの早期発見
- IDE補完の効果的活用

### 3. Modularity
- 疎結合な設計
- マイクロサービス的アプローチ
- エージェントの独立性保証

### 4. Multilingual Support
- 多言語対応をコアに組み込み
- ドキュメントの英語・日本語併記

## 重要な制約

### セキュリティ
- APIキーは環境変数で管理
- センシティブデータのログ出力禁止
- Redis接続は暗号化推奨

### パフォーマンス
- LLM呼び出しは非同期処理を考慮
- 大規模ワークフローは段階的実行
- メモリ使用量の監視

### 互換性
- Python 3.11+必須
- 後方互換性の維持
- 非推奨機能は段階的廃止

## データフロー

### エージェント実行フロー

```
1. YAML設定読み込み
   ↓
2. Pydanticモデル検証
   ↓
3. エージェントインスタンス生成
   ↓
4. 状態初期化
   ↓
5. pre-processing hook (オプション)
   ↓
6. LLM/Tool実行
   ↓
7. post-processing hook (オプション)
   ↓
8. 結果検証・返却
```

## 参考ドキュメント

- [公式ドキュメント](https://www.kagura-ai.com/)
- [Agent Overview](../docs/en/agents/overview.md)
- [System Configuration](../docs/en/system-configuration.md)
