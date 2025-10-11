# RFC-017: Shell Integration & Command Execution

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-09
- **関連Issue**: #84
- **優先度**: High

## 概要

Kagura AIにセキュアなシェルコマンド実行機能を統合し、ビルトインエージェントとして提供します。

### 目標
- セキュアなBash/シェルコマンド実行エンジン
- ビルトインエージェント（`@builtin.shell`）として提供
- Git、ファイルシステム操作の高度な統合
- サンドボックス環境での安全な実行

### 非目標
- 任意のシステムコマンドの無制限実行（セキュリティリスク）
- リモートサーバーへのSSH接続（スコープ外）

## モチベーション

### 現在の課題
1. エージェントからシステムコマンドを実行できない
2. CodeExecutorはPythonコード専用で、シェル操作ができない
3. Git操作、ファイル管理などの自動化が困難
4. ユーザーが手動でコマンドを実行する必要がある

### 解決するユースケース
- **Git自動化**: コミット、プッシュ、PR作成
- **ファイル操作**: 検索、整理、バックアップ
- **開発ツール統合**: npm/pip install、ビルド、テスト実行
- **システム情報取得**: ディスク容量、プロセス監視
- **CI/CDパイプライン**: デプロイ、リリース自動化

### なぜ今実装すべきか
- v2.0.0のコア機能完成後の自然な拡張
- RFC-012（Commands & Hooks）との相乗効果
- RFC-007（MCP）でShellツールとして公開可能

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         User / Agent                        │
│  @agent                                     │
│  async def deploy():                        │
│      await shell.exec("git push")           │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│       Shell Integration Layer               │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  ShellExecutor                      │   │
│  │  - Command validation               │   │
│  │  - Sandbox enforcement              │   │
│  │  - Timeout management               │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│                 ▼                           │
│  ┌─────────────────────────────────────┐   │
│  │  Built-in Agents                    │   │
│  │  - @builtin.shell                   │   │
│  │  - @builtin.git                     │   │
│  │  - @builtin.file                    │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│                 ▼                           │
│  ┌─────────────────────────────────────┐   │
│  │  Security Layer                     │   │
│  │  - Whitelist commands               │   │
│  │  - Blacklist dangerous operations   │   │
│  │  - User confirmation (optional)     │   │
│  └──────────────┬──────────────────────┘   │
└─────────────────┼───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│       Execution Environment                 │
│  - subprocess (restricted)                  │
│  - Docker container (future)                │
│  - Working directory isolation              │
└─────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. ShellExecutor

