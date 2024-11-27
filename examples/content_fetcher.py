from typing import Any, Dict, Union

from kagura.core.agent import Agent
from kagura.core.utils.console import KaguraConsole
from kagura.core.models import StateModel


async def arun(agent_name: str, state: Dict[str, Any]):

    agent = Agent.assigner(agent_name, state)
    result = await agent.execute()

    console = KaguraConsole()
    console.print_data_table(result.model_dump())


if __name__ == "__main__":
    import asyncio

    agent_name = "content_fetcher"
    state = {
        "url": "https://github.com/"
    }
    asyncio.run(arun(agent_name, state))
