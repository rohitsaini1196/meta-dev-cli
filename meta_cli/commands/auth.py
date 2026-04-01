import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from meta_cli.api.graph_client import AuthError, GraphAPIError, GraphClient
from meta_cli.config.config_manager import ConfigManager
from meta_cli.models.responses import MeResponse
from meta_cli.utils import error_exit, success

console = Console()

TOKEN_INSTRUCTIONS = """[bold]How to get your Meta access token:[/bold]

[bold cyan]Option 1 — Graph API Explorer (recommended for development)[/bold cyan]
  1. Go to [link=https://developers.facebook.com/tools/explorer]https://developers.facebook.com/tools/explorer[/link]
  2. Select your app from the top-right dropdown
  3. Click [bold]"Generate Access Token"[/bold]
  4. Grant requested permissions
  5. Copy the token shown

[bold cyan]Option 2 — System User token (recommended for production)[/bold cyan]
  1. Go to [link=https://business.facebook.com/settings]https://business.facebook.com/settings[/link]
  2. Navigate to [bold]Users → System Users[/bold]
  3. Create or select a System User
  4. Click [bold]"Generate New Token"[/bold] → select your app + permissions
  5. Copy the token

[bold cyan]Required permissions for WhatsApp commands:[/bold cyan]
  • [green]whatsapp_business_messaging[/green]   — send messages
  • [green]whatsapp_business_management[/green]  — manage templates, phone numbers

[dim]Tokens from the Explorer expire in ~1 hour.
System User tokens don't expire (unless manually revoked).[/dim]"""


def login(
    ctx: typer.Context,
    token: str = typer.Option(
        None,
        "--token",
        prompt=False,
        hide_input=True,
        help="Meta Graph API access token. Run without --token to see setup instructions.",
    ),
):
    """Authenticate with Meta Graph API and store credentials locally."""
    if token is None:
        console.print(Panel(TOKEN_INSTRUCTIONS, title="[bold]meta login — Setup Guide[/bold]", border_style="blue", padding=(1, 2)))
        token = typer.prompt("Access Token", hide_input=True)

    client = GraphClient(access_token=token)
    with console.status("Verifying token..."):
        try:
            data = client.get("/me", params={"fields": "id,name"})
        except AuthError as e:
            error_exit(f"Invalid token: {e.message}", hint="Make sure you're using a valid User or System User access token.")
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    me = MeResponse.model_validate(data)
    ConfigManager().update(access_token=token)
    success(f"Logged in as [bold]{me.name or 'Unknown'}[/bold] (ID: {me.id})")
