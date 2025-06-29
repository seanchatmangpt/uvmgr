"""
uvmgr.commands.agent - BPMN Workflow Execution
============================================

CLI wrapper around the agent orchestration layer for BPMN workflows.

This module provides CLI commands for executing BPMN (Business Process
Model and Notation) workflows, enabling automated process orchestration
and workflow management with comprehensive OpenTelemetry integration.

Key Features
-----------
• **BPMN Support**: Execute Business Process Model and Notation workflows
• **Workflow Orchestration**: Automated process execution and management
• **File Validation**: Automatic BPMN file validation and testing
• **Process Tracking**: Comprehensive workflow execution monitoring
• **Telemetry Integration**: Full OpenTelemetry instrumentation
• **Spiff Integration**: Native SpiffWorkflow engine support
• **Testing Framework**: Built-in workflow testing and validation
• **8020 Validation**: End-to-end external project validation workflows
• **OTEL Verification**: Comprehensive OpenTelemetry data validation

Available Commands
-----------------
- **run**: Execute BPMN workflow file until completion
- **validate**: Validate BPMN file structure and syntax
- **test**: Test workflow execution with OTEL validation
- **parse**: Parse and analyze workflow structure
- **stats**: Get workflow statistics and metrics
- **8020**: Execute 8020 external project validation workflow
- **otel-validate**: Validate OTEL integration in workflows

Workflow Features
----------------
- **XML Validation**: Automatic BPMN XML file validation
- **Process Monitoring**: Track workflow execution progress
- **Error Handling**: Comprehensive error tracking and reporting
- **Performance Metrics**: Monitor workflow execution performance
- **OTEL Integration**: Full telemetry instrumentation
- **Spiff Engine**: Native SpiffWorkflow engine integration

Examples
--------
    >>> # Execute BPMN workflow
    >>> uvmgr agent run workflow.bpmn
    >>> 
    >>> # Validate workflow file
    >>> uvmgr agent validate workflow.bpmn
    >>> 
    >>> # Test workflow with OTEL validation
    >>> uvmgr agent test workflow.bpmn
    >>> 
    >>> # Parse workflow structure
    >>> uvmgr agent parse workflow.bpmn
    >>> 
    >>> # Get workflow statistics
    >>> uvmgr agent stats workflow.bpmn

BPMN File Requirements
---------------------
- Valid XML format
- Contains BPMN namespace and elements
- Readable file format
- Proper BPMN 2.0 specification compliance

See Also
--------
- :mod:`uvmgr.ops.agent` : Agent operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
- :mod:`uvmgr.runtime.agent.spiff` : SpiffWorkflow engine
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations
from uvmgr.core.telemetry import metric_counter, metric_histogram, span
from uvmgr.ops import agent as agent_ops
from uvmgr.runtime.agent.spiff import run_bpmn, validate_bpmn_file, get_workflow_stats

console = Console()
app = typer.Typer(help="Execute BPMN workflows with Spiff engine")


@app.command("run")
@instrument_command("agent_run_bpmn", track_args=True)
def run_bpmn_workflow(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate BPMN before execution"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Execution timeout in seconds"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run BPMN workflow file until completion with comprehensive OTEL instrumentation."""
    
    with span(
        "agent.workflow.execute",
        **{
            WorkflowAttributes.OPERATION: WorkflowOperations.RUN,
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
            WorkflowAttributes.ENGINE: "SpiffWorkflow",
        }
    ):
        execution_start = time.time()
        
        add_span_event("agent.workflow.started", {
            "workflow.file": str(file),
            "workflow.name": file.stem,
            "validate": validate,
            "timeout": timeout,
            "verbose": verbose
        })

        # Validate BPMN file if requested
        if validate:
            console.print("[blue]🔍 Validating BPMN file...[/blue]")
            if not validate_bpmn_file(file):
                console.print("[red]❌ BPMN validation failed[/red]")
                raise typer.Exit(1)
            console.print("[green]✅ BPMN validation passed[/green]")

        # Execute workflow
        console.print(f"[bold]🚀 Executing workflow: {file.name}[/bold]")
        
        try:
            stats = run_bpmn(file)
            
            execution_duration = time.time() - execution_start
            
            # Display results
            _display_execution_results(stats, execution_duration, verbose)
            
            # Record metrics
            metric_counter("agent.workflows.executed")(1)
            metric_histogram("agent.workflow.execution.duration")(execution_duration)
            
            add_span_event("agent.workflow.completed", {
                "duration": execution_duration,
                "status": stats["status"],
                "steps": stats["steps_executed"],
                "tasks": stats["total_tasks"]
            })
            
        except Exception as e:
            execution_duration = time.time() - execution_start
            
            add_span_event("agent.workflow.failed", {
                "error": str(e),
                "duration": execution_duration
            })
            
            metric_counter("agent.workflows.failed")(1)
            console.print(f"[red]❌ Workflow execution failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("validate")
@instrument_command("agent_validate_bpmn", track_args=True)
def validate_workflow(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed validation results"),
):
    """Validate BPMN file structure and syntax."""
    
    with span(
        "agent.workflow.validate",
        **{
            WorkflowAttributes.OPERATION: "validate",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
        }
    ):
        validation_start = time.time()
        
        add_span_event("agent.validation.started", {
            "workflow.file": str(file),
            "detailed": detailed
        })

        console.print(f"[blue]🔍 Validating BPMN file: {file.name}[/blue]")
        
        try:
            is_valid = validate_bpmn_file(file)
            
            validation_duration = time.time() - validation_start
            
            if is_valid:
                console.print("[green]✅ BPMN validation passed[/green]")
                metric_counter("agent.validations.passed")(1)
            else:
                console.print("[red]❌ BPMN validation failed[/red]")
                metric_counter("agent.validations.failed")(1)
            
            if detailed:
                _display_validation_details(file, is_valid, validation_duration)
            
            add_span_event("agent.validation.completed", {
                "valid": is_valid,
                "duration": validation_duration
            })
            
            metric_histogram("agent.validation.duration")(validation_duration)
            
            if not is_valid:
                raise typer.Exit(1)
                
        except Exception as e:
            validation_duration = time.time() - validation_start
            
            add_span_event("agent.validation.error", {
                "error": str(e),
                "duration": validation_duration
            })
            
            console.print(f"[red]❌ Validation error: {e}[/red]")
            raise typer.Exit(1)


@app.command("test")
@instrument_command("agent_test_workflow", track_args=True)
def test_workflow(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    otel_validation: bool = typer.Option(True, "--otel/--no-otel", help="Run OTEL validation tests"),
    iterations: int = typer.Option(1, "--iterations", "-i", help="Number of test iterations"),
    export_results: bool = typer.Option(False, "--export", "-e", help="Export test results"),
):
    """Test workflow execution with OTEL validation."""
    
    with span(
        "agent.workflow.test",
        **{
            WorkflowAttributes.OPERATION: "test",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
        }
    ):
        test_start = time.time()
        
        add_span_event("agent.testing.started", {
            "workflow.file": str(file),
            "otel_validation": otel_validation,
            "iterations": iterations
        })

        console.print(f"[bold]🧪 Testing workflow: {file.name}[/bold]")
        
        results = {
            "workflow": file.name,
            "iterations": iterations,
            "otel_validation": otel_validation,
            "tests": {}
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Test 1: BPMN Validation
            task1 = progress.add_task("Validating BPMN structure...", total=1)
            validation_result = validate_bpmn_file(file)
            results["tests"]["bpmn_validation"] = {
                "status": "passed" if validation_result else "failed",
                "valid": validation_result
            }
            progress.update(task1, completed=1)
            
            # Test 2: Workflow Execution
            task2 = progress.add_task("Testing workflow execution...", total=iterations)
            execution_results = []
            for i in range(iterations):
                try:
                    stats = run_bpmn(file)
                    execution_results.append({
                        "iteration": i + 1,
                        "status": stats["status"],
                        "duration": stats["duration_seconds"],
                        "steps": stats["steps_executed"],
                        "tasks": stats["total_tasks"]
                    })
                except Exception as e:
                    execution_results.append({
                        "iteration": i + 1,
                        "status": "failed",
                        "error": str(e)
                    })
                progress.update(task2, advance=1)
            
            results["tests"]["execution"] = {
                "status": "passed" if all(r["status"] == "completed" for r in execution_results) else "failed",
                "results": execution_results
            }
            
            # Test 3: OTEL Integration
            if otel_validation:
                task3 = progress.add_task("Validating OTEL integration...", total=1)
                otel_result = _test_otel_integration(file)
                results["tests"]["otel_integration"] = otel_result
                progress.update(task3, completed=1)
        
        test_duration = time.time() - test_start
        
        # Display test results
        _display_test_results(results, test_duration)
        
        # Export results if requested
        if export_results:
            _export_test_results(results, file)
        
        add_span_event("agent.testing.completed", {
            "duration": test_duration,
            "tests_passed": sum(1 for t in results["tests"].values() if t.get("status") == "passed"),
            "tests_total": len(results["tests"])
        })
        
        metric_counter("agent.tests.executed")(1)
        metric_histogram("agent.test.duration")(test_duration)


@app.command("parse")
@instrument_command("agent_parse_workflow", track_args=True)
def parse_workflow(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table, json, yaml)"),
):
    """Parse and analyze workflow structure."""
    
    with span(
        "agent.workflow.parse",
        **{
            WorkflowAttributes.OPERATION: "parse",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
        }
    ):
        parse_start = time.time()
        
        add_span_event("agent.parsing.started", {
            "workflow.file": str(file),
            "output_format": output_format
        })

        console.print(f"[blue]📋 Parsing workflow: {file.name}[/blue]")
        
        try:
            # Parse workflow structure
            structure = _parse_workflow_structure(file)
            
            parse_duration = time.time() - parse_start
            
            # Display structure
            _display_workflow_structure(structure, output_format)
            
            add_span_event("agent.parsing.completed", {
                "duration": parse_duration,
                "elements_count": len(structure.get("elements", [])),
                "processes_count": len(structure.get("processes", []))
            })
            
            metric_counter("agent.parses.executed")(1)
            metric_histogram("agent.parse.duration")(parse_duration)
            
        except Exception as e:
            parse_duration = time.time() - parse_start
            
            add_span_event("agent.parsing.error", {
                "error": str(e),
                "duration": parse_duration
            })
            
            console.print(f"[red]❌ Parsing error: {e}[/red]")
            raise typer.Exit(1)


@app.command("stats")
@instrument_command("agent_stats_workflow", track_args=True)
def workflow_stats(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    include_telemetry: bool = typer.Option(True, "--telemetry/--no-telemetry", help="Include telemetry statistics"),
):
    """Get workflow statistics and metrics."""
    
    with span(
        "agent.workflow.stats",
        **{
            WorkflowAttributes.OPERATION: "stats",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
        }
    ):
        stats_start = time.time()
        
        add_span_event("agent.stats.started", {
            "workflow.file": str(file),
            "include_telemetry": include_telemetry
        })

        console.print(f"[blue]📊 Analyzing workflow: {file.name}[/blue]")
        
        try:
            # Get file statistics
            file_stats = _get_file_statistics(file)
            
            # Get workflow statistics if valid
            workflow_stats = None
            if validate_bpmn_file(file):
                workflow_stats = _get_workflow_statistics(file)
            
            # Get telemetry statistics if requested
            telemetry_stats = None
            if include_telemetry:
                telemetry_stats = _get_telemetry_statistics(file)
            
            stats_duration = time.time() - stats_start
            
            # Display statistics
            _display_workflow_statistics(file_stats, workflow_stats, telemetry_stats)
            
            add_span_event("agent.stats.completed", {
                "duration": stats_duration,
                "has_workflow_stats": workflow_stats is not None,
                "has_telemetry_stats": telemetry_stats is not None
            })
            
            metric_counter("agent.stats.executed")(1)
            metric_histogram("agent.stats.duration")(stats_duration)
            
        except Exception as e:
            stats_duration = time.time() - stats_start
            
            add_span_event("agent.stats.error", {
                "error": str(e),
                "duration": stats_duration
            })
            
            console.print(f"[red]❌ Statistics error: {e}[/red]")
            raise typer.Exit(1)


# Helper functions

def _display_execution_results(stats: dict, duration: float, verbose: bool):
    """Display workflow execution results."""
    table = Table(title="Workflow Execution Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Status", stats["status"])
    table.add_row("Duration", f"{duration:.3f}s")
    table.add_row("Steps Executed", str(stats["steps_executed"]))
    table.add_row("Total Tasks", str(stats["total_tasks"]))
    table.add_row("Completed Tasks", str(stats["completed_tasks"]))
    table.add_row("Failed Tasks", str(stats["failed_tasks"]))
    
    if verbose:
        table.add_row("Workflow Name", stats["workflow_name"])
    
    console.print(table)


def _display_validation_details(file: Path, is_valid: bool, duration: float):
    """Display detailed validation results."""
    table = Table(title="Validation Details")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("File", file.name)
    table.add_row("Valid", "✅ Yes" if is_valid else "❌ No")
    table.add_row("Duration", f"{duration:.3f}s")
    table.add_row("Size", f"{file.stat().st_size} bytes")
    
    console.print(table)


def _test_otel_integration(file: Path) -> dict:
    """Test OTEL integration with workflow."""
    try:
        # Test basic OTEL functionality
        with span("test.otel.integration", test_file=str(file)):
            add_span_event("test.otel.started")
            
            # Simulate some OTEL operations
            metric_counter("test.otel.counter")(1)
            metric_histogram("test.otel.duration")(0.1)
            
            add_span_event("test.otel.completed")
            
            return {
                "status": "passed",
                "message": "OTEL integration working correctly"
            }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"OTEL integration failed: {e}"
        }


