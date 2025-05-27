"""
uvmgr.cli
=========

Root Typer application.

• Sets up logging once (plain `logging` + optional OpenTelemetry)
• Adds a global `--json / -j` flag
• Dynamically mounts every sub-command package found in **uvmgr.commands**
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import typer

from uvmgr.core.shell import colour, dump_json
from uvmgr.core.telemetry import setup_logging

import os
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

# ──────────────────────────────────────────────────────────────────────────────
#  Logging bootstrap (idempotent)
# ──────────────────────────────────────────────────────────────────────────────
setup_logging("INFO")

# ──────────────────────────────────────────────────────────────────────────────
#  Root Typer application
# ──────────────────────────────────────────────────────────────────────────────
app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    help="**uvmgr** – unified Python workflow engine (powered by *uv*).",
)

# Record JSON preference in ctx.meta so sub-commands can honour it -------------
def _json_cb(ctx: typer.Context, value: bool):  # noqa: D401
    if value:
        ctx.meta["json"] = True


@app.callback()
def _root(                              # noqa: D401
    ctx: typer.Context,
    json_: bool = typer.Option(
        False,
        "--json",
        "-j",
        callback=_json_cb,
        is_eager=True,
        help="Print machine-readable JSON and exit",
    ),
):
    """Callback only sets the JSON flag – no other side-effects."""


def maybe_json(ctx: typer.Context, payload: Any) -> None:
    """
    Utility: in sub-commands call **maybe_json(ctx, data)**; if the user
    passed --json we dump the object and exit early.
    """
    if ctx.meta.get("json"):
        dump_json(payload)
        raise typer.Exit()


# ──────────────────────────────────────────────────────────────────────────────
#  Mount every sub-command defined in *uvmgr.commands*
# ──────────────────────────────────────────────────────────────────────────────
commands_pkg = importlib.import_module("uvmgr.commands")

for verb in commands_pkg.__all__:
    mod = importlib.import_module(f"uvmgr.commands.{verb}")

    # Expect exactly one typer.Typer object in the module's globals ------------
    sub_app = next(
        (obj for obj in mod.__dict__.values() if isinstance(obj, typer.Typer)),
        None,
    )
    if sub_app is None:  # Fail fast during development
        raise ImportError(f"`{verb}` has no Typer sub-app")

    # Mount under the same name (convert _ to - for nicer CLI UX) --------------
    app.add_typer(sub_app, name=verb.replace("_", "-"))

