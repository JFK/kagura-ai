### Kagura AI Agent Documentation

---

## Overview

Kagura provides four agent patterns to build complex AI systems.

---

### Basic Agent Structure

```
agents/
└── agent_name/
    ├── agent.yml         # Agent configuration
    ├── state_model.yml   # State model (optional)
    └── tools/            # Custom tools (optional)
        ├── __init__.py
        └── tool.py
```

---

## Agent Types

### 1. Simple Gen Response Agent

- Basic conversational agent
- No state management
- Ideal for chatbots
- Example:

```yaml
llm_stream: true
skip_state_model: true
description:
  - language: en
    text: Simple chat agent
instructions:
  - language: en
    text: |
      You are a conversational assistant.
prompt:
  - language: en
    template: "{QUERY}"
llm_model: openai/gpt-4
```

### 2. GenAI Agent

- Stateful LLM agent
- Structured responses
- Content analysis/generation
- Type-safe state management

### 3. Function Agent

- Non-LLM functional agent
- Data processing focus
- Fast execution
- Error handling

### 4. Orchestrator Agent

- Multi-agent control
- Conditional flows
- State binding
- Error recovery

---

## Core Features

### State Management

- **Pydantic** model type safety
- Inter-agent state sharing
- Redis persistence
- Complex data structures

### Workflow Control

- Conditional routing
- Error handling
- Retry mechanisms
- Pre/post hooks

### Tool Integration

- Custom functionality
- External API integration
- Batch processing
- Async operations

---

## Design Principles

1. **Single Responsibility**
   - Clear agent roles
   - Function separation
   - Reusable components

2. **Type Safety**
   - Strict type checking
   - Validation
   - Error detection

3. **Modularity**
   - Independent components
   - Flexible combination
   - Maintainability

---

## Best Practices

### Agent Design

1. **Clear Responsibilities**
2. **Appropriate Granularity**
3. **Error Handling**

### State Models

1. **Clear Type Definitions**
2. **Minimal State**
3. **Proper Defaults**

### Workflows

1. **Error Recovery Paths**
2. **Monitoring Points**
3. **Scalability Consideration**

---

## Core Agent Patterns

Kagura supports four fundamental agent patterns:

### 1. Simple Gen Response Agent

The most basic pattern for direct LLM interactions without state management.

```yaml
# agent.yml
llm_stream: true
skip_state_model: true
description:
  - language: en
    text: Simple chat agent
instructions:
  - language: en
    text: |
      You are a helpful assistant.
prompt:
  - language: en
    template: "{QUERY}"
llm_model: openai/gpt-4o-mini  # Any LiteLLM supported model
```

**Directory Structure:**
```
agents/
└── simple_chat/
    └── agent.yml  # skip_state_model: true
```

**Example usage:**
```python
from kagura.core.agent import Agent

async def run_simple_chat():
    agent = Agent.assigner("simple_chat")
    async for c in await agent.execute("Tell me about AI"):
        print(c, end="")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_simple_chat())
```

**Key Characteristics:**
- Minimal configuration
- No state model required
- Direct query-response pattern
- Ideal for simple chatbots

---

### 2. GenAI Agent

Stateful agent with structured LLM responses.

```yaml
# agent.yml
description:
  - language: en
    text: Content analysis agent
instructions:
  - language: en
    text: |
      Analyze content and provide structured insights.
prompt:
  - language: en
    template: |
      Analyze the following content and provide structured insights:
      {content}
response_fields:
  - analysis
  - key_points
llm_model: anthropic/claude-3-opus
llm_max_tokens: 4096
llm_retry_count: 3

# state_model.yml
custom_models:
  - name: Analysis
    fields:
      - name: summary
        type: str
        description:
          - language: en
            text: Concise summary of the analysis
      - name: key_points
        type: List[str]
        description:
          - language: en
            text: Key insights extracted from content
      - name: sentiment
        type: float
        description:
          - language: en
            text: Sentiment score (-1.0 to 1.0)

state_fields:
  - name: content
    type: str
  - name: analysis
    type: Analysis
```

