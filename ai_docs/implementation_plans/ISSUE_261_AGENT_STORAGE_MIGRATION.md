# Issue #261 Implementation Plan: Migrate Agent Storage to ~/.kagura/agents/

**Issue**: #261
**Type**: Refactoring, Enhancement
**Priority**: ⭐️⭐️ Medium
**Estimated Duration**: 1 day
**Target Version**: v2.5.11 or v2.6.0

---

## Summary

Migrate custom agent storage from project-level `./agents/` to user-level `~/.kagura/agents/` for better organization and cross-project sharing.

**Key Decision**: **No backward compatibility** - completely remove `./agents/` loading.

---

## Background

### Current Situation

**Built-in Agents** (framework-provided):
```
src/kagura/agents/
├── __init__.py
├── code_agent.py        # CodeExecutionAgent (built-in)
└── (future built-ins)
```

**Custom Agents** (user-generated):
```
./agents/                # ← Current location (project-level)
├── README.md
└── (user-generated agents via MetaAgent)
```

### Problems

1. **Project clutter**: Each project needs `./agents/` directory
2. **No sharing**: Agents not reusable across projects
3. **Inconsistent documentation**: References deleted commands (`kagura build`, `kagura repl`)
4. **Unclear separation**: Built-in vs custom agents confusion

---

## Proposed Architecture

### Clear Separation

```
# Built-in Agents (framework, in package)
src/kagura/agents/
├── __init__.py
├── code_agent.py        # CodeExecutionAgent
└── (future built-ins)   # Available via API import

# Custom Agents (user-generated, user-level)
~/.kagura/agents/
├── translator.py
├── youtube_summarizer.py
└── (user-created agents via MetaAgent)
```

**Differences**:
| Type | Location | Purpose | Import |
|------|----------|---------|--------|
| Built-in | `src/kagura/agents/` | Framework features | `from kagura.agents import CodeExecutionAgent` |
| Custom | `~/.kagura/agents/` | User-created agents | Loaded dynamically in chat |

---

## Implementation Plan

### Phase 1: Update Agent Loading (Core Changes)

#### 1.1 Update `src/kagura/chat/session.py`

**Current** (Line 752-813):
```python
def _load_custom_agents(self) -> None:
    """Load custom agents from ./agents directory."""
    agents_dir = Path.cwd() / "agents"  # ← Project-level

    if not agents_dir.exists() or not agents_dir.is_dir():
        return
    # ...
```

**New**:
```python
def _load_custom_agents(self) -> None:
    """Load custom agents from ~/.kagura/agents/"""
    agents_dir = Path.home() / ".kagura" / "agents"  # ← User-level

    # Create directory if not exists
    agents_dir.mkdir(parents=True, exist_ok=True)

    if not agents_dir.is_dir():
        return
    # ... (rest of loading logic unchanged)
```

**Changes**:
- ✅ Change path from `Path.cwd() / "agents"` to `Path.home() / ".kagura" / "agents"`
- ✅ Add `mkdir(parents=True, exist_ok=True)` to auto-create directory
- ❌ Remove `./agents/` fallback (no backward compatibility)

**Updated help message** (Line 1189-1193):
```python
if not self.custom_agents:
    self.console.print(
        "[yellow]No custom agents available.[/]\n"
        "[dim]Custom agents are stored in ~/.kagura/agents/[/]\n"
        "[dim]Create agents using natural language in chat.[/]"
    )
    return
```

---

#### 1.2 Update `src/kagura/meta/meta_agent.py`

**Current** (Line 98-122):
```python
async def generate_and_save(
    self, description: str, output_path: Path
) -> tuple[str, Path]:
    """Generate agent code and save to file

    Args:
        description: Natural language agent description
        output_path: Output file path  # ← Required parameter
    """
    code = await self.generate(description)
    self.generator.save(code, output_path)
    return code, output_path
```

**New**:
```python
async def generate_and_save(
    self,
    description: str,
    output_path: Path | None = None  # ← Optional
) -> tuple[str, Path]:
    """Generate agent code and save to file

    Args:
        description: Natural language agent description
        output_path: Output file path (default: ~/.kagura/agents/<name>.py)

    Returns:
        Tuple of (generated_code, output_path)

    Example:
        >>> # Default location
        >>> code, path = await meta.generate_and_save(
        ...     "Create a translator agent"
        ... )
        >>> print(path)  # ~/.kagura/agents/translator.py

        >>> # Custom location
        >>> code, path = await meta.generate_and_save(
        ...     "Create a translator agent",
        ...     Path("/custom/path/translator.py")
        ... )
    """
    # Parse description to get agent name
    spec = await self.parser.parse(description)

    # Default to ~/.kagura/agents/<name>.py
    if output_path is None:
        agents_dir = Path.home() / ".kagura" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        output_path = agents_dir / f"{spec.name}.py"

    code = await self.generate(description)
    self.generator.save(code, output_path)
    return code, output_path
```

**Changes**:
- ✅ Make `output_path` optional (default: `None`)
- ✅ Auto-generate path as `~/.kagura/agents/{agent_name}.py`
- ✅ Auto-create `~/.kagura/agents/` directory
- ✅ Use `spec.name` from parsed description for filename

---

#### 1.3 Check `src/kagura/meta/generator.py`

**Verify**: Does `generator.save()` need changes?

```bash
# Read generator.py to check save() implementation
```

**Expected**: Should work as-is (just receives path from `meta_agent.py`)

---

### Phase 2: Documentation Updates

#### 2.1 Remove `agents/README.md`

**Action**: Delete `./agents/README.md` (project root)

**Reason**:
- Custom agents no longer stored in project
- References deleted commands (`kagura build agent`)
- No longer needed

#### 2.2 Update Session Help Text

**File**: `src/kagura/chat/session.py`

**Locations to update**:
1. Line 1191-1193 (already shown in 1.1)
2. Welcome message (if mentions agent location)
3. Help command output (if mentions agent location)

---

### Phase 3: Tests

#### 3.1 Update Test Files

**Files to check**:
```bash
tests/chat/test_session.py       # Agent loading tests
tests/meta/test_meta_agent.py    # Save path tests
tests/meta/test_generator.py     # Save function tests
```

**Changes**:
- ✅ Update expected paths to `~/.kagura/agents/`
- ✅ Use temporary directory for tests (avoid polluting `~/.kagura/`)
- ✅ Test auto-creation of `~/.kagura/agents/`
- ✅ Remove tests for `./agents/` loading (no longer supported)

**Example Test**:
```python
import tempfile
from pathlib import Path
from unittest.mock import patch

@pytest.mark.asyncio
async def test_meta_agent_default_save_path(monkeypatch):
    """Test MetaAgent saves to ~/.kagura/agents/ by default"""
    # Use temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir)
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        meta = MetaAgent()
        code, path = await meta.generate_and_save("Create a translator")

        # Check path is ~/.kagura/agents/<name>.py
        assert path == fake_home / ".kagura" / "agents" / "translator.py"
        assert path.exists()
        assert path.read_text() == code

@pytest.mark.asyncio
async def test_session_loads_from_user_agents_dir(monkeypatch):
    """Test ChatSession loads agents from ~/.kagura/agents/"""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir)
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create a test agent
        agents_dir = fake_home / ".kagura" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "test_agent.py").write_text("""
from kagura import agent

@agent
async def test_agent(input: str) -> str:
    '''Test agent'''
    return f"Processed: {input}"
""")

        # Load session
        session = ChatSession()

        # Check agent loaded
        assert "test_agent" in session.custom_agents
```

---

### Phase 4: Documentation

#### 4.1 Update User Docs

**Files**:
- `docs/en/guides/meta-agent.md` - Update agent storage location
- `docs/en/api/meta.md` - Update `generate_and_save()` signature
- `docs/en/guides/chat.md` - Update custom agent loading info

**Changes**:
- ✅ Replace `./agents/` with `~/.kagura/agents/`
- ✅ Update examples to use new default behavior
- ✅ Add section on agent storage location

#### 4.2 Update AI Docs (Developer)

**Files**:
- `ai_docs/NEXT_STEPS.md` - Add completion note
- `ai_docs/work_logs/2025-10-17_issue_261.md` - Create work log

---

## File Changes Summary

### Modified Files

