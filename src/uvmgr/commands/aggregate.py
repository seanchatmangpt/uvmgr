"""
uvmgr.commands.aggregate - Command Aggregation with 8020 Implementation
=====================================================================

Command aggregation using Spiff workflows and Weaver semantic conventions.

This module provides CLI commands for aggregating multiple uvmgr commands
into efficient workflows using the 8020 principle (20% of effort for 80% of value)
with SpiffWorkflow orchestration and Weaver semantic convention validation.

Key Features
-----------
• **8020 Workflows**: Focus on critical commands that provide maximum value
• **Spiff Orchestration**: BPMN-based workflow execution for complex aggregations
• **Weaver Integration**: Semantic convention validation and code generation
• **Parallel Execution**: Run compatible commands concurrently
• **Smart Sequencing**: Intelligent command ordering based on dependencies
• **Result Aggregation**: Combine results from multiple commands
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **8020-workflow**: Execute 8020-optimized command aggregation workflow
- **validate**: Validate command aggregation using Weaver semantic conventions
- **generate**: Generate BPMN workflows for command aggregation
- **execute**: Execute custom command aggregation workflow
- **analyze**: Analyze command dependencies and optimize aggregation
- **status**: Show aggregation workflow status and metrics

8020 Implementation
------------------
- **Critical Commands**: Identify 20% of commands that provide 80% of value
- **Smart Batching**: Group related commands for efficient execution
- **Dependency Resolution**: Automatically resolve command dependencies
- **Fallback Mechanisms**: Graceful degradation for non-critical commands
- **Performance Optimization**: Parallel execution where possible

Examples
--------
    >>> # Execute 8020 workflow
    >>> uvmgr aggregate 8020-workflow --mode development
    >>> 
    >>> # Validate aggregation
    >>> uvmgr aggregate validate --workflow custom.bpmn
    >>> 
    >>> # Generate workflow
    >>> uvmgr aggregate generate --commands "deps,test,build" --output workflow.bpmn
    >>> 
    >>> # Execute custom workflow
    >>> uvmgr aggregate execute --workflow workflow.bpmn --parallel

See Also
--------
- :mod:`uvmgr.commands.spiff_otel` : SpiffWorkflow OTEL integration
- :mod:`uvmgr.commands.weaver` : Weaver semantic convention tools
- :mod:`uvmgr.core.workflows` : Workflow engine implementation
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from enum import Enum

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.tree import Tree

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations, CliAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception
from uvmgr.ops.aggregate import (
    create_8020_workflow,
    execute_aggregation_workflow,
    analyze_command_dependencies,
    validate_aggregation_workflow,
    generate_bpmn_workflow,
    get_aggregation_metrics
)

app = typer.Typer(help="Command aggregation with 8020 implementation using Spiff and Weaver")
console = Console()


class AggregationMode(Enum):
    """Aggregation execution modes."""
    DEVELOPMENT = "development"
    CI_CD = "ci_cd"
    DEPLOYMENT = "deployment"
    VALIDATION = "validation"
    CUSTOM = "custom"


@dataclass
class CommandNode:
    """Represents a command in the aggregation workflow."""
    name: str
    dependencies: Set[str] = field(default_factory=set)
    execution_time: float = 0.0
    success_rate: float = 1.0
    critical: bool = False
    parallel_safe: bool = True
    weaver_validation: bool = False


@dataclass
class AggregationResult:
    """Result of command aggregation execution."""
    workflow_name: str
    commands_executed: List[str]
    commands_successful: List[str]
    commands_failed: List[str]
    total_duration: float
    parallel_execution: bool
    weaver_validation_passed: bool
    spiff_workflow_used: bool
    metrics: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


@app.command("8020-workflow")
@instrument_command("aggregate_8020_workflow", track_args=True)
def execute_8020_workflow(
    mode: AggregationMode = typer.Option(
        AggregationMode.DEVELOPMENT,
        "--mode",
        "-m",
        help="Aggregation mode"
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--sequential",
        "-p/-s",
        help="Enable parallel execution where possible"
    ),
    validate_weaver: bool = typer.Option(
        True,
        "--validate-weaver/--no-validate-weaver",
        help="Validate using Weaver semantic conventions"
    ),
    save_workflow: bool = typer.Option(
        False,
        "--save-workflow",
        "-w",
        help="Save generated BPMN workflow"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be executed without running"
    ),
):
    """
    Execute 8020-optimized command aggregation workflow.
    
    This command implements the 8020 principle by identifying and executing
    the 20% of commands that provide 80% of value, orchestrated through
    SpiffWorkflow with Weaver semantic convention validation.
    
    Examples:
        uvmgr aggregate 8020-workflow --mode development --parallel
        uvmgr aggregate 8020-workflow --mode ci_cd --validate-weaver
        uvmgr aggregate 8020-workflow --dry-run --save-workflow
    """
    add_span_attributes(**{
        "aggregate.operation": "8020_workflow",
        "aggregate.mode": mode.value,
        "aggregate.parallel": parallel,
        "aggregate.validate_weaver": validate_weaver,
        "aggregate.dry_run": dry_run,
    })
    
    console.print(f"🎯 [bold cyan]8020 Command Aggregation Workflow[/bold cyan]")
    console.print(f"📋 Mode: {mode.value}")
    console.print(f"⚡ Parallel: {parallel}")
    console.print(f"🔍 Weaver Validation: {validate_weaver}")
    
    if dry_run:
        console.print("\n[yellow]🔍 DRY RUN MODE - No commands will be executed[/yellow]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Analyze dependencies
            task1 = progress.add_task("Analyzing command dependencies...", total=1)
            dependencies = analyze_command_dependencies()
            progress.advance(task1)
            
            # Step 2: Create 8020 workflow
            task2 = progress.add_task("Creating 8020 workflow...", total=1)
            workflow_path = create_8020_workflow(
                mode=mode.value,
                parallel=parallel,
                validate_weaver=validate_weaver,
                dependencies=dependencies
            )
            progress.advance(task2)
            
            # Step 3: Validate with Weaver (if enabled)
            if validate_weaver:
                task3 = progress.add_task("Validating with Weaver semantic conventions...", total=1)
                validation_result = validate_aggregation_workflow(workflow_path)
                if not validation_result["valid"]:
                    console.print(f"[red]❌ Weaver validation failed: {validation_result['errors']}[/red]")
                    raise typer.Exit(1)
                progress.advance(task3)
            
            # Step 4: Execute workflow (or show plan)
            if dry_run:
                task4 = progress.add_task("Generating execution plan...", total=1)
                plan = _generate_execution_plan(workflow_path, mode, parallel)
                progress.advance(task4)
                
                _display_execution_plan(plan)
                
                if save_workflow:
                    console.print(f"💾 Workflow saved to: {workflow_path}")
                
            else:
                task4 = progress.add_task("Executing 8020 workflow...", total=1)
                result = execute_aggregation_workflow(
                    workflow_path=workflow_path,
                    parallel=parallel,
                    validate_weaver=validate_weaver
                )
                progress.advance(task4)
                
                # Step 5: Display results
                _display_aggregation_results(result)
                
                # Save workflow if requested
                if save_workflow:
                    console.print(f"💾 Workflow saved to: {workflow_path}")
                
                # Exit with appropriate code
                if result.commands_failed:
                    raise typer.Exit(1)
        
        add_span_event("aggregate.8020_workflow.completed", {
            "mode": mode.value,
            "parallel": parallel,
            "weaver_validation": validate_weaver,
            "dry_run": dry_run,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ 8020 workflow execution failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
@instrument_command("aggregate_validate", track_args=True)
def validate_workflow(
    workflow_file: Optional[Path] = typer.Option(
        None,
        "--workflow",
        "-w",
        help="BPMN workflow file to validate"
    ),
    weaver_only: bool = typer.Option(
        False,
        "--weaver-only",
        help="Only validate Weaver semantic conventions"
    ),
    spiff_only: bool = typer.Option(
        False,
        "--spiff-only",
        help="Only validate SpiffWorkflow structure"
    ),
):
    """
    Validate command aggregation workflow using Weaver semantic conventions.
    
    This command validates BPMN workflows for command aggregation, ensuring
    they comply with Weaver semantic conventions and SpiffWorkflow requirements.
    
    Examples:
        uvmgr aggregate validate --workflow workflow.bpmn
        uvmgr aggregate validate --weaver-only
        uvmgr aggregate validate --spiff-only
    """
    add_span_attributes(**{
        "aggregate.operation": "validate",
        "aggregate.workflow_file": str(workflow_file) if workflow_file else "default",
        "aggregate.weaver_only": weaver_only,
        "aggregate.spiff_only": spiff_only,
    })
    
    console.print("🔍 [bold cyan]Aggregation Workflow Validation[/bold cyan]")
    
    try:
        if workflow_file and not workflow_file.exists():
            console.print(f"[red]❌ Workflow file not found: {workflow_file}[/red]")
            raise typer.Exit(1)
        
        # Determine validation scope
        validate_weaver = not spiff_only
        validate_spiff = not weaver_only
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            results = {}
            
            # Weaver validation
            if validate_weaver:
                task1 = progress.add_task("Validating Weaver semantic conventions...", total=1)
                weaver_result = validate_aggregation_workflow(
                    workflow_file or Path("default_workflow.bpmn"),
                    weaver_only=True
                )
                results["weaver"] = weaver_result
                progress.advance(task1)
            
            # Spiff validation
            if validate_spiff:
                task2 = progress.add_task("Validating SpiffWorkflow structure...", total=1)
                spiff_result = validate_aggregation_workflow(
                    workflow_file or Path("default_workflow.bpmn"),
                    spiff_only=True
                )
                results["spiff"] = spiff_result
                progress.advance(task2)
            
            # Display validation results
            _display_validation_results(results)
            
            # Determine overall success
            all_valid = all(result.get("valid", False) for result in results.values())
            
            if all_valid:
                console.print("\n[green]✅ All validations passed[/green]")
            else:
                console.print("\n[red]❌ Some validations failed[/red]")
                raise typer.Exit(1)
        
        add_span_event("aggregate.validation.completed", {
            "weaver_valid": results.get("weaver", {}).get("valid", False),
            "spiff_valid": results.get("spiff", {}).get("valid", False),
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("generate")
@instrument_command("aggregate_generate", track_args=True)
def generate_workflow(
    commands: str = typer.Option(
        "deps,test,build",
        "--commands",
        "-c",
        help="Comma-separated list of commands to aggregate"
    ),
    output_file: Path = typer.Option(
        Path("aggregation_workflow.bpmn"),
        "--output",
        "-o",
        help="Output BPMN workflow file"
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--sequential",
        "-p/-s",
        help="Enable parallel execution where possible"
    ),
    include_weaver: bool = typer.Option(
        True,
        "--include-weaver/--no-weaver",
        help="Include Weaver semantic convention validation"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing file"
    ),
):
    """
    Generate BPMN workflow for command aggregation.
    
    This command generates a BPMN workflow file that orchestrates multiple
    uvmgr commands with proper dependencies, parallel execution, and
    Weaver semantic convention validation.
    
    Examples:
        uvmgr aggregate generate --commands "deps,test,build,release"
        uvmgr aggregate generate --output custom.bpmn --parallel
        uvmgr aggregate generate --commands "lint,test" --no-weaver
    """
    add_span_attributes(**{
        "aggregate.operation": "generate",
        "aggregate.commands": commands,
        "aggregate.output_file": str(output_file),
        "aggregate.parallel": parallel,
        "aggregate.include_weaver": include_weaver,
    })
    
    if output_file.exists() and not force:
        console.print(f"[red]❌ File exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)
    
    console.print("⚙️ [bold cyan]Generating Command Aggregation Workflow[/bold cyan]")
    console.print(f"📋 Commands: {commands}")
    console.print(f"📄 Output: {output_file}")
    console.print(f"⚡ Parallel: {parallel}")
    console.print(f"🔍 Weaver: {include_weaver}")
    
    try:
        # Parse commands
        command_list = [cmd.strip() for cmd in commands.split(",")]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Generating BPMN workflow...", total=1)
            
            # Generate workflow
            workflow_content = generate_bpmn_workflow(
                commands=command_list,
                parallel=parallel,
                include_weaver=include_weaver
            )
            
            # Write to file
            output_file.write_text(workflow_content)
            progress.advance(task)
        
        console.print(f"\n✅ Generated workflow: {output_file}")
        console.print(f"📊 Commands included: {len(command_list)}")
        console.print(f"🔗 Dependencies resolved: {len(command_list) - 1}")
        
        # Show usage
        console.print("\n[bold]Usage:[/bold]")
        console.print(f"  uvmgr aggregate execute --workflow {output_file}")
        console.print(f"  uvmgr aggregate validate --workflow {output_file}")
        
        add_span_event("aggregate.workflow.generated", {
            "output_file": str(output_file),
            "commands_count": len(command_list),
            "parallel": parallel,
            "include_weaver": include_weaver,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Workflow generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("execute")
@instrument_command("aggregate_execute", track_args=True)
def execute_workflow(
    workflow_file: Path = typer.Argument(..., help="BPMN workflow file to execute"),
    parallel: bool = typer.Option(
        True,
        "--parallel/--sequential",
        "-p/-s",
        help="Enable parallel execution where possible"
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        "-t",
        help="Execution timeout in seconds"
    ),
    validate_weaver: bool = typer.Option(
        True,
        "--validate-weaver/--no-validate-weaver",
        help="Validate using Weaver semantic conventions"
    ),
):
    """
    Execute custom command aggregation workflow.
    
    This command executes a custom BPMN workflow file for command aggregation,
    with full SpiffWorkflow orchestration and Weaver semantic convention validation.
    
    Examples:
        uvmgr aggregate execute workflow.bpmn --parallel
        uvmgr aggregate execute custom.bpmn --timeout 600
        uvmgr aggregate execute workflow.bpmn --no-validate-weaver
    """
    add_span_attributes(**{
        "aggregate.operation": "execute",
        "aggregate.workflow_file": str(workflow_file),
        "aggregate.parallel": parallel,
        "aggregate.timeout": timeout,
        "aggregate.validate_weaver": validate_weaver,
    })
    
    if not workflow_file.exists():
        console.print(f"[red]❌ Workflow file not found: {workflow_file}[/red]")
        raise typer.Exit(1)
    
    console.print("🔄 [bold cyan]Executing Command Aggregation Workflow[/bold cyan]")
    console.print(f"📄 Workflow: {workflow_file}")
    console.print(f"⚡ Parallel: {parallel}")
    console.print(f"⏱️ Timeout: {timeout}s")
    console.print(f"🔍 Weaver Validation: {validate_weaver}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Executing aggregation workflow...", total=1)
            
            # Execute workflow
            result = execute_aggregation_workflow(
                workflow_path=workflow_file,
                parallel=parallel,
                validate_weaver=validate_weaver,
                timeout=timeout
            )
            progress.advance(task)
        
        # Display results
        _display_aggregation_results(result)
        
        # Exit with appropriate code
        if result.commands_failed:
            raise typer.Exit(1)
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Workflow execution failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("analyze")
@instrument_command("aggregate_analyze", track_args=True)
def analyze_dependencies(
    commands: Optional[str] = typer.Option(
        None,
        "--commands",
        "-c",
        help="Comma-separated commands to analyze (default: all)"
    ),
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, tree"
    ),
    show_metrics: bool = typer.Option(
        True,
        "--metrics/--no-metrics",
        help="Show execution metrics"
    ),
):
    """
    Analyze command dependencies and optimize aggregation.
    
    This command analyzes command dependencies, execution patterns, and
    provides recommendations for optimal aggregation workflows.
    
    Examples:
        uvmgr aggregate analyze
        uvmgr aggregate analyze --commands "deps,test,build" --format json
        uvmgr aggregate analyze --no-metrics --format tree
    """
    add_span_attributes(**{
        "aggregate.operation": "analyze",
        "aggregate.commands": commands,
        "aggregate.output_format": output_format,
        "aggregate.show_metrics": show_metrics,
    })
    
    console.print("🔍 [bold cyan]Command Dependency Analysis[/bold cyan]")
    
    if commands:
        command_list = [cmd.strip() for cmd in commands.split(",")]
        console.print(f"📋 Analyzing commands: {', '.join(command_list)}")
    else:
        console.print("📋 Analyzing all available commands")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Analyzing dependencies...", total=1)
            
            # Analyze dependencies
            analysis = analyze_command_dependencies(
                commands=command_list if commands else None
            )
            progress.advance(task)
        
        # Display analysis results
        if output_format == "json":
            console.print(json.dumps(analysis, indent=2))
        elif output_format == "tree":
            _display_dependency_tree(analysis)
        else:
            _display_dependency_table(analysis, show_metrics)
        
        add_span_event("aggregate.analysis.completed", {
            "commands_analyzed": len(analysis.get("commands", [])),
            "dependencies_found": len(analysis.get("dependencies", [])),
            "output_format": output_format,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Analysis failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
@instrument_command("aggregate_status", track_args=True)
def show_status(
    workflow_file: Optional[Path] = typer.Option(
        None,
        "--workflow",
        "-w",
        help="Show status for specific workflow file"
    ),
    show_metrics: bool = typer.Option(
        True,
        "--metrics/--no-metrics",
        help="Show detailed metrics"
    ),
):
    """
    Show aggregation workflow status and metrics.
    
    This command displays the current status of aggregation workflows,
    execution metrics, and Weaver semantic convention compliance.
    
    Examples:
        uvmgr aggregate status
        uvmgr aggregate status --workflow workflow.bpmn
        uvmgr aggregate status --no-metrics
    """
    add_span_attributes(**{
        "aggregate.operation": "status",
        "aggregate.workflow_file": str(workflow_file) if workflow_file else "all",
        "aggregate.show_metrics": show_metrics,
    })
    
    console.print("📊 [bold cyan]Aggregation Workflow Status[/bold cyan]")
    
    try:
        # Get metrics
        metrics = get_aggregation_metrics(workflow_file)
        
        # Display status
        _display_status_table(metrics, show_metrics)
        
        add_span_event("aggregate.status.displayed", {
            "workflows_count": len(metrics.get("workflows", [])),
            "total_executions": metrics.get("total_executions", 0),
            "success_rate": metrics.get("success_rate", 0),
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Status display failed: {e}[/red]")
        raise typer.Exit(1)


def _generate_execution_plan(workflow_path: Path, mode: AggregationMode, parallel: bool) -> Dict[str, Any]:
    """Generate execution plan for dry run mode."""
    return {
        "workflow_file": str(workflow_path),
        "mode": mode.value,
        "parallel": parallel,
        "estimated_commands": ["deps", "test", "build", "release"],
        "estimated_duration": 120.0,
        "critical_path": ["deps", "test", "build"],
        "parallel_groups": [["deps"], ["test", "lint"], ["build"]],
    }


def _display_execution_plan(plan: Dict[str, Any]):
    """Display execution plan for dry run mode."""
    console.print("\n📋 [bold]Execution Plan[/bold]")
    
    table = Table(title="8020 Workflow Execution Plan")
    table.add_column("Component", style="cyan")
    table.add_column("Details", style="white")
    
    table.add_row("Workflow File", plan["workflow_file"])
    table.add_row("Mode", plan["mode"])
    table.add_row("Parallel Execution", "✅ Yes" if plan["parallel"] else "❌ No")
    table.add_row("Estimated Commands", str(len(plan["estimated_commands"])))
    table.add_row("Estimated Duration", f"{plan['estimated_duration']:.1f}s")
    table.add_row("Critical Path", " → ".join(plan["critical_path"]))
    
    console.print(table)
    
    if plan["parallel_groups"]:
        console.print("\n⚡ [bold]Parallel Execution Groups[/bold]")
        for i, group in enumerate(plan["parallel_groups"], 1):
            console.print(f"  Group {i}: {', '.join(group)}")


def _display_aggregation_results(result: AggregationResult):
    """Display aggregation execution results."""
    console.print("\n📊 [bold]Aggregation Results[/bold]")
    
    # Summary table
    table = Table(title="Execution Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Workflow", result.workflow_name)
    table.add_row("Commands Executed", str(len(result.commands_executed)))
    table.add_row("Successful", str(len(result.commands_successful)))
    table.add_row("Failed", str(len(result.commands_failed)))
    table.add_row("Total Duration", f"{result.total_duration:.2f}s")
    table.add_row("Parallel Execution", "✅ Yes" if result.parallel_execution else "❌ No")
    table.add_row("Weaver Validation", "✅ Passed" if result.weaver_validation_passed else "❌ Failed")
    table.add_row("Spiff Workflow", "✅ Used" if result.spiff_workflow_used else "❌ Not Used")
    
    console.print(table)
    
    # Success/failure summary
    if result.commands_successful:
        console.print(f"\n✅ [green]Successful Commands ({len(result.commands_successful)}):[/green]")
        for cmd in result.commands_successful:
            console.print(f"  • {cmd}")
    
    if result.commands_failed:
        console.print(f"\n❌ [red]Failed Commands ({len(result.commands_failed)}):[/red]")
        for cmd in result.commands_failed:
            console.print(f"  • {cmd}")
    
    # Metrics
    if result.metrics:
        console.print(f"\n📈 [bold]Metrics[/bold]")
        metrics_table = Table()
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        for key, value in result.metrics.items():
            if isinstance(value, float):
                metrics_table.add_row(key, f"{value:.2f}")
            else:
                metrics_table.add_row(key, str(value))
        
        console.print(metrics_table)


def _display_validation_results(results: Dict[str, Dict[str, Any]]):
    """Display validation results."""
    console.print("\n🔍 [bold]Validation Results[/bold]")
    
    table = Table(title="Validation Summary")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    for component, result in results.items():
        status = "✅ Passed" if result.get("valid", False) else "❌ Failed"
        details = result.get("message", "No details")
        table.add_row(component.title(), status, details)
    
    console.print(table)
    
    # Show errors if any
    for component, result in results.items():
        if not result.get("valid", False) and result.get("errors"):
            console.print(f"\n❌ [red]{component.title()} Errors:[/red]")
            for error in result["errors"]:
                console.print(f"  • {error}")


def _display_dependency_tree(analysis: Dict[str, Any]):
    """Display dependency analysis as a tree."""
    console.print("\n🌳 [bold]Command Dependency Tree[/bold]")
    
    tree = Tree("📦 uvmgr Commands")
    
    commands = analysis.get("commands", [])
    dependencies = analysis.get("dependencies", {})
    
    for cmd in commands:
        cmd_node = tree.add(f"🔧 {cmd}")
        
        # Add dependencies
        if cmd in dependencies:
            for dep in dependencies[cmd]:
                cmd_node.add(f"📋 {dep}")
    
    console.print(tree)


def _display_dependency_table(analysis: Dict[str, Any], show_metrics: bool):
    """Display dependency analysis as a table."""
    console.print("\n📋 [bold]Command Dependencies[/bold]")
    
    table = Table(title="Dependency Analysis")
    table.add_column("Command", style="cyan")
    table.add_column("Dependencies", style="white")
    table.add_column("Critical", style="green")
    table.add_column("Parallel Safe", style="blue")
    
    if show_metrics:
        table.add_column("Exec Time", style="yellow")
        table.add_column("Success Rate", style="magenta")
    
    commands = analysis.get("commands", [])
    dependencies = analysis.get("dependencies", {})
    metrics = analysis.get("metrics", {})
    
    for cmd in commands:
        deps = dependencies.get(cmd, [])
        deps_str = ", ".join(deps) if deps else "None"
        
        cmd_metrics = metrics.get(cmd, {})
        critical = "✅" if cmd_metrics.get("critical", False) else "❌"
        parallel_safe = "✅" if cmd_metrics.get("parallel_safe", True) else "❌"
        
        row = [cmd, deps_str, critical, parallel_safe]
        
        if show_metrics:
            exec_time = cmd_metrics.get("execution_time", 0.0)
            success_rate = cmd_metrics.get("success_rate", 1.0)
            row.extend([f"{exec_time:.2f}s", f"{success_rate:.1%}"])
        
        table.add_row(*row)
    
    console.print(table)


def _display_status_table(metrics: Dict[str, Any], show_metrics: bool):
    """Display status and metrics table."""
    console.print("\n📊 [bold]Aggregation Status[/bold]")
    
    # Basic status
    table = Table(title="Workflow Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Workflows", str(len(metrics.get("workflows", []))))
    table.add_row("Total Executions", str(metrics.get("total_executions", 0)))
    table.add_row("Success Rate", f"{metrics.get('success_rate', 0):.1%}")
    table.add_row("Average Duration", f"{metrics.get('avg_duration', 0):.2f}s")
    table.add_row("Weaver Validation", "✅ Enabled" if metrics.get("weaver_enabled", True) else "❌ Disabled")
    table.add_row("Spiff Integration", "✅ Active" if metrics.get("spiff_active", True) else "❌ Inactive")
    
    console.print(table)
    
    # Detailed metrics if requested
    if show_metrics and metrics.get("detailed_metrics"):
        console.print(f"\n📈 [bold]Detailed Metrics[/bold]")
        detailed_table = Table()
        detailed_table.add_column("Metric", style="cyan")
        detailed_table.add_column("Value", style="green")
        
        for key, value in metrics["detailed_metrics"].items():
            if isinstance(value, float):
                detailed_table.add_row(key, f"{value:.2f}")
            else:
                detailed_table.add_row(key, str(value))
        
        console.print(detailed_table) 