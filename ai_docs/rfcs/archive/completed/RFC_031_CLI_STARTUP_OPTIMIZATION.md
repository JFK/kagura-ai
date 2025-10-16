# RFC-031: CLI Startup Optimization

**ステータス**: Draft
**作成日**: 2025-10-15
**優先度**: 🔥 High (UX Critical)
**関連Issue**: TBD
**依存RFC**: なし

---

## 📋 概要

### 問題

現在のKagura AI CLIの起動が**非常に遅い**です：

```bash
$ time kagura --help
real    0m8.823s  # 8.8秒！
user    0m7.697s
sys     0m0.918s
```

**原因分析**（`python -X importtime`）:
```
import time:       706 |    7715782 | kagura.cli.main  # 7.7秒！

内訳:
- mcp パッケージ:      393ms (393,283μs)
  - uvicorn:           20ms
  - sse_starlette:     22ms
  - fastmcp.server:   151ms
- observability:       3.2ms (Rich含む)
- その他:              ~0.3ms
```

**ユーザー影響**:
- ✅ `kagura --help` → **8.8秒待機** ← 許容不可
- ✅ `kagura chat` → **8.8秒 + chat起動** ← 体験悪化
- ✅ 全コマンドが影響を受ける

### 根本原因

**トップレベルでの即座インポート**:
```python
# src/kagura/cli/main.py (現状 - ❌ 悪い)
from .mcp import mcp              # 393ms - 使われない場合も読み込む！
from .monitor import monitor      # 3.2ms
from .chat import chat
from .repl import repl
# ...
```

**問題点**:
1. `kagura --help` でもMCPサーバー関連をすべてインポート
2. `kagura chat` でもMonitor/REPL/MCPをすべてインポート
3. 実際に使うコマンドは1つだけなのに、全部読み込む

### 解決策

**Lazy Loading（遅延インポート）** - 使用時のみインポート

**期待効果**:
- ✅ `kagura --help`: **8.8秒 → 0.3秒** (97%削減)
- ✅ `kagura chat`: **8.8秒 → 0.5秒** (94%削減)
- ✅ 初回体験が劇的に改善

---

## 🎯 目標

### 成功指標

1. **起動速度**
   - ✅ `kagura --help`: **0.3秒以下** (現状: 8.8秒)
   - ✅ `kagura chat`: **0.5秒以下** (現状: 8.8秒+)
   - ✅ `kagura mcp start`: **1.0秒以下** (現状: 8.8秒+)

2. **ユーザー体験**
   - ✅ 体感的に「速い」と感じる
   - ✅ 初回実行でストレスなし
   - ✅ 頻繁に使うコマンドが高速

3. **後方互換性**
   - ✅ 既存コード変更不要
   - ✅ すべてのテスト通過
   - ✅ API変更なし

---

## 🏗️ アーキテクチャ

### 現在の構成（❌ 遅い）

```
$ kagura --help
   ↓
main.py (トップレベル)
   ├─ from .mcp import mcp          # 393ms - 不要なのに読み込む！
   ├─ from .monitor import monitor  # 3.2ms
   ├─ from .chat import chat        # ...
   ├─ from .repl import repl        # ...
   └─ from .build_cli import build_group
   ↓
cli() 関数実行 (--help表示)
   → mcp/monitor/chat は使わないのに読み込み済み ← 無駄！
```

### 改善後の構成（✅ 速い）

```
$ kagura --help
   ↓
main.py (トップレベル)
   ├─ （何もインポートしない）
   └─ lazy command定義のみ
   ↓
cli() 関数実行 (--help表示)
   → インポートなし、即座に表示 ✅

---

$ kagura mcp start
   ↓
main.py (トップレベル)
   └─ （何もインポートしない）
   ↓
mcp コマンド実行
   └─ from .mcp import mcp  # ← この時点で初めてインポート ✅
```

---

## 📦 Phase 1: Lazy Loading実装 (Week 1)

### 実装内容

#### 1.1 LazyGroup実装

