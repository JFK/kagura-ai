# Kagura AI 2.0

![Kagura AI Logo](https://www.kagura-ai.com/assets/kagura-logo.svg)

[![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)](https://pypi.org/project/kagura-ai/)
[![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)](https://codecov.io/gh/JFK/kagura-ai)
[![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)](https://github.com/JFK/kagura-ai/actions)

**Python ファーストの AI エージェントフレームワーク（コード実行機能付き）**

Kagura AI 2.0 は、シンプルさと開発者体験に焦点を当てた完全な再設計版です。一つのデコレータで、あらゆる Python 関数を AI エージェントに変換できます。

---

## ✨ 特徴

- **@agent デコレータ**: 1行で AI エージェントを作成
- **Jinja2 テンプレート**: docstring 内での強力なプロンプトテンプレート
- **型ベース解析**: 型ヒントを使用した自動レスポンス解析
- **Pydantic モデル**: 構造化された出力のファーストクラスサポート
- **コード実行**: 安全な Python コード生成・実行
- **インタラクティブ REPL**: `kagura repl` で高速プロトタイピング
- **マルチ LLM サポート**: [LiteLLM](https://github.com/BerriAI/litellm) 経由で OpenAI、Anthropic、Google などをサポート

## 🚀 クイックスタート

### インストール

```bash
pip install kagura-ai
```

### 基本的な例

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    '''{{ name }}に挨拶する'''
    pass

# エージェントを実行
result = await hello("世界")
print(result)  # "こんにちは、世界！"
```

### Pydantic を使った構造化出力

```python
from kagura import agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    '''次のテキストから人物情報を抽出: {{ text }}'''
    pass

result = await extract_person("アリスは30歳で、ソフトウェアエンジニアとして働いています")
print(f"{result.name}, {result.age}, {result.occupation}")
# 出力: アリス, 30, ソフトウェアエンジニア
```

### コード実行

```python
from kagura.agents import execute_code

result = await execute_code("10の階乗を計算")
if result["success"]:
    print(result["result"])  # 3628800
```

### インタラクティブ REPL

```bash
kagura repl
```

利用可能なコマンド:
- `/help` - 利用可能なコマンドを表示
- `/agents` - 定義済みエージェントを一覧表示
- `/exit` - REPL を終了
- `/clear` - 画面をクリア

## 📚 ドキュメント

- [完全なドキュメント](https://www.kagura-ai.com/)
- [API リファレンス](https://www.kagura-ai.com/en/api/)
- [サンプルコード](./examples/)
- [コントリビューションガイド](./CONTRIBUTING_JA.md)

## 🎯 2.0 の新機能

Kagura AI 2.0 は 1.x からの**完全な再設計**です：

### 以前 (1.x)
```yaml
# agent.yml
type: atomic
llm:
  model: gpt-4
prompt:
  - language: ja
    template: "あなたは親切なアシスタントです"
```

### 現在 (2.0)
```python
@agent
async def assistant(query: str) -> str:
    '''あなたは親切なアシスタントです。質問に答えて: {{ query }}'''
    pass
```

**主な変更点:**
- **Python ファースト**: YAML 設定が不要
- **シンプルな API**: 複雑な設定の代わりに1つのデコレータ
- **型安全性**: 完全な型ヒントと Pydantic サポート
- **コード実行**: 安全なコード生成・実行機能を内蔵
- **優れた DX**: 高速開発のためのインタラクティブ REPL

**1.x からの移行**: [移行ガイド](./ai_docs/migration_guide.md)を参照

## 🔧 コア概念

### 1. Agent デコレータ
任意の非同期関数を AI エージェントに変換:

```python
@agent
async def my_agent(input: str) -> str:
    '''{{ input }}を処理する'''
    pass
```

### 2. テンプレートエンジン
docstring 内で Jinja2 テンプレートを使用して動的プロンプトを作成:

```python
@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''{{ lang }}に翻訳: {{ text }}'''
    pass
```

### 3. 型ベース解析
戻り値の型ヒントに基づく自動レスポンス解析:

```python
@agent
async def extract_data(text: str) -> list[str]:
    '''次のテキストからキーワードを抽出: {{ text }}'''
    pass
```

### 4. コードエグゼキュータ
セキュリティ制約付きの安全な Python コード実行:

```python
from kagura.core.executor import CodeExecutor

executor = CodeExecutor()
result = await executor.execute("""
import math
result = math.factorial(10)
""")
print(result.result)  # 3628800
```

## 🎨 サンプル

### 基本的なチャットエージェント
```python
from kagura import agent

@agent
async def chat(message: str) -> str:
    '''あなたは親切な AI アシスタントです。次のメッセージに返答: {{ message }}'''
    pass

response = await chat("人生の意味は何ですか？")
print(response)
```

### データ抽出
```python
from kagura import agent
from pydantic import BaseModel
from typing import List

class Task(BaseModel):
    title: str
    priority: int

class TaskList(BaseModel):
    tasks: List[Task]

@agent
async def extract_tasks(text: str) -> TaskList:
    '''次のテキストからタスクを抽出: {{ text }}'''
    pass

result = await extract_tasks("1. バグ修正（高優先度）、2. ドキュメント作成（低優先度）")
for task in result.tasks:
    print(f"{task.title} - 優先度: {task.priority}")
```

### 複数ステップのワークフロー
```python
from kagura import agent

@agent
async def plan(goal: str) -> list[str]:
    '''次の目標をステップに分解: {{ goal }}'''
    pass

@agent
async def execute_step(step: str) -> str:
    '''次のステップを実行: {{ step }}'''
    pass

# 計画を生成
steps = await plan("Web アプリを構築")

# 各ステップを実行
for step in steps:
    result = await execute_step(step)
    print(f"✓ {step}: {result}")
```

## 🤝 コントリビューション

コントリビューションを歓迎します！ガイドラインについては [CONTRIBUTING_JA.md](./CONTRIBUTING_JA.md) を参照してください。

### 開発環境のセットアップ

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --dev
```

テストの実行:
```bash
pytest
```

型チェック:
```bash
pyright
```

## 📄 ライセンス

Apache License 2.0 - 詳細は [LICENSE](./LICENSE) を参照

## 🙏 謝辞

Kagura AI は日本の伝統芸能「神楽（かぐら）」にちなんで名付けられ、調和、つながり、創造性の原理を体現しています。

---

Kagura AI コミュニティが ❤️ を込めて開発