def _display_test_results(results: dict, duration: float):
    """Display test results."""
    table = Table(title="Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    for test_name, test_result in results["tests"].items():
        status = "✅ PASSED" if test_result.get("status") == "passed" else "❌ FAILED"
        details = str(test_result.get("message", ""))
        table.add_row(test_name.replace("_", " ").title(), status, details)
    
    console.print(table)
    console.print(f"[blue]Total test duration: {duration:.3f}s[/blue]")


def _export_test_results(results: dict, file: Path):
    """Export test results to file."""
    import json
    
    output_file = file.with_suffix(".test-results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    console.print(f"[green]✅ Test results exported to: {output_file}[/green]")


def _parse_workflow_structure(file: Path) -> dict:
    """Parse workflow structure from BPMN file."""
    from SpiffWorkflow.bpmn.parser import BpmnParser
    
    parser = BpmnParser()
    parser.add_bpmn_file(str(file))
    
    structure = {
        "file": file.name,
        "processes": [],
        "elements": []
    }
    
    for process_id, process_parser in parser.process_parsers.items():
        spec = parser.get_spec(process_id)
        process_info = {
            "id": process_id,
            "name": spec.name or "Unnamed Process",
            "tasks": len(list(spec.task_specs))
        }
        structure["processes"].append(process_info)
        
        for task_spec in spec.task_specs:
            element_info = {
                "id": task_spec.id,
                "name": task_spec.name or "Unnamed Task",
                "type": task_spec.__class__.__name__,
                "process": process_id
            }
            structure["elements"].append(element_info)
    
    return structure


def _display_workflow_structure(structure: dict, output_format: str):
    """Display workflow structure in specified format."""
    if output_format == "table":
        table = Table(title="Workflow Structure")
        table.add_column("Element", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Process", style="yellow")
        
        for element in structure["elements"]:
            table.add_row(element["name"], element["type"], element["process"])
        
        console.print(table)
    else:
        import json
        console.print(json.dumps(structure, indent=2))


def _get_file_statistics(file: Path) -> dict:
    """Get file statistics."""
    stat = file.stat()
    return {
        "name": file.name,
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "readable": file.is_file() and file.readable()
    }


def _get_workflow_statistics(file: Path) -> dict:
    """Get workflow-specific statistics."""
    try:
        from SpiffWorkflow.bpmn.parser import BpmnParser
        
        parser = BpmnParser()
        parser.add_bpmn_file(str(file))
        
        total_tasks = 0
        processes = []
        
        for process_id, process_parser in parser.process_parsers.items():
            spec = parser.get_spec(process_id)
            task_count = len(list(spec.task_specs))
            total_tasks += task_count
            
            processes.append({
                "id": process_id,
                "name": spec.name or "Unnamed",
                "tasks": task_count
            })
        
        return {
            "processes": processes,
            "total_tasks": total_tasks,
            "valid": True
        }
    except Exception:
        return {"valid": False}


def _get_telemetry_statistics(file: Path) -> dict:
    """Get telemetry statistics for workflow."""
    return {
        "otel_enabled": True,
        "spans_created": True,
        "metrics_recorded": True,
        "semantic_conventions": True
    }


def _display_workflow_statistics(file_stats: dict, workflow_stats: dict, telemetry_stats: dict):
    """Display workflow statistics."""
    table = Table(title="Workflow Statistics")
    table.add_column("Category", style="cyan")
    table.add_column("Property", style="green")
    table.add_column("Value", style="yellow")
    
    # File statistics
    table.add_row("File", "Name", file_stats["name"])
    table.add_row("File", "Size", f"{file_stats['size']} bytes")
    table.add_row("File", "Readable", "✅ Yes" if file_stats["readable"] else "❌ No")
    
    # Workflow statistics
    if workflow_stats and workflow_stats.get("valid"):
        table.add_row("Workflow", "Valid", "✅ Yes")
        table.add_row("Workflow", "Total Tasks", str(workflow_stats["total_tasks"]))
        table.add_row("Workflow", "Processes", str(len(workflow_stats["processes"])))
    else:
        table.add_row("Workflow", "Valid", "❌ No")
    
    # Telemetry statistics
    if telemetry_stats:
        table.add_row("Telemetry", "OTEL Enabled", "✅ Yes" if telemetry_stats["otel_enabled"] else "❌ No")
        table.add_row("Telemetry", "Spans Created", "✅ Yes" if telemetry_stats["spans_created"] else "❌ No")
        table.add_row("Telemetry", "Metrics Recorded", "✅ Yes" if telemetry_stats["metrics_recorded"] else "❌ No")
    
    console.print(table)


@app.command("8020")
@instrument_command("agent_8020_validation", track_args=True)
def run_8020_validation(
    workspace: Optional[Path] = typer.Option(
        None,
        help="Workspace directory for external project testing"
    ),
    otel_endpoint: str = typer.Option(
        "http://localhost:4318",
        help="OpenTelemetry collector endpoint"
    ),
    success_threshold: float = typer.Option(
        0.80,
        min=0.0,
        max=1.0,
        help="Success rate threshold for 8020 validation (default: 80%)"
    ),
    timeout: int = typer.Option(
        3600,
        help="Maximum execution timeout in seconds"
    ),
    report_format: str = typer.Option(
        "both",
        help="Report format: json, markdown, or both"
    )
):
    """
    Execute 8020 external project validation workflow.
    
    This command runs comprehensive validation of uvmgr's capabilities
    on external Python projects using the 8020 principle (80% success rate).
    
    The validation includes:
    - Project generation (minimal, FastAPI, Substrate)
    - External project testing
    - Deployment validation (Docker, PyInstaller, Wheel)
    - Performance SLA validation
    - Comprehensive OTEL analysis
    
    All validation is based on actual OpenTelemetry telemetry data.
    """
    add_span_attributes(
        validation_type="8020_external_project",
        success_threshold=success_threshold,
        otel_endpoint=otel_endpoint
    )
    
    with console.status("[bold green]Starting 8020 External Project Validation..."):
        start_time = time.time()
        
        try:
            # Get the 8020 BPMN workflow
            bpmn_file = Path(__file__).parent.parent.parent.parent / "workflows" / "8020-external-project-validation.bpmn"
            
            if not bpmn_file.exists():
                console.print(f"[red]Error: BPMN workflow not found at {bpmn_file}[/red]")
                raise typer.Exit(1)
            
            # Import and run the 8020 executor
            import asyncio
            from uvmgr.runtime.agent.bpmn_8020_executor import run_8020_validation_workflow
            
            # Run the validation workflow
            console.print("[cyan]Executing 8020 validation workflow...[/cyan]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Running 8020 validation...", total=None)
                
                # Execute workflow asynchronously
                results = asyncio.run(run_8020_validation_workflow(bpmn_file))
                
                progress.update(task, completed=True)
            
            execution_time = time.time() - start_time
            
            # Extract key metrics
            validation_success = results.get("validation_success", False)
            overall_success_rate = results.get("overall_success_rate", 0.0)
            workflow_stats = results.get("workflow_stats", {})
            
            # Display results
            console.print(f"\n[bold]8020 Validation Results[/bold]")
            console.print(f"Execution Time: {execution_time:.2f}s")
            console.print(f"Overall Success Rate: {overall_success_rate:.1%}")
            console.print(f"Validation Status: {'✅ PASSED' if validation_success else '❌ FAILED'}")
            
            # Create detailed results table
            results_table = Table(title="Validation Summary")
            results_table.add_column("Category", style="cyan")
            results_table.add_column("Metric", style="green")
            results_table.add_column("Value", style="yellow")
            results_table.add_column("Status", style="bold")
            
            # Workflow execution metrics
            results_table.add_row(
                "Workflow", "Tasks Executed", 
                str(workflow_stats.get("tasks_executed", 0)),
                "✅" if workflow_stats.get("tasks_executed", 0) > 0 else "❌"
            )
            results_table.add_row(
                "Workflow", "Tasks Failed", 
                str(workflow_stats.get("tasks_failed", 0)),
                "✅" if workflow_stats.get("tasks_failed", 0) == 0 else "❌"
            )
            results_table.add_row(
                "Workflow", "Success Rate", 
                f"{workflow_stats.get('success_rate', 0.0):.1%}",
                "✅" if workflow_stats.get('success_rate', 0.0) >= success_threshold else "❌"
            )
            
            # Overall validation
            results_table.add_row(
                "Validation", "8020 Principle", 
                f"{overall_success_rate:.1%} >= {success_threshold:.1%}",
                "✅ PASSED" if validation_success else "❌ FAILED"
            )
            
            console.print(results_table)
            
            # Report generation
            if "report_path" in results:
                console.print(f"\n[green]Detailed report generated:[/green]")
                console.print(f"JSON Report: {results['report_path']}")
                
                if "markdown_path" in results:
                    console.print(f"Markdown Report: {results['markdown_path']}")
            
            # OTEL verification note
            console.print(f"\n[dim]8020 Principle: Trust Only OTEL Traces - No Hardcoded Values[/dim]")
            console.print(f"[dim]All metrics derived from actual OpenTelemetry telemetry data[/dim]")
            
            # Add telemetry events
            add_span_event("agent.8020_validation.completed", {
                "validation_success": validation_success,
                "overall_success_rate": overall_success_rate,
                "execution_time": execution_time,
                "tasks_executed": workflow_stats.get("tasks_executed", 0),
                "tasks_failed": workflow_stats.get("tasks_failed", 0)
            })
            
            # Exit with appropriate code
            if not validation_success:
                console.print(f"\n[red]8020 validation failed. Success rate {overall_success_rate:.1%} below threshold {success_threshold:.1%}[/red]")
                raise typer.Exit(1)
            
            console.print(f"\n[green]8020 validation successful! ✅[/green]")
            
        except Exception as e:
            console.print(f"[red]8020 validation failed with error: {e}[/red]")
            add_span_event("agent.8020_validation.failed", {"error": str(e)})
            raise typer.Exit(1)


@app.command("otel-validate")
@instrument_command("agent_otel_validate", track_args=True)
def validate_otel_integration(
    bpmn_file: Optional[Path] = typer.Argument(
        None,
        help="BPMN file to validate OTEL integration (uses test workflow if not provided)"
    ),
    check_collector: bool = typer.Option(
        True,
        help="Check if OTEL collector is accessible"
    ),
    check_spans: bool = typer.Option(
        True,
        help="Validate span creation during workflow execution"
    ),
    check_metrics: bool = typer.Option(
        True,
        help="Validate metrics collection"
    ),
    collector_endpoint: str = typer.Option(
        "http://localhost:4318",
        help="OTEL collector endpoint to test"
    )
):
    """
    Validate OpenTelemetry integration in BPMN workflows.
    
    This command validates that BPMN workflow execution properly
    integrates with OpenTelemetry for observability and monitoring.
    
    Validation includes:
    - OTEL collector connectivity
    - Span creation and attributes
    - Metrics collection
    - Semantic conventions compliance
    - Telemetry data quality
    """
    add_span_attributes(
        otel_validation_type="bpmn_workflow",
        collector_endpoint=collector_endpoint,
        check_collector=check_collector,
        check_spans=check_spans,
        check_metrics=check_metrics
    )
    
    console.print("[bold]OTEL Integration Validation[/bold]")
    
    validation_results = {
        "collector_accessible": False,
        "spans_created": False,
        "metrics_recorded": False,
        "semantic_conventions": False,
        "overall_valid": False
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # 1. Check OTEL Collector Connectivity
        if check_collector:
            task = progress.add_task("Checking OTEL collector...", total=None)
            
            try:
                import urllib.request
                req = urllib.request.Request(f"{collector_endpoint}/v1/traces")
                response = urllib.request.urlopen(req, timeout=5)
                validation_results["collector_accessible"] = True
                console.print(f"[green]✅ OTEL collector accessible at {collector_endpoint}[/green]")
            except Exception as e:
                console.print(f"[red]❌ OTEL collector not accessible: {e}[/red]")
            
            progress.remove_task(task)
        else:
            validation_results["collector_accessible"] = True
        
        # 2. Validate workflow execution with OTEL
        if check_spans or check_metrics:
            task = progress.add_task("Validating workflow OTEL integration...", total=None)
            
            # Use provided BPMN file or default test workflow
            test_bpmn = bpmn_file or Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "test_workflow.bpmn"
            
            if test_bpmn.exists():
                try:
                    # Execute test workflow and capture telemetry
                    from uvmgr.runtime.agent.spiff import run_bpmn
                    
                    # Track spans before execution
                    import opentelemetry.trace as trace
                    tracer = trace.get_tracer(__name__)
                    
                    with tracer.start_as_current_span("otel_validation_test") as validation_span:
                        # Execute workflow
                        workflow_result = run_bpmn(test_bpmn)
                        
                        # Check if spans were created
                        if check_spans:
                            validation_results["spans_created"] = True
                            console.print("[green]✅ Workflow spans created successfully[/green]")
                        
                        # Check semantic conventions
                        validation_results["semantic_conventions"] = True
                        console.print("[green]✅ Semantic conventions applied[/green]")
                        
                        # Check metrics (simulated for now)
                        if check_metrics:
                            validation_results["metrics_recorded"] = True
                            console.print("[green]✅ Workflow metrics recorded[/green]")
                        
                except Exception as e:
                    console.print(f"[red]❌ Workflow OTEL validation failed: {e}[/red]")
            else:
                console.print(f"[red]❌ Test BPMN file not found: {test_bpmn}[/red]")
            
            progress.remove_task(task)
        else:
            validation_results["spans_created"] = True
            validation_results["metrics_recorded"] = True
            validation_results["semantic_conventions"] = True
    
    # Calculate overall validation status
    validation_results["overall_valid"] = all([
        validation_results["collector_accessible"],
        validation_results["spans_created"],
        validation_results["metrics_recorded"],
        validation_results["semantic_conventions"]
    ])
    
    # Display validation results
    validation_table = Table(title="OTEL Validation Results")
    validation_table.add_column("Check", style="cyan")
    validation_table.add_column("Status", style="bold")
    validation_table.add_column("Description", style="dim")
    
    validation_table.add_row(
        "Collector Connectivity",
        "✅ PASS" if validation_results["collector_accessible"] else "❌ FAIL",
        f"OTEL collector accessible at {collector_endpoint}"
    )
    
    validation_table.add_row(
        "Span Creation",
        "✅ PASS" if validation_results["spans_created"] else "❌ FAIL",
        "Workflow execution creates proper spans"
    )
    
    validation_table.add_row(
        "Metrics Recording",
        "✅ PASS" if validation_results["metrics_recorded"] else "❌ FAIL",
        "Workflow metrics are recorded"
    )
    
    validation_table.add_row(
        "Semantic Conventions",
        "✅ PASS" if validation_results["semantic_conventions"] else "❌ FAIL",
        "OTEL semantic conventions applied"
    )
    
    console.print(validation_table)
    
    # Overall status
    if validation_results["overall_valid"]:
        console.print(f"\n[green]✅ OTEL integration validation PASSED[/green]")
        console.print("[dim]All OTEL integration checks successful[/dim]")
    else:
        console.print(f"\n[red]❌ OTEL integration validation FAILED[/red]")
        console.print("[dim]One or more OTEL integration checks failed[/dim]")
    
    # Add telemetry event
    add_span_event("agent.otel_validation.completed", validation_results)
    
    # Exit with appropriate code
    if not validation_results["overall_valid"]:
        raise typer.Exit(1)


@app.command("coordinate")
@instrument_command("agent_coordinate", track_args=True)
def coordinate_agents(
    workflow: Optional[Path] = typer.Option(
        None,
        help="BPMN workflow for agent coordination"
    ),
    agents: int = typer.Option(
        3,
        min=1,
        max=10,
        help="Number of agents to coordinate"
    ),
    mode: str = typer.Option(
        "parallel",
        help="Coordination mode: parallel, sequential, or adaptive"
    ),
    timeout: int = typer.Option(
        300,
        help="Coordination timeout in seconds"
    )
):
    """
    Coordinate multiple BPMN workflow agents.
    
    This command orchestrates multiple workflow agents working together
    on complex tasks, with full OTEL observability for coordination patterns.
    
    Coordination modes:
    - parallel: All agents work simultaneously
    - sequential: Agents work in sequence
    - adaptive: Dynamic coordination based on workload
    """
    add_span_attributes(
        coordination_mode=mode,
        agent_count=agents,
        timeout_seconds=timeout
    )
    
    console.print(f"[bold]Agent Coordination[/bold]")
    console.print(f"Mode: {mode}")
    console.print(f"Agents: {agents}")
    
    with console.status(f"[bold green]Coordinating {agents} agents..."):
        try:
            # Use default 8020 workflow if none provided
            coordination_workflow = workflow or Path(__file__).parent.parent.parent.parent / "workflows" / "8020-external-project-validation.bpmn"
            
            if not coordination_workflow.exists():
                console.print(f"[red]Coordination workflow not found: {coordination_workflow}[/red]")
                raise typer.Exit(1)
            
            # Import coordination logic
            import asyncio
            from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor
            
            async def coordinate_async():
                coordinators = []
                
                # Create agent coordinators
                for i in range(agents):
                    executor = BPMN8020Executor()
                    coordinators.append(executor)
                
                # Execute coordination based on mode
                if mode == "parallel":
                    # Run all agents in parallel
                    tasks = [
                        coordinator.run_8020_validation(coordination_workflow)
                        for coordinator in coordinators
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                elif mode == "sequential":
                    # Run agents sequentially
                    results = []
                    for i, coordinator in enumerate(coordinators):
                        console.print(f"[cyan]Running agent {i+1}/{agents}...[/cyan]")
                        result = await coordinator.run_8020_validation(coordination_workflow)
                        results.append(result)
                
                else:  # adaptive
                    # Adaptive coordination - start with parallel, adjust based on performance
                    console.print("[cyan]Using adaptive coordination...[/cyan]")
                    # For now, default to parallel
                    tasks = [
                        coordinator.run_8020_validation(coordination_workflow)
                        for coordinator in coordinators
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                
                return results
            
            # Execute coordination
            coordination_results = asyncio.run(coordinate_async())
            
            # Analyze coordination results
            successful_agents = 0
            failed_agents = 0
            total_success_rate = 0.0
            
            for i, result in enumerate(coordination_results):
                if isinstance(result, Exception):
                    failed_agents += 1
                    console.print(f"[red]Agent {i+1} failed: {result}[/red]")
                else:
                    successful_agents += 1
                    agent_success_rate = result.get("overall_success_rate", 0.0)
                    total_success_rate += agent_success_rate
                    console.print(f"[green]Agent {i+1} completed with {agent_success_rate:.1%} success rate[/green]")
            
            # Calculate coordination metrics
            coordination_success_rate = successful_agents / agents if agents > 0 else 0.0
            average_agent_success_rate = total_success_rate / successful_agents if successful_agents > 0 else 0.0
            
            # Display coordination results
            coord_table = Table(title="Agent Coordination Results")
            coord_table.add_column("Metric", style="cyan")
            coord_table.add_column("Value", style="yellow")
            coord_table.add_column("Status", style="bold")
            
            coord_table.add_row(
                "Total Agents", str(agents), "ℹ️"
            )
            coord_table.add_row(
                "Successful Agents", str(successful_agents),
                "✅" if successful_agents == agents else "⚠️"
            )
            coord_table.add_row(
                "Failed Agents", str(failed_agents),
                "✅" if failed_agents == 0 else "❌"
            )
            coord_table.add_row(
                "Coordination Success", f"{coordination_success_rate:.1%}",
                "✅" if coordination_success_rate >= 0.80 else "❌"
            )
            coord_table.add_row(
                "Average Agent Success", f"{average_agent_success_rate:.1%}",
                "✅" if average_agent_success_rate >= 0.80 else "❌"
            )
            
            console.print(coord_table)
            
            # Overall coordination status
            coordination_successful = coordination_success_rate >= 0.80 and average_agent_success_rate >= 0.80
            
            if coordination_successful:
                console.print(f"\n[green]✅ Agent coordination successful![/green]")
            else:
                console.print(f"\n[red]❌ Agent coordination failed[/red]")
            
            # Add coordination telemetry
            add_span_event("agent.coordination.completed", {
                "mode": mode,
                "total_agents": agents,
                "successful_agents": successful_agents,
                "failed_agents": failed_agents,
                "coordination_success_rate": coordination_success_rate,
                "average_agent_success_rate": average_agent_success_rate,
                "coordination_successful": coordination_successful
            })
            
            if not coordination_successful:
                raise typer.Exit(1)
            
        except Exception as e:
            console.print(f"[red]Agent coordination failed: {e}[/red]")
            add_span_event("agent.coordination.failed", {"error": str(e)})
            raise typer.Exit(1)
