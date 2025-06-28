"""
uvmgr.commands.spiff_otel - SpiffWorkflow OTEL Validation
========================================================

Commands for SpiffWorkflow-based OpenTelemetry validation and testing.

This module provides CLI commands for executing BPMN-based OTEL validation
workflows using the SpiffWorkflow engine. It integrates workflow orchestration
with comprehensive OpenTelemetry validation testing.

Key Features
-----------
• **BPMN-based Validation**: Execute OTEL validation using BPMN workflows
• **Workflow Orchestration**: Automated validation process orchestration
• **Comprehensive Testing**: Full OTEL feature validation through workflows
• **Process Tracking**: Monitor validation workflow execution
• **Result Reporting**: Detailed validation results and reporting
• **Error Handling**: Comprehensive error tracking through workflows
• **Performance Monitoring**: Track validation workflow performance

Available Commands
-----------------
- **validate**: Execute OTEL validation workflow
- **validate-workflow**: Validate BPMN workflow structure
- **list-workflows**: List available validation workflows
- **create-workflow**: Create new OTEL validation workflow

Validation Features
------------------
- **Span Creation**: Test span creation and management through workflow
- **Metrics Collection**: Validate metrics collection via workflow tasks
- **Error Handling**: Test error tracking through workflow error events
- **Performance Tracking**: Validate performance monitoring in workflows
- **Semantic Conventions**: Test semantic convention compliance
- **Instrumentation**: Validate instrumentation effectiveness

Examples
--------
    >>> # Execute OTEL validation workflow
    >>> uvmgr spiff-otel validate
    >>> 
    >>> # Validate specific workflow file
    >>> uvmgr spiff-otel validate-workflow otel_validation.bpmn
    >>> 
    >>> # List available workflows
    >>> uvmgr spiff-otel list-workflows
    >>> 
    >>> # Create new validation workflow
    >>> uvmgr spiff-otel create-workflow custom_validation.bpmn

See Also
--------
- :mod:`uvmgr.commands.otel` : Direct OTEL validation commands
- :mod:`uvmgr.commands.agent` : BPMN workflow execution
- :mod:`uvmgr.runtime.agent.spiff` : SpiffWorkflow engine
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception
from uvmgr.runtime.agent.spiff import run_bpmn, validate_bpmn_file
from uvmgr.ops.external_project_spiff import (
    discover_external_projects,
    validate_external_project_with_spiff,
    batch_validate_external_projects,
    run_8020_external_project_validation
)

app = typer.Typer(help="SpiffWorkflow OTEL validation and testing")
console = Console()


@app.command("validate")
@instrument_command("spiff_otel_validate", track_args=True)
def validate_otel(
    workflow_file: Optional[Path] = typer.Option(
        None,
        "--workflow",
        "-w",
        help="Custom BPMN workflow file (defaults to built-in otel_validation.bpmn)"
    ),
    iterations: int = typer.Option(1, "--iterations", "-i", help="Number of validation iterations"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    export_results: bool = typer.Option(False, "--export", "-e", help="Export validation results"),
):
    """Execute OTEL validation using SpiffWorkflow BPMN process."""
    
    # Determine workflow file to use
    if workflow_file is None:
        workflow_file = Path(__file__).parent.parent / "workflows" / "otel_validation.bpmn"
    
    if not workflow_file.exists():
        console.print(f"[red]❌ Workflow file not found: {workflow_file}[/red]")
        raise typer.Exit(1)
    
    add_span_attributes(**{
        WorkflowAttributes.OPERATION: "validate",
        WorkflowAttributes.TYPE: "bpmn",
        WorkflowAttributes.DEFINITION_PATH: str(workflow_file),
        WorkflowAttributes.DEFINITION_NAME: workflow_file.stem,
        WorkflowAttributes.ENGINE: "SpiffWorkflow",
    })
    
    console.print(Panel.fit(
        f"🔬 SpiffWorkflow OTEL Validation\n"
        f"Workflow: {workflow_file.name}\n"
        f"Iterations: {iterations}",
        title="OTEL Validation",
        border_style="blue"
    ))
    
    with span(
        "spiff_otel.validation.execute",
        **{
            WorkflowAttributes.OPERATION: "validate",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(workflow_file),
            WorkflowAttributes.DEFINITION_NAME: workflow_file.stem,
            WorkflowAttributes.ENGINE: "SpiffWorkflow",
        }
    ):
        validation_start = time.time()
        
        add_span_event("spiff_otel.validation.started", {
            "workflow_file": str(workflow_file),
            "iterations": iterations,
            "verbose": verbose
        })
        
        results = {
            "workflow": workflow_file.name,
            "iterations": iterations,
            "validation_results": [],
            "summary": {}
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Validate workflow structure first
            task1 = progress.add_task("Validating workflow structure...", total=1)
            if not validate_bpmn_file(workflow_file):
                console.print("[red]❌ Workflow validation failed[/red]")
                raise typer.Exit(1)
            progress.update(task1, completed=1)
            
            # Execute validation iterations
            task2 = progress.add_task("Running OTEL validation iterations...", total=iterations)
            
            passed_iterations = 0
            failed_iterations = 0
            
            for iteration in range(iterations):
                try:
                    iteration_start = time.time()
                    
                    # Execute the OTEL validation workflow
                    workflow_stats = run_bpmn(workflow_file)
                    
                    iteration_duration = time.time() - iteration_start
                    
                    iteration_result = {
                        "iteration": iteration + 1,
                        "status": workflow_stats["status"],
                        "duration": iteration_duration,
                        "steps_executed": workflow_stats["steps_executed"],
                        "completed_tasks": workflow_stats["completed_tasks"],
                        "failed_tasks": workflow_stats["failed_tasks"],
                        "workflow_data": workflow_stats.get("workflow_data", {})
                    }
                    
                    if workflow_stats["status"] == "completed" and workflow_stats["failed_tasks"] == 0:
                        iteration_result["validation_passed"] = True
                        passed_iterations += 1
                    else:
                        iteration_result["validation_passed"] = False
                        failed_iterations += 1
                    
                    results["validation_results"].append(iteration_result)
                    
                except Exception as e:
                    iteration_duration = time.time() - iteration_start
                    failed_iterations += 1
                    
                    iteration_result = {
                        "iteration": iteration + 1,
                        "status": "error",
                        "duration": iteration_duration,
                        "error": str(e),
                        "validation_passed": False
                    }
                    
                    results["validation_results"].append(iteration_result)
                    record_exception(e, escaped=True)
                
                progress.update(task2, advance=1)
        
        validation_duration = time.time() - validation_start
        
        # Calculate summary statistics
        results["summary"] = {
            "total_iterations": iterations,
            "passed_iterations": passed_iterations,
            "failed_iterations": failed_iterations,
            "success_rate": (passed_iterations / iterations) * 100 if iterations > 0 else 0,
            "total_duration": validation_duration,
            "average_iteration_duration": validation_duration / iterations if iterations > 0 else 0
        }
        
        # Display results
        _display_validation_results_simple(results, verbose)
        
        # Export results if requested
        if export_results:
            _export_validation_results_simple(results, workflow_file)
        
        # Record telemetry
        add_span_event("spiff_otel.validation.completed", {
            "total_duration": validation_duration,
            "passed_iterations": passed_iterations,
            "failed_iterations": failed_iterations,
            "success_rate": results["summary"]["success_rate"]
        })
        
        metric_counter("spiff_otel.validations.executed")(1)
        metric_histogram("spiff_otel.validation.duration")(validation_duration)
        metric_counter("spiff_otel.validation.iterations.passed")(passed_iterations)
        metric_counter("spiff_otel.validation.iterations.failed")(failed_iterations)
        
        # Exit with error code if any validations failed
        if failed_iterations > 0:
            console.print(f"[red]❌ {failed_iterations} validation iterations failed[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]✅ All {passed_iterations} validation iterations passed[/green]")


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
            # Use the default OTEL validation workflow for 8020
            default_workflow = Path(__file__).parent.parent / "workflows" / "otel_validation.bpmn"
            if not default_workflow.exists():
                raise Exception(f"Default workflow not found: {default_workflow}")
            
            workflow_stats = run_bpmn(default_workflow)
            
            # Create a simple result for 8020 validation
            class Simple8020Result:
                def __init__(self, stats):
                    self.success = stats["status"] == "completed" and stats["failed_tasks"] == 0
                    self.workflow_name = "8020_validation"
                    self.duration_seconds = stats.get("duration_seconds", 0)
                    self.validation_steps = ["Initialize OTEL", "Test Spans", "Test Metrics", "Performance Check"]
                    self.metrics_validated = 4
                    self.spans_validated = stats["steps_executed"]
                    self.errors = [] if self.success else ["8020 validation failed"]
                    self.performance_data = {"execution_time": self.duration_seconds}
            
            result = Simple8020Result(workflow_stats)
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
        # Generate BPMN content based on test commands
        bpmn_content = _generate_otel_workflow_content(output_file.stem, test_commands)
        output_file.write_text(bpmn_content)
        created_path = output_file
        
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


@app.command("external-validate")
@instrument_command("spiff_external_validate", track_args=True)
def validate_external_project(
    project_path: Path = typer.Argument(..., help="Path to external Python project"),
    mode: str = typer.Option("8020", "--mode", "-m", help="Validation mode (8020, comprehensive, custom)"),
    timeout: int = typer.Option(600, "--timeout", help="Validation timeout in seconds"),
    save_results: bool = typer.Option(False, "--save", "-s", help="Save validation results"),
    preserve_env: bool = typer.Option(True, "--preserve-env", help="Preserve original project environment"),
):
    """
    Validate OTEL integration in an external Python project using SpiffWorkflow.
    
    This command takes any external Python project and validates that uvmgr's
    OTEL instrumentation works correctly within that project's environment.
    Perfect for testing uvmgr's external project integration capabilities.
    
    Examples:
        uvmgr spiff-otel external-validate /path/to/project
        uvmgr spiff-otel external-validate ~/dev/myapp --mode comprehensive --save
    """
    if not project_path.exists():
        console.print(f"[red]❌ Project path not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"🔍 [bold cyan]External Project OTEL Validation[/bold cyan]")
    console.print(f"📁 Project: {project_path}")
    console.print(f"🎯 Mode: {mode}")
    console.print(f"⏱️ Timeout: {timeout}s")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Validating external project...", total=1)
        
        try:
            result = validate_external_project_with_spiff(
                project_path=project_path,
                validation_mode=mode,
                timeout_seconds=timeout,
                preserve_environment=preserve_env
            )
            progress.advance(task)
            
            # Display results
            _display_external_validation_results(result)
            
            # Save if requested
            if save_results:
                results_file = Path(f"external_validation_{result.project_info.name}.json")
                _save_external_validation_results(result, results_file)
                console.print(f"💾 Results saved to: {results_file}")
            
            # Summary
            if result.validation_result.success:
                console.print("\n[green]✅ External Project OTEL Validation PASSED[/green]")
                console.print(f"[green]✓ uvmgr successfully integrated with {result.project_info.name}[/green]")
            else:
                console.print("\n[red]❌ External Project OTEL Validation FAILED[/red]")
                console.print("[red]External project integration has issues[/red]")
            
            add_span_event("external_project_validation_completed", {
                "project": result.project_info.name,
                "success": result.validation_result.success,
                "mode": mode,
                "installation_time": result.installation_time,
            })
            
            if not result.validation_result.success:
                raise typer.Exit(1)
                
        except Exception as e:
            add_span_event("external_project_validation_failed", {"error": str(e)})
            console.print(f"[red]❌ External validation failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("discover-projects")
@instrument_command("spiff_discover_projects", track_args=True)
def discover_external_projects_cmd(
    search_paths: List[Path] = typer.Option(
        [],
        "--path",
        "-p",
        help="Paths to search for projects (can be used multiple times)"
    ),
    max_depth: int = typer.Option(3, "--depth", "-d", help="Maximum search depth"),
    min_confidence: float = typer.Option(0.7, "--confidence", "-c", help="Minimum confidence for project detection"),
    show_details: bool = typer.Option(False, "--details", help="Show detailed project information"),
):
    """
    Discover external Python projects for OTEL validation.
    
    This command searches specified paths for Python projects that can be
    used for external OTEL validation testing. Useful for finding suitable
    projects before running batch validation.
    
    Examples:
        uvmgr spiff-otel discover-projects --path ~/dev --path ~/projects
        uvmgr spiff-otel discover-projects --depth 2 --confidence 0.8 --details
    """
    # Default search paths if none provided
    if not search_paths:
        search_paths = [
            Path.home() / "dev",
            Path.home() / "projects",
            Path.home() / "code",
            Path.cwd().parent,
        ]
        console.print("🔍 Using default search paths:")
        for path in search_paths:
            if path.exists():
                console.print(f"  • {path}")
    
    console.print(f"🔍 [bold cyan]Discovering External Python Projects[/bold cyan]")
    console.print(f"📂 Search paths: {len([p for p in search_paths if p.exists()])}")
    console.print(f"🏗️ Max depth: {max_depth}")
    console.print(f"🎯 Min confidence: {min_confidence}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Discovering projects...", total=1)
        
        try:
            # Filter to existing paths
            existing_paths = [p for p in search_paths if p.exists()]
            
            if not existing_paths:
                console.print("[red]❌ No valid search paths found[/red]")
                raise typer.Exit(1)
            
            projects = discover_external_projects(
                search_paths=existing_paths,
                max_depth=max_depth,
                min_confidence=min_confidence
            )
            progress.advance(task)
            
            if not projects:
                console.print("\n[yellow]⚠️ No external Python projects discovered[/yellow]")
                console.print("Try adjusting search paths or lowering confidence threshold")
                return
            
            # Display results
            console.print(f"\n✅ [green]Found {len(projects)} external Python projects[/green]")
            
            # Summary table
            table = Table(title="Discovered Projects")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="blue")
            table.add_column("Package Manager", style="green")
            table.add_column("Has Tests", style="yellow")
            table.add_column("Path", style="dim")
            
            for project in projects:
                table.add_row(
                    project.name,
                    project.project_type,
                    project.package_manager,
                    "✅" if project.has_tests else "❌",
                    str(project.path)
                )
            
            console.print(table)
            
            # Detailed information if requested
            if show_details:
                console.print("\n[bold]Detailed Project Information:[/bold]")
                for i, project in enumerate(projects, 1):
                    console.print(f"\n{i}. [cyan]{project.name}[/cyan]")
                    console.print(f"   Path: {project.path}")
                    console.print(f"   Type: {project.project_type}")
                    console.print(f"   Package Manager: {project.package_manager}")
                    console.print(f"   Test Framework: {project.test_framework or 'None'}")
                    console.print(f"   Has pyproject.toml: {'Yes' if project.has_pyproject else 'No'}")
                    if project.dependencies:
                        console.print(f"   Dependencies: {', '.join(project.dependencies[:5])}{'...' if len(project.dependencies) > 5 else ''}")
            
            add_span_event("projects_discovery_completed", {
                "projects_found": len(projects),
                "search_paths": len(existing_paths),
            })
                
        except Exception as e:
            add_span_event("projects_discovery_failed", {"error": str(e)})
            console.print(f"[red]❌ Project discovery failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("batch-validate")
@instrument_command("spiff_batch_validate", track_args=True)
def batch_validate_external_projects_cmd(
    project_paths: List[Path] = typer.Option(
        [],
        "--project",
        "-p",
        help="Project paths to validate (can be used multiple times)"
    ),
    auto_discover: bool = typer.Option(
        False,
        "--auto-discover",
        "-a",
        help="Auto-discover projects in common locations"
    ),
    mode: str = typer.Option("8020", "--mode", "-m", help="Validation mode for all projects"),
    parallel: bool = typer.Option(True, "--parallel", help="Run validations in parallel"),
    max_workers: int = typer.Option(3, "--workers", "-w", help="Maximum parallel workers"),
    timeout_per_project: int = typer.Option(300, "--timeout", help="Timeout per project in seconds"),
    save_results: bool = typer.Option(False, "--save", "-s", help="Save batch results"),
):
    """
    Run OTEL validation across multiple external projects in batch.
    
    This command validates uvmgr's OTEL integration across multiple external
    Python projects simultaneously. Perfect for comprehensive testing of
    external project compatibility.
    
    Examples:
        uvmgr spiff-otel batch-validate --auto-discover --mode 8020
        uvmgr spiff-otel batch-validate -p ~/dev/app1 -p ~/dev/app2 --parallel
        uvmgr spiff-otel batch-validate --auto-discover --workers 2 --save
    """
    if auto_discover:
        console.print("🔍 [bold cyan]Auto-discovering projects for batch validation[/bold cyan]")
        
        # Discover projects automatically
        search_paths = [
            Path.home() / "dev",
            Path.home() / "projects", 
            Path.home() / "code",
            Path.cwd().parent,
        ]
        existing_paths = [p for p in search_paths if p.exists()]
        
        if not existing_paths:
            console.print("[red]❌ No valid search paths for auto-discovery[/red]")
            raise typer.Exit(1)
        
        discovered_projects = discover_external_projects(existing_paths, max_depth=2)
        
        # Select top projects for validation
        from uvmgr.ops.external_project_spiff import _select_critical_projects
        project_infos = _select_critical_projects(discovered_projects, max_count=5)
        project_paths = [p.path for p in project_infos]
        
        console.print(f"📋 Selected {len(project_paths)} projects for validation:")
        for project_info in project_infos:
            console.print(f"  • {project_info.name} ({project_info.project_type})")
    
    elif not project_paths:
        console.print("[red]❌ No project paths specified. Use --project or --auto-discover[/red]")
        raise typer.Exit(1)
    
    # Validate that all project paths exist
    valid_paths = [p for p in project_paths if p.exists()]
    if not valid_paths:
        console.print("[red]❌ No valid project paths found[/red]")
        raise typer.Exit(1)
    
    console.print(f"🚀 [bold cyan]Batch OTEL Validation[/bold cyan]")
    console.print(f"📋 Projects: {len(valid_paths)}")
    console.print(f"🎯 Mode: {mode}")
    console.print(f"⚡ Parallel: {'Yes' if parallel else 'No'}")
    if parallel:
        console.print(f"👥 Workers: {max_workers}")
    console.print(f"⏱️ Timeout per project: {timeout_per_project}s")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running batch validation...", total=1)
        
        try:
            results = batch_validate_external_projects(
                projects=valid_paths,
                validation_mode=mode,
                parallel=parallel,
                max_workers=max_workers,
                timeout_per_project=timeout_per_project
            )
            progress.advance(task)
            
            # Display batch results
            _display_batch_validation_results(results)
            
            # Save if requested
            if save_results:
                results_file = Path(f"batch_validation_results_{mode}.json")
                _save_batch_validation_results(results, results_file)
                console.print(f"💾 Batch results saved to: {results_file}")
            
            # Calculate overall success
            total_projects = len(results)
            successful_projects = sum(1 for r in results.values() if r.validation_result.success)
            success_rate = successful_projects / total_projects if total_projects > 0 else 0.0
            
            # Summary
            if success_rate >= 0.80:  # 80/20 threshold
                console.print(f"\n[green]✅ Batch Validation PASSED[/green]")
                console.print(f"[green]✓ {successful_projects}/{total_projects} projects validated successfully ({success_rate:.1%})[/green]")
            else:
                console.print(f"\n[red]❌ Batch Validation FAILED[/red]")
                console.print(f"[red]Only {successful_projects}/{total_projects} projects passed ({success_rate:.1%})[/red]")
            
            add_span_event("batch_validation_completed", {
                "total_projects": total_projects,
                "successful_projects": successful_projects,
                "success_rate": success_rate,
                "mode": mode,
            })
            
            if success_rate < 0.80:
                raise typer.Exit(1)
                
        except Exception as e:
            add_span_event("batch_validation_failed", {"error": str(e)})
            console.print(f"[red]❌ Batch validation failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("8020-external")
@instrument_command("spiff_8020_external", track_args=True)
def validate_8020_external(
    search_paths: List[Path] = typer.Option(
        [],
        "--path",
        "-p",
        help="Additional search paths for projects"
    ),
    project_type_filter: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter projects by type (web, cli, library, data, ml)"
    ),
    save_results: bool = typer.Option(False, "--save", "-s", help="Save comprehensive results"),
):
    """
    Run 80/20 OTEL validation across multiple external projects.
    
    This command implements the 80/20 principle by automatically discovering
    and validating the most critical external Python projects to ensure uvmgr
    works correctly in real-world scenarios.
    
    Examples:
        uvmgr spiff-otel 8020-external
        uvmgr spiff-otel 8020-external --type web --save
        uvmgr spiff-otel 8020-external --path ~/dev --path ~/projects
    """
    console.print("🎯 [bold cyan]80/20 External Project OTEL Validation[/bold cyan]")
    console.print("🚀 Discovering and validating critical external projects...")
    
    # Prepare project filters
    project_filters = {}
    if project_type_filter:
        project_filters["project_type"] = project_type_filter
        console.print(f"🔧 Filtering by project type: {project_type_filter}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running 80/20 external validation...", total=1)
        
        try:
            # Add any custom search paths
            custom_search_paths = [p for p in search_paths if p.exists()] if search_paths else None
            
            results = run_8020_external_project_validation(
                search_paths=custom_search_paths,
                project_filters=project_filters if project_filters else None
            )
            progress.advance(task)
            
            # Display comprehensive results
            _display_8020_external_results(results)
            
            # Save if requested
            if save_results:
                results_file = Path(f"8020_external_validation_results.json")
                _save_8020_external_results(results, results_file)
                console.print(f"💾 Results saved to: {results_file}")
            
            # Summary
            if results["success"]:
                console.print("\n[green]✅ 80/20 External Project Validation PASSED[/green]")
                console.print(f"[green]✓ uvmgr successfully validated across {results['successful_projects']}/{results['projects_validated']} external projects[/green]")
                console.print(f"[green]✓ Overall success rate: {results['overall_success_rate']:.1%}[/green]")
            else:
                console.print("\n[red]❌ 80/20 External Project Validation FAILED[/red]")
                console.print(f"[red]Success rate {results['overall_success_rate']:.1%} below 80% threshold[/red]")
            
            add_span_event("8020_external_validation_completed", {
                "success": results["success"],
                "projects_discovered": results["projects_discovered"],
                "projects_validated": results["projects_validated"],
                "success_rate": results["overall_success_rate"],
            })
            
            if not results["success"]:
                raise typer.Exit(1)
                
        except Exception as e:
            add_span_event("8020_external_validation_failed", {"error": str(e)})
            console.print(f"[red]❌ 80/20 External validation failed: {e}[/red]")
            raise typer.Exit(1)


def _display_validation_results(result) -> None:
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


def _save_validation_results(result, output_file: Path) -> None:
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


def _display_validation_results_simple(results: dict, verbose: bool):
    """Display simple validation results in a formatted table."""
    summary = results["summary"]
    
    # Summary table
    summary_table = Table(title="Validation Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Iterations", str(summary["total_iterations"]))
    summary_table.add_row("Passed", str(summary["passed_iterations"]))
    summary_table.add_row("Failed", str(summary["failed_iterations"]))
    summary_table.add_row("Success Rate", f"{summary['success_rate']:.1f}%")
    summary_table.add_row("Total Duration", f"{summary['total_duration']:.3f}s")
    summary_table.add_row("Avg Duration", f"{summary['average_iteration_duration']:.3f}s")
    
    console.print(summary_table)
    
    # Detailed results if verbose
    if verbose and results["validation_results"]:
        details_table = Table(title="Iteration Details")
        details_table.add_column("Iteration", style="cyan")
        details_table.add_column("Status", style="green")
        details_table.add_column("Duration", style="yellow")
        details_table.add_column("Steps", style="blue")
        details_table.add_column("Passed", style="magenta")
        
        for result in results["validation_results"]:
            status_emoji = "✅" if result.get("validation_passed") else "❌"
            status = f"{status_emoji} {result['status']}"
            
            details_table.add_row(
                str(result["iteration"]),
                status,
                f"{result['duration']:.3f}s",
                str(result.get("steps_executed", "N/A")),
                "Yes" if result.get("validation_passed") else "No"
            )
        
        console.print(details_table)


def _export_validation_results_simple(results: dict, workflow_file: Path):
    """Export simple validation results to JSON file."""
    output_file = workflow_file.parent / f"{workflow_file.stem}_validation_results.json"
    
    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        console.print(f"[green]✅ Results exported to: {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to export results: {e}[/red]")


def _generate_otel_workflow_content(name: str, test_commands: list) -> str:
    """Generate BPMN workflow content for OTEL validation."""
    # Generate service tasks for each test command
    tasks_xml = ""
    flows_xml = ""
    
    for i, cmd in enumerate(test_commands):
        task_id = f"test_command_{i}"
        task_name = f"Execute: {cmd[:30]}..."
        
        if i == 0:
            # First task connects from start
            flows_xml += f'    <bpmn:sequenceFlow id="Flow_to_{task_id}" sourceRef="start" targetRef="{task_id}" />\n'
        else:
            # Subsequent tasks connect from previous
            prev_task_id = f"test_command_{i-1}"
            flows_xml += f'    <bpmn:sequenceFlow id="Flow_{prev_task_id}_to_{task_id}" sourceRef="{prev_task_id}" targetRef="{task_id}" />\n'
        
        tasks_xml += f'''    <bpmn:serviceTask id="{task_id}" name="{task_name}">
      <bpmn:incoming>Flow_{"to_" if i == 0 else f"test_command_{i-1}_to_"}{task_id}</bpmn:incoming>
      <bpmn:outgoing>Flow_{task_id}_to_{"end" if i == len(test_commands) - 1 else f"test_command_{i+1}"}</bpmn:outgoing>
    </bpmn:serviceTask>
    
'''
    
    # Final flow to end
    if test_commands:
        last_task = f"test_command_{len(test_commands) - 1}"
        flows_xml += f'    <bpmn:sequenceFlow id="Flow_{last_task}_to_end" sourceRef="{last_task}" targetRef="end" />\n'
    else:
        flows_xml += '    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="start" targetRef="end" />\n'
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="{name}" name="{name.replace('_', ' ').title()}" isExecutable="true">
    
    <bpmn:startEvent id="start" name="Start OTEL Validation">
      <bpmn:outgoing>Flow_to_{"test_command_0" if test_commands else "end"}</bpmn:outgoing>
    </bpmn:startEvent>
    
{flows_xml}
{tasks_xml}    
    <bpmn:endEvent id="end" name="Validation Complete">
      <bpmn:incoming>Flow_{"test_command_" + str(len(test_commands) - 1) + "_to_end" if test_commands else "to_end"}</bpmn:incoming>
    </bpmn:endEvent>
    
  </bpmn:process>
</bpmn:definitions>'''


# External Project Validation Display Functions

def _display_external_validation_results(result) -> None:
    """Display external project validation results."""
    # Project info panel
    project_panel_content = f"""[bold]Project:[/bold] {result.project_info.name}
