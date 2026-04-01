import json

import typer
from rich.console import Console
from rich.table import Table

from meta_cli.config.config_manager import ConfigManager
from meta_cli.utils import success

console = Console()
config_app = typer.Typer(help="Inspect and manage local CLI configuration.", no_args_is_help=True)


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "****"
    return token[:6] + "..." + token[-4:]


@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@config_app.command("show")
def show_config(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output as machine-readable JSON."),
    reveal: bool = typer.Option(False, "--reveal", help="Show full access token (use with caution)."),
):
    """Show current configuration (token is masked by default)."""
    config = ConfigManager().load()

    token = config.access_token or ""
    displayed_token = token if reveal else (_mask_token(token) if token else "")

    if json_output:
        data = config.model_dump()
        if not reveal and data.get("access_token"):
            data["access_token"] = _mask_token(data["access_token"])
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table("KEY", "VALUE", show_header=False, show_lines=False, box=None)
    table.add_row("[dim]access_token[/dim]", displayed_token or "[dim]not set[/dim]")
    table.add_row("[dim]default_app_id[/dim]", config.default_app_id or "[dim]not set[/dim]")
    table.add_row("[dim]waba_id[/dim]", config.waba_id or "[dim]not set[/dim]")
    table.add_row("[dim]phone_number_id[/dim]", config.phone_number_id or "[dim]not set[/dim]")
    console.print(table)


@config_app.command("reset")
def reset_config(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
):
    """Clear all stored configuration."""
    if not force:
        typer.confirm("This will clear your token and all stored IDs. Continue?", abort=True)

    cm = ConfigManager()
    config_path = cm.config_path
    if config_path.exists():
        config_path.unlink()
        success("Configuration cleared.")
    else:
        console.print("[dim]No configuration file found.[/dim]")
