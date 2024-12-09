from kagura.core.models import StateModel


async def pre_process(state: StateModel) -> StateModel:
    return state


async def post_process(state: StateModel) -> StateModel:
    return state
