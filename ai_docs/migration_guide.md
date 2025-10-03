# Kagura AI 移行・アップグレードガイド

## 概要

このドキュメントは、Kagura AIのバージョンアップグレード、依存ライブラリの更新、コード移行を行う際のガイドラインです。

---

## 一般原則

### 移行の基本方針

1. **段階的な移行**: 一度に全てを変更せず、小さな単位で段階的に実施
2. **後方互換性の維持**: 可能な限り既存のエージェント設定が動作するよう配慮
3. **テストファースト**: 移行前後でテストを実行し、動作を保証
4. **ドキュメント更新**: 変更内容を`ai_docs/`に記録

---

## Python バージョンアップグレード

### Python 3.11 → 3.12への移行

#### 事前準備
```bash
# 現在のPythonバージョン確認
python --version

# 依存関係の互換性チェック
uv pip list --outdated
```

#### 移行手順

1. **`.python-version`の更新**
   ```
   3.12
   ```

2. **`pyproject.toml`の更新**
   ```toml
   [project]
   requires-python = ">=3.12"
   ```

3. **仮想環境の再作成**
   ```bash
   rm -rf .venv
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

4. **テスト実行**
   ```bash
   make test
   ```

5. **型チェック**
   ```bash
   make right
   ```

#### 注意点
- Python 3.12で廃止されたAPIがないか確認
- 型ヒントの新機能 (`type` statement等) は段階的に採用

---

## 依存ライブラリのアップグレード

### LiteLLM バージョンアップ

**現在**: `litellm==1.53.1`

#### アップグレード手順

1. **バージョン確認**
   ```bash
   uv pip show litellm
   ```

2. **リリースノート確認**
   - [LiteLLM Releases](https://github.com/BerriAI/litellm/releases)
   - Breaking Changesをチェック

3. **テスト環境でアップグレード**
   ```bash
   uv pip install litellm==1.60.0
   make test
   ```

4. **互換性確認**
   - LLM呼び出しが正常に動作するか
   - 新しいモデルのサポート状況
   - エラーハンドリングの変更

5. **`pyproject.toml`更新**
   ```toml
   dependencies = [
       "litellm==1.60.0",
       ...
   ]
   ```

### Pydantic v2 → v3 (将来)

**現在**: `pydantic>=2.10.2`

#### 移行戦略

1. **非推奨警告の確認**
   ```bash
   pytest -W default::DeprecationWarning
   ```

2. **段階的な移行**
   - まず`pydantic-compat`で互換性レイヤーを使用
   - 警告を一つずつ解消
   - 全ての警告解消後、完全移行

3. **モデル定義の更新**
   ```python
   # v2
   class AgentConfig(BaseModel):
       model_config = ConfigDict(strict=True)

   # v3 (仮)
   class AgentConfig(BaseModel):
       # 新しい設定方法に従う
       pass
   ```

---

## コード移行パターン

### レガシーコードのモダン化

#### パターン1: `dict` → Pydanticモデル

**移行前**:
```python
def create_agent(config: dict) -> Agent:
    name = config.get("name", "default")
    model = config.get("model", "gpt-4")
    return Agent(name, model)
```

**移行後**:
```python
from pydantic import BaseModel

class AgentConfig(BaseModel):
    name: str = "default"
    model: str = "gpt-4"

def create_agent(config: AgentConfig) -> Agent:
    return Agent(config.name, config.model)
```

#### パターン2: 同期 → 非同期

**移行前**:
```python
def run_agent(agent: Agent, input_data: str) -> str:
    result = agent.process(input_data)
    return result
```

**移行後**:
```python
async def run_agent(agent: Agent, input_data: str) -> str:
    result = await agent.process_async(input_data)
    return result
```

#### パターン3: `print()` → `logging`

**移行前**:
```python
def process():
    print("Processing started")
    result = heavy_task()
    print(f"Result: {result}")
    return result
```

**移行後**:
```python
import logging

logger = logging.getLogger(__name__)

def process():
    logger.info("Processing started")
    result = heavy_task()
    logger.debug(f"Result: {result}")
    return result
```

---

## YAML設定の移行

### エージェント設定のバージョンアップ

#### v0.0.8 → v0.0.9

**変更内容**:
- 新しい設定フィールドの追加
- 非推奨フィールドの削除

**移行前** (`agent.yml`):
```yaml
name: my_agent
role: assistant
model: gpt-3.5-turbo
temperature: 0.7
```

**移行後**:
```yaml
name: my_agent
role: assistant
model: gpt-4  # デフォルトモデルの推奨変更
temperature: 0.7
max_tokens: 4096  # 新フィールド
response_format: json  # 新フィールド
```

#### 自動移行スクリプト

```python
# scripts/migrate_agent_config.py
import yaml
from pathlib import Path

def migrate_agent_config(config_path: Path) -> None:
    """エージェント設定を最新版に移行"""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # 非推奨フィールドの削除
    if "old_field" in config:
        del config["old_field"]

    # デフォルト値の追加
    config.setdefault("max_tokens", 4096)
    config.setdefault("response_format", "json")

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
```

---

## テスト戦略

### 移行時のテストチェックリスト

- [ ] **ユニットテストがグリーン**
  ```bash
  pytest tests/
  ```

- [ ] **統合テストの実行**
  ```bash
  pytest tests/integration/
  ```

- [ ] **型チェックの成功**
  ```bash
  make right
  ```

- [ ] **リントエラーなし**
  ```bash
  make ruff
  ```

- [ ] **カバレッジ維持**
  ```bash
  pytest --cov=kagura --cov-report=term
  ```

- [ ] **既存エージェントの動作確認**
  ```bash
  kagura run agents/test_agent
  ```

---

## ロールバック戦略

### 移行失敗時の対処

1. **Gitブランチでの作業**
   ```bash
   git checkout -b migrate/litellm-upgrade
   # 移行作業
   # 問題があれば
   git checkout main
   ```

2. **依存関係の固定**
   ```bash
   # uv.lockでバージョン固定されているため
   uv sync  # ロックファイルから復元
   ```

3. **バックアップの作成**
   ```bash
   # 重要な設定ファイルのバックアップ
   cp -r agents/ agents.backup/
   ```

---

## 非推奨機能の扱い

### 非推奨機能の段階的廃止

1. **警告の追加** (v0.0.9)
   ```python
   import warnings

   def old_function():
       warnings.warn(
           "old_function is deprecated, use new_function instead",
           DeprecationWarning,
           stacklevel=2
       )
   ```

2. **ドキュメントに記載** (v0.0.9)
   - READMEに非推奨リストを記載
   - 移行パスを明示

3. **削除** (v0.1.0)
   - メジャーバージョンアップ時に削除

---

## 参考資料

- [Semantic Versioning](https://semver.org/)
- [Python Migration Guide](https://docs.python.org/3/whatsnew/)
- [Pydantic Migration Guide](https://docs.pydantic.dev/latest/migration/)

---

## 変更履歴

| バージョン | 日付 | 主な変更 |
|-----------|------|---------|
| v0.0.9 | 2024-12 | 初回リリース |

---

このドキュメントは、バージョンアップグレードごとに更新されます。
