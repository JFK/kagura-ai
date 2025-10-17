# 07_presets - Agent Presets

This directory contains examples demonstrating Kagura AI's pre-configured agent presets (RFC-026).

## Overview

Agent Presets provide ready-to-use, production-quality agents for common use cases:
- **ChatbotPreset** - Conversational AI with personality
- **ResearchPreset** - Research assistant with web search
- **CodeReviewPreset** - Code review and analysis
- **TranslatorPreset** - Multi-language translation
- **DataAnalystPreset** - Data analysis and insights
- **PersonalAssistantPreset** - Personal task management
- **ContentWriterPreset** - Content generation
- **TechnicalSupportPreset** - Technical support bot
- **LearningTutorPreset** - Educational tutor
- **ProjectManagerPreset** - Project planning and tracking

## Why Use Presets?

```
Traditional Approach:
  1. Design agent architecture
  2. Configure memory system
  3. Set up tools
  4. Tune prompts
  5. Add error handling
  ⏱️ Time: 2-3 hours

Preset Approach:
  1. Select preset
  2. Customize (optional)
  3. Build
  ⏱️ Time: 5 minutes
```

**Benefits:**
- ⚡ Instant setup
- ✅ Best practices built-in
- 🎯 Optimized prompts
- 🔧 Easy customization
- 📊 Production-ready

## Available Presets (10 Total)

### Core Presets (3)
1. **ChatbotPreset** - General conversation
2. **ResearchPreset** - Web research
3. **CodeReviewPreset** - Code analysis

### Extended Presets (7) - RFC-026
4. **TranslatorPreset** - Translation
5. **DataAnalystPreset** - Data analysis
6. **PersonalAssistantPreset** - Task management
7. **ContentWriterPreset** - Content creation
8. **TechnicalSupportPreset** - Support automation
9. **LearningTutorPreset** - Education
10. **ProjectManagerPreset** - Project planning

## Examples

### 1. chatbot_preset.py - Conversational AI
**Demonstrates:**
- Basic chatbot setup
- Personality customization
- Conversational memory
- Context awareness

```python
from kagura.presets import ChatbotPreset

# Create chatbot with personality
chatbot = (
    ChatbotPreset("friendly_bot")
    .with_model("gpt-4o-mini")
    .with_context(
        personality="friendly and enthusiastic",
        style="casual but professional",
        tone="warm and helpful"
    )
    .build()
)

# Conversation
response = await chatbot("Hi! What can you help me with?")
print(response)
```

**Built-in Features:**
- Conversational memory
- Personality traits
- Style adaptation
- Context retention

**Use Cases:**
- Customer service
- Virtual assistants
- Community management
- User onboarding

---

### 2. research_preset.py - Research Assistant
**Demonstrates:**
- Web search integration
- Multi-source research
- Citation tracking
- Summary generation

```python
from kagura.presets import ResearchPreset

# Create research assistant
researcher = (
    ResearchPreset("research_bot")
    .with_model("gpt-4o")
    .with_web_search(provider="brave")  # or "duckduckgo"
    .with_context(
        depth="comprehensive",
        citation_style="APA"
    )
    .build()
)

# Research a topic
result = await researcher("Latest developments in quantum computing")
# → Returns summary with citations
```

**Built-in Features:**
- Web search (Brave/DuckDuckGo)
- Source verification
- Citation formatting
- Summary synthesis

**Use Cases:**
- Market research
- Academic research
- Competitive analysis
- News monitoring

---

### 3. code_review_preset.py - Code Reviewer
**Demonstrates:**
- Code analysis
- Bug detection
- Best practice suggestions
- Security review

```python
from kagura.presets import CodeReviewPreset

# Create code reviewer
reviewer = (
    CodeReviewPreset("code_reviewer")
    .with_model("claude-3-5-sonnet")  # Excellent for code
    .with_context(
        languages=["python", "javascript"],
        focus_areas=["security", "performance", "style"],
        strictness="medium"
    )
    .build()
)

# Review code
code = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item.price
    return total
"""

feedback = await reviewer(code)
# → Detailed review with suggestions
```

