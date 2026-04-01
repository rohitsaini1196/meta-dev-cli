import secrets
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from meta_cli.api.graph_client import GraphAPIError, GraphClient
from meta_cli.config.config_manager import ConfigError, ConfigManager
from meta_cli.utils import error_exit, success

console = Console()
webhook_app = typer.Typer(help="Manage WhatsApp webhook configuration.", no_args_is_help=True)


@webhook_app.callback(invoke_without_command=True)
def webhook_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@webhook_app.command("set")
def set_webhook(
    ctx: typer.Context,
    url: str = typer.Argument(..., help="Public HTTPS URL for receiving webhook events"),
    verify_token: Optional[str] = typer.Option(
        None,
        "--verify-token",
        help="Custom verify token (auto-generated if not provided)",
    ),
):
    """Configure the webhook endpoint for the selected app."""
    if not url.startswith("https://"):
        error_exit("Webhook URL must start with https://")

    cm = ConfigManager()
    try:
        token = cm.require_token()
        app_id = cm.require_app_id()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    if not verify_token:
        verify_token = secrets.token_hex(16)

    client = GraphClient(token)
    with console.status("Setting webhook..."):
        try:
            client.post(
                f"/{app_id}/subscriptions",
                json={
                    "object": "whatsapp_business_account",
                    "callback_url": url,
                    "verify_token": verify_token,
                    "fields": ["messages"],
                },
            )
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    cm.update(webhook_verify_token=verify_token) if hasattr(cm.load(), "webhook_verify_token") else None

    console.print(
        Panel(
            f"[green]Webhook set:[/green] {url}\n\n"
            f"[bold yellow]Verify Token:[/bold yellow] [bold]{verify_token}[/bold]\n\n"
            "[dim]Configure this verify token on your server to respond to Meta's verification request.[/dim]",
            title="Webhook Configured",
            border_style="green",
        )
    )


@webhook_app.command("test")
def test_webhook(ctx: typer.Context):
    """Send a test verification request to the configured webhook URL."""
    import urllib.parse

    import requests as req

    cm = ConfigManager()
    config = cm.load()

    if not config.access_token:
        error_exit("Not logged in.", hint="Run: meta login")

    # Retrieve webhook URL from subscriptions
    try:
        token = cm.require_token()
        app_id = cm.require_app_id()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    client = GraphClient(token)
    with console.status("Fetching webhook subscriptions..."):
        try:
            data = client.get(f"/{app_id}/subscriptions")
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    subscriptions = data.get("data", [])
    if not subscriptions:
        error_exit("No webhook subscriptions found.", hint="Run: meta wa webhook set <url>")

    callback_url = subscriptions[0].get("callback_url")
    if not callback_url:
        error_exit("No callback URL found in subscriptions.")

    challenge = secrets.token_hex(8)
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": challenge,
        "hub.verify_token": config.access_token[:10],  # partial token as proxy
    }

    query = urllib.parse.urlencode(params)
    test_url = f"{callback_url}?{query}"

    console.print(f"Sending verification GET to: [cyan]{test_url}[/cyan]")
    try:
        resp = req.get(test_url, timeout=10)
        if resp.status_code == 200 and resp.text.strip() == challenge:
            success(f"Webhook verification succeeded! Challenge echoed: [bold]{challenge}[/bold]")
        else:
            console.print(
                Panel(
                    f"[yellow]Response status:[/yellow] {resp.status_code}\n"
                    f"[yellow]Response body:[/yellow] {resp.text[:200]}",
                    title="Webhook Response",
                    border_style="yellow",
                )
            )
    except req.exceptions.RequestException as e:
        error_exit(f"Failed to reach webhook URL: {e}")
