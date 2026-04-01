import re
from typing import Callable, Optional

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel

console = Console()
err_console = Console(stderr=True)


def validate_phone_number(phone: str) -> str:
    """Strip formatting and validate E.164 phone number. Returns digits only."""
    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone)
    if not re.match(r"^[1-9]\d{6,14}$", cleaned):
        raise typer.BadParameter(
            f"Invalid phone number '{phone}'. Must include country code (e.g. +14155552671 or 14155552671)."
        )
    return cleaned


def resolve_json_flag(ctx: typer.Context, local_json: bool) -> bool:
    """Returns True if --json was set at any level (command or root)."""
    from meta_cli.cli import AppState
    state = ctx.find_object(AppState)
    return local_json or (state is not None and state.json_output)


def output_or_json(ctx: typer.Context, table_fn: Callable, data: BaseModel, local_json: bool = False) -> None:
    if resolve_json_flag(ctx, local_json):
        typer.echo(data.model_dump_json(indent=2))
    else:
        table_fn()


def error_exit(message: str, hint: Optional[str] = None) -> None:
    body = f"[red]{message}[/red]"
    if hint:
        body += f"\n\n[dim]{hint}[/dim]"
    err_console.print(Panel(body, title="[bold red]Error[/bold red]", border_style="red"))
    raise typer.Exit(code=1)


def success(message: str) -> None:
    console.print(Panel(f"[green]{message}[/green]", border_style="green"))
