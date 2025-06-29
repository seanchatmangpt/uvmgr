"""
uvmgr.commands.shell - Interactive Shell and REPL
===============================================

Open IPython or Python REPL in project environment.

This module provides CLI commands for launching interactive Python shells
within the project's virtual environment, with automatic dependency
management and project context.

Key Features
-----------
• **Interactive REPL**: Launch Python interactive shell
• **IPython Support**: Automatic IPython detection and usage
• **Project Environment**: Shell runs in project virtual environment
• **Dependency Access**: All project dependencies available
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **open**: Open interactive Python shell (IPython or standard REPL)

Shell Types
----------
- **IPython**: Enhanced interactive shell (preferred)
- **Standard REPL**: Fallback to Python's built-in interactive shell

Examples
--------
    >>> # Open interactive shell
    >>> uvmgr shell open
    >>> 
    >>> # Shell will have access to project dependencies
    >>> # and can import project modules

See Also
--------
- :mod:`uvmgr.ops.shell` : Shell operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import ShellAttributes, ShellOperations
from uvmgr.ops import shell as shell_ops

app = typer.Typer(help="Open IPython / Python REPL in project env")


@app.command("open")
@instrument_command("shell_open", track_args=True)
def open_():
    """Drop into IPython if available, else plain REPL."""
    # Track shell/REPL startup
    add_span_attributes(
        **{
            ShellAttributes.OPERATION: ShellOperations.INTERACTIVE,
            ShellAttributes.INTERACTIVE: True,
            "shell.type": "repl",
        }
    )
    add_span_event("shell.repl.starting", {"type": "interactive"})
    shell_ops.open()