**Directory Structure:**
```
agents/
└── content_analyzer/
    ├── agent.yml           # LLM configuration & response_fields
    └── state_model.yml     # Custom models & state fields
```

**Example usage:**
```python
from kagura.core.agent import Agent
from kagura.core.models import ModelRegistry

Analysis = ModelRegistry.get("Analysis")

async def summarizer():
    state = {
        "content": """
        AI technology has seen rapid advancement in recent years.
        Machine learning models are becoming more sophisticated.
        """
    }

    agent = Agent.assigner("content_analyzer", state)
    result = await agent.execute()

    if result.ERROR_MESSAGE:
        print(f"Error: {result.ERROR_MESSAGE}")
    else:
        print(f"Result: {result.analysis.summary}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(summarizer())
```

**Key Characteristics:**
- Structured state management
- Type-safe responses
- Complex data modeling
- Retry mechanism for reliability

---

### 3. Function Agent

Pure function execution without LLM interaction.

```yaml
# agent.yml
description:
  - language: en
    text: Content fetching agent
skip_llm_invoke: true
custom_tool: kagura.agents.fetcher.tools.fetch

# state_model.yml
custom_models:
  - name: ContentItem
    fields:
      - name: text
        type: str
      - name: content_type
        type: str
      - name: metadata
        type: Dict[str, Any]

state_fields:
  - name: url
    type: str
  - name: content
    type: ContentItem
```

**Directory Structure:**
```
agents/
└── content_fetcher/
    ├── agent.yml           # skip_llm_invoke: true
    ├── state_model.yml     # State definition
    └── tools/
        ├── __init__.py     # Exports fetch
        └── fetch.py        # Implementation
```

**Example usage:**
```python
from kagura.core.agent import Agent

async def run_fetcher():
    state = {"url": "https://example.com"}

    agent = Agent.assigner("content_fetcher", state)
    result = await agent.execute()

    if result.ERROR_MESSAGE:
        print(f"Error: {result.ERROR_MESSAGE}")
    else:
        print(f"Content type: {result.content.content_type}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_fetcher())
```

**Implementation example:**
```python
from kagura.core.models import ModelRegistry, validate_required_state_fields

ContentItem = ModelRegistry.get("ContentItem")

class FetcherError(Exception):
    pass

class Fetcher:
    """Fetcher tool implementation"""
    async def fetch(self, url: str) -> tuple:
        # Implementation for fetching content from the URL
        pass

    @classmethod
    def get_instance(cls):
        return cls()

async def extract_metadata(content: str) -> Dict[str, Any]:
    # Implementation for extracting metadata from content
    pass

async def fetch(state: StateModel) -> StateModel:
    """
    Fetches and processes content from a URL.

    Args:
        state: State model containing url field

    Returns:
        Updated state with content field

    Raises:
        FetcherError: On fetch or processing failure
    """
    try:
        validate_required_state_fields(state, ["url"])

        fetcher = Fetcher.get_instance()
        content, content_type = await fetcher.fetch(state.url)
        metadata = await extract_metadata(content)

        state.content = ContentItem(
            text=content,
            content_type=content_type,
            metadata=metadata
        )
        return state

    except Exception as e:
        raise FetcherError(f"Fetch failed: {str(e)}")
```

**Key Characteristics:**
- Pure function execution without LLM
- Fast data processing
- External API integration
- Error handling implementation

---

### 4. Orchestrator Agent

Coordinates multiple agents in complex workflows.

