# [SETUP-002] Create minimal project structure for v2.0

## 🎯 目的

Kagura AI 2.0の基本ディレクトリ構造とエントリーポイントを作成。型チェック・テストが通る最小限の実装。

## 📑 出力契約(Claude必読)

- すべてMarkdownで出力
- 各ステップ終了時に作業ログを記録
- エラー/不明点は質問節で停止

## 📂 スコープ境界

**許可パス**:
- `src/kagura/` (全て)
- `tests/` (全て)
- `pyproject.toml` (依存関係のみ)

**禁止パス**:
- `src/kagura_legacy/` (変更不可)
- `ai_docs/` (変更不可)

## 🛡️ 安全弁

- **Draft PR**で作成
- ブランチ名: `feature/SETUP-002-structure`
- 実装は最小限(スタブのみ)

## 📋 Claude Code用タスク定義

### ステップ1: ブランチ作成

1. mainから新ブランチ作成
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/SETUP-002-structure
   ```

### ステップ2: ディレクトリ構造作成

2. 新しいディレクトリとファイルを作成

```bash
# コアモジュール
mkdir -p src/kagura/core
touch src/kagura/core/__init__.py
touch src/kagura/core/decorators.py
touch src/kagura/core/executor.py
touch src/kagura/core/llm.py
touch src/kagura/core/parser.py
touch src/kagura/core/prompt.py

# CLI
mkdir -p src/kagura/cli
touch src/kagura/cli/__init__.py
touch src/kagura/cli/main.py

# Agents
mkdir -p src/kagura/agents
touch src/kagura/agents/__init__.py

# バージョン
touch src/kagura/version.py

# テスト
mkdir -p tests/core
mkdir -p tests/cli
mkdir -p tests/agents
touch tests/__init__.py
touch tests/conftest.py
touch tests/core/__init__.py
touch tests/core/test_decorators.py
touch tests/cli/__init__.py
touch tests/agents/__init__.py
```

### ステップ3: 各ファイルに最小限の実装

3. `src/kagura/version.py`
```python
"""Version information for Kagura AI"""
__version__ = "2.0.0-alpha.1"
```

4. `src/kagura/__init__.py`
```python
"""
Kagura AI 2.0 - Python-First AI Agent Framework

Example:
    from kagura import agent

    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        pass

    result = await hello("World")
"""
from .version import __version__
from .core.decorators import agent, tool, workflow

__all__ = ["agent", "tool", "workflow", "__version__"]
```

5. `src/kagura/core/__init__.py`
```python
"""Core functionality for Kagura AI"""
from .decorators import agent, tool, workflow

__all__ = ["agent", "tool", "workflow"]
```

6. `src/kagura/core/decorators.py`
```python
"""
Decorators to convert functions into AI agents

This is a stub implementation. Full implementation in Issue #CORE-001.
"""
from typing import TypeVar, Callable, ParamSpec, Awaitable

P = ParamSpec('P')
T = TypeVar('T')


def agent(
    fn: Callable[P, Awaitable[T]] | None = None,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    **kwargs
) -> Callable[P, Awaitable[T]]:
    """
    Convert a function into an AI agent.

    Args:
        fn: Function to convert
        model: LLM model to use
        temperature: Temperature for LLM
        **kwargs: Additional LLM parameters

    Returns:
        Decorated async function

    Example:
        @agent
        async def hello(name: str) -> str:
            '''Say hello to {{ name }}'''
            pass

        result = await hello("World")
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Stub: Just return the original function
        # TODO: Implement in Issue #CORE-001
        return func

    return decorator if fn is None else decorator(fn)


def tool(fn: Callable[P, T] | None = None) -> Callable[P, T]:
    """
    Convert a function into a tool (non-LLM function).

    Stub implementation.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # Stub
        return func

    return decorator if fn is None else decorator(fn)


def workflow(fn: Callable[P, Awaitable[T]] | None = None) -> Callable[P, Awaitable[T]]:
    """
    Convert a function into a workflow (multi-agent orchestration).

    Stub implementation.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Stub
        return func

    return decorator if fn is None else decorator(fn)
```

7. `src/kagura/core/llm.py`
```python
"""LLM integration (stub)"""
# TODO: Implement in Issue #CORE-001
```

8. `src/kagura/core/parser.py`
```python
"""Type-based response parsing (stub)"""
# TODO: Implement in Issue #CORE-003
```

9. `src/kagura/core/prompt.py`
```python
"""Prompt template engine (stub)"""
# TODO: Implement in Issue #CORE-002
```

10. `src/kagura/core/executor.py`
```python
"""Code executor (stub)"""
# TODO: Implement in Issue #EXEC-001
```

11. `src/kagura/cli/__init__.py`
```python
"""CLI interface for Kagura AI"""
```

12. `src/kagura/cli/main.py`
```python
"""
Main CLI entry point

