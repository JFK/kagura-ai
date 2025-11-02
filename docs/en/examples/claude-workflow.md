# Claude + Kagura AI Workflow Examples

> **Practical workflows for using Kagura AI with Claude Desktop and Claude Code**

This guide provides real-world workflow examples for integrating Kagura AI with Claude platforms (Desktop and Code) via Local MCP.

---

## 📋 Setup

### Prerequisites

**Claude Desktop**:
1. Kagura installed: `pip install kagura-ai[full]`
2. MCP configured: `kagura mcp install`
3. Claude Desktop restarted

**Claude Code**:
1. Kagura installed: `pip install kagura-ai[full]`
2. MCP added: `claude mcp add --transport stdio kagura -- kagura mcp serve`
3. Verify: `claude mcp list`

See:
- [Claude Desktop Setup](../mcp-setup.md)
- [Claude Code Setup](../mcp-claude-code-setup.md)

---

## 💻 Workflow 1: Full-Stack Development (Local MCP)

**Use Case**: Develop a FastAPI application with full file access and Git integration

**Unique to Local MCP**: File read/write, shell execution, media preview

### Example: Building an API

```
User: "Start coding session for 'Build user authentication API'"

Claude: [Uses coding_start_session]

User: "Read the current project structure"

Claude: [Uses dir_list, file_read]
        "Your project:
         - main.py (FastAPI app)
         - models.py (User model exists)
         - auth.py (empty, needs implementation)"

User: "Create an OAuth2 implementation in auth.py"

Claude: [Uses file_write]
        "I've created auth.py with:
         - TokenData and User schemas
         - get_current_user dependency
         - create_access_token function"

User: "Run the tests"

Claude: [Uses shell_exec - generates command]
        "Command: pytest tests/test_auth.py -v"

User: "The tests failed with ImportError. Record this error."

Claude: [Uses coding_record_error]

User: "Search for similar errors I've had before"

Claude: [Uses coding_search_errors]
        "You had a similar ImportError 5 days ago.
         Solution: Add __init__.py to auth module"

User: "Fix it and re-run tests"

Claude: [Uses file_write, shell_exec]
        "Fixed! All tests passing ✅"

User: "Track all these changes"

Claude: [Uses coding_track_file_change]

User: "Create a GitHub issue for documenting this auth system"

Claude: [Uses github_issue_create via github_exec]
        "Created issue #475: 'Document OAuth2 authentication'"

User: "End session and generate PR description"

Claude: [Uses coding_end_session, coding_generate_pr_description]
        "Summary: Implemented OAuth2 authentication
         Files: auth.py (new), __init__.py (modified)
         Tests: 12 passing
         Cost: $0.18

         PR Description:
         ## What
         Implement OAuth2 JWT authentication for user endpoints

         ## Why
         Secure API access with industry-standard authentication

         ## Changes
         - Add auth.py with JWT token handling
         - Create User schema and dependencies
         - Add 12 unit tests

         ## Testing
         - ✅ All tests passing
         - ✅ Manual testing with Postman

         Closes #475"
```

### Benefits

- ✅ **File Access**: Read/write project files directly
- ✅ **Shell Commands**: Run tests, linters, Git commands
- ✅ **Error Tracking**: Learn from past mistakes
- ✅ **GitHub Integration**: Create issues, PRs seamlessly
- ✅ **AI Summaries**: Automatic session summaries + PR descriptions

---

## 📝 Workflow 2: Documentation Writing

**Use Case**: Write and preview documentation with live file editing

### Example: Writing API Docs

```
User: "Start session for 'Write API documentation'"

Claude: [Uses coding_start_session]

User: "Read the current API endpoints from main.py"

Claude: [Uses file_read]
        "Found endpoints:
         - POST /auth/login
         - POST /auth/register
         - GET /users/me
         - PUT /users/me
         - DELETE /users/me"

User: "Create API documentation in docs/api.md"

Claude: [Uses file_write]
        "I've created comprehensive API docs with:
         - Authentication section
         - All 5 endpoints with examples
         - Error responses
         - Rate limiting notes"

User: "Read it back to me to verify"

Claude: [Uses file_read]
        [Shows full content]

User: "Search the web for API documentation best practices"

Claude: [Uses brave_web_search]

User: "Remember these best practices with tags=['documentation', 'api']:
       - Use OpenAPI/Swagger spec
       - Provide curl examples
       - Document error codes
       - Include rate limits
       - Add versioning info"

Claude: [Uses memory_store]

User: "Update the docs with these best practices"

Claude: [Uses file_write]

User: "List all markdown files in docs/"

Claude: [Uses dir_list]

User: "Track this documentation change"

Claude: [Uses coding_track_file_change]

User: "End session with summary"

Claude: [Uses coding_end_session]
        "Documentation session complete:
         - Created docs/api.md (125 lines)
         - Researched best practices
         - Applied improvements
         Cost: $0.12"
```

