# RFC-005 Phase 3: Self-Improving Agent Implementation Plan

**Status**: Planning
**Created**: 2025-10-15
**Phase**: 3 of 3 (Final Phase)
**Priority**: High
**Estimated Time**: 1-2 weeks
**Dependencies**: Phase 1 ✅, Phase 2 ✅

---

## 📋 概要

Meta Agent Phase 3では、**Self-Improving（自己改善）**機能を実装します。生成されたエージェントがエラーを起こした場合、自動的にエラーを分析し、コードを修正し、再試行する機能です。

### Phase 1 & 2の成果

**Phase 1: Meta Agent Core** ✅
- 自然言語 → AgentSpec → Pythonコード生成
- `kagura build agent` CLI実装
- REPL/Chat統合

**Phase 2: Code-Aware Agent** ✅
- コード実行必要性の自動検出
- `execute_code` ツール自動追加
- Code execution template生成

### Phase 3の目標

**Self-Improving Agent**:
- エラー自動検出・分析
- コード自動修正（AST操作 + LLM）
- フィードバック学習
- リトライロジック

---

## 🎯 問題定義

### 現在の課題

**Phase 2完了後の生成エージェント**:
```python
# 生成されたエージェント
@agent(tools=[execute_code])
async def data_analyst(csv_path: str) -> dict:
    """Analyze CSV and calculate stats"""
    pass

# 実行
result = await data_analyst("sales.csv")
```

**問題**:
- ❌ CSVファイルが存在しない → エラーで停止
- ❌ 列名が想定と違う → エラーで停止
- ❌ 生成されたコードにバグ → エラーで停止
- ❌ ユーザーが手動で修正する必要がある

**Phase 3で解決**:
- ✅ エラー発生時に自動分析
- ✅ コード自動修正（最大3回リトライ）
- ✅ エラーから学習（次回同じエラーを回避）
- ✅ ユーザーに修正提案

---

## 🏗️ アーキテクチャ

### 全体フロー

```
┌─────────────────────────────────────────────────────┐
│           Self-Improving Agent Workflow             │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────┐
    │  1. Execute Generated Agent       │
    │     - Run with user input         │
    │     - Catch exceptions             │
    └───────────────┬───────────────────┘
                    │
            ┌───────┴────────┐
            │ Success?       │
            └───────┬────────┘
                    │
        ┌───────────┴───────────┐
        │ Yes                   │ No
        │                       │
        ▼                       ▼
    ┌────────┐      ┌──────────────────────┐
    │ Return │      │  2. ErrorAnalyzer    │
    │ Result │      │     - Parse error    │
    └────────┘      │     - Identify root  │
                    │       cause          │
                    │     - Suggest fix    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  3. CodeFixer        │
                    │     - Modify code    │
                    │     - Apply fix      │
                    │     - Validate AST   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  4. Retry Execution  │
                    │     Max 3 attempts   │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴──────────┐
                    │ Fixed?              │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │ Yes       │ No      │
                    │           │         │
                    ▼           ▼         │
                ┌────────┐  ┌─────────┐  │
                │ Return │  │ Report  │  │
                │ Result │  │ Error   │  │
                └────────┘  └─────────┘  │
                                         │
                               ┌─────────┴──────────┐
                               │  5. FeedbackLearner│
                               │     - Log error    │
                               │     - Store fix    │
                               │     - Improve next │
                               │       generation   │
                               └────────────────────┘
```

---

## 📦 実装コンポーネント

### 1. ErrorAnalyzer

**ファイル**: `src/kagura/meta/error_analyzer.py`

**機能**:
- Python例外の解析
- エラーの根本原因特定
- 修正方法の提案

