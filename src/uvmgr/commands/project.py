import typer

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import ProjectAttributes, ProjectOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import project as project_ops

from .. import main as cli_root

proj_app = typer.Typer(help="Project scaffolding (Copier template)")
cli_root.app.add_typer(proj_app, name="new")


@proj_app.command()
@instrument_command("project_new", track_args=True)
def new(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Directory / project name"),
    fastapi: bool = typer.Option(False, "--fastapi", help="Include FastAPI API skeleton"),
    typer_cli: bool = typer.Option(True, "--typer/--no-typer", help="Include Typer CLI skeleton"),
):
    # Track project creation
    add_span_attributes(**{
        ProjectAttributes.OPERATION: ProjectOperations.CREATE,
        ProjectAttributes.NAME: name,
        ProjectAttributes.LANGUAGE: "python",
        "project.fastapi": fastapi,
        "project.typer_cli": typer_cli,
    })
    add_span_event("project.new.started", {
        "name": name,
        "fastapi": fastapi,
        "typer_cli": typer_cli
    })
    
    payload = project_ops.new(name, fastapi=fastapi, typer_cli=typer_cli)
    
    # Track successful creation
    add_span_attributes(**{
        "project.path": payload.get("path"),
        "project.created": True,
    })
    add_span_event("project.new.completed", {
        "path": payload.get("path"),
        "success": True
    })
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour(f"✔ created project in {payload['path']}", "green")
