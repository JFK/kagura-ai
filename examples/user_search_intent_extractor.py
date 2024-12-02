from kagura.core.agent import Agent


async def arun():

    agent_name = "user_search_intent_extractor"
    user_query = "I am interested in Kagura(神楽)"

    agent = Agent.assigner(agent_name, {"user_query": user_query})
    result = await agent.execute()
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(arun())
