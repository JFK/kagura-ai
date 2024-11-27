import os

from aiohttp import ClientSession

from kagura.core.models import ModelRegistry, validate_required_state_fields

StateModel = ModelRegistry.get("StateModel")
GoogleSearchResult = ModelRegistry.get("GoogleSearchResult")

BASE_URL = "https://www.googleapis.com/customsearch/v1"
API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")
NUM_RESULTS = os.getenv("GOOGLE_SEARCH_NUM_RESULTS", 5)


class GoogleSearcherException(Exception):
    pass


async def search(state: StateModel) -> StateModel:

    validate_required_state_fields(state, ["query", "google_search_results"])
    try:
        if not API_KEY or not CSE_ID:
            raise ValueError(
                "The environment variables: GOOGLE_SEARCH_API_KEY and GOOGLE_CSE_ID are required."
            )

        async with ClientSession() as session:
            params = {
                "q": state.query,
                "cx": CSE_ID,
                "key": API_KEY,
                "num": NUM_RESULTS,
            }

            state.google_search_results = []
            async with session.get(BASE_URL, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    for item in result.get("items", {}):
                        state.google_search_results.append(
                            GoogleSearchResult(
                                title=item["title"],
                                snippet=item["snippet"],
                                link=item["link"],
                            )
                        )
                    return state

                else:
                    error_text = await response.text()
                    raise GoogleSearcherException(
                        f"Google Search API Error: {response.status} - {error_text}"
                    )
    except Exception as e:
        raise GoogleSearcherException(str(e))
