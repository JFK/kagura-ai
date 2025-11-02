# ChatGPT + Kagura AI Workflow Examples

> **Practical workflows for using Kagura AI with ChatGPT**

This guide provides real-world workflow examples for integrating Kagura AI with ChatGPT via Remote MCP.

---

## 📋 Setup

### Prerequisites

1. **Kagura Remote MCP Server** running
2. **ChatGPT** configured with MCP connection
3. **API Keys** (optional): Brave Search, Gemini

See: [MCP over HTTP/SSE Setup Guide](../mcp-http-setup.md)

---

## 🎯 Workflow 1: Project Management

**Use Case**: Track project tasks, meeting notes, and decisions across multiple conversations

### Example Session 1: Morning Planning

```
User: "Start a new project tracking session for 'kagura-ai v4.0 documentation'"

ChatGPT: [Uses coding_start_session]

User: "Remember these priorities with tags=['documentation', 'v4.0']:
       1. Chat Integration Tips
       2. Workflow Examples
       3. Troubleshooting Guide"

ChatGPT: [Uses memory_store with scope="persistent"]

User: "Set project deadline to November 15, 2025. This is important."

ChatGPT: [Uses memory_store]
```

### Example Session 2: Afternoon Work

```
User: "What are my documentation priorities?"

ChatGPT: [Uses memory_search with tags=['documentation', 'v4.0']]
         "Your priorities are:
          1. Chat Integration Tips
          2. Workflow Examples
          3. Troubleshooting Guide"

User: "I completed the Chat Integration Tips document. Record this."

ChatGPT: [Uses coding_track_file_change]

User: "Search the web for best practices on writing technical documentation"

ChatGPT: [Uses brave_web_search]
```

### Example Session 3: Evening Review

```
User: "What's my project deadline?"

ChatGPT: [Uses memory_recall]
         "Your deadline is November 15, 2025"

User: "End the coding session and generate a summary"

ChatGPT: [Uses coding_end_session]
         "Summary: Completed Chat Integration Tips (370 lines).
          Cost: $0.15 for embeddings. Remaining: Workflow Examples,
          Troubleshooting Guide."
```

### Benefits

- ✅ **Persistent Memory**: Tasks survive across conversations
- ✅ **Cross-Platform**: Access from any ChatGPT session
- ✅ **AI Summaries**: Automatic session summaries with cost tracking
- ✅ **Searchable**: Find tasks by tags, keywords, or semantic search

---

## 📚 Workflow 2: Learning & Research Notes

**Use Case**: Build a personal knowledge base from YouTube videos, web articles, and papers

### Example: Learning FastAPI

```
User: "I'm learning FastAPI. Start tracking this."

ChatGPT: [Uses coding_start_session]

User: "Search YouTube for 'FastAPI tutorial for beginners'"

ChatGPT: [Uses brave_video_search]
         "Found: 'FastAPI Tutorial - Build a REST API in 15 Minutes'
          URL: https://www.youtube.com/watch?v=xxxxx"

User: "Summarize this video: https://www.youtube.com/watch?v=xxxxx"

ChatGPT: [Uses youtube_summarize]
         "Summary: Covers basics of FastAPI including routing,
          Pydantic models, automatic docs, async support..."

User: "Remember this summary with tags=['fastapi', 'tutorial', 'learning'].
       This is important for future reference."

ChatGPT: [Uses memory_store with scope="persistent"]

User: "Search arXiv for papers about API performance optimization"

ChatGPT: [Uses arxiv_search]

User: "Remember the top 3 papers with tags=['fastapi', 'performance', 'research']"

ChatGPT: [Uses memory_store]

User: "Search the web for FastAPI vs Django performance benchmarks"

ChatGPT: [Uses brave_web_search]

User: "Save this comparison with tags=['fastapi', 'django', 'comparison']:
       FastAPI: 3x faster for async workloads, better type safety
       Django: More batteries-included, larger ecosystem"

ChatGPT: [Uses memory_store]
```

### Later Session: Recall Knowledge

```
User: "What did I learn about FastAPI?"

ChatGPT: [Uses memory_search with query="FastAPI learning"]
         "You learned:
          1. FastAPI tutorial summary (async, Pydantic, auto docs)
          2. Performance: 3x faster than Django for async
          3. Research papers: [lists 3 papers]"

User: "Show me all memories tagged with 'fastapi'"

ChatGPT: [Uses memory_search with tags=['fastapi']]

User: "What are the key differences between FastAPI and Django?"

ChatGPT: [Uses memory_recall]
         "FastAPI: 3x faster for async, better type safety
          Django: More batteries-included, larger ecosystem"
```

### Benefits

