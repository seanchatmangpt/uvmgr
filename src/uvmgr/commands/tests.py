"""
Typer sub-app: uvmgr tests …

This module implements a command (run) and a subcommand (coverage) to run the test suite and generate coverage reports.
"""

from __future__ import annotations

import subprocess
import sys
import typer

from .. import main as cli_root

tests_app = typer.Typer(help="Run the test suite (and coverage) using pytest and coverage.")

# Mount the sub-app under the name 'tests' (so that 'uvmgr tests' works)
cli_root.app.add_typer(tests_app, name="tests")


@tests_app.command("run")
def run_tests(verbose: bool = typer.Option(False, "--verbose", "-v", help="Run tests verbosely.")):
    """Run the test suite using pytest."""
    cmd = ["pytest"]
    if verbose:
        cmd.append("-v")
    subprocess.run(cmd, check=True)


@tests_app.command("coverage")
def run_coverage(verbose: bool = typer.Option(False, "--verbose", "-v", help="Run coverage verbosely.")):
    """Generate coverage reports using coverage run + coverage report."""
    cmd_run = ["coverage", "run", "--module", "pytest"]
    cmd_report = ["coverage", "report"]
    if verbose:
        cmd_run.append("-v")
    subprocess.run(cmd_run, check=True)
    subprocess.run(cmd_report, check=True) 