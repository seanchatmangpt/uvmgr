"""
uvmgr shell open
"""

from __future__ import annotations

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import ShellAttributes, ShellOperations
from uvmgr.ops import shell as shell_ops

from .. import main as cli_root

shell_app = typer.Typer(help="Open IPython / Python REPL in project env")
cli_root.app.add_typer(shell_app, name="shell")


@shell_app.command("open")
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
