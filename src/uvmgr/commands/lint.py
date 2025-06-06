"""
uvmgr.commands.lint – linting sub-command.

Provides commands for running code quality checks using Ruff.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from uvmgr.core.lint import enforce_ruff, map_exception
from uvmgr.cli_utils import handle_cli_exception, maybe_json

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
    result = subprocess.run(args, check=False)
    return result.returncode


@app.command()
def check(
    ctx: typer.Context,
    path: Optional[Path] = typer.Argument(
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
        
        maybe_json(ctx, {"status": "success", "message": "✅ No Ruff violations found"}, exit_code=0)
        console.print("[green]✅ No Ruff violations found[/green]")
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=map_exception(e))


@app.command()
def format(
    ctx: typer.Context,
    path: Optional[Path] = typer.Argument(
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
    try:
        cmd = ["format"]
        if check:
            cmd.append("--check")
        
        if _run_ruff(cmd, str(path) if path else "."):
            maybe_json(ctx, {"status": "error", "message": "❌ Formatting issues found"}, exit_code=1)
            console.print("[red]❌ Formatting issues found[/red]")
            sys.exit(1)
        
        maybe_json(ctx, {"status": "success", "message": "✅ Code formatted successfully"}, exit_code=0)
        console.print("[green]✅ Code formatted successfully[/green]")
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=map_exception(e))


@app.command()
def fix(
    ctx: typer.Context,
    path: Optional[Path] = typer.Argument(
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
    try:
        # First run the formatter
        if _run_ruff(["format"], str(path) if path else "."):
            maybe_json(ctx, {"status": "error", "message": "❌ Formatting failed"}, exit_code=1)
            console.print("[red]❌ Formatting failed[/red]")
            sys.exit(1)
        
        # Then run the linter with fixes
        if _run_ruff(["check", "--fix"], str(path) if path else "."):
            maybe_json(ctx, {"status": "error", "message": "❌ Some issues could not be fixed automatically"}, exit_code=1)
            console.print("[red]❌ Some issues could not be fixed automatically[/red]")
            sys.exit(1)
        
        maybe_json(ctx, {"status": "success", "message": "✅ All issues fixed successfully"}, exit_code=0)
        console.print("[green]✅ All issues fixed successfully[/green]")
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=map_exception(e)) 