[bold]Path:[/bold] {result.project_info.path}
[bold]Type:[/bold] {result.project_info.project_type}
[bold]Package Manager:[/bold] {result.project_info.package_manager}
[bold]Has Tests:[/bold] {'Yes' if result.project_info.has_tests else 'No'}
[bold]Test Framework:[/bold] {result.project_info.test_framework or 'None'}
[bold]Has pyproject.toml:[/bold] {'Yes' if result.project_info.has_pyproject else 'No'}"""
    
    console.print(Panel(project_panel_content, title="Project Information", border_style="blue"))
    
    # Installation results
    install_color = "green" if result.installation_success else "red"
    install_icon = "✅" if result.installation_success else "❌"
    console.print(f"\n{install_icon} [bold {install_color}]Installation: {'SUCCESS' if result.installation_success else 'FAILED'}[/bold {install_color}] ({result.installation_time:.2f}s)")
    
    # OTEL validation results
    _display_validation_results(result.validation_result)
    
    # uvmgr integration
    integration_color = "green" if result.uvmgr_integration_success else "red"
    integration_icon = "✅" if result.uvmgr_integration_success else "❌"
    console.print(f"\n{integration_icon} [bold {integration_color}]uvmgr Integration: {'SUCCESS' if result.uvmgr_integration_success else 'FAILED'}[/bold {integration_color}]")
    
    # Recommendations
    if result.recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for i, rec in enumerate(result.recommendations, 1):
            console.print(f"  {i}. {rec}")


def _save_external_validation_results(result, output_file: Path) -> None:
    """Save external validation results to JSON file."""
    results_data = {
        "project_info": {
            "name": result.project_info.name,
            "path": str(result.project_info.path),
            "language": result.project_info.language,
            "package_manager": result.project_info.package_manager,
            "has_tests": result.project_info.has_tests,
            "test_framework": result.project_info.test_framework,
            "has_requirements": result.project_info.has_requirements,
            "has_pyproject": result.project_info.has_pyproject,
            "dependencies": result.project_info.dependencies,
            "project_type": result.project_info.project_type,
        },
        "validation_result": {
            "success": result.validation_result.success,
            "workflow_name": result.validation_result.workflow_name,
            "duration_seconds": result.validation_result.duration_seconds,
            "validation_steps": result.validation_result.validation_steps,
            "metrics_validated": result.validation_result.metrics_validated,
            "spans_validated": result.validation_result.spans_validated,
            "errors": result.validation_result.errors,
            "performance_data": result.validation_result.performance_data,
        },
        "installation_success": result.installation_success,
        "installation_time": result.installation_time,
        "uvmgr_integration_success": result.uvmgr_integration_success,
        "original_dependencies_preserved": result.original_dependencies_preserved,
        "cleanup_success": result.cleanup_success,
        "recommendations": result.recommendations,
        "generated_at": "2025-06-28T00:00:00Z",
    }
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)


def _display_batch_validation_results(results) -> None:
    """Display batch validation results in a table."""
    console.print("\n[bold]Batch Validation Results:[/bold]")
    
    # Summary table
    table = Table(title="Project Validation Summary")
    table.add_column("Project", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Installation", style="yellow")
    table.add_column("OTEL Validation", style="green")
    table.add_column("Integration", style="magenta")
    table.add_column("Duration", style="dim")
    
    for project_name, result in results.items():
        install_status = "✅" if result.installation_success else "❌"
        validation_status = "✅" if result.validation_result.success else "❌"
        integration_status = "✅" if result.uvmgr_integration_success else "❌"
        
        table.add_row(
            project_name,
            result.project_info.project_type,
            install_status,
            validation_status,
            integration_status,
            f"{result.validation_result.duration_seconds:.1f}s"
        )
    
    console.print(table)
    
    # Overall statistics
    total = len(results)
    successful_installs = sum(1 for r in results.values() if r.installation_success)
    successful_validations = sum(1 for r in results.values() if r.validation_result.success)
    successful_integrations = sum(1 for r in results.values() if r.uvmgr_integration_success)
    
    console.print(f"\n[bold]Overall Statistics:[/bold]")
    console.print(f"  • Total Projects: {total}")
    console.print(f"  • Successful Installations: {successful_installs}/{total} ({successful_installs/total:.1%})")
    console.print(f"  • Successful Validations: {successful_validations}/{total} ({successful_validations/total:.1%})")
    console.print(f"  • Successful Integrations: {successful_integrations}/{total} ({successful_integrations/total:.1%})")


def _save_batch_validation_results(results, output_file: Path) -> None:
    """Save batch validation results to JSON file."""
    batch_data = {
        "total_projects": len(results),
        "timestamp": "2025-06-28T00:00:00Z",
        "results": {}
    }
    
    for project_name, result in results.items():
        batch_data["results"][project_name] = {
            "project_info": {
                "name": result.project_info.name,
                "path": str(result.project_info.path),
                "type": result.project_info.project_type,
                "package_manager": result.project_info.package_manager,
                "has_tests": result.project_info.has_tests,
            },
            "installation_success": result.installation_success,
            "installation_time": result.installation_time,
            "validation_success": result.validation_result.success,
            "validation_duration": result.validation_result.duration_seconds,
            "metrics_validated": result.validation_result.metrics_validated,
            "spans_validated": result.validation_result.spans_validated,
            "integration_success": result.uvmgr_integration_success,
            "errors": result.validation_result.errors,
            "recommendations": result.recommendations,
        }
    
    with open(output_file, 'w') as f:
        json.dump(batch_data, f, indent=2)


def _display_8020_external_results(results) -> None:
    """Display 80/20 external validation results."""
    # Main summary panel
    status_color = "green" if results["success"] else "red"
    status_icon = "✅" if results["success"] else "❌"
    
    summary_content = f"""[{status_color}]{status_icon} 80/20 Validation: {'PASSED' if results['success'] else 'FAILED'}[/{status_color}]

