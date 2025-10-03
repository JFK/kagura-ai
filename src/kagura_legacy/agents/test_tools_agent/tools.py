from kagura.core.models import (
    StateModel,
    get_custom_model,
    validate_required_state_fields,
)


class ContentFetcherError(Exception):
    pass


async def fetch(state: StateModel) -> StateModel:
    ContentItem = get_custom_model("ContentItem")

    validate_required_state_fields(state, ["url"])

    try:
        state.content = ContentItem(
            text="Mocked content from URL.",
            content_type="webpage",
            url=state.url,
        )
        return state
    except Exception as e:
        raise ContentFetcherError(str(e))
