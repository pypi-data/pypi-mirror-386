"""Status command for ConnectOnion CLI - handles 'co status'."""

import os
import toml
import requests
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

console = Console()


def _load_api_key() -> str:
    """Load OPENONION_API_KEY from environment.

    Checks in order:
    1. Environment variable
    2. Local .env file
    3. Global ~/.co/keys.env file

    Returns:
        API key if found, None otherwise
    """
    # Check environment variable first
    api_key = os.getenv("OPENONION_API_KEY")
    if api_key:
        return api_key

    # Check local .env
    local_env = Path(".env")
    if local_env.exists():
        load_dotenv(local_env)
        api_key = os.getenv("OPENONION_API_KEY")
        if api_key:
            return api_key

    # Check global ~/.co/keys.env
    global_env = Path.home() / ".co" / "keys.env"
    if global_env.exists():
        load_dotenv(global_env)
        api_key = os.getenv("OPENONION_API_KEY")
        if api_key:
            return api_key

    return None


def _load_config() -> dict:
    """Load config from .co/config.toml or ~/.co/config.toml.

    Returns:
        Config dict if found, empty dict otherwise
    """
    # Check local .co/config.toml first
    local_config = Path(".co") / "config.toml"
    if local_config.exists():
        return toml.load(local_config)

    # Check global ~/.co/config.toml
    global_config = Path.home() / ".co" / "config.toml"
    if global_config.exists():
        return toml.load(global_config)

    return {}


def handle_status():
    """Check account status without re-authenticating.

    Shows:
    - Agent ID
    - Email address
    - Balance (remaining credits)
    - Total spent
    - Last seen
    - Warnings if balance is low
    """
    # Load API key
    api_key = _load_api_key()
    if not api_key:
        console.print("\n❌ [bold red]No API key found[/bold red]")
        console.print("\n[cyan]Authenticate first:[/cyan]")
        console.print("  [bold]co auth[/bold]     Authenticate with OpenOnion\n")
        return

    # Load config for agent info
    config = _load_config()
    agent_info = config.get("agent", {})

    # Decode JWT to extract public_key and re-authenticate to get fresh data
    import jwt
    import time
    from ... import address

    # Load keys to re-sign
    co_dir = Path(".co")
    if not (co_dir.exists() and (co_dir / "keys" / "agent.key").exists()):
        co_dir = Path.home() / ".co"

    addr_data = address.load(co_dir)
    if not addr_data:
        console.print("\n❌ [bold red]No keys found[/bold red]")
        console.print("[yellow]Run 'co auth' first.[/yellow]\n")
        return

    public_key = addr_data["address"]
    timestamp = int(time.time())
    message = f"ConnectOnion-Auth-{public_key}-{timestamp}"
    signature = address.sign(addr_data, message.encode()).hex()

    # Call auth endpoint to get fresh user data
    response = requests.post(
        "https://oo.openonion.ai/api/v1/auth",
        json={
            "public_key": public_key,
            "signature": signature,
            "message": message
        }
    )

    if response.status_code != 200:
        console.print(f"\n❌ [bold red]Error {response.status_code}[/bold red]")
        console.print(f"[yellow]{response.text}[/yellow]\n")
        return

    data = response.json()
    user = data.get("user", {})
    email_info = user.get("email") or {}

    # Build info display
    api_key_display = f"{api_key[:20]}..." if len(api_key) > 20 else api_key

    info_lines = [
        f"[cyan]Agent Address:[/cyan] {public_key}",
        f"[cyan]Agent ID:[/cyan] {agent_info.get('short_address', 'Unknown')}",
        f"[cyan]Email:[/cyan] {email_info.get('address') or agent_info.get('email', 'Not configured')}",
        f"[cyan]API Key:[/cyan] {api_key_display}",
        f"[cyan]Balance:[/cyan] ${user.get('balance_usd', 0.0):.4f}",
        f"[cyan]Total Spent:[/cyan] ${user.get('total_cost_usd', 0.0):.4f}",
        f"[cyan]Credits:[/cyan] ${user.get('credits_usd', 0.0):.4f}",
    ]

    console.print("\n")
    console.print(Panel.fit(
        "\n".join(info_lines),
        title="📊 Account Status",
        border_style="cyan"
    ))

    if user.get('balance_usd', 0) <= 0:
        console.print("\n[yellow]⚠️  Low balance! Purchase tokens at https://oo.openonion.ai[/yellow]")

    console.print("\n[yellow]💡 Tips:[/yellow]")
    console.print("   • Use 'co auth' to refresh your token")
    console.print("   • Visit https://oo.openonion.ai to manage your account\n")
