"""
Typer sub-app: uvmgr deps …
"""

from __future__ import annotations

from typing import List

import typer

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
def add(
    ctx: typer.Context,
    pkgs: list[str] = typer.Argument(..., help="Packages e.g. fastapi requests"),
    dev: bool = typer.Option(False, "--dev", "-D", help="Add to dev group"),
):
    res = deps_ops.add(pkgs, dev=dev)
    _maybe_json(ctx, res)
    colour(f"✔ added {' '.join(pkgs)}", "green")


@deps_app.command("remove")
def remove(
    ctx: typer.Context,
    pkgs: list[str] = typer.Argument(...),
):
    res = deps_ops.remove(pkgs)
    _maybe_json(ctx, res)
    colour(f"✔ removed {' '.join(pkgs)}", "green")


@deps_app.command("upgrade")
def upgrade(
    ctx: typer.Context,
    all_: bool = typer.Option(False, "--all", help="Upgrade everything"),
    pkgs: list[str] = typer.Argument(None, help="Specific packages"),
):
    res = deps_ops.upgrade(all_pkgs=all_, pkgs=pkgs or None)
    _maybe_json(ctx, res)
    colour("✔ dependencies upgraded", "green")


@deps_app.command("list")
def _list(ctx: typer.Context):
    pkgs = deps_ops.list_pkgs()
    _maybe_json(ctx, pkgs)
    for p in pkgs:
        colour(p, "cyan")
