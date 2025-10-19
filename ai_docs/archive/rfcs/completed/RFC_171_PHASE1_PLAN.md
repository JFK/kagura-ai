# RFC-171 Phase 1: Parallel Test Execution Implementation Plan

## 📋 Current Status Analysis

### Test Suite Statistics
- **Total tests**: 1,207 tests
- **Test files**: 90+ files
- **Total test code**: ~21,500 lines
- **Integration tests**: 42 tests (in `tests/integration/`)
- **Legacy tests**: Excluded via `norecursedirs` in pyproject.toml

### Current Bottlenecks
1. **Sequential Execution**: All tests run sequentially
2. **Integration Tests**: 42 integration tests making real LLM API calls (3-7 minutes)
3. **Limited Mock Usage**: Only 2/6 integration test files use mocks (33%)
   - ✅ `test_agent_workflow.py` - Uses `mock_llm_response`
   - ✅ `test_code_execution.py` - Uses `mock_llm_response`
   - ❌ `test_multimodal_integration.py` - Real API calls
   - ❌ `test_oauth2_integration.py` - Real API calls
   - ❌ `test_web_integration.py` - Real API calls
   - ❌ `test_full_featured.py` - Real API calls

### RFC-022 LLMMock Status
- ✅ **Implemented**: `kagura.testing.mocking.LLMMock`
- ✅ **Available fixtures**: `mock_llm_response` in `tests/integration/conftest.py`
- ⚠️ **Usage rate**: 33% (2/6 files) - **Target: 80%+**

---

## 🎯 Phase 1: Parallel Test Execution

### Objectives
1. Implement `pytest-xdist` for parallel execution
2. Configure optimal worker count
3. Handle shared resources (DB, files)
4. Ensure test isolation

### Expected Impact
- **Time reduction**: 5-10 min → 2-3 min (50-60% reduction)
- **CI/CD improvement**: Faster feedback loop
- **Developer experience**: Reduced wait time

---

## 📝 Implementation Steps

### Step 1: Install pytest-xdist
```bash
# Add to pyproject.toml dev dependencies
pytest-xdist>=3.5
```

### Step 2: Configure pytest for Parallel Execution
```toml
# pyproject.toml [tool.pytest.ini_options]
addopts = [
    "-n", "auto",  # Use all available CPU cores
    "--dist", "loadgroup",  # Distribute by test groups
]
```

### Step 3: Mark Tests for Grouping
```python
# tests/integration/conftest.py
@pytest.fixture(scope="session")
def worker_id(request):
    """Get pytest-xdist worker ID."""
    return getattr(request.config, "workerinput", {}).get("workerid", "master")

# Add loadgroup markers for shared resources
pytestmark = pytest.mark.xdist_group(name="llm_api")
```

### Step 4: Handle Shared Resources
1. **File system**: Use worker-specific temp directories
2. **Database**: Use worker-specific DB instances (if applicable)
3. **LLM API rate limits**: Group LLM tests together

### Step 5: Test Isolation Validation
```bash
# Run tests multiple times to ensure no race conditions
pytest -n 4 --count=3
```

---

## ✅ Success Criteria

### Performance
- [ ] Total test time: 5-10 min → 2-3 min (60% reduction)
- [ ] CI/CD time: <5 minutes
- [ ] No test failures due to parallelization

### Quality
- [ ] All 1,207 tests pass in parallel mode
- [ ] No flaky tests (run 10 times successfully)
- [ ] Coverage remains ≥90%

### Configuration
- [ ] `pytest-xdist` added to `pyproject.toml`
- [ ] Parallel execution enabled by default
- [ ] Sequential mode available via `pytest -n 0`

---

## 📅 Implementation Timeline

### Day 1: Setup & Configuration (2 hours)
- ✅ Analyze current test structure
- ✅ Create implementation plan
- ⏳ Install pytest-xdist
- ⏳ Configure pyproject.toml
- ⏳ Create GitHub branch from Issue #171

### Day 2: Implementation & Testing (3 hours)
- ⏳ Add worker-specific fixtures
- ⏳ Handle shared resources
- ⏳ Test parallel execution
- ⏳ Fix any race conditions

### Day 3: Validation & Documentation (2 hours)
- ⏳ Run full test suite 10 times
- ⏳ Measure time reduction
- ⏳ Update documentation
- ⏳ Create PR

---

## 🔄 Scope Boundary

### ✅ In Scope (Phase 1)
- Install and configure pytest-xdist
- Enable parallel test execution
- Handle shared resources
- Validate test isolation

### ❌ Out of Scope (Future Phases)
- **Phase 2**: Expand LLMMock usage (33% → 80%)
- **Phase 3**: Test hierarchy (smoke/unit/integration)
- **Phase 4**: Advanced optimizations (test selection, caching)

---

## 📊 Related Issues & RFCs
- **Issue**: #171 (Testing: Reduce Test Execution Time)
- **RFC-022**: Testing Framework (LLMMock implementation)
- **Dependencies**: None

---

## 🚨 Risks & Mitigation

### Risk 1: Flaky Tests
- **Mitigation**: Run tests 10 times before merging
- **Fallback**: Mark flaky tests with `@pytest.mark.serial`

### Risk 2: Shared Resource Conflicts
- **Mitigation**: Worker-specific temp directories
- **Fallback**: Use `xdist_group` for resource-heavy tests

### Risk 3: Performance Not Improved
- **Mitigation**: Profile tests to find bottlenecks
- **Fallback**: Combine with Phase 2 (LLM mocking)

---

## 📚 References
- [pytest-xdist Documentation](https://pytest-xdist.readthedocs.io/)
- [RFC-022: Testing Framework](./RFC_022_TESTING_FRAMEWORK.md)
- [Issue #171](https://github.com/kiyotaman/kagura-ai/issues/171)
