# Code Execution & Chat Interface - 設計プラン

## 要件整理

### ユーザーの要望
1. **リクエストに応じてPythonコードを生成・実行**
2. **他のライブラリもimportして使える汎用性**
3. **Chatインターフェースの要否を検討**
4. **Kagura 2.0のコンセプトは維持**

---

## 分析: Chatインターフェースは必要か？

### 現状の`kagura chat`の役割

```python
# 現在の実装
@click.command()
def chat():
    """Start interactive chat with Kagura AI"""
    # 既存のchatエージェントと対話
```

**既存の課題**:
- 単なるLLMチャット(エージェント実行とは別)
- コード生成・実行機能なし
- 汎用ライブラリとしての活用が限定的

### 💡 結論: **Chatインターフェースは必要だが、進化が必要**

**理由**:

1. **開発者向けREPL的な使い方**
   ```bash
   kagura repl  # または kagura dev
   # エージェントをインタラクティブに試せる
   ```

2. **プロダクション向けはAPI/SDK**
   ```python
   # Pythonライブラリとして使う
   from kagura import agent
   result = await my_agent(input)
   ```

3. **ハイブリッドアプローチ**
   - **CLI Chat**: 開発・デバッグ用
   - **Python SDK**: プログラマティック利用
   - **API Server**: 外部統合

---

## 提案: Kagura 2.0 の3つのインターフェース

### 1. Python SDK (Primary) - コア機能

```python
from kagura import agent, executor

@agent
async def code_generator(task: str) -> str:
    """Generate Python code for: {{ task }}"""
    pass

@agent(execute_code=True)  # 🔥 新機能
async def code_executor(task: str) -> dict:
    """
    Generate and execute Python code for: {{ task }}
    Return both code and execution result.
    """
    pass

# 使い方
result = await code_executor("Calculate fibonacci(10)")
# => {
#   "code": "def fib(n): ...",
#   "output": "55",
#   "success": True
# }
```

### 2. Interactive REPL - 開発・デバッグ用

```bash
$ kagura repl

🎭 Kagura AI REPL v2.0

>>> @agent
... async def hello(name: str) -> str:
...     """Say hello to {{ name }}"""
...     pass

Agent 'hello' registered ✓

>>> await hello("World")
Hello, World!

>>> execute("pip install requests and fetch https://example.com")
Executing code...
Output: <html>...</html>

>>> /agents
Available agents:
  - hello
  - code_executor

>>> /help
Commands:
  /agents   - List agents
  /execute  - Execute code
  /run      - Run agent
  /exit     - Exit REPL
```

### 3. API Server (Optional) - 外部統合

```python
# kagura serve で起動
from kagura import serve

@serve
class MyAPI:
    @agent
    async def process(self, input: str) -> str:
        pass
```

```bash
$ kagura serve my_agents.py --port 8000

# POST /execute
# POST /agents/process
```

---

## 🔥 新機能: Code Execution Agent

### コンセプト

**"Ask → Generate Code → Execute → Return Result"**

### 基本設計

```python
# kagura/core/executor.py

import ast
import sys
from io import StringIO
from typing import Any, Dict
import contextlib

class CodeExecutor:
    """Safe Python code executor with sandboxing"""

    def __init__(
        self,
        allowed_imports: list[str] | None = None,
        timeout: int = 30
    ):
        self.allowed_imports = allowed_imports or [
            "math", "json", "datetime", "re", "itertools",
            "collections", "functools", "typing",
            # 追加可能なライブラリ
            "requests", "pandas", "numpy", "httpx"
        ]
        self.timeout = timeout

    def validate_code(self, code: str) -> bool:
        """Validate code for dangerous operations"""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # 危険な操作をチェック
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_imports:
                            raise ValueError(f"Import not allowed: {alias.name}")

                if isinstance(node, ast.ImportFrom):
                    if node.module not in self.allowed_imports:
                        raise ValueError(f"Import not allowed: {node.module}")

                # ファイル操作の制限
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["open", "exec", "eval", "compile"]:
                            raise ValueError(f"Function not allowed: {node.func.id}")

            return True
        except SyntaxError as e:
            raise ValueError(f"Syntax error: {e}")

    async def execute(
        self,
        code: str,
        timeout: int | None = None
    ) -> Dict[str, Any]:
        """
        Execute Python code safely

        Returns:
            {
                "success": bool,
                "output": str,
                "error": str | None,
                "result": Any
            }
        """
        # バリデーション
        self.validate_code(code)

        # 出力をキャプチャ
        stdout = StringIO()
        stderr = StringIO()

        result = {
            "success": False,
            "output": "",
            "error": None,
            "result": None
        }

        try:
            # 実行環境の準備
            globals_dict = {"__builtins__": __builtins__}
            locals_dict = {}

            # タイムアウト付きで実行
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    # async対応
                    import asyncio
                    exec(code, globals_dict, locals_dict)

                    # 最後の式の評価結果を取得
                    if locals_dict:
                        result["result"] = locals_dict.get("result")

            result["success"] = True
            result["output"] = stdout.getvalue()

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            result["output"] = stderr.getvalue()

        return result
```