```yaml
# agent.yml
description:
  - language: en
    text: Content analysis workflow orchestrator
entry_point: content_fetcher
nodes:
  - content_fetcher    # Function Agent
  - text_processor     # Function Agent
  - sentiment_analyzer # GenAI Agent
  - summarizer         # GenAI Agent

edges:
  - from: content_fetcher
    to: text_processor
  - from: text_processor
    to: sentiment_analyzer
  - from: sentiment_analyzer
    to: summarizer

state_field_bindings:
  - from: content_fetcher.content.text
    to: text_processor.raw_text
  - from: text_processor.processed_text
    to: sentiment_analyzer.input.text
  - from: sentiment_analyzer.sentiment
    to: summarizer.context.sentiment

conditional_edges:
  text_processor:
    condition_function: kagura.agents.workflow.tools.check_processing
    conditions:
      success: sentiment_analyzer
      retry: text_processor
      error: error_handler
```

**Condition function example:**
```python
async def check_processing(state: StateModel) -> str:
    if not state.processed_text:
        return "error"
    if len(state.processed_text) < 10:
        return "retry"
    return "success"
```

**Example usage:**
```python
from kagura.core.agent import Agent
from kagura.core.utils.console import KaguraConsole


async def run_summarizer():
    console = KaguraConsole()
    state = {"url": "https://bbc.com"}
    agent_name = "content_summarizer"

    agent = Agent.assigner(agent_name, state)
    if agent.is_workflow:
        async for update in await agent.execute():
            console.print_data_table(update)

    else:
        print("Error: Agent is not a workflow")
        print(f"agent.is_workflow: {agent.is_workflow}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_summarizer())
```

**Directory Structure:**
```
agents/
└── content_workflow/
    ├── agent.yml           # nodes, edges, bindings
    └── tools/
        ├── __init__.py     # Exports condition functions
        └── conditions.py   # Edge conditions implementation
```

**Key Characteristics:**
- Multi-agent coordination
- Conditional workflow paths
- State binding between agents
- Error handling and retries

---

## State Management

### State Model Definition

```yaml
# state_model.yml
custom_models:
  - name: ProcessedContent
    fields:
      - name: text
        type: str
        description:
          - language: en
            text: Processed text content
      - name: metadata
        type: Dict[str, Any]
        description:
          - language: en
            text: Processing metadata
      - name: stats
        type: Dict[str, float]
        description:
          - language: en
            text: Processing statistics

state_fields:
  # Local fields
  - name: raw_content
    type: str

  # Reused fields from other agents
  - agent_name: content_fetcher
    state_field_name: url

  - name: processed
    type: ProcessedContent
```

### State Field Bindings

**Simple binding:**
```yaml
state_field_bindings:
  - from: source_agent.output
    to: target_agent.input
```

**Nested field binding:**
```yaml
state_field_bindings:
  - from: analyzer.results.sentiment
    to: summarizer.context.mood
```

**List field binding:**
```yaml
state_field_bindings:
  - from: extractor.keywords
    to: searcher.query.terms
```

---

## Advanced Features

### Tool Lifecycle Hooks

```yaml
# agent.yml
pre_custom_tool: kagura.tools.preprocess
post_custom_tool: kagura.tools.postprocess
custom_tool: kagura.tools.main_process  # Alias for post_custom_tool
```

**Execution order:**
1. `pre_custom_tool`: Before LLM invocation
2. LLM processing (if enabled)
3. `post_custom_tool`/`custom_tool`: After LLM invocation

### Error Handling

**System-level retry:**
```yaml
# system.yml
llm:
  retry_count: 3
  max_tokens: 4096
```

**Agent-level retry:**
```yaml
# agent.yml
llm_retry_count: 5
```

**Custom tool error handling:**
```python
class ProcessingError(Exception):
    pass

async def process(state: StateModel) -> StateModel:
    try:
        validate_required_state_fields(state, ["input"])
        # Processing logic
        return state
    except ValueError as e:
        raise ProcessingError(f"Invalid input: {str(e)}")
    except Exception as e:
        raise ProcessingError(f"Processing failed: {str(e)}")
```

