from typing import Any, Dict

from kagura.core.agent import Agent
from kagura.core.utils.console import KaguraConsole


async def arun(agent_name: str, state: Dict[str, Any]):
    agent = Agent.assigner(agent_name, state)
    result = await agent.execute()

    console = KaguraConsole()
    console.print_data_table(result.model_dump())

    print("Summary:")
    print(result.summary)


if __name__ == "__main__":
    import asyncio

    text = """
# Kagura AI

Kagura is a powerful yet simple AI agent framework that enables you to build, configure, and orchestrate AI agents using YAML files. Its design philosophy emphasizes flexibility and modularity while maintaining ease of use.

## Core Concepts

### LLM Integration
Kagura uses LiteLLM for model integration, supporting a wide range of AI models:
- OpenAI (e.g., `openai/gpt-4o-mini`, `openai/gpt-3.5-turbo`)
- Anthropic (e.g., `anthropic/claude-3-opus`, `anthropic/claude-3-sonnet`)
- Ollama (e.g., `ollama/llama3.2`, `ollama/gemma2.5`)
- Google (e.g., `google/gemini-pro`)
- Many others
    """

    agent_name = "summarizer"
    state = {
        "content": {
            "text": text,
        }
    }
    asyncio.run(arun(agent_name, state))
