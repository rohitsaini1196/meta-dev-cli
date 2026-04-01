import typer
from rich.console import Console
from rich.table import Table

from meta_cli.api.graph_client import GraphAPIError, GraphClient
from meta_cli.config.config_manager import ConfigError, ConfigManager
from meta_cli.models.responses import TemplatesResponse
from meta_cli.utils import error_exit, output_or_json, resolve_json_flag

console = Console()
templates_app = typer.Typer(help="Manage WhatsApp message templates.", no_args_is_help=True)


@templates_app.callback(invoke_without_command=True)
def templates_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@templates_app.command("list")
def list_templates(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output as machine-readable JSON."),
):
    """List all message templates for the current WhatsApp Business Account."""
    cm = ConfigManager()
    try:
        token = cm.require_token()
        waba_id = cm.require_waba_id()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    client = GraphClient(token)
    with console.status("Fetching templates..."):
        try:
            data = client.get(
                f"/{waba_id}/message_templates",
                params={"fields": "id,name,status,category,language"},
            )
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    response = TemplatesResponse.model_validate(data)

    def render_table():
        table = Table("ID", "NAME", "STATUS", "CATEGORY", "LANGUAGE", show_lines=False)
        for t in response.data:
            table.add_row(t.id, t.name, t.status, t.category, t.language or "-")
        if not response.data:
            console.print("[dim]No templates found.[/dim]")
        else:
            console.print(table)

    output_or_json(ctx, render_table, response, json_output)
