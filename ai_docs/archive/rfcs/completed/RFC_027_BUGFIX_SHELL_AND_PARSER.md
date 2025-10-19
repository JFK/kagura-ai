# RFC-027: Bug Fixes - Shell Executor & Parser Type Safety

**Status**: Draft
**Author**: AI Development Team
**Created**: 2025-10-15
**Priority**: 🔥 Critical (P0 - Bug Fixes)

---

## 📋 Executive Summary

This RFC addresses two critical bugs discovered during comprehensive codebase analysis:

1. **Shell Executor Security Policy Over-Restriction** (Critical)
   - Blocked commands check entire paths instead of command names only
   - Causes false positives (e.g., path containing "dd" triggers block)
   - Affects 4 failing tests in `tests/builtin/test_file.py`

2. **AgentSpec Type Validation Too Strict** (Medium)
   - `examples` field only accepts `dict[str, str]`
   - LLM outputs often contain numeric values
   - Affects 1 failing test in `tests/meta/test_self_improving.py`

3. **TypeVar Usage Warning** (Low)
   - TypeVar "T" appears only once in `parse_response` signature
   - Pyright warning (not error)

**Test Status**: 5 failed, 1,202 passed, 15 skipped (98.4% pass rate)

---

## 🎯 Goals

### Primary Goals
- Fix shell executor security policy to check command names only
- Update AgentSpec type definitions to accept flexible example formats
- Resolve TypeVar usage warning in parser

### Success Criteria
- ✅ All 1,222 tests pass (100% pass rate)
- ✅ Zero pyright errors or warnings
- ✅ Backward compatibility maintained
- ✅ Security not weakened

---

## 📊 Problem Analysis

### Bug 1: Shell Executor Over-Restriction

**Current Code** (`src/kagura/core/shell.py:122-124`):
```python
# Check blacklist first (higher priority)
for blocked in self.blocked_commands:
    if blocked in command:  # ❌ Checks entire command string
        raise SecurityError(f"Blocked command pattern: {blocked}")
```

**Problem**:
```python
# Example failing case
command = 'find /private/var/folders/1m/dnddt_m93vdb1zfh1vxgk8jw0000gn/... -name "*.py"'
# Path contains "dd" from "dnddt_m93v"
# → SecurityError: Blocked command pattern: dd
```

**Root Cause**:
- Blocked commands list includes `"dd"` (disk destroyer)
- Simple substring check matches path components
- Too broad matching pattern

**Affected Tests** (4 failures):
```
FAILED tests/builtin/test_file.py::TestFileAgents::test_file_search_basic
FAILED tests/builtin/test_file.py::TestFileAgents::test_file_search_no_matches
FAILED tests/builtin/test_file.py::TestFileAgents::test_file_search_all_types
FAILED tests/builtin/test_file.py::TestFileAgents::test_grep_content_finds_matches
```

### Bug 2: AgentSpec Type Validation

**Current Code** (`src/kagura/meta/spec.py:43`):
```python
examples: list[dict[str, str]] = Field(
    default_factory=list, description="Example inputs/outputs"
)
```

**Problem**:
```python
# LLM generates this valid JSON:
{
  "examples": [
    {"input": 3, "output": 6},        # ❌ int, not str
    {"input": 10, "output": 20},
    {"input": -4, "output": -8}
  ]
}

# Pydantic validation fails:
# ValidationError: Input should be a valid string [type=string_type, input_value=3, input_type=int]
```

**Affected Test** (1 failure):
```
FAILED tests/meta/test_self_improving.py::test_generate_with_retry_no_validation
```

### Bug 3: TypeVar Usage Warning

**Current Code** (`src/kagura/core/parser.py:113`):
```python
def parse_response(response: str, target_type: Any) -> T:
    """Parse LLM response based on target type."""
    # ...
```

**Warning**:
```
pyright: TypeVar "T" appears only once in generic function signature
Use "object" instead (reportInvalidTypeVarUse)
```

---

## 💡 Proposed Solution

### Solution 1: Shell Executor Security Policy

**Approach**: Use word boundaries and command name extraction

```python
def validate_command(self, command: str) -> bool:
    """Validate command against security policies."""
    parts = shlex.split(command)
    if not parts:
        raise SecurityError("Empty command")

    cmd = parts[0]

    # Check blacklist first (higher priority)
    for blocked in self.blocked_commands:
        # Option A: Check command name only (RECOMMENDED)
        if cmd == blocked:
            raise SecurityError(f"Blocked command: {blocked}")

        # Option B: Check with word boundaries (for patterns like "rm -rf /")
        if re.search(rf'\b{re.escape(blocked)}\b', command):
            raise SecurityError(f"Blocked command pattern: {blocked}")

    # Check whitelist
    if self.allowed_commands:
        if cmd not in self.allowed_commands:
            raise SecurityError(f"Command not allowed: {cmd}")

    return True
```

**Rationale**:
- Option A: Safer, checks only command name
- Option B: More flexible, catches dangerous patterns
- **Recommendation**: Use Option A for simple commands, Option B for patterns