### Memory System

**Redis configuration:**
```yaml
# system.yml
backends:
 - name: redis
   host: localhost
   port: 6379
   db: 0

memory:
  message_history:
    window_size: 1000
    context_window: 20
    ttl_hours: 24
```

---

## Common Use Cases

### 1. Content Processing Pipeline

```yaml
nodes:
  - url_fetcher      # Function Agent: Fetches content
  - text_extractor   # Function Agent: Extracts text
  - classifier       # GenAI Agent: Classifies content
  - summarizer       # GenAI Agent: Generates summary
  - translator       # GenAI Agent: Translates if needed
```

### 2. Interactive Assistant

```yaml
nodes:
  - intent_classifier # GenAI Agent: Understands user intent
  - tool_selector    # Function Agent: Selects appropriate tool
  - executor         # Dynamic: Based on selected tool
  - response_gen     # Simple Gen Response: Formats response
```

### 3. Research Assistant

```yaml
nodes:
  - query_analyzer    # GenAI Agent: Analyzes research query
  - search_executor   # Function Agent: Performs search
  - content_fetcher   # Function Agent: Fetches results
  - synthesizer       # GenAI Agent: Synthesizes information
  - citation_manager  # Function Agent: Manages citations
```

---

## Implementation Best Practices

### Agent Design Principles

1. **Single Responsibility**

```yaml
# Good: Focused agent
description:
  - language: en
    text: Content fetcher agent
custom_tool: kagura.tools.fetch

# Avoid: Mixed responsibilities
description:
  - language: en
    text: Fetch and analyze content
custom_tool: kagura.tools.fetch_and_analyze
```

2. **State Model Design**

```yaml
# Good: Clear model structure
custom_models:
  - name: SearchResult
    fields:
      - name: title
        type: str
      - name: url
        type: str
      - name: relevance
        type: float

# Avoid: Ambiguous types
custom_models:
  - name: Result
    fields:
      - name: data
        type: Any
```

3. **Error Handling Strategy**

```python
class ContentError(Exception):
    """Base error for content operations"""
    pass

class FetchError(ContentError):
    """Content fetch specific error"""
    pass

class ProcessError(ContentError):
    """Processing specific error"""
    pass

async def fetch_content(state: StateModel) -> StateModel:
    validate_required_state_fields(state, ["url"])
    try:
        response = await make_request(state.url)
        state.content = process_response(response)
        return state
    except RequestError as e:
        raise FetchError(f"Failed to fetch: {str(e)}")
    except ProcessingError as e:
        raise ProcessError(f"Failed to process: {str(e)}")
```

### Workflow Design Patterns

1. **Linear Processing**

```yaml
nodes:
  - fetcher
  - processor
  - analyzer
edges:
  - from: fetcher
    to: processor
  - from: processor
    to: analyzer
```

2. **Branching Logic**

```yaml
conditional_edges:
  content_classifier:
    condition_function: check_content_type
    conditions:
      text: text_processor
      image: image_processor
      video: video_processor
      error: error_handler

state_field_bindings:
  - from: classifier.content_type
    to: processor.input_type
  - from: classifier.content
    to: processor.raw_content
```

3. **Error Recovery**

```yaml
nodes:
  - main_processor
  - error_handler
  - cleanup
  - retry_manager

conditional_edges:
  main_processor:
    condition_function: check_processing_status
    conditions:
      success: next_step
      retry: retry_manager
      error: error_handler
      cleanup_needed: cleanup
```

---

## Configuration Management

### Environment-Specific Configuration

```yaml
# system.yml
system:
  environment: ${KAGURA_ENV:-development}

llm:
  model: ${LLM_MODEL:-openai/gpt-4}
  max_tokens: ${MAX_TOKENS:-4096}

backends:
  - name: redis
    host: ${REDIS_HOST:-localhost}
    port: ${REDIS_PORT:-6379}
```
