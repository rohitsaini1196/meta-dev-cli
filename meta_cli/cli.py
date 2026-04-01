from dataclasses import dataclass, field

import typer

from meta_cli.commands import auth, apps
from meta_cli.commands.config import config_app
from meta_cli.commands.whatsapp import wa_app

app = typer.Typer(
    name="meta",
    help="Meta Developer CLI — manage Meta apps and WhatsApp Cloud API.\n\nNot affiliated with Meta Platforms, Inc.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@dataclass
class AppState:
    json_output: bool = field(default=False)


@app.callback()
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as machine-readable JSON.",
        is_eager=False,
    ),
):
    ctx.ensure_object(AppState)
    ctx.obj.json_output = json_output


app.command("login")(auth.login)
app.add_typer(apps.app, name="apps")
app.add_typer(wa_app, name="wa")
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
