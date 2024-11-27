# System Configuration

Create `system.yml` in `~/.config/kagura/`:

```yaml
system:
  language: en
prompt:
  instructions:
    - language: en
      description: |
        Your name is Kagura.
        You will always respond in English.
    - language: ja
      description: |
        あなたの名前は、神楽（かぐら）です。
        あたなたは、必ず日本語で返答します。
memory:
  message_history:
    history_uuid: kagura_personal_chat
    window_size: 1000
    context_window: 20
    ttl_hours: 24
  backend:
    default_ttl_hours: 24
    cleanup_interval_hours: 1
llm:
  model: openai/gpt-4o-mini
  max_tokens: 4096
  retry_count: 3
backends:
 - name: redis
   host: localhost
   port: 6379
   db: 0

```

### Field Descriptions

**system**:

- `language`: Defines the default language for system instructions. Supported values include `en` (English) and `ja` (Japanese).

**prompt**:

- `instructions`: A list of language-specific instructions describing how the assistant should behave.
- `language`: Specifies the language of the instruction.
- `description`: Detailed instructions for the assistant's behavior.

**memory.message_history**:

- `history_uuid`: Unique identifier for the chat history.
- `window_size`: Number of messages to store in history.
- `context_window`: Number of messages to consider as context for responses.
- `ttl_hours`: Time-to-live for the chat history in hours.

**memory.backend**:

- `default_ttl_hours`: Default time-to-live for memory storage.
- `cleanup_interval_hours`: Interval in hours for cleaning up memory storage.

**llm**:

- `model`: The LLM model to use (e.g., `openai/gpt-4o-mini`).
- `max_tokens`: Maximum number of tokens the model can generate per response.
- `retry_count`: Number of retry attempts in case of model failure.

**backends**:

List of backend services for storage or processing.

- `name`: Name of the backend (e.g., `redis`).
- `host`: Host address of the backend.
- `port`: Port number for the backend service.
- `db`: Database index to use in the backend.


---

## Supported LLM Providers

Kagura supports multiple providers via LiteLLM:

- OpenAI (`openai/gpt-4`, `openai/gpt-3.5-turbo`)
- Anthropic (`anthropic/claude-3-opus`, `anthropic/claude-3-sonnet`)
- Ollama (`ollama/llama3.2`, `ollama/gemma2.5`)
- Google (`google/gemini-pro`)

For a complete list of supported providers, see the [LiteLLM Documentation](https://docs.litellm.ai/docs/providers).

---

## AI Agents Configuration

For a detailed explanation of agent-related settings, refer to the [AI Agents Overview](agents/overview.md):

---


[Quick Start →](quickstart.md){: .md-button .md-button--primary }
