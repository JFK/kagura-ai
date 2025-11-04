"""CLI commands for API Key management.

Manages API keys for remote access to Kagura Memory API.
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from kagura.api.auth import get_api_key_manager

console = Console()


@click.group(name="api")
def api_group() -> None:
    """API Key management commands.

    Manage API keys for remote access to Kagura Memory API.
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
    """Create a new API key.

    Generates a new API key for authentication. The key is only shown once,
    so make sure to save it securely.

    Examples:
        # Create a key for local testing
        kagura api create-key --name "local-dev"

        # Create a key for specific user with expiration
        kagura api create-key --name "chatgpt" --user-id "user_alice" --expires 90
    """
    try:
        manager = get_api_key_manager()

        console.print(
            f"\n[cyan]Creating API key '{name}' for user '{user_id}'...[/cyan]"
        )

        # Create key
        api_key = manager.create_key(
            name=name,
            user_id=user_id,
            expires_days=expires,
        )

        # Display success message
        console.print("\n[green]✓ API key created successfully![/green]")
        console.print()
        console.print(
            "[yellow]⚠️  Save this key securely - it won't be shown again:[/yellow]"
        )
        console.print()
        console.print(f"  [bold white]{api_key}[/bold white]")
        console.print()

        # Show usage example
        console.print("[cyan]Usage example:[/cyan]")
        console.print()
        console.print("  # Set as environment variable")
        console.print(f"  export KAGURA_API_KEY={api_key}")
        console.print()
        console.print("  # Use in HTTP requests")
        console.print(f"  curl -H 'Authorization: Bearer {api_key}' \\")
        console.print("       http://localhost:8000/mcp")
        console.print()

        if expires:
            console.print(
                f"[yellow]Note: This key will expire in {expires} days[/yellow]"
            )
            console.print()

    except ValueError as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        raise click.Abort()

    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error: {e}[/red]")
        raise click.Abort()


@api_group.command(name="list-keys")
@click.option(
    "--user-id",
    help="Filter by user ID (show all users by default)",
)
def list_keys(user_id: str | None) -> None:
    """List all API keys.

    Shows metadata for all API keys, including creation time, last usage,
    and expiration status.

    Examples:
        # List all keys
        kagura api list-keys

        # List keys for specific user
        kagura api list-keys --user-id user_alice
    """
    try:
        manager = get_api_key_manager()

        # Get keys
        keys = manager.list_keys(user_id=user_id)

        if not keys:
            console.print("\n[yellow]No API keys found[/yellow]")
            console.print()
            console.print(
                "Create a key with: [cyan]kagura api create-key --name <name>[/cyan]"
            )
            console.print()
            return

        # Create table
        table = Table(title="API Keys", show_header=True)
        table.add_column("Name", style="cyan", width=20)
        table.add_column("User ID", width=15)
        table.add_column("Prefix", width=20)
        table.add_column("Created", width=20)
        table.add_column("Last Used", width=20)
        table.add_column("Status", width=15)

        for key in keys:
            # Determine status
            if key["revoked_at"]:
                status = "[red]Revoked[/red]"
            elif key["expires_at"]:
                from datetime import datetime

                expires_dt = datetime.fromisoformat(key["expires_at"])
                if datetime.now() > expires_dt:
                    status = "[red]Expired[/red]"
                else:
                    status = "[green]Active[/green]"
            else:
                status = "[green]Active[/green]"

            # Format dates
            created = key["created_at"][:19] if key["created_at"] else "-"
            last_used = key["last_used_at"][:19] if key["last_used_at"] else "Never"

            table.add_row(
                key["name"],
                key["user_id"],
                key["key_prefix"] + "...",
                created,
                last_used,
                status,
            )

        console.print()
        console.print(table)
        console.print()

        # Show summary
        active_count = sum(
            1
            for k in keys
            if not k["revoked_at"]
            and (
                not k["expires_at"]
                or datetime.fromisoformat(k["expires_at"]) > datetime.now()
            )
        )
        console.print(f"[cyan]Total: {len(keys)} keys ({active_count} active)[/cyan]")
        console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error: {e}[/red]")
        raise click.Abort()


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
    """Revoke an API key.

    Revoked keys can no longer be used for authentication, but are kept
    in the database for audit purposes.

    Examples:
        kagura api revoke-key --name "old-key"
        kagura api revoke-key --name "chatgpt" --user-id user_alice
    """
    try:
        manager = get_api_key_manager()

        console.print(
            f"\n[cyan]Revoking API key '{name}' for user '{user_id}'...[/cyan]"
        )

        # Revoke key
        success = manager.revoke_key(name=name, user_id=user_id)

        if success:
            console.print("\n[green]✓ API key revoked successfully[/green]")
            console.print()
            console.print("The key can no longer be used for authentication.")
            console.print()
        else:
            console.print("\n[yellow]⚠️  API key not found or already revoked[/yellow]")
            console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error: {e}[/red]")
        raise click.Abort()


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
    """Permanently delete an API key.

    WARNING: This permanently removes the key from the database.
    Consider using 'revoke-key' instead to keep audit history.

    Examples:
        kagura api delete-key --name "old-key"
    """
    try:
        manager = get_api_key_manager()

        console.print(
            f"\n[cyan]Deleting API key '{name}' for user '{user_id}'...[/cyan]"
        )

        # Delete key
        success = manager.delete_key(name=name, user_id=user_id)

        if success:
            console.print("\n[green]✓ API key deleted successfully[/green]")
            console.print()
        else:
            console.print("\n[yellow]⚠️  API key not found[/yellow]")
            console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error: {e}[/red]")
        raise click.Abort()