```python
# src/kagura/cli/lazy.py

import click
from typing import Callable, Optional

class LazyGroup(click.Group):
    """Lazy-loading Click Group

    Subcommands are imported only when invoked.
    This dramatically reduces CLI startup time.
    """

    def __init__(self, *args, lazy_subcommands: Optional[dict[str, tuple[str, str]]] = None, **kwargs):
        """Initialize lazy group

        Args:
            lazy_subcommands: Dict of {command_name: (module_path, attr_name)}
                Example: {"mcp": ("kagura.cli.mcp", "mcp")}
        """
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        """Get command, importing lazily if needed"""
        # Try regular command first
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd

        # Lazy load if defined
        if cmd_name in self.lazy_subcommands:
            module_path, attr_name = self.lazy_subcommands[cmd_name]

            # Import module lazily
            import importlib
            module = importlib.import_module(module_path)

            # Get command
            cmd = getattr(module, attr_name)

            # Cache it for next time
            self.add_command(cmd, cmd_name)

            return cmd

        return None

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List all commands (including lazy ones)"""
        regular = super().list_commands(ctx)
        lazy = list(self.lazy_subcommands.keys())
        return sorted(set(regular + lazy))
```

#### 1.2 main.pyのリファクタ

```python
# src/kagura/cli/main.py

import click
from ..version import __version__
from .lazy import LazyGroup


@click.group(cls=LazyGroup, lazy_subcommands={
    "repl": ("kagura.cli.repl", "repl"),
    "chat": ("kagura.cli.chat", "chat"),
    "mcp": ("kagura.cli.mcp", "mcp"),
    "run": ("kagura.cli.commands_cli", "run"),
    "monitor": ("kagura.cli.monitor", "monitor"),
    "auth": ("kagura.cli.auth_cli", "auth_group"),
    "build": ("kagura.cli.build_cli", "build_group"),
})
@click.version_option(version=__version__, prog_name="Kagura AI")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool):
    """
    Kagura AI - Python-First AI Agent Framework

    A framework for building AI agents with code execution capabilities.
    Use subcommands to interact with the framework.

    Examples:
      kagura version          Show version information
      kagura --help           Show this help message
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@cli.command()
@click.pass_context
def version(ctx: click.Context):
    """Show version information"""
    if not ctx.obj.get("quiet"):
        click.echo(f"Kagura AI v{__version__}")
        if ctx.obj.get("verbose"):
            click.echo("Python-First AI Agent Framework")
            click.echo("https://github.com/JFK/kagura-ai")


if __name__ == "__main__":
    cli(obj={})
```

**Before**:
```python
# ❌ Slow
from .mcp import mcp              # 393ms
from .monitor import monitor      # 3.2ms
from .chat import chat
# ...

cli.add_command(mcp)
cli.add_command(monitor)
```

**After**:
```python
# ✅ Fast
@click.group(cls=LazyGroup, lazy_subcommands={
    "mcp": ("kagura.cli.mcp", "mcp"),        # Import only when used
    "monitor": ("kagura.cli.monitor", "monitor"),
    # ...
})
```

### テスト

```python
# tests/cli/test_lazy_loading.py

import time
import subprocess
import pytest

def test_help_is_fast():
    """Test that --help is fast (< 0.5s)"""
    start = time.time()
    result = subprocess.run(
        ["kagura", "--help"],
        capture_output=True,
        text=True
    )
    duration = time.time() - start

    assert result.returncode == 0
    assert duration < 0.5, f"--help took {duration:.2f}s (expected < 0.5s)"

def test_chat_startup_is_fast():
    """Test that chat startup is fast (< 1.0s)"""
    start = time.time()
    result = subprocess.run(
        ["kagura", "chat", "--help"],
        capture_output=True,
        text=True
    )
    duration = time.time() - start

    assert result.returncode == 0
    assert duration < 1.0, f"chat --help took {duration:.2f}s (expected < 1.0s)"

def test_lazy_loading_works():
    """Test that lazy loading actually imports on demand"""
    # This should NOT import mcp module
    result = subprocess.run(
        ["python", "-c",
         "from kagura.cli.main import cli; "
         "import sys; "
         "print('mcp' in sys.modules)"],
        capture_output=True,
        text=True
    )

    assert "False" in result.stdout, "mcp module should not be imported"

def test_all_commands_still_work():
    """Test that all commands still work after lazy loading"""
    commands = ["repl", "chat", "mcp", "monitor", "auth", "build"]

    for cmd in commands:
        result = subprocess.run(
            ["kagura", cmd, "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"{cmd} command failed"
        assert len(result.stdout) > 0, f"{cmd} has no help output"

# 10+ more tests...
```

