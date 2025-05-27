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

from typing import List

import typer

from .. import main as cli_root
from uvmgr.core.shell import colour
from uvmgr.ops import tools as tools_ops

tool_app = typer.Typer(help="Run or manage extra tools inside the venv")
cli_root.app.add_typer(tool_app, name="tool")   # ← mount on the root CLI


# ──────────────────────────────────────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────────────────────────────────────
@tool_app.command("run")
def run(
    pkg_and_args: List[str] = typer.Argument(
        ...,
        metavar="COMMAND [ARGS]...",
        help="Tool name followed by its arguments (e.g.  black --check src/)",
    )
):
    """Execute an installed console-script."""
    if not pkg_and_args:  # happy-path code rarely reaches this
        typer.echo("No command supplied", err=True)
        raise typer.Exit(1)

    command, *args = pkg_and_args
    tools_ops.run(command, args)


@tool_app.command("install")
def install(
    pkgs: List[str] = typer.Argument(
        ...,
        metavar="PACKAGE...",
        help="One or more PyPI package names to install in the venv",
    )
):
    """Install additional tools via *uv pip install*."""
    tools_ops.install(pkgs)


@tool_app.command("dir")
def dir_() -> None:
    """Print the venv’s *bin* directory that hosts console-scripts."""
    colour(tools_ops.tool_dir(), "cyan")