```python
# src/kagura/core/shell.py
from typing import Optional, List, Dict
from pathlib import Path
import subprocess
import shlex
import asyncio

class ShellExecutor:
    """Secure shell command executor"""

    def __init__(
        self,
        allowed_commands: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None,
        working_dir: Optional[Path] = None,
        timeout: int = 30,
        require_confirmation: bool = False
    ):
        self.allowed_commands = allowed_commands or self._default_allowed()
        self.blocked_commands = blocked_commands or self._default_blocked()
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout
        self.require_confirmation = require_confirmation

    @staticmethod
    def _default_allowed() -> List[str]:
        """Default whitelist of allowed commands"""
        return [
            # Git
            "git",
            # File operations
            "ls", "cat", "find", "grep", "mkdir", "rm", "cp", "mv",
            # Package managers
            "npm", "pip", "uv", "poetry", "yarn",
            # Build tools
            "make", "cmake", "cargo", "go",
            # Testing
            "pytest", "jest", "vitest",
            # Others
            "echo", "pwd", "which", "wc", "sort", "uniq"
        ]

    @staticmethod
    def _default_blocked() -> List[str]:
        """Blacklist of dangerous commands"""
        return [
            "sudo", "su", "passwd", "shutdown", "reboot",
            "dd", "mkfs", "fdisk", "parted",
            "eval", "exec", "source",
            "curl -s | sh", "wget -O - | sh"
        ]

    def validate_command(self, command: str) -> bool:
        """Validate command against whitelist/blacklist"""
        parts = shlex.split(command)
        if not parts:
            return False

        cmd = parts[0]

        # Check blacklist first
        for blocked in self.blocked_commands:
            if blocked in command:
                raise SecurityError(f"Blocked command: {blocked}")

        # Check whitelist
        if self.allowed_commands:
            if cmd not in self.allowed_commands:
                raise SecurityError(f"Command not allowed: {cmd}")

        return True

    async def exec(
        self,
        command: str,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True
    ) -> ShellResult:
        """Execute shell command"""
        self.validate_command(command)

        if self.require_confirmation:
            confirmed = await self._ask_confirmation(command)
            if not confirmed:
                raise UserCancelledError("Command execution cancelled")

        try:
            result = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                cwd=str(self.working_dir),
                env=env
            )

            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=self.timeout
            )

            return ShellResult(
                return_code=result.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                command=command
            )

        except asyncio.TimeoutError:
            result.kill()
            raise TimeoutError(f"Command timed out after {self.timeout}s")

    async def _ask_confirmation(self, command: str) -> bool:
        """Ask user confirmation for command execution"""
        # To be implemented with CLI/UI integration
        print(f"Execute command: {command}? [y/N] ", end="")
        response = input()
        return response.lower() == "y"


class ShellResult:
    """Result of shell command execution"""

    def __init__(
        self,
        return_code: int,
        stdout: str,
        stderr: str,
        command: str
    ):
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        self.command = command

    @property
    def success(self) -> bool:
        return self.return_code == 0

    def __str__(self) -> str:
        return self.stdout if self.success else self.stderr


class SecurityError(Exception):
    """Raised when command violates security policy"""
    pass


class UserCancelledError(Exception):
    """Raised when user cancels command execution"""
    pass
```

#### 2. Built-in Shell Agent

```python
# src/kagura/builtin/shell.py
from kagura import agent
from kagura.core.shell import ShellExecutor

# Global executor instance
_executor = ShellExecutor()


@agent(model="gpt-4o-mini", builtin=True)
async def shell(command: str, working_dir: str = ".") -> str:
    """
    Execute a shell command safely.

    Args:
        command: The shell command to execute
        working_dir: Working directory (default: current directory)

    Returns:
        Command output (stdout/stderr)

    Example:
        >>> await shell("ls -la")
        >>> await shell("git status")
    """
    from pathlib import Path

    executor = ShellExecutor(working_dir=Path(working_dir))
    result = await executor.exec(command)

    if not result.success:
        raise RuntimeError(f"Command failed: {result.stderr}")

    return result.stdout
```

#### 3. Built-in Git Agent

```python
# src/kagura/builtin/git.py
from kagura import agent
from kagura.core.shell import ShellExecutor
from typing import List, Optional

_executor = ShellExecutor(allowed_commands=["git"])


@agent(model="gpt-4o-mini", builtin=True)
async def git_commit(
    message: str,
    files: Optional[List[str]] = None,
    all: bool = False
) -> str:
    """
    Create a git commit.

    Args:
        message: Commit message
        files: Files to commit (optional)
        all: Commit all changes (git commit -a)

    Returns:
        Git commit output
    """
    commands = []

    if files:
        for file in files:
            commands.append(f"git add {file}")
    elif all:
        commands.append("git add -A")

    commands.append(f'git commit -m "{message}"')

    results = []
    for cmd in commands:
        result = await _executor.exec(cmd)
        results.append(result.stdout)

    return "\n".join(results)


@agent(model="gpt-4o-mini", builtin=True)
async def git_push(remote: str = "origin", branch: Optional[str] = None) -> str:
    """
    Push commits to remote repository.

    Args:
        remote: Remote name (default: origin)
        branch: Branch name (default: current branch)

    Returns:
        Git push output
    """
    if branch:
        cmd = f"git push {remote} {branch}"
    else:
        cmd = f"git push {remote}"

    result = await _executor.exec(cmd)
    return result.stdout


@agent(model="gpt-4o-mini", builtin=True)
async def git_status() -> str:
    """
    Get git repository status.

    Returns:
        Git status output
    """
    result = await _executor.exec("git status")
    return result.stdout


@agent(model="gpt-4o-mini", builtin=True)
async def git_create_pr(
    title: str,
    body: str,
    base: str = "main"
) -> str:
    """
    Create a pull request using GitHub CLI.

    Args:
        title: PR title
        body: PR description
        base: Base branch (default: main)

    Returns:
        PR URL
    """
    cmd = f'gh pr create --title "{title}" --body "{body}" --base {base}'
    result = await _executor.exec(cmd)
    return result.stdout
```