**Built-in Features:**
- Multi-language support
- Security analysis
- Performance tips
- Style checking

**Use Cases:**
- Pull request reviews
- Code quality checks
- Security audits
- Refactoring suggestions

---

### 4. translator_preset.py - Multi-language Translator
**Demonstrates:**
- High-quality translation
- Language detection
- Cultural context
- Formality levels

```python
from kagura.presets import TranslatorPreset

# Create translator
translator = (
    TranslatorPreset("translator")
    .with_model("gpt-4o")
    .with_context(
        source_language="auto",  # Auto-detect
        target_language="french",
        formality="formal",
        preserve_formatting=True
    )
    .build()
)

# Translate
result = await translator("Hello, how are you?")
# → "Bonjour, comment allez-vous ?"
```

**Built-in Features:**
- 100+ languages
- Auto-detection
- Context preservation
- Formality control

---

### 5. data_analyst_preset.py - Data Analysis
**Demonstrates:**
- Data analysis
- Statistical insights
- Visualization suggestions
- Report generation

```python
from kagura.presets import DataAnalystPreset

analyst = (
    DataAnalystPreset("analyst")
    .with_model("gpt-4o")
    .with_tools(["pandas", "matplotlib"])
    .build()
)

# Analyze data
data_summary = await analyst("""
Analyze this sales data:
Q1: $100k, Q2: $150k, Q3: $120k, Q4: $180k
""")
```

**Built-in Features:**
- Statistical analysis
- Trend identification
- Visualization hints
- Actionable insights

---

### 6. personal_assistant_preset.py - Task Management
**Demonstrates:**
- Task tracking
- Reminders
- Email drafting
- Schedule management

```python
from kagura.presets import PersonalAssistantPreset

assistant = (
    PersonalAssistantPreset("assistant")
    .with_memory(type="persistent")
    .with_context(user_name="Alice")
    .build()
)

# Manage tasks
await assistant("Add a task: Review Q3 report by Friday")
await assistant("What are my pending tasks?")
```

---

### 7. content_writer_preset.py - Content Generation
**Demonstrates:**
- Blog writing
- Social media posts
- SEO optimization
- Style adaptation

```python
from kagura.presets import ContentWriterPreset

writer = (
    ContentWriterPreset("writer")
    .with_model("gpt-4o")
    .with_context(
        content_type="blog",
        tone="professional",
        seo_optimization=True
    )
    .build()
)

# Generate content
article = await writer("Write a blog post about AI in healthcare")
```

---

### 8. technical_support_preset.py - Support Bot
**Demonstrates:**
- Issue diagnosis
- Solution suggestions
- Escalation handling
- Knowledge base integration

```python
from kagura.presets import TechnicalSupportPreset

support = (
    TechnicalSupportPreset("support_bot")
    .with_knowledge_base(path="./docs")
    .with_context(
        product="Kagura AI",
        escalation_trigger="complex_issue"
    )
    .build()
)

# Handle support query
response = await support("My agent is not responding")
```

---

### 9. learning_tutor_preset.py - Educational Tutor
**Demonstrates:**
- Personalized teaching
- Concept explanation
- Practice problems
- Progress tracking

```python
from kagura.presets import LearningTutorPreset

tutor = (
    LearningTutorPreset("tutor")
    .with_context(
        subject="Python programming",
        difficulty_level="beginner",
        teaching_style="interactive"
    )
    .build()
)

# Teach concept
explanation = await tutor("Explain what a function is")
```

---

### 10. project_manager_preset.py - Project Planning
**Demonstrates:**
- Task breakdown
- Timeline estimation
- Resource allocation
- Risk assessment

```python
from kagura.presets import ProjectManagerPreset

pm = (
    ProjectManagerPreset("pm")
    .with_context(
        methodology="agile",
        team_size=5
    )
    .build()
)

# Plan project
plan = await pm("Plan a web app development project")
```

