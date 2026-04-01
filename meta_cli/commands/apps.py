import typer
from rich.console import Console
from rich.table import Table

from meta_cli.api.graph_client import GraphAPIError, GraphClient, NotFoundError
from meta_cli.config.config_manager import ConfigError, ConfigManager
from meta_cli.models.responses import App, AppsResponse, MeResponse
from meta_cli.utils import error_exit, output_or_json, resolve_json_flag, success

console = Console()
app = typer.Typer(help="Manage Meta developer apps.", no_args_is_help=True)


@app.callback(invoke_without_command=True)
def apps_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


APPS_PERMISSION_HINT = """[bold yellow]Could not auto-list apps.[/bold yellow]

The [cyan]user_applications[/cyan] permission is required, which is not granted by default.

[bold]Find your App ID:[/bold]
  1. Go to [link=https://developers.facebook.com/apps]https://developers.facebook.com/apps[/link]
  2. Click your app — the App ID is shown at the top of the dashboard
  3. Run: [bold green]meta apps use <app-id>[/bold green]

[dim]If you're using a System User token, make sure the System User
has been added to the app with the required permissions.[/dim]"""


@app.command("list")
def list_apps(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output as machine-readable JSON."),
):
    """List all Meta apps associated with your account."""
    cm = ConfigManager()
    try:
        token = cm.require_token()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    client = GraphClient(token)
    with console.status("Fetching apps..."):
        try:
            data = client.get("/me/apps", params={"fields": "id,name,category"})
        except GraphAPIError as e:
            # Code 100 = field doesn't exist / missing permission
            if e.code == 100:
                from rich.panel import Panel
                console.print(Panel(APPS_PERMISSION_HINT, title="[bold]meta apps list[/bold]", border_style="yellow", padding=(1, 2)))
                raise typer.Exit(code=1)
            error_exit(f"API error: {e.message}")

    response = AppsResponse.model_validate(data)

    def render_table():
        table = Table("APP_ID", "NAME", "CATEGORY", show_lines=False)
        for a in response.data:
            table.add_row(a.id, a.name, a.category or "-")
        if not response.data:
            console.print("[dim]No apps found.[/dim]")
        else:
            console.print(table)

    output_or_json(ctx, render_table, response, json_output)


@app.command("use")
def use_app(
    ctx: typer.Context,
    app_id: str = typer.Argument(..., help="App ID to set as default"),
):
    """Set the default app for subsequent commands."""
    cm = ConfigManager()
    try:
        token = cm.require_token()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    client = GraphClient(token)
    with console.status(f"Verifying app {app_id}..."):
        try:
            data = client.get(f"/{app_id}", params={"fields": "id,name"})
        except NotFoundError:
            error_exit(f"App '{app_id}' not found.")
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    app_data = App.model_validate(data)
    cm.update(default_app_id=app_id)
    success(f"Default app set to [bold]{app_data.name}[/bold] (ID: {app_id})")


@app.command("info")
def app_info(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output as machine-readable JSON."),
):
    """Show details for the currently selected app."""
    cm = ConfigManager()
    try:
        token = cm.require_token()
        app_id = cm.require_app_id()
    except ConfigError as e:
        error_exit(str(e), hint=e.hint)

    client = GraphClient(token)
    with console.status("Fetching app info..."):
        try:
            data = client.get(f"/{app_id}", params={"fields": "id,name,category,description"})
        except GraphAPIError as e:
            error_exit(f"API error: {e.message}")

    app_data = App.model_validate(data)

    def render_table():
        table = Table("FIELD", "VALUE", show_header=False, show_lines=False)
        table.add_row("ID", app_data.id)
        table.add_row("Name", app_data.name)
        table.add_row("Category", app_data.category or "-")
        table.add_row("Description", app_data.description or "-")
        console.print(table)

    output_or_json(ctx, render_table, app_data, json_output)
