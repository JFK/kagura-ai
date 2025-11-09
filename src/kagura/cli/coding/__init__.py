"""Coding CLI commands - coding memory inspection."""

import click

from kagura.cli.coding import decisions, errors, sessions, utils


@click.group()
def coding():
    """Coding memory inspection commands.

    Query sessions, decisions, errors, and file changes from terminal.
    Useful for reviewing past work and restoring context.

    Examples:
        kagura coding projects
        kagura coding sessions --project kagura-ai
        kagura coding decisions --project kagura-ai --recent 10
        kagura coding errors --project kagura-ai --unresolved
        kagura coding search --project kagura-ai --query "authentication"
    """
    pass


# Register all commands
coding.add_command(sessions.projects)
coding.add_command(sessions.sessions_command, name="sessions")
coding.add_command(sessions.session_command, name="session")
coding.add_command(decisions.decisions_command, name="decisions")
coding.add_command(decisions.decision_command, name="decision")
coding.add_command(errors.errors_command, name="errors")
coding.add_command(errors.error_command, name="error")
coding.add_command(utils.search_command, name="search")
coding.add_command(utils.doctor_command, name="doctor")

__all__ = ["coding"]
