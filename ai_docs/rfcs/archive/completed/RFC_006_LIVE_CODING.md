# RFC-006: Live Coding - AI-Powered Pair Programming

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: #66
- **優先度**: High

## 概要

Kagura AIをリアルタイムペアプログラミングパートナーとして機能させます。ユーザーがコードを書いている最中に、AIがリアルタイムで提案、補完、デバッグ、テストをサポートします。さらに、**対話型Chat REPL**により、ターミナルから即座にAIと自然言語で対話できます。

### 目標
- **対話型Chat REPL**（`kagura chat`）でエージェント定義不要の即座の対話
- リアルタイムコード補完とインテリジェントな提案
- エディタ統合（VS Code、Cursor、Vim/Neovimなど）
- インタラクティブなデバッグとエラー修正
- テスト駆動開発（TDD）のワークフロー統合
- ペアプログラミング体験の実現

### 非目標
- 完全自動コーディング（人間の判断を尊重）
- IDE全体の置き換え（既存エディタとの統合に注力）

## モチベーション

### 現在の課題
1. GitHub Copilot等は提案のみで、対話的なペアプログラミングではない
2. コード生成後のデバッグやテストは手動
3. コンテキストを保持しながらの継続的な開発が困難

### 解決するユースケース
- **即座のAI対話**: ターミナルから`kagura chat`で即座にAIアシスタント起動
- **ワンタイムタスク**: コード書くほどでもない質問・翻訳・要約を即実行
- **リアルタイムペアプログラミング**: AIとペアを組んでコーディング
- **コードレビュー**: 書いたコードをその場でレビュー
- **TDD**: テストを書きながら実装を進める
- **リファクタリング**: 既存コードを対話的に改善
- **デバッグ**: エラーをリアルタイムで解決

### なぜ今実装すべきか
- GPT-4o、Claude 3.5 Sonnetなど、コード理解に優れたモデルの登場
- ストリーミングAPIでリアルタイム応答が可能
- LSP（Language Server Protocol）により、エディタ統合が標準化

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│            User Interfaces                  │
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │  VS Code     │  │  Vim/Neovim  │        │
│  │  Extension   │  │  Plugin      │        │
│  └──────┬───────┘  └───────┬──────┘        │
│         │                  │               │
│         └─────────┬────────┘               │
│                   │                        │
│        ┌──────────▼─────────┐              │
│        │   LSP Server       │              │
│        │  (Kagura LSP)      │              │
│        └──────────┬─────────┘              │
│                   │                        │
│  ┌────────────────┼────────────────┐       │
│  │                │                │       │
│  │   ┌────────────▼────────────┐   │       │
│  │   │  Interactive Chat REPL │   │       │
│  │   │  - kagura chat         │   │       │
│  │   │  - Natural language    │   │       │
│  │   │  - Session management  │   │       │
│  │   └────────────┬────────────┘   │       │
│  └────────────────┼────────────────┘       │
└───────────────────┼────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│          Kagura Live Coding Core            │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │    Code Context Manager             │   │
│  │  - File watching                    │   │
│  │  - AST parsing                      │   │
│  │  - Dependency tracking              │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │    Real-time Agent Engine           │   │
│  │  - Streaming responses              │   │
│  │  - Code completion                  │   │
│  │  - Inline suggestions               │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │    Interactive Debugger             │   │
│  │  - Error detection                  │   │
│  │  - Fix suggestions                  │   │
│  │  - Test execution                   │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. Kagura LSP Server

Language Server Protocolを実装し、各種エディタと統合：

```python
from kagura.live import LSPServer

server = LSPServer()

@server.on_completion()
async def provide_completion(document, position):
    """コード補完を提供"""
    context = server.get_context(document, position)
    suggestions = await agent.complete(context)
    return suggestions

@server.on_hover()
async def provide_hover(document, position):
    """ホバー時の情報表示"""
    symbol = server.get_symbol(document, position)
    explanation = await agent.explain(symbol)
    return explanation

@server.on_code_action()
async def provide_code_action(document, range, diagnostics):
    """コードアクション（リファクタリング、修正提案）"""
    actions = await agent.suggest_actions(document, range, diagnostics)
    return actions
```

#### 2. Interactive Chat REPL

ターミナルから即座にAIと対話できるチャットモード：

```bash
# Chat REPL起動
kagura chat

# または既存REPLからチャットモード
kagura repl --chat
```