### エージェント統合

```python
# kagura/agents/code_executor.py

from kagura import agent
from kagura.core.executor import CodeExecutor

executor = CodeExecutor(
    allowed_imports=[
        "math", "json", "datetime", "re",
        "requests", "pandas", "numpy", "httpx"
    ]
)

@agent
async def execute_code(task: str) -> dict:
    """
    Generate and execute Python code for the task: {{ task }}

    Steps:
    1. Generate Python code
    2. Validate for safety
    3. Execute code
    4. Return results

    You must return valid Python code that accomplishes the task.
    """
    pass  # LLMがコード生成

# 実際の使用
from kagura.core.agent import agent

@agent(
    post_process=executor.execute  # 生成後に自動実行
)
async def smart_executor(task: str) -> dict:
    """
    Generate Python code to: {{ task }}

    Return only the Python code, no explanations.
    """
    pass
```

---

## 使用例

### 例1: 基本的な計算

```python
from kagura.agents import execute_code

result = await execute_code("Calculate fibonacci(20)")

print(result)
# {
#   "success": True,
#   "code": "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\nresult = fib(20)",
#   "output": "",
#   "result": 6765
# }
```

### 例2: 外部ライブラリ使用

```python
result = await execute_code(
    "Fetch JSON from https://api.github.com/repos/JFK/kagura-ai and extract stargazers_count"
)

# 生成されるコード:
# import requests
# response = requests.get("https://api.github.com/repos/JFK/kagura-ai")
# data = response.json()
# result = data["stargazers_count"]
```

### 例3: データ分析

```python
result = await execute_code(
    """
    Create a pandas DataFrame with columns [name, age, city]:
    - Alice, 25, Tokyo
    - Bob, 30, NYC
    - Charlie, 35, London

    Calculate average age
    """
)

# 生成されるコード:
# import pandas as pd
# df = pd.DataFrame([
#     {"name": "Alice", "age": 25, "city": "Tokyo"},
#     {"name": "Bob", "age": 30, "city": "NYC"},
#     {"name": "Charlie", "age": 35, "city": "London"}
# ])
# result = df["age"].mean()
```

---

## セキュリティ対策

### 1. Import制限

```python
ALLOWED_IMPORTS = [
    # 標準ライブラリ
    "math", "json", "datetime", "re", "collections",
    "itertools", "functools", "typing", "pathlib",

    # データ処理
    "pandas", "numpy", "polars",

    # HTTP
    "requests", "httpx",

    # その他
    "beautifulsoup4", "lxml",
]

BLOCKED_IMPORTS = [
    "os", "sys", "subprocess", "shutil",  # システム操作
    "socket", "asyncio.subprocess",        # ネットワーク
    "__import__", "importlib",            # 動的import
]
```

### 2. 関数制限

```python
BLOCKED_FUNCTIONS = [
    "exec", "eval", "compile",   # コード実行
    "open",                       # ファイル操作
    "__import__",                 # 動的import
    "globals", "locals", "vars",  # スコープアクセス
]
```

### 3. タイムアウト

```python
@agent(timeout=30)  # 30秒でタイムアウト
async def execute_code(task: str) -> dict:
    pass
```

### 4. リソース制限

```python
import resource

# メモリ制限: 512MB
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, -1))

# CPU時間制限: 30秒
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
```

---

## REPLインターフェース改善案