**実装**:
```python
# src/kagura/meta/error_analyzer.py

import traceback
from dataclasses import dataclass
from typing import Any, Optional
from kagura.core.llm import call_llm, LLMConfig


@dataclass
class ErrorAnalysis:
    """Error analysis result"""

    error_type: str  # e.g., "FileNotFoundError"
    error_message: str
    stack_trace: str
    root_cause: str  # LLM-identified root cause
    suggested_fix: str  # How to fix it
    fix_code: Optional[str] = None  # Code snippet to apply


class ErrorAnalyzer:
    """Analyze runtime errors in generated agents"""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize error analyzer

        Args:
            llm_config: LLM configuration for error analysis
        """
        self.llm_config = llm_config or LLMConfig(
            model="gpt-4o-mini", temperature=0.3
        )

    async def analyze(
        self,
        exception: Exception,
        agent_code: str,
        user_input: dict[str, Any],
    ) -> ErrorAnalysis:
        """Analyze error and suggest fix

        Args:
            exception: Exception that occurred
            agent_code: Generated agent code
            user_input: User input that caused error

        Returns:
            ErrorAnalysis with suggested fix
        """
        # Extract error details
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

        # LLM-based analysis
        analysis_prompt = f"""
Analyze this error in a Kagura AI agent and suggest a fix.

**Agent Code:**
```python
{agent_code}
```

**User Input:**
{user_input}

**Error:**
Type: {error_type}
Message: {error_message}

**Stack Trace:**
{stack_trace}

**Task:**
1. Identify the root cause
2. Suggest a specific fix
3. Provide the corrected code snippet (if applicable)

**Output format:**
Root cause: [explanation]
Suggested fix: [fix description]
Fix code: [code snippet or "N/A"]
"""

        response = await call_llm(analysis_prompt, self.llm_config)

        # Parse LLM response
        root_cause = self._extract_section(response, "Root cause")
        suggested_fix = self._extract_section(response, "Suggested fix")
        fix_code = self._extract_section(response, "Fix code")

        return ErrorAnalysis(
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            fix_code=fix_code if fix_code != "N/A" else None,
        )

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract section from LLM response"""
        lines = text.split("\n")
        result = []
        in_section = False

        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                # Extract content after colon
                if ":" in line:
                    result.append(line.split(":", 1)[1].strip())
                continue

            if in_section:
                # Stop at next section
                if any(
                    keyword in line.lower()
                    for keyword in ["root cause", "suggested fix", "fix code"]
                ):
                    break
                result.append(line)

        return "\n".join(result).strip()
```

---

### 2. CodeFixer

**ファイル**: `src/kagura/meta/fixer.py`

**機能**:
- ErrorAnalysisに基づいてコード修正
- AST操作でコード変更
- 修正後のコード検証

**実装**:
```python
# src/kagura/meta/fixer.py

import ast
from typing import Optional
from kagura.meta.validator import CodeValidator
from kagura.meta.error_analyzer import ErrorAnalysis


class CodeFixer:
    """Fix errors in generated agent code"""

    def __init__(self):
        """Initialize code fixer"""
        self.validator = CodeValidator()

    def apply_fix(
        self,
        original_code: str,
        error_analysis: ErrorAnalysis,
    ) -> Optional[str]:
        """Apply fix to code

        Args:
            original_code: Original agent code
            error_analysis: Error analysis with suggested fix

        Returns:
            Fixed code or None if fix failed
        """
        if not error_analysis.fix_code:
            # No code fix suggested, return original
            return None

        try:
            # Attempt to apply fix
            fixed_code = self._apply_code_patch(
                original_code, error_analysis.fix_code
            )

            # Validate fixed code
            is_valid = self.validator.validate(fixed_code)
            if not is_valid:
                return None

            return fixed_code

        except Exception as e:
            # Fix failed
            return None

    def _apply_code_patch(self, original: str, fix_snippet: str) -> str:
        """Apply code patch (simple string replacement)

        For Phase 3, we use simple string-based patching.
        Future: AST-based code transformation (libcst)

        Args:
            original: Original code
            fix_snippet: Fix code snippet

        Returns:
            Fixed code
        """
        # Simple approach: If fix snippet is complete function,
        # replace the entire function

        try:
            # Parse fix snippet to see if it's a complete function
            fix_ast = ast.parse(fix_snippet)

            # If fix is a function definition, extract it
            for node in ast.walk(fix_ast):
                if isinstance(node, ast.FunctionDef):
                    # Replace function in original code
                    return self._replace_function(original, node.name, fix_snippet)

        except SyntaxError:
            pass

        # Fallback: If fix is a code snippet (not complete function),
        # try to intelligently insert it
        # For Phase 3, we return original if not applicable
        return original

    def _replace_function(
        self, original: str, func_name: str, new_func: str
    ) -> str:
        """Replace function definition in code

        Args:
            original: Original code
            func_name: Function name to replace
            new_func: New function code

        Returns:
            Code with replaced function
        """
        try:
            tree = ast.parse(original)

            # Find function definition
            for i, node in enumerate(tree.body):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    # Replace using line-based approach
                    lines = original.split("\n")
                    start_line = node.lineno - 1
                    end_line = node.end_lineno

                    # Replace lines
                    new_lines = (
                        lines[:start_line] + [new_func] + lines[end_line:]
                    )
                    return "\n".join(new_lines)

        except Exception:
            pass

        # Fallback: return original
        return original
```