```python
from kagura import agent
from kagura.chat import ChatSession
from rich.console import Console
from rich.markdown import Markdown

@agent(model="gpt-4o-mini", streaming=True)
async def chat_agent(history: list[dict], user_input: str) -> str:
    """
    Previous conversation:
    {% for msg in history %}
    {{ msg.role }}: {{ msg.content }}
    {% endfor %}

    User: {{ user_input }}

    Respond naturally and helpfully. Provide code examples when relevant.
    """
    pass

class ChatSession:
    """Interactive chat session manager"""

    def __init__(self):
        self.console = Console()
        self.history = []
        self.presets = {
            "translate": "Translate text",
            "summarize": "Summarize content",
            "review": "Review code",
            "debug": "Debug code"
        }

    async def run(self):
        """Run interactive chat loop"""
        self.console.print("[bold green]Kagura Chat[/] - Type /help for commands\n")

        while True:
            user_input = self.console.input("[bold blue]You:[/] ")

            # Commands
            if user_input.startswith("/"):
                await self.handle_command(user_input)
                continue

            # Regular chat
            response = await chat_agent(self.history, user_input)

            self.console.print("\n[bold green]AI:[/]")
            async for chunk in response:
                self.console.print(chunk, end="")
            self.console.print("\n")

            # Save history
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": response})

    async def handle_command(self, cmd: str):
        """Handle slash commands"""
        if cmd == "/help":
            self.show_help()
        elif cmd == "/clear":
            self.history = []
        elif cmd == "/save":
            self.save_session()
        elif cmd.startswith("/translate"):
            # Preset agent
            text = cmd.split(" ", 2)[2] if len(cmd.split()) > 2 else ""
            await self.preset_translate(text)
        # ... more commands
```

**使用例:**

```bash
$ kagura chat

You: このコードレビューして
[コード貼り付け]

AI: このコードには以下の改善点があります:
    1. エラーハンドリングが不足しています
    2. 型ヒントを追加すべきです
    ...

You: じゃあ修正コード書いて

AI: 修正版です:
```python
def process(data: dict) -> Result:
    try:
        if not data:
            raise ValueError("Empty data")
        return Result(data)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
```

You: /save
Session saved to: ~/.kagura/sessions/2025-10-04_10-30.json

You: /exit
```

**Preset Commands:**

```bash
# 翻訳
You: /translate "Hello" to ja
AI: こんにちは

# 要約
You: /summarize [長い文章]
AI: [要約結果]

# コードレビュー
You: /review
[コード貼り付け]
AI: [レビュー結果]
```

#### 3. Real-time Code Agent

リアルタイムでコードを理解し、提案を生成：

```python
from kagura import agent, live

@agent(model="gpt-4o", streaming=True)
@live.context_aware
async def code_assistant(request: str, context: dict) -> str:
    """
    Real-time coding assistant.

    Context includes:
    - Current file: {{ context.file }}
    - Cursor position: {{ context.position }}
    - Recent changes: {{ context.changes }}
    - Project structure: {{ context.project }}

    Request: {{ request }}
    """
    pass

# ストリーミング応答
async for chunk in code_assistant.stream("Add error handling"):
    print(chunk, end="", flush=True)
```

#### 4. Interactive REPL with Live Editing

REPLとエディタを融合：

```bash
# ライブコーディングREPL起動
kagura live

# ファイルを開く
> /open src/main.py

# AIとペアプログラミング
You: この関数にエラーハンドリングを追加して
AI: [リアルタイムでコード修正を提案]

# インラインでコード実行
You: /run test_main.py
AI: テストを実行中... ✓ 3 passed

# コードレビュー
You: /review
AI: 以下の改善点があります:
    1. Line 15: 例外処理が不足
    2. Line 23: 型ヒントがありません
```

#### 5. TDD Workflow Integration

テスト駆動開発のワークフロー：

```python
from kagura import live, agent

@live.tdd_mode
class Calculator:
    """電卓クラス"""

    @live.test_first
    def add(self, a: int, b: int) -> int:
        """
        Add two numbers.

        AI will:
        1. Generate test cases first
        2. Suggest implementation
        3. Run tests automatically
        """
        pass

# ライブコーディングセッション
session = live.TDDSession("calculator.py")

# AIがテストを先に生成
await session.generate_tests()
# => test_calculator.py作成

# 実装提案
await session.implement("add")
# => 実装コードを提案

# 自動テスト
await session.run_tests()
# => pytest実行、結果表示
```

### API設計

#### `kagura live` コマンド

```bash
# 基本起動
kagura live

# ファイルを指定して起動
kagura live src/main.py

# TDDモード
kagura live --tdd tests/test_main.py

# エディタ統合モード
kagura live --lsp --port 9999
```

#### エディタプラグイン

**VS Code Extension:**

```json
{
  "kagura.enable": true,
  "kagura.model": "gpt-4o-mini",
  "kagura.streaming": true,
  "kagura.features": {
    "completion": true,
    "hover": true,
    "codeAction": true,
    "refactor": true
  }
}
```

**Neovim Plugin:**

```lua
require('kagura').setup({
  model = 'gpt-4o-mini',
  streaming = true,
  keybindings = {
    complete = '<C-k>',
    explain = '<leader>e',
    refactor = '<leader>r',
    test = '<leader>t'
  }
})
```