### 現在の`kagura chat`を進化

```python
# kagura/cli/commands/repl_command.py

@click.command()
@click.option("--unsafe", is_flag=True, help="Allow all imports (危険)")
def repl(unsafe: bool):
    """Interactive REPL for Kagura AI"""

    console = Console()
    executor = CodeExecutor(
        allowed_imports=None if unsafe else DEFAULT_ALLOWED_IMPORTS
    )

    console.print("[bold green]🎭 Kagura AI REPL v2.0[/bold green]")
    console.print("\nCommands:")
    console.print("  @agent    - Define new agent")
    console.print("  execute   - Execute Python code")
    console.print("  /agents   - List agents")
    console.print("  /help     - Show help")
    console.print("  /exit     - Exit\n")

    agents = {}

    while True:
        try:
            prompt = Prompt.ask("[bold cyan]>>>[/bold cyan]")

            if prompt.startswith("@agent"):
                # エージェント定義モード
                agent_code = collect_multiline_input()
                # エージェント登録
                pass

            elif prompt.startswith("execute "):
                code = prompt[8:]
                result = await executor.execute(code)
                console.print(result)

            elif prompt.startswith("/"):
                # コマンド処理
                handle_command(prompt)

            else:
                # 通常のチャット
                await chat_agent.process(prompt)

        except KeyboardInterrupt:
            break
```

### 使用例

```bash
$ kagura repl

🎭 Kagura AI REPL v2.0

>>> execute print("Hello World")
Executing...
Hello World
✓ Success

>>> @agent
... async def summarize(text: str) -> str:
...     """Summarize: {{ text }}"""
...     pass

Agent 'summarize' registered ✓

>>> await summarize("Long text...")
This is a summary...

>>> execute import pandas as pd; df = pd.DataFrame({"a": [1,2,3]}); print(df.mean())
   a
0  2.0
✓ Success
```

---

## 実装優先順位

### Phase 1: Code Executor Core (2週間)

- [ ] `CodeExecutor`クラス実装
- [ ] AST解析によるバリデーション
- [ ] セキュリティ制限
- [ ] ユニットテスト

### Phase 2: Agent Integration (1週間)

- [ ] `@agent(execute_code=True)`デコレータ
- [ ] コード生成→実行パイプライン
- [ ] エラーハンドリング

### Phase 3: REPL Enhancement (2週間)

- [ ] `kagura repl`コマンド
- [ ] マルチライン入力
- [ ] エージェント定義機能
- [ ] コマンド拡張

### Phase 4: Advanced Features (2週間)

- [ ] ファイルシステムサンドボックス
- [ ] Docker統合(完全隔離)
- [ ] ストリーミング出力
- [ ] デバッグモード

---

## ディレクトリ構造

```
kagura/
├── core/
│   ├── executor.py           # 🆕 Code executor
│   ├── sandbox.py            # 🆕 Sandboxing
│   └── validator.py          # 🆕 Code validator
├── agents/
│   ├── code_executor.py      # 🆕 Built-in agent
│   └── code_generator.py     # 🆕 Code gen agent
├── cli/
│   └── commands/
│       ├── repl_command.py   # 🆕 Enhanced REPL
│       └── execute_command.py # 🆕 One-off execution
└── integrations/
    └── jupyter.py            # 🆕 Jupyter integration
```

---

## まとめ

### ✅ 推奨アプローチ

1. **Chat → REPL に進化**
   - 開発者向けインタラクティブ環境
   - エージェント定義・テスト・実行を統合

2. **Code Execution を組み込み機能に**
   - `@agent(execute_code=True)`
   - セキュアなサンドボックス実行
   - 汎用ライブラリ対応

3. **3つのインターフェース**
   - **Python SDK**: メイン(プログラマティック)
   - **REPL**: 開発・デバッグ
   - **API Server**: 外部統合

### 🎯 ゴール

```python
# たった数行で、リクエストに応じてコード生成・実行
from kagura.agents import execute_code

result = await execute_code(
    "Fetch latest Bitcoin price and calculate 30-day moving average"
)

print(result["code"])    # 生成されたコード
print(result["result"])  # 実行結果
```

**Kagura AI 2.0 = AI Agent + Code Executor + REPL の統合フレームワーク**