### 完了条件

- [ ] LazyGroup実装
- [ ] main.pyリファクタ
- [ ] 10+ tests全パス
- [ ] 起動速度: `kagura --help` < 0.5秒
- [ ] 既存テスト（1,213+）全パス
- [ ] ドキュメント更新

---

## 📦 Phase 2: Progress Indicator（オプション） (Week 2)

### 目標

長時間かかるコマンドの体感速度向上

### 実装内容

#### 2.1 Spinnerの追加

```python
# src/kagura/cli/progress.py

import click
import time
from contextlib import contextmanager

@contextmanager
def spinner(message: str = "Loading..."):
    """Show spinner during long operations

    Example:
        with spinner("Starting MCP server..."):
            # Long operation
            time.sleep(2)
    """
    import threading
    import sys

    stop_spinner = threading.Event()

    def spin():
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while not stop_spinner.is_set():
            frame = frames[i % len(frames)]
            sys.stderr.write(f"\r{frame} {message}")
            sys.stderr.flush()
            time.sleep(0.1)
            i += 1
        sys.stderr.write("\r" + " " * (len(message) + 3) + "\r")
        sys.stderr.flush()

    thread = threading.Thread(target=spin, daemon=True)
    thread.start()

    try:
        yield
    finally:
        stop_spinner.set()
        thread.join(timeout=0.5)
```

#### 2.2 長時間コマンドへの適用

```python
# src/kagura/cli/mcp.py (例)

from .progress import spinner

@mcp.command()
def start(...):
    """Start MCP server"""
    with spinner("Starting MCP server..."):
        # Import heavy dependencies here
        from ..mcp.server import MCPServer
        # ... server setup ...

    click.echo("✓ MCP server started")
```

### テスト

```python
# tests/cli/test_progress.py

import time
from kagura.cli.progress import spinner

def test_spinner_works():
    """Test that spinner displays correctly"""
    with spinner("Testing..."):
        time.sleep(0.5)
    # If no exception, it works

def test_spinner_cleans_up():
    """Test that spinner cleans up after itself"""
    import sys
    import io

    stderr = io.StringIO()
    sys.stderr = stderr

    with spinner("Test"):
        time.sleep(0.2)

    sys.stderr = sys.__stderr__
    output = stderr.getvalue()

    # Should contain spinner frames
    assert any(frame in output for frame in ["⠋", "⠙", "⠹"])

    # Should clean up (last line empty)
    assert output.rstrip().endswith("\r")

# 5+ more tests...
```

### 完了条件

- [ ] Spinner実装
- [ ] 長時間コマンドへの適用（mcp start, chat等）
- [ ] 5+ tests全パス
- [ ] UXレビュー（体感速度向上）

---

## 📊 成功指標

### Phase 1完了時（Lazy Loading）

**起動速度**:
- ✅ `kagura --help`: **8.8秒 → 0.3秒** (97%削減)
- ✅ `kagura chat --help`: **8.8秒 → 0.5秒** (94%削減)
- ✅ `kagura mcp start`: **8.8秒 → 1.0秒** (89%削減)

**品質**:
- ✅ 15+ 新規テスト全パス
- ✅ 既存テスト（1,213+）全パス
- ✅ Pyright 0 errors
- ✅ 後方互換性100%

### Phase 2完了時（Progress Indicator）

**UX**:
- ✅ 長時間コマンドにSpinner表示
- ✅ 体感速度向上（ユーザーフィードバック）
- ✅ プロフェッショナルなCLI体験

---

## 📝 ドキュメント

### 開発者ガイド

```markdown
# docs/en/guides/cli-performance.md

## CLI Performance

Kagura CLI uses lazy loading to ensure fast startup times.

### Lazy Loading

Subcommands are imported only when invoked:

```python
# Before (slow)
from .mcp import mcp  # Always imported

