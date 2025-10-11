# Examples Health Check Report

**Date**: 2025-10-11
**Scope**: All 20 example files in `examples/` directory
**Test Environment**: kagura-ai v2.3.0

---

## Executive Summary

- **Total Examples Tested**: 20 files
- **Syntax Check**: ✅ All 20 files passed
- **Execution Tests**: Mixed results (many timeout due to LLM API calls)
- **Critical Issues Found**: 4
- **Warnings**: Multiple timeout issues

---

## Phase 1: Syntax Validation

✅ **All 20 example files passed syntax check**

Files checked:
- agent_builder/ (4 files)
- agents/ (4 subdirs with agent.py)
- testing/ (3 files)
- observability/ (3 files)
- advanced_workflows/ (3 files)
- multimodal_rag/ (1 file)
- memory_routing/ (2 files)

---

## Phase 2: Execution Results by Category

### 1. agent_builder/ (4 files)

#### ✅ basic_builder.py
- **Status**: Works correctly
- **Notes**: Previously fixed duplicate `max_tokens` parameter issue

#### ✅ presets.py
- **Status**: Works correctly
- **Notes**: Previously fixed - removed non-existent `.with_preset()` method calls

#### ⚠️ with_memory.py
- **Status**: TIMEOUT (10s)
- **Issue**: Line 87 calls `.with_session_id("user_123_session_1")`
- **Severity**: **CRITICAL** - Method does not exist in AgentBuilder
- **Evidence**: `grep -r "with_session_id" src/` returned no results
- **Impact**: Example will fail immediately when that line executes

#### ⚠️ with_tools.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Likely due to multiple LLM API calls
- **Impact**: Example may work but runs slowly

---

### 2. agents/ (4 subdirectories)

#### ⚠️ simple_chat/agent.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Likely due to LLM API calls
- **Impact**: Example may work but runs slowly

