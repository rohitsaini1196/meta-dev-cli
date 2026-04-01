import json

import typer
from rich.console import Console
from rich.table import Table

from meta_cli.api.graph_client import GraphAPIError, GraphClient
from meta_cli.commands.templates import templates_app
from meta_cli.commands.webhook import webhook_app
from meta_cli.config.config_manager import ConfigError, ConfigManager
from meta_cli.models.responses import PhoneNumbersResponse, SendMessageResponse
from meta_cli.utils import error_exit, output_or_json, resolve_json_flag, success, validate_phone_number

console = Console()
wa_app = typer.Typer(help="WhatsApp Cloud API commands.", no_args_is_help=True)
wa_app.add_typer(templates_app, name="templates")
wa_app.add_typer(webhook_app, name="webhook")


@wa_app.callback(invoke_without_command=True)
def wa_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@wa_app.command("phone-numbers")
def phone_numbers(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output as machine-readable JSON."),
):
    """List WhatsApp phone numbers for the current WhatsApp Business Account."""
    cm = ConfigManager()
    try:
        token = cm.require_token()
        waba_id = cm.require_waba_id()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    client = GraphClient(token)
    with console.status("Fetching phone numbers..."):
        try:
            data = client.get(
                f"/{waba_id}/phone_numbers",
                params={"fields": "id,display_phone_number,verified_name,quality_rating,status"},
            )
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    response = PhoneNumbersResponse.model_validate(data)

    def render_table():
        table = Table("ID", "NUMBER", "VERIFIED NAME", "STATUS", show_lines=False)
        for p in response.data:
            table.add_row(
                p.id,
                p.display_phone_number,
                p.verified_name or "-",
                p.status or "-",
            )
        if not response.data:
            console.print("[dim]No phone numbers found.[/dim]")
        else:
            console.print(table)
            console.print(
                f"\n[dim]To set a sender phone number, run: meta wa setup --phone-number-id <ID>[/dim]"
            )

    output_or_json(ctx, render_table, response, json_output)


@wa_app.command("setup")
def setup(
    ctx: typer.Context,
    waba_id: str = typer.Option(..., "--waba-id", prompt="WhatsApp Business Account ID", help="WABA ID"),
    phone_number_id: str = typer.Option(
        ..., "--phone-number-id", prompt="Phone Number ID", help="Sender phone number ID"
    ),
):
    """Configure WhatsApp Business Account ID and sender phone number ID."""
    cm = ConfigManager()
    try:
        cm.require_token()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    cm.update(waba_id=waba_id, phone_number_id=phone_number_id)
    success(f"WhatsApp configured.\nWABA ID: [bold]{waba_id}[/bold]\nPhone Number ID: [bold]{phone_number_id}[/bold]")


@wa_app.command("send")
def send(
    ctx: typer.Context,
    phone: str = typer.Argument(..., help="Recipient phone number with country code (e.g. +14155552671)"),
    message: str = typer.Argument(..., help="Text message to send"),
    json_output: bool = typer.Option(False, "--json", help="Output as machine-readable JSON."),
):
    """Send a WhatsApp text message."""
    try:
        cleaned_phone = validate_phone_number(phone)
    except typer.BadParameter as e:
        error_exit(str(e))

    cm = ConfigManager()
    try:
        token = cm.require_token()
        phone_number_id = cm.require_phone_number_id()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    client = GraphClient(token)
    with console.status("Sending message..."):
        try:
            data = client.post(
                f"/{phone_number_id}/messages",
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": cleaned_phone,
                    "type": "text",
                    "text": {"preview_url": False, "body": message},
                },
            )
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    response = SendMessageResponse.model_validate(data)
    msg_id = response.messages[0].id if response.messages else "unknown"

    if resolve_json_flag(ctx, json_output):
        typer.echo(json.dumps({"message_id": msg_id, "status": "sent", "to": cleaned_phone}, indent=2))
    else:
        success(f"Message sent to [bold]+{cleaned_phone}[/bold]\nMessage ID: {msg_id}")


@wa_app.command("send-test")
def send_test(
    ctx: typer.Context,
    phone: str = typer.Argument(..., help="Recipient phone number with country code"),
    json_output: bool = typer.Option(False, "--json", help="Output as machine-readable JSON."),
):
    """Send the hello_world template message for testing."""
    try:
        cleaned_phone = validate_phone_number(phone)
    except typer.BadParameter as e:
        error_exit(str(e))

    cm = ConfigManager()
    try:
        token = cm.require_token()
        phone_number_id = cm.require_phone_number_id()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    client = GraphClient(token)
    with console.status("Sending test message..."):
        try:
            data = client.post(
                f"/{phone_number_id}/messages",
                json={
                    "messaging_product": "whatsapp",
                    "to": cleaned_phone,
                    "type": "template",
                    "template": {
                        "name": "hello_world",
                        "language": {"code": "en_US"},
                    },
                },
            )
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    response = SendMessageResponse.model_validate(data)
    msg_id = response.messages[0].id if response.messages else "unknown"

    if resolve_json_flag(ctx, json_output):
        typer.echo(json.dumps({"message_id": msg_id, "status": "sent", "template": "hello_world", "to": cleaned_phone}, indent=2))
    else:
        success(f"Test message (hello_world) sent to [bold]+{cleaned_phone}[/bold]\nMessage ID: {msg_id}")
