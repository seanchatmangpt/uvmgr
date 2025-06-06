from pathlib import Path

import typer

from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import project as project_ops

from .. import main as cli_root

proj_app = typer.Typer(help="Project scaffolding (Copier template)")
cli_root.app.add_typer(proj_app, name="new")


@proj_app.command()
def new(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Directory / project name"),
    fastapi: bool = typer.Option(False, "--fastapi", help="Include FastAPI API skeleton"),
    typer_cli: bool = typer.Option(True, "--typer/--no-typer", help="Include Typer CLI skeleton"),
):
    payload = project_ops.new(name, fastapi=fastapi, typer_cli=typer_cli)
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour(f"✔ created project in {payload['path']}", "green")