### 統合例

#### 例1: リアルタイムペアプログラミング

**ユーザーがコードを書く:**
```python
def process_data(data):
    # AIがリアルタイムで提案
    |  # ← カーソル位置
```

**AIが自動提案:**
```python
def process_data(data):
    """Process input data with validation and error handling."""
    if not data:
        raise ValueError("Data cannot be empty")

    # Type validation
    if not isinstance(data, (list, dict)):
        raise TypeError("Data must be list or dict")

    # Process
    result = []
    for item in data:
        processed = transform(item)
        result.append(processed)

    return result
```

#### 例2: インタラクティブデバッグ

**エラー検出:**
```python
# ユーザーがコードを書く
result = api.fetch_data()
print(result.name)  # ← エラー: AttributeError

# AIが即座に検出して提案
AI: ⚠️ Line 2: 'result' may be None. Add null check:

if result is not None:
    print(result.name)
else:
    print("No data")

# または
print(result.name if result else "No data")
```

#### 例3: TDDワークフロー

```bash
kagura live --tdd

# ステップ1: 要件を伝える
You: ユーザー認証機能を実装したい

AI: テストケースを生成します...

# test_auth.py 生成
def test_login_success():
    user = authenticate("john", "password123")
    assert user is not None
    assert user.username == "john"

def test_login_invalid_password():
    user = authenticate("john", "wrongpass")
    assert user is None

# ステップ2: 実装提案
AI: 実装を提案します...

# auth.py 生成
def authenticate(username: str, password: str) -> User | None:
    user = db.get_user(username)
    if user and verify_password(password, user.password_hash):
        return user
    return None

# ステップ3: テスト実行
AI: テストを実行します...
✓ test_login_success
✓ test_login_invalid_password

2 passed in 0.12s
```

#### 例4: コードレビューとリファクタリング

```python
# 既存コード
def calc(x, y, op):
    if op == '+':
        return x + y
    elif op == '-':
        return x - y
    elif op == '*':
        return x * y
    else:
        return x / y

# AIのレビュー
AI: このコードには以下の改善点があります:

1. 型ヒントがありません
2. ゼロ除算のチェックがありません
3. 関数名が不明瞭です
4. サポートされない演算子の処理がありません

リファクタリング案:

from typing import Literal

Operator = Literal['+', '-', '*', '/']

def calculate(x: float, y: float, operator: Operator) -> float:
    """
    Perform arithmetic operation on two numbers.

    Args:
        x: First number
        y: Second number
        operator: Arithmetic operator

    Returns:
        Result of the operation

    Raises:
        ValueError: If operator is invalid or division by zero
    """
    operations = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b if b != 0 else (_ for _ in ()).throw(ValueError("Division by zero"))
    }

    if operator not in operations:
        raise ValueError(f"Invalid operator: {operator}")

    return operations[operator](x, y)
```

## 実装計画

### Phase 1: Core Live Coding & Chat Mode (v2.2.0)
- [ ] **Interactive Chat REPL** (`kagura chat`)
- [ ] チャット履歴管理・セッション保存
- [ ] Preset agents（translate, summarize, review）
- [ ] ストリーミング応答表示（Rich統合）
- [ ] リアルタイムストリーミングエージェント
- [ ] コンテキスト管理（ファイル、プロジェクト構造）
- [ ] `kagura live` REPLコマンド
- [ ] 基本的なコード補完・提案

### Phase 2: LSP Integration (v2.3.0)
- [ ] Kagura LSP Server実装
- [ ] VS Code Extension開発
- [ ] Neovim Plugin開発
- [ ] LSP機能（completion, hover, codeAction）

### Phase 3: TDD & Testing (v2.4.0)
- [ ] TDDワークフロー統合
- [ ] テスト自動生成
- [ ] テスト実行・結果表示
- [ ] カバレッジトラッキング

### Phase 4: Advanced Features (v2.5.0)
- [ ] インタラクティブデバッガ
- [ ] リファクタリング提案
- [ ] コードレビュー機能
- [ ] プロジェクト全体の最適化提案

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
live = [
    "pygls>=1.3.0",           # Language Server Protocol
    "watchdog>=3.0.0",        # File watching
    "tree-sitter>=0.20.4",    # Fast AST parsing
    "jedi>=0.19.1",           # Python code analysis
    "rope>=1.11.0",           # Refactoring library
    "pytest-watch>=4.2.0",    # Live test execution
]
```

### LSP実装

```python
# src/kagura/live/lsp.py
from pygls.server import LanguageServer
from kagura import agent

server = LanguageServer("kagura-lsp", "v2.0")

