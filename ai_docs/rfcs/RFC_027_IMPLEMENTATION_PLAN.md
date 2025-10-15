# RFC-027 Implementation Plan: Bug Fixes - Shell Executor & Parser

**RFC**: [RFC-027](./RFC_027_BUGFIX_SHELL_AND_PARSER.md)
**Priority**: 🔥 Critical (P0)
**Estimated Time**: 3-4 hours (Single Day)

---

## 📋 Overview

This implementation plan covers fixing 3 bugs discovered during codebase analysis:
1. **Shell Executor Over-Restriction** (Critical) - 4 test failures
2. **AgentSpec Type Validation** (Medium) - 1 test failure
3. **TypeVar Usage Warning** (Low) - Pyright warning

**Goal**: Achieve 100% test pass rate (1,222/1,222) with zero warnings.

---

## 🎯 Success Criteria (Output Contract)

### Deliverables
- ✅ Fixed: `src/kagura/core/shell.py`
- ✅ Fixed: `src/kagura/meta/spec.py`
- ✅ Fixed: `src/kagura/core/parser.py`
- ✅ New tests: 6+ tests covering edge cases
- ✅ Test pass rate: 100% (1,222/1,222)
- ✅ Pyright: 0 errors, 0 warnings
- ✅ Documentation updated

### Scope Boundary

**✅ Can Modify**:
```
src/kagura/core/shell.py
src/kagura/meta/spec.py
src/kagura/core/parser.py
tests/core/test_shell.py
tests/meta/test_agent_spec.py
tests/core/test_parser.py
ai_docs/NEXT_STEPS.md
```

**❌ Cannot Modify**:
```
src/kagura_legacy/       # Legacy code
examples/                # User examples (Phase 4 only)
docs/                    # User docs (Phase 4 only)
```

---

## 📅 Implementation Timeline

### Phase 1: Shell Executor Fix (60 min)

#### Step 1.1: Update blocked commands structure (15 min)

**File**: `src/kagura/core/shell.py`

**Current** (lines 82-101):
```python
@staticmethod
def _default_blocked() -> list[str]:
    """Get blacklist of dangerous commands."""
    return [
        "sudo",
        "su",
        "passwd",
        "shutdown",
        "reboot",
        "dd",       # ← Problem: too broad
        "mkfs",
        # ...
    ]
```

**Updated**:
```python
@staticmethod
def _default_blocked() -> dict[str, str]:
    """Get blacklist of dangerous commands.

    Returns:
        Dict mapping command/pattern to match type:
        - "exact": Match command name only (first word)
        - "pattern": Match pattern anywhere in command string
    """
    return {
        # Exact command name matches
        "sudo": "exact",
        "su": "exact",
        "passwd": "exact",
        "shutdown": "exact",
        "reboot": "exact",
        "dd": "exact",          # ← Fixed: only blocks "dd" command
        "mkfs": "exact",
        "fdisk": "exact",
        "parted": "exact",
        "eval": "exact",
        "exec": "exact",
        "source": "exact",

        # Pattern matches (dangerous command sequences)
        "rm -rf /": "pattern",
        "curl -s | sh": "pattern",
        "wget -O - | sh": "pattern",
    }
```

**Type Annotation Update**:
```python
# Update __init__ signature (line 20)
def __init__(
    self,
    allowed_commands: Optional[list[str]] = None,
    blocked_commands: Optional[dict[str, str]] = None,  # ← Changed type
    working_dir: Optional[Path] = None,
    timeout: int = 30,
    require_confirmation: bool = False,
):
```

#### Step 1.2: Update validation logic (20 min)

**File**: `src/kagura/core/shell.py`

**Current** (lines 121-124):
```python
# Check blacklist first (higher priority)
for blocked in self.blocked_commands:
    if blocked in command:  # ← Too broad
        raise SecurityError(f"Blocked command pattern: {blocked}")
```

