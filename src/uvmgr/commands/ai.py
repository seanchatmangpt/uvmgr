"""
Typer sub-app:  uvmgr ai …
"""

from __future__ import annotations

import pathlib

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import AIAttributes
from uvmgr.core.shell import colour, dump_json, markdown
from uvmgr.ops import ai as ai_ops

from .. import main as cli_root

ai_app = typer.Typer(help="Local or remote Language-Model helpers")
cli_root.app.add_typer(ai_app, name="ai")

# Create ollama subcommand
ollama_app = typer.Typer(help="Manage Ollama models and interactions")
ai_app.add_typer(ollama_app, name="ollama")

_DEFAULT_MODEL = "ollama/phi3:medium-128k"


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #
def _maybe_json(ctx: typer.Context, payload):
    if ctx.meta.get("json"):
        dump_json(payload)
        raise typer.Exit()


# --------------------------------------------------------------------------- #
# Ollama Commands
# --------------------------------------------------------------------------- #
@ollama_app.command("list")
@instrument_command("ai_ollama_list", track_args=True)
def list_models(
    ctx: typer.Context,
):
    """List all available Ollama models."""
    # Track Ollama list operation
    add_span_attributes(
        **{
            AIAttributes.OPERATION: "list_models",
            AIAttributes.PROVIDER: "ollama",
        }
    )
    add_span_event("ai.ollama.list.started")
    models = ai_ops.list_models()
    if not models:
        colour("No Ollama models found. Make sure Ollama is running.", "yellow")
        raise typer.Exit(1)

    if ctx.meta.get("json"):
        dump_json({"models": models})
        raise typer.Exit()

    colour("Available Ollama models:", "green")
    for model in models:
        colour(f"• {model}", "cyan")


@ollama_app.command("delete")
@instrument_command("ai_ollama_delete", track_args=True)
def delete_model(
    ctx: typer.Context,
    model: str = typer.Argument(..., help="Name of the model to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Delete without confirmation"),
):
    """Delete an Ollama model."""
    # Track Ollama delete operation
    add_span_attributes(
        **{
            AIAttributes.OPERATION: "delete_model",
            AIAttributes.PROVIDER: "ollama",
            AIAttributes.MODEL: model,
            "ai.force_delete": force,
        }
    )
    add_span_event("ai.ollama.delete.started", {"model": model})
    # First verify the model exists
    models = ai_ops.list_models()
    if model not in models:
        colour(
            f"Model '{model}' not found. Use 'uvmgr ai ollama list' to see available models.", "red"
        )
        raise typer.Exit(1)

    # Ask for confirmation unless --force is used
    if not force:
        if not typer.confirm(f"Are you sure you want to delete the model '{model}'?"):
            raise typer.Abort()

    # Delete the model
    if ai_ops.delete_model(model):
        colour(f"✔ Successfully deleted model '{model}'", "green")
    else:
        colour(f"Failed to delete model '{model}'", "red")
        raise typer.Exit(1)


# --------------------------------------------------------------------------- #
# AI Commands
# --------------------------------------------------------------------------- #
@ai_app.command("ask")
@instrument_command("ai_ask", track_args=True)
def ask(
    ctx: typer.Context,
    prompt: str = typer.Argument(..., show_default=False),
    model: str = typer.Option(_DEFAULT_MODEL, "--model", "-m"),
):
    # Track AI ask operation
    add_span_attributes(
        **{
            AIAttributes.OPERATION: "ask",
            AIAttributes.MODEL: model,
            AIAttributes.PROVIDER: model.split("/")[0] if "/" in model else "unknown",
            "ai.prompt_length": len(prompt),
        }
    )
    add_span_event("ai.ask.started", {"model": model})
    reply = ai_ops.ask(model, prompt)
    _maybe_json(ctx, {"reply": reply})
    colour(reply, "cyan")


@ai_app.command("plan")
@instrument_command("ai_plan", track_args=True)
def plan(
    ctx: typer.Context,
    topic: str,
    model: str = typer.Option(_DEFAULT_MODEL, "--model", "-m"),
    out: pathlib.Path | None = typer.Option(None, "--out", "-o", dir_okay=False),
):
    # Track AI plan operation
    add_span_attributes(
        **{
            AIAttributes.OPERATION: "plan",
            AIAttributes.MODEL: model,
            AIAttributes.PROVIDER: model.split("/")[0] if "/" in model else "unknown",
            "ai.topic": topic,
        }
    )
    add_span_event("ai.plan.started", {"model": model, "topic": topic})
    md = ai_ops.plan(model, topic, out)
    _maybe_json(ctx, {"plan": md})
    markdown(md)


@ai_app.command("fix-tests")
@instrument_command("ai_fix_tests", track_args=True)
def fix_tests(
    ctx: typer.Context,
    model: str = typer.Option(_DEFAULT_MODEL, "--model", "-m"),
    patch: pathlib.Path = typer.Option("fix.patch", "--patch", "-p"),
):
    # Track AI fix-tests operation
    add_span_attributes(
        **{
            AIAttributes.OPERATION: "fix_tests",
            AIAttributes.MODEL: model,
            AIAttributes.PROVIDER: model.split("/")[0] if "/" in model else "unknown",
        }
    )
    add_span_event("ai.fix_tests.started", {"model": model})
    diff = ai_ops.fix_tests(model, patch)
    if not diff:
        colour("✔ tests already pass", "green")
    else:
        colour(f"Patch written to {patch}", "green")
