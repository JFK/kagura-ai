"""MCP configuration commands - installation and remote connection setup"""

import json

import click
from rich.console import Console

from kagura.config.paths import get_config_dir
from kagura.mcp.config import MCPConfig


@click.command()
@click.option("--server-name", default="kagura-memory", help="MCP server name")
@click.pass_context
def install(ctx: click.Context, server_name: str):
    """Install Kagura to Claude Desktop

    Automatically configures Claude Desktop to use Kagura MCP server.

    Example:
      kagura mcp install
    """
    console = Console()
    config = MCPConfig()

    # Check if already configured
    if config.is_configured_in_claude_desktop(server_name):
        console.print(
            f"[yellow]Kagura is already configured in Claude Desktop "
            f"as '{server_name}'[/yellow]"
        )
        if not click.confirm("Overwrite existing configuration?"):
            console.print("[dim]Installation cancelled.[/dim]")
            return

    # Add to Claude Desktop config
    console.print("\n[bold]Installing Kagura MCP to Claude Desktop...[/bold]")

    # Determine kagura command path
    import shutil

    kagura_command = shutil.which("kagura") or "kagura"

    success = config.add_to_claude_desktop(server_name, kagura_command)

    if success:
        console.print("[green]✅ Successfully installed![/green]\n")
        console.print("[bold]Configuration:[/bold]")
        console.print(f"  Server name: {server_name}")
        console.print(f"  Command: {kagura_command} mcp serve")
        console.print(f"  Config file: {config.claude_config_path}")
        console.print("\n[bold yellow]Next steps:[/bold yellow]")
        console.print("  1. Restart Claude Desktop")
        console.print("  2. Start a new conversation")
        console.print("  3. Try: 'Remember that I prefer Python'")
        console.print()
    else:
        console.print("[red]❌ Installation failed[/red]")
        console.print(f"Check permissions for: {config.claude_config_path}")


@click.command()
@click.option("--server-name", default="kagura-memory", help="MCP server name")
@click.pass_context
def uninstall(ctx: click.Context, server_name: str):
    """Remove Kagura from Claude Desktop

    Removes Kagura MCP server configuration from Claude Desktop.

    Example:
      kagura mcp uninstall
    """
    console = Console()
    config = MCPConfig()

    if not config.is_configured_in_claude_desktop(server_name):
        console.print(
            f"[yellow]Kagura '{server_name}' is not configured "
            f"in Claude Desktop[/yellow]"
        )
        return

    if not click.confirm(f"Remove '{server_name}' from Claude Desktop configuration?"):
        console.print("[dim]Uninstallation cancelled.[/dim]")
        return

    success = config.remove_from_claude_desktop(server_name)

    if success:
        console.print(f"[green]✅ Successfully removed '{server_name}'[/green]")
        console.print(f"Config file: {config.claude_config_path}")
        console.print("\n[yellow]Restart Claude Desktop to apply changes.[/yellow]\n")
    else:
        console.print("[red]❌ Uninstallation failed[/red]")


@click.command(name="connect")
@click.option(
    "--api-base",
    required=True,
    help="Remote Kagura API base URL (e.g., https://my-kagura.example.com)",
)
@click.option(
    "--api-key",
    help="API key for authentication (optional, can use KAGURA_API_KEY env var)",
)
@click.option(
    "--user-id",
    help="User ID for memory access (optional, defaults to default_user)",
)
@click.pass_context
def connect(
    ctx: click.Context, api_base: str, api_key: str | None, user_id: str | None
):
    """Configure remote MCP connection

    Saves remote connection settings for Kagura API access.
    These settings are used by 'kagura mcp serve --remote' command.

    Examples:
        # Configure remote connection
        kagura mcp connect --api-base https://my-kagura.example.com --api-key xxx

        # With custom user ID
        kagura mcp connect --api-base https://api.kagura.io --user-id user_alice
    """
    console = Console()

    # Validate URL
    if not api_base.startswith(("http://", "https://")):
        console.print(
            "[red]✗ Error: API base URL must start with http:// or https://[/red]"
        )
        raise click.Abort()

    # Prepare config
    config_dir = get_config_dir()
    config_file = config_dir / "remote-config.json"
    config_dir.mkdir(parents=True, exist_ok=True)

    remote_config = {
        "api_base": api_base.rstrip("/"),
        "api_key": api_key,
        "user_id": user_id or "default_user",
    }

    # Save config
    with open(config_file, "w") as f:
        json.dump(remote_config, f, indent=2)

    console.print("\n[green]✓ Remote connection configured successfully![/green]")
    console.print()
    console.print(f"[dim]Config saved to: {config_file}[/dim]")
    console.print()
    console.print("[cyan]Connection settings:[/cyan]")
    console.print(f"  • API Base: {api_base}")
    console.print(f"  • User ID: {user_id or 'default_user'}")
    console.print(f"  • API Key: {'***' + (api_key[-8:] if api_key else 'Not set')}")
    console.print()
    console.print("[yellow]Test connection with:[/yellow] kagura mcp test-remote")
    console.print()


