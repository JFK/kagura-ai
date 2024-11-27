# Quick Start

## Basic Usage

**Start Kagura AI Chatbot**:

To start the Kagura chatbot, use the following command:

```bash
kagura
```

During the chat session, you can use the following commands:

- `/help`: Show available commands and usage instructions.
- `/clear`: Clear the current chat history.
- `/history`: View the current chat history.

---

## Creating an Agent

### Step 1: Create Agent Directory

Create a directory for your agent configuration:
```bash
mkdir -p ~/.config/kagura/agents/my_agent
```

### Step 2: Define Basic Agent Configuration

Create an `agent.yml` file in the newly created directory:
```yaml
# ~/.config/kagura/agents/my_agent/agent.yml
llm:
  stream: true
skip_state_model: true  # must be set to true if response_fields is not defined or there is no state_model.yml
description:
  - language: en
    text: This is the default agent.
  - language: ja
    text: デフォルトのエージェントです。
instructions:
  - language: en
    description: |
      You will always respond in English.
  - language: ja
    description: |
      あたなたは、必ず日本語で返答します。
prompt:
  - language: en
    template: |
      {QUERY}
  - language: ja
    template: |
      {QUERY}
```

### Step 3: Use the Agent in Your Code

To interact with the agent programmatically, use the following Python code:

```python
from kagura.core.agent import Agent

async def chat():
    # Assign the created agent by its directory name
    agent = Agent.assigner("my_agent")
    # Send a query and stream the responses
    async for response in await agent.execute("Tell me about AI"):
        print(response, end="")

if __name__ == "__main__":
    import asyncio
    asyncio.run(chat())
```

### Expected Output

When you run the Python script, the agent will respond to your query, for example:
```plaintext
Artificial Intelligence (AI) refers to the simulation of human intelligence...
```

---

## Additional Tips

- **Configuration Options**: You can expand the `agent.yml` file to include more complex instructions, prompts, or language settings.
- **Testing**: Use `/history` and `/clear` commands during chatbot sessions to manage your interactions.
- **Documentation**: Refer to the [Agents Overview](agents/overview.md) for more details on customizing agents.

---

[AI Agents Overview →](agents/overview.md){: .md-button .md-button--primary }
