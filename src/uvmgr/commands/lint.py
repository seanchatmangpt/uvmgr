"""
uvmgr.commands.lint - Code Quality and Linting
=============================================

Linting sub-commands for code quality checks and formatting using Ruff.

This module provides comprehensive code quality tools using Ruff for
linting, formatting, and automatic fixing of Python code. All operations
are instrumented with OpenTelemetry for monitoring code quality metrics.

Key Features
-----------
• **Ruff Integration**: Fast Python linter and formatter
• **Multiple Operations**: Check, format, and fix capabilities
• **Auto-fixing**: Automatic correction of common issues
• **Path Support**: Flexible path specification for targeted checks
• **JSON Output**: Structured output for automation
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **check**: Run Ruff linter to find code quality issues
- **format**: Format Python code using Ruff formatter
- **fix**: Run both linter and formatter to fix all auto-fixable issues

Operation Modes
--------------
- **Check Mode**: Identify issues without making changes
- **Fix Mode**: Automatically correct fixable issues
- **Format Mode**: Apply consistent code formatting
- **Show Fixes**: Preview changes without applying them

Examples
--------
    >>> # Check code quality
    >>> uvmgr lint check src/
    >>> 
    >>> # Format code
    >>> uvmgr lint format --check
    >>> 
    >>> # Fix all auto-fixable issues
    >>> uvmgr lint fix
    >>> 
    >>> # Check with auto-fixing
    >>> uvmgr lint check --fix

Configuration
------------
Ruff configuration is read from:
- `pyproject.toml` (recommended)
- `ruff.toml`
- `.ruff.toml`

See Also
--------
- :mod:`uvmgr.core.lint` : Core linting utilities
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

from uvmgr.cli_utils import handle_cli_exception, maybe_json
from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.lint import map_exception
from uvmgr.core.process import run_logged
from uvmgr.core.semconv import CliAttributes

app = typer.Typer(
    help="Run code quality checks and formatting using Ruff.",
    rich_markup_mode="rich",
)

console = Console()


def _run_ruff(cmd: list[str], path: str | None = None) -> int:
    """Run Ruff with the given command and path."""
    args = ["ruff"] + cmd
    if path:
        args.append(str(path))
    # Use instrumented subprocess call
    try:
        run_logged(args)
        return 0
    except subprocess.CalledProcessError as e:
        return e.returncode


@app.command()
@instrument_command("lint_check", track_args=True)
def check(
    ctx: typer.Context,
    path: Path | None = typer.Argument(
        None,
        help="Path to check (default: current directory)",
        exists=True,
        dir_okay=True,
        file_okay=True,
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Automatically fix violations",
    ),
    show_fixes: bool = typer.Option(
        False,
        "--show-fixes",
        help="Show what would be fixed without making changes",
    ),
) -> None:
    """
    Run Ruff linter on the specified path.

    If no path is provided, checks the current directory.
    """
    # Track lint operation
    add_span_attributes(**{
        "lint.operation": "check",
        "lint.tool": "ruff",
        "lint.path": str(path) if path else ".",
        "lint.fix": fix,
        "lint.show_fixes": show_fixes,
    })
    add_span_event("lint.check.started", {"path": str(path) if path else "."})

    try:
        cmd = ["check"]
        if fix:
            cmd.append("--fix")
        if show_fixes:
            cmd.append("--show-fixes")

        if _run_ruff(cmd, str(path) if path else "."):
            maybe_json(ctx, {"status": "error", "message": "❌ Ruff violations found"}, exit_code=1)
            console.print("[red]❌ Ruff violations found[/red]")
            sys.exit(1)

        maybe_json(
            ctx, {"status": "success", "message": "✅ No Ruff violations found"}, exit_code=0
        )
        console.print("[green]✅ No Ruff violations found[/green]")
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=map_exception(e))


@app.command()
@instrument_command("lint_format", track_args=True)
def format(
    ctx: typer.Context,
    path: Path | None = typer.Argument(
        None,
        help="Path to format (default: current directory)",
        exists=True,
        dir_okay=True,
        file_okay=True,
    ),
    check: bool = typer.Option(
        False,
        "--check",
        "-c",
        help="Check if files are formatted without making changes",
    ),
) -> None:
    """
    Format Python code using Ruff formatter.

    If no path is provided, formats the current directory.
    """
    # Track format operation
    add_span_attributes(**{
        "lint.operation": "format",
        "lint.tool": "ruff",
        "lint.path": str(path) if path else ".",
        "lint.check_only": check,
    })
    add_span_event("lint.format.started", {"path": str(path) if path else ".", "check_only": check})

    try:
        cmd = ["format"]
        if check:
            cmd.append("--check")

        if _run_ruff(cmd, str(path) if path else "."):
            maybe_json(
                ctx, {"status": "error", "message": "❌ Formatting issues found"}, exit_code=1
            )
            console.print("[red]❌ Formatting issues found[/red]")
            sys.exit(1)

        maybe_json(
            ctx, {"status": "success", "message": "✅ Code formatted successfully"}, exit_code=0
        )
        console.print("[green]✅ Code formatted successfully[/green]")
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=map_exception(e))


@app.command()
@instrument_command("lint_fix", track_args=True)
def fix(
    ctx: typer.Context,
    path: Path | None = typer.Argument(
        None,
        help="Path to fix (default: current directory)",
        exists=True,
        dir_okay=True,
        file_okay=True,
    ),
) -> None:
    """
    Run Ruff linter and formatter to fix all auto-fixable issues.

    This is equivalent to running both `check --fix` and `format`.
    """
    # Track fix operation
    add_span_attributes(**{
        "lint.operation": "fix",
        "lint.tool": "ruff",
        "lint.path": str(path) if path else ".",
        "lint.auto_fix": True,
    })
    add_span_event("lint.fix.started", {"path": str(path) if path else "."})

    try:
        # First run the formatter
        if _run_ruff(["format"], str(path) if path else "."):
            maybe_json(ctx, {"status": "error", "message": "❌ Formatting failed"}, exit_code=1)
            console.print("[red]❌ Formatting failed[/red]")
            sys.exit(1)

        # Then run the linter with fixes
        if _run_ruff(["check", "--fix"], str(path) if path else "."):
            maybe_json(
                ctx,
                {"status": "error", "message": "❌ Some issues could not be fixed automatically"},
                exit_code=1,
            )
            console.print("[red]❌ Some issues could not be fixed automatically[/red]")
            sys.exit(1)

        maybe_json(
            ctx, {"status": "success", "message": "✅ All issues fixed successfully"}, exit_code=0
        )
        console.print("[green]✅ All issues fixed successfully[/green]")
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=map_exception(e))
