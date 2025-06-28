"""
SpiffWorkflow OTEL Integration Commands
======================================

Commands for executing BPMN workflows that validate OpenTelemetry instrumentation
and test validation processes. Uses SpiffWorkflow engine with comprehensive OTEL
monitoring and the 80/20 principle for efficient validation.

Available Commands:
- validate: Run OTEL validation through BPMN workflow
- create-workflow: Create custom OTEL validation workflow
- run-workflow: Execute existing BPMN workflow with OTEL
- 8020-validate: Run critical OTEL validation (80/20 approach)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations, TestAttributes
from uvmgr.ops.spiff_otel_validation import (
    create_otel_validation_workflow,
    execute_otel_validation_workflow,
    run_8020_otel_validation,
    OTELValidationResult
)

app = typer.Typer(help="SpiffWorkflow OTEL validation and testing")
console = Console()


@app.command("validate")
@instrument_command("spiff_otel_validate", track_args=True)
def validate_otel(
    test_commands: List[str] = typer.Option(
        ["uvmgr otel status", "uvmgr tests run tests/test_instrumentation.py"],
        "--test",
        "-t",
        help="Test commands to validate"
    ),
    workflow_file: Optional[Path] = typer.Option(
        None,
        "--workflow",
        "-w",
        help="Custom BPMN workflow file"
    ),
    project_path: Optional[Path] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project path for validation"
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        help="Timeout in seconds"
    ),
    save_results: bool = typer.Option(
        False,
        "--save-results",
        "-s",
        help="Save validation results to file"
    ),
):
    """
    Run OTEL validation through SpiffWorkflow BPMN process.
    
    This command creates and executes a BPMN workflow that systematically
    validates OpenTelemetry instrumentation through test execution and
    comprehensive monitoring.
    
    Examples:
        uvmgr spiff-otel validate
        uvmgr spiff-otel validate -t "uvmgr tests run" -t "uvmgr otel validate"
        uvmgr spiff-otel validate --project /path/to/project --timeout 600
    """
    add_span_attributes(**{
        WorkflowAttributes.OPERATION: WorkflowOperations.RUN,
        WorkflowAttributes.TYPE: "otel_validation",
        TestAttributes.OPERATION: "spiff_validation",
        TestAttributes.TEST_COUNT: len(test_commands),
    })
    
    console.print("🔄 [bold cyan]SpiffWorkflow OTEL Validation[/bold cyan]")
    console.print(f"📋 Test Commands: {len(test_commands)}")
    for i, cmd in enumerate(test_commands, 1):
        console.print(f"  {i}. {cmd}")
    
    if project_path:
        console.print(f"📁 Project: {project_path}")
    console.print(f"⏱️ Timeout: {timeout}s")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up OTEL validation workflow...", total=4)
        
        try:
            # Step 1: Create or use workflow
            if workflow_file and workflow_file.exists():
                console.print(f"📄 Using existing workflow: {workflow_file}")
                workflow_path = workflow_file
            else:
                progress.update(task, description="Creating BPMN workflow...")
                workflow_dir = Path.cwd() / ".uvmgr_temp" / "workflows"
                workflow_path = workflow_dir / "otel_validation.bpmn"
                create_otel_validation_workflow(workflow_path, test_commands)
                console.print(f"✅ Created workflow: {workflow_path}")
            
            progress.advance(task)
            
            # Step 2: Execute validation workflow
            progress.update(task, description="Executing validation workflow...")
            result = execute_otel_validation_workflow(
                workflow_path=workflow_path,
                test_commands=test_commands,
                project_path=project_path,
                timeout_seconds=timeout
            )
            
            progress.advance(task)
            
            # Step 3: Display results
            progress.update(task, description="Processing results...")
            _display_validation_results(result)
            
            progress.advance(task)
            
            # Step 4: Save results if requested
            if save_results:
                progress.update(task, description="Saving results...")
                results_file = Path(f"otel_validation_results_{result.workflow_name}.json")
                _save_validation_results(result, results_file)
                console.print(f"💾 Results saved to: {results_file}")
            
            progress.advance(task)
            
            # Final status
            if result.success:
                console.print("\n[green]✅ OTEL Validation PASSED[/green]")
            else:
                console.print("\n[red]❌ OTEL Validation FAILED[/red]")
                console.print(f"[red]Errors: {len(result.errors)}[/red]")
                for error in result.errors[:3]:  # Show first 3 errors
                    console.print(f"  • {error}")
                if len(result.errors) > 3:
                    console.print(f"  ... and {len(result.errors) - 3} more errors")
            
            add_span_event("spiff_otel_validation_completed", {
                "success": result.success,
                "workflow": result.workflow_name,
                "metrics_validated": result.metrics_validated,
                "spans_validated": result.spans_validated,
                "duration": result.duration_seconds,
            })
            
            # Exit with appropriate code
            if not result.success:
                raise typer.Exit(1)
                
        except Exception as e:
            add_span_event("spiff_otel_validation_failed", {"error": str(e)})
            console.print(f"[red]❌ Validation failed: {e}[/red]")
            raise typer.Exit(1)
        finally:
            # Cleanup temporary workflow if created
            if not workflow_file and 'workflow_path' in locals():
                if workflow_path.exists():
                    workflow_path.unlink()


@app.command("8020-validate")
@instrument_command("spiff_otel_8020_validate", track_args=True)
def validate_8020(
    project_path: Optional[Path] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project path for validation"
    ),
    save_results: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save validation results"
    ),
):
    """
    Run 80/20 OTEL validation focusing on critical test paths.
    
    This command executes the most important OTEL validation tests that
    provide 80% of the validation value with 20% of the effort. Perfect
    for quick validation and CI/CD pipelines.
    
    Examples:
        uvmgr spiff-otel 8020-validate
        uvmgr spiff-otel 8020-validate --project /path/to/project --save
    """
    console.print("🎯 [bold cyan]80/20 OTEL Validation[/bold cyan]")
    console.print("🚀 Running critical validation tests...")
    
    if project_path:
        console.print(f"📁 Project: {project_path}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Executing critical OTEL validation...", total=1)
        
        try:
            result = run_8020_otel_validation(project_path)
            progress.advance(task)
            
            # Display results
            _display_validation_results(result)
            
            # Save if requested
            if save_results:
                results_file = Path(f"8020_otel_validation_{result.workflow_name}.json")
                _save_validation_results(result, results_file)
                console.print(f"💾 Results saved to: {results_file}")
            
            # Summary
            if result.success:
                console.print("\n[green]✅ 80/20 OTEL Validation PASSED[/green]")
                console.print(f"[green]✓ All critical systems validated in {result.duration_seconds:.2f}s[/green]")
            else:
                console.print("\n[red]❌ 80/20 OTEL Validation FAILED[/red]")
                console.print("[red]Critical OTEL systems have issues![/red]")
            
            add_span_event("8020_otel_validation_completed", {
                "success": result.success,
                "duration": result.duration_seconds,
                "project": str(project_path) if project_path else "global",
            })
            
            if not result.success:
                raise typer.Exit(1)
                
        except Exception as e:
            add_span_event("8020_otel_validation_failed", {"error": str(e)})
            console.print(f"[red]❌ 80/20 Validation failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("create-workflow")
@instrument_command("spiff_create_workflow", track_args=True)
def create_workflow(
    output_file: Path = typer.Argument(..., help="Output BPMN workflow file"),
    test_commands: List[str] = typer.Option(
        [],
        "--test",
        "-t",
        help="Test commands to include in workflow"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing file"
    ),
):
    """
    Create a custom OTEL validation BPMN workflow.
    
    This command generates a BPMN workflow file that can be used for
    customized OTEL validation processes. The workflow includes test
    execution, validation, and result compilation steps.
    
    Examples:
        uvmgr spiff-otel create-workflow validation.bpmn -t "uvmgr tests run"
        uvmgr spiff-otel create-workflow custom.bpmn -t "pytest" -t "uvmgr otel status"
    """
    if output_file.exists() and not force:
        console.print(f"[red]❌ File exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)
    
    if not test_commands:
        test_commands = [
            "uvmgr otel status",
            "uvmgr tests run tests/test_instrumentation.py -v",
            "uvmgr otel validate spans",
            "uvmgr otel validate metrics",
        ]
        console.print("📋 Using default test commands:")
        for cmd in test_commands:
            console.print(f"  • {cmd}")
    
    console.print(f"📄 Creating BPMN workflow: {output_file}")
    console.print(f"🔧 Test commands: {len(test_commands)}")
    
    try:
        created_path = create_otel_validation_workflow(output_file, test_commands)
        
        console.print(f"✅ Created workflow: {created_path}")
        console.print("\n[bold]Usage:[/bold]")
        console.print(f"  uvmgr spiff-otel validate --workflow {created_path}")
        
        add_span_event("workflow_created", {
            "output_file": str(output_file),
            "test_commands": len(test_commands),
        })
        
    except Exception as e:
        add_span_event("workflow_creation_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to create workflow: {e}[/red]")
        raise typer.Exit(1)


@app.command("run-workflow")
@instrument_command("spiff_run_workflow", track_args=True)
def run_workflow(
    workflow_file: Path = typer.Argument(..., help="BPMN workflow file to execute"),
    project_path: Optional[Path] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project path for execution context"
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        help="Execution timeout in seconds"
    ),
):
    """
    Execute an existing BPMN workflow with OTEL instrumentation.
    
    This command runs any BPMN workflow file with full OTEL monitoring
    and telemetry collection. Perfect for custom validation processes
    and complex test orchestration.
    
    Examples:
        uvmgr spiff-otel run-workflow validation.bpmn
        uvmgr spiff-otel run-workflow custom.bpmn --project /path/to/project
    """
    if not workflow_file.exists():
        console.print(f"[red]❌ Workflow file not found: {workflow_file}[/red]")
        raise typer.Exit(1)
    
    console.print(f"🔄 [bold cyan]Executing BPMN Workflow[/bold cyan]")
    console.print(f"📄 Workflow: {workflow_file}")
    if project_path:
        console.print(f"📁 Project: {project_path}")
    console.print(f"⏱️ Timeout: {timeout}s")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Executing BPMN workflow...", total=1)
        
        try:
            # Import and execute directly through Spiff runtime
            from uvmgr.runtime.agent.spiff import run_bpmn
            
            stats = run_bpmn(workflow_file)
            progress.advance(task)
            
            # Display execution results
            console.print("\n[green]✅ Workflow Completed[/green]")
            
            # Results table
            table = Table(title="Workflow Execution Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Status", stats["status"])
            table.add_row("Duration", f"{stats['duration_seconds']:.2f}s")
            table.add_row("Steps Executed", str(stats["steps_executed"]))
            table.add_row("Total Tasks", str(stats["total_tasks"]))
            table.add_row("Completed Tasks", str(stats["completed_tasks"]))
            table.add_row("Failed Tasks", str(stats["failed_tasks"]))
            
            console.print(table)
            
            add_span_event("workflow_executed", {
                "workflow_file": str(workflow_file),
                "status": stats["status"],
                "duration": stats["duration_seconds"],
                "steps": stats["steps_executed"],
            })
            
            if stats["status"] != "completed":
                raise typer.Exit(1)
                
        except Exception as e:
            add_span_event("workflow_execution_failed", {"error": str(e)})
            console.print(f"[red]❌ Workflow execution failed: {e}[/red]")
            raise typer.Exit(1)


def _display_validation_results(result: OTELValidationResult) -> None:
    """Display validation results in a formatted table."""
    # Main results panel
    status_color = "green" if result.success else "red"
    status_icon = "✅" if result.success else "❌"
    
    panel_content = f"""[{status_color}]{status_icon} Validation {['FAILED', 'PASSED'][result.success]}[/{status_color}]
    