### Benefits

- ✅ **File Editing**: Write docs directly in project
- ✅ **Content Verification**: Read back to check accuracy
- ✅ **Research Integration**: Web search + persistent memory
- ✅ **Change Tracking**: Monitor documentation growth

---

## 🎨 Workflow 3: Image Analysis & Multimodal RAG

**Use Case**: Index project screenshots and find them semantically

**Requires**: Gemini API key

### Example: Screenshot Management

```
User: "Index all images in ./screenshots directory"

Claude: [Uses dir_list, multimodal_index]
        "Indexed 47 images:
         - UI mockups: 12
         - Error screenshots: 18
         - Architecture diagrams: 8
         - Performance graphs: 9"

User: "Find screenshots of database connection errors"

Claude: [Uses multimodal_search]
        "Found 3 matches:
         1. error_postgres_connection_refused.png (similarity: 0.92)
         2. db_timeout_error.png (similarity: 0.87)
         3. connection_pool_exhausted.png (similarity: 0.81)"

User: "Open the first one"

Claude: [Uses media_open_image - Local MCP only]
        "Opening error_postgres_connection_refused.png..."

User: "This is the error I'm seeing now! What was the solution?"

Claude: [Uses coding_search_errors]
        "You fixed this before:
         1. Check PostgreSQL is running
         2. Verify connection string
         3. Add retry logic"

User: "Remember to create a troubleshooting guide with this screenshot"

Claude: [Uses memory_store with tags=['todo', 'documentation']]
```

### Benefits

- ✅ **Visual Memory**: Find images by description
- ✅ **Multi-Language**: Works in 100+ languages
- ✅ **Quick Preview**: Open images directly from Claude
- ✅ **Context Linking**: Connect images to solutions

---

## 🔬 Workflow 4: Data Analysis with CSV Files

**Use Case**: Analyze CSV data with direct file access

### Example: Performance Analysis

```
User: "Read the performance_metrics.csv file"

Claude: [Uses file_read]
        "CSV contains:
         - Timestamp, endpoint, response_time_ms, status_code
         - 10,000 rows of API performance data"

User: "Start analyzing this data. Track this session."

Claude: [Uses coding_start_session]

User: "What's the average response time?"

Claude: [Analyzes data from file_read]
        "Average response time: 245ms
         Median: 198ms
         95th percentile: 850ms
         Slowest endpoint: /api/search (avg 1200ms)"

User: "Search the web for API response time best practices"

Claude: [Uses brave_web_search]

User: "Remember this benchmark with tags=['performance', 'api']:
       - Excellent: < 100ms
       - Good: 100-300ms
       - Acceptable: 300-1000ms
       - Slow: > 1000ms"

Claude: [Uses memory_store]

User: "Based on this, which endpoints need optimization?"

Claude: "According to the benchmark you saved:
         - /api/search: 1200ms (SLOW - needs optimization)
         - /api/reports: 780ms (Acceptable, but room for improvement)
         - All others: Good to Excellent"

User: "Create a GitHub issue to optimize /api/search"

Claude: [Uses github_issue_create]
        "Created Issue #476: 'Optimize /api/search endpoint (1200ms avg)'"

User: "Write analysis summary to performance_analysis.md"

Claude: [Uses file_write]

User: "End session"

Claude: [Uses coding_end_session]
        "Analysis complete:
         - Analyzed 10,000 API requests
         - Identified 1 critical optimization target
         - Created GitHub issue #476
         - Generated analysis report
         Cost: $0.09"
```

### Benefits