@server.feature(TEXT_DOCUMENT_COMPLETION)
async def completion(params):
    """Code completion"""
    document = server.workspace.get_document(params.text_document.uri)
    position = params.position

    # コンテキスト取得
    context = extract_context(document, position)

    # AI補完
    @agent(model="gpt-4o-mini", streaming=False)
    async def complete_code(ctx: str) -> list[str]:
        """Suggest code completions for: {{ ctx }}"""
        pass

    completions = await complete_code(context)
    return [CompletionItem(label=c) for c in completions]

@server.feature(TEXT_DOCUMENT_HOVER)
async def hover(params):
    """Hover information"""
    document = server.workspace.get_document(params.text_document.uri)
    position = params.position

    symbol = get_symbol_at_position(document, position)

    @agent(model="gpt-4o-mini")
    async def explain_symbol(sym: str) -> str:
        """Explain this code symbol: {{ sym }}"""
        pass

    explanation = await explain_symbol(symbol)
    return Hover(contents=MarkupContent(kind="markdown", value=explanation))
```

### ストリーミング応答

```python
from kagura import agent

@agent(model="gpt-4o", streaming=True)
async def live_code_assistant(prompt: str) -> str:
    """{{ prompt }}"""
    pass

# リアルタイム出力
async for chunk in live_code_assistant.stream("Implement user authentication"):
    # エディタにリアルタイム表示
    editor.insert_at_cursor(chunk)
    await asyncio.sleep(0.01)  # スムーズな表示
```

### ファイル監視

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CodeChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        """ファイル変更時にAI分析"""
        if event.src_path.endswith('.py'):
            analyze_and_suggest(event.src_path)

observer = Observer()
observer.schedule(CodeChangeHandler(), path="src/", recursive=True)
observer.start()
```

## テスト戦略

### ユニットテスト

```python
# tests/live/test_lsp.py
import pytest
from kagura.live import LSPServer

@pytest.mark.asyncio
async def test_code_completion():
    server = LSPServer()
    document = create_test_document("def hello(")
    position = Position(line=0, character=11)

    completions = await server.completion(document, position)

    assert len(completions) > 0
    assert any("name: str" in c.label for c in completions)
```

### 統合テスト

```python
# tests/live/test_live_session.py
import pytest
from kagura import live

@pytest.mark.asyncio
async def test_live_coding_session():
    session = live.Session("test.py")

    # AIに実装依頼
    await session.request("Create a fibonacci function")

    # 生成されたコードを確認
    code = session.get_code()
    assert "def fibonacci" in code

    # テスト実行
    result = await session.run_tests()
    assert result.passed
```

## セキュリティ考慮事項

1. **コード実行の制限**
   - サンドボックス環境でのテスト実行
   - 危険なコードの検出と警告

2. **プライバシー**
   - ローカルコードの外部送信は最小限に
   - センシティブな情報（パスワード、APIキー）の自動検出・除外
   - ユーザーの明示的な許可を取得

3. **リソース管理**
   - LSPサーバーのメモリ使用量制限
   - 長時間実行タスクのタイムアウト

## マイグレーション

既存のKaguraユーザーへの影響なし。ライブコーディング機能はオプトイン：

```bash
# ライブコーディング機能のインストール
pip install kagura-ai[live]

# VS Code拡張インストール
code --install-extension kagura.kagura-live

# Neovimプラグインインストール
:KaguraInstall
```

## ドキュメント

### 必要なドキュメント
1. Live Coding クイックスタートガイド
2. エディタプラグイン設定ガイド
3. TDDワークフローチュートリアル
4. LSPカスタマイズリファレンス
5. トラブルシューティングFAQ

### サンプルコード
- ペアプログラミングセッション例
- TDD実践例
- リファクタリングワークフロー
- デバッグセッション例

## 代替案

### 案1: GitHub Copilot風のスタンドアロンプラグイン
- 各エディタ専用のプラグイン開発
- **却下理由**: メンテナンスコスト高、統一体験が困難

### 案2: Webベースエディタ統合
- ブラウザで動くエディタ提供
- **却下理由**: ユーザーは既存エディタを使いたい

### 案3: CLIのみ（エディタ統合なし）
- `kagura live` REPLのみ提供
- **却下理由**: 開発体験が分断される

## 未解決の問題

1. **レイテンシの最小化**
   - リアルタイム補完には低レイテンシが必須
   - ローカルLLMとクラウドLLMのハイブリッド戦略

2. **コンテキストウィンドウの管理**
   - 大規模プロジェクトでのコンテキスト選択
   - 関連ファイルの自動検出

3. **エディタごとの挙動の違い**
   - LSPの実装差異への対応
   - 統一されたUX提供

## 参考資料

- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)
- [GitHub Copilot](https://github.com/features/copilot)
- [Cursor](https://cursor.sh/)
- [Codeium](https://codeium.com/)
- [Tabnine](https://www.tabnine.com/)

## 改訂履歴

- 2025-10-04: 初版作成