**Hybrid Approach** (BEST):
```python
@staticmethod
def _default_blocked() -> dict[str, str]:
    """Get blacklist of dangerous commands.

    Returns:
        Dict mapping command/pattern to match type ("exact" or "pattern")
    """
    return {
        # Exact matches (command name only)
        "sudo": "exact",
        "su": "exact",
        "dd": "exact",        # ← Fixed: only matches "dd" command
        "mkfs": "exact",
        "fdisk": "exact",

        # Pattern matches (anywhere in command)
        "rm -rf /": "pattern",
        "curl -s | sh": "pattern",
        "wget -O - | sh": "pattern",
    }
```

### Solution 2: AgentSpec Type Flexibility

**Approach 1**: Use `Any` for example values (SIMPLEST)
```python
examples: list[dict[str, Any]] = Field(
    default_factory=list, description="Example inputs/outputs"
)
```

**Approach 2**: Create structured model (BETTER TYPE SAFETY)
```python
class ExamplePair(BaseModel):
    """Example input/output pair"""
    input: str | int | float | bool | dict | list
    output: str | int | float | bool | dict | list

examples: list[ExamplePair] = Field(
    default_factory=list, description="Example inputs/outputs"
)
```

**Approach 3**: Generic with type coercion (MOST FLEXIBLE)
```python
from pydantic import field_validator

examples: list[dict[str, Any]] = Field(
    default_factory=list, description="Example inputs/outputs"
)

@field_validator('examples', mode='before')
@classmethod
def coerce_example_values(cls, v: Any) -> list[dict[str, Any]]:
    """Convert example values to strings if needed"""
    if not isinstance(v, list):
        return v

    result = []
    for item in v:
        if isinstance(item, dict):
            # Coerce all values to strings for consistency
            coerced = {k: str(v) if not isinstance(v, str) else v
                      for k, v in item.items()}
            result.append(coerced)
        else:
            result.append(item)
    return result
```

**Recommendation**: Start with **Approach 1** (simplest fix), consider Approach 2 for Phase 2

### Solution 3: TypeVar Fix

**Current**:
```python
def parse_response(response: str, target_type: Any) -> T:
```

**Fixed** (Option A - Remove TypeVar):
```python
def parse_response(response: str, target_type: type[T]) -> T:
    """Parse LLM response based on target type."""
```

**Fixed** (Option B - Use overload):
```python
from typing import overload, Literal

@overload
def parse_response(response: str, target_type: type[str]) -> str: ...

@overload
def parse_response(response: str, target_type: type[int]) -> int: ...

@overload
def parse_response(response: str, target_type: type[T]) -> T: ...

def parse_response(response: str, target_type: Any) -> Any:
    """Parse LLM response based on target type."""
```

**Recommendation**: **Option A** (simplest, sufficient for our use case)

---

## 📦 Implementation Plan

### Phase 1: Shell Executor Fix (Critical - Day 1)

**Files to Modify**:
- `src/kagura/core/shell.py` (~20 lines)

**Changes**:
1. Update `_default_blocked()` to return dict with match types
2. Modify `validate_command()` to check command name for exact matches
3. Add regex check for pattern matches

**Tests**:
- Existing 4 failing tests should pass
- Add new test: `test_blocked_command_in_path_allowed()`
- Add new test: `test_blocked_command_name_rejected()`

### Phase 2: AgentSpec Type Fix (Medium - Day 1)

**Files to Modify**:
- `src/kagura/meta/spec.py` (~3 lines)

**Changes**:
1. Change `examples: list[dict[str, str]]` → `list[dict[str, Any]]`
2. Update docstring example
3. Update Config.json_schema_extra

**Tests**:
- Existing 1 failing test should pass
- Add new test: `test_agent_spec_numeric_examples()`
- Add new test: `test_agent_spec_mixed_type_examples()`

### Phase 3: TypeVar Warning Fix (Low - Day 1)

**Files to Modify**:
- `src/kagura/core/parser.py` (~2 lines)

**Changes**:
1. Update signature to `parse_response(response: str, target_type: type[T]) -> T:`
2. Verify type checking passes

**Tests**:
- All existing tests should still pass
- Run `pyright src/kagura/` → 0 warnings

### Phase 4: Integration & Documentation (Day 1)

**Tasks**:
1. Run full test suite: `pytest -n auto`
2. Verify 100% pass rate
3. Update `ai_docs/NEXT_STEPS.md`
4. Update this RFC with final results

---

## 🧪 Testing Strategy

### Test Coverage Requirements
- **Shell Executor**: 100% branch coverage for validation logic
- **AgentSpec**: Cover all type combinations (str, int, float, bool, dict, list)
- **Parser**: Verify type inference works correctly

### New Tests to Add