Stub implementation.
"""
import click
from ..version import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """Kagura AI - Python-First AI Agent Framework"""
    pass


@cli.command()
def version():
    """Show version"""
    click.echo(f"Kagura AI v{__version__}")


if __name__ == "__main__":
    cli()
```

13. `src/kagura/agents/__init__.py`
```python
"""Built-in agents"""
# TODO: Add code_executor in Issue #EXEC-002
```

14. `tests/conftest.py`
```python
"""Pytest configuration"""
import pytest


@pytest.fixture
def sample_agent():
    """Sample agent for testing"""
    from kagura import agent

    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        return f"Hello, {name}!"

    return hello
```

15. `tests/core/test_decorators.py`
```python
"""Tests for decorators (stub)"""
import pytest
from kagura import agent


@pytest.mark.asyncio
async def test_agent_decorator_exists():
    """Test that @agent decorator exists"""
    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        return f"Hello, {name}!"

    # Stub test: just check it doesn't crash
    result = await hello("World")
    assert result == "Hello, World!"
```

### ステップ4: pyproject.toml更新

16. `pyproject.toml`に最小限の依存関係を追加

```toml
[project]
name = "kagura-ai"
version = "2.0.0-alpha.1"
description = "Python-First AI Agent Framework with Code Execution"
authors = [
    { name = "JFK", email = "fumikazu.kiyota@gmail.com" }
]
readme = "README.md"
requires-python = ">=3.11"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "pydantic>=2.10",
    "click>=8.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.25",
    "pytest-cov>=6.0",
    "ruff>=0.8",
    "pyright>=1.1",
]

[project.scripts]
kagura = "kagura.cli.main:cli"

[build-system]
requires = ["setuptools>=42.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["kagura*"]

[tool.pyright]
include = ["src/kagura", "tests"]
typeCheckingMode = "strict"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

### ステップ5: 動作確認

17. 依存関係をインストール
```bash
uv sync
uv pip install -e ".[dev]"
```

18. 型チェック
```bash
uv run pyright src/kagura
```

19. テスト実行
```bash
uv run pytest tests/
```

20. CLIコマンド確認
```bash
uv run kagura --version
uv run kagura version
```

### ステップ6: コミット・PR作成

21. 変更をコミット
```bash
git add .
git commit -m "feat(core): create minimal project structure (#SETUP-002)

- Add core modules (decorators, llm, parser, prompt, executor)
- Add CLI entry point with Click
- Add test structure with pytest
- Update pyproject.toml with minimal dependencies
- All files are stubs - implementation in future issues"
```

22. Draft PRを作成
```bash
gh pr create --draft --title "[SETUP-002] Create minimal project structure for v2.0" \
  --body "## Summary

Created minimal project structure for Kagura AI 2.0:

### Directory Structure
\`\`\`
src/kagura/
├── __init__.py
├── version.py
├── core/
│   ├── decorators.py (stub)
│   ├── llm.py (stub)
│   ├── parser.py (stub)
│   ├── prompt.py (stub)
│   └── executor.py (stub)
├── cli/
│   └── main.py
└── agents/

tests/
├── conftest.py
├── core/
│   └── test_decorators.py
└── cli/
\`\`\`

### Verification
- ✅ \`uv sync\` successful
- ✅ \`pyright\` passes (strict mode)
- ✅ \`pytest\` passes (1 stub test)
- ✅ \`kagura --version\` works

### Next Steps
- Issue #CORE-001: Implement @agent decorator

## Related
- Depends on: #SETUP-001
- See: \`ai_docs/DEVELOPMENT_ROADMAP.md\`"
```

23. 作業ログ記録
```markdown
## 作業ログ

### 実施内容
- ディレクトリ構造作成: src/kagura/core, cli, agents
- スタブ実装: decorators.py, llm.py, parser.py等
- テスト構造作成: tests/core, cli
- pyproject.toml更新: 最小限の依存関係

### 変更ファイル数
- 新規作成: 20 files

### 検証結果
- ✅ uv sync: 成功
- ✅ pyright: 0 errors (strict mode)
- ✅ pytest: 1 passed
- ✅ kagura --version: 動作

### 発見した問題点
- なし(全てスタブ実装のため)

### 次のステップ
- Issue #CORE-001: @agentデコレータの実装
```

## 🧾 コミット規約

```
feat(core): <変更内容> (#SETUP-002)
```

## ⚠️ 制約・注意事項

- [ ] 全てスタブ実装(実際の機能は後のIssueで実装)
- [ ] 型チェックが通ること(pyright strict mode)
- [ ] テストが通ること(stub testでOK)
- [ ] `kagura --version` が動作すること

## 📚 参考資料

- `ai_docs/DEVELOPMENT_ROADMAP.md` - 開発ロードマップ
- `ai_docs/coding_standards.md` - コーディング規約
- `ai_docs/architecture.md` - アーキテクチャ

## ✅ 完了条件

- [ ] ディレクトリ構造作成完了
- [ ] 全__init__.py作成
- [ ] スタブ実装完了(decorators.py等)
- [ ] pyproject.toml更新
- [ ] `uv sync` 成功
- [ ] `pyright src/kagura` 成功(0 errors)
- [ ] `pytest tests/` 成功(最低1テスト)
- [ ] `kagura --version` 動作
- [ ] Draft PR作成
- [ ] 作業ログ記録