**Updated**:
```python
import re

# Check blacklist first (higher priority)
for blocked_cmd, match_type in self.blocked_commands.items():
    if match_type == "exact":
        # Check command name only (first word after parsing)
        if cmd == blocked_cmd:
            raise SecurityError(f"Blocked command: {blocked_cmd}")
    elif match_type == "pattern":
        # Check pattern anywhere in command string
        if re.search(rf'\b{re.escape(blocked_cmd)}\b', command):
            raise SecurityError(f"Blocked command pattern: {blocked_cmd}")
```

**Add import** (line 8):
```python
import re
```

#### Step 1.3: Add tests (25 min)

**File**: `tests/core/test_shell.py`

**Add new test class**:
```python
class TestShellExecutorSecurity:
    """Test security policy validation"""

    @pytest.mark.asyncio
    async def test_blocked_command_in_path_allowed(self, tmp_path):
        """Path containing blocked command name should be allowed"""
        # Create path with "dd" in it
        test_dir = tmp_path / "dnddt_test_directory"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("# test")

        executor = ShellExecutor(working_dir=tmp_path)

        # Should not raise SecurityError
        result = await executor.exec(f'find {test_dir} -name "*.py"')
        assert result.success
        assert "test.py" in result.stdout

    @pytest.mark.asyncio
    async def test_blocked_command_name_rejected(self):
        """Command 'dd' itself should be blocked"""
        executor = ShellExecutor()

        with pytest.raises(SecurityError, match="Blocked command: dd"):
            await executor.exec('dd if=/dev/zero of=/tmp/test bs=1M count=1')

    @pytest.mark.asyncio
    async def test_dangerous_pattern_rejected(self):
        """Dangerous patterns should be blocked"""
        executor = ShellExecutor()

        with pytest.raises(SecurityError, match="Blocked command pattern: rm -rf /"):
            await executor.exec('rm -rf / --no-preserve-root')

    @pytest.mark.asyncio
    async def test_eval_command_blocked(self):
        """eval command should be blocked"""
        executor = ShellExecutor()

        with pytest.raises(SecurityError, match="Blocked command: eval"):
            await executor.exec('eval "echo malicious"')

    @pytest.mark.asyncio
    async def test_allowed_command_with_dd_in_args(self):
        """Allowed command with 'dd' in arguments should work"""
        executor = ShellExecutor()

        # 'echo' is allowed, 'dd' appears only in arguments
        result = await executor.exec('echo "added some text"')
        assert result.success
        assert "added some text" in result.stdout
```

**Run tests**:
```bash
pytest tests/core/test_shell.py::TestShellExecutorSecurity -v
pytest tests/builtin/test_file.py -v  # Should now pass
```

---

### Phase 2: AgentSpec Type Fix (30 min)

#### Step 2.1: Update type definition (10 min)

**File**: `src/kagura/meta/spec.py`

**Current** (line 43):
```python
examples: list[dict[str, str]] = Field(
    default_factory=list, description="Example inputs/outputs"
)
```

**Updated**:
```python
from typing import Any

examples: list[dict[str, Any]] = Field(
    default_factory=list,
    description="Example inputs/outputs (values can be any JSON-serializable type)"
)
```

**Update Config example** (lines 50-67):
```python
class Config:
    """Pydantic configuration"""

    json_schema_extra = {
        "example": {
            "name": "translator",
            "description": "Translate English to Japanese",
            "input_type": "str",
            "output_type": "str",
            "tools": [],
            "has_memory": False,
            "requires_code_execution": False,
            "system_prompt": (
                "You are a professional translator. "
                "Translate the given text from English to Japanese."
            ),
            "examples": [
                {"input": "Hello world", "output": "こんにちは世界"},
                {"input": 5, "output": 10},  # ← Add numeric example
                {"input": [1, 2], "output": {"sum": 3}}  # ← Add complex example
            ],
        }
    }
```

#### Step 2.2: Add tests (20 min)

**File**: `tests/meta/test_agent_spec.py` (create if not exists)

