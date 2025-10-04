# RFC-012: Custom Commands & Hooks System - 拡張可能なコマンド・フックシステム

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: TBD
- **優先度**: High

## 概要

Kagura AIに**Markdown形式のカスタムコマンド定義**と**Hooks System**を追加します。Claude Codeのコマンドシステムを参考に、宣言的なコマンド定義とツール実行前後の介入機能を実現します。

### 目標
- Markdown形式でカスタムコマンドを定義
- PreToolUse/PostToolUse Hooksでツール実行を制御
- `!`コマンド実行結果の埋め込み（`!`git status``）
- allowed-toolsによるセキュリティ制御
- 非プログラマーでも使える宣言的API

### 非目標
- Kaguraの既存`@agent` APIの置き換え（共存する）
- 完全なDSL言語の実装

## モチベーション

### 現在の課題
1. エージェント作成にPythonコードが必須
2. ツール実行前のバリデーション機構がない
3. よく使うタスクの再利用が困難
4. 非プログラマーが参入しにくい

### 解決するユースケース
- **簡単なタスク自動化**: Markdownで定義、即実行
- **ツールバリデーション**: 危険なコマンドをブロック
- **コマンド共有**: チームで共通コマンドを共有
- **セキュリティ**: allowed-toolsで実行可能ツールを制限

### なぜ今実装すべきか
- Claude Codeで実証済みのパターン
- Kaguraのプログラマブル性と組み合わせると強力
- コミュニティ拡大（非プログラマーも参加可能）

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         User Interface                      │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  CLI: kagura run <command>          │   │
│  │  REPL: > /commit-pr                 │   │
│  └──────────────┬──────────────────────┘   │
└─────────────────┼──────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         Command Loader                      │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Load from ~/.kagura/commands/      │   │
│  │  Parse Markdown frontmatter         │   │
│  │  Extract metadata & content         │   │
│  └──────────────┬──────────────────────┘   │
└─────────────────┼──────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         Command Executor                    │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Execute inline commands (!`...`)   │   │
│  │  Build prompt from template         │   │
│  │  Invoke Kagura agent                │   │
│  └──────────────┬──────────────────────┘   │
└─────────────────┼──────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         Hooks System                        │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  PreToolUse Hooks                   │   │
│  │  - Validate tool input              │   │
│  │  - Block/suggest/allow              │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  PostToolUse Hooks                  │   │
│  │  - Log tool output                  │   │
│  │  - Transform result                 │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. Markdown Command Definition

`~/.kagura/commands/commit-pr.md`:

```markdown
---
name: commit-pr
description: Create commit, push, and open PR
allowed_tools: [git, gh]
model: gpt-4o-mini
---

## Context

- Git status: !`git status`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -5`

## Your Task

Based on the above changes:
1. Create a new branch if on main/master
2. Create a single commit with an appropriate message
3. Push the branch to origin
4. Create a pull request using `gh pr create`

You MUST do all steps in a single response with parallel tool calls.
```

**使用:**
```bash
# CLIから実行
kagura run commit-pr

# REPLから実行
kagura repl
> /commit-pr
```

#### 2. Inline Command Execution (`!` syntax)

コマンド実行結果を埋め込み：

```markdown
## Context
- Current directory: !`pwd`
- File count: !`find . -type f | wc -l`
- Git status: !`git status --short`
```

実行時に自動展開：

```markdown
## Context
- Current directory: /home/user/project
- File count: 42
- Git status:
  M src/main.py
  ?? new_file.py
```

#### 3. Hooks System

**PreToolUse Hook:**

`~/.kagura/hooks/bash_validator.py`:

```python
#!/usr/bin/env python3
"""Validate bash commands before execution"""

import json
import sys
import re