#### 4. Built-in File Agent

```python
# src/kagura/builtin/file.py
from kagura import agent
from kagura.core.shell import ShellExecutor
from typing import List

_executor = ShellExecutor(allowed_commands=["find", "grep", "ls", "cat"])


@agent(model="gpt-4o-mini", builtin=True)
async def file_search(
    pattern: str,
    directory: str = ".",
    file_type: str = "*"
) -> List[str]:
    """
    Search for files matching pattern.

    Args:
        pattern: File name pattern
        directory: Directory to search
        file_type: File extension (e.g., "*.py")

    Returns:
        List of matching file paths
    """
    cmd = f'find {directory} -name "{file_type}" -type f | grep "{pattern}"'
    result = await _executor.exec(cmd)

    if not result.stdout:
        return []

    return result.stdout.strip().split("\n")


@agent(model="gpt-4o-mini", builtin=True)
async def grep_content(pattern: str, files: List[str]) -> dict:
    """
    Search for content in files.

    Args:
        pattern: Text pattern to search
        files: List of files to search

    Returns:
        Dict of file -> matching lines
    """
    results = {}

    for file in files:
        cmd = f'grep -n "{pattern}" {file}'
        result = await _executor.exec(cmd)

        if result.stdout:
            results[file] = result.stdout.strip().split("\n")

    return results
```

### API設計

#### 基本的な使い方

```python
from kagura.builtin import shell, git_commit, git_push, file_search

# Shell command execution
output = await shell("ls -la")
print(output)

# Git operations
await git_commit("feat: add new feature", files=["src/main.py"])
await git_push()

# File operations
files = await file_search("test", directory="./tests", file_type="*.py")
print(files)
```

#### エージェント内での使用

```python
from kagura import agent
from kagura.builtin import shell, git_commit, git_push

@agent(model="gpt-4o-mini")
async def deploy_to_production(version: str) -> str:
    """
    Deploy version {{ version }} to production.

    Steps:
    1. Run tests
    2. Build project
    3. Tag version
    4. Push to GitHub
    5. Deploy
    """
    # 1. Run tests
    test_result = await shell("pytest tests/")
    if "FAILED" in test_result:
        return "Tests failed, aborting deployment"

    # 2. Build
    await shell("uv build")

    # 3. Git operations
    await git_commit(f"chore: release v{version}")
    await shell(f"git tag v{version}")
    await git_push()
    await shell("git push --tags")

    # 4. Deploy
    await shell(f"./scripts/deploy.sh {version}")

    return f"✓ Deployed v{version} to production"
```

#### RFC-012 Commands統合

```markdown
---
name: auto-deploy
allowed_tools: [shell, git]
---

## Task
Automatically deploy the latest version:
1. Run tests
2. Create commit
3. Push to GitHub
4. Deploy

Use @builtin.shell and @builtin.git agents.
```

### 統合例

#### 例1: 自動コミット & PR作成