---

### 3. SelfImprovingMetaAgent

**ファイル**: `src/kagura/meta/self_improving.py`

**機能**:
- MetaAgentを拡張
- エラーハンドリング + 自動修正
- リトライロジック（最大3回）

**実装**:
```python
# src/kagura/meta/self_improving.py

from typing import Any, Optional
from kagura.meta.meta_agent import MetaAgent
from kagura.meta.error_analyzer import ErrorAnalyzer, ErrorAnalysis
from kagura.meta.fixer import CodeFixer
from kagura.core.llm import LLMConfig
import logging

logger = logging.getLogger(__name__)


class SelfImprovingMetaAgent(MetaAgent):
    """Meta Agent with self-improving capabilities

    Extends MetaAgent to automatically fix errors in generated agents.
    """

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        max_retries: int = 3,
    ):
        """Initialize self-improving meta agent

        Args:
            llm_config: LLM configuration
            max_retries: Maximum retry attempts for error fixing
        """
        super().__init__(llm_config=llm_config)
        self.error_analyzer = ErrorAnalyzer(llm_config=llm_config)
        self.code_fixer = CodeFixer()
        self.max_retries = max_retries
        self._error_history: list[ErrorAnalysis] = []

    async def generate_with_retry(
        self,
        description: str,
        validate: bool = True,
    ) -> tuple[str, list[ErrorAnalysis]]:
        """Generate agent with automatic error fixing

        Args:
            description: Agent description
            validate: Whether to validate generated code

        Returns:
            Tuple of (generated_code, error_history)
        """
        # Initial generation
        code = await self.generate(description)

        if not validate:
            return code, []

        # Validate and fix if needed
        attempts = 0
        errors = []

        while attempts < self.max_retries:
            # Validate code
            is_valid = self.validator.validate(code)

            if is_valid:
                logger.info(f"Code validated successfully (attempt {attempts + 1})")
                return code, errors

            # Code has issues, analyze
            logger.warning(f"Validation failed (attempt {attempts + 1})")

            # Get validation errors
            # For Phase 3, we simulate validation errors
            # Future: CodeValidator should return detailed errors

            # Try to fix
            analysis = await self._analyze_validation_error(code, description)
            errors.append(analysis)

            fixed_code = self.code_fixer.apply_fix(code, analysis)

            if not fixed_code:
                logger.error("Failed to apply fix")
                break

            code = fixed_code
            attempts += 1

        # Max retries reached
        logger.error(f"Max retries ({self.max_retries}) reached")
        return code, errors

    async def execute_with_recovery(
        self,
        agent_code: str,
        user_input: dict[str, Any],
    ) -> tuple[Any, Optional[ErrorAnalysis]]:
        """Execute agent with automatic error recovery

        Args:
            agent_code: Generated agent code
            user_input: User input for agent

        Returns:
            Tuple of (result, error_if_failed)
        """
        attempts = 0
        current_code = agent_code

        while attempts < self.max_retries:
            try:
                # Execute agent
                # For Phase 3, we simulate execution
                # Real implementation would use CodeExecutor
                result = await self._execute_agent(current_code, user_input)
                return result, None

            except Exception as e:
                logger.warning(f"Execution failed (attempt {attempts + 1}): {e}")

                # Analyze error
                analysis = await self.error_analyzer.analyze(
                    exception=e,
                    agent_code=current_code,
                    user_input=user_input,
                )

                # Store for learning
                self._error_history.append(analysis)

                # Try to fix
                fixed_code = self.code_fixer.apply_fix(current_code, analysis)

                if not fixed_code:
                    # Cannot fix, return error
                    return None, analysis

                current_code = fixed_code
                attempts += 1

        # Max retries reached
        return None, self._error_history[-1] if self._error_history else None

    async def _analyze_validation_error(
        self, code: str, description: str
    ) -> ErrorAnalysis:
        """Analyze validation errors"""
        # Simplified for Phase 3
        # Future: Get actual validation errors from CodeValidator
        return ErrorAnalysis(
            error_type="ValidationError",
            error_message="Code validation failed",
            stack_trace="",
            root_cause="Syntax or type error in generated code",
            suggested_fix="Review code for syntax errors",
            fix_code=None,
        )

    async def _execute_agent(
        self, agent_code: str, user_input: dict[str, Any]
    ) -> Any:
        """Execute generated agent (simulated for Phase 3)"""
        # Future: Use CodeExecutor to actually run the agent
        # For now, validate only
        is_valid = self.validator.validate(agent_code)
        if not is_valid:
            raise ValueError("Generated code is invalid")
        return {"status": "success", "simulated": True}

    def get_error_history(self) -> list[ErrorAnalysis]:
        """Get error history for learning"""
        return self._error_history.copy()

    def clear_error_history(self) -> None:
        """Clear error history"""
        self._error_history.clear()
```

