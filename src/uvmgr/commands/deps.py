"""
Typer sub-app: uvmgr deps …
"""

from __future__ import annotations

import typer

from uvmgr.core.instrumentation import add_span_attributes, instrument_command
from uvmgr.core.semconv import PackageAttributes, PackageOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import deps as deps_ops

from .. import main as cli_root

deps_app = typer.Typer(help="Dependency management (uv add/remove/upgrade)")

cli_root.app.add_typer(deps_app, name="deps")


# --------------------------------------------------------------------------- #
# Shared util
# --------------------------------------------------------------------------- #
def _maybe_json(ctx: typer.Context, payload):
    if ctx.meta.get("json"):
        dump_json(payload)
        raise typer.Exit()


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
@deps_app.command("add")
@instrument_command("deps_add", track_args=True)
def add(
    ctx: typer.Context,
    pkgs: list[str] = typer.Argument(..., help="Packages e.g. fastapi requests"),
    dev: bool = typer.Option(False, "--dev", "-D", help="Add to dev group"),
):
    # Add package operation attributes to span
    add_span_attributes(
        **{
            PackageAttributes.OPERATION: PackageOperations.ADD,
            "package.count": len(pkgs),
            "package.names": ",".join(pkgs),
            PackageAttributes.DEV_DEPENDENCY: dev,
        }
    )

    res = deps_ops.add(pkgs, dev=dev)
    _maybe_json(ctx, res)
    colour(f"✔ added {' '.join(pkgs)}", "green")


@deps_app.command("remove")
@instrument_command("deps_remove", track_args=True)
def remove(
    ctx: typer.Context,
    pkgs: list[str] = typer.Argument(...),
):
    # Add package operation attributes to span
    add_span_attributes(
        **{
            PackageAttributes.OPERATION: PackageOperations.REMOVE,
            "package.count": len(pkgs),
            "package.names": ",".join(pkgs),
        }
    )

    res = deps_ops.remove(pkgs)
    _maybe_json(ctx, res)
    colour(f"✔ removed {' '.join(pkgs)}", "green")


@deps_app.command("upgrade")
@instrument_command("deps_upgrade", track_args=True)
def upgrade(
    ctx: typer.Context,
    all_: bool = typer.Option(False, "--all", help="Upgrade everything"),
    pkgs: list[str] = typer.Argument(None, help="Specific packages"),
):
    # Add package operation attributes to span
    add_span_attributes(
        **{
            PackageAttributes.OPERATION: PackageOperations.UPDATE,
            "package.update.all": all_,
            "package.count": len(pkgs) if pkgs else 0,
        }
    )
    if pkgs:
        add_span_attributes(**{"package.names": ",".join(pkgs)})

    res = deps_ops.upgrade(all_pkgs=all_, pkgs=pkgs or None)
    _maybe_json(ctx, res)
    colour("✔ dependencies upgraded", "green")


@deps_app.command("list")
@instrument_command("deps_list")
def _list(ctx: typer.Context):
    pkgs = deps_ops.list_pkgs()

    # Add package operation attributes to span
    add_span_attributes(
        **{
            PackageAttributes.OPERATION: PackageOperations.LIST,
            "package.count": len(pkgs),
        }
    )

    _maybe_json(ctx, pkgs)
    for p in pkgs:
        colour(p, "cyan")
