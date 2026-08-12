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
from uvmgr.core.testing import TestDiscovery
from uvmgr.core.testing import generate_test_templates as make_test_templates
from uvmgr.ops.tests import (
    CIPipelineResult,
    TestRunOptions,
    TestRunPlan,
    build_ci_plan,
    build_coverage_report_plan,
    build_test_plan,
    ci_pipeline_result_as_dict,
    execute_ci_plan,
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
    """Render an execution receipt without changing its standing."""
    if json_output:
        typer.echo(json.dumps(receipt_as_dict(receipt), sort_keys=True))
        return
    console.print(
        f"[bold]{receipt.outcome}[/bold] exit={receipt.exit_code} "
        f"receipt={receipt.receipt_path} sha256={receipt.receipt_sha256}"
    )


def _execute(
    plan: TestRunPlan,
    *,
    json_output: bool,
    timeout: float | None = None,
) -> TestExecutionReceipt:
    """Execute a plan, emit its receipt, and preserve the process exit code."""
    add_span_attributes(
        **{
            "test.command": list(plan.command),
            "test.working_directory": str(plan.working_directory),
        }
    )
    add_span_event("tests.execution.started", {"command": list(plan.command)})
    receipt = execute_test_plan(plan, timeout=timeout)
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
    return receipt


def _display_ci_result(result: CIPipelineResult) -> None:
    """Render named CI checks and their receipt identities."""
    table = Table(title=f"uvmgr CI: {result.mode}/{result.runner}")
    table.add_column("Check")
    table.add_column("Required")
    table.add_column("Standing")
    table.add_column("Exit", justify="right")
    table.add_column("Receipt")
    for check in result.checks:
        table.add_row(
            check.description,
            "yes" if check.required else "no",
            check.receipt.outcome,
            str(check.receipt.exit_code),
            check.receipt.receipt_sha256[:12],
        )
    console.print(table)
    if result.removed_artifacts:
        console.print("Removed bounded artifacts:")
        for artifact in result.removed_artifacts:
            console.print(f"  {artifact}")


def _run_ci(  # noqa: PLR0913
    mode: str,
    *,
    runner: str = "native",
    timeout: int,
    skip_build: bool = False,
    clean: bool = True,
    json_output: bool = False,
) -> None:
    """Build and execute one deterministic local-CI plan."""
    try:
        plan = build_ci_plan(
            mode,
            runner=runner,
            skip_build=skip_build,
            clean=clean,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    result = execute_ci_plan(plan, timeout=timeout)
    if json_output:
        typer.echo(json.dumps(ci_pipeline_result_as_dict(result), sort_keys=True))
    else:
        _display_ci_result(result)
    if not result.success:
        raise typer.Exit(1)


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
    generate_report: Annotated[
        bool,
        typer.Option(
            "--report/--no-report",
            help="Render a human-readable execution receipt.",
        ),
    ] = True,
    timeout: Annotated[
        int | None,
        typer.Option("--timeout", min=1, help="Process timeout in seconds."),
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
            generate_report=generate_report,
        ),
    )
    _execute(
        plan,
        json_output=json_output or not generate_report,
        timeout=timeout,
    )


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
    test_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Template category for compatibility."),
    ] = "unit",
) -> None:
    """Generate repository-native test templates for one module."""
    templates = make_test_templates(Path.cwd(), module)
    typer.echo(f"type={test_type}")
    for template in templates:
        typer.echo(str(template))


@app.command("coverage", context_settings=_PASSTHROUGH_CONTEXT)
@instrument_command("tests_coverage", track_args=True)
def run_coverage(  # noqa: PLR0913
    ctx: typer.Context,
    selectors: Annotated[
        list[str] | None,
        typer.Argument(help="Optional pytest paths or node IDs."),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Add pytest verbose output."),
    ] = False,
    fail_under: Annotated[
        int | None,
        typer.Option("--fail-under", min=0, max=100),
    ] = None,
    format_type: Annotated[
        str,
        typer.Option("--format", help="Coverage projection: term, html, xml, json."),
    ] = "term",
    timeout: Annotated[
        int | None,
        typer.Option("--timeout", min=1, help="Process timeout in seconds."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Emit receipts as JSON."),
    ] = False,
) -> None:
    """Run tests with coverage, then verify the resulting projection."""
    _execute(
        build_test_plan(
            selectors or (),
            ctx.args,
            options=TestRunOptions(
                verbose=verbose,
                coverage=True,
                parallel=False,
            ),
        ),
        json_output=json_output,
        timeout=timeout,
    )
    _execute(
        build_coverage_report_plan(
            fail_under=fail_under,
            format_type=format_type,
        ),
        json_output=json_output,
        timeout=timeout,
    )


@ci_app.command("quick")
@instrument_command("tests_ci_quick", track_args=True)
def ci_quick(
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", min=1, help="Per-check timeout."),
    ] = 30,
    clean: Annotated[
        bool,
        typer.Option("--clean/--no-clean", help="Remove bounded build artifacts."),
    ] = True,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Emit machine-readable results."),
    ] = False,
) -> None:
    """Run the historical quick PyInstaller CI capability safely."""
    _run_ci(
        "quick",
        timeout=timeout,
        clean=clean,
        json_output=json_output,
    )


@ci_app.command("verify")
@instrument_command("tests_ci_verify", track_args=True)
def ci_verify(
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", min=1, help="Per-check timeout."),
    ] = 300,
    skip_build: Annotated[
        bool,
        typer.Option("--skip-build", help="Skip executable build checks."),
    ] = False,
    clean: Annotated[
        bool,
        typer.Option("--clean/--no-clean", help="Remove bounded build artifacts."),
    ] = True,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Emit machine-readable results."),
    ] = False,
) -> None:
    """Run comprehensive local CI verification with receipts."""
    _run_ci(
        "verify",
        timeout=timeout,
        skip_build=skip_build,
        clean=clean,
        json_output=json_output,
    )


@ci_app.command("run")
@instrument_command("tests_ci_run", track_args=True)
def ci_run(
    runner: Annotated[
        str,
        typer.Option("--runner", "-r", help="Runner: native, act, or docker."),
    ] = "native",
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", min=1, help="Per-check timeout."),
    ] = 600,
    clean: Annotated[
        bool,
        typer.Option("--clean/--no-clean", help="Remove bounded build artifacts."),
    ] = True,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Emit machine-readable results."),
    ] = False,
) -> None:
    """Run the complete CI capability through native, act, or Docker."""
    _run_ci(
        "run",
        runner=runner,
        timeout=timeout,
        clean=clean,
        json_output=json_output,
    )