---

### 4. CLI Integration

**ファイル**: `src/kagura/cli/build_cli.py` (拡張)

**追加機能**:
- `--self-improve` フラグでSelf-Improving有効化
- エラー発生時の自動修正プロセス表示

**実装**:
```python
# src/kagura/cli/build_cli.py

@click.option(
    "--self-improve",
    is_flag=True,
    default=False,
    help="Enable self-improving mode (auto-fix errors)",
)
async def build_agent(..., self_improve: bool):
    """Build agent CLI with self-improving option"""

    if self_improve:
        # Use SelfImprovingMetaAgent
        meta = SelfImprovingMetaAgent()
        console.print("[bold cyan]Self-improving mode enabled[/bold cyan]")
    else:
        # Use regular MetaAgent
        meta = MetaAgent()

    # Generate
    code, errors = await meta.generate_with_retry(description, validate=True)

    # Display errors if any
    if errors:
        console.print("\n[yellow]⚠️  Errors encountered:[/yellow]")
        for i, err in enumerate(errors, 1):
            console.print(f"  {i}. {err.error_type}: {err.suggested_fix}")

    # Display final code
    console.print("\n[bold green]✓ Generated agent:[/bold green]")
    console.print(Syntax(code, "python", theme="monokai"))
```

---

## 📝 実装ステップ

### Phase 3-1: ErrorAnalyzer Implementation (Day 1-2)

**タスク**:
1. `ErrorAnalysis` dataclass作成
2. `ErrorAnalyzer` クラス実装
3. LLMベースのエラー分析ロジック
4. テスト5個追加

**成果物**:
- `src/kagura/meta/error_analyzer.py`: 新規（150行）
- `tests/meta/test_error_analyzer.py`: 新規（100行、5テスト）

### Phase 3-2: CodeFixer Implementation (Day 3-4)

**タスク**:
1. `CodeFixer` クラス実装
2. 単純なコードパッチロジック（string-based）
3. AST検証統合
4. テスト5個追加

**成果物**:
- `src/kagura/meta/fixer.py`: 新規（120行）
- `tests/meta/test_fixer.py`: 新規（90行、5テスト）

### Phase 3-3: SelfImprovingMetaAgent (Day 5-6)

**タスク**:
1. `SelfImprovingMetaAgent` クラス実装
2. リトライロジック（最大3回）
3. エラー履歴管理
4. テスト10個追加

**成果物**:
- `src/kagura/meta/self_improving.py`: 新規（200行）
- `tests/meta/test_self_improving.py`: 新規（200行、10テスト）

### Phase 3-4: CLI Integration (Day 7)

**タスク**:
1. `--self-improve` フラグ追加
2. エラー表示UI改善
3. テスト3個追加

**成果物**:
- `src/kagura/cli/build_cli.py`: +30行
- `tests/meta/test_cli.py`: +50行（3テスト）

### Phase 3-5: Documentation (Day 8-10)

**タスク**:
1. ユーザーガイド更新
2. APIリファレンス追加
3. サンプルコード追加

**成果物**:
- `docs/en/guides/meta-agent.md`: +200行（Phase 3セクション）
- `docs/en/api/meta.md`: +150行
- `examples/meta_agent/self_improving_example.py`: 新規

---

## ✅ 成功指標