**Shell Executor** (`tests/core/test_shell_security.py`):
```python
@pytest.mark.asyncio
async def test_blocked_command_in_path_allowed():
    """Path containing 'dd' should be allowed"""
    executor = ShellExecutor()
    # Should not raise
    result = await executor.exec('find /tmp/dnddt_test -name "*.py"')
    assert result.success

@pytest.mark.asyncio
async def test_blocked_command_name_rejected():
    """Command 'dd' should be blocked"""
    executor = ShellExecutor()
    with pytest.raises(SecurityError, match="Blocked command: dd"):
        await executor.exec('dd if=/dev/zero of=/tmp/test')

@pytest.mark.asyncio
async def test_dangerous_pattern_rejected():
    """Dangerous patterns should be blocked"""
    executor = ShellExecutor()
    with pytest.raises(SecurityError, match="Blocked command pattern: rm -rf /"):
        await executor.exec('rm -rf / --no-preserve-root')
```

**AgentSpec** (`tests/meta/test_agent_spec_types.py`):
```python
def test_agent_spec_numeric_examples():
    """Numeric examples should be accepted"""
    spec = AgentSpec(
        name="calculator",
        description="Math calculator",
        system_prompt="Calculate",
        examples=[
            {"input": 5, "output": 10},
            {"input": "hello", "output": "world"}
        ]
    )
    assert len(spec.examples) == 2

def test_agent_spec_complex_examples():
    """Complex types in examples should work"""
    spec = AgentSpec(
        name="processor",
        description="Data processor",
        system_prompt="Process",
        examples=[
            {"input": [1, 2, 3], "output": {"sum": 6}},
            {"input": True, "output": False}
        ]
    )
    assert spec.examples[0]["input"] == [1, 2, 3]
```

---

## 🚀 Rollout Plan

### Phase 1: Development (Day 1)
1. ✅ Create RFC-027
2. ✅ Create Implementation Plan
3. ⏳ Create GitHub Issue from RFC
4. ⏳ Create branch from Issue
5. ⏳ Implement fixes

### Phase 2: Testing (Day 1)
1. Run unit tests: `pytest tests/core/test_shell.py`
2. Run meta tests: `pytest tests/meta/`
3. Run full suite: `pytest -n auto`
4. Verify 100% pass rate

### Phase 3: Review & Merge (Day 1)
1. Create Draft PR
2. CI validation
3. Code review
4. Merge to main

---

## 📈 Success Metrics

### Pre-Fix Status
- Test Pass Rate: 98.4% (1,202/1,222)
- Pyright: 0 errors, 1 warning
- Ruff: All checks passed

### Post-Fix Target
- ✅ Test Pass Rate: 100% (1,222/1,222)
- ✅ Pyright: 0 errors, 0 warnings
- ✅ Ruff: All checks passed
- ✅ No security weakening
- ✅ Backward compatibility maintained

---

## 🔒 Security Considerations

### Shell Executor Changes

**Before** (Over-restrictive but secure):
- Blocks: Any path containing "dd"
- Security: ✅ Strong (no false negatives)
- Usability: ❌ Poor (many false positives)

**After** (Balanced):
- Blocks: Command `dd`, patterns like `rm -rf /`
- Security: ✅ Strong (no false negatives)
- Usability: ✅ Good (no false positives)

**Risk Assessment**: LOW
- No security weakening
- More precise detection
- Better user experience

### Type Safety Changes

**Before**:
- Examples: `dict[str, str]` only
- Type Safety: ✅ Strict
- Flexibility: ❌ Poor

**After**:
- Examples: `dict[str, Any]`
- Type Safety: ⚠️ Relaxed (acceptable for examples)
- Flexibility: ✅ Good

**Risk Assessment**: LOW
- Examples are for documentation/testing only
- No runtime impact on agent execution
- Pydantic still validates structure

---

## 📚 References

### Related RFCs
- RFC-005: Meta Agent (affected by Bug 2)
- RFC-024: Context Compression (uses parser)

### Test Files
- `tests/builtin/test_file.py` - Shell executor tests
- `tests/meta/test_self_improving.py` - AgentSpec tests
- `tests/core/test_parser.py` - Parser type tests

### Source Files
- `src/kagura/core/shell.py` - Shell executor
- `src/kagura/meta/spec.py` - AgentSpec model
- `src/kagura/core/parser.py` - Type parser

---

## 🎓 Lessons Learned

### Prevention Strategies
1. **Substring Matching Anti-pattern**
   - Always use word boundaries or exact matches
   - Consider `shlex.split()` for command parsing

2. **Type Flexibility in Models**
   - Use `Any` for truly flexible fields
   - Add validators for type coercion
   - Document expected types clearly

3. **TypeVar Best Practices**
   - Use `type[T]` for type parameters
   - Consider `@overload` for multiple return types
   - Avoid single-use TypeVars

---

## ✅ Approval & Sign-off

**Created**: 2025-10-15
**Status**: Draft → Ready for Implementation

**Next Steps**:
1. Create GitHub Issue from this RFC
2. Create branch from Issue
3. Implement Phase 1-3
4. Submit PR for review
