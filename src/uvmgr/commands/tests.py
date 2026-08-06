"""Test execution, discovery, coverage, and local-CI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from uvmgr.core.instrumentation import (
    add_span_attributes,
    add_span_event,
    instrument_command,
)
from uvmgr.core.testing import TestDiscovery, generate_test_templates
from uvmgr.ops.tests import (
    TestRunOptions,
    TestRunPlan,
    build_coverage_report_plan,
    build_test_plan,
    execute_test_plan,
)
from uvmgr.runtime.tests import TestExecutionReceipt, receipt_as_dict

app = typer.Typer(help="Run pytest through a receipted Command → Ops → Runtime path.")
ci_app = typer.Typer(help="Run repository CI acceptance lanes locally.")
app.add_typer(ci_app, name="ci")
console = Console()

_PASSTHROUGH_CONTEXT = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
}


def _emit_receipt(receipt: TestExecutionReceipt, *, json_output: bool) -> None:
    """Render the execution receipt without changing its standing."""
    if json_output:
        typer.echo(json.dumps(receipt_as_dict(receipt), sort_keys=True))
        return
    console.print(
        f"[bold]{receipt.outcome}[/bold] exit={receipt.exit_code} "
        f"receipt={receipt.receipt_path} sha256={receipt.receipt_sha256}"
    )


def _execute(plan: TestRunPlan, *, json_output: bool) -> None:
    """Execute a plan, emit its receipt, and preserve the process exit code."""
    add_span_attributes(
        **{
            "test.command": list(plan.command),
            "test.working_directory": str(plan.working_directory),
        }
    )
    add_span_event("tests.execution.started", {"command": list(plan.command)})
    receipt = execute_test_plan(plan)
    _emit_receipt(receipt, json_output=json_output)
    add_span_event(
        "tests.execution.completed",
        {
            "exit_code": receipt.exit_code,
            "outcome": receipt.outcome,
            "receipt_sha256": receipt.receipt_sha256,
        },
    )
    if receipt.exit_code:
        raise typer.Exit(receipt.exit_code)


@app.command("run", context_settings=_PASSTHROUGH_CONTEXT)
@instrument_command("tests_run", track_args=True)
def run_tests(  # noqa: PLR0913
    ctx: typer.Context,
    selectors: Annotated[
        list[str] | None,
        typer.Argument(help="Optional pytest paths or node IDs."),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Add pytest verbose output."),
    ] = False,
    parallel: Annotated[
        bool,
        typer.Option("--parallel/--no-parallel", help="Use pytest-xdist."),
    ] = True,
    coverage: Annotated[
        bool,
        typer.Option("--coverage/--no-coverage", help="Collect coverage."),
    ] = True,
    fail_fast: Annotated[
        bool,
        typer.Option("--fail-fast", "-x", help="Stop after the first failure."),
    ] = False,
    test_type: Annotated[
        list[str] | None,
        typer.Option("--type", "-t", help="Marker-backed test type."),
    ] = None,
    marker: Annotated[
        list[str] | None,
        typer.Option("--marker", "-m", help="Pytest marker expression term."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Emit the receipt as JSON."),
    ] = False,
) -> None:
    """Run selected tests while forwarding unknown pytest arguments unchanged."""
    plan = build_test_plan(
        selectors or (),
        ctx.args,
        options=TestRunOptions(
            verbose=verbose,
            parallel=parallel,
            coverage=coverage,
            fail_fast=fail_fast,
            test_types=tuple(test_type or ()),
            markers=tuple(marker or ()),
        ),
    )
    _execute(plan, json_output=json_output)


@app.command("discover")
@instrument_command("tests_discover", track_args=True)
def discover_tests(
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Output discovery as JSON."),
    ] = False,
) -> None:
    """Discover the repository test topology without executing it."""
    discovery = TestDiscovery(Path.cwd())
    discovered = discovery.discover_tests()
    statistics = discovery.get_test_statistics()
    payload = {
        "discovered_tests": {
            test_type.value: [str(path) for path in paths]
            for test_type, paths in discovered.items()
        },
        "statistics": statistics,
    }
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True, default=str))
        return

    table = Table(title="Test topology")
    table.add_column("Type")
    table.add_column("Files", justify="right")
    for test_type, paths in discovered.items():
        table.add_row(test_type.value, str(len(paths)))
    console.print(table)


@app.command("generate")
@instrument_command("tests_generate", track_args=True)
def generate_tests(
    module: Annotated[str, typer.Argument(help="Import path to generate tests for.")],
) -> None:
    """Generate repository-native test templates for one module."""
    templates = generate_test_templates(Path.cwd(), module)
    for template in templates:
        typer.echo(str(template))


@app.command("coverage", context_settings=_PASSTHROUGH_CONTEXT)
@instrument_command("tests_coverage", track_args=True)
def run_coverage(
    ctx: typer.Context,
    selectors: Annotated[
        list[str] | None,
        typer.Argument(help="Optional pytest paths or node IDs."),
    ] = None,
    fail_under: Annotated[
        int | None,
        typer.Option("--fail-under", min=0, max=100),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Emit receipts as JSON."),
    ] = False,
) -> None:
    """Run tests with coverage, then verify the resulting report."""
    _execute(
        build_test_plan(
            selectors or (),
            ctx.args,
            options=TestRunOptions(coverage=True, parallel=False),
        ),
        json_output=json_output,
    )
    _execute(
        build_coverage_report_plan(fail_under=fail_under),
        json_output=json_output,
    )


def _ci_plan(selectors: tuple[str, ...]) -> TestRunPlan:
    """Build the deterministic CI plan shared by CI subcommands."""
    return build_test_plan(
        selectors,
        ("--tb=short",),
        options=TestRunOptions(
            verbose=True,
            parallel=False,
            coverage=True,
            fail_fast=True,
        ),
    )


@ci_app.command("quick")
@instrument_command("tests_ci_quick", track_args=True)
def ci_quick() -> None:
    """Run the fast CLI and import acceptance tests."""
    _execute(
        _ci_plan(("tests/test_cli.py", "tests/test_import.py")),
        json_output=False,
    )


@ci_app.command("verify")
@instrument_command("tests_ci_verify", track_args=True)
def ci_verify() -> None:
    """Run the complete repository test suite with a receipt."""
    _execute(_ci_plan(("tests",)), json_output=False)


@ci_app.command("run")
@instrument_command("tests_ci_run", track_args=True)
def ci_run() -> None:
    """Alias for the complete local CI verification."""
    ci_verify()