```python
from kagura import agent
from kagura.builtin import git_status, git_commit, git_push, git_create_pr

@agent(model="gpt-4o-mini")
async def auto_pr(feature_name: str) -> str:
    """
    Create a PR for {{ feature_name }} automatically.
    """
    # Check status
    status = await git_status()
    if "nothing to commit" in status:
        return "No changes to commit"

    # Create commit
    await git_commit(f"feat: implement {feature_name}")

    # Push
    await git_push()

    # Create PR
    pr_url = await git_create_pr(
        title=f"feat: implement {feature_name}",
        body=f"This PR implements {feature_name}\n\nAuto-generated by Kagura AI"
    )

    return f"✓ PR created: {pr_url}"
```

#### 例2: コードレビュー自動化

```python
from kagura import agent
from kagura.builtin import shell, grep_content, file_search

@agent(model="gpt-4o-mini")
async def code_review_checklist() -> dict:
    """
    Run automated code review checklist.
    """
    issues = {}

    # 1. Find Python files
    py_files = await file_search("*.py", directory="src/")

    # 2. Check for TODO comments
    todos = await grep_content("TODO", py_files)
    if todos:
        issues["todos"] = todos

    # 3. Check for print statements (should use logging)
    prints = await grep_content("print(", py_files)
    if prints:
        issues["print_statements"] = prints

    # 4. Run type checker
    pyright_output = await shell("pyright src/")
    if "error" in pyright_output.lower():
        issues["type_errors"] = pyright_output

    return issues
```

#### 例3: プロジェクトセットアップ自動化

```python
from kagura import agent
from kagura.builtin import shell

@agent(model="gpt-4o-mini")
async def setup_python_project(project_name: str) -> str:
    """
    Setup a new Python project with {{ project_name }}.
    """
    commands = [
        f"mkdir {project_name}",
        f"cd {project_name}",
        "uv init",
        "uv add pytest pyright ruff",
        "mkdir src tests docs",
        "git init",
        'git add .',
        'git commit -m "Initial commit"'
    ]

    results = []
    for cmd in commands:
        result = await shell(cmd)
        results.append(f"✓ {cmd}")

    return "\n".join(results)
```

## 実装計画

### Phase 1: Core Shell Executor (v2.1.0)
- [ ] ShellExecutor基本実装
- [ ] コマンド検証（whitelist/blacklist）
- [ ] セキュリティレイヤー
- [ ] タイムアウト管理

### Phase 2: Built-in Agents (v2.1.0)
- [ ] @builtin.shell
- [ ] @builtin.git (commit, push, status)
- [ ] @builtin.file (search, grep)
- [ ] ドキュメント・サンプル

### Phase 3: Advanced Features (v2.2.0)
- [ ] User confirmation UI
- [ ] Docker sandbox (optional)
- [ ] Command history/logging
- [ ] RFC-012 Commands統合

### Phase 4: MCP Integration (v2.3.0)
- [ ] ShellツールのMCP公開
- [ ] Claude Codeから呼び出し可能に
- [ ] セキュリティポリシー共有

## 技術的詳細

### 依存関係

```toml
[project.dependencies]
# 既存の依存関係に追加なし（標準ライブラリで実装可能）

[project.optional-dependencies]
shell = [
    "docker>=6.0.0",  # Optional: Docker sandbox
]
```

### セキュリティポリシー設定

`~/.kagura/security.toml`:

```toml
[shell]
# Enable shell execution
enabled = true

# Require user confirmation for dangerous commands
require_confirmation = true

# Timeout (seconds)
timeout = 30

# Allowed commands (whitelist)
allowed_commands = [
    "git", "npm", "pip", "uv", "pytest",
    "ls", "cat", "grep", "find"
]

# Blocked commands (blacklist)
blocked_commands = [
    "sudo", "su", "rm -rf /", "dd",
    "eval", "exec", "curl -s | sh"
]

# Working directory restrictions
allowed_directories = [
    "~/projects",
    "~/work"
]
```