- ✅ **Knowledge Retention**: Never forget what you learned
- ✅ **Organized**: Tags for easy retrieval
- ✅ **Multi-Source**: YouTube, web, arXiv, all in one place
- ✅ **Searchable**: Semantic search finds related topics

---

## 💻 Workflow 3: Code Development & Error Tracking

**Use Case**: Track coding sessions, errors, and solutions for future reference

### Example: Debugging a Python Error

```
User: "Start coding session for 'Fix database connection issue'"

ChatGPT: [Uses coding_start_session]

User: "I'm getting this error:
       psycopg2.OperationalError: could not connect to server:
       Connection refused"

ChatGPT: "Let me search for similar past errors"
         [Uses coding_search_errors]

         "You encountered a similar error 2 weeks ago. The solution was:
          Check if PostgreSQL is running: sudo systemctl start postgresql"

User: "That fixed it! Record this solution."

ChatGPT: [Uses coding_record_error with solution]

User: "I also added retry logic to the connection code"

ChatGPT: "Great design decision. Let me record it."
         [Uses coding_record_decision]

User: "Search the web for PostgreSQL connection pooling best practices"

ChatGPT: [Uses brave_web_search]

User: "Remember this with tags=['postgresql', 'connection-pooling', 'best-practice']:
       Use pgBouncer for connection pooling in production.
       Max pool size = (2 × CPU cores) + disk count"

ChatGPT: [Uses memory_store]

User: "End session and generate summary"

ChatGPT: [Uses coding_end_session]
         "Summary: Fixed PostgreSQL connection error. Added retry logic.
          Researched connection pooling best practices.
          Files modified: 1 (database.py)
          Cost: $0.08"
```

### Later: Encountering Similar Error

```
User: "I'm getting 'Connection refused' error again"

ChatGPT: [Uses coding_search_errors]
         "You've seen this before! Solution:
          1. Check if PostgreSQL is running
          2. You added retry logic in database.py
          3. Consider using pgBouncer for pooling"

User: "What were my connection pooling best practices?"

ChatGPT: [Uses memory_search]
         "You learned: Use pgBouncer in production.
          Max pool size = (2 × CPU cores) + disk count"
```

### Benefits

- ✅ **Error History**: Never debug the same issue twice
- ✅ **Solution Tracking**: Remember what worked
- ✅ **Design Decisions**: Document why you chose a solution
- ✅ **Pattern Learning**: AI analyzes your coding patterns

---

## 🎨 Workflow 4: Content Creation & Writing

**Use Case**: Research, draft, and refine content with persistent memory

### Example: Writing a Blog Post

```
User: "I'm writing a blog post about 'Why FastAPI is great for ML APIs'.
       Start tracking this."

ChatGPT: [Uses coding_start_session]

User: "Search the web for latest FastAPI adoption statistics"

ChatGPT: [Uses brave_web_search]

User: "Remember these stats with tags=['fastapi', 'adoption', 'blog']:
       - 50K+ GitHub stars
       - Used by Netflix, Uber, Microsoft
       - 3x faster than Flask for async"

ChatGPT: [Uses memory_store]

User: "Search for research papers about ML serving performance"

ChatGPT: [Uses arxiv_search]

User: "Search for YouTube talks about FastAPI in production"

ChatGPT: [Uses brave_video_search]

User: "Summarize this talk: [URL]"

ChatGPT: [Uses youtube_summarize]

User: "Save this outline with tags=['blog', 'outline']:
       1. Introduction (FastAPI adoption)
       2. Performance benchmarks
       3. ML-specific features (Pydantic, async)
       4. Production case studies
       5. Conclusion"

ChatGPT: [Uses memory_store]
```

### Next Session: Writing Draft

```
User: "Show me my blog post outline"

ChatGPT: [Uses memory_recall]

User: "What statistics did I collect?"

ChatGPT: [Uses memory_search with tags=['fastapi', 'adoption']]

User: "I finished the introduction. Track this change."

ChatGPT: [Uses coding_track_file_change]
```

### Final Session: Publishing

```
User: "End session and generate a summary for my writing log"

ChatGPT: [Uses coding_end_session]
         "Blog post completed: 'Why FastAPI is great for ML APIs'
          Research: 5 web sources, 3 papers, 2 YouTube talks
          Sections: 5 (all complete)
          Cost: $0.22"

User: "Remember to publish this on November 10, 2025"

ChatGPT: [Uses memory_store with tags=['blog', 'deadline']]
```

### Benefits

- ✅ **Research Organization**: All sources in one place
- ✅ **Version Tracking**: Track outline and draft changes
- ✅ **Cross-Session**: Resume work anytime
- ✅ **AI Summaries**: Automatic progress summaries

---

## 📊 Workflow 5: Data Analysis & Insights

