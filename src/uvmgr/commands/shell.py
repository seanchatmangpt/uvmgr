"""
uvmgr shell open
"""

from __future__ import annotations

import typer

from .. import main as cli_root
from uvmgr.ops import shell as shell_ops

shell_app = typer.Typer(help="Open IPython / Python REPL in project env")
cli_root.app.add_typer(shell_app, name="shell")


@shell_app.command("open")
def open_():
    """Drop into IPython if available, else plain REPL."""
    shell_ops.open()