```python
"""Tests for AgentSpec model validation"""

import pytest
from kagura.meta.spec import AgentSpec


class TestAgentSpecExamples:
    """Test AgentSpec examples field with various types"""

    def test_string_examples(self):
        """String examples should work"""
        spec = AgentSpec(
            name="translator",
            description="Translate text",
            system_prompt="Translate",
            examples=[
                {"input": "hello", "output": "こんにちは"},
                {"input": "world", "output": "世界"}
            ]
        )
        assert len(spec.examples) == 2
        assert spec.examples[0]["input"] == "hello"

    def test_numeric_examples(self):
        """Numeric examples should be accepted"""
        spec = AgentSpec(
            name="calculator",
            description="Calculate math",
            system_prompt="Calculate",
            examples=[
                {"input": 5, "output": 10},
                {"input": 10, "output": 20},
                {"input": -4, "output": -8}
            ]
        )
        assert len(spec.examples) == 3
        assert spec.examples[0]["input"] == 5
        assert spec.examples[0]["output"] == 10

    def test_mixed_type_examples(self):
        """Mixed type examples should work"""
        spec = AgentSpec(
            name="processor",
            description="Process data",
            system_prompt="Process",
            examples=[
                {"input": "text", "output": 5},
                {"input": 10, "output": "twenty"},
                {"input": True, "output": False}
            ]
        )
        assert len(spec.examples) == 3
        assert isinstance(spec.examples[0]["output"], int)
        assert isinstance(spec.examples[1]["output"], str)

    def test_complex_type_examples(self):
        """Complex types (dict, list) should work"""
        spec = AgentSpec(
            name="aggregator",
            description="Aggregate data",
            system_prompt="Aggregate",
            examples=[
                {"input": [1, 2, 3], "output": {"sum": 6, "avg": 2}},
                {"input": {"a": 1, "b": 2}, "output": [1, 2]}
            ]
        )
        assert len(spec.examples) == 2
        assert spec.examples[0]["input"] == [1, 2, 3]
        assert spec.examples[0]["output"]["sum"] == 6

    def test_empty_examples(self):
        """Empty examples should be valid"""
        spec = AgentSpec(
            name="simple",
            description="Simple agent",
            system_prompt="Do something",
            examples=[]
        )
        assert len(spec.examples) == 0
```

**Run tests**:
```bash
pytest tests/meta/test_agent_spec.py -v
pytest tests/meta/test_self_improving.py::test_generate_with_retry_no_validation -v
```

---

### Phase 3: TypeVar Warning Fix (20 min)

#### Step 3.1: Update function signature (10 min)

**File**: `src/kagura/core/parser.py`

**Current** (line 113):
```python
def parse_response(response: str, target_type: Any) -> T:
    """
    Parse LLM response based on target type.
    # ...
```

**Updated**:
```python
def parse_response(response: str, target_type: type[T]) -> T:
    """
    Parse LLM response based on target type.

    Args:
        response: LLM response text
        target_type: Target return type class

    Returns:
        Parsed value of target type

    Raises:
        ValueError: If parsing fails

    Example:
        >>> parse_response("42", int)
        42
        >>> parse_response('{"name": "test"}', dict)
        {'name': 'test'}
    """
    # Implementation stays the same
```

#### Step 3.2: Verify type checking (10 min)

**Run type checker**:
```bash
pyright src/kagura/core/parser.py
# Expected: 0 errors, 0 warnings

pyright src/kagura/
# Expected: 0 errors, 0 warnings
```

**Run existing tests**:
```bash
pytest tests/core/test_parser.py -v
# All should pass
```

---

### Phase 4: Integration & Validation (30 min)

#### Step 4.1: Run full test suite (15 min)

```bash
# Clean test cache
rm -rf .pytest_cache

# Run all tests in parallel
pytest -n auto --cov=src/kagura --cov-report=term-missing

# Expected results:
# - 1,228 tests passed (1,222 original + 6 new)
# - 0 failed
# - Coverage >= 90%
```

#### Step 4.2: Validate code quality (10 min)

