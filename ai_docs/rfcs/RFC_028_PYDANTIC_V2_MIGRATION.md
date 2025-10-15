# RFC-028: Pydantic v2 Config Migration

**Status**: Draft
**Author**: AI Development Team
**Created**: 2025-10-15
**Priority**: Medium (Code Quality)
**Target Version**: v2.5.2

---

## 📋 Executive Summary

Pydantic v2では、`class Config`が非推奨となり、`ConfigDict`への移行が推奨されています。
現在Kagura AIでは3ファイルで古い形式を使用しており、テスト実行時に12件の警告が出ています。

v2.5.2でこれらを一括で移行し、コード品質とメンテナビリティを向上させます。

---

## 🎯 Goals

### Primary Goals
- Pydantic v2の推奨形式(`ConfigDict`)への移行
- 全警告の解消（12 warnings → 0）
- Pydantic v3への将来的な互換性確保

### Success Criteria
- ✅ 全`class Config`を`model_config = ConfigDict()`に移行
- ✅ テスト実行時の警告0件
- ✅ 全テスト100%パス維持
- ✅ 後方互換性維持

---

## 📊 Problem Analysis

### Current State

**警告メッセージ**:
```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated, 
use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0.
```

**影響ファイル** (3files):
1. `src/kagura/meta/spec.py` - AgentSpec
2. `src/kagura/builder/config.py` - Builder config classes
3. `src/kagura/auth/config.py` - Auth config classes

**警告数**: 12 warnings（テスト実行時）

---

## 💡 Proposed Solution

### Migration Pattern

**Before** (class-based Config):
```python
from pydantic import BaseModel

class AgentSpec(BaseModel):
    name: str
    
    class Config:
        json_schema_extra = {"example": {"name": "translator"}}
```

**After** (ConfigDict):
```python
from pydantic import BaseModel, ConfigDict

class AgentSpec(BaseModel):
    name: str
    
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "translator"}}
    )
```

### File-by-File Migration

#### 1. src/kagura/meta/spec.py

**Current**:
```python
class AgentSpec(BaseModel):
    # ...fields...
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "translator",
                # ...
            }
        }
```

**Migrated**:
```python
from pydantic import ConfigDict

class AgentSpec(BaseModel):
    # ...fields...
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "translator",
                # ...
            }
        }
    )
```

#### 2. src/kagura/builder/config.py

**Current**:
```python
class MemoryConfig(BaseModel):
    # ...fields...
    
    class Config:
        arbitrary_types_allowed = True
```

**Migrated**:
```python
from pydantic import ConfigDict

class MemoryConfig(BaseModel):
    # ...fields...
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

#### 3. src/kagura/auth/config.py

**Current**:
```python
class AuthConfig(BaseModel):
    # ...fields...
    
    class Config:
        validate_assignment = True
```

**Migrated**:
```python
from pydantic import ConfigDict

class AuthConfig(BaseModel):
    # ...fields...
    
    model_config = ConfigDict(validate_assignment=True)
```

---

## 📦 Implementation Plan

### Phase 1: Migration (30 min)

**Changes**:
1. `src/kagura/meta/spec.py` (~5 lines)
2. `src/kagura/builder/config.py` (~10 lines)
3. `src/kagura/auth/config.py` (~5 lines)

**Total**: ~20 lines changed across 3 files

### Phase 2: Validation (15 min)

**Tests**:
```bash
# Run tests - should have 0 warnings
pytest -n auto

# Type checking
pyright src/kagura/

# Linting
ruff check src/kagura/
```

### Phase 3: Documentation (15 min)

**Update**:
- `CHANGELOG.md`: Add v2.5.2 entry
- `ai_docs/UNIFIED_ROADMAP.md`: Add v2.5.2 completion

---

## 🧪 Testing Strategy

### Backward Compatibility

**Critical**: Ensure no breaking changes
- All existing tests must pass
- API surface unchanged
- User code unaffected

### Test Plan

```bash
# 1. Run full test suite
pytest -n auto --tb=short

# Expected: 1,213 passed, 0 warnings

# 2. Run specific model tests
pytest tests/meta/test_self_improving.py -v
pytest tests/builder/test_agent_builder.py -v
pytest tests/auth/test_config.py -v

# 3. Type checking
pyright src/kagura/

# 4. Linting
ruff check src/kagura/
```

---

## 🚀 Rollout Plan

### Step 1: Create Issue & Branch

```bash
# Create Issue
gh issue create --title "RFC-028: Pydantic v2 Config Migration" \
  --body "Migrate class Config → ConfigDict. See RFC-028."

# Create branch from Issue
gh issue develop [ISSUE_NUM] --checkout
```

### Step 2: Implement Migration

```bash
# Edit 3 files with ConfigDict migration
# Commit with conventional commit message
git add src/kagura/meta/spec.py src/kagura/builder/config.py src/kagura/auth/config.py
git commit -m "refactor(models): migrate to Pydantic v2 ConfigDict (#XXX)

- Replace class Config with model_config = ConfigDict()
- Resolves 12 deprecation warnings
- Maintains backward compatibility

Closes #XXX"
```

### Step 3: Create PR & Merge

```bash
# Push & create PR
git push
gh pr create --draft --title "refactor(models): migrate to Pydantic v2 ConfigDict (#XXX)"

# Wait for CI
gh pr checks

# Ready & merge
gh pr ready [PR_NUM]
gh pr merge [PR_NUM] --squash
```

### Step 4: Release v2.5.2

```bash
# Update version
# Edit pyproject.toml: version = "2.5.2"
# Update CHANGELOG.md

git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v2.5.2"
git push

# Create release
git tag v2.5.2
git push --tags
gh release create v2.5.2 --title "v2.5.2 - Code Quality" \
  --notes "Pydantic v2 Config migration. See CHANGELOG.md"
```

---

## 📈 Success Metrics

### Pre-Migration
- Warnings: 12
- Test Pass: 1,213/1,213 (100%)

### Post-Migration Target
- ✅ Warnings: 0
- ✅ Test Pass: 1,213/1,213 (100%)
- ✅ Pyright: 0 errors, 0 warnings
- ✅ Ruff: All checks passed

---

## 🔒 Risk Assessment

**Risk Level**: **LOW**

**Rationale**:
- Small, focused change (3 files, ~20 lines)
- No API changes
- Well-documented migration path
- Backward compatible

**Mitigation**:
- Full test suite validation
- Type checking with pyright
- Code review before merge

---

## 📚 References

### Pydantic Documentation
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [ConfigDict Reference](https://docs.pydantic.dev/latest/api/config/)

### Project Files
- `src/kagura/meta/spec.py`
- `src/kagura/builder/config.py`
- `src/kagura/auth/config.py`

---

## ✅ Approval & Sign-off

**Created**: 2025-10-15
**Status**: Draft → Ready for Implementation

**Estimated Time**: 1 hour
**Target Release**: v2.5.2 (2025-10-15)
