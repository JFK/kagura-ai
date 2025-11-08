"""Configuration management CLI for Kagura AI.

Provides commands for setting up, validating, and testing configuration.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import click

from kagura.cli.utils import (
    create_console,
    create_success_panel,
    create_table,
)
from kagura.config.env import (
    check_required_env_vars,
    get_anthropic_api_key,
    get_anthropic_default_model,
    get_brave_search_api_key,
    get_google_ai_default_model,
    get_google_api_key,
    get_openai_api_key,
    get_openai_default_model,
    list_env_vars,
)

console = create_console()


@click.group(name="config")
def app() -> None:
    """Manage Kagura configuration, user profile, and API keys.

    This command provides tools to configure user preferences, manage API keys,
    and validate environment variables.

    Common commands:
      kagura config profile    Setup user preferences
      kagura config api        Manage Memory API keys
      kagura config list       Show environment variables
      kagura config test       Test API connectivity
    """


@app.command(name="list")
def list_config() -> None:
    """List all configuration variables (API keys are masked)."""
    console.print("\n[bold blue]Kagura Configuration[/]\n")

    env_vars = list_env_vars()

    table = create_table()
    table.add_column("Variable", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="white")

    for name, value in env_vars.items():
        if value and value != "None":
            if name.endswith("_KEY"):
                # Mask API keys
                display_value = "***" + value[-4:] if len(value) > 4 else "***"
                status = "[green]✓ Set[/]"
            else:
                display_value = str(value)
                status = "[green]✓ Set[/]"
        else:
            display_value = "[dim]not set[/]"
            status = "[yellow]✗ Not set[/]"

        table.add_row(name, display_value, status)

    console.print(table)
    console.print()


@app.command()
def setup() -> None:
    """Interactive API key setup wizard.

    Guides you through configuring API keys for:
    - OpenAI (GPT models)
    - Anthropic (Claude)
    - Google AI (Gemini)
    - GitHub (REST API)
    - Brave Search

    Configuration saved to .env file in current directory.
    """
    import os

    from rich.prompt import Prompt

    console.print("\n[bold blue]⚙️  Kagura API Key Setup Wizard[/]\n")
    console.print("[dim]Configure API keys for AI providers and services[/dim]")
    console.print("[dim]Press Enter to skip any key you don't need[/dim]\n")

    env_path = Path.cwd() / ".env"
    env_vars = {}

    # Load existing .env if present
    if env_path.exists():
        console.print(f"[yellow]ℹ️  Found existing .env file: {env_path}[/]")
        console.print(
            "[dim]Existing values will be preserved unless you override them[/dim]\n"
        )
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    # API Key prompts
    keys_config = [
        {
            "name": "OPENAI_API_KEY",
            "description": "OpenAI API",
            "example": "sk-...",
            "required": False,
        },
        {
            "name": "ANTHROPIC_API_KEY",
            "description": "Anthropic (Claude)",
            "example": "sk-ant-...",
            "required": False,
        },
        {
            "name": "GOOGLE_API_KEY",
            "description": "Google AI (Gemini)",
            "example": "AIza...",
            "required": False,
        },
        {
            "name": "GITHUB_TOKEN",
            "description": "GitHub API",
            "example": "ghp_... or github_pat_...",
            "required": False,
        },
        {
            "name": "BRAVE_SEARCH_API_KEY",
            "description": "Brave Search",
            "example": "BSA...",
            "required": False,
        },
    ]

    updated = False
    for key_info in keys_config:
        name = key_info["name"]
        existing = env_vars.get(name, "")

        if existing:
            masked = "***" + existing[-4:] if len(existing) > 4 else "***"
            console.print(
                f"[cyan]{key_info['description']}[/] [dim](current: {masked})[/]"
            )
        else:
            console.print(f"[cyan]{key_info['description']}[/]")

        value = Prompt.ask(
            f"  {name}", password=True, default=existing or "", show_default=False
        )

        if value and value != existing:
            env_vars[name] = value
            updated = True
        elif not value and not existing:
            # User skipped, keep empty
            pass

    # Save to .env
    if updated or not env_path.exists():
        lines = []
        lines.append("# Kagura AI Configuration")
        lines.append("# Generated by: kagura config setup")
        lines.append("")
        for name, value in env_vars.items():
            if value:
                lines.append(f"{name}={value}")

        env_path.write_text("\n".join(lines) + "\n")
        console.print(f"\n[green]✓ Configuration saved to {env_path}[/]")
    else:
        console.print("\n[yellow]ℹ️  No changes made[/]")

    # Run validation
    console.print("\n[bold]Running validation...[/]")
    os.environ.update(env_vars)  # Reload for validation
    missing = check_required_env_vars()

    if not missing:
        console.print("[green]✓ All required configuration is set[/]\n")
    else:
        console.print("[yellow]⚠ Optional keys not configured:[/]")
        for item in missing:
            console.print(f"  [dim]- {item}[/]")
        console.print()


@app.command()
def validate() -> None:
    """Validate configuration (check for missing required variables)."""
    console.print("\n[bold blue]Validating Configuration...[/]\n")

    missing = check_required_env_vars()

    if not missing:
        console.print("[green]✓ All required configuration is set[/]\n")
        return

    console.print("[yellow]⚠ Missing required configuration:[/]\n")
    for item in missing:
        console.print(f"  [red]✗[/] {item}")

    console.print("\n[blue]💡 Tip:[/] Set environment variables in:")
    console.print("  - .env file (recommended for development)")
    console.print("  - System environment variables")
    console.print("  - Docker environment\n")


async def _test_openai_api(api_key: str) -> tuple[bool, str]:
    """Test OpenAI API connection.

    Uses shared utility. Related: Issue #538
    """
    from kagura.utils.api_check import check_llm_api

    return await check_llm_api("openai", api_key, get_openai_default_model())


async def _test_anthropic_api(api_key: str) -> tuple[bool, str]:
    """Test Anthropic API connection.

    Uses shared utility. Related: Issue #538
    """
    from kagura.utils.api_check import check_llm_api

    return await check_llm_api("anthropic", api_key, get_anthropic_default_model())


async def _test_google_api(api_key: str) -> tuple[bool, str]:
    """Test Google AI API connection.

    Uses shared utility. Related: Issue #538
    """
    from kagura.utils.api_check import check_llm_api

    return await check_llm_api("google", api_key, get_google_ai_default_model())


async def _test_brave_search_api(api_key: str) -> tuple[bool, str]:
    """Test Brave Search API connection.

    Uses shared utility. Related: Issue #538
    """
    from kagura.utils.api_check import check_brave_search_api

    return await check_brave_search_api(api_key)


async def _test_github_api(api_token: str) -> tuple[bool, str]:
    """Test GitHub API connection.

    Uses shared utility. Related: Issue #538
    """
    from kagura.utils.api_check import check_github_api

    return await check_github_api(api_token)


@app.command()
@click.argument("provider", required=False)
def test(provider: str | None) -> None:
    """Test API connections to verify configuration.

    Examples:

        kagura config test           # Test all configured APIs

        kagura config test openai    # Test only OpenAI

        kagura config test brave     # Test only Brave Search
    """
    console.print("\n[bold blue]Testing API Connections...[/]\n")

    # Determine which providers to test
    providers_to_test: dict[str, tuple[str | None, Any]] = {}

    if provider is None or provider == "openai":
        providers_to_test["OpenAI"] = (get_openai_api_key(), _test_openai_api)

    if provider is None or provider == "anthropic":
        providers_to_test["Anthropic"] = (get_anthropic_api_key(), _test_anthropic_api)

    if provider is None or provider == "google":
        providers_to_test["Google AI"] = (get_google_api_key(), _test_google_api)

    if provider is None or provider == "brave":
        providers_to_test["Brave Search"] = (
            get_brave_search_api_key(),
            _test_brave_search_api,
        )

    if provider is None or provider == "github":
        from kagura.config.env import get_github_token

        providers_to_test["GitHub"] = (
            get_github_token(),
            _test_github_api,
        )

    if not providers_to_test:
        console.print(f"[red]Unknown provider: {provider}[/]")
        console.print("Available providers: openai, anthropic, google, github, brave")
        return

    # Test each provider
    any_success = False
    any_failure = False

    for name, (api_key, test_func) in providers_to_test.items():
        with console.status(f"[cyan]Testing {name}...[/]"):
            if not api_key:
                console.print(f"[yellow]⊘ {name}:[/] API key not set")
                continue

            try:
                success, message = asyncio.run(test_func(api_key))
                if success:
                    console.print(f"[green]✓ {name}:[/] {message}")
                    any_success = True
                else:
                    console.print(f"[red]✗ {name}:[/] {message}")
                    any_failure = True
            except Exception as e:
                console.print(f"[red]✗ {name}:[/] Unexpected error: {e}")
                any_failure = True

    console.print()

    # Summary
    if any_success and not any_failure:
        console.print("[green]✓ All configured APIs are working[/]\n")
    elif any_failure:
        console.print("[yellow]⚠ Some API connections failed[/]")
        console.print("[blue]💡 Check your API keys and network connection[/]\n")


@app.command()
def doctor() -> None:
    """Run comprehensive configuration diagnostics.

    This command checks:

    - Required environment variables

    - API key validity (format)

    - API connectivity

    - Configuration file locations
    """
    console.print("\n")
    console.print(
        create_success_panel(
            "[bold]Kagura Configuration Doctor[/]\n"
            "Running comprehensive diagnostics...",
            title="Info",
        )
    )
    console.print()

    # 1. Check required variables
    console.print("[bold cyan]1. Checking required variables...[/]")
    missing = check_required_env_vars()
    if not missing:
        console.print("   [green]✓ All required variables are set[/]\n")
    else:
        console.print("   [yellow]⚠ Missing required variables:[/]")
        for item in missing:
            console.print(f"     [red]✗[/] {item}")
        console.print()

    # 2. Check API key formats
    console.print("[bold cyan]2. Checking API key formats...[/]")
    keys_ok = True

    openai_key = get_openai_api_key()
    if openai_key:
        if openai_key.startswith("sk-"):
            console.print("   [green]✓ OpenAI API key format looks valid[/]")
        else:
            console.print("   [yellow]⚠ OpenAI API key format looks incorrect[/]")
            keys_ok = False

    anthropic_key = get_anthropic_api_key()
    if anthropic_key:
        if anthropic_key.startswith("sk-ant-"):
            console.print("   [green]✓ Anthropic API key format looks valid[/]")
        else:
            console.print("   [yellow]⚠ Anthropic API key format looks incorrect[/]")
            keys_ok = False

    google_key = get_google_api_key()
    if google_key and len(google_key) > 20:
        console.print("   [green]✓ Google API key format looks valid[/]")
    elif google_key:
        console.print("   [yellow]⚠ Google API key format looks incorrect[/]")
        keys_ok = False

    if keys_ok:
        console.print()
    else:
        console.print(
            "   [blue]💡 Check your API keys - "
            "they may not be in the correct format[/]\n"
        )

    # 3. Check configuration file locations
    console.print("[bold cyan]3. Checking configuration files...[/]")
    cwd = Path.cwd()
    env_file = cwd / ".env"
    if env_file.exists():
        console.print(f"   [green]✓ .env file found:[/] {env_file}")
    else:
        console.print("   [yellow]⊘ .env file not found[/] (using system environment)")

    from kagura.config.paths import get_data_dir

    kagura_dir = get_data_dir()
    if kagura_dir.exists():
        console.print(f"   [green]✓ Kagura data directory:[/] {kagura_dir}")
    else:
        console.print(f"   [blue]ℹ Kagura directory will be created:[/] {kagura_dir}")
    console.print()

    # 4. Test API connectivity
    console.print("[bold cyan]4. Testing API connectivity...[/]")
    console.print("   (This may take a few seconds...)\n")

    # Run connectivity tests using click context
    ctx = click.get_current_context()
    ctx.invoke(test, provider=None)

    # Final summary
    console.print()
    console.print(
        create_success_panel(
            "[bold]Diagnostics Complete[/]\n\n"
            "If you see any errors, check:\n"
            "  • API keys are correct and properly formatted\n"
            "  • Network connection is working\n"
            "  • API services are not experiencing outages",
            title="Summary",
        )
    )
    console.print()


# Note: 'kagura config show' removed in v4.1.1 (Issue #555)
# Use 'kagura config list' instead


@app.command(name="profile")
@click.option(
    "--reset",
    is_flag=True,
    help="Reset user profile to defaults",
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
    help="Full setup (user profile + RAG + reranking)",
)
def profile(
    reset: bool, setup_rag: bool, setup_reranking: bool, full: bool
) -> None:
    """Setup user preferences and profile.

    Configure your name, location, language, and interests for personalized
    AI responses. Optionally set up RAG and reranking models.

    Examples:
        # Setup user profile
        kagura config profile

        # Reset profile to defaults
        kagura config profile --reset

        # Setup RAG environment
        kagura config profile --setup-rag

        # Full setup
        kagura config profile --full
    """
    # Import here to avoid circular dependency
    from kagura.cli.init import init as init_command

    # Invoke the original init command with all parameters
    ctx = click.get_current_context()
    ctx.invoke(init_command, reset=reset, setup_rag=setup_rag, setup_reranking=setup_reranking, full=full)


# API Key management subgroup
@app.group(name="api")
def api_group() -> None:
    """Manage Memory API keys for remote access.

    Create, list, revoke, and delete API keys for authenticating
    with Kagura Memory API.

    Examples:
        kagura config api create-key --name "my-key"
        kagura config api list-keys
        kagura config api revoke-key --name "my-key"
    """
    pass


@api_group.command(name="create-key")
@click.option(
    "--name",
    required=True,
    help="Friendly name for the API key",
)
@click.option(
    "--user-id",
    default="default_user",
    help="User ID that owns this key (default: default_user)",
)
@click.option(
    "--expires",
    type=int,
    help="Expiration in days (optional, no expiration by default)",
)
def create_key(name: str, user_id: str, expires: int | None) -> None:
    """Create a new API key for Memory API authentication."""
    from kagura.cli.api_cli import create_key as create_key_command

    ctx = click.get_current_context()
    ctx.invoke(create_key_command, name=name, user_id=user_id, expires=expires)


@api_group.command(name="list-keys")
@click.option(
    "--user-id",
    help="Filter by user ID (show all users by default)",
)
def list_keys(user_id: str | None) -> None:
    """List all Memory API keys."""
    from kagura.cli.api_cli import list_keys as list_keys_command

    ctx = click.get_current_context()
    ctx.invoke(list_keys_command, user_id=user_id)


@api_group.command(name="revoke-key")
@click.option(
    "--name",
    required=True,
    help="Name of the API key to revoke",
)
@click.option(
    "--user-id",
    default="default_user",
    help="User ID that owns the key (default: default_user)",
)
def revoke_key(name: str, user_id: str) -> None:
    """Revoke a Memory API key."""
    from kagura.cli.api_cli import revoke_key as revoke_key_command

    ctx = click.get_current_context()
    ctx.invoke(revoke_key_command, name=name, user_id=user_id)


@api_group.command(name="delete-key")
@click.option(
    "--name",
    required=True,
    help="Name of the API key to delete",
)
@click.option(
    "--user-id",
    default="default_user",
    help="User ID that owns the key (default: default_user)",
)
@click.confirmation_option(
    prompt="Are you sure you want to permanently delete this key?"
)
def delete_key(name: str, user_id: str) -> None:
    """Permanently delete a Memory API key."""
    from kagura.cli.api_cli import delete_key as delete_key_command

    ctx = click.get_current_context()
    ctx.invoke(delete_key_command, name=name, user_id=user_id)


if __name__ == "__main__":
    app()