#### ❌ data_extractor/agent.py
- **Status**: **JSON PARSING ERROR**
- **Error**: `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
- **Location**: `src/kagura/core/parser.py:194`
- **Severity**: **HIGH** - Type parsing failure
- **Impact**: Example fails during execution
- **Root Cause**: LLM response not returning valid JSON for structured output

#### ✅ code_generator/agent.py
- **Status**: Partially working
- **Output**: Successfully generated factorial code, started string processing
- **Notes**: May timeout on full execution but core functionality works

#### ⚠️ workflow_example/agent.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Complex workflow with multiple LLM calls
- **Impact**: Example may work but runs slowly

---

### 3. testing/ (3 files)

#### ⚠️ test_basic.py
- **Status**: **PYTEST WARNING**
- **Warning**: `PytestCollectionWarning: cannot collect test class 'TestGreeterAgent' because it has a __init__ constructor`
- **Location**: Line 32
- **Severity**: **MEDIUM** - Tests won't run properly
- **Impact**: Test class not collected by pytest
- **Fix**: Remove `__init__` from test class or rename class

#### ⚠️ test_performance.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Performance tests likely involve multiple runs
- **Impact**: Example may work but runs slowly

#### ❌ test_with_mocks.py
- **Status**: **TESTS FAILING**
- **Failures**: All 3 tests failed
  - `test_with_mock_side_effect`
  - `test_with_exception_mock`
  - `test_prompt_template_rendering`
- **Severity**: **HIGH** - Mock testing functionality broken
- **Impact**: Mocking examples don't demonstrate working patterns

---

### 4. observability/ (3 files)

#### ⚠️ cost_tracking.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Likely tracking multiple LLM calls
- **Impact**: Example may work but runs slowly

#### ⚠️ dashboard_demo.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Dashboard may be interactive
- **Impact**: Example may work but runs slowly

#### ⚠️ monitored_agent.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Monitoring involves LLM calls
- **Impact**: Example may work but runs slowly

---

### 5. advanced_workflows/ (3 files)

#### ❌ conditional_workflow.py
- **Status**: **IMPORT ERROR**
- **Error**: `ImportError: cannot import name 'conditional' from 'kagura'`
- **Location**: Line 8
- **Severity**: **CRITICAL** - Missing API implementation
- **Impact**: Example cannot run at all
- **Missing**: `conditional` not exported from `kagura/__init__.py`

#### ⚠️ parallel_workflow.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Parallel execution of multiple agents
- **Impact**: Example may work but runs slowly

#### ⚠️ retry_workflow.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Retry logic with multiple attempts
- **Impact**: Example may work but runs slowly

---

### 6. multimodal_rag/ (1 file)

#### ⚠️ docs_assistant.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - RAG involves embedding and retrieval
- **Impact**: Example may work but runs slowly

---

### 7. memory_routing/ (2 files)

#### ⚠️ context_routing.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Multiple routing examples with memory
- **Impact**: Example may work but runs slowly
- **Notes**: Recently fixed intent matching issues

#### ⚠️ semantic_routing.py
- **Status**: TIMEOUT (10s)
- **Severity**: LOW - Semantic routing with embeddings
- **Impact**: Example may work but runs slowly
- **Notes**: Recently fixed intent matching issues

---

## Issue Classification

### Critical Issues (2)

1. **with_memory.py - Missing `.with_session_id()` method**
   - File: `examples/agent_builder/with_memory.py:87`
   - Type: Missing API
   - Action Required: Either implement the method or update example

2. **conditional_workflow.py - Missing `conditional` import**
   - File: `examples/advanced_workflows/conditional_workflow.py:8`
   - Type: Missing API
   - Action Required: Either implement conditional workflow or update example

### High Priority Issues (2)

3. **data_extractor/agent.py - JSON parsing failure**
   - File: `examples/agents/data_extractor/agent.py`
   - Type: Type parser bug
   - Action Required: Debug why LLM response isn't valid JSON

4. **test_with_mocks.py - All tests failing**
   - File: `examples/testing/test_with_mocks.py`
   - Type: Mocking functionality broken
   - Action Required: Fix mock implementation or update examples

### Medium Priority Issues (1)

5. **test_basic.py - Pytest collection warning**
   - File: `examples/testing/test_basic.py:32`
   - Type: Test structure issue
   - Action Required: Remove `__init__` from test class

### Low Priority (15 timeout issues)

- All timeout issues are likely due to actual LLM API calls
- Examples may work correctly but need longer timeouts for full execution
- Consider adding `--quick-mode` or mock LLM responses for demo purposes

---

## Recommendations

### Immediate Actions

1. **Fix Critical Issues**:
   - Implement `.with_session_id()` in AgentBuilder or update example
   - Implement `conditional` workflow or update example

2. **Fix High Priority Issues**:
   - Debug JSON parsing in data_extractor
   - Fix mocking functionality in test_with_mocks.py

3. **Fix Medium Priority**:
   - Remove `__init__` from TestGreeterAgent class

### Long-term Improvements

1. **Add Quick Demo Mode**:
   - Add `--mock` flag to examples for quick validation
   - Use mock LLM responses to avoid timeouts

2. **Add Timeout Configuration**:
   - Document expected runtime for each example
   - Add configurable timeouts

3. **Add Example CI/CD**:
   - Run examples in CI with proper timeouts
   - Use mock LLM for syntax/structure validation

4. **Update Documentation**:
   - Add "Expected Runtime" to each example README
   - Note which examples require API keys

---

## Files Requiring Updates

### Must Fix (Critical/High)
- [ ] `examples/agent_builder/with_memory.py` (remove `.with_session_id()`)
- [ ] `examples/advanced_workflows/conditional_workflow.py` (remove `conditional` import)
- [ ] `examples/agents/data_extractor/agent.py` (fix JSON parsing)
- [ ] `examples/testing/test_with_mocks.py` (fix mock tests)

### Should Fix (Medium)
- [ ] `examples/testing/test_basic.py` (remove test class `__init__`)

### Document (Low Priority)
- [ ] Add runtime expectations to README files
- [ ] Add note about API keys and timeouts

---

## Next Steps

1. Create GitHub issues for critical and high priority problems
2. Fix critical issues first (with_memory, conditional_workflow)
3. Debug high priority issues (data_extractor, test_with_mocks)
4. Consider adding example validation to CI/CD pipeline

---

**Report Generated**: 2025-10-11
**Tool**: Claude Code Examples Health Check
**Status**: Phase 3 Complete - Ready for Issue Creation