### 機能
- ✅ エラー自動検出: 100%
- ✅ エラー分析精度: 80%+
- ✅ 自動修正成功率: 60%+（シンプルなエラー）
- ✅ リトライロジック動作: 100%

### 品質
- ✅ 23+ tests全パス（5 + 5 + 10 + 3）
- ✅ Pyright: 0 errors（strict mode）
- ✅ Ruff: All checks passed
- ✅ Coverage: 90%+

### ユーザー体験
- ✅ エラー発生時に自動修正試行
- ✅ 修正プロセスが可視化される
- ✅ `--self-improve` フラグで簡単に有効化

---

## 🔄 Scope Boundary

### ✅ In Scope (Phase 3)

- ErrorAnalyzer実装（LLMベース分析）
- CodeFixer実装（シンプルなパッチ適用）
- SelfImprovingMetaAgent実装（リトライロジック）
- CLI統合（`--self-improve` フラグ）
- 基本テスト（23+ tests）
- ドキュメント（ユーザーガイド + API）

### ❌ Out of Scope (Future)

- **高度なAST操作**: libcst使用（v2.6.0）
- **機械学習ベース修正**: エラーパターン学習（v2.7.0）
- **Sandbox実行**: Docker/VM統合（v2.6.0）
- **テスト自動生成強化**: より詳細なテストケース（v2.6.0）

---

## 📊 Related Issues & RFCs

- **RFC-005**: Meta Agent（全体仕様）
- **Phase 1**: #65, PR #156 ✅
- **Phase 2**: #157, PR #158 ✅
- **Phase 3**: 新規Issue作成予定
- **Dependencies**: CodeExecutor (RFC-017), CodeValidator (Phase 1)

---

## 🚨 Risks & Mitigation

### Risk 1: 自動修正の精度不足
- **Mitigation**: 最大3回までリトライ、それ以上は人間に任せる
- **Fallback**: エラー詳細をユーザーに表示

### Risk 2: 無限ループ
- **Mitigation**: max_retries制限、各リトライでコード変更を確認
- **Fallback**: タイムアウト設定

### Risk 3: 修正が状況を悪化させる
- **Mitigation**: 各修正後にCodeValidator検証
- **Fallback**: 修正が無効なら元のコードを保持

---

## 📅 Implementation Timeline

```
Day 1-2:  ErrorAnalyzer実装（150行 + 5テスト）
Day 3-4:  CodeFixer実装（120行 + 5テスト）
Day 5-6:  SelfImprovingMetaAgent実装（200行 + 10テスト）
Day 7:    CLI統合（+30行 + 3テスト）
Day 8-10: Documentation（+350行）

Total: 10 days (2 weeks)
```

---

## 🎓 Learning & References

### Similar Systems
- **Cursor**: AI-powered code editing with error fixing
- **GitHub Copilot Chat**: Error explanation and fixes
- **Aider**: AI pair programming with automatic fixes

### Error Recovery Patterns
- Retry with exponential backoff
- Graceful degradation
- Fallback strategies

### LLM Code Fixing
- Few-shot prompting for error correction
- Chain-of-thought for complex fixes
- Test-driven fixing

---

## 🎉 Expected Outcome

After Phase 3 completion, Meta Agent will:

1. **Generate agents** from natural language (Phase 1) ✅
2. **Detect code execution needs** automatically (Phase 2) ✅
3. **Fix errors automatically** when they occur (Phase 3) ← NEW!

**Example user experience**:
```bash
$ kagura build agent --chat --self-improve

What should your agent do?
> Analyze sales.csv and calculate average revenue

Generating agent... ✓
Validating code... ⚠️  Found issue: Missing import
Fixing automatically... ✓ Fixed!
Validating again... ✓ All checks passed!

Your agent 'sales_analyzer' is ready!
  - Code execution: Yes
  - Self-improving: Yes
  - Validation: Passed
```

**Impact**: Meta Agent becomes production-ready with automatic error recovery! 🚀

---

## 📚 References

- [RFC_005_META_AGENT.md](./RFC_005_META_AGENT.md)
- [RFC_005_PHASE1_PLAN.md](./RFC_005_PHASE1_PLAN.md)
- [RFC_005_PHASE2_PLAN.md](./RFC_005_PHASE2_PLAN.md)
- [CodeExecutor](../../src/kagura/core/executor.py)
- [CodeValidator](../../src/kagura/meta/validator.py)