---

## Prerequisites

```bash
# Install Kagura AI
pip install kagura-ai

# For presets with web search
pip install kagura-ai[web]

# For all features
pip install kagura-ai[all]
```

## Running Examples

```bash
# Run any preset example
python chatbot_preset.py
python research_preset.py
python code_review_preset.py
python translator_preset.py
python data_analyst_preset.py
python personal_assistant_preset.py
python content_writer_preset.py
python technical_support_preset.py
python learning_tutor_preset.py
python project_manager_preset.py
```

## Preset Comparison

| Preset | Memory | Tools | Web | Best For |
|--------|--------|-------|-----|----------|
| **Chatbot** | ✅ Yes | ❌ No | ❌ No | Conversations |
| **Research** | ✅ Yes | ✅ Yes | ✅ Yes | Information gathering |
| **CodeReview** | ❌ No | ✅ Yes | ❌ No | Code analysis |
| **Translator** | ❌ No | ❌ No | ❌ No | Translation |
| **DataAnalyst** | ❌ No | ✅ Yes | ❌ No | Data insights |
| **PersonalAssistant** | ✅ Yes | ✅ Yes | ✅ Yes | Task management |
| **ContentWriter** | ❌ No | ❌ No | ✅ Yes | Content creation |
| **TechnicalSupport** | ✅ Yes | ✅ Yes | ✅ Yes | Customer support |
| **LearningTutor** | ✅ Yes | ❌ No | ✅ Yes | Education |
| **ProjectManager** | ✅ Yes | ✅ Yes | ❌ No | Project planning |

## Common Patterns

### Pattern 1: Basic Preset Usage
```python
from kagura.presets import ChatbotPreset

# Minimal setup
chatbot = ChatbotPreset("bot").build()

# Use immediately
response = await chatbot("Hello!")
```

### Pattern 2: Customized Preset
```python
from kagura.presets import ResearchPreset

# Full customization
researcher = (
    ResearchPreset("researcher")
    .with_model("gpt-4o")
    .with_web_search(provider="brave", api_key="...")
    .with_memory(type="persistent", persist_dir="./memory")
    .with_context(
        depth="comprehensive",
        citation_style="APA",
        max_sources=10
    )
    .build()
)
```

### Pattern 3: Preset with Custom Tools
```python
from kagura import tool
from kagura.presets import DataAnalystPreset

@tool
def custom_analyzer(data: str) -> str:
    """Custom data analysis tool"""
    # Implementation
    pass

analyst = (
    DataAnalystPreset("analyst")
    .with_tools([custom_analyzer])
    .build()
)
```

### Pattern 4: Multi-Preset System
```python
from kagura.presets import ChatbotPreset, ResearchPreset
from kagura.routing import AgentRouter

# Create multiple presets
chatbot = ChatbotPreset("chat").build()
researcher = ResearchPreset("research").build()

# Route between them
router = AgentRouter()
router.register(chatbot, intents=["chat", "conversation"])
router.register(researcher, intents=["research", "information"])

# Use router
response = await router.route("Tell me about quantum computing")
```

## Best Practices

### 1. Choose the Right Preset

✅ **Good:**
```python
# Use specialized preset for task
from kagura.presets import CodeReviewPreset
reviewer = CodeReviewPreset("reviewer").build()
```

❌ **Bad:**
```python
# Use generic agent for specialized task
from kagura import agent
@agent
async def code_reviewer(code: str) -> str:
    """Review code..."""  # Missing optimizations
    pass
```

### 2. Customize Context Appropriately

```python
# ✅ Good: Specific context
chatbot = (
    ChatbotPreset("support_bot")
    .with_context(
        personality="professional and empathetic",
        domain="customer support",
        company="Acme Corp"
    )
    .build()
)

# ❌ Bad: Too vague
chatbot = ChatbotPreset("bot").build()  # Generic personality
```

### 3. Enable Memory When Needed

