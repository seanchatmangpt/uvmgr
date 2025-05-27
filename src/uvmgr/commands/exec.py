"""
uvmgr exec script …
"""

from __future__ import annotations

import pathlib
from typing import List

import typer

from .. import main as cli_root
from uvmgr.ops import exec as exec_ops

exec_app = typer.Typer(help="Execute Python script inside project env")
cli_root.app.add_typer(exec_app, name="exec")


@exec_app.command("script")
def script(
    path: pathlib.Path = typer.Argument(..., exists=True, readable=True),
    argv: List[str] = typer.Argument(None, help="Args forwarded to script"),
):
    exec_ops.script(path, argv)