- ✅ **Direct File Access**: Read CSV without copy/paste
- ✅ **Large Data**: Handle 10K+ rows efficiently
- ✅ **Persistent Benchmarks**: Save standards for future reference
- ✅ **Action Items**: Create issues directly from analysis

---

## 🎥 Workflow 5: Learning from Video Content

**Use Case**: Extract and organize knowledge from YouTube tutorials

### Example: Learning Docker

```
User: "Search for Docker tutorial videos"

Claude: [Uses brave_video_search]
        "Found:
         1. 'Docker Tutorial for Beginners' (1.2M views)
         2. 'Docker Compose in 12 Minutes' (500K views)
         3. 'Docker Production Best Practices' (300K views)"

User: "Get the transcript for video #1"

Claude: [Uses get_youtube_transcript]
        [Returns full transcript]

User: "Summarize this tutorial"

Claude: [Uses youtube_summarize]
        "Summary:
         - Docker basics: containers vs VMs
         - Key concepts: images, containers, Dockerfile
         - Commands: docker build, run, ps, stop
         - Volumes for data persistence
         - Networks for container communication"

User: "Save this summary with tags=['docker', 'tutorial', 'learning']"

Claude: [Uses memory_store]

User: "Fact-check the claim that 'containers are 10x more efficient than VMs'"

Claude: [Uses youtube_fact_check]
        "Claim verified:
         - Multiple sources confirm 5-10x resource efficiency
         - Containers share OS kernel (lighter overhead)
         - Startup time: containers (seconds) vs VMs (minutes)
         Sources: Docker docs, research papers, benchmarks"

User: "Remember this with tags=['docker', 'performance', 'verified']"

Claude: [Uses memory_store]

User: "Create a Dockerfile for our FastAPI project based on what I learned"

Claude: [Uses file_write with knowledge from memory]
        "Created Dockerfile:
         FROM python:3.11-slim
         WORKDIR /app
         COPY requirements.txt .
         RUN pip install -r requirements.txt
         COPY . .
         CMD ['uvicorn', 'main:app', '--host', '0.0.0.0']"

User: "Search for Docker security best practices"

Claude: [Uses brave_web_search]

User: "Update the Dockerfile with security improvements"

Claude: [Uses file_write]
        "Updated with best practices:
         - Non-root user
         - Multi-stage build
         - Minimal base image
         - .dockerignore file"
```

### Benefits

- ✅ **Video Learning**: Extract knowledge without watching
- ✅ **Fact Verification**: Check claims against web sources
- ✅ **Applied Learning**: Immediately create files based on lessons
- ✅ **Knowledge Retention**: Persistent memory for future reference

---

## 🔄 Workflow 6: Refactoring with Dependency Analysis

**Use Case**: Safely refactor code by understanding dependencies

### Example: Refactoring a Module

```
User: "I want to refactor the database.py module. Analyze its dependencies first."

Claude: [Uses coding_analyze_file_dependencies]
        "database.py dependencies:
         Imports:
         - psycopg2 (external)
         - config (internal: ./config.py)
         - models (internal: ./models.py)

         Used by (7 files):
         - main.py (imports: get_db)
         - auth.py (imports: get_db, User)
         - api/users.py (imports: get_db)
         - api/posts.py (imports: get_db)
         - tests/test_db.py (imports: all functions)
         - tests/test_api.py (imports: get_db)
         - migrations/init_db.py (imports: engine)"

User: "What's the safe order to refactor if I also need to update auth.py and models.py?"

Claude: [Uses coding_suggest_refactor_order]
        "Safe refactoring order:
         1. models.py (no dependencies on others)
         2. database.py (depends on models)
         3. auth.py (depends on database, models)

         Reasoning:
         - models.py is at the bottom of dependency chain
         - database.py imports models
         - auth.py imports both
         - Refactoring bottom-up avoids breaking imports"

User: "Analyze the impact if I change the get_db function signature"

Claude: [Uses coding_analyze_refactor_impact]
        "Impact analysis:
         ⚠️ HIGH IMPACT - get_db is used in 6 files

         Files affected:
         - main.py: 1 usage
         - auth.py: 3 usages
         - api/users.py: 5 usages
         - api/posts.py: 4 usages
         - tests/test_api.py: 12 usages

         Recommendation:
         1. Update function signature
         2. Update all 25 usages
         3. Run full test suite
         4. Consider deprecation warning for gradual migration"

User: "Record this design decision: We'll use async database connections"

Claude: [Uses coding_record_decision]
        "Design decision recorded:
         - Decision: Migrate to async database connections
         - Rationale: Better performance for I/O-bound operations
         - Impact: 6 files affected, 25 usages to update
         - Risk: High (core dependency)
         - Mitigation: Full test coverage before deployment"

User: "Start the refactoring. Update models.py first."

Claude: [Uses file_read, file_write]
        "Updated models.py with async SQLAlchemy support"

User: "Track this change"

Claude: [Uses coding_track_file_change]
```

