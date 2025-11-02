"""CLI command for user configuration setup"""

import click
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.panel import Panel

from kagura.config import ConfigManager, UserConfig


def prompt_with_default(session: PromptSession, message: str, default: str = "") -> str:
    """Prompt user with default value support

    Args:
        session: PromptSession instance
        message: Prompt message
        default: Default value

    Returns:
        User input or default
    """

    # Show default in prompt
    if default:
        display_msg = f"{message} [{default}]: "
    else:
        display_msg = f"{message}: "

    # Use sync version for compatibility with click
    try:
        result = session.prompt(display_msg)
        return result.strip() if result.strip() else default
    except (KeyboardInterrupt, EOFError):
        return default


@click.command()
@click.option(
    "--reset",
    is_flag=True,
    help="Reset config to defaults",
)
def init(reset: bool) -> None:
    """
    Interactive setup for user preferences.

    Saves configuration to ~/.kagura/config.json for personalized
    responses from Personal Tools (news, weather, recipes, events).

    Supports full multibyte character input (Japanese, Chinese, etc.)
    with proper backspace handling.

    Examples:

        # First-time setup
        kagura init

        # Reset to defaults
        kagura init --reset
    """
    console = Console()
    manager = ConfigManager()

    if reset:
        manager.reset()
        console.print("[green]✓ Config reset to defaults[/]")
        return

    # Welcome message
    welcome = Panel(
        "[bold green]Welcome to Kagura AI Setup![/]\n\n"
        "Let's personalize your experience with Kagura AI.\n"
        "This information will be used by Personal Tools to provide\n"
        "better, more relevant responses.\n\n"
        "[dim]All fields are optional - press Enter to skip\n"
        "Multibyte characters (日本語, 中文, etc.) fully supported![/]",
        title="Kagura Init",
        border_style="green",
    )
    console.print(welcome)
    console.print("")

    # Create prompt session for multibyte support
    session: PromptSession[str] = PromptSession()

    # Load existing config
    existing = manager.get()

    # Collect user information
    console.print("[bold cyan]📋 Basic Information[/]")

    name = prompt_with_default(
        session, "👤 Your name", default=existing.name if existing.name else ""
    )

    location = prompt_with_default(
        session,
        "📍 Default location (city or region)",
        default=existing.location if existing.location else "",
    )

    # Language selection
    console.print("\n[bold cyan]🌐 Language Preferences[/]")
    language_choices = {
        "1": ("en", "English"),
        "2": ("ja", "Japanese (日本語)"),
        "3": ("zh", "Chinese (中文)"),
        "4": ("es", "Spanish (Español)"),
    }

    console.print("\nSelect your preferred language:")
    for key, (code, label) in language_choices.items():
        marker = " ✓" if existing.language == code else ""
        console.print(f"  {key}. {label}{marker}")

    # Use click.prompt for simple choice (numbers only, no multibyte issue)
    lang_choice = click.prompt(
        "\nChoice",
        type=click.Choice(list(language_choices.keys())),
        default="1" if existing.language == "en" else "2",
    )
    language = language_choices[lang_choice][0]

    # News topics
    console.print("\n[bold cyan]📰 News Preferences[/]")
    console.print(
        "[dim]Enter topics separated by commas (e.g., Technology, AI, Startups)[/]"
    )

    existing_topics = ", ".join(existing.news_topics) if existing.news_topics else ""
    news_topics_str = prompt_with_default(
        session,
        "Topics of interest",
        default=existing_topics if existing_topics else "Technology",
    )
    news_topics = [t.strip() for t in news_topics_str.split(",") if t.strip()]

    # Cuisine preferences
    console.print("\n[bold cyan]🍳 Cuisine Preferences[/]")
    console.print(
        "[dim]Enter cuisines separated by commas (e.g., Japanese, Italian, Thai)[/]"
    )

    existing_cuisines = (
        ", ".join(existing.cuisine_prefs) if existing.cuisine_prefs else ""
    )
    cuisine_str = prompt_with_default(
        session,
        "Preferred cuisines",
        default=existing_cuisines if existing_cuisines else "",
    )
    cuisine_prefs = [c.strip() for c in cuisine_str.split(",") if c.strip()]

    # Create config
    config = UserConfig(
        name=name,
        location=location,
        language=language,
        news_topics=news_topics,
        cuisine_prefs=cuisine_prefs,
    )

    # Save
    manager.save(config)

    # Show summary
    console.print("\n" + "=" * 60)
    console.print("[bold green]✓ Configuration saved![/]\n")

    # Format cuisines display
    cuisines_display = (
        ", ".join(config.cuisine_prefs) if config.cuisine_prefs else "[dim](none)[/]"
    )

    summary = f"""[cyan]Location:[/] {manager.config_path}

[bold]Your Preferences:[/]
  👤 Name: {config.name or "[dim](not set)[/]"}
  📍 Location: {config.location or "[dim](not set)[/]"}
  🌐 Language: {config.language}
  📰 News topics: {", ".join(config.news_topics)}
  🍳 Cuisines: {cuisines_display}
"""

    console.print(Panel(summary, title="Saved Configuration", border_style="green"))

    # Tips
    console.print("\n[bold cyan]💡 What's next?[/]\n")
    console.print("Try these commands in [cyan]kagura chat[/]:")
    console.print("  • '天気は？' - Uses your default location automatically")
    console.print("  • 'ニュース' - Shows news from your preferred topics")
    console.print("  • 'レシピ' - Suggests recipes matching your cuisine preferences\n")
    console.print("[dim]To update your config, run [cyan]kagura init[/] again.[/]")
