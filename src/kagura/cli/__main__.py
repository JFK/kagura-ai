import sys
from importlib.metadata import version
from typing import List

import click

from kagura.core.config import ConfigInitializer

from .commands import chat, create, install


def get_version():
    try:
        return version("kagura-ai")
    except Exception:
        return "unknown"


def get_zen() -> List[str]:
    """
    Returns Kagura's Zen principles - inspired by Python's Zen
    but focused on AI agent development and interaction.
    """
    return [
        "Harmony is better than discord.",
        "Explicit is better than implicit.",
        "Simple is better than complex.",
        "Complex is better than complicated.",
        "Composition is better than inheritance.",
        "YAML is better than JSON for human configuration.",
        "Types are better than any.",
        "Errors should never pass silently.",
        "Unless explicitly silenced.",
        "In the face of ambiguity, refuse the temptation to guess.",
        "There should be one-- and preferably only one --obvious way to do it.",
        "Although that way may not be obvious at first.",
        "Now is better than never.",
        "Although never is often better than *right* now.",
        "If the implementation is hard to explain, it's a bad idea.",
        "If the implementation is easy to explain, it may be a good idea.",
        "Agents should be one thing, rather than everything.",
        "Dependencies are both necessary and a liability.",
        "While reactivity matters, thoughtfulness is key.",
        "Although practicality beats purity.",
        "Errors should never fail to inform.",
        "In the face of many options, take the one most explicit.",
        "Unless that path is fraught with danger.",
        "Beautiful is better than ugly.",
        "Understanding is better than magic.",
        "Although black boxes are sometimes necessary.",
        "Agent composition should be intuitive.",
        "Even though agents can be complex.",
        "Simple tasks should be simple.",
        "Complex tasks should be possible.",
        "The present is more important than the past.",
        "The future is more important than the present.",
        "But the past holds lessons we shouldn't forget.",
    ]


def zen(return_str: bool = True) -> str:
    """
    Returns Kagura's Zen as a formatted string or list.

    Args:
        return_str: If True, returns a formatted string. If False, returns a list.
    """
    zen_list = get_zen()
    return "\n".join(zen_list)


@click.group(invoke_without_command=True)
@click.version_option(version=get_version())
@click.pass_context
def cli(ctx):
    ConfigInitializer().initialize()
    if ctx.invoked_subcommand is None:
        print("Welcome to Kagura AI!")
        print("Here are some of Kagura's Zen principles:")
        print("-" * 40)
        print(zen())


# Add the create command
cli.add_command(create)

# Add the install command
cli.add_command(install)

# Add the chat command
cli.add_command(chat)


def entry_point():
    """Entry point for the CLI application"""
    return cli()


if __name__ == "__main__":
    sys.exit(entry_point())
