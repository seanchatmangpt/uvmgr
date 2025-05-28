"""
uvmgr exec – execute Python scripts with uv run.

This command provides a convenient way to run Python scripts using uv run,
which automatically manages dependencies and virtual environments.

Examples
--------
Run a script:
    uvmgr exec script.py

Run a script with arguments:
    uvmgr exec script.py arg1 arg2

Run a script with dependencies:
    uvmgr exec --with rich script.py

Run a script without installing the current project:
    uvmgr exec --no-project script.py

Run a script from stdin:
    echo 'print("hello")' | uvmgr exec -
"""

from __future__ import annotations

import pathlib
import sys
from typing import List

import typer

from .. import main as cli_root
from uvmgr.ops import exec as exec_ops

exec_app = typer.Typer(
    help="Execute Python scripts with uv run",
    rich_markup_mode="rich",
)
cli_root.app.add_typer(exec_app, name="exec")


@exec_app.callback(invoke_without_command=True)
def fallback(
    ctx: typer.Context,
    args: List[str] = typer.Argument(None),
    no_project: bool = typer.Option(
        False,
        "--no-project",
        help="Skip installing the current project",
    ),
    with_deps: List[str] = typer.Option(
        None,
        "--with",
        help="Dependencies to install before running the script",
    ),
):
    """
    Fallback: if the user runs `uvmgr exec <script.py> [args...]`, treat it as a script.
    """
    if not args:
        typer.echo("No command supplied", err=True)
        raise typer.Exit(1)
        
    first = args[0]
    
    # Handle stdin case
    if first == "-":
        exec_ops.script(
            stdin=True,
            argv=args[1:],
            no_project=no_project,
            with_deps=with_deps,
        )
        raise typer.Exit()
        
    # Handle script file case
    if first.endswith(".py") and pathlib.Path(first).exists():
        exec_ops.script(
            path=pathlib.Path(first),
            argv=args[1:],
            no_project=no_project,
            with_deps=with_deps,
        )
        raise typer.Exit()
        
    # Otherwise, print a helpful error
    typer.echo(
        f"[ERROR] No such command or script: {first}\n"
        "If you meant to run a Python script, use:\n"
        "  uvmgr exec <script.py> [args...]\n"
        "or\n"
        "  uvmgr exec script <script.py> [args...]\n"
        "or\n"
        "  uvmgr exec -  # to read from stdin\n",
        err=True,
    )
    raise typer.Exit(1)


@exec_app.command("script")
def script(
    path: pathlib.Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to the Python script to execute",
    ),
    argv: List[str] = typer.Argument(
        None,
        help="Arguments to pass to the script",
    ),
    no_project: bool = typer.Option(
        False,
        "--no-project",
        help="Skip installing the current project",
    ),
    with_deps: List[str] = typer.Option(
        None,
        "--with",
        help="Dependencies to install before running the script",
    ),
):
    """
    Execute a Python script using uv run.
    
    The script will be executed in an environment managed by uv, which will
    automatically handle dependencies and virtual environments.
    
    If the script has inline metadata (using the # /// script format), uv will
    respect those dependencies. Otherwise, you can specify dependencies using
    the --with option.
    """
    exec_ops.script(
        path=path,
        argv=argv,
        no_project=no_project,
        with_deps=with_deps,
    )
