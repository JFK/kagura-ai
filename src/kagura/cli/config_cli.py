"""Configuration management CLI for Kagura AI.

Provides commands for setting up, validating, and testing configuration.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

console = Console()


@click.group(name="config")
def app() -> None:
    """Manage Kagura configuration and API keys.

    This command provides tools to list, validate, and test your
    Kagura configuration including API keys and environment variables.
    """


@app.command(name="list")
def list_config() -> None:
    """List all configuration variables (API keys are masked)."""
    console.print("\n[bold blue]Kagura Configuration[/]\n")

    env_vars = list_env_vars()

    table = Table(show_header=True, header_style="bold magenta")
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
    """Test OpenAI API connection."""
    try:
        from litellm import acompletion

        model = get_openai_default_model()
        await acompletion(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            api_key=api_key,
            max_tokens=1,
        )
        return True, "Connection successful"
    except ImportError:
        return False, "litellm not installed (optional)"
    except Exception as e:
        error_msg = str(e)

        # Provide helpful hints for common errors
        if (
            "authentication" in error_msg.lower()
            or "invalid api key" in error_msg.lower()
            or "invalid key" in error_msg.lower()
        ):
            return False, "Invalid API key (check format and validity)"
        elif "rate_limit" in error_msg.lower() or "quota" in error_msg.lower():
            return False, "Rate limit exceeded (try again later)"
        else:
            return False, f"Connection failed: {error_msg[:200]}"


async def _test_anthropic_api(api_key: str) -> tuple[bool, str]:
    """Test Anthropic API connection."""
    try:
        from litellm import acompletion

        model = get_anthropic_default_model()
        await acompletion(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            api_key=api_key,
            max_tokens=1,
        )
        return True, "Connection successful"
    except ImportError:
        return False, "litellm not installed (optional)"
    except Exception as e:
        error_msg = str(e)

        # Provide helpful hints for common errors
        if (
            "authentication_error" in error_msg.lower()
            or "invalid x-api-key" in error_msg.lower()
        ):
            return False, "Invalid API key (check format and validity)"
        elif "rate_limit" in error_msg.lower() or "overloaded" in error_msg.lower():
            return False, "Rate limit exceeded or API overloaded (try again later)"
        else:
            # Truncate long error messages
            return False, f"Connection failed: {error_msg[:200]}"


async def _test_google_api(api_key: str) -> tuple[bool, str]:
    """Test Google AI API connection."""
    try:
        from litellm import acompletion

        model = get_google_ai_default_model()
        await acompletion(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            api_key=api_key,
            max_tokens=1,
        )
        return True, "Connection successful"
    except ImportError:
        return False, "litellm not installed (optional)"
    except Exception as e:
        error_msg = str(e)

        # Provide helpful hints for common errors
        if (
            "authentication_error" in error_msg.lower()
            or "invalid api key" in error_msg.lower()
            or "api key not valid" in error_msg.lower()
        ):
            return False, "Invalid API key (check format and validity)"
        elif "rate_limit" in error_msg.lower() or "quota" in error_msg.lower():
            return False, "Rate limit exceeded (try again later)"
        else:
            # Truncate long error messages
            return False, f"Connection failed: {error_msg[:200]}"


async def _test_brave_search_api(api_key: str) -> tuple[bool, str]:
    """Test Brave Search API connection."""
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": "test", "count": 1},
                headers={"X-Subscription-Token": api_key},
                timeout=10.0,
            )
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except ImportError:
        return False, "httpx not installed (optional)"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


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

    if not providers_to_test:
        console.print(f"[red]Unknown provider: {provider}[/]")
        console.print("Available providers: openai, anthropic, google, brave")
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
        Panel(
            "[bold]Kagura Configuration Doctor[/]\n"
            "Running comprehensive diagnostics...",
            style="blue",
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
        Panel(
            "[bold]Diagnostics Complete[/]\n\n"
            "If you see any errors, check:\n"
            "  • API keys are correct and properly formatted\n"
            "  • Network connection is working\n"
            "  • API services are not experiencing outages",
            style="blue",
        )
    )
    console.print()


@app.command()
@click.argument("variable")
def show(variable: str) -> None:
    """Show a specific configuration variable (API keys are masked).

    Example:

        kagura config show OPENAI_API_KEY
    """
    env_vars = list_env_vars()

    if variable not in env_vars:
        console.print(f"[red]Unknown variable: {variable}[/]")
        console.print("\n[blue]Available variables:[/]")
        for name in env_vars.keys():
            console.print(f"  - {name}")
        return

    value = env_vars[variable]
    if value and value != "None":
        if variable.endswith("_KEY"):
            # Mask API keys
            display_value = "***" + value[-4:] if len(value) > 4 else "***"
        else:
            display_value = str(value)
        console.print(f"\n{variable} = {display_value}\n")
    else:
        console.print(f"\n{variable} = [dim]not set[/]\n")


if __name__ == "__main__":
    app()
