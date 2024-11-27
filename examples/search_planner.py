from kagura.core.agent import Agent

async def arun():

    agent_name = "user_search_intent_extractor"
    user_query = "What is the best way to fine-tune the learning rate of an AI model?"
    state = {"user_query": user_query}
    user_intent_agent = Agent.assigner(agent_name, state)
    result = await user_intent_agent.execute()

    user_search_intents = result.model_dump()["user_search_intents"]
    print(user_search_intents)

    state = {"user_search_intents": user_search_intents}
    planner_agent = Agent.assigner("search_planner", state)
    search_plan = await planner_agent.execute()

    print(search_plan)

if __name__ == "__main__":
    import asyncio

    asyncio.run(arun())