```python
# ✅ Good: Memory for conversations
chatbot = (
    ChatbotPreset("bot")
    .with_memory(type="context", max_messages=50)
    .build()
)

# ❌ Bad: No memory for chatbot
chatbot = ChatbotPreset("bot").build()  # Won't remember context
```

### 4. Use Appropriate Models

```python
# ✅ Good: Match model to task
code_reviewer = (
    CodeReviewPreset("reviewer")
    .with_model("claude-3-5-sonnet")  # Best for code
    .build()
)

translator = (
    TranslatorPreset("translator")
    .with_model("gpt-4o")  # Good for translation
    .build()
)

# ❌ Bad: Wrong model for task
code_reviewer = (
    CodeReviewPreset("reviewer")
    .with_model("gpt-3.5-turbo")  # Weaker for code
    .build()
)
```

## Creating Custom Presets

```python
from kagura import AgentBuilder
from kagura.presets import BasePreset

class CustomPreset(BasePreset):
    """Custom preset for specific use case"""

    def __init__(self, name: str):
        super().__init__(name)
        self.builder = (
            AgentBuilder(name)
            .with_model("gpt-4o-mini")
            .with_system_prompt(self._get_system_prompt())
        )

    def _get_system_prompt(self) -> str:
        return """
        You are a specialized assistant for...
        [Custom instructions]
        """

    def with_custom_feature(self, param: str):
        """Add custom configuration"""
        self.builder = self.builder.with_context(
            custom_param=param
        )
        return self

    def build(self):
        """Build the agent"""
        return self.builder.build()

# Use custom preset
custom_agent = (
    CustomPreset("my_agent")
    .with_custom_feature("value")
    .build()
)
```

## Advanced Customization

### Override Default Prompts
```python
from kagura.presets import ChatbotPreset

chatbot = (
    ChatbotPreset("custom_bot")
    .with_system_prompt("""
        You are a specialized chatbot for...
        [Custom instructions]
    """)
    .build()
)
```

### Add Multiple Tools
```python
from kagura.presets import ResearchPreset

researcher = (
    ResearchPreset("researcher")
    .with_tools([
        custom_search_tool,
        custom_scraper_tool,
        custom_analyzer_tool
    ])
    .build()
)
```

### Combine Features
```python
from kagura.presets import PersonalAssistantPreset

assistant = (
    PersonalAssistantPreset("assistant")
    .with_model("gpt-4o")
    .with_memory(type="persistent", persist_dir="./memory")
    .with_web_search(provider="brave")
    .with_tools([calendar_tool, email_tool])
    .with_context(
        user_name="Alice",
        timezone="UTC",
        language="en"
    )
    .build()
)
```

## Troubleshooting

### Issue: Preset not available
**Solution:** Check import and install extras:
```bash
pip install kagura-ai[all]
```

```python
from kagura.presets import ChatbotPreset  # ✅ Correct import
```

### Issue: Web search not working
**Solution:** Set API key:
```bash
export BRAVE_SEARCH_API_KEY="your-key"
```

```python
researcher = (
    ResearchPreset("researcher")
    .with_web_search(provider="brave")
    .build()
)
```

### Issue: Memory not persisting
**Solution:** Enable persistent memory:
```python
chatbot = (
    ChatbotPreset("bot")
    .with_memory(
        type="persistent",
        persist_dir=Path("./memory")
    )
    .build()
)
```

## Next Steps

After mastering presets, explore:
- [08_real_world](../08_real_world/) - Production examples with presets
- [01_basic](../01_basic/) - Build custom agents
- [06_advanced](../06_advanced/) - Advanced features

## Documentation

- [RFC-026: Extended Presets](../../ai_docs/rfcs/RFC_026_EXTENDED_PRESETS.md)
- [API Reference - Presets](../../docs/en/api/presets.md)
- [Preset Customization Guide](../../docs/en/guides/preset_customization.md)

---

**Presets provide the fastest path to production-ready AI agents. Start with a preset and customize as needed!**
