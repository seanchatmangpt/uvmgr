"""
uvmgr.commands.tool
===================

Light-weight wrapper that lets you

  • run any console-script in the project’s virtual-env
  • install additional tools on-the-fly
  • locate the bin/ directory that hosts entry-points

Examples
--------
uvmgr tool run black --version
uvmgr tool install httpie
uvmgr tool dir
"""

from __future__ import annotations

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import ToolAttributes, ToolOperations
from uvmgr.core.shell import colour
from uvmgr.ops import tools as tools_ops

from .. import main as cli_root

tool_app = typer.Typer(help="Run or manage extra tools inside the venv")
cli_root.app.add_typer(tool_app, name="tool")  # ← mount on the root CLI


# ──────────────────────────────────────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────────────────────────────────────
@tool_app.command("run")
@instrument_command("tool_run", track_args=True)
def run(
    pkg_and_args: list[str] = typer.Argument(
        ...,
        metavar="COMMAND [ARGS]...",
        help="Tool name followed by its arguments (e.g.  black --check src/)",
    ),
):
    """Execute an installed console-script."""
    if not pkg_and_args:  # happy-path code rarely reaches this
        typer.echo("No command supplied", err=True)
        raise typer.Exit(1)

    command, *args = pkg_and_args
    tools_ops.run(command, args)


@tool_app.command("install")
@instrument_command("tool_install", track_args=True)
def install(
    pkgs: list[str] = typer.Argument(
        ...,
        metavar="PACKAGE...",
        help="One or more PyPI package names to install in the venv",
    ),
):
    """Install additional tools via *uv pip install*."""
    tools_ops.install(pkgs)


@tool_app.command("dir")
@instrument_command("tool_dir", track_args=True)
def dir_() -> None:
    """Print the venv’s *bin* directory that hosts console-scripts."""
    colour(tools_ops.tool_dir(), "cyan")
