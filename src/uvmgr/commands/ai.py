"""
Typer sub-app:  uvmgr ai …
"""

from __future__ import annotations

import pathlib
import typer

from .. import main as cli_root
from uvmgr.core.shell import colour, dump_json, markdown
from uvmgr.ops import ai as ai_ops

ai_app = typer.Typer(help="Local or remote Language-Model helpers")
cli_root.app.add_typer(ai_app, name="ai")

_DEFAULT_MODEL = "ollama/phi3:medium-128k"


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #
def _maybe_json(ctx: typer.Context, payload):
    if ctx.meta.get("json"):
        dump_json(payload)
        raise typer.Exit()


# --------------------------------------------------------------------------- #
# Verbs
# --------------------------------------------------------------------------- #
@ai_app.command("ask")
def ask(
    ctx: typer.Context,
    prompt: str = typer.Argument(..., show_default=False),
    model: str = typer.Option(_DEFAULT_MODEL, "--model", "-m"),
):
    reply = ai_ops.ask(model, prompt)
    _maybe_json(ctx, {"reply": reply})
    colour(reply, "cyan")


@ai_app.command("plan")
def plan(
    ctx: typer.Context,
    topic: str,
    model: str = typer.Option(_DEFAULT_MODEL, "--model", "-m"),
    out: pathlib.Path | None = typer.Option(None, "--out", "-o", dir_okay=False),
):
    md = ai_ops.plan(model, topic, out)
    _maybe_json(ctx, {"plan": md})
    markdown(md)


@ai_app.command("fix-tests")
def fix_tests(
    ctx: typer.Context,
    model: str = typer.Option(_DEFAULT_MODEL, "--model", "-m"),
    patch: pathlib.Path = typer.Option("fix.patch", "--patch", "-p"),
):
    diff = ai_ops.fix_tests(model, patch)
    if not diff:
        colour("✔ tests already pass", "green")
    else:
        colour(f"Patch written to {patch}", "green")
