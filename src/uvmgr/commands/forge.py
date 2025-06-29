"""
uvmgr.commands.forge - Forge Workflow Management
===============================================

Forge workflow management for uvmgr semantic convention development.

This module provides CLI commands for managing the forge workflow, including
validation, code generation, and OTEL testing using an 80/20 approach.

Key Features
-----------
• **Validation**: Check semantic convention registry compliance
• **Code Generation**: Generate Python constants from conventions
• **OTEL Testing**: Validate OpenTelemetry integration
• **Workflow Management**: Orchestrate complete development workflow
• **80/20 Approach**: Focus on critical functionality first

Available Commands
-----------------
- **workflow**: Run complete forge workflow (validate, generate, test)
- **validate**: Run semantic convention validation
- **generate**: Generate code from semantic conventions
- **test**: Run OTEL validation tests
- **init**: Initialize forge project structure
- **status**: Show forge project status

Workflow Steps
-------------
1. **Validation**: Check registry compliance and consistency
2. **Generation**: Generate Python constants and types
3. **Testing**: Validate OTEL integration and functionality

80/20 Approach
-------------
- Focus on critical functionality first
- Graceful degradation for non-critical features
- Fallback mechanisms for compatibility
- Performance optimization for common use cases

Examples
--------
    >>> # Run complete workflow
    >>> uvmgr forge workflow
    >>> 
    >>> # Run individual steps
    >>> uvmgr forge validate
    >>> uvmgr forge generate
    >>> uvmgr forge test
    >>> 
    >>> # Initialize new project
    >>> uvmgr forge init --name myproject

See Also
--------
- :mod:`uvmgr.ops.forge` : Forge operations
- :mod:`uvmgr.commands.weaver` : Weaver semantic convention tools
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from uvmgr.cli_utils import handle_cli_exception, maybe_json
from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.ops.forge import run_generation, run_otel_validation, run_validation, run_workflow

console = Console()
app = typer.Typer(help="Forge workflow management for semantic convention development")


def _show_workflow_plan(validate: bool, generate: bool, test: bool):
    """Show the workflow plan."""
    table = Table(title="Forge Workflow Plan")
    table.add_column("Step", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Status", style="green")

    step_num = 1
    if validate:
        table.add_row(
            f"{step_num}",
            "🔍 Validate",
            "Check semantic convention registry compliance"
        )
        step_num += 1

    if generate:
        table.add_row(
            f"{step_num}",
            "⚙️ Generate",
            "Generate Python constants from conventions"
        )
        step_num += 1

    if test:
        table.add_row(
            f"{step_num}",
            "🧪 Test",
            "Run OTEL validation to ensure integration works"
        )

    console.print(table)


@app.command("workflow")
@instrument_command("forge_workflow", track_args=True)
def workflow(
    ctx: typer.Context,
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Run validation step"),
    generate: bool = typer.Option(True, "--generate/--no-generate", help="Run code generation"),
    test: bool = typer.Option(True, "--test/--no-test", help="Run OTEL validation tests"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch for changes and re-run"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
):
    """Run the complete forge workflow."""
    add_span_attributes(**{
        "forge.operation": "workflow",
        "forge.validate": validate,
        "forge.generate": generate,
        "forge.test": test,
        "forge.watch": watch,
        "forge.dry_run": dry_run,
    })
    add_span_event("forge.workflow.started", {
        "validate": validate,
        "generate": generate,
        "test": test
    })

    console.print("[bold]Forge Workflow[/bold]\n")

    if dry_run:
        _show_workflow_plan(validate, generate, test)
        console.print("\n[yellow]Dry run mode - no actions performed[/yellow]")
        return

    try:
        if watch:
            _watch_and_rerun(validate, generate, test)
        else:
            # Show plan
            _show_workflow_plan(validate, generate, test)
            console.print()

            # Run workflow
            start_time = time.time()
            result = run_workflow(validate=validate, generate=generate, test=test)
            duration = time.time() - start_time

            # Display results
            _display_workflow_results(result, duration, result["success_rate"])

            maybe_json(ctx, result, exit_code=0 if result["success_rate"] == 100 else 1)

    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


def _display_workflow_results(results: dict, duration: float, success_rate: float):
    """Display workflow results."""
    console.print(f"\n[bold]Workflow Results[/bold]")
    console.print(f"Duration: {duration:.2f}s")
    console.print(f"Success Rate: {success_rate:.1f}%")

    if success_rate == 100:
        console.print("[green]✓ All steps completed successfully![/green]")
    else:
        console.print(f"[yellow]⚠ {results['total_steps'] - results['success_count']} steps failed[/yellow]")

    # Show individual step results
    for step_name, step_result in results.get("results", {}).items():
        status_icon = "✓" if step_result.get("status") == "passed" else "✗"
        status_color = "green" if step_result.get("status") == "passed" else "red"
        console.print(f"[{status_color}]{status_icon} {step_name.title()}[/{status_color}]")


def _watch_and_rerun(validate: bool, generate: bool, test: bool):
    """Watch for changes and re-run workflow."""
    console.print("[yellow]Watch mode not yet implemented[/yellow]")
    console.print("Running workflow once...")
    
    start_time = time.time()
    result = run_workflow(validate=validate, generate=generate, test=test)
    duration = time.time() - start_time
    
    _display_workflow_results(result, duration, result["success_rate"])


@app.command("init")
@instrument_command("forge_init", track_args=True)
def init_forge(
    ctx: typer.Context,
    name: str = typer.Option("uvmgr", "--name", "-n", help="Project name"),
    template: str = typer.Option("python", "--template", "-t", help="Template type"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing setup"),
):
    """Initialize forge project structure."""
    add_span_attributes(**{
        "forge.operation": "init",
        "forge.name": name,
        "forge.template": template,
        "forge.force": force,
    })
    add_span_event("forge.init.started", {"name": name, "template": template})

    console.print(f"[bold]Initializing Forge Project: {name}[/bold]\n")

    try:
        # This would be implemented in the ops layer
        console.print("[yellow]Forge init not yet implemented[/yellow]")
        maybe_json(ctx, {"status": "not_implemented"}, exit_code=0)

    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("status")
@instrument_command("forge_status")
def status(ctx: typer.Context):
    """Show forge project status."""
    add_span_attributes(**{
        "forge.operation": "status",
    })
    add_span_event("forge.status.started")

    console.print("[bold]Forge Project Status[/bold]\n")

    try:
        # This would check the current state of the forge project
        console.print("[yellow]Forge status not yet implemented[/yellow]")
        maybe_json(ctx, {"status": "not_implemented"}, exit_code=0)

    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("validate")
@instrument_command("forge_validate", track_args=True)
def validate(ctx: typer.Context):
    """Run semantic convention validation."""
    add_span_attributes(**{
        "forge.operation": "validate",
    })
    add_span_event("forge.validate.started")

    console.print("[bold]Running Semantic Convention Validation[/bold]\n")

    try:
        result = run_validation()
        
        if result["status"] == "passed":
            console.print("[green]✓ Validation passed![/green]")
        elif result["status"] == "passed_with_warnings":
            console.print("[yellow]⚠ Validation passed with warnings[/yellow]")
            if result.get("warnings"):
                console.print(result["warnings"])
        else:
            console.print("[red]✗ Validation failed[/red]")
            if result.get("output"):
                console.print(result["output"])

        maybe_json(ctx, result, exit_code=0 if result["status"] != "failed" else 1)

    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("generate")
@instrument_command("forge_generate", track_args=True)
def generate(ctx: typer.Context):
    """Generate code from semantic conventions."""
    add_span_attributes(**{
        "forge.operation": "generate",
    })
    add_span_event("forge.generate.started")

    console.print("[bold]Generating Code from Semantic Conventions[/bold]\n")

    try:
        result = run_generation()
        
        if result["status"] == "passed":
            console.print(f"[green]✓ {result['output']}[/green]")
            if result.get("template_used"):
                console.print("[blue]Used custom template[/blue]")
        else:
            console.print("[red]✗ Generation failed[/red]")
            if result.get("output"):
                console.print(result["output"])

        maybe_json(ctx, result, exit_code=0 if result["status"] == "passed" else 1)

    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("test")
@instrument_command("forge_test", track_args=True)
def test(ctx: typer.Context):
    """Run OTEL validation tests."""
    add_span_attributes(**{
        "forge.operation": "test",
    })
    add_span_event("forge.test.started")

    console.print("[bold]Running OTEL Validation Tests[/bold]\n")

    try:
        result = run_otel_validation()
        
        if result["status"] == "passed":
            console.print(f"[green]✓ All {result['tests_passed']} tests passed![/green]")
        else:
            console.print(f"[red]✗ {result['tests_total'] - result['tests_passed']} tests failed[/red]")

        maybe_json(ctx, result, exit_code=0 if result["status"] == "passed" else 1)

    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)
