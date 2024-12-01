# Coding Examples

This guide provides practical coding examples for Kagura AI. Each example demonstrates a specific use case and includes complete, runnable code with detailed comments.

## 1. Basic Chat Agent Example

Simple example of creating a chat interaction with Kagura AI.

```python
from kagura.core.agent import Agent

async def chat():
    # Initialize the default chat agent
    # This uses the configuration from ~/.config/kagura/agents/chat/
    agent = Agent.assigner("chat")

    # Execute the agent with a query and stream the response
    # Streaming allows real-time display of the agent's response
    async for response in await agent.execute("Who are you?"):
        print(response, end="")  # Print each chunk of the response as it arrives

    print()  # Add a newline after completion

if __name__ == "__main__":
    import asyncio
    # Run the async function in the event loop
    asyncio.run(chat())
```

## 2. Content Fetching Example

Example of fetching content from a URL using the content fetcher agent.

```python
from kagura.core.agent import Agent
from kagura.core.utils.console import KaguraConsole
from kagura.core.models import StateModel

async def arun(agent_name: str, state: Dict[str, Any]):
    # Initialize the content fetcher agent with the given state
    # The state must include a 'url' field for the content source
    agent = Agent.assigner(agent_name, state)
    
    # Execute the agent to fetch the content
    # The agent will handle URL validation and content retrieval
    result = await agent.execute()

    # Initialize the console for pretty printing
    # KaguraConsole provides formatted output for better readability
    console = KaguraConsole()
    
    # Display the result in a formatted table
    # model_dump() converts the Pydantic model to a dictionary
    console.print_data_table(result.model_dump())

if __name__ == "__main__":
    import asyncio

    # Specify the agent and initial state
    agent_name = "content_fetcher"
    state = {
        "url": "https://github.com/"  # URL to fetch content from
    }
    # Run the async function
    asyncio.run(arun(agent_name, state))
```

## 3. Content Summarization Example

Example of summarizing text content using the summarizer agent.

```python
from kagura.core.agent import Agent
from kagura.core.utils.console import KaguraConsole

async def arun(agent_name: str, state: Dict[str, Any]):
    # Initialize the summarizer agent with the input text
    # The state must include content.text field with the text to summarize
    agent = Agent.assigner(agent_name, state)
    
    # Execute the agent to generate the summary
    # The agent will process the text and create a concise summary
    result = await agent.execute()

    # Initialize the console for formatted output
    console = KaguraConsole()
    
    # Display the full result including metadata
    console.print_data_table(result.model_dump())

    # Print the generated summary separately for clarity
    print("Summary:")
    print(result.summary)

if __name__ == "__main__":
    import asyncio

    # Sample text to summarize
    text = """
    # Kagura AI
    Kagura is a powerful yet simple AI agent framework that enables you to build, 
    configure, and orchestrate AI agents using YAML files...
    """

    # Configure the agent and state
    agent_name = "summarizer"
    state = {
        "content": {
            "text": text,  # Text to be summarized
        }
    }
    # Run the async function
    asyncio.run(arun(agent_name, state))
```

## 4. Search Intent Analysis Example

Example of analyzing search intents and creating search plans.

```python
from kagura.core.agent import Agent

async def arun():
    # Configure the search intent extractor
    agent_name = "user_search_intent_extractor"
    user_query = "What is the best way to fine-tune the learning rate of an AI model?"
    
    # Initialize state with the user's query
    state = {"user_query": user_query}
    
    # Extract search intents from the query
    # This agent analyzes the query to understand user's search intentions
    user_intent_agent = Agent.assigner(agent_name, state)
    result = await user_intent_agent.execute()

    # Extract the search intents from the result
    user_search_intents = result.model_dump()["user_search_intents"]
    print(user_search_intents)

    # Create a search plan based on the extracted intents
    # The planner agent will create a structured plan for the search
    state = {"user_search_intents": user_search_intents}
    planner_agent = Agent.assigner("search_planner", state)
    search_plan = await planner_agent.execute()

    # Display the generated search plan
    print(search_plan)

if __name__ == "__main__":
    import asyncio
    # Run the async function
    asyncio.run(arun())
```

## 5. Workflow Integration Example

Example of using a workflow that combines multiple agents.

```python
from kagura.core.agent import Agent
from kagura.core.utils.console import KaguraConsole

async def arun(agent_name: str, state: Dict[str, Any]):
    # Initialize the workflow agent
    # This agent coordinates multiple sub-agents in a defined workflow
    agent = Agent.assigner(agent_name, state)

    # Check if the agent is configured as a workflow
    if agent.is_workflow:
        # Initialize console for progress display
        console = KaguraConsole()
        
        # Execute the workflow and display updates
        # The workflow will process through multiple stages
        async for update in await agent.execute():
            # Display the state update after each step
            console.print_data_table(update)
    else:
        # Warn if the agent is not a workflow
        print(f"{agent_name} is not a workflow agent")

if __name__ == "__main__":
    import asyncio

    # Configure the workflow
    agent_name = "content_summarizer"  # This workflow fetches and summarizes content
    state = {
        "url": "https://github.com"  # Starting URL for the workflow
    }
    # Run the async function
    asyncio.run(arun(agent_name, state))
```

Each example is a complete, standalone script that you can run directly. The comments explain what each part of the code does and why. Make sure you have Kagura AI properly installed and configured before running these examples. For more detailed information about each agent type and their configurations, refer to the full documentation.