```bash
# Type checking
pyright src/kagura/
# Expected: 0 errors, 0 warnings

# Linting
ruff check src/kagura/
# Expected: All checks passed!

# Formatting
ruff format src/kagura/ --check
# Expected: All files formatted correctly
```

#### Step 4.3: Update documentation (5 min)

**File**: `ai_docs/NEXT_STEPS.md`

**Add entry**:
```markdown
## Recent Changes

### 2025-10-15: Bug Fixes (RFC-027)

**Fixed**:
- ✅ Shell executor security policy over-restriction
- ✅ AgentSpec type validation for numeric examples
- ✅ TypeVar usage warning in parser

**Impact**:
- Test pass rate: 98.4% → 100% (1,222/1,222)
- Pyright warnings: 1 → 0
- New test coverage: +6 tests

**Files Modified**:
- `src/kagura/core/shell.py` - Precise command blocking
- `src/kagura/meta/spec.py` - Flexible example types
- `src/kagura/core/parser.py` - Correct TypeVar usage

**See**: [RFC-027](./rfcs/RFC_027_BUGFIX_SHELL_AND_PARSER.md)
```

---

## 🧪 Testing Checklist

### Pre-Implementation
- [x] Record baseline: 1,202/1,222 tests passing
- [x] Identify failing tests: 5 specific failures
- [x] Understand root causes

### During Implementation
- [ ] Phase 1: Shell executor tests pass (4 failures → 0)
- [ ] Phase 2: AgentSpec tests pass (1 failure → 0)
- [ ] Phase 3: No new pyright warnings
- [ ] New tests added: 6+ tests

### Post-Implementation
- [ ] Full test suite: 100% pass rate
- [ ] Coverage maintained: >= 90%
- [ ] Type checking: 0 errors, 0 warnings
- [ ] Linting: All checks passed
- [ ] No regressions in existing functionality

---

## 🎯 Code Examples

### Example 1: Using Fixed Shell Executor

```python
from kagura.core.shell import ShellExecutor

# Create executor
executor = ShellExecutor()

# ✅ This now works (path contains "dd")
result = await executor.exec('find /tmp/dnddt_test -name "*.py"')
assert result.success

# ❌ This is still blocked (command is "dd")
try:
    await executor.exec('dd if=/dev/zero of=/tmp/file')
except SecurityError:
    print("Correctly blocked dangerous command")

# ❌ Dangerous patterns still blocked
try:
    await executor.exec('rm -rf / --no-preserve-root')
except SecurityError:
    print("Correctly blocked dangerous pattern")
```

### Example 2: Using Fixed AgentSpec

```python
from kagura.meta.spec import AgentSpec

# ✅ Numeric examples now work
spec = AgentSpec(
    name="multiply_by_two",
    description="Multiply number by 2",
    system_prompt="Multiply input by 2",
    examples=[
        {"input": 3, "output": 6},      # int values
        {"input": 10, "output": 20},
        {"input": "5", "output": "10"}  # string values
    ]
)

# ✅ Complex types also work
spec = AgentSpec(
    name="data_processor",
    description="Process data",
    system_prompt="Process",
    examples=[
        {"input": [1, 2, 3], "output": {"sum": 6}},
        {"input": {"x": 1}, "output": [1, 2]}
    ]
)
```

### Example 3: Using Fixed Parser

```python
from kagura.core.parser import parse_response

# No more TypeVar warnings in IDE/type checker
result = parse_response("42", int)
assert result == 42
assert isinstance(result, int)

# Type inference works correctly
text = parse_response("hello", str)
assert isinstance(text, str)

from pydantic import BaseModel
class User(BaseModel):
    name: str
    age: int

user = parse_response('{"name": "Alice", "age": 30}', User)
assert isinstance(user, User)
```

---

## 📊 Verification Criteria

### Must Pass
- ✅ `pytest tests/builtin/test_file.py` - All 4 tests pass
- ✅ `pytest tests/meta/test_self_improving.py` - All tests pass
- ✅ `pytest -n auto` - 100% pass rate (1,228+/1,228+)
- ✅ `pyright src/kagura/` - 0 errors, 0 warnings
- ✅ `ruff check src/kagura/` - All checks passed

