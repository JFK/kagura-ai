from kagura.core.config import ConfigBase
from kagura.core.models import ModelRegistry, validate_required_state_fields

# Get custom model using ModelRegistry
StateModel = ModelRegistry.get("StateModel")


class ReadmeError(Exception):
    pass


async def readme(state: StateModel) -> StateModel:
    """
    Load README content and update state.
    Handles both English and Japanese README files.
    """
    validate_required_state_fields(state, ["readme"])
    try:
        # Load system language from config
        config = ConfigBase()

        # Load appropriate README content
        readme_content = config.agent_readme

        # Update state with README content
        state.readme = readme_content

        return state

    except Exception as e:
        raise ReadmeError(f"Failed to process README: {str(e)}")
