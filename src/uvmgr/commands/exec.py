"""
uvmgr.commands.exec - Python Script Execution
===========================================

Execute Python scripts with uv run for dependency management.

This module provides CLI commands for executing Python scripts using uv run,
which automatically manages dependencies and virtual environments. Supports
both file-based scripts and stdin input with flexible dependency management.

Key Features
-----------
• **uv Integration**: Automatic dependency management with uv run
• **Flexible Input**: Support for file scripts and stdin input
• **Dependency Management**: Automatic and manual dependency installation
• **Project Isolation**: Option to exclude current project dependencies
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **script**: Execute a Python script file
- **fallback**: Execute scripts directly (default behavior)

Execution Modes
--------------
- **File Scripts**: Execute Python files with automatic dependency resolution
- **Stdin Input**: Execute Python code from standard input
- **Inline Dependencies**: Support for # /// script metadata format
- **Manual Dependencies**: Specify dependencies with --with option

Examples
--------
    >>> # Run a script file
    >>> uvmgr exec script.py
    >>> 
    >>> # Run with arguments
    >>> uvmgr exec script.py arg1 arg2
    >>> 
    >>> # Run with additional dependencies
    >>> uvmgr exec --with rich script.py
    >>> 
    >>> # Run without current project
    >>> uvmgr exec --no-project script.py
    >>> 
    >>> # Run from stdin
    >>> echo 'print("hello")' | uvmgr exec -

Dependency Resolution
--------------------
1. **Inline Metadata**: Scripts can specify dependencies using # /// format
2. **Manual Dependencies**: Use --with option to specify additional packages
3. **Project Dependencies**: Current project is installed by default
4. **Isolation**: Use --no-project to exclude current project

See Also
--------
- :mod:`uvmgr.ops.exec` : Execution operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import pathlib

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import ProcessAttributes
from uvmgr.ops import exec as exec_ops

app = typer.Typer(
    help="Execute Python scripts with uv run",
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
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


@app.command("script")
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
