"""CLI command for user configuration setup"""

import subprocess
import sys

import click
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from kagura.config import ConfigManager, UserConfig


def _setup_rag_environment(console: Console) -> None:
    """Setup RAG environment interactively.

    Args:
        console: Rich console for output
    """
    console.print("\n")
    console.print(
        Panel(
            "[bold]RAG Environment Setup[/]\n\n"
            "This will:\n"
            "  1. Check dependencies (chromadb, sentence-transformers)\n"
            "  2. Download embedding model (~1.5 GB)\n"
            "  3. Build vector index from existing memories",
            style="blue",
        )
    )
    console.print()

    # Step 1: Check dependencies
    console.print("[bold cyan]Step 1/3: Checking dependencies...[/]")

    missing_deps = []
    try:
        import chromadb  # type: ignore # noqa: F401

        console.print("   [green]✓[/] chromadb: Installed")
    except ImportError:
        console.print("   [red]✗[/] chromadb: Not installed")
        missing_deps.append("chromadb")

    try:
        import sentence_transformers  # type: ignore # noqa: F401

        console.print("   [green]✓[/] sentence-transformers: Installed")
    except ImportError:
        console.print("   [red]✗[/] sentence-transformers: Not installed")
        missing_deps.append("sentence-transformers")

    if missing_deps:
        console.print()
        if click.confirm(
            f"Install missing packages: {', '.join(missing_deps)}?", default=True
        ):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Installing packages...", total=None)
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install"] + missing_deps,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    progress.update(task, completed=True)
                    console.print("   [green]✓[/] Packages installed")
                except subprocess.CalledProcessError as e:
                    console.print(f"   [red]✗[/] Installation failed: {e}")
                    return
        else:
            console.print("[yellow]Skipping RAG setup[/]")
            return

    console.print()

    # Step 2: Download embedding model
    from kagura.config.models import DEFAULT_EMBEDDING_MODEL

    console.print("[bold cyan]Step 2/3: Downloading embedding model...[/]")
    console.print(f"   Model: {DEFAULT_EMBEDDING_MODEL} (~1.5 GB)")
    console.print()

    if click.confirm("Download now?", default=True):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading model...", total=None)
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore

                _ = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
                progress.update(task, completed=True)
                console.print("   [green]✓[/] Model downloaded")
            except Exception as e:
                console.print(f"   [red]✗[/] Download failed: {e}")
                return
    else:
        console.print("[yellow]Skipping model download[/]")
        return

    console.print()

    # Step 3: Build index
    console.print("[bold cyan]Step 3/3: Building vector index...[/]")

    from kagura.core.memory import MemoryManager

    try:
        manager = MemoryManager(user_id="system", agent_name="setup")
        memory_count = manager.persistent.count()

        console.print(f"   Found {memory_count} memories in database")

        if memory_count > 0:
            if click.confirm("Build vector index now?", default=True):
                # Note: Index building logic would go here
                # This is a placeholder - actual implementation would iterate through memories
                console.print("   [yellow]⚠[/] Index building not yet implemented")
                console.print(
                    "   [dim]Run 'kagura memory index' manually after setup[/]"
                )
        else:
            console.print("   [dim]No memories to index yet[/]")
    except Exception as e:
        console.print(f"   [red]✗[/] Failed: {e}")

    console.print()
    console.print("[bold green]✅ RAG setup complete![/]")
    console.print()
    console.print("[bold]Next steps:[/]")
    console.print("  1. Test search: [cyan]kagura coding search --query 'test'[/]")
    console.print(
        "  2. Enable reranking (optional): [cyan]kagura init --setup-reranking[/]"
    )
    console.print(
        "  3. Set env vars: [cyan]export KAGURA_DEFAULT_PROJECT=your-project[/]"
    )
    console.print()


def _setup_reranking(console: Console) -> None:
    """Setup reranking model interactively.

    Args:
        console: Rich console for output
    """
    from kagura.config.models import DEFAULT_RERANKING_MODEL

    console.print("\n")
    console.print(
        Panel(
            "[bold]Reranking Model Setup[/]\n\n"
            "This will download the cross-encoder reranking model\n"
            "to improve search quality (highly recommended).\n\n"
            f"Model: {DEFAULT_RERANKING_MODEL} (~80 MB)",
            style="blue",
        )
    )
    console.print()

    # Check sentence-transformers
    try:
        import sentence_transformers  # type: ignore # noqa: F401
    except ImportError:
        console.print("[red]✗[/] sentence-transformers not installed")
        console.print("   Install with: [cyan]pip install sentence-transformers[/]")
        return

    if click.confirm("Download reranking model?", default=True):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading model...", total=None)
            try:
                from sentence_transformers import CrossEncoder  # type: ignore

                _ = CrossEncoder(DEFAULT_RERANKING_MODEL)
                progress.update(task, completed=True)
                console.print("   [green]✓[/] Model downloaded")
            except Exception as e:
                console.print(f"   [red]✗[/] Download failed: {e}")
                return
    else:
        console.print("[yellow]Skipping model download[/]")
        return

    console.print()
    console.print("[bold green]✅ Reranking setup complete![/]")
    console.print()
    console.print("[bold]To enable reranking:[/]")
    console.print("  [cyan]export KAGURA_ENABLE_RERANKING=true[/]")
    console.print()
    console.print("[dim]Add this to your .bashrc or .zshrc to make it permanent[/]")
    console.print()


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
@click.option(
    "--setup-rag",
    is_flag=True,
    help="Setup RAG environment (download models and build index)",
)
@click.option(
    "--setup-reranking",
    is_flag=True,
    help="Setup reranking model for improved search quality",
)
@click.option(
    "--full",
    is_flag=True,
    help="Full setup (user config + RAG + reranking)",
)
def init(reset: bool, setup_rag: bool, setup_reranking: bool, full: bool) -> None:
    """
    Interactive setup for user preferences and RAG environment.

    Saves configuration to ~/.kagura/config.json for personalized
    responses from Personal Tools (news, weather, recipes, events).

    Supports full multibyte character input (Japanese, Chinese, etc.)
    with proper backspace handling.

    Examples:

        # First-time setup (user preferences only)
        kagura init

        # Setup RAG environment
        kagura init --setup-rag

        # Setup reranking model
        kagura init --setup-reranking

        # Full setup (everything)
        kagura init --full

        # Reset to defaults
        kagura init --reset
    """
    console = Console()
    manager = ConfigManager()

    if reset:
        manager.reset()
        console.print("[green]✓ Config reset to defaults[/]")
        return

    # Handle --full flag
    if full:
        setup_rag = True
        setup_reranking = True

    # Handle RAG setup
    if setup_rag:
        _setup_rag_environment(console)
        if not setup_reranking:
            return

    # Handle reranking setup
    if setup_reranking:
        _setup_reranking(console)
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
