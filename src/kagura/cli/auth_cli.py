"""CLI commands for OAuth2 authentication"""

import logging
from datetime import datetime, timezone

import click
from rich.console import Console
from rich.table import Table

from kagura.auth import OAuth2Manager
from kagura.auth.exceptions import AuthenticationError

console = Console()
logger = logging.getLogger(__name__)


@click.group(name="auth")
def auth_group() -> None:
    """OAuth2 authentication commands

    Manage authentication for Kagura AI services.
    """
    pass


@auth_group.command(name="login")
@click.option(
    "--provider",
    type=str,
    default="google",
    help="OAuth2 provider (default: google)",
)
def login_command(provider: str) -> None:
    """Login with OAuth2 provider

    Opens a browser window for authentication. After successful login,
    credentials are encrypted and stored locally.

    Example:
        kagura auth login --provider google
    """
    try:
        console.print(f"[cyan]Starting authentication with {provider}...[/cyan]")
        console.print()
        console.print("[yellow]A browser window will open for authentication.[/yellow]")
        console.print(
            "[yellow]Please log in to your account and authorize Kagura AI.[/yellow]"
        )
        console.print()

        auth = OAuth2Manager(provider=provider)
        auth.login()

        console.print()
        console.print("[green]✓ Authentication successful![/green]")
        console.print(
            f"[green]✓ Credentials saved securely to: {auth.creds_file}[/green]"
        )
        console.print()
        console.print("You can now use Kagura AI without setting API keys!")

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]", style="bold")
        console.print()
        console.print(
            "[yellow]Please follow these steps to get client_secrets.json:[/yellow]"
        )
        console.print("  1. Go to https://console.cloud.google.com/apis/credentials")
        console.print("  2. Create OAuth 2.0 Client ID (Desktop application)")
        console.print(f"  3. Download JSON and save to: {auth.client_secrets_file}")  # type: ignore
        raise click.Abort()

    except AuthenticationError as e:
        console.print(f"[red]✗ Authentication failed: {e}[/red]", style="bold")
        raise click.Abort()

    except Exception as e:
        logger.exception("Unexpected error during login")
        console.print(f"[red]✗ Unexpected error: {e}[/red]", style="bold")
        raise click.Abort()


@auth_group.command(name="logout")
@click.option(
    "--provider",
    type=str,
    default="google",
    help="OAuth2 provider (default: google)",
)
def logout_command(provider: str) -> None:
    """Logout from OAuth2 provider

    Removes stored credentials for the specified provider.

    Example:
        kagura auth logout --provider google
    """
    try:
        auth = OAuth2Manager(provider=provider)

        if not auth.is_authenticated():
            console.print(f"[yellow]Not authenticated with {provider}[/yellow]")
            return

        auth.logout()
        console.print(f"[green]✓ Successfully logged out from {provider}[/green]")

    except AuthenticationError as e:
        console.print(f"[red]✗ Logout failed: {e}[/red]", style="bold")
        raise click.Abort()

    except Exception as e:
        logger.exception("Unexpected error during logout")
        console.print(f"[red]✗ Unexpected error: {e}[/red]", style="bold")
        raise click.Abort()


@auth_group.command(name="status")
def status_command() -> None:
    """Show authentication status

    Displays authentication status for all supported providers.

    Example:
        kagura auth status
    """
    try:
        providers = ["google"]  # Add more providers in the future
        table = Table(title="Authentication Status", show_header=True)
        table.add_column("Provider", style="cyan", width=15)
        table.add_column("Status", width=15)
        table.add_column("Token Expiry", width=25)

        for provider in providers:
            auth = OAuth2Manager(provider=provider)

            if not auth.is_authenticated():
                table.add_row(provider, "[red]Not authenticated[/red]", "-")
                continue

            try:
                creds = auth.get_credentials()
                status = "[green]✓ Authenticated[/green]"

                # Get token expiry
                if hasattr(creds, "expiry") and creds.expiry:
                    # Convert to UTC if naive
                    expiry = creds.expiry
                    if expiry.tzinfo is None:
                        expiry = expiry.replace(tzinfo=timezone.utc)

                    now = datetime.now(timezone.utc)
                    if expiry > now:
                        delta = expiry - now
                        hours = delta.total_seconds() / 3600
                        expiry_str = (
                            f"[green]{expiry.strftime('%Y-%m-%d %H:%M:%S UTC')}[/green]"
                        )
                        if hours < 1:
                            expiry_str += " [yellow](expires soon)[/yellow]"
                    else:
                        expiry_str = "[red]Expired[/red]"
                else:
                    expiry_str = "Unknown"

                table.add_row(provider, status, expiry_str)

            except AuthenticationError as e:
                table.add_row(
                    provider,
                    "[yellow]Authentication issue[/yellow]",
                    str(e),
                )

        console.print()
        console.print(table)
        console.print()

        # Show instructions for unauthenticated providers
        all_authenticated = all(
            OAuth2Manager(provider=p).is_authenticated() for p in providers
        )

        if not all_authenticated:
            console.print(
                "[yellow]To authenticate, run:[/yellow] "
                "kagura auth login --provider <provider>"
            )
            console.print()

    except Exception as e:
        logger.exception("Unexpected error during status check")
        console.print(f"[red]✗ Unexpected error: {e}[/red]", style="bold")
        raise click.Abort()