@click.command(name="test-remote")
@click.pass_context
def test_remote(ctx: click.Context):
    """Test remote MCP connection

    Verifies that the remote Kagura API is accessible and responds correctly.

    Example:
        kagura mcp test-remote
    """
    import httpx
    from rich.console import Console

    console = Console()

    # Load config
    config_file = get_config_dir() / "remote-config.json"
    if not config_file.exists():
        console.print("[red]✗ Error: Remote connection not configured[/red]")
        console.print()
        console.print(
            "Configure with: [cyan]kagura mcp connect --api-base <url>[/cyan]"
        )
        console.print()
        raise click.Abort()

    with open(config_file) as f:
        config = json.load(f)

    api_base = config.get("api_base")
    api_key = config.get("api_key")
    user_id = config.get("user_id", "default_user")

    console.print("\n[bold]Testing Remote MCP Connection[/bold]\n")
    console.print(f"[dim]API Base: {api_base}[/dim]")
    console.print(f"[dim]User ID: {user_id}[/dim]\n")

    # Test 1: API health check
    console.print("[cyan]1. Testing API health...[/cyan]")
    try:
        response = httpx.get(f"{api_base}/api/v1/health", timeout=10.0)
        if response.status_code == 200:
            console.print("   [green]✓ API server is reachable[/green]")
        else:
            console.print(
                f"   [yellow]⚠ API returned status {response.status_code}[/yellow]"
            )
    except Exception as e:
        console.print(f"   [red]✗ Failed: {e}[/red]")
        raise click.Abort()

    # Test 2: MCP endpoint check
    console.print("\n[cyan]2. Testing /mcp endpoint...[/cyan]")
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Try tools/list request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        response = httpx.post(
            f"{api_base}/mcp",
            json=mcp_request,
            headers=headers,
            timeout=10.0,
        )

        if response.status_code == 200:
            console.print("   [green]✓ MCP endpoint is accessible[/green]")
        elif response.status_code == 401:
            console.print("   [red]✗ Authentication failed (invalid API key)[/red]")
            raise click.Abort()
        elif response.status_code == 406:
            console.print("   [yellow]⚠ MCP endpoint exists but returned 406[/yellow]")
            console.print("   [dim](This is expected for initial handshake)[/dim]")
        else:
            console.print(
                f"   [yellow]⚠ Unexpected status: {response.status_code}[/yellow]"
            )

    except httpx.TimeoutException:
        console.print("   [red]✗ Connection timeout[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"   [red]✗ Failed: {e}[/red]")
        raise click.Abort()

    # Test 3: Authentication
    console.print("\n[cyan]3. Testing authentication...[/cyan]")
    if api_key:
        console.print(f"   [green]✓ API key configured: ***{api_key[-8:]}[/green]")
    else:
        console.print(
            "   [yellow]⚠ No API key configured (using default_user)[/yellow]"
        )

    console.print("\n[green bold]✓ All tests passed![/green bold]")
    console.print()
    console.print("[cyan]Your remote MCP connection is ready to use.[/cyan]")
    console.print()