| File | Changes | Lines |
|------|---------|-------|
| `src/kagura/chat/session.py` | Update agent loading path | ~752-813, 1191-1193 |
| `src/kagura/meta/meta_agent.py` | Add default save path logic | ~98-122 |
| `src/kagura/meta/generator.py` | (Verify only, likely no change) | - |
| `tests/chat/test_session.py` | Update test paths | TBD |
| `tests/meta/test_meta_agent.py` | Update test paths | TBD |
| `docs/en/guides/meta-agent.md` | Update documentation | TBD |
| `docs/en/api/meta.md` | Update API docs | TBD |

### Deleted Files

| File | Reason |
|------|--------|
| `agents/README.md` | No longer needed (agents not in project) |

### New Behavior

| Feature | Old | New |
|---------|-----|-----|
| Custom agent loading | `./agents/` | `~/.kagura/agents/` |
| MetaAgent default save | (required path) | `~/.kagura/agents/<name>.py` |
| Directory creation | Manual | Auto-created |
| Backward compatibility | N/A | ❌ None (breaking change) |

---

## Migration Guide for Users

### Manual Migration (if user has existing ./agents/)

```bash
# If user has agents in ./agents/, they need to manually migrate:

# Create target directory
mkdir -p ~/.kagura/agents

# Copy agents
cp ./agents/*.py ~/.kagura/agents/

# Delete old directory (optional)
rm -rf ./agents
```

**Note**: This is a **breaking change** - users with existing `./agents/` will need to manually migrate.

---

## Testing Checklist

### Unit Tests
- [ ] `test_session_loads_from_user_agents_dir` - Load from `~/.kagura/agents/`
- [ ] `test_session_creates_agents_dir` - Auto-create directory
- [ ] `test_meta_agent_default_save_path` - Default to `~/.kagura/agents/<name>.py`
- [ ] `test_meta_agent_custom_save_path` - Support custom paths
- [ ] `test_generator_save` - Verify save function works

### Integration Tests
- [ ] Create agent via chat → saved to `~/.kagura/agents/`
- [ ] Restart chat → agent loaded automatically
- [ ] Multiple agents → all loaded correctly
- [ ] Agent name extraction → correct filename

### Manual Tests
- [ ] `kagura chat` → create agent → check `~/.kagura/agents/`
- [ ] Restart chat → agent appears in `/agent` list
- [ ] `/agent <name> <input>` → executes correctly

---

## Risks & Mitigations

### Risk 1: Breaking Change for Existing Users
**Impact**: High (existing `./agents/` will stop working)
**Probability**: High (intentional)
**Mitigation**:
- ✅ Clear migration guide in release notes
- ✅ Update documentation prominently
- ✅ Consider version bump to v2.6.0 (minor version)

### Risk 2: Agent Name Extraction Failure
**Impact**: Medium (cannot generate filename)
**Probability**: Low (parser is robust)
**Mitigation**:
- ✅ Add fallback: if `spec.name` is invalid, use timestamp
- ✅ Validate filename (remove invalid characters)

### Risk 3: Permission Issues on ~/.kagura/
**Impact**: Low (rare)
**Probability**: Very Low
**Mitigation**:
- ✅ Use `exist_ok=True` in `mkdir()`
- ✅ Add try-except for permission errors
- ✅ Show helpful error message

---

## Success Criteria

- [ ] Custom agents load from `~/.kagura/agents/` only
- [ ] MetaAgent saves to `~/.kagura/agents/<name>.py` by default
- [ ] `~/.kagura/agents/` auto-created if missing
- [ ] `./agents/` loading completely removed (no backward compat)
- [ ] `agents/README.md` deleted
- [ ] All tests pass with new paths
- [ ] Documentation updated
- [ ] No references to `./agents/` in codebase

---

## Timeline

**Total Duration**: 1 day

### Morning (4 hours)
- ✅ Update `session.py` (1h)
- ✅ Update `meta_agent.py` (1h)
- ✅ Update tests (2h)

### Afternoon (4 hours)
- ✅ Run all tests (1h)
- ✅ Update documentation (2h)
- ✅ Manual testing (1h)

---

## Related Issues & RFCs

- #249 - CLI simplification (deleted `kagura build`, `kagura repl`)
- #258 - Centralized env var management (similar pattern)
- RFC-033 - Chat Enhancement (agent management)

---

## Notes

- **No backward compatibility**: This is a clean break from `./agents/`
- **Breaking change**: Consider bumping to v2.6.0
- **User migration**: Provide clear instructions in release notes
- **Future**: Built-in agents (`src/kagura/agents/`) can be expanded separately
