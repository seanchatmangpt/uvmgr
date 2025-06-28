"""
uvmgr.commands.tool_backup - Legacy Tool Management
=================================================

Light-weight wrapper for running console-scripts in project virtual environment.

This module provides legacy tool management functionality for running
console-scripts in the project's virtual environment, installing additional
tools, and locating the bin directory. This is a backup/legacy version
of the enhanced tool module.

Key Features
-----------
• **Console Script Execution**: Run any console-script in project venv
• **On-the-fly Installation**: Install additional tools as needed
• **Bin Directory Location**: Find the directory hosting entry-points
• **Virtual Environment Integration**: Seamless venv integration
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **run**: Execute an installed console-script
- **install**: Install additional tools via uv pip install
- **dir**: Print the venv's bin directory location

Examples
--------
    >>> # Run a tool
    >>> uvmgr tool run black --version
    >>> 
    >>> # Install a tool
    >>> uvmgr tool install httpie
    >>> 
    >>> # Show bin directory
    >>> uvmgr tool dir

Notes
-----
This is a legacy/backup version of the tool module. For enhanced functionality
including uvx integration, smart recommendations, and health checking, use
the main tool module instead.

See Also
--------
- :mod:`uvmgr.commands.tool` : Enhanced tool management
- :mod:`uvmgr.ops.tools` : Tool operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
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
    """Print the venv's *bin* directory that hosts console-scripts."""
    colour(tools_ops.tool_dir(), "cyan")
