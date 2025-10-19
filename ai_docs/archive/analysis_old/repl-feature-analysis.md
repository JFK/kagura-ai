# REPL機能分析と改善提案

**Date**: 2025-10-03
**Scope**: CLI/REPL機能の現状確認と改善提案

---

## 📊 現在実装されている機能

### CLI Commands
```bash
kagura version    # バージョン表示
kagura repl       # REPL起動
```

### REPL Commands
- `/help` - ヘルプ表示
- `/agents` - 定義済みエージェント一覧
- `/model [name]` - モデル設定
- `/temp [value]` - temperature設定
- `/exit` - 終了
- `/clear` - 画面クリア

### Core Features
1. **@agentデコレータ** - エージェント定義
2. **LiteLLM統合** - 環境変数からAPIキー自動読み取り
3. **REPL** - 基本的な対話環境
4. **Code Executor** - 安全なコード実行

---

## ❌ 実装されていない機能

### 1. エージェントの永続化
**現状**: セッション終了でエージェント消失

**問題**:
- REPLを閉じると定義したエージェントが全て消える
- 毎回エージェントを再定義する必要がある

**ユースケース**:
```python
# 現在（不便）
$ kagura repl
>>> @agent
... async def my_agent(...): ...

# REPLを終了すると消える
>>> /exit

# 次回REPLを起動すると、また定義し直す必要がある
$ kagura repl
>>> @agent  # また書き直し
... async def my_agent(...): ...
```

---

### 2. .envファイルのサポート
**現状**: LiteLLMが環境変数を読み取るが、.envファイルの自動読み込みなし

**問題**:
- 毎回 `export OPENAI_API_KEY=...` が必要
- プロジェクトごとの設定が難しい

**ユースケース**:
```bash
# 現在（不便）
$ export OPENAI_API_KEY=sk-...
$ export ANTHROPIC_API_KEY=sk-ant-...
$ kagura repl

# 期待する動作
$ cat .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_TEMPERATURE=0.7

$ kagura repl  # .envを自動読み込み
```

---

### 3. 設定ファイル
**現状**: 設定ファイルのサポートなし

**問題**:
- デフォルトモデル、temperatureなどを永続化できない
- プロジェクトごとの設定不可

**ユースケース**:
```yaml
# .kagura.yaml
model: gpt-4o-mini
temperature: 0.7
max_tokens: 2000

agents_dir: ./my_agents  # エージェント保存先
history_file: ~/.kagura_history
```

---

### 4. REPL履歴保存
**現状**: 上下キーで履歴を遡れない

**問題**:
- 前のコマンドを再実行できない
- 長いエージェント定義を再入力する必要がある

**期待する動作**:
```python
>>> await hello("World")
'Hello, World!'

# 上キーを押すと前のコマンドが表示される
>>> await hello("World")  # ← 自動で表示

# ~/.kagura_history に保存される
```

---

### 5. 簡易エージェント定義コマンド
**現状**: 毎回`@agent`デコレータで定義

**問題**:
- マルチライン入力が必要
- `from kagura import agent` を毎回書く必要がある（実際は不要だが、ユーザーが混乱）

**改善案**:
```python
# 現在（冗長）
>>> from kagura import agent
>>> @agent
... async def hello(name: str) -> str:
...     '''Say hello to {{ name }}'''
...     pass

# 改善案
>>> /agent hello(name: str) -> str
... Say hello to {{ name }}
Agent 'hello' defined

>>> await hello("World")
'Hello, World!'
```

---

## 🎯 改善提案

### Priority 1: 必須（Beta版リリース前）

#### 1. .envファイルサポート
**実装内容**:
```python
# src/kagura/cli/main.py
from dotenv import load_dotenv

@cli.command()
def repl():
    load_dotenv()  # .envを自動読み込み
    # ...
```

**依存関係**:
```toml
dependencies = [
    "python-dotenv>=1.0",
]
```

**所要時間**: 30分

---

#### 2. REPL履歴保存（readline）
**実装内容**:
```python
# src/kagura/cli/repl.py
import readline
import os

class KaguraREPL:
    def __init__(self):
        self.history_file = os.path.expanduser("~/.kagura_history")
        self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)

    def _save_history(self):
        readline.write_history_file(self.history_file)
```

**所要時間**: 1時間

---

### Priority 2: 推奨（Beta版後）

#### 3. エージェントの永続化
**実装内容**:
```python
# ~/.kagura/agents/my_agent.py として保存
/save my_agent  # エージェントを保存
/load my_agent  # エージェント読み込み
/agents --saved # 保存済みエージェント一覧
```

**設計**:
```
~/.kagura/
  agents/
    my_agent.py
    data_extractor.py
  history
  config.yaml
```

**所要時間**: 3時間

---

#### 4. 設定ファイルサポート
**実装内容**:
```yaml
# .kagura.yaml
model: gpt-4o-mini
temperature: 0.7
agents_dir: ~/.kagura/agents
history_file: ~/.kagura_history
auto_load_agents: true
```

**所要時間**: 2時間

---

#### 5. /agentコマンド（簡易定義）
**実装内容**:
```python
def execute_command(self, command: str):
    # ...
    elif cmd == "/agent":
        self._create_agent_from_command(arg)
```

**所要時間**: 2時間

---

## 📋 実装ロードマップ

### Phase 1: Quick Wins（Beta版前）
**所要時間**: 1.5時間

1. `.env`ファイルサポート（30分）
2. REPL履歴保存（1時間）

**期待効果**:
- ✅ APIキー設定が簡単に
- ✅ コマンド履歴が使える
- ✅ 基本的なREPL体験向上

---

### Phase 2: Persistence（Beta版後）
**所要時間**: 7時間

3. エージェント永続化（3時間）
4. 設定ファイルサポート（2時間）
5. `/agent`コマンド（2時間）

**期待効果**:
- ✅ エージェントを再利用可能
- ✅ プロジェクトごとの設定
- ✅ エージェント定義が簡単に

---

## 🚀 推奨アクション

### 今すぐ実施（Beta版前）

**Issue作成**: `[CLI-003] Add .env support and readline history to REPL`

**内容**:
1. python-dotenvで.env自動読み込み
2. readlineでコマンド履歴保存
3. テスト追加

**期待結果**: REPL使いやすさ大幅向上

---

### Beta版後に実施

**Issue作成**: `[CLI-004] Add agent persistence and config file support`

**内容**:
1. エージェント保存・読み込み機能
2. .kagura.yaml設定ファイル
3. `/save`, `/load`, `/agent`コマンド

---

## 📊 優先度マトリクス

| 機能 | 実装難易度 | ユーザー価値 | 優先度 |
|------|-----------|------------|--------|
| .env サポート | 低 | 高 | ⭐⭐⭐ |
| readline履歴 | 低 | 高 | ⭐⭐⭐ |
| エージェント永続化 | 中 | 中 | ⭐⭐ |
| 設定ファイル | 中 | 中 | ⭐⭐ |
| /agentコマンド | 中 | 低 | ⭐ |

---

## 📝 結論

**現状**: 基本機能は実装済み、REPLの使いやすさに課題

**推奨**:
1. Phase 1（.env + readline）を**Beta版前**に実装
2. Phase 2（永続化 + 設定）を**Beta版後**に実装

**次のアクション**: Issue #56を作成して、Phase 1を実装

---

**参考実装例**:

**IPython**: readline履歴、magic commands
**Poetry**: pyproject.toml設定ファイル
**AWS CLI**: ~/.aws/config設定ファイル
