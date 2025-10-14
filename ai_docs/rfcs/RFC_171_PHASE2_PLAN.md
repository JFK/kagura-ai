# RFC-171 Phase 2: LLM Mocking Expansion Implementation Plan

## 📋 Current Status Analysis (Post-Phase 1)

### Integration Test Statistics
- **Total integration tests**: 42 tests across 6 files
- **Current mock usage**: 23/42 (55%) ← Better than initially thought!
- **Real API calls**: 19/42 (45%)

### Detailed Breakdown

| File | Tests | Mocked | Real API | Mock % |
|------|-------|--------|----------|--------|
| `test_agent_workflow.py` | 4 | ✅ 4 | - | 100% |
| `test_code_execution.py` | 5 | ✅ 5 | - | 100% |
| `test_web_integration.py` | 9 | ✅ 9 | - | **100%** ✨ |
| `test_full_featured.py` | 6 | ✅ 5 | ⚠️ 1 | 83% |
| **`test_multimodal_integration.py`** | **7** | **⚠️ 1** | **❌ 6** | **14%** 🔥 |
| `test_oauth2_integration.py` | 8 | ❌ 0 | ⚠️ 8* | 0% |

**Notes**:
- *OAuth tests are skipped in CI (requires interactive auth)
- **Main bottleneck**: `test_multimodal_integration.py` (6 tests use Gemini API)

---

## 🎯 Phase 2: Focus on Multimodal Tests

### Objectives
1. Mock Gemini API calls in `test_multimodal_integration.py` (6 tests)
2. Fix failing test in `test_full_featured.py` (1 test)
3. Achieve **90%+ mock coverage** (target: 38/42 = 90%)
4. Enable parallel execution for integration tests

### Expected Impact
- **Integration test time**: 3-7 min → 30-60 sec (80-90% reduction)
- **Full test suite time**: 5-10 min → 2-3 min (50-60% reduction)
- **CI/CD time**: Faster feedback loop

---

## 📝 Implementation Steps

### Step 1: Mock Gemini API in `test_multimodal_integration.py`

**Target tests** (6 tests):
1. ❌ `test_multimodal_rag_initialization` - Currently uses real Gemini
2. ❌ `test_multimodal_rag_query` - Calls `build_index()` with Gemini
3. ✅ `test_agent_with_multimodal_rag` - Already mocked!
4. ❌ `test_chat_session_multimodal_initialization` - Gemini init
5. ❌ `test_directory_scanner` - Gemini file scanning
6. ❌ `test_gemini_loader_supported_types` - Gemini loader init
7. ❌ `test_file_type_detection` - No API (pure logic) ← No change needed

**Strategy**:
```python
# Mock GeminiLoader to avoid real API calls
@pytest.fixture
def mock_gemini_loader():
    """Mock Gemini API for multimodal tests"""
    with patch('kagura.loaders.gemini.GeminiLoader') as mock:
        # Mock instance
        instance = MagicMock()
        instance.process_file = AsyncMock(return_value={
            "content": "Mocked content",
            "metadata": {}
        })
        instance.analyze_image = AsyncMock(return_value="Image description")
        instance.transcribe_audio = AsyncMock(return_value="Audio transcript")
        instance.analyze_video = AsyncMock(return_value="Video description")
        instance.analyze_pdf = AsyncMock(return_value="PDF content")
        mock.return_value = instance
        yield mock
```

### Step 2: Fix `test_full_mode_memory_persistence`

**Current issue**: This test is failing (Phase 1 analysis)

**Investigation needed**:
- Check if it's a real failure or test environment issue
- Fix if necessary or skip if environment-specific

### Step 3: Update Integration Test Configuration

**pyproject.toml** (optional):
```toml
[tool.pytest.ini_options]
markers = [
    "integration: Integration tests (deselect with '-m \"not integration\"')",
    "integration_real_api: Integration tests requiring real API (slower)",
    "integration_mocked: Integration tests using mocks (faster)",
]
```

### Step 4: Enable Parallel Execution for Integration Tests

**Test run**:
```bash
# Integration tests with mocks in parallel
pytest -m integration -n auto --tb=short

# Should now complete in <1 minute
```

---

## ✅ Success Criteria

### Performance
- [ ] Integration test time: 3-7 min → <1 min (85%+ reduction)
- [ ] Full test suite time: 5-10 min → 2-3 min (50-60% reduction)
- [ ] Mock coverage: 23/42 (55%) → 38/42 (90%+)

### Quality
- [ ] All 42 integration tests pass with mocks
- [ ] No flaky tests in parallel mode
- [ ] Coverage remains ≥90%

### Configuration
- [ ] Gemini API mocked in multimodal tests
- [ ] Integration tests can run in parallel
- [ ] CI completes in <5 minutes

---

## 📅 Implementation Timeline

### Day 1: Mock Gemini API (3 hours)
- ⏳ Create `mock_gemini_loader` fixture
- ⏳ Update 6 tests in `test_multimodal_integration.py`
- ⏳ Verify tests pass with mocks

### Day 2: Fix & Test (2 hours)
- ⏳ Fix `test_full_mode_memory_persistence`
- ⏳ Run integration tests in parallel
- ⏳ Measure time reduction

### Day 3: Document & PR (1 hour)
- ⏳ Update RFC_171_PHASE2_RESULTS.md
- ⏳ Commit and push
- ⏳ Update PR #185

---

## 🔄 Scope Boundary

### ✅ In Scope (Phase 2)
- Mock Gemini API in multimodal tests
- Fix failing `test_full_mode_memory_persistence`
- Enable parallel execution for integration tests
- Achieve 90%+ mock coverage

### ❌ Out of Scope (Future)
- **OAuth2 tests**: Require interactive auth, already skipped in CI
- **Test hierarchy**: Smoke/unit/integration organization (Phase 3)
- **Advanced optimizations**: Test selection, caching (Phase 3+)

---

## 📊 Related Issues & RFCs
- **Issue**: #171 (Testing: Reduce Test Execution Time)
- **RFC-171 Phase 1**: Parallel Test Execution (PR #185)
- **RFC-022**: Testing Framework (LLMMock implementation)

---

## 🚨 Risks & Mitigation

### Risk 1: Gemini Mock Incomplete
- **Mitigation**: Mock all GeminiLoader methods comprehensively
- **Fallback**: Keep 1-2 tests with real API (mark as `@pytest.mark.slow`)

### Risk 2: Test Behavior Changes
- **Mitigation**: Verify test logic remains the same (only API mocked)
- **Fallback**: Manual testing with real API before major releases

### Risk 3: Mock Drift from Real API
- **Mitigation**: Periodic manual runs with real API
- **Fallback**: Integration test suite for scheduled CI runs (e.g., nightly)

---

## 📚 References
- [RFC-171 Phase 1 Results](./RFC_171_PHASE1_RESULTS.md)
- [RFC-022: Testing Framework](./RFC_022_TESTING_FRAMEWORK.md)
- [Issue #171](https://github.com/kiyotaman/kagura-ai/issues/171)
- [PR #185](https://github.com/kiyotaman/kagura-ai/pull/185)

---

## 🎯 Key Insight

**Main Bottleneck**: `test_multimodal_integration.py`
- Only 1/7 tests mocked (14%)
- 6 tests make real Gemini API calls
- Fixing this file will achieve our 90% mock coverage goal

**Expected Results After Phase 2**:
- Mock coverage: 55% → 90%
- Integration test time: 3-7 min → <1 min
- **Combined with Phase 1**: Total test time 5-10 min → 2-3 min ✨
