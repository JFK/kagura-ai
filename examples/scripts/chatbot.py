from kagura.core.agent import Agent


async def chat():
    # Assign pre-defined agent
    agent = Agent.assigner("chat")

    # Send a query and stream the responses
    async for response in await agent.execute("Who are you?"):
        print(response, end="")

    print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(chat())