### Should Pass
- ✅ Coverage >= 90%
- ✅ No performance degradation
- ✅ Backward compatibility maintained
- ✅ Security not weakened

---

## 🚀 Rollout Steps

### Step 1: Create Issue
```bash
gh issue create \
  --title "RFC-027: Fix Shell Executor & Parser Type Bugs" \
  --body "$(cat <<'EOF'
## Summary
Fix 3 bugs causing 5 test failures:
1. Shell executor over-restriction (4 failures)
2. AgentSpec type validation (1 failure)
3. TypeVar usage warning

## Links
- RFC: [RFC-027](../ai_docs/rfcs/RFC_027_BUGFIX_SHELL_AND_PARSER.md)
- Plan: [Implementation Plan](../ai_docs/rfcs/RFC_027_IMPLEMENTATION_PLAN.md)

## Success Criteria
- ✅ 100% test pass rate (1,228+/1,228+)
- ✅ 0 pyright warnings
- ✅ No security weakening
EOF
)"
```

### Step 2: Create Branch from Issue
```bash
# Get issue number (e.g., 200)
ISSUE_NUM=$(gh issue list --limit 1 --json number --jq '.[0].number')

# Create branch from issue
gh issue develop $ISSUE_NUM --checkout
# Example branch: 200-rfc-027-fix-shell-executor-parser-type-bugs
```

### Step 3: Implement & Test
```bash
# Implement Phase 1-3 (see timeline above)

# Run tests after each phase
pytest tests/core/test_shell.py -v
pytest tests/meta/test_agent_spec.py -v
pytest tests/core/test_parser.py -v

# Final validation
pytest -n auto
pyright src/kagura/
ruff check src/kagura/
```

### Step 4: Commit & Push
```bash
git add .
git commit -m "$(cat <<'EOF'
fix(core,meta): resolve shell security and type validation bugs (#200)

- Shell executor: Use precise command-name matching instead of substring
- AgentSpec: Accept Any type for example values (not just str)
- Parser: Fix TypeVar usage warning

Fixes 5 test failures, achieves 100% pass rate.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push
```

### Step 5: Create PR
```bash
gh pr create --draft \
  --title "fix(core,meta): resolve shell security and type validation bugs (#200)" \
  --body "$(cat <<'EOF'
## Summary
Fixes 3 bugs causing 5 test failures in shell executor and parser.

## Changes
- `src/kagura/core/shell.py`: Precise command-name matching
- `src/kagura/meta/spec.py`: Flexible example types (Any)
- `src/kagura/core/parser.py`: Fixed TypeVar usage
- Tests: +6 new security & type validation tests

## Test Results
```bash
pytest -n auto
# 1,228 passed, 0 failed (was 1,202 passed, 5 failed)

pyright src/kagura/
# 0 errors, 0 warnings (was 1 warning)
```

## Related
Closes #200

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### Step 6: CI & Review
```bash
# Wait for CI to pass
gh pr checks

# Mark as ready when green
gh pr ready $ISSUE_NUM

# Merge when approved
gh pr merge $ISSUE_NUM --squash
```

---

## 📚 Resources

### Related Files
- RFC: [RFC-027](./RFC_027_BUGFIX_SHELL_AND_PARSER.md)
- Source: `src/kagura/core/shell.py`
- Source: `src/kagura/meta/spec.py`
- Source: `src/kagura/core/parser.py`
- Tests: `tests/builtin/test_file.py`
- Tests: `tests/meta/test_self_improving.py`

### External References
- [Python shlex](https://docs.python.org/3/library/shlex.html)
- [Pydantic Field Types](https://docs.pydantic.dev/latest/concepts/types/)
- [Python TypeVar](https://docs.python.org/3/library/typing.html#typing.TypeVar)

---

**Ready to implement!** 🚀