**Use Case**: Analyze your own interaction patterns and interests

### Example: Self-Reflection

```
User: "Analyze my coding patterns from the past month"

ChatGPT: [Uses coding_analyze_patterns]
         "Your patterns:
          - Primary language: Python (85%)
          - Frameworks: FastAPI (60%), Django (25%), Flask (15%)
          - Most common errors: Database connection (12 times)
          - Peak coding hours: 9-11 AM, 2-4 PM
          - Average session: 2.3 hours"

User: "What topics do I interact with most?"

ChatGPT: [Uses memory_get_user_pattern]
         "Your top interests:
          1. Backend development (FastAPI, Django)
          2. Database optimization (PostgreSQL)
          3. API design
          4. Documentation writing
          5. Python best practices"

User: "Show me my memory statistics"

ChatGPT: [Uses memory_stats]
         "Memory Health Report:
          - Total memories: 342
          - Persistent: 198 (57.8%)
          - Working: 144 (42.2%)
          - Top tags: python (87), fastapi (56), tutorial (42)
          - Storage: 2.4 MB
          - Last cleanup: 3 days ago"

User: "What are my most useful memories?"

ChatGPT: [Uses memory_list with filters]
         "Top rated memories (by usefulness score):
          1. PostgreSQL connection pooling best practices (0.95)
          2. FastAPI vs Django comparison (0.92)
          3. Python type hints guide (0.88)"
```

### Benefits

- ✅ **Self-Awareness**: Understand your coding habits
- ✅ **Interest Tracking**: See what topics you care about
- ✅ **Memory Health**: Monitor and optimize memory usage
- ✅ **Quality Metrics**: Identify most valuable memories

---

## 🔄 Workflow 6: Cross-Platform Continuity

**Use Case**: Start work in ChatGPT, continue in Claude Desktop/Code

### Morning: ChatGPT (Web)

```
User: "Remember for user_id='john_doe': Today's task is to implement
       OAuth2 authentication in the FastAPI project"

ChatGPT: [Uses memory_store with user_id="john_doe"]

User: "Search for OAuth2 best practices"

ChatGPT: [Uses brave_web_search]

User: "Save this implementation plan with tags=['oauth2', 'plan']:
       1. Install python-jose, passlib
       2. Create user models
       3. Implement token endpoints
       4. Add protected routes
       5. Write tests"

ChatGPT: [Uses memory_store]
```

### Afternoon: Claude Desktop (Local)

```
User: "What task did I set for user_id='john_doe' today?"

Claude: [Uses memory_recall with user_id="john_doe"]
        "Today's task: Implement OAuth2 authentication in FastAPI"

User: "Show me the implementation plan"

Claude: [Uses memory_search with tags=['oauth2', 'plan']]

User: "Read the current auth.py file"

Claude: [Uses file_read - Local MCP only]

User: "I implemented step 1-3. Track these changes for user_id='john_doe'"

Claude: [Uses coding_track_file_change]
```

### Evening: ChatGPT (Mobile)

```
User: "What progress did user_id='john_doe' make on OAuth2?"

ChatGPT: [Uses memory_search + coding session history]
         "Completed steps 1-3:
          1. ✅ Installed dependencies
          2. ✅ Created user models
          3. ✅ Implemented token endpoints
          Remaining: Protected routes, tests"
```

### Benefits

- ✅ **Platform Independence**: Work seamlessly across devices
- ✅ **Context Preservation**: Never lose your place
- ✅ **Unified Memory**: One source of truth
- ✅ **Flexible Workflow**: Use the best tool for each task

---

## 💡 Pro Tips

### 1. Use Consistent user_id

Always specify the same `user_id` across platforms:

```
"Remember for user_id='john_doe': [information]"
```

### 2. Tag Everything

Tags make retrieval easier:

```
"Save this with tags=['python', 'best-practice', 'typing']: ..."
```

### 3. Be Explicit About Persistence

Don't rely on defaults:

```
"Remember this PERMANENTLY: ..."
"Save this temporarily for this session: ..."
```

### 4. Use Semantic Search

Don't search for exact keywords:

```
✅ "Find memories about database optimization"
❌ "Find memory with key 'postgresql_connection_pooling_2024'"
```

### 5. Provide Feedback

Help Kagura learn what's useful:

```
"Mark this memory as very useful"
"This information is outdated"
```

---

## 🔗 Related Resources

- [Chat Integration Tips](../chat-integration-tips.md) - Main guide
- [Claude Workflow Examples](./claude-workflow.md) - Claude-specific workflows
- [MCP Setup (ChatGPT)](../mcp-http-setup.md) - Setup guide

---

**Version**: 4.0.0
**Last updated**: 2025-11-02
