# Kagura AI コーディング規約

## 概要

本ドキュメントは、Kagura AIプロジェクトにおけるコーディング規約を定義します。コードの一貫性、可読性、保守性を高めるため、全ての貢献者がこの規約に従ってください。

## Python スタイルガイド

### 基本原則
- [PEP 8](https://peps.python.org/pep-0008/) に準拠
- [PEP 484](https://peps.python.org/pep-0484/) 型ヒントを積極的に使用

### 命名規則

#### モジュール・パッケージ
```python
# ✅ 良い例
import kagura.core.agent
from kagura.utils import validator

# ❌ 悪い例
import KaguraAgent
from utils import Validator
```

#### クラス名
```python
# ✅ 良い例: PascalCase
class AtomicAgent:
    pass

class LLMConfig:
    pass

# ❌ 悪い例
class atomic_agent:  # スネークケースは不可
    pass
```

#### 関数・変数名
```python
# ✅ 良い例: snake_case
def create_agent(config_path: str) -> Agent:
    agent_instance = Agent()
    return agent_instance

# ❌ 悪い例
def CreateAgent(ConfigPath: str):  # PascalCaseは不可
    AgentInstance = Agent()
    return AgentInstance
```

#### 定数
```python
# ✅ 良い例: UPPER_SNAKE_CASE
DEFAULT_MODEL = "gpt-4"
MAX_RETRIES = 3
API_TIMEOUT_SECONDS = 30

# ❌ 悪い例
default_model = "gpt-4"  # 小文字は不可
maxRetries = 3           # camelCaseは不可
```

#### プライベート属性・メソッド
```python
# ✅ 良い例
class Agent:
    def __init__(self):
        self._internal_state = {}  # プライベート属性

    def _validate_config(self):    # プライベートメソッド
        pass

# ❌ 悪い例
class Agent:
    def __init__(self):
        self.internalState = {}  # publicだが内部用のような命名
```

### 型ヒント

#### 必須の型ヒント
```python
# ✅ 良い例
def process_data(
    input_data: dict[str, Any],
    max_items: int = 10
) -> list[dict[str, str]]:
    """データを処理して結果を返す"""
    return []

# ❌ 悪い例 - 型ヒントなし
def process_data(input_data, max_items=10):
    return []
```

#### 複雑な型
```python
from typing import Optional, Union, Callable
from collections.abc import Sequence

# ✅ 良い例
def create_workflow(
    agents: Sequence[Agent],
    error_handler: Optional[Callable[[Exception], None]] = None
) -> Workflow:
    pass

# ❌ 悪い例 - Anyの乱用
def create_workflow(agents: Any, error_handler: Any) -> Any:
    pass
```

#### Pydanticモデル
```python
from pydantic import BaseModel, Field

# ✅ 良い例
class AgentConfig(BaseModel):
    """エージェント設定"""
    name: str = Field(..., description="エージェント名")
    model: str = Field(default="gpt-4", description="使用するLLMモデル")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
```

### ドキュメント文字列

#### モジュール
```python
"""
Kagura AI Core Agent Module

このモジュールはエージェントの基底クラスを提供します。
"""
```

#### クラス・関数
```python
def create_agent(config_path: str, enable_memory: bool = False) -> Agent:
    """
    YAML設定からエージェントを作成する

    Args:
        config_path: エージェント設定ファイルのパス
        enable_memory: メモリ機能を有効化するか

    Returns:
        作成されたエージェントインスタンス

    Raises:
        ValueError: 設定ファイルが不正な場合
        FileNotFoundError: 設定ファイルが存在しない場合

    Example:
        >>> agent = create_agent("agents/my_agent/agent.yml")
        >>> result = agent.run({"input": "test"})
    """
    pass
```

## コードスタイル

### インポート順序
```python
# 1. 標準ライブラリ
import os
import sys
from typing import Any, Optional

# 2. サードパーティライブラリ
import click
from pydantic import BaseModel
from rich.console import Console

# 3. ローカルモジュール
from kagura.core.agent import Agent
from kagura.core.config import Config
```

### 行の長さ
- 最大88文字 (ruffのデフォルト)
- 長い行は適切に分割

```python
# ✅ 良い例
result = some_function(
    param1=value1,
    param2=value2,
    param3=value3,
)

# ❌ 悪い例
result = some_function(param1=value1, param2=value2, param3=value3, param4=value4, param5=value5)
```

### 文字列
- 通常の文字列: ダブルクォート `"`
- docstring: トリプルダブルクォート `"""`

```python
# ✅ 良い例
name = "Kagura AI"
description = "AI Agent Framework"

def function():
    """関数の説明"""
    pass

# ❌ 悪い例
name = 'Kagura AI'  # シングルクォートは避ける
```

## エラーハンドリング

### 例外の使用
```python
# ✅ 良い例 - 具体的な例外
class ConfigurationError(Exception):
    """設定に関するエラー"""
    pass

def load_config(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"設定ファイルが見つかりません: {path}")

    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"YAML解析エラー: {e}") from e

# ❌ 悪い例 - 汎用的すぎる
def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception:  # 全ての例外を握りつぶす
        return {}
```

### ロギング
```python
import logging

logger = logging.getLogger(__name__)

# ✅ 良い例
def process_agent(agent: Agent) -> dict[str, Any]:
    logger.info(f"エージェント処理開始: {agent.name}")
    try:
        result = agent.run()
        logger.debug(f"処理結果: {result}")
        return result
    except Exception as e:
        logger.error(f"エージェント実行エラー: {e}", exc_info=True)
        raise

# ❌ 悪い例 - print文の使用
def process_agent(agent):
    print(f"Processing {agent.name}")  # 本番コードでprint使用禁止
    result = agent.run()
    return result
```

## テスト

### テストファイル命名
```
tests/
├── core/
│   ├── test_agent.py
│   ├── test_config.py
│   └── test_memory.py
└── cli/
    └── test_commands.py
```

### テストケース
```python
import pytest
from kagura.core.agent import Agent

class TestAgent:
    """Agentクラスのテスト"""

    def test_create_agent_with_valid_config(self):
        """正常な設定でエージェントが作成できる"""
        agent = Agent(config_path="test_config.yml")
        assert agent is not None
        assert agent.name == "test_agent"

    def test_create_agent_with_invalid_config(self):
        """不正な設定では例外が発生する"""
        with pytest.raises(ValueError):
            Agent(config_path="invalid.yml")

    @pytest.mark.asyncio
    async def test_async_agent_execution(self):
        """非同期実行が正常に動作する"""
        agent = Agent(config_path="async_config.yml")
        result = await agent.run_async({"input": "test"})
        assert result is not None
```

## 禁止事項

### ❌ やってはいけないこと

1. **`print()`の使用**
   ```python
   # ❌ 悪い例
   print("Debug info")

   # ✅ 良い例
   logger.debug("Debug info")
   ```

2. **`Any`型の乱用**
   ```python
   # ❌ 悪い例
   def process(data: Any) -> Any:
       pass

   # ✅ 良い例
   def process(data: dict[str, str]) -> list[str]:
       pass
   ```

3. **グローバル変数**
   ```python
   # ❌ 悪い例
   CURRENT_AGENT = None  # グローバル状態

   def set_agent(agent):
       global CURRENT_AGENT
       CURRENT_AGENT = agent

   # ✅ 良い例
   class AgentManager:
       def __init__(self):
           self.current_agent: Optional[Agent] = None
   ```

4. **ハードコードされた設定**
   ```python
   # ❌ 悪い例
   API_KEY = "sk-1234567890"

   # ✅ 良い例
   import os
   API_KEY = os.getenv("OPENAI_API_KEY")
   ```

5. **例外の握りつぶし**
   ```python
   # ❌ 悪い例
   try:
       risky_operation()
   except:
       pass

   # ✅ 良い例
   try:
       risky_operation()
   except SpecificError as e:
       logger.error(f"操作失敗: {e}")
       raise
   ```

## ツールとチェック

### 実行コマンド

```bash
# コードフォーマット
make ruff

# 型チェック
make right

# テスト実行
make test

# 全チェック
make check
```

### pre-commit hooks

プロジェクトは`.pre-commit-config.yaml`で自動チェックが設定されています:

```bash
# フックのインストール
pre-commit install

# 手動実行
pre-commit run --all-files
```

## 参考資料

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [ruff Documentation](https://docs.astral.sh/ruff/)

## 更新履歴

このドキュメントは定期的に見直され、プロジェクトの成長に合わせて更新されます。