[bold]Workflow:[/bold] {result.workflow_name}
[bold]Duration:[/bold] {result.duration_seconds:.2f}s
[bold]Steps:[/bold] {len(result.validation_steps)}
[bold]Metrics Validated:[/bold] {result.metrics_validated}
[bold]Spans Validated:[/bold] {result.spans_validated}"""
    
    if result.errors:
        panel_content += f"\n[bold red]Errors:[/bold red] {len(result.errors)}"
    
    console.print(Panel(panel_content, title="OTEL Validation Results", border_style=status_color))
    
    # Validation steps table
    if result.validation_steps:
        console.print("\n[bold]Validation Steps:[/bold]")
        steps_table = Table()
        steps_table.add_column("#", style="dim")
        steps_table.add_column("Step", style="cyan")
        steps_table.add_column("Status", style="green")
        
        for i, step in enumerate(result.validation_steps, 1):
            status = "✅ PASS" if step != "FAIL" else "❌ FAIL"
            steps_table.add_row(str(i), step, status)
        
        console.print(steps_table)
    
    # Performance data
    if result.performance_data:
        console.print("\n[bold]Performance Data:[/bold]")
        perf_table = Table()
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="green")
        
        for metric, value in result.performance_data.items():
            if isinstance(value, float):
                perf_table.add_row(metric, f"{value:.3f}s")
            else:
                perf_table.add_row(metric, str(value))
        
        console.print(perf_table)
    
    # Errors detail
    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for i, error in enumerate(result.errors[:5], 1):  # Show first 5 errors
            console.print(f"  {i}. {error}")
        if len(result.errors) > 5:
            console.print(f"  ... and {len(result.errors) - 5} more errors")


def _save_validation_results(result: OTELValidationResult, output_file: Path) -> None:
    """Save validation results to JSON file."""
    results_data = {
        "success": result.success,
        "workflow_name": result.workflow_name,
        "duration_seconds": result.duration_seconds,
        "validation_steps": result.validation_steps,
        "metrics_validated": result.metrics_validated,
        "spans_validated": result.spans_validated,
        "errors": result.errors,
        "performance_data": result.performance_data,
        "generated_at": "2025-06-28T00:00:00Z",  # Would use actual timestamp
    }
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)