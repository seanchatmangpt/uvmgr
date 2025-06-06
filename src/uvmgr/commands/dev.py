"""
DX shortcuts: lint / test / serve
"""

from __future__ import annotations

import typer
from typing import List

from .. import main as cli_root
from uvmgr.core.shell import colour
from uvmgr.ops import devtasks as ops

dev_app = typer.Typer(help="Developer tasks: lint, test, serve")
cli_root.app.add_typer(dev_app)


@dev_app.command()
def lint():
    """Run Ruff + MyPy + Pre-commit."""
    ops.lint()


@dev_app.command()
def test(
    extra: List[str] = typer.Argument(None, help="Extra pytest args", show_default=False)
):
    """Run coverage + pytest."""
    ops.test(extra)


@dev_app.command()
def explain(
    model: str = typer.Option(
        "ollama/phi3:medium-128k",
        "--model",
        "-m",
        help="AI model to use for explanation",
    ),
):
    """Run tests and explain any failures using AI."""
    explanation = ops.explain_tests(model)
    if not explanation:
        colour("✔ All tests passed!", "green")
    else:
        colour("\nTest Failure Analysis:", "yellow")
        colour(explanation, "cyan")


@dev_app.command()
def serve(
    dev: bool = typer.Option(False, "--dev", help="Reload mode"),
    host: str = typer.Option("0.0.0.0", "--host"),
    port: str = typer.Option("8000", "--port"),
):
    """Start FastAPI dev server (template projects only)."""
    ops.serve(dev, host, port)
