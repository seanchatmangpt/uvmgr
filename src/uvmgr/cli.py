"""Root Typer application for uvmgr."""

from __future__ import annotations

import importlib
import importlib.metadata
import os
from types import ModuleType

import typer

from uvmgr.core.instrumentation import instrument_command
from uvmgr.logging_config import setup_logging

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
setup_logging()

app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    help="**uvmgr** – unified Python workflow engine (powered by *uv*).",
    context_settings={"allow_extra_args": True},
)
COMMAND_LOAD_FAILURES: dict[str, str] = {}


def _json_callback(ctx: typer.Context, value: bool) -> None:
    """Record the global machine-readable output preference."""
    if value:
        ctx.meta["json"] = True


def _version_callback(value: bool) -> None:
    """Show the installed version and exit."""
    if not value:
        return
    try:
        version = importlib.metadata.version("uvmgr")
    except importlib.metadata.PackageNotFoundError:
        version = "dev"
    typer.echo(f"uvmgr {version}")
    raise typer.Exit()


@app.callback()
@instrument_command("uvmgr_main", track_args=True)
def _root(
    ctx: typer.Context,
    json_: bool = typer.Option(
        False,
        "--json",
        "-j",
        callback=_json_callback,
        is_eager=True,
        help="Print machine-readable JSON.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Initialize command context without ambient actuation."""


def _find_typer_app(module: ModuleType) -> typer.Typer | None:
    """Resolve the canonical Typer app from a command module."""
    candidate = getattr(module, "app", None)
    if isinstance(candidate, typer.Typer):
        return candidate
    return next(
        (value for value in vars(module).values() if isinstance(value, typer.Typer)),
        None,
    )


def _unavailable_app(verb: str, error: str) -> typer.Typer:
    """Create a typed, visible refusal surface for a broken enabled command."""
    unavailable = typer.Typer(
        help=f"BUILD_BROKEN: enabled command failed to load ({error})",
    )

    @unavailable.callback(invoke_without_command=True)
    def show_failure() -> None:
        typer.echo(
            f"BUILD_BROKEN command={verb} import_error={error}",
            err=True,
        )
        raise typer.Exit(70)

    return unavailable


commands_package = importlib.import_module("uvmgr.commands")
for command_name in commands_package.__all__:
    try:
        command_module = importlib.import_module(f"uvmgr.commands.{command_name}")
        command_app = _find_typer_app(command_module)
        if command_app is None:
            raise ImportError(f"{command_name!r} has no Typer application")
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
        COMMAND_LOAD_FAILURES[command_name] = failure
        command_app = _unavailable_app(command_name, failure)

    app.add_typer(command_app, name=command_name.replace("_", "-"))


if __name__ == "__main__":
    app()
