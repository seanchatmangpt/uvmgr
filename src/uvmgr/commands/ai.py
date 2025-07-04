"""
uvmgr.commands.ai - AI-Assisted Development
=========================================

Local or remote Language-Model helpers for AI-assisted development.

This module provides CLI commands for interacting with AI models to assist
with development tasks, including code generation, planning, and problem
solving. Supports both local models (via Ollama) and remote AI services.

Key Features
-----------
• **Ollama Integration**: Local AI model management and interaction
• **Multiple Operations**: Ask, plan, and fix-tests capabilities
• **Model Management**: List, delete, and manage local models
• **Code Assistance**: AI-powered code generation and fixes
• **Planning Tools**: AI-assisted project planning and documentation
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
AI Operations
- **ask**: Ask questions to AI models
- **plan**: Generate project plans and documentation
- **fix-tests**: AI-assisted test fixing and generation

Ollama Management
- **ollama list**: List available Ollama models
- **ollama delete**: Remove Ollama models

Default Models
-------------
- **Default**: ollama/phi3:medium-128k
- **Custom**: Specify any model with --model option

Examples
--------
    >>> # Ask AI for help
    >>> uvmgr ai ask "How do I create a Python package?"
    >>> 
    >>> # Generate project plan
    >>> uvmgr ai plan "Build a web API with FastAPI"
    >>> 
    >>> # Fix failing tests
    >>> uvmgr ai fix-tests --patch fix.patch
    >>> 
    >>> # List Ollama models
    >>> uvmgr ai ollama list
    >>> 
    >>> # Delete model
    >>> uvmgr ai ollama delete llama2:7b

See Also
--------
- :mod:`uvmgr.ops.ai` : AI operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import pathlib

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import AIAttributes
from uvmgr.core.shell import colour, dump_json, markdown
from uvmgr.ops import ai as ai_ops

app = typer.Typer(help="Local or remote Language-Model helpers")

# Create ollama subcommand
ollama_app = typer.Typer(help="Manage Ollama models and interactions")
app.add_typer(ollama_app, name="ollama")

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
@app.command("ask")
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


@app.command("plan")
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


@app.command("fix-tests")
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