def validate_bash_command(command: str) -> tuple[int, str]:
    """
    Validate bash command.

    Returns:
        (exit_code, message)
        - 0: OK, proceed
        - 1: Show error to user (not Claude)
        - 2: Block tool + show error to Claude
    """
    # 危険なコマンドをブロック
    dangerous_patterns = [
        r"rm\s+-rf\s+/",
        r"dd\s+if=.*of=/dev/",
        r"mkfs\.",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            return (2, f"❌ Dangerous command blocked: {command}")

    # 非推奨コマンドを提案
    if re.search(r"^grep\b(?!.*\|)", command):
        return (1, "💡 Consider using 'rg' instead of 'grep' for better performance")

    if re.search(r"^find\s+\S+\s+-name\b", command):
        return (1, "💡 Consider using 'rg --files -g pattern' instead of 'find -name'")

    return (0, "")

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    exit_code, message = validate_bash_command(command)

    if message:
        print(message, file=sys.stderr)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
```

**設定:**

`~/.kagura/config.toml`:

```toml
[hooks]
enabled = true

[[hooks.pre_tool_use]]
matcher = "Bash"
type = "command"
command = "python3 ~/.kagura/hooks/bash_validator.py"

[[hooks.pre_tool_use]]
matcher = "Edit"
type = "command"
command = "python3 ~/.kagura/hooks/edit_validator.py"

[[hooks.post_tool_use]]
matcher = "*"
type = "command"
command = "python3 ~/.kagura/hooks/logger.py"
```

#### 4. Python API for Hooks

プログラマティックなフック定義：

```python
from kagura import hook, HookResult

@hook.pre_tool_use("bash")
def validate_bash(tool_input: dict) -> HookResult:
    """Validate bash commands"""
    command = tool_input.get("command", "")

    # 危険なコマンドをブロック
    if "rm -rf /" in command:
        return HookResult.block("Dangerous command detected!")

    # 提案
    if "grep" in command:
        return HookResult.suggest(
            "Consider using 'rg' for faster search",
            suggestion=command.replace("grep", "rg")
        )

    return HookResult.ok()

@hook.post_tool_use("*")
def log_tool_usage(tool_name: str, tool_input: dict, tool_output: str):
    """Log all tool usage"""
    import logging
    logging.info(f"Tool used: {tool_name}, Input: {tool_input}")
    return HookResult.ok()
```

### 統合例

#### 例1: Git Workflow Command

`~/.kagura/commands/git-workflow.md`:

```markdown
---
name: git-workflow
description: Complete git workflow (commit, push, PR)
allowed_tools: [git, gh]
---

## Context

**Repository Information:**
- Status: !`git status`
- Branch: !`git branch --show-current`
- Uncommitted changes: !`git diff --stat`

## Task

Execute the following git workflow:

1. **Branch Management**
   - If on main/master, create feature branch
   - Branch name should be descriptive

2. **Commit**
   - Stage all changes
   - Create meaningful commit message
   - Follow conventional commits format

3. **Push & PR**
   - Push to origin with -u flag
   - Create PR with gh pr create
   - Include summary and test plan

Execute all steps in parallel when possible.
```

**実行:**
```bash
$ kagura run git-workflow

Executing git-workflow...
✓ Created branch: feature/add-hooks-system
✓ Committed: feat(hooks): Add PreToolUse validation system
✓ Pushed to origin
✓ Created PR: https://github.com/user/repo/pull/42

Done!
```

#### 例2: Code Review Command

`~/.kagura/commands/code-review.md`:

```markdown
---
name: code-review
description: Comprehensive code review
allowed_tools: [git, gh, read]
model: gpt-4o
---

## Context

**Changed Files:**
!`git diff --name-only HEAD~1`

**Diff:**
!`git diff HEAD~1`

## Task

Perform comprehensive code review:

1. **Code Quality**
   - Check for code smells
   - Verify naming conventions
   - Check complexity

2. **Best Practices**
   - Error handling
   - Type hints
   - Documentation

3. **Security**
   - SQL injection risks
   - XSS vulnerabilities
   - Hardcoded secrets

4. **Performance**
   - Inefficient algorithms
   - N+1 queries
   - Resource leaks

Provide detailed feedback with line numbers.
```

#### 例3: Data Analysis Command

`~/.kagura/commands/analyze-data.md`:

```markdown
---
name: analyze-data
description: Analyze CSV data
allowed_tools: [bash, read]
parameters:
  file: string
---

## Context

**File Information:**
- Size: !`wc -l {{ file }}`
- First 10 rows: !`head -10 {{ file }}`
- Columns: !`head -1 {{ file }}`

## Task

Analyze the CSV data:
1. Data summary (rows, columns, types)
2. Missing values
3. Statistical summary
4. Correlations
5. Recommendations
```

**使用:**
```bash
kagura run analyze-data --file data.csv
```

## 実装計画

### Phase 1: Command System (v2.3.0)
- [ ] Markdown command loader
- [ ] Frontmatter parser
- [ ] Inline command execution (`!`...``)
- [ ] `kagura run <command>` CLI
- [ ] REPL `/command` integration

### Phase 2: Hooks System (v2.4.0)
- [ ] Hook infrastructure
- [ ] PreToolUse hooks
- [ ] PostToolUse hooks
- [ ] Python API for hooks
- [ ] Hook configuration (config.toml)

### Phase 3: Advanced Features (v2.5.0)
- [ ] Command parameters support
- [ ] Command composition (call other commands)
- [ ] Command templates
- [ ] Command marketplace integration (RFC-008)

### Phase 4: Ecosystem (v2.6.0)
- [ ] Official command library
- [ ] Hook library
- [ ] Documentation generator
- [ ] Command testing framework

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
commands = [
    "python-frontmatter>=1.0.0",  # Markdown frontmatter
    "jinja2>=3.1.2",               # Template rendering
    "pyyaml>=6.0",                 # YAML parsing
]
```

### Command Loader Implementation

```python
# src/kagura/commands/loader.py
import frontmatter
from pathlib import Path
from typing import Dict, Any
import subprocess
import re

class CommandLoader:
    """Load and execute custom commands from Markdown files"""

    def __init__(self, commands_dir: Path = None):
        self.commands_dir = commands_dir or Path.home() / ".kagura" / "commands"
        self.commands: Dict[str, Command] = {}

    def load_all(self):
        """Load all commands from commands directory"""
        if not self.commands_dir.exists():
            return

        for md_file in self.commands_dir.glob("*.md"):
            command = self.load_command(md_file)
            self.commands[command.name] = command

    def load_command(self, path: Path) -> "Command":
        """Load a single command from Markdown file"""
        content = frontmatter.load(path)

        return Command(
            name=content.metadata.get("name", path.stem),
            description=content.metadata.get("description", ""),
            allowed_tools=content.metadata.get("allowed_tools", []),
            model=content.metadata.get("model", "gpt-4o-mini"),
            parameters=content.metadata.get("parameters", {}),
            template=content.content
        )

    def execute_inline_commands(self, template: str) -> str:
        """Execute !`command` and replace with output"""
        pattern = r'!`([^`]+)`'

        def execute(match):
            command = match.group(1)
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.stdout.strip()
            except Exception as e:
                return f"[Error executing: {command}]"

        return re.sub(pattern, execute, template)

class Command:
    """Represents a custom command"""

    def __init__(
        self,
        name: str,
        description: str,
        template: str,
        allowed_tools: list[str] = None,
        model: str = "gpt-4o-mini",
        parameters: dict = None
    ):
        self.name = name
        self.description = description
        self.template = template
        self.allowed_tools = allowed_tools or []
        self.model = model
        self.parameters = parameters or {}

    async def execute(self, **kwargs) -> str:
        """Execute the command"""
        from kagura import agent

        # パラメータ置換
        rendered = self.template
        for key, value in kwargs.items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))

        # インラインコマンド実行
        loader = CommandLoader()
        rendered = loader.execute_inline_commands(rendered)

        # エージェント実行
        @agent(model=self.model)
        async def command_agent(prompt: str) -> str:
            """{{ prompt }}"""
            pass

        return await command_agent(rendered)
```

### Hooks Implementation

```python
# src/kagura/hooks/manager.py
import subprocess
import json
from enum import Enum
from typing import Callable, Optional

class HookExitCode(Enum):
    OK = 0           # Proceed with tool execution
    WARNING = 1      # Show warning to user (not Claude)
    BLOCK = 2        # Block tool execution and show to Claude

class HookResult:
    """Result from a hook execution"""

    def __init__(
        self,
        exit_code: HookExitCode,
        message: str = "",
        suggestion: Optional[str] = None
    ):
        self.exit_code = exit_code
        self.message = message
        self.suggestion = suggestion

    @classmethod
    def ok(cls):
        return cls(HookExitCode.OK)

    @classmethod
    def warn(cls, message: str):
        return cls(HookExitCode.WARNING, message)

    @classmethod
    def block(cls, message: str):
        return cls(HookExitCode.BLOCK, message)

    @classmethod
    def suggest(cls, message: str, suggestion: str):
        return cls(HookExitCode.WARNING, message, suggestion)

class HookManager:
    """Manage and execute hooks"""

    def __init__(self):
        self.pre_tool_use_hooks: dict[str, list[Callable]] = {}
        self.post_tool_use_hooks: dict[str, list[Callable]] = {}

    def register_pre_tool_use(self, tool_name: str, hook: Callable):
        """Register a PreToolUse hook"""
        if tool_name not in self.pre_tool_use_hooks:
            self.pre_tool_use_hooks[tool_name] = []
        self.pre_tool_use_hooks[tool_name].append(hook)

    def register_post_tool_use(self, tool_name: str, hook: Callable):
        """Register a PostToolUse hook"""
        if tool_name not in self.post_tool_use_hooks:
            self.post_tool_use_hooks[tool_name] = []
        self.post_tool_use_hooks[tool_name].append(hook)

    async def execute_pre_hooks(
        self,
        tool_name: str,
        tool_input: dict
    ) -> HookResult:
        """Execute all PreToolUse hooks for a tool"""
        hooks = self.pre_tool_use_hooks.get(tool_name, [])
        hooks.extend(self.pre_tool_use_hooks.get("*", []))

        for hook in hooks:
            if isinstance(hook, str):
                # External command hook
                result = self._execute_command_hook(hook, tool_name, tool_input)
            else:
                # Python function hook
                result = hook(tool_input)

            if result.exit_code != HookExitCode.OK:
                return result

        return HookResult.ok()

    def _execute_command_hook(
        self,
        command: str,
        tool_name: str,
        tool_input: dict
    ) -> HookResult:
        """Execute external command hook"""
        hook_input = {
            "tool_name": tool_name,
            "tool_input": tool_input
        }

        try:
            result = subprocess.run(
                command,
                input=json.dumps(hook_input),
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )

            exit_code = HookExitCode(result.returncode)
            message = result.stderr.strip()

            return HookResult(exit_code, message)

        except Exception as e:
            return HookResult.block(f"Hook execution failed: {e}")

# Global hook manager
hook_manager = HookManager()

# Decorator API
class hook:
    @staticmethod
    def pre_tool_use(tool_name: str):
        """Decorator for PreToolUse hooks"""
        def decorator(func: Callable):
            hook_manager.register_pre_tool_use(tool_name, func)
            return func
        return decorator

    @staticmethod
    def post_tool_use(tool_name: str):
        """Decorator for PostToolUse hooks"""
        def decorator(func: Callable):
            hook_manager.register_post_tool_use(tool_name, func)
            return func
        return decorator
```

## テスト戦略

```python
# tests/commands/test_loader.py
import pytest
from kagura.commands import CommandLoader
from pathlib import Path

def test_load_command(tmp_path):
    # Create test command
    cmd_file = tmp_path / "test.md"
    cmd_file.write_text("""---
name: test-cmd
description: Test command
allowed_tools: [git]
---

Test content: !`echo "hello"`
""")

    loader = CommandLoader(tmp_path)
    command = loader.load_command(cmd_file)

    assert command.name == "test-cmd"
    assert command.allowed_tools == ["git"]

def test_inline_command_execution():
    loader = CommandLoader()

    template = "Current dir: !`pwd`"
    result = loader.execute_inline_commands(template)

    assert "Current dir:" in result
    assert result != template
```

## セキュリティ考慮事項

1. **Inline Command Execution**
   - タイムアウト設定（デフォルト10秒）
   - 危険なコマンドのブロックリスト
   - サンドボックス実行（オプション）

2. **Hooks**
   - Hook実行のタイムアウト
   - Hook失敗時の安全なフォールバック
   - 信頼できるHooksのみ実行

3. **Allowed Tools**
   - ツール実行前にallowed_toolsをチェック
   - 違反時はブロック

## マイグレーション

既存のKaguraユーザーへの影響なし。新機能として追加：

```bash
# コマンドディレクトリ作成
mkdir -p ~/.kagura/commands
mkdir -p ~/.kagura/hooks

# サンプルコマンド作成
kagura command init commit-pr
```

## ドキュメント

### 必要なドキュメント
1. Custom Commands Guide
2. Writing Hooks Tutorial
3. Command Template Reference
4. Security Best Practices
5. Command Sharing Guide

## 参考資料

- [Claude Code Commands](https://docs.anthropic.com/en/docs/claude-code)
- [Python Frontmatter](https://python-frontmatter.readthedocs.io/)

## 改訂履歴

- 2025-10-04: 初版作成（Claude Codeのコマンド・フックシステムを参考）
