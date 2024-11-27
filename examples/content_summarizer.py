from typing import Any, Dict, Union

from kagura.core.agent import Agent
from kagura.core.utils.console import KaguraConsole


async def arun(agent_name: str, state: Dict[str, Any]):

    agent = Agent.assigner(agent_name, state)

    if agent.is_workflow:
        console = KaguraConsole()
        async for update in await agent.execute():
            console.print_data_table(update)

    else:
        print(f"{agent_name} is not a workflow agent")


if __name__ == "__main__":
    import asyncio

    agent_name = "content_summarizer"
    state = {
        "url": "https://github.com"
    }
    asyncio.run(arun(agent_name, state))