# After (fast)
@click.group(cls=LazyGroup, lazy_subcommands={
    "mcp": ("kagura.cli.mcp", "mcp")  # Import on demand
})
```

### Adding New Commands

When adding a new CLI command, use lazy loading:

```python
# src/kagura/cli/main.py

@click.group(cls=LazyGroup, lazy_subcommands={
    "mycommand": ("kagura.cli.mycommand", "mycommand"),
})
```

### Performance Guidelines

1. **Avoid top-level imports** of heavy modules
2. **Use lazy loading** for all subcommands
3. **Add spinners** for operations > 0.5s
4. **Test startup time** in CI

### Benchmarking

```bash
# Measure startup time
time kagura --help

# Profile imports
python -X importtime -c "from kagura.cli.main import cli" 2>&1 | tail -50
```
```

---

## 🚀 実装順序

### Week 1: Lazy Loading
- Day 1: LazyGroup実装
- Day 2: main.pyリファクタ
- Day 3-4: テスト（15+ tests）
- Day 5: 既存テスト確認、修正
- Day 6-7: ドキュメント、PR作成

### Week 2: Progress Indicator（オプション）
- Day 1-2: Spinner実装
- Day 3: 長時間コマンドへの適用
- Day 4: テスト（5+ tests）
- Day 5: UXレビュー
- Day 6-7: ドキュメント、PR作成

---

## 📋 チェックリスト

### Phase 1 完了条件
- [ ] LazyGroup実装
- [ ] main.pyリファクタ（lazy_subcommands）
- [ ] 15+ tests全パス
- [ ] `kagura --help` < 0.5秒
- [ ] `kagura chat --help` < 1.0秒
- [ ] 既存テスト（1,213+）全パス
- [ ] Pyright 0 errors
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

### Phase 2 完了条件（オプション）
- [ ] Spinner実装
- [ ] 長時間コマンドへの適用
- [ ] 5+ tests全パス
- [ ] UXレビュー合格
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

---

## 🎓 参考資料

### Lazy Loading Patterns
- [Click Documentation - Custom Multi Commands](https://click.palletsprojects.com/en/8.1.x/commands/#custom-multi-commands)
- [Python importlib](https://docs.python.org/3/library/importlib.html)

### CLI Performance Best Practices
- [Click Performance Tips](https://click.palletsprojects.com/en/8.1.x/advanced/#performance)
- [Python Startup Time Optimization](https://wiki.python.org/moin/PythonSpeed/PerformanceTips#Import_Statement_Overhead)

### Progress Indicators
- [Click Progress Bars](https://click.palletsprojects.com/en/8.1.x/api/#click.progressbar)
- [Rich Progress](https://rich.readthedocs.io/en/stable/progress.html)

---

## 💡 技術的な考察

### なぜLazy Loadingが効果的か

**インポート時間の内訳**:
```
mcp パッケージ:     393ms
  ├─ uvicorn:        20ms (ASGI server)
  ├─ sse_starlette:  22ms (Server-Sent Events)
  └─ fastmcp:       151ms (FastMCP server)
```

**使用頻度分析**（推測）:
- `kagura --help`: 50% ← mcpは不要
- `kagura chat`: 30% ← mcpは不要
- `kagura mcp`: 10% ← mcpが必要
- その他: 10%

**結論**: 90%のケースでmcpインポートは不要 → Lazy Loadingで大幅高速化

### 代替案の検討

#### 案1: Top-level import削減（採用）✅
- **メリット**: 最大の効果、後方互換性維持
- **デメリット**: LazyGroup実装が必要

#### 案2: エントリーポイント分割
```bash
kagura-mcp start  # 別バイナリ
kagura-chat      # 別バイナリ
```
- **メリット**: 各コマンド完全独立
- **デメリット**: UX悪化、複数バイナリ管理

#### 案3: Import最適化
```python
# Heavy importを遅延
def mcp_start():
    import uvicorn  # ← 関数内でインポート
```
- **メリット**: 簡単
- **デメリット**: 効果限定的（Click解析は残る）

**選択**: 案1（Lazy Loading）が最適

---

**このRFCにより、Kagura AI CLIは世界最速級のPython CLIになります！**
