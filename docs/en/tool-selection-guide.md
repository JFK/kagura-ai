# Kagura MCP Tools - Selection Guide

Quick reference for choosing the right tool for your task.

---

## For Most Users (90% of use cases)

### 📝 Memory Management

**Saving Information**
- **memory_store**: Save information to remember later
  - When: "Remember that...", "Save my preference..."
  - Example: `memory_store(user_id, key="user_name", value="Kiyota")`
  - Defaults: `agent_name="global"`, `scope="persistent"` ✨ NEW in v4.0.10

**Finding Information**
- **memory_search**: Find previously saved information
  - When: "What did we discuss about...", "Find memories about..."
  - Auto-combines semantic + keyword search
  - Example: `memory_search(user_id, agent_name, query="authentication setup")`

**Retrieving Specific Values**
- **memory_recall**: Get value by exact key
  - When: "What's my...", exact key known
  - Example: `memory_recall(user_id, agent_name, key="user_name")`

---

### 💻 Coding Assistance

**Session Management**
- **coding_start_session**: Begin tracking work session
  - When: Starting new feature/bug fix
  - Example: `coding_start_session(user_id, project_id, description="Fix auth bug")`

- **coding_track_file_change**: Record file modifications
  - When: After editing files
  - Example: `coding_track_file_change(..., file_path="src/auth.py", action="edit", reason="Fix JWT validation")`

- **coding_end_session**: Finish session with AI summary
  - When: Work completed
  - Generates comprehensive summary automatically

**Recording**
- **coding_record_error**: Log errors with solutions
- **coding_record_decision**: Document design decisions

---

### 🐙 GitHub Integration

- **github_issue_view**: Get issue details
- **github_pr_view**: Get PR details
- **github_pr_create**: Create pull request
- **github_pr_merge**: Merge pull request

---

## Specialized Tools (10% of use cases)

### 🔍 Advanced Memory Search

- **memory_timeline**: Time-based search
  - When: "What did we do last week", "Recent conversations"
  - Example: `memory_timeline(user_id, agent_name, time_range="last_7_days")`

- **memory_fuzzy_recall**: Approximate key matching
  - When: "Something about auth...", unsure of exact key
  - Uses Levenshtein distance for fuzzy matching

- **memory_search_hybrid**: Fine-tune search balance
  - When: Need to adjust keyword vs semantic ratio
  - Parameters: `keyword_weight`, `semantic_weight`

### 🔬 Code Analysis

- **coding_analyze_patterns**: Detect coding patterns and preferences
- **coding_search_source_code**: Search indexed codebase semantically
- **coding_analyze_refactor_impact**: Assess refactoring risk
- **coding_suggest_refactor_order**: Safe refactoring sequence

### 🌐 Web & Research

- **brave_web_search**: Search the web
- **arxiv_search**: Search academic papers
- **youtube_summarize**: Summarize YouTube videos
- **fact_check_claim**: Verify claims with sources

---

## Developer/Debug Tools

- **memory_list**: Browse all stored memories
- **memory_stats**: Memory health statistics
- **telemetry_stats**: Usage statistics
- **telemetry_tools**: Analyze tool usage patterns ✨ NEW in v4.0.10

---

## Decision Flowchart

```
Need to remember something?
├─ Save new info → memory_store (use defaults!)
├─ Find by concept → memory_search
├─ Find by exact key → memory_recall
└─ Find by time → memory_timeline

Working on code?
├─ Start work → coding_start_session
├─ Track changes → coding_track_file_change
├─ Record error → coding_record_error
├─ Record decision → coding_record_decision
└─ Finish work → coding_end_session

GitHub operation?
├─ View issue/PR → github_issue_view / github_pr_view
├─ Create → github_pr_create
└─ Merge → github_pr_merge

Need information?
├─ Web search → brave_web_search
├─ Academic papers → arxiv_search
├─ YouTube content → youtube_summarize
└─ Fact check → fact_check_claim
```

---

## Best Practices

### 1. Start Simple
Use common tools first (memory_store/search, coding_start/end_session).

### 2. Use Defaults (v4.0.10)
Most parameters have sensible defaults:
- `memory_store`: `agent_name="global"`, `scope="persistent"`
- `memory_search`: `k=3`, `scope="all"`, `mode="full"`

### 3. Check Tool Descriptions
Each tool has usage examples in its docstring.

### 4. Browse by Category
```bash
kagura mcp tools --category memory    # Memory tools
kagura mcp tools --category coding    # Coding tools
kagura mcp tools --category github    # GitHub tools
```

### 5. Analyze Your Usage
```bash
kagura telemetry tools                # See which tools you use most
```

---

## Common Patterns

### Pattern 1: Conversation Memory

```python
# Save user preference
await memory_store(
    user_id="user_123",
    key="preferred_language",
    value="Japanese"
)
# Uses defaults: global/persistent

# Later, in any conversation
await memory_recall(user_id="user_123", agent_name="global", key="preferred_language")
# Returns: "Japanese"
```

### Pattern 2: Coding Session

```python
# 1. Start session
await coding_start_session(
    user_id="dev_kiyota",
    project_id="my-app",
    description="Implement authentication system"
)

# 2. Track work
await coding_track_file_change(
    ..., file_path="src/auth.py", action="create", reason="Add JWT auth"
)

await coding_record_decision(
    ..., decision="Use RS256 for JWT signing", rationale="Better security..."
)

# 3. End session
await coding_end_session(..., success="true", save_to_github="true")
# Generates AI summary, posts to GitHub Issue
```

### Pattern 3: Research & Fact-Checking

```python
# 1. Search web
results = await brave_web_search(query="Python async best practices 2025")

# 2. Verify claims
await fact_check_claim(claim="Python 3.13 is 40% faster than 3.12")

# 3. Save findings
await memory_store(..., key="python_3.13_perf", value="Confirmed: 40% faster...")
```

---

## Anti-Patterns (What NOT to Do)

### ❌ Don't Forget to Clean Up Unused Memory
```python
# BAD
memory_store(..., key="temp_result")  # Never deleted, accumulates over time

# GOOD
memory_store(..., key="temp_result")
# ... use the data ...
memory_delete(..., key="temp_result")  # Clean up when done
```

### ❌ Don't Forget to End Sessions
```python
# BAD
coding_start_session(...)
# ... work ...
# (never call coding_end_session - no summary!)

# GOOD
coding_start_session(...)
# ... work ...
coding_end_session()  # Generates summary
```

### ❌ Don't Mix Thread and Global Without Reason
```python
# BAD - Inconsistent storage
memory_store(..., agent_name="global", key="temp_var", ...)
memory_store(..., agent_name="thread_123", key="user_name", ...)

# GOOD - Logical separation
memory_store(..., agent_name="global", key="user_name", ...)  # Permanent
memory_store(..., agent_name="thread_123", key="temp_var", ...)  # Temporary
```

---

## Need Help?

- **CLI**: `kagura mcp tools --help`
- **Docs**: https://docs.kagura-ai.dev
- **Issues**: https://github.com/JFK/kagura-ai/issues

**Feedback**: Help us improve this guide! File an issue or PR.
