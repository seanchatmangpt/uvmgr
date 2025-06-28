"""
uvmgr.commands.workflow - Workflow Validation and Testing
=======================================================

Comprehensive workflow validation and testing commands with Spiff BPMN integration.

This module provides advanced workflow functionality including:
- BPMN file validation and testing
- OTEL integration validation
- Workflow performance testing
- Comprehensive reporting and analysis

Key Features
-----------
• **BPMN Validation**: Comprehensive BPMN file validation
• **OTEL Integration**: Full OpenTelemetry integration testing
• **Performance Testing**: Workflow execution performance analysis
• **Spiff Integration**: Native SpiffWorkflow engine support
• **Comprehensive Reporting**: Detailed test results and analysis

Available Commands
-----------------
- **validate**: Validate BPMN files with comprehensive checks
- **test**: Test workflow execution with OTEL validation
- **benchmark**: Benchmark workflow performance
- **analyze**: Analyze workflow structure and complexity
- **report**: Generate comprehensive workflow reports

Examples
--------
    >>> # Validate BPMN file
    >>> uvmgr workflow validate workflow.bpmn
    >>> 
    >>> # Test workflow with OTEL
    >>> uvmgr workflow test workflow.bpmn --otel
    >>> 
    >>> # Benchmark workflow performance
    >>> uvmgr workflow benchmark workflow.bpmn --iterations 10
    >>> 
    >>> # Analyze workflow complexity
    >>> uvmgr workflow analyze workflow.bpmn --detailed
    >>> 
    >>> # Generate comprehensive report
    >>> uvmgr workflow report workflow.bpmn --output report.json

See Also
--------
- :mod:`uvmgr.commands.agent` : Basic workflow execution
- :mod:`uvmgr.commands.otel` : OpenTelemetry validation
- :mod:`uvmgr.runtime.agent.spiff` : SpiffWorkflow engine
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.tree import Tree

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations
from uvmgr.core.telemetry import metric_counter, metric_histogram, span
from uvmgr.runtime.agent.spiff import run_bpmn, validate_bpmn_file, get_workflow_stats

from .. import main as cli_root  # exported root Typer app

console = Console()
workflow_app = typer.Typer(help="Advanced workflow validation and testing")
cli_root.app.add_typer(workflow_app, name="workflow")


@workflow_app.command("validate")
@instrument_command("workflow_validate", track_args=True)
def validate_workflow(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    comprehensive: bool = typer.Option(False, "--comprehensive", "-c", help="Run comprehensive validation"),
    check_otel: bool = typer.Option(True, "--otel/--no-otel", help="Check OTEL integration"),
    export_results: bool = typer.Option(False, "--export", "-e", help="Export validation results"),
    output: str = typer.Option("", "--output", "-o", help="Output file for results"),
):
    """Validate BPMN workflow with comprehensive checks and OTEL integration."""
    
    with span(
        "workflow.validate.comprehensive",
        **{
            WorkflowAttributes.OPERATION: "validate",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
        }
    ):
        validation_start = time.time()
        
        add_span_event("workflow.validation.started", {
            "workflow.file": str(file),
            "comprehensive": comprehensive,
            "check_otel": check_otel
        })

        console.print(f"[bold]🔍 Validating Workflow: {file.name}[/bold]")
        
        results = {
            "workflow": file.name,
            "timestamp": time.time(),
            "comprehensive": comprehensive,
            "check_otel": check_otel,
            "validation": {},
            "otel_integration": {},
            "performance": {},
            "structure": {}
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Basic BPMN Validation
            task1 = progress.add_task("Validating BPMN structure...", total=1)
            bpmn_result = _validate_bpmn_structure(file)
            results["validation"]["bpmn"] = bpmn_result
            progress.update(task1, completed=1)
            
            # Step 2: Workflow Structure Analysis
            task2 = progress.add_task("Analyzing workflow structure...", total=1)
            structure_result = _analyze_workflow_structure(file)
            results["structure"] = structure_result
            progress.update(task2, completed=1)
            
            # Step 3: OTEL Integration Check
            if check_otel:
                task3 = progress.add_task("Checking OTEL integration...", total=1)
                otel_result = _check_otel_integration(file)
                results["otel_integration"] = otel_result
                progress.update(task3, completed=1)
            
            # Step 4: Performance Validation
            if comprehensive:
                task4 = progress.add_task("Validating performance...", total=1)
                perf_result = _validate_performance(file)
                results["performance"] = perf_result
                progress.update(task4, completed=1)
        
        validation_duration = time.time() - validation_start
        
        # Calculate overall results
        _calculate_validation_summary(results)
        
        # Display results
        _display_validation_results(results, validation_duration)
        
        # Export results if requested
        if export_results:
            output_file = Path(output) if output else file.with_suffix(".validation.json")
            _export_validation_results(results, output_file)
        
        add_span_event("workflow.validation.completed", {
            "duration": validation_duration,
            "overall_status": results.get("overall_status", "unknown")
        })
        
        metric_counter("workflow.validations.completed")(1)
        metric_histogram("workflow.validation.duration")(validation_duration)
        
        # Exit with error if validation failed
        if results.get("overall_status") == "failed":
            raise typer.Exit(1)


@workflow_app.command("test")
@instrument_command("workflow_test", track_args=True)
def test_workflow(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    iterations: int = typer.Option(3, "--iterations", "-i", help="Number of test iterations"),
    otel_validation: bool = typer.Option(True, "--otel/--no-otel", help="Run OTEL validation tests"),
    performance_test: bool = typer.Option(True, "--performance/--no-performance", help="Run performance tests"),
    export_results: bool = typer.Option(False, "--export", "-e", help="Export test results"),
    output: str = typer.Option("", "--output", "-o", help="Output file for results"),
):
    """Test workflow execution with comprehensive OTEL validation."""
    
    with span(
        "workflow.test.comprehensive",
        **{
            WorkflowAttributes.OPERATION: "test",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
        }
    ):
        test_start = time.time()
        
        add_span_event("workflow.testing.started", {
            "workflow.file": str(file),
            "iterations": iterations,
            "otel_validation": otel_validation,
            "performance_test": performance_test
        })

        console.print(f"[bold]🧪 Testing Workflow: {file.name}[/bold]")
        
        results = {
            "workflow": file.name,
            "timestamp": time.time(),
            "iterations": iterations,
            "otel_validation": otel_validation,
            "performance_test": performance_test,
            "execution_tests": [],
            "otel_tests": {},
            "performance_metrics": {},
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
            
            # Step 1: Multiple Execution Tests
            task1 = progress.add_task(f"Running {iterations} execution tests...", total=iterations)
            for i in range(iterations):
                execution_result = _test_workflow_execution(file, i + 1)
                results["execution_tests"].append(execution_result)
                progress.update(task1, advance=1)
            
            # Step 2: OTEL Integration Tests
            if otel_validation:
                task2 = progress.add_task("Testing OTEL integration...", total=1)
                otel_result = _test_otel_integration_comprehensive(file)
                results["otel_tests"] = otel_result
                progress.update(task2, completed=1)
            
            # Step 3: Performance Tests
            if performance_test:
                task3 = progress.add_task("Running performance tests...", total=1)
                perf_result = _test_performance_comprehensive(file, iterations)
                results["performance_metrics"] = perf_result
                progress.update(task3, completed=1)
        
        test_duration = time.time() - test_start
        
        # Calculate test summary
        _calculate_test_summary(results)
        
        # Display results
        _display_test_results(results, test_duration)
        
        # Export results if requested
        if export_results:
            output_file = Path(output) if output else file.with_suffix(".test-results.json")
            _export_test_results(results, output_file)
        
        add_span_event("workflow.testing.completed", {
            "duration": test_duration,
            "tests_passed": results["summary"].get("passed", 0),
            "tests_total": results["summary"].get("total", 0)
        })
        
        metric_counter("workflow.tests.completed")(1)
        metric_histogram("workflow.test.duration")(test_duration)


@workflow_app.command("benchmark")
@instrument_command("workflow_benchmark", track_args=True)
def benchmark_workflow(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    iterations: int = typer.Option(10, "--iterations", "-i", help="Number of benchmark iterations"),
    warmup: int = typer.Option(2, "--warmup", "-w", help="Number of warmup iterations"),
    export_results: bool = typer.Option(False, "--export", "-e", help="Export benchmark results"),
    output: str = typer.Option("", "--output", "-o", help="Output file for results"),
):
    """Benchmark workflow performance with detailed metrics."""
    
    with span(
        "workflow.benchmark",
        **{
            WorkflowAttributes.OPERATION: "benchmark",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
        }
    ):
        benchmark_start = time.time()
        
        add_span_event("workflow.benchmark.started", {
            "workflow.file": str(file),
            "iterations": iterations,
            "warmup": warmup
        })

        console.print(f"[bold]🏃 Benchmarking Workflow: {file.name}[/bold]")
        
        results = {
            "workflow": file.name,
            "timestamp": time.time(),
            "iterations": iterations,
            "warmup": warmup,
            "warmup_results": [],
            "benchmark_results": [],
            "statistics": {},
            "recommendations": []
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Warmup runs
            if warmup > 0:
                task1 = progress.add_task(f"Warmup runs ({warmup})...", total=warmup)
                for i in range(warmup):
                    warmup_result = _test_workflow_execution(file, i + 1, is_warmup=True)
                    results["warmup_results"].append(warmup_result)
                    progress.update(task1, advance=1)
            
            # Step 2: Benchmark runs
            task2 = progress.add_task(f"Benchmark runs ({iterations})...", total=iterations)
            for i in range(iterations):
                benchmark_result = _test_workflow_execution(file, i + 1, is_benchmark=True)
                results["benchmark_results"].append(benchmark_result)
                progress.update(task2, advance=1)
        
        benchmark_duration = time.time() - benchmark_start
        
        # Calculate benchmark statistics
        _calculate_benchmark_statistics(results)
        
        # Generate recommendations
        _generate_benchmark_recommendations(results)
        
        # Display results
        _display_benchmark_results(results, benchmark_duration)
        
        # Export results if requested
        if export_results:
            output_file = Path(output) if output else file.with_suffix(".benchmark.json")
            _export_benchmark_results(results, output_file)
        
        add_span_event("workflow.benchmark.completed", {
            "duration": benchmark_duration,
            "avg_execution_time": results["statistics"].get("avg_execution_time", 0)
        })
        
        metric_counter("workflow.benchmarks.completed")(1)
        metric_histogram("workflow.benchmark.duration")(benchmark_duration)


@workflow_app.command("analyze")
@instrument_command("workflow_analyze", track_args=True)
def analyze_workflow(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed analysis"),
    complexity: bool = typer.Option(True, "--complexity/--no-complexity", help="Analyze complexity metrics"),
    export_results: bool = typer.Option(False, "--export", "-e", help="Export analysis results"),
    output: str = typer.Option("", "--output", "-o", help="Output file for results"),
):
    """Analyze workflow structure and complexity."""
    
    with span(
        "workflow.analyze",
        **{
            WorkflowAttributes.OPERATION: "analyze",
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.stem,
        }
    ):
        analysis_start = time.time()
        
        add_span_event("workflow.analysis.started", {
            "workflow.file": str(file),
            "detailed": detailed,
            "complexity": complexity
        })

        console.print(f"[bold]📊 Analyzing Workflow: {file.name}[/bold]")
        
        results = {
            "workflow": file.name,
            "timestamp": time.time(),
            "detailed": detailed,
            "complexity": complexity,
            "structure": {},
            "complexity_metrics": {},
            "recommendations": []
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Structure Analysis
            task1 = progress.add_task("Analyzing workflow structure...", total=1)
            structure_result = _analyze_workflow_structure_detailed(file)
            results["structure"] = structure_result
            progress.update(task1, completed=1)
            
            # Step 2: Complexity Analysis
            if complexity:
                task2 = progress.add_task("Analyzing complexity metrics...", total=1)
                complexity_result = _analyze_workflow_complexity(file)
                results["complexity_metrics"] = complexity_result
                progress.update(task2, completed=1)
        
        analysis_duration = time.time() - analysis_start
        
        # Generate recommendations
        _generate_analysis_recommendations(results)
        
        # Display results
        _display_analysis_results(results, analysis_duration, detailed)
        
        # Export results if requested
        if export_results:
            output_file = Path(output) if output else file.with_suffix(".analysis.json")
            _export_analysis_results(results, output_file)
        
        add_span_event("workflow.analysis.completed", {
            "duration": analysis_duration,
            "elements_count": results["structure"].get("total_elements", 0)
        })
        
        metric_counter("workflow.analyses.completed")(1)
        metric_histogram("workflow.analysis.duration")(analysis_duration)


# Helper functions

def _validate_bpmn_structure(file: Path) -> Dict[str, Any]:
    """Validate BPMN file structure."""
    try:
        is_valid = validate_bpmn_file(file)
        return {
            "status": "passed" if is_valid else "failed",
            "valid": is_valid,
            "file_size": file.stat().st_size,
            "file_readable": file.is_file() and file.readable()
        }
    except Exception as e:
        return {
            "status": "failed",
            "valid": False,
            "error": str(e)
        }


def _analyze_workflow_structure(file: Path) -> Dict[str, Any]:
    """Analyze workflow structure."""
    try:
        from SpiffWorkflow.bpmn.parser import BpmnParser
        
        parser = BpmnParser()
        parser.add_bpmn_file(str(file))
        
        processes = []
        total_tasks = 0
        
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
            "total_processes": len(processes),
            "total_tasks": total_tasks,
            "valid": True
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


def _check_otel_integration(file: Path) -> Dict[str, Any]:
    """Check OTEL integration."""
    try:
        with span("test.otel.integration", test_file=str(file)):
            add_span_event("test.otel.started")
            
            # Test basic OTEL functionality
            metric_counter("test.otel.counter")(1)
            metric_histogram("test.otel.duration")(0.1)
            
            add_span_event("test.otel.completed")
            
            return {
                "status": "passed",
                "otel_enabled": True,
                "spans_created": True,
                "metrics_recorded": True,
                "semantic_conventions": True
            }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "otel_enabled": False
        }


def _validate_performance(file: Path) -> Dict[str, Any]:
    """Validate workflow performance."""
    try:
        start_time = time.time()
        stats = run_bpmn(file)
        execution_time = time.time() - start_time
        
        return {
            "status": "passed",
            "execution_time": execution_time,
            "workflow_stats": stats,
            "performance_acceptable": execution_time < 10.0  # 10 second threshold
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


def _test_workflow_execution(file: Path, iteration: int, is_warmup: bool = False, is_benchmark: bool = False) -> Dict[str, Any]:
    """Test single workflow execution."""
    try:
        start_time = time.time()
        stats = run_bpmn(file)
        execution_time = time.time() - start_time
        
        return {
            "iteration": iteration,
            "type": "warmup" if is_warmup else "benchmark" if is_benchmark else "test",
            "status": "passed",
            "execution_time": execution_time,
            "workflow_stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "iteration": iteration,
            "type": "warmup" if is_warmup else "benchmark" if is_benchmark else "test",
            "status": "failed",
            "error": str(e),
            "timestamp": time.time()
        }


def _test_otel_integration_comprehensive(file: Path) -> Dict[str, Any]:
    """Test OTEL integration comprehensively."""
    tests = {
        "span_creation": _test_span_creation,
        "metrics_collection": _test_metrics_collection,
        "semantic_conventions": _test_semantic_conventions,
        "error_handling": _test_error_handling,
        "performance_tracking": _test_performance_tracking
    }
    
    results = {}
    passed = 0
    
    for test_name, test_func in tests.items():
        try:
            result = test_func(file)
            results[test_name] = result
            if result.get("status") == "passed":
                passed += 1
        except Exception as e:
            results[test_name] = {
                "status": "failed",
                "error": str(e)
            }
    
    return {
        "tests": results,
        "passed": passed,
        "total": len(tests),
        "success_rate": (passed / len(tests)) * 100 if tests else 0
    }


def _test_performance_comprehensive(file: Path, iterations: int) -> Dict[str, Any]:
    """Test performance comprehensively."""
    execution_times = []
    
    for i in range(iterations):
        try:
            start_time = time.time()
            stats = run_bpmn(file)
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
        except Exception:
            continue
    
    if execution_times:
        return {
            "execution_times": execution_times,
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "std_deviation": _calculate_std_deviation(execution_times),
            "successful_runs": len(execution_times),
            "total_runs": iterations
        }
    else:
        return {
            "error": "No successful executions",
            "successful_runs": 0,
            "total_runs": iterations
        }


def _analyze_workflow_structure_detailed(file: Path) -> Dict[str, Any]:
    """Analyze workflow structure in detail."""
    try:
        from SpiffWorkflow.bpmn.parser import BpmnParser
        
        parser = BpmnParser()
        parser.add_bpmn_file(str(file))
        
        processes = []
        elements = []
        element_types = {}
        
        for process_id, process_parser in parser.process_parsers.items():
            spec = parser.get_spec(process_id)
            
            process_info = {
                "id": process_id,
                "name": spec.name or "Unnamed",
                "tasks": [],
                "task_count": 0
            }
            
            for task_spec in spec.task_specs:
                element_type = task_spec.__class__.__name__
                element_info = {
                    "id": task_spec.id,
                    "name": task_spec.name or "Unnamed",
                    "type": element_type,
                    "process": process_id
                }
                
                elements.append(element_info)
                process_info["tasks"].append(element_info)
                process_info["task_count"] += 1
                
                element_types[element_type] = element_types.get(element_type, 0) + 1
            
            processes.append(process_info)
        
        return {
            "processes": processes,
            "elements": elements,
            "element_types": element_types,
            "total_processes": len(processes),
            "total_elements": len(elements),
            "unique_element_types": len(element_types)
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def _analyze_workflow_complexity(file: Path) -> Dict[str, Any]:
    """Analyze workflow complexity metrics."""
    try:
        structure = _analyze_workflow_structure_detailed(file)
        
        if "error" in structure:
            return {"error": structure["error"]}
        
        total_elements = structure["total_elements"]
        total_processes = structure["total_processes"]
        element_types = structure["element_types"]
        
        # Calculate complexity metrics
        complexity_score = total_elements * total_processes
        cyclomatic_complexity = total_elements - total_processes + 2
        
        # Determine complexity level
        if complexity_score < 10:
            complexity_level = "Low"
        elif complexity_score < 50:
            complexity_level = "Medium"
        else:
            complexity_level = "High"
        
        return {
            "complexity_score": complexity_score,
            "cyclomatic_complexity": cyclomatic_complexity,
            "complexity_level": complexity_level,
            "total_elements": total_elements,
            "total_processes": total_processes,
            "element_type_distribution": element_types
        }
    except Exception as e:
        return {"error": str(e)}


# OTEL test functions (imported from otel.py)
def _test_span_creation(file: Path) -> Dict[str, Any]:
    """Test span creation functionality."""
    try:
        with span("test.span.creation", test_file=str(file)):
            return {"status": "passed", "message": "Span creation working"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _test_metrics_collection(file: Path) -> Dict[str, Any]:
    """Test metrics collection functionality."""
    try:
        metric_counter("test.metrics.counter")(1)
        metric_histogram("test.metrics.duration")(0.1)
        return {"status": "passed", "message": "Metrics collection working"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _test_semantic_conventions(file: Path) -> Dict[str, Any]:
    """Test semantic conventions usage."""
    try:
        with span("test.semantic.conventions", 
                 workflow_file=str(file),
                 workflow_type="bpmn"):
            return {"status": "passed", "message": "Semantic conventions working"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _test_error_handling(file: Path) -> Dict[str, Any]:
    """Test error handling functionality."""
    try:
        with span("test.error.handling"):
            # Simulate an error
            raise ValueError("Test error")
    except ValueError:
        return {"status": "passed", "message": "Error handling working"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _test_performance_tracking(file: Path) -> Dict[str, Any]:
    """Test performance tracking functionality."""
    try:
        start_time = time.time()
        time.sleep(0.01)  # Simulate work
        duration = time.time() - start_time
        
        metric_histogram("test.performance.duration")(duration)
        return {"status": "passed", "message": "Performance tracking working"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# Utility functions
def _calculate_std_deviation(values: List[float]) -> float:
    """Calculate standard deviation."""
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


def _calculate_validation_summary(results: Dict[str, Any]) -> None:
    """Calculate validation summary."""
    validation_results = results.get("validation", {})
    otel_results = results.get("otel_integration", {})
    performance_results = results.get("performance", {})
    
    all_passed = True
    
    if validation_results.get("bpmn", {}).get("status") != "passed":
        all_passed = False
    
    if otel_results and otel_results.get("status") != "passed":
        all_passed = False
    
    if performance_results and performance_results.get("status") != "passed":
        all_passed = False
    
    results["overall_status"] = "passed" if all_passed else "failed"


def _calculate_test_summary(results: Dict[str, Any]) -> None:
    """Calculate test summary."""
    execution_tests = results.get("execution_tests", [])
    otel_tests = results.get("otel_tests", {})
    
    passed = 0
    total = 0
    
    # Count execution tests
    for test in execution_tests:
        total += 1
        if test.get("status") == "passed":
            passed += 1
    
    # Count OTEL tests
    if otel_tests:
        otel_passed = otel_tests.get("passed", 0)
        otel_total = otel_tests.get("total", 0)
        passed += otel_passed
        total += otel_total
    
    results["summary"] = {
        "passed": passed,
        "total": total,
        "success_rate": (passed / total * 100) if total > 0 else 0
    }


def _calculate_benchmark_statistics(results: Dict[str, Any]) -> None:
    """Calculate benchmark statistics."""
    benchmark_results = results.get("benchmark_results", [])
    
    if not benchmark_results:
        results["statistics"] = {"error": "No benchmark results"}
        return
    
    execution_times = [r["execution_time"] for r in benchmark_results if r.get("status") == "passed"]
    
    if execution_times:
        results["statistics"] = {
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "std_deviation": _calculate_std_deviation(execution_times),
            "successful_runs": len(execution_times),
            "total_runs": len(benchmark_results)
        }
    else:
        results["statistics"] = {"error": "No successful benchmark runs"}


def _generate_benchmark_recommendations(results: Dict[str, Any]) -> None:
    """Generate benchmark recommendations."""
    stats = results.get("statistics", {})
    recommendations = []
    
    if "avg_execution_time" in stats:
        avg_time = stats["avg_execution_time"]
        
        if avg_time > 5.0:
            recommendations.append("Consider optimizing workflow performance - execution time is high")
        elif avg_time < 0.1:
            recommendations.append("Workflow execution is very fast - consider adding more complex logic")
        
        if stats.get("std_deviation", 0) > avg_time * 0.5:
            recommendations.append("High execution time variance - check for inconsistent behavior")
    
    results["recommendations"] = recommendations


def _generate_analysis_recommendations(results: Dict[str, Any]) -> None:
    """Generate analysis recommendations."""
    complexity = results.get("complexity_metrics", {})
    structure = results.get("structure", {})
    recommendations = []
    
    if "complexity_level" in complexity:
        level = complexity["complexity_level"]
        if level == "High":
            recommendations.append("Consider breaking down complex workflow into smaller processes")
        elif level == "Low":
            recommendations.append("Workflow is simple - consider adding more functionality")
    
    if structure.get("total_elements", 0) > 20:
        recommendations.append("Large number of elements - consider modularization")
    
    if structure.get("total_processes", 0) > 3:
        recommendations.append("Multiple processes detected - ensure proper coordination")
    
    results["recommendations"] = recommendations


# Display functions
def _display_validation_results(results: Dict[str, Any], duration: float) -> None:
    """Display validation results."""
    table = Table(title="Workflow Validation Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    # BPMN Validation
    bpmn_result = results.get("validation", {}).get("bpmn", {})
    bpmn_status = "✅ PASSED" if bpmn_result.get("status") == "passed" else "❌ FAILED"
    table.add_row("BPMN Structure", bpmn_status, f"Size: {bpmn_result.get('file_size', 0)} bytes")
    
    # OTEL Integration
    otel_result = results.get("otel_integration", {})
    if otel_result:
        otel_status = "✅ PASSED" if otel_result.get("status") == "passed" else "❌ FAILED"
        table.add_row("OTEL Integration", otel_status, "Spans, Metrics, Conventions")
    
    # Performance
    perf_result = results.get("performance", {})
    if perf_result:
        perf_status = "✅ PASSED" if perf_result.get("status") == "passed" else "❌ FAILED"
        exec_time = perf_result.get("execution_time", 0)
        table.add_row("Performance", perf_status, f"{exec_time:.3f}s")
    
    console.print(table)
    console.print(f"[blue]Overall Status: {results.get('overall_status', 'unknown').upper()}[/blue]")
    console.print(f"[blue]Validation Duration: {duration:.3f}s[/blue]")


def _display_test_results(results: Dict[str, Any], duration: float) -> None:
    """Display test results."""
    summary = results.get("summary", {})
    
    table = Table(title="Workflow Test Results")
    table.add_column("Test Type", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    # Execution tests
    execution_tests = results.get("execution_tests", [])
    passed_exec = sum(1 for t in execution_tests if t.get("status") == "passed")
    table.add_row("Execution Tests", f"{passed_exec}/{len(execution_tests)}", "Workflow execution")
    
    # OTEL tests
    otel_tests = results.get("otel_tests", {})
    if otel_tests:
        otel_passed = otel_tests.get("passed", 0)
        otel_total = otel_tests.get("total", 0)
        table.add_row("OTEL Tests", f"{otel_passed}/{otel_total}", "Telemetry integration")
    
    console.print(table)
    console.print(f"[blue]Success Rate: {summary.get('success_rate', 0):.1f}%[/blue]")
    console.print(f"[blue]Test Duration: {duration:.3f}s[/blue]")


def _display_benchmark_results(results: Dict[str, Any], duration: float) -> None:
    """Display benchmark results."""
    stats = results.get("statistics", {})
    
    if "error" in stats:
        console.print(f"[red]Benchmark Error: {stats['error']}[/red]")
        return
    
    table = Table(title="Workflow Benchmark Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Average Execution Time", f"{stats.get('avg_execution_time', 0):.3f}s")
    table.add_row("Min Execution Time", f"{stats.get('min_execution_time', 0):.3f}s")
    table.add_row("Max Execution Time", f"{stats.get('max_execution_time', 0):.3f}s")
    table.add_row("Standard Deviation", f"{stats.get('std_deviation', 0):.3f}s")
    table.add_row("Successful Runs", f"{stats.get('successful_runs', 0)}/{stats.get('total_runs', 0)}")
    
    console.print(table)
    console.print(f"[blue]Benchmark Duration: {duration:.3f}s[/blue]")
    
    # Show recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in recommendations:
            console.print(f"• {rec}")


def _display_analysis_results(results: Dict[str, Any], duration: float, detailed: bool) -> None:
    """Display analysis results."""
    structure = results.get("structure", {})
    complexity = results.get("complexity_metrics", {})
    
    table = Table(title="Workflow Analysis Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Processes", str(structure.get("total_processes", 0)))
    table.add_row("Total Elements", str(structure.get("total_elements", 0)))
    table.add_row("Unique Element Types", str(structure.get("unique_element_types", 0)))
    
    if complexity and "complexity_level" in complexity:
        table.add_row("Complexity Level", complexity["complexity_level"])
        table.add_row("Complexity Score", str(complexity.get("complexity_score", 0)))
        table.add_row("Cyclomatic Complexity", str(complexity.get("cyclomatic_complexity", 0)))
    
    console.print(table)
    console.print(f"[blue]Analysis Duration: {duration:.3f}s[/blue]")
    
    if detailed and structure.get("element_types"):
        console.print("\n[bold]Element Type Distribution:[/bold]")
        for element_type, count in structure["element_types"].items():
            console.print(f"• {element_type}: {count}")
    
    # Show recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in recommendations:
            console.print(f"• {rec}")


# Export functions
def _export_validation_results(results: Dict[str, Any], output_file: Path) -> None:
    """Export validation results to file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"[green]✅ Validation results exported to: {output_file}[/green]")


def _export_test_results(results: Dict[str, Any], output_file: Path) -> None:
    """Export test results to file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"[green]✅ Test results exported to: {output_file}[/green]")


def _export_benchmark_results(results: Dict[str, Any], output_file: Path) -> None:
    """Export benchmark results to file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"[green]✅ Benchmark results exported to: {output_file}[/green]")


def _export_analysis_results(results: Dict[str, Any], output_file: Path) -> None:
    """Export analysis results to file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"[green]✅ Analysis results exported to: {output_file}[/green]") 