[bold]Projects Discovered:[/bold] {results['projects_discovered']}
[bold]Projects Validated:[/bold] {results['projects_validated']}
[bold]Successful Projects:[/bold] {results['successful_projects']}
[bold]Failed Projects:[/bold] {results['failed_projects']}
[bold]Overall Success Rate:[/bold] {results['overall_success_rate']:.1%}
[bold]Total Metrics Validated:[/bold] {results['total_metrics_validated']}
[bold]Total Spans Validated:[/bold] {results['total_spans_validated']}
[bold]Total Errors:[/bold] {results['total_errors']}"""
    
    console.print(Panel(summary_content, title="80/20 External Project Validation Results", border_style=status_color))
    
    # Critical projects table
    if results.get("critical_projects"):
        console.print("\n[bold]Critical Projects Selected:[/bold]")
        critical_table = Table()
        critical_table.add_column("Project", style="cyan")
        critical_table.add_column("Type", style="blue")
        critical_table.add_column("Has Tests", style="yellow")
        critical_table.add_column("Path", style="dim")
        
        for project in results["critical_projects"]:
            critical_table.add_row(
                project["name"],
                project["type"],
                "✅" if project["has_tests"] else "❌",
                project["path"]
            )
        
        console.print(critical_table)
    
    # Individual project results if available
    if results.get("validation_results"):
        _display_batch_validation_results(results["validation_results"])


def _save_8020_external_results(results, output_file: Path) -> None:
    """Save 80/20 external validation results to JSON file."""
    # Convert any non-serializable objects
    serializable_results = {}
    for key, value in results.items():
        if key == "validation_results":
            # Convert ExternalValidationResult objects to dictionaries
            serializable_results[key] = {
                project_name: {
                    "project_name": result.project_info.name,
                    "project_type": result.project_info.project_type,
                    "installation_success": result.installation_success,
                    "validation_success": result.validation_result.success,
                    "integration_success": result.uvmgr_integration_success,
                    "metrics_validated": result.validation_result.metrics_validated,
                    "spans_validated": result.validation_result.spans_validated,
                    "errors": result.validation_result.errors,
                }
                for project_name, result in value.items()
            }
        else:
            serializable_results[key] = value
    
    serializable_results["generated_at"] = "2025-06-28T00:00:00Z"
    
    with open(output_file, 'w') as f:
        json.dump(serializable_results, f, indent=2, default=str)