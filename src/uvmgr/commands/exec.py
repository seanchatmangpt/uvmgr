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

import typer

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import ProcessAttributes
from uvmgr.ops import exec as exec_ops

from .. import main as cli_root

exec_app = typer.Typer(
    help="Execute Python scripts with uv run",
    rich_markup_mode="rich",
)
cli_root.app.add_typer(exec_app, name="exec")


@exec_app.callback(invoke_without_command=True)
@instrument_command("exec_fallback", track_args=True)
def fallback(
    ctx: typer.Context,
    args: list[str] = typer.Argument(None),
    no_project: bool = typer.Option(
        False,
        "--no-project",
        help="Skip installing the current project",
    ),
    with_deps: list[str] = typer.Option(
        None,
        "--with",
        help="Dependencies to install before running the script",
    ),
):
    """
    Fallback: if the user runs `uvmgr exec <script.py> [args...]`, treat it as a script.
    """
    # Track exec operation
    if args:
        add_span_attributes(
            **{
                ProcessAttributes.OPERATION: "exec",
                ProcessAttributes.EXECUTABLE: "python",
                "exec.target": args[0],
                "exec.no_project": no_project,
            }
        )
        add_span_event("exec.started", {"mode": "fallback"})
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
@instrument_command("exec_script", track_args=True)
def script(
    path: pathlib.Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to the Python script to execute",
    ),
    argv: list[str] = typer.Argument(
        None,
        help="Arguments to pass to the script",
    ),
    no_project: bool = typer.Option(
        False,
        "--no-project",
        help="Skip installing the current project",
    ),
    with_deps: list[str] = typer.Option(
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
    # Track script execution
    add_span_attributes(
        **{
            ProcessAttributes.OPERATION: "exec_script",
            ProcessAttributes.EXECUTABLE: "python",
            "exec.script_path": str(path),
            "exec.no_project": no_project,
        }
    )
    add_span_event("exec.script.started", {"script": str(path)})
    exec_ops.script(
        path=path,
        argv=argv,
        no_project=no_project,
        with_deps=with_deps,
    )