### エラーハンドリング

```python
from kagura.builtin import shell
from kagura.core.shell import SecurityError, TimeoutError

try:
    result = await shell("git push")
except SecurityError as e:
    print(f"Security violation: {e}")
except TimeoutError as e:
    print(f"Command timed out: {e}")
except Exception as e:
    print(f"Execution failed: {e}")
```

## テスト戦略

### ユニットテスト

```python
# tests/core/test_shell.py
import pytest
from kagura.core.shell import ShellExecutor, SecurityError

@pytest.mark.asyncio
async def test_shell_executor_basic():
    executor = ShellExecutor()
    result = await executor.exec("echo 'hello'")

    assert result.success
    assert "hello" in result.stdout

@pytest.mark.asyncio
async def test_shell_executor_blocked_command():
    executor = ShellExecutor()

    with pytest.raises(SecurityError):
        await executor.exec("sudo rm -rf /")

@pytest.mark.asyncio
async def test_shell_executor_timeout():
    executor = ShellExecutor(timeout=1)

    with pytest.raises(TimeoutError):
        await executor.exec("sleep 10")
```

### 統合テスト

```python
# tests/builtin/test_git.py
import pytest
from kagura.builtin import git_status, git_commit

@pytest.mark.asyncio
async def test_git_status():
    status = await git_status()
    assert isinstance(status, str)

@pytest.mark.asyncio
async def test_git_commit(tmp_path):
    # Setup test repo
    # ... (create test git repo)

    result = await git_commit("test commit", all=True)
    assert "test commit" in result
```

## セキュリティ考慮事項

1. **Command Injection対策**
   - `shlex.split()` による安全なパース
   - 入力の厳格な検証

2. **Sandbox実行**
   - Working directory制限
   - 環境変数制御
   - オプション: Docker container内実行

3. **リソース制限**
   - タイムアウト設定
   - 同時実行数制限
   - メモリ使用制限（将来）

4. **監査ログ**
   - 実行コマンドの記録
   - 成功/失敗の追跡
   - セキュリティ違反の検出

## マイグレーション

既存のKaguraユーザーへの影響なし。Shell機能はオプトイン：

```python
# 明示的な有効化が必要
from kagura.builtin import shell

# または設定ファイルで有効化
# ~/.kagura/config.toml
[features]
shell = true
```

## ドキュメント

### 必要なドキュメント
1. Shell Integration クイックスタートガイド
2. セキュリティベストプラクティス
3. Built-in Agents リファレンス
4. トラブルシューティングFAQ

### サンプルコード
- Git自動化ワークフロー
- CI/CDパイプライン統合
- プロジェクトセットアップ自動化

## 代替案

### 案1: Python subprocess直接使用
- 各エージェントで`subprocess`を直接呼び出し
- **却下理由**: セキュリティリスク、一貫性なし

### 案2: 既存ツール（fabric、invoke等）使用
- タスクランナーライブラリ統合
- **却下理由**: 依存関係増加、オーバースペック

### 案3: Docker-only実行
- 全てのコマンドをDockerコンテナ内で実行
- **却下理由**: セットアップが複雑、パフォーマンス低下

## 未解決の問題

1. **インタラクティブコマンド**
   - 標準入力が必要なコマンドの扱い
   - パスワードプロンプト等

2. **並列実行**
   - 複数コマンドの同時実行
   - リソース競合の解決

3. **クロスプラットフォーム**
   - Windows/Mac/Linuxでのコマンド互換性
   - シェル差異（bash/zsh/powershell）

## 参考資料

- [subprocess — Subprocess management](https://docs.python.org/3/library/subprocess.html)
- [shlex — Simple lexical analysis](https://docs.python.org/3/library/shlex.html)
- [Docker Python SDK](https://docker-py.readthedocs.io/)

## 改訂履歴

- 2025-10-09: 初版作成