### Benefits

- ✅ **Dependency Awareness**: Know what breaks before you break it
- ✅ **Safe Ordering**: Refactor in the right sequence
- ✅ **Impact Analysis**: Understand scope of changes
- ✅ **Decision Documentation**: Record why you made changes

---

## 🧠 Workflow 7: Cross-Platform Memory Sync

**Use Case**: Start in Claude Desktop (local files), continue in Claude Code (CLI)

### Morning: Claude Desktop

```
User: "Start coding session for 'Implement rate limiting'"

Claude Desktop: [Uses coding_start_session]

User: "Read the current API implementation"

Claude Desktop: [Uses file_read on main.py]

User: "Search the web for rate limiting algorithms"

Claude Desktop: [Uses brave_web_search]

User: "Remember for user_id='john': Use token bucket algorithm with Redis backend.
       Tags: ['rate-limiting', 'design']"

Claude Desktop: [Uses memory_store]

User: "I need to leave for a meeting. Save my progress."

Claude Desktop: [Uses coding_track_file_change]
```

### Afternoon: Claude Code (CLI)

```
$ claude

User: "What was I working on for user_id='john'?"

Claude Code: [Uses memory_search with user_id="john"]
             "You were implementing rate limiting using token bucket
              algorithm with Redis backend"

User: "Show me the design I chose"

Claude Code: [Uses memory_recall with tags=['rate-limiting', 'design']]

User: "Continue the implementation. Install dependencies first."

Claude Code: [Uses shell_exec]
             "Running: pip install redis fastapi-limiter"

User: "Create rate_limiter.py"

Claude Code: [Uses file_write]

User: "Run tests"

Claude Code: [Uses shell_exec]
             "pytest tests/test_rate_limit.py -v
              ✅ 5 passing"

User: "End session"

Claude Code: [Uses coding_end_session]
             "Session complete:
              - Implemented token bucket rate limiting
              - Added Redis backend
              - 5 tests passing
              Cost: $0.14"
```

### Benefits

- ✅ **Seamless Transition**: Desktop GUI → CLI without losing context
- ✅ **Unified Memory**: Same user_id, same memories
- ✅ **Flexible Environment**: Use best tool for each task
- ✅ **Continuous Sessions**: Pick up exactly where you left off

---

## 💡 Pro Tips for Local MCP

### 1. Leverage File Access

Use `file_read` instead of copy/paste:

```
✅ "Read config.py and show me the database settings"
❌ [copy/paste entire file]
```

### 2. Safe Shell Execution

Use `github_exec` for Git operations:

```
"Execute: gh issue list --state open"
"Run: git status"
```

### 3. Preview Media Files

Open images/videos directly:

```
"Show me screenshot.png"
[Uses media_open_image]
```

### 4. Analyze Dependencies Before Refactoring

Always check dependencies first:

```
"Analyze dependencies for auth.py before I refactor it"
[Uses coding_analyze_file_dependencies]
```

### 5. Track Everything

Don't forget to track file changes:

```
After every file modification:
"Track this change to database.py"
[Uses coding_track_file_change]
```

---

## 🔗 Related Resources

- [Chat Integration Tips](../chat-integration-tips.md) - Main guide
- [ChatGPT Workflow Examples](./chatgpt-workflow.md) - ChatGPT-specific workflows
- [Claude Desktop Setup](../mcp-setup.md) - Setup guide
- [Claude Code Setup](../mcp-claude-code-setup.md) - CLI setup

---

**Version**: 4.0.0
**Last updated**: 2025-11-02
