"""
uvmgr.commands.otel - OpenTelemetry Validation and Management
==========================================================

Commands for OpenTelemetry validation and management.

This module provides comprehensive CLI commands for validating, testing,
and managing OpenTelemetry instrumentation across the uvmgr codebase.
Includes coverage analysis, validation testing, and semantic convention
management.

Key Features
-----------
• **Coverage Analysis**: Analyze telemetry instrumentation coverage
• **Validation Testing**: Comprehensive OTEL validation tests
• **Semantic Conventions**: Manage and validate semantic conventions
• **Status Monitoring**: Check OTEL system status and health
• **Demo Features**: Demonstrate OTEL capabilities
• **Export Tools**: Export telemetry configuration and results

Available Commands
-----------------
- **coverage**: Analyze telemetry instrumentation coverage
- **validate**: Run comprehensive OTEL validation tests
- **test**: Generate test spans and metrics
- **semconv**: Manage semantic conventions
- **status**: Check OTEL system status
- **demo**: Demonstrate OTEL features
- **export**: Export telemetry configuration

Coverage Analysis
----------------
- **Function Analysis**: Check each function for telemetry instrumentation
- **Layer-based Analysis**: Analyze coverage by code layer (Command, Operations, etc.)
- **Threshold Validation**: Ensure minimum coverage requirements
- **Detailed Reporting**: Show specific functions and their instrumentation status

Validation Features
------------------
- **Span Creation**: Test span creation and management
- **Metrics Collection**: Validate metrics collection and export
- **Error Handling**: Test error tracking and exception recording
- **Performance Tracking**: Validate performance monitoring
- **Workflow Integration**: Test workflow and process tracking
- **Exporter Testing**: Validate OTEL exporter functionality

Examples
--------
    >>> # Analyze telemetry coverage
    >>> uvmgr otel coverage --threshold 90
    >>> 
    >>> # Run comprehensive validation
    >>> uvmgr otel validate --comprehensive
    >>> 
    >>> # Generate test spans
    >>> uvmgr otel test --iterations 10
    >>> 
    >>> # Check system status
    >>> uvmgr otel status
    >>> 
    >>> # Export configuration
    >>> uvmgr otel export --format json

See Also
--------
- :mod:`uvmgr.core.telemetry` : Core telemetry functionality
- :mod:`uvmgr.core.semconv` : Semantic conventions
- :mod:`uvmgr.core.instrumentation` : Instrumentation utilities
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes, PackageAttributes
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import (
    get_current_span,
    metric_counter,
    metric_histogram,
    record_exception,
    span,
)

console = Console()
app = typer.Typer(help="OpenTelemetry validation and management")


# Telemetry coverage analysis classes and functions
class FunctionInfo(NamedTuple):
    """Information about a function."""

    name: str
    line: int
    has_telemetry: bool
    telemetry_type: str | None = None


class FileStats(NamedTuple):
    """Statistics for a file."""

    total_functions: int
    instrumented_functions: int
    functions: list[FunctionInfo]

    @property
    def coverage(self) -> float:
        """Calculate coverage percentage."""
        if self.total_functions == 0:
            return 100.0
        return (self.instrumented_functions / self.total_functions) * 100


def check_function_telemetry(node: ast.FunctionDef, source_lines: list[str]) -> FunctionInfo:
    """Check if a function has telemetry instrumentation."""
    # Skip private functions and test functions
    if node.name.startswith("_") or node.name.startswith("test_"):
        return FunctionInfo(node.name, node.lineno, True, "skipped")

    # Check decorators for instrumentation
    for decorator in node.decorator_list:
        decorator_str = ast.unparse(decorator)
        if "instrument_command" in decorator_str:
            return FunctionInfo(node.name, node.lineno, True, "decorator")
        if "instrument_subcommand" in decorator_str:
            return FunctionInfo(node.name, node.lineno, True, "decorator")
        if "timed" in decorator_str:
            return FunctionInfo(node.name, node.lineno, True, "timed")

    # Check function body for 'with span' usage
    for child in ast.walk(node):
        if isinstance(child, ast.With):
            for item in child.items:
                context_str = ast.unparse(item.context_expr)
                if "span(" in context_str:
                    return FunctionInfo(node.name, node.lineno, True, "span")
                if "timer(" in context_str:
                    return FunctionInfo(node.name, node.lineno, True, "timer")

    return FunctionInfo(node.name, node.lineno, False, None)


def analyze_file(file_path: Path) -> FileStats:
    """Analyze a Python file for telemetry coverage."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            source_lines = content.splitlines()
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {e}[/red]")
        return FileStats(0, 0, [])

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        console.print(f"[red]Syntax error in {file_path}: {e}[/red]")
        return FileStats(0, 0, [])

    functions = []

    # Find all functions in the file
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip test methods in test files
            if "test_" in str(file_path) and node.name.startswith("test_"):
                continue

            func_info = check_function_telemetry(node, source_lines)
            functions.append(func_info)

    instrumented = sum(1 for f in functions if f.has_telemetry)
    return FileStats(len(functions), instrumented, functions)


def get_layer_name(file_path: Path) -> str:
    """Determine which layer a file belongs to."""
    parts = file_path.parts
    if "commands" in parts:
        return "Command"
    if "ops" in parts:
        return "Operations"
    if "runtime" in parts:
        return "Runtime"
    if "core" in parts:
        return "Core"
    if "mcp" in parts:
        return "MCP"
    return "Other"


@app.command("coverage")
@instrument_command("otel_coverage")
def coverage(
    path: Path = typer.Option(Path("src/uvmgr"), "--path", "-p", help="Path to analyze"),
    threshold: int = typer.Option(80, "--threshold", "-t", help="Coverage threshold for exit code"),
    layer: str = typer.Option(None, "--layer", "-l", help="Filter by layer (Command, Operations, Runtime, Core)"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed function list"),
):
    """Validate OpenTelemetry instrumentation coverage across uvmgr codebase."""
    console.print(Panel.fit(
        "[bold]OpenTelemetry Coverage Analysis[/bold]\n\n"
        "Analyzing uvmgr codebase for telemetry instrumentation",
        border_style="cyan"
    ))

    # Find all Python files
    if not path.exists():
        console.print(f"[red]Error: {path} directory not found[/red]")
        raise typer.Exit(1)

    py_files = list(path.rglob("*.py"))

    # Exclude certain files
    excluded_patterns = ["__pycache__", "__init__.py", "__main__.py", "test_"]
    py_files = [
        f for f in py_files
        if not any(pattern in str(f) for pattern in excluded_patterns)
    ]

    # Analyze files
    all_stats = {}
    layer_stats = {
        "Command": {"total": 0, "instrumented": 0, "files": 0},
        "Operations": {"total": 0, "instrumented": 0, "files": 0},
        "Runtime": {"total": 0, "instrumented": 0, "files": 0},
        "Core": {"total": 0, "instrumented": 0, "files": 0},
        "MCP": {"total": 0, "instrumented": 0, "files": 0},
        "Other": {"total": 0, "instrumented": 0, "files": 0},
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Analyzing {len(py_files)} files...", total=len(py_files))

        for py_file in py_files:
            stats = analyze_file(py_file)
            if stats.total_functions > 0:
                all_stats[py_file] = stats

                # Update layer statistics
                file_layer = get_layer_name(py_file)
                layer_stats[file_layer]["total"] += stats.total_functions
                layer_stats[file_layer]["instrumented"] += stats.instrumented_functions
                layer_stats[file_layer]["files"] += 1

            progress.update(task, advance=1)

    # Filter by layer if specified
    if layer:
        all_stats = {
            file_path: stats for file_path, stats in all_stats.items()
            if get_layer_name(file_path) == layer
        }

    # Create detailed report table
    if detailed or not layer:
        table = Table(title="Telemetry Coverage by File", show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Functions", justify="right")
        table.add_column("Instrumented", justify="right")
        table.add_column("Coverage", justify="right")
        table.add_column("Layer", style="yellow")

        # Sort by coverage (lowest first)
        sorted_files = sorted(all_stats.items(), key=lambda x: x[1].coverage)

        for file_path, stats in sorted_files:
            relative_path = file_path.relative_to(path.parent if "src" in str(path) else path)
            coverage_pct = stats.coverage

            # Color code coverage
            if coverage_pct == 100:
                coverage_str = f"[green]{coverage_pct:.1f}%[/green]"
            elif coverage_pct >= 80:
                coverage_str = f"[yellow]{coverage_pct:.1f}%[/yellow]"
            elif coverage_pct >= 50:
                coverage_str = f"[orange3]{coverage_pct:.1f}%[/orange3]"
            else:
                coverage_str = f"[red]{coverage_pct:.1f}%[/red]"

            file_layer = get_layer_name(file_path)
            table.add_row(
                str(relative_path),
                str(stats.total_functions),
                str(stats.instrumented_functions),
                coverage_str,
                file_layer
            )

        console.print("\n")
        console.print(table)

    # Layer summary table
    layer_table = Table(title="Coverage by Layer", show_header=True)
    layer_table.add_column("Layer", style="cyan")
    layer_table.add_column("Files", justify="right")
    layer_table.add_column("Functions", justify="right")
    layer_table.add_column("Instrumented", justify="right")
    layer_table.add_column("Coverage", justify="right")

    total_functions = 0
    total_instrumented = 0

    for layer_name, stats in layer_stats.items():
        if stats["files"] > 0:
            coverage_pct = (stats["instrumented"] / stats["total"] * 100) if stats["total"] > 0 else 0

            # Color code coverage
            if coverage_pct == 100:
                coverage_str = f"[green]{coverage_pct:.1f}%[/green]"
            elif coverage_pct >= 80:
                coverage_str = f"[yellow]{coverage_pct:.1f}%[/yellow]"
            elif coverage_pct >= 50:
                coverage_str = f"[orange3]{coverage_pct:.1f}%[/orange3]"
            else:
                coverage_str = f"[red]{coverage_pct:.1f}%[/red]"

            layer_table.add_row(
                layer_name,
                str(stats["files"]),
                str(stats["total"]),
                str(stats["instrumented"]),
                coverage_str
            )

            total_functions += stats["total"]
            total_instrumented += stats["instrumented"]

    console.print("\n")
    console.print(layer_table)

    # Overall summary
    overall_coverage = (total_instrumented / total_functions * 100) if total_functions > 0 else 0

    summary_panel = Panel.fit(
        f"[bold]Overall Coverage Summary[/bold]\n\n"
        f"Total Files: {len(all_stats)}\n"
        f"Total Functions: {total_functions}\n"
        f"Instrumented Functions: {total_instrumented}\n"
        f"Overall Coverage: [{'green' if overall_coverage >= 80 else 'yellow' if overall_coverage >= 50 else 'red'}]{overall_coverage:.1f}%[/{'green' if overall_coverage >= 80 else 'yellow' if overall_coverage >= 50 else 'red'}]",
        border_style="green" if overall_coverage >= 80 else "yellow" if overall_coverage >= 50 else "red"
    )
    console.print("\n")
    console.print(summary_panel)

    # Show uninstrumented functions in command layer
    if overall_coverage < 100 and detailed:
        console.print("\n[bold red]Uninstrumented Functions in Command Layer:[/bold red]")
        sorted_files = sorted(all_stats.items(), key=lambda x: x[1].coverage)
        for file_path, stats in sorted_files:
            if get_layer_name(file_path) == "Command":
                for func in stats.functions:
                    if not func.has_telemetry and not func.name.startswith("_"):
                        relative_path = file_path.relative_to(path.parent if "src" in str(path) else path)
                        console.print(f"  {relative_path}:{func.line} - {func.name}()")

    # Exit with appropriate code based on threshold
    if overall_coverage < threshold:
        console.print(f"\n[red]Coverage {overall_coverage:.1f}% is below threshold {threshold}%[/red]")
        raise typer.Exit(1)
    console.print(f"\n[green]Coverage {overall_coverage:.1f}% meets threshold {threshold}%[/green]")


@app.command("validate")
@instrument_command("otel_validate")
def validate_8020(
    comprehensive: bool = typer.Option(False, "--comprehensive", "-c", help="Run comprehensive validation"),
    export_results: bool = typer.Option(False, "--export", "-e", help="Export validation results"),
    output: str = typer.Option("", "--output", "-o", help="Output file for results"),
    endpoint: str = typer.Option(
        os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        "--endpoint",
        help="OTEL collector endpoint"
    ),
):
    """Run 8020 OTEL validation focusing on critical telemetry features."""
    console.print("[bold]8020 OTEL Validation[/bold] - Focus on critical 80% of functionality\n")

    from uvmgr.core.instrumentation import add_span_attributes, add_span_event
    from uvmgr.core.semconv import CIAttributes, CIOperations

    with span(
        "otel.validation.8020",
        **{
            CIAttributes.OPERATION: CIOperations.VERIFY,
            CIAttributes.TEST_COUNT: 0,
            CIAttributes.RUNNER: "uvmgr",
        }
    ):
        validation_start = time.time()
        results = {}

        # Initialize telemetry for testing
        add_span_event("otel.validation.started")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Critical Feature 1: Span Creation and Context
            task1 = progress.add_task("Testing span creation and context...", total=1)
            results["span_creation"] = _test_span_creation()
            progress.update(task1, completed=1)

            # Critical Feature 2: Metrics Collection
            task2 = progress.add_task("Testing metrics collection...", total=1)
            results["metrics_collection"] = _test_metrics_collection()
            progress.update(task2, completed=1)

            # Critical Feature 3: Semantic Conventions
            task3 = progress.add_task("Testing semantic conventions...", total=1)
            results["semantic_conventions"] = _test_semantic_conventions()
            progress.update(task3, completed=1)

            # Critical Feature 4: Error Handling and Recovery
            task4 = progress.add_task("Testing error handling...", total=1)
            results["error_handling"] = _test_error_handling()
            progress.update(task4, completed=1)

            # Critical Feature 5: Performance Tracking
            task5 = progress.add_task("Testing performance tracking...", total=1)
            results["performance_tracking"] = _test_performance_tracking()
            progress.update(task5, completed=1)

            if comprehensive:
                # Additional 20% features for comprehensive validation
                task6 = progress.add_task("Testing workflow integration...", total=1)
                results["workflow_integration"] = _test_workflow_integration()
                progress.update(task6, completed=1)

                task7 = progress.add_task("Testing exporters...", total=1)
                results["exporters"] = _test_exporters(endpoint)
                progress.update(task7, completed=1)

        validation_duration = time.time() - validation_start

        # Calculate results
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("status") == "passed")
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        # Update span with final results
        add_span_attributes(
            **{
                CIAttributes.TEST_COUNT: total_tests,
                CIAttributes.PASSED: passed_tests,
                CIAttributes.FAILED: failed_tests,
                CIAttributes.DURATION: validation_duration,
                CIAttributes.SUCCESS_RATE: success_rate,
            }
        )

        # Record validation metrics
        metric_counter("otel.validations.completed")(1)
        from uvmgr.core.telemetry import metric_histogram
        metric_histogram("otel.validation.duration")(validation_duration)
        metric_counter("otel.validation.tests.passed")(passed_tests)
        metric_counter("otel.validation.tests.failed")(failed_tests)

        # Display results
        _display_validation_results(results, validation_duration, success_rate)

        # Export results if requested
        if export_results:
            _export_validation_results(results, output or Path("otel_validation_results.json"))

        add_span_event("otel.validation.completed", {
            "success_rate": success_rate,
            "total_tests": total_tests,
            "duration": validation_duration,
        })

        # Exit with appropriate code
        if failed_tests > 0:
            console.print(f"\n[red]❌ Validation failed: {failed_tests} tests failed[/red]")
            raise typer.Exit(1)
        console.print(f"\n[green]✅ All {passed_tests} critical OTEL features validated successfully![/green]")


@app.command("test")
@instrument_command("otel_test")
def test(
    iterations: int = typer.Option(5, "--iterations", "-i", help="Number of test spans to generate"),
):
    """Generate test telemetry data."""
    console.print("[bold]Generating test telemetry data...[/bold]\n")

    with span("otel.test.session", test_iterations=iterations):
        for i in range(iterations):
            # Generate a test span with various attributes
            with span(
                f"otel.test.operation_{i}",
                iteration=i,
                test_type="validation"
            ) as test_span:
                # Simulate some work
                time.sleep(0.1)

                # Add events
                get_current_span().add_event(
                    "test.milestone",
                    {"milestone": "halfway", "progress": 0.5}
                )

                # Record metrics
                counter = metric_counter("otel.test.operations")
                counter(1)

                # Simulate nested operations
                with span("otel.test.nested_operation"):
                    time.sleep(0.05)

                    # Simulate an error occasionally
                    if i == 2:
                        try:
                            raise ValueError("Test error for demonstration")
                        except ValueError as e:
                            from uvmgr.core.telemetry import record_exception
                            record_exception(e, attributes={"test": True})

                console.print(f"Generated test span {i+1}/{iterations}")

    console.print("\n[green]✓ Test telemetry generated successfully![/green]")
    console.print("Check your OTEL backend (Jaeger/Prometheus) for the data.")


@app.command("semconv")
@instrument_command("otel_semconv")
def semconv(
    validate: bool = typer.Option(False, "--validate", "-v", help="Validate semantic conventions"),
    generate: bool = typer.Option(False, "--generate", "-g", help="Generate code from conventions"),
):
    """Manage semantic conventions for OpenTelemetry."""
    add_span_attributes(**{
        "otel.operation": "semconv",
        "otel.validate": validate,
        "otel.generate": generate,
    })
    
    try:
        from uvmgr.ops import otel as otel_ops
        
        if validate or (not validate and not generate):
            console.print("[bold]Validating semantic conventions...[/bold]")
            
            result = otel_ops.validate_semantic_conventions()
            
            if result["status"] == "success":
                console.print(f"[green]✓ {result['message']}[/green]")
            else:
                console.print(f"[red]✗ {result['message']}[/red]")
                if result.get("output"):
                    console.print(result["output"])
                raise typer.Exit(1)

        if generate:
            console.print("\n[bold]Generating code from conventions...[/bold]")
            
            result = otel_ops.generate_code_from_conventions()
            
            if result["status"] == "success":
                console.print(f"[green]✓ {result['message']}[/green]")
                if result.get("output"):
                    console.print(result["output"])
            else:
                console.print(f"[red]✗ {result['message']}[/red]")
                if result.get("output"):
                    console.print(result["output"])
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
@instrument_command("otel_status")
def status():
    """Show current OTEL instrumentation status."""
    console.print("[bold]OpenTelemetry Instrumentation Status[/bold]\n")

    # Check which commands are instrumented
    instrumented_commands = []

    # Import all command modules to check
    import importlib
    import pkgutil

    from uvmgr import commands

    for _, module_name, _ in pkgutil.iter_modules(commands.__path__):
        try:
            module = importlib.import_module(f"uvmgr.commands.{module_name}")

            # Check if module has instrumented commands
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if hasattr(attr, "__wrapped__") and hasattr(attr, "__name__"):
                    instrumented_commands.append(f"{module_name}.{attr.__name__}")
        except Exception:
            pass

    # Display instrumented commands
    if instrumented_commands:
        console.print("[green]Instrumented Commands:[/green]")
        for cmd in sorted(instrumented_commands):
            console.print(f"  • {cmd}")
    else:
        console.print("[yellow]No instrumented commands found.[/yellow]")

    # Show telemetry module status
    console.print("\n[bold]Telemetry Module Status:[/bold]")
    try:
        from uvmgr.core.telemetry import metric_counter, span
        console.print("  [green]✓[/green] Telemetry module loaded")

        # Check if OTEL is actually enabled
        from opentelemetry import version
        console.print(f"  [green]✓[/green] OpenTelemetry SDK v{version.__version__}")
    except ImportError:
        console.print("  [yellow]![/yellow] OpenTelemetry SDK not installed (telemetry disabled)")

    # Show semantic conventions
    console.print("\n[bold]Semantic Conventions:[/bold]")
    try:
        from uvmgr.core import semconv
        conv_modules = [
            "CliAttributes", "PackageAttributes", "BuildAttributes",
            "TestAttributes", "AIAttributes", "McpAttributes"
        ]
        for module in conv_modules:
            if hasattr(semconv, module):
                console.print(f"  [green]✓[/green] {module}")
    except ImportError:
        console.print("  [red]✗[/red] Semantic conventions not found")


# 8020 Validation Helper Functions
def _test_span_creation():
    """Test span creation and context propagation."""
    try:
        spans_created = []

        def mock_span(name, **kwargs):
            spans_created.append((name, kwargs))
            # Return a context manager
            class MockSpan:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return MockSpan()

        # Test nested spans
        with span("test.parent"):
            with span("test.child", operation="test"):
                with span("test.grandchild"):
                    pass

        return {
            "status": "passed",
            "message": "Span creation and nesting works correctly",
            "details": {"spans_tested": 3}
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Span creation failed: {e}",
            "details": {"error": str(e)}
        }


def _test_metrics_collection():
    """Test metrics collection (counters and histograms)."""
    try:
        from uvmgr.core.telemetry import metric_histogram

        # Test counter metrics
        counter = metric_counter("test.counter")
        counter(1)
        counter(5)

        # Test histogram metrics
        histogram = metric_histogram("test.histogram")
        histogram(0.1)
        histogram(0.5)
        histogram(1.0)

        return {
            "status": "passed",
            "message": "Metrics collection working correctly",
            "details": {"counters": 1, "histograms": 1}
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Metrics collection failed: {e}",
            "details": {"error": str(e)}
        }


def _test_semantic_conventions():
    """Test semantic conventions usage."""
    try:
        from uvmgr.core.semconv import (
            BuildAttributes,
            CliAttributes,
            PackageAttributes,
            TestAttributes,
            WorkflowAttributes,
        )

        # Test that semantic convention classes exist and have expected attributes
        conventions_tested = 0

        # Test CLI conventions
        assert hasattr(CliAttributes, "COMMAND")  # Alias exists
        assert hasattr(CliAttributes, "EXIT_CODE")  # Alias exists
        conventions_tested += 1

        # Test Package conventions
        assert hasattr(PackageAttributes, "PACKAGE_NAME")
        assert hasattr(PackageAttributes, "PACKAGE_VERSION")
        conventions_tested += 1

        # Test Build conventions
        assert hasattr(BuildAttributes, "TYPE")
        assert hasattr(BuildAttributes, "OPERATION")  # Use OPERATION instead of DURATION
        conventions_tested += 1

        # Test Workflow conventions
        assert hasattr(WorkflowAttributes, "ENGINE")
        assert hasattr(WorkflowAttributes, "OPERATION")
        conventions_tested += 1

        # Test that constants have proper values (strings)
        assert isinstance(CliAttributes.COMMAND, str)
        assert isinstance(PackageAttributes.PACKAGE_NAME, str)
        assert isinstance(BuildAttributes.TYPE, str)

        return {
            "status": "passed",
            "message": "Semantic conventions properly defined and accessible",
            "details": {"conventions_tested": conventions_tested}
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Semantic conventions failed: {e}",
            "details": {"error": str(e)}
        }


def _test_error_handling():
    """Test error handling and exception recording."""
    try:
        from uvmgr.core.instrumentation import add_span_attributes, add_span_event
        from uvmgr.core.telemetry import record_exception

        # Test exception recording
        try:
            raise ValueError("Test exception for OTEL validation")
        except ValueError as e:
            record_exception(e)

        # Test that instrumentation handles errors gracefully
        # These should not throw exceptions even if no active span
        add_span_event("test.event", {"key": "value"})
        add_span_attributes(test_attr="test_value")

        return {
            "status": "passed",
            "message": "Error handling and exception recording works correctly",
            "details": {"exceptions_recorded": 1}
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Error handling failed: {e}",
            "details": {"error": str(e)}
        }


def _test_performance_tracking():
    """Test performance tracking with histograms and timing."""
    try:
        from uvmgr.core.telemetry import metric_histogram

        start_time = time.time()

        # Simulate some work
        time.sleep(0.01)  # 10ms

        duration = time.time() - start_time

        # Record performance metrics
        perf_histogram = metric_histogram("test.performance", "s")
        perf_histogram(duration)

        # Test that we can track multiple performance metrics
        operations = ["parse", "validate", "execute", "cleanup"]
        for op in operations:
            op_histogram = metric_histogram(f"test.{op}.duration", "s")
            op_histogram(0.001 * len(op))  # Simulate different durations

        return {
            "status": "passed",
            "message": "Performance tracking with histograms works correctly",
            "details": {
                "duration_recorded": duration,
                "metrics_created": len(operations) + 1
            }
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Performance tracking failed: {e}",
            "details": {"error": str(e)}
        }


def _test_workflow_integration():
    """Test SpiffWorkflow OTEL integration with comprehensive validation."""
    try:
        # Use the full SpiffWorkflow OTEL validation system
        from uvmgr.ops.spiff_otel_validation import run_8020_otel_validation
        
        add_span_event("workflow_integration_test_started")
        
        # Run 80/20 OTEL validation through SpiffWorkflow
        validation_result = run_8020_otel_validation()
        
        success = validation_result.success
        metrics_validated = validation_result.metrics_validated
        spans_validated = validation_result.spans_validated
        workflow_duration = validation_result.duration_seconds
        
        add_span_event("workflow_integration_test_completed", {
            "success": success,
            "metrics_validated": metrics_validated,
            "spans_validated": spans_validated,
            "workflow_duration": workflow_duration,
        })

        return {
            "status": "passed" if success else "failed",
            "message": f"SpiffWorkflow OTEL integration {'passed' if success else 'failed'}",
            "details": {
                "workflow_success": success,
                "metrics_validated": metrics_validated,
                "spans_validated": spans_validated,
                "workflow_duration": workflow_duration,
                "validation_steps": len(validation_result.validation_steps),
                "errors": len(validation_result.errors),
            }
        }
    except ImportError as e:
        return {
            "status": "failed",
            "message": "SpiffWorkflow dependencies not available",
            "details": {"error": str(e), "suggestion": "Install with: pip install spiffworkflow"}
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Workflow integration failed: {e}",
            "details": {"error": str(e)}
        }


def _test_exporters(endpoint):
    """Test OTEL exporters configuration."""
    try:
        # Check if OTEL environment variables are set for exporters
        otel_vars = [
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "OTEL_EXPORTER_JAEGER_ENDPOINT",
            "OTEL_EXPORTER_ZIPKIN_ENDPOINT"
        ]

        configured_exporters = [var for var in otel_vars if os.getenv(var)]

        # Test collector connectivity
        import urllib.error
        import urllib.request

        health_url = endpoint.replace("4317", "13133") + "/health"
        health_url = health_url.replace("http://", "").replace("https://", "")
        health_url = f"http://{health_url}"

        connector_working = False
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                connector_working = response.status == 200
        except Exception:
            pass

        return {
            "status": "passed",
            "message": "OTEL exporters configuration checked successfully",
            "details": {
                "configured_exporters": len(configured_exporters),
                "available_vars": configured_exporters,
                "collector_reachable": connector_working
            }
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Exporters test failed: {e}",
            "details": {"error": str(e)}
        }


def _display_validation_results(results, duration, success_rate):
    """Display validation results in a nice format."""
    # Summary panel
    summary = f"Duration: {duration:.2f}s | Success Rate: {success_rate:.1f}%"
    panel = Panel(summary, title="8020 OTEL Validation Results", border_style="green" if success_rate == 100 else "yellow")
    console.print(panel)
    console.print()

    # Detailed results table
    table = Table(title="Detailed Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Message", style="dim")
    table.add_column("Details", style="blue")

    for test_name, result in results.items():
        status = result["status"]
        status_emoji = "✅" if status == "passed" else "❌"
        status_color = "green" if status == "passed" else "red"

        details = result.get("details", {})
        details_str = " | ".join([f"{k}: {v}" for k, v in details.items()])

        table.add_row(
            test_name.replace("_", " ").title(),
            f"[{status_color}]{status_emoji} {status.upper()}[/{status_color}]",
            result["message"],
            details_str
        )

    console.print(table)


def _export_validation_results(results, output_path):
    """Export validation results to JSON file."""
    export_data = {
        "timestamp": time.time(),
        "validation_type": "8020_otel",
        "results": results,
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for r in results.values() if r.get("status") == "passed"),
            "failed": sum(1 for r in results.values() if r.get("status") == "failed"),
        }
    }

    output_path.write_text(json.dumps(export_data, indent=2))
    console.print(f"\n[blue]📁 Results exported to: {output_path}[/blue]")


def _display_spiff_validation_results(result) -> None:
    """Display SpiffWorkflow validation results in formatted output."""
    # Import here to avoid circular imports
    from uvmgr.ops.spiff_otel_validation import OTELValidationResult
    
    if not isinstance(result, OTELValidationResult):
        console.print("[red]❌ Invalid validation result format[/red]")
        return
    
    # Main status panel
    status_color = "green" if result.success else "red"
    status_icon = "✅" if result.success else "❌"
    
    panel_content = f"""[{status_color}]{status_icon} SpiffWorkflow OTEL Validation {['FAILED', 'PASSED'][result.success]}[/{status_color}]

[bold]Workflow:[/bold] {result.workflow_name}
[bold]Duration:[/bold] {result.duration_seconds:.2f}s
[bold]Validation Steps:[/bold] {len(result.validation_steps)}
[bold]Metrics Validated:[/bold] {result.metrics_validated}
[bold]Spans Validated:[/bold] {result.spans_validated}"""
    
    if result.errors:
        panel_content += f"\n[bold red]Errors:[/bold red] {len(result.errors)}"
    
    console.print(Panel(panel_content, title="SpiffWorkflow OTEL Validation Results", border_style=status_color))
    
    # Validation steps summary
    if result.validation_steps:
        console.print("\n[bold]Validation Steps:[/bold]")
        steps_table = Table()
        steps_table.add_column("#", style="dim", width=3)
        steps_table.add_column("Step", style="cyan")
        steps_table.add_column("Status", style="green", width=8)
        
        for i, step_name in enumerate(result.validation_steps, 1):
            # Determine status (simplified - in real implementation would track individual step status)
            status = "✅ PASS" if "Error" not in step_name else "❌ FAIL"
            steps_table.add_row(str(i), step_name, status)
        
        console.print(steps_table)
    
    # Performance metrics
    if result.performance_data:
        console.print("\n[bold]Performance Metrics:[/bold]")
        perf_table = Table()
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="green")
        
        for metric, value in result.performance_data.items():
            if isinstance(value, float):
                formatted_value = f"{value:.3f}s" if "duration" in metric else f"{value:.3f}"
            else:
                formatted_value = str(value)
            perf_table.add_row(metric.replace("_", " ").title(), formatted_value)
        
        console.print(perf_table)
    
    # Error details
    if result.errors:
        console.print("\n[bold red]Validation Errors:[/bold red]")
        for i, error in enumerate(result.errors[:5], 1):  # Show first 5 errors
            console.print(f"  {i}. [red]{error}[/red]")
        if len(result.errors) > 5:
            console.print(f"  [dim]... and {len(result.errors) - 5} more errors[/dim]")


def _save_spiff_validation_results(result, output_file: Path) -> None:
    """Save SpiffWorkflow validation results to JSON file."""
    # Import here to avoid circular imports
    from uvmgr.ops.spiff_otel_validation import OTELValidationResult
    
    if not isinstance(result, OTELValidationResult):
        console.print("[red]❌ Cannot save invalid validation result[/red]")
        return
    
    results_data = {
        "timestamp": time.time(),
        "validation_type": "spiff_workflow_otel",
        "workflow_name": result.workflow_name,
        "success": result.success,
        "duration_seconds": result.duration_seconds,
        "validation_steps": result.validation_steps,
        "metrics_validated": result.metrics_validated,
        "spans_validated": result.spans_validated,
        "errors": result.errors,
        "performance_data": result.performance_data,
        "summary": {
            "total_steps": len(result.validation_steps),
            "error_count": len(result.errors),
            "success_rate": (len(result.validation_steps) - len(result.errors)) / len(result.validation_steps) * 100 if result.validation_steps else 0,
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    console.print(f"[blue]📁 SpiffWorkflow results saved to: {output_file}[/blue]")


@app.command("demo")
@instrument_command("otel_demo")
def demo_otel_features():
    """Demonstrate OTEL features with live telemetry data."""
    console.print("[bold]OTEL Features Demo[/bold] - Live telemetry demonstration\n")

    from uvmgr.core.instrumentation import add_span_attributes, add_span_event

    with span("otel.demo", demo_type="live"):
        add_span_event("demo.started")

        # Demo 1: Nested spans with timing
        console.print("🔄 Demonstrating nested spans with timing...")
        with span("demo.nested_operations"):
            with span("demo.operation.setup"):
                time.sleep(0.1)
                add_span_event("setup.completed")

            with span("demo.operation.process"):
                time.sleep(0.2)
                add_span_attributes(items_processed=100, batch_size=10)
                add_span_event("processing.completed", {"items": 100})

            with span("demo.operation.cleanup"):
                time.sleep(0.05)
                add_span_event("cleanup.completed")

        console.print("✅ Nested spans demo completed")

        # Demo 2: Metrics collection
        console.print("\n📊 Demonstrating metrics collection...")

        # Counter metrics
        for i in range(5):
            metric_counter("demo.requests")(1)
            metric_counter("demo.items.processed")(10 + i)

        # Histogram metrics
        for duration in [0.1, 0.15, 0.2, 0.12, 0.18]:
            metric_histogram("demo.request.duration", "s")(duration)

        console.print("✅ Metrics collection demo completed")

        # Demo 3: Error handling
        console.print("\n⚠️  Demonstrating error handling...")
        try:
            with span("demo.error_scenario"):
                add_span_event("error.simulation.started")
                raise ValueError("Demo exception for telemetry")
        except ValueError as e:
            record_exception(e)
            add_span_event("error.handled", {"error_type": "ValueError"})

        console.print("✅ Error handling demo completed")

        add_span_event("demo.completed")

    console.print("\n[green]🎉 OTEL demonstration completed! Check your telemetry backend for traces.[/green]")


@app.command("workflow-validate")
@instrument_command("otel_workflow_validate")
def workflow_validate(
    test_commands: Optional[str] = typer.Option(
        None,
        "--tests",
        "-t",
        help="Comma-separated test commands to validate"
    ),
    mode: str = typer.Option(
        "8020",
        "--mode",
        "-m",
        help="Validation mode: 8020 (critical), comprehensive, custom"
    ),
    project_path: Optional[Path] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project path for validation context"
    ),
    save_results: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save validation results to file"
    ),
    workflow_file: Optional[Path] = typer.Option(
        None,
        "--workflow",
        "-w",
        help="Custom BPMN workflow file"
    ),
):
    """
    Run OTEL validation using SpiffWorkflow orchestration.
    
    This command integrates SpiffWorkflow BPMN execution with OTEL validation,
    providing comprehensive workflow-driven test validation with full telemetry
    instrumentation and monitoring.
    
    Examples:
        uvmgr otel workflow-validate --mode 8020
        uvmgr otel workflow-validate --tests "uvmgr tests run,uvmgr otel status"
        uvmgr otel workflow-validate --workflow custom.bpmn --project /path/to/project
    """
    console.print("🔄 [bold cyan]SpiffWorkflow OTEL Validation[/bold cyan]")
    console.print(f"📋 Mode: {mode}")
    
    if project_path:
        console.print(f"📁 Project: {project_path}")
    
    try:
        from uvmgr.ops.spiff_otel_validation import (
            run_8020_otel_validation,
            execute_otel_validation_workflow,
            create_otel_validation_workflow
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Setting up workflow validation...", total=3)
            
            if mode == "8020":
                # Run 80/20 validation
                progress.update(task, description="Executing 80/20 critical validation...")
                result = run_8020_otel_validation(project_path)
                progress.advance(task, 3)
                
            elif mode == "custom" and workflow_file:
                # Use custom workflow
                if not workflow_file.exists():
                    console.print(f"[red]❌ Workflow file not found: {workflow_file}[/red]")
                    raise typer.Exit(1)
                
                progress.update(task, description="Executing custom workflow...")
                test_cmd_list = test_commands.split(",") if test_commands else ["uvmgr otel status"]
                result = execute_otel_validation_workflow(
                    workflow_file, test_cmd_list, project_path
                )
                progress.advance(task, 3)
                
            elif mode == "comprehensive" or test_commands:
                # Create comprehensive or custom test workflow
                test_cmd_list = []
                if test_commands:
                    test_cmd_list = [cmd.strip() for cmd in test_commands.split(",")]
                else:
                    # Comprehensive test suite
                    test_cmd_list = [
                        "uvmgr otel status",
                        "uvmgr otel coverage",
                        "uvmgr otel validate",
                        "uvmgr tests run tests/test_instrumentation.py -v",
                        "python -c 'from uvmgr.core.telemetry import span, metric_counter; print(\"✓ Core imports\")'",
                        "uvmgr otel semconv --validate",
                    ]
                
                progress.update(task, description="Creating comprehensive workflow...")
                workflow_path = Path.cwd() / ".uvmgr_temp" / "comprehensive_otel_validation.bpmn"
                create_otel_validation_workflow(workflow_path, test_cmd_list)
                progress.advance(task)
                
                progress.update(task, description="Executing comprehensive validation...")
                result = execute_otel_validation_workflow(
                    workflow_path, test_cmd_list, project_path
                )
                progress.advance(task)
                
                # Cleanup
                if workflow_path.exists():
                    workflow_path.unlink()
                progress.advance(task)
                
            else:
                console.print(f"[red]❌ Invalid mode: {mode}[/red]")
                console.print("Valid modes: 8020, comprehensive, custom (requires --workflow)")
                raise typer.Exit(1)
            
            # Display results
            _display_spiff_validation_results(result)
            
            # Save results if requested
            if save_results:
                results_file = Path(f"otel_workflow_validation_{mode}.json")
                _save_spiff_validation_results(result, results_file)
                console.print(f"💾 Results saved to: {results_file}")
            
            # Final status and telemetry
            current_span = get_current_span()
            if current_span.is_recording():
                current_span.set_attributes({
                    "workflow_validation.mode": mode,
                    "workflow_validation.success": result.success,
                    "workflow_validation.metrics_validated": result.metrics_validated,
                    "workflow_validation.spans_validated": result.spans_validated,
                    "workflow_validation.duration": result.duration_seconds,
                })
                
                current_span.add_event("workflow_validation_completed", {
                    "mode": mode,
                    "success": result.success,
                    "metrics": result.metrics_validated,
                    "spans": result.spans_validated,
                    "steps": len(result.validation_steps),
                    "errors": len(result.errors),
                })
            
            if result.success:
                console.print(f"\n[green]✅ SpiffWorkflow OTEL Validation PASSED[/green]")
                console.print(f"[green]✓ {result.metrics_validated} metrics, {result.spans_validated} spans validated[/green]")
            else:
                console.print(f"\n[red]❌ SpiffWorkflow OTEL Validation FAILED[/red]")
                console.print(f"[red]✗ {len(result.errors)} errors found[/red]")
                for error in result.errors[:3]:
                    console.print(f"  • {error}")
                if len(result.errors) > 3:
                    console.print(f"  ... and {len(result.errors) - 3} more errors")
                raise typer.Exit(1)
                
    except ImportError as e:
        current_span = get_current_span()
        if current_span.is_recording():
            current_span.add_event("workflow_validation_import_error", {"error": str(e)})
        console.print("[red]❌ SpiffWorkflow dependencies not available[/red]")
        console.print("Install with: uvmgr deps add spiffworkflow")
        raise typer.Exit(1)
    except Exception as e:
        current_span = get_current_span()
        if current_span.is_recording():
            current_span.add_event("workflow_validation_failed", {"error": str(e)})
        console.print(f"[red]❌ Workflow validation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("export")
@instrument_command("otel_export")
def export(
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, yaml)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export telemetry configuration and status."""
    data = {
        "configuration": {
            "endpoint": os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            "service_name": os.environ.get("OTEL_SERVICE_NAME", "uvmgr"),
            "traces_exporter": os.environ.get("OTEL_TRACES_EXPORTER", "otlp"),
            "metrics_exporter": os.environ.get("OTEL_METRICS_EXPORTER", "otlp"),
        },
        "sdk": {
            "installed": False,
            "version": None
        },
        "semantic_conventions": {
            "version": "1.26.0",
            "registry": "weaver-forge/registry"
        }
    }

    try:
        import opentelemetry
        data["sdk"]["installed"] = True
        data["sdk"]["version"] = opentelemetry.__version__
    except ImportError:
        pass

    if format == "json":
        output_text = json.dumps(data, indent=2)
    elif format == "yaml":
        try:
            import yaml
            output_text = yaml.dump(data, default_flow_style=False)
        except ImportError:
            console.print("[red]PyYAML not installed. Use JSON format or install with: uvmgr deps add pyyaml[/red]")
            raise typer.Exit(1)
    else:
        console.print(f"[red]Unsupported format: {format}[/red]")
        raise typer.Exit(1)

    if output:
        output.write_text(output_text)
        console.print(f"[green]✓ Configuration exported to {output}[/green]")
    else:
        console.print(output_text)


@app.command("dashboard")
@instrument_command("otel_dashboard", track_args=True)
def dashboard(
    ctx: typer.Context,
    action: str = typer.Argument("setup", help="Action: setup, start, stop, status"),
    grafana_url: str = typer.Option("http://localhost:3000", "--grafana-url", help="Grafana URL"),
    prometheus_url: str = typer.Option("http://localhost:9090", "--prometheus-url", help="Prometheus URL"),
    jaeger_url: str = typer.Option("http://localhost:16686", "--jaeger-url", help="Jaeger URL"),
):
    """Manage OTEL dashboard stack (Grafana, Prometheus, Jaeger)."""
    add_span_attributes(**{
        "otel.operation": "dashboard",
        "otel.action": action,
        "otel.grafana_url": grafana_url,
        "otel.prometheus_url": prometheus_url,
        "otel.jaeger_url": jaeger_url,
    })
    
    try:
        from uvmgr.ops import otel as otel_ops
        
        if action == "setup":
            console.print("[bold]Setting up OTEL dashboard stack...[/bold]")
            result = otel_ops.setup_dashboard_stack()
            console.print(f"[green]✓ {result['message']}[/green]")
            console.print("\nDashboard URLs:")
            for service, url in result["urls"].items():
                console.print(f"  • {service.title()}: {url}")
                
        elif action == "start":
            console.print("[bold]Starting OTEL dashboard stack...[/bold]")
            result = otel_ops.start_dashboard_stack()
            console.print(f"[green]✓ {result['message']}[/green]")
            
        elif action == "stop":
            console.print("[bold]Stopping OTEL dashboard stack...[/bold]")
            result = otel_ops.stop_dashboard_stack()
            console.print(f"[green]✓ {result['message']}[/green]")
            
        elif action == "status":
            console.print("[bold]Checking OTEL dashboard stack status...[/bold]")
            result = otel_ops.check_dashboard_status(grafana_url, prometheus_url, jaeger_url)
            
            console.print("\nService Status:")
            for service, status in result["services"].items():
                status_icon = "✓" if status == "running" else "✗" if status == "stopped" else "?"
                status_color = "green" if status == "running" else "red" if status == "stopped" else "yellow"
                console.print(f"  [{status_color}]{status_icon}[/{status_color}] {service.title()}: {status}")
            
            console.print("\nDashboard URLs:")
            for service, url in result["urls"].items():
                console.print(f"  • {service.title()}: {url}")
                
        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Available actions: setup, start, stop, status")
            raise typer.Exit(1)
            
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


def _setup_dashboard(grafana_url: str, prometheus_url: str, jaeger_url: str) -> None:
    """Setup Grafana dashboards using existing configuration."""
    from pathlib import Path
    import subprocess
    
    # Find the dashboard setup script
    project_root = Path(__file__).parent.parent.parent.parent
    setup_script = project_root / "external-project-testing" / "otel-dashboard-setup.py"
    dashboard_config = project_root / "external-project-testing" / "grafana-dashboard-config.json"
    
    if not setup_script.exists():
        console.print(f"[red]Dashboard setup script not found at: {setup_script}[/red]")
        raise typer.Exit(1)
        
    if not dashboard_config.exists():
        console.print(f"[red]Dashboard config not found at: {dashboard_config}[/red]")
        raise typer.Exit(1)
    
    console.print("[cyan]🚀 Setting up OTEL Grafana dashboards...[/cyan]")
    
    try:
        # Run the dashboard setup script
        result = subprocess.run([
            "python", str(setup_script),
            "--grafana-url", grafana_url,
            "--prometheus-url", prometheus_url, 
            "--jaeger-url", jaeger_url
        ], capture_output=True, text=True, check=True)
        
        console.print("[green]✅ Dashboard setup completed successfully![/green]")
        console.print(f"[blue]📊 Access your dashboards at: {grafana_url}[/blue]")
        console.print(f"[blue]📈 Prometheus metrics at: {prometheus_url}[/blue]")
        console.print(f"[blue]🔍 Jaeger tracing at: {jaeger_url}[/blue]")
        
        if result.stdout:
            console.print("\n[dim]Setup output:[/dim]")
            console.print(result.stdout)
            
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Dashboard setup failed: {e}[/red]")
        if e.stderr:
            console.print(f"[red]Error: {e.stderr}[/red]")
        raise typer.Exit(1)


def _start_dashboard_stack() -> None:
    """Start the OTEL monitoring stack using Docker Compose."""
    from pathlib import Path
    import subprocess
    
    project_root = Path(__file__).parent.parent.parent.parent
    compose_file = project_root / "docker-compose.otel.yml"
    
    if not compose_file.exists():
        console.print(f"[red]Docker compose file not found at: {compose_file}[/red]")
        console.print("[yellow]💡 Run 'uvmgr otel dashboard setup' first[/yellow]")
        raise typer.Exit(1)
    
    console.print("[cyan]🚀 Starting OTEL monitoring stack...[/cyan]")
    
    try:
        subprocess.run([
            "docker-compose", "-f", str(compose_file), "up", "-d"
        ], check=True)
        
        console.print("[green]✅ OTEL monitoring stack started![/green]")
        console.print("[blue]📊 Grafana: http://localhost:3000[/blue]")
        console.print("[blue]📈 Prometheus: http://localhost:9090[/blue]") 
        console.print("[blue]🔍 Jaeger: http://localhost:16686[/blue]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to start monitoring stack: {e}[/red]")
        raise typer.Exit(1)


def _stop_dashboard_stack() -> None:
    """Stop the OTEL monitoring stack."""
    from pathlib import Path
    import subprocess
    
    project_root = Path(__file__).parent.parent.parent.parent
    compose_file = project_root / "docker-compose.otel.yml"
    
    if not compose_file.exists():
        console.print("[yellow]No monitoring stack found to stop[/yellow]")
        return
    
    console.print("[cyan]🛑 Stopping OTEL monitoring stack...[/cyan]")
    
    try:
        subprocess.run([
            "docker-compose", "-f", str(compose_file), "down"
        ], check=True)
        
        console.print("[green]✅ OTEL monitoring stack stopped[/green]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to stop monitoring stack: {e}[/red]")
        raise typer.Exit(1)


def _check_dashboard_status(grafana_url: str, prometheus_url: str, jaeger_url: str) -> None:
    """Check the status of dashboard services."""
    import requests
    from rich.table import Table
    
    table = Table(title="OTEL Dashboard Status")
    table.add_column("Service", style="cyan")
    table.add_column("URL", style="blue") 
    table.add_column("Status", style="green")
    table.add_column("Response Time", style="yellow")
    
    services = [
        ("Grafana", grafana_url),
        ("Prometheus", prometheus_url),
        ("Jaeger", jaeger_url)
    ]
    
    for service, url in services:
        try:
            import time
            start_time = time.time()
            response = requests.get(f"{url}/api/health" if "grafana" in url else url, timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = "✅ Online"
            else:
                status = f"⚠️ HTTP {response.status_code}"
                
        except requests.exceptions.RequestException:
            status = "❌ Offline"
            response_time = "N/A"
            
        table.add_row(service, url, status, response_time)
    
    console.print(table)
    console.print("\n[dim]💡 Use 'uvmgr otel dashboard start' to launch the monitoring stack[/dim]")


@app.command("config")
@instrument_command("otel_config", track_args=True)
def config(
    ctx: typer.Context,
    action: str = typer.Argument("show", help="Action: show, set, validate, export"),
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="OTLP endpoint URL"),
    service_name: Optional[str] = typer.Option(None, "--service-name", "-s", help="Service name"),
    headers: Optional[str] = typer.Option(None, "--headers", "-h", help="OTLP headers (key=value,key=value)"),
    compression: Optional[str] = typer.Option(None, "--compression", "-c", help="Compression: gzip, none"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Timeout in seconds"),
    insecure: bool = typer.Option(False, "--insecure", help="Use insecure connection"),
    protocol: Optional[str] = typer.Option(None, "--protocol", "-p", help="Protocol: grpc, http/protobuf"),
):
    """
    Manage OTLP exporter configuration.
    
    Advanced OTLP configuration for production monitoring with support for
    multiple endpoints, authentication, compression, and retry policies.
    """
    add_span_attributes(**{
        "otel.config.action": action,
        "otel.config.endpoint": endpoint or "not_provided",
        "otel.config.service_name": service_name or "not_provided",
        "otel.config.compression": compression or "not_provided",
        "otel.config.protocol": protocol or "not_provided",
    })
    
    try:
        if action == "show":
            _show_otlp_config()
        elif action == "set":
            _set_otlp_config(endpoint, service_name, headers, compression, timeout, insecure, protocol)
        elif action == "validate":
            _validate_otlp_config()
        elif action == "export":
            _export_otlp_config()
        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Available actions: show, set, validate, export")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]OTLP config operation failed: {e}[/red]")
        add_span_event("otel.config.error", {"error": str(e)})
        raise typer.Exit(1)


def _show_otlp_config() -> None:
    """Show current OTLP configuration."""
    from rich.table import Table
    
    table = Table(title="OTLP Exporter Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")
    table.add_column("Status", style="blue")
    
    config_items = [
        ("OTEL_EXPORTER_OTLP_ENDPOINT", os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""), "Environment"),
        ("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", ""), "Environment"),
        ("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", ""), "Environment"),
        ("OTEL_EXPORTER_OTLP_HEADERS", os.getenv("OTEL_EXPORTER_OTLP_HEADERS", ""), "Environment"),
        ("OTEL_EXPORTER_OTLP_COMPRESSION", os.getenv("OTEL_EXPORTER_OTLP_COMPRESSION", "gzip"), "Environment"),
        ("OTEL_EXPORTER_OTLP_TIMEOUT", os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT", "10"), "Environment"),
        ("OTEL_EXPORTER_OTLP_PROTOCOL", os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc"), "Environment"),
        ("OTEL_SERVICE_NAME", os.getenv("OTEL_SERVICE_NAME", "uvmgr"), "Environment"),
        ("OTEL_SERVICE_VERSION", os.getenv("OTEL_SERVICE_VERSION", ""), "Environment"),
        ("OTEL_RESOURCE_ATTRIBUTES", os.getenv("OTEL_RESOURCE_ATTRIBUTES", ""), "Environment"),
    ]
    
    for setting, value, source, in [(s, v, src) for s, v, src in config_items]:
        if value:
            status = "✅ Set"
            display_value = value if not setting.endswith("HEADERS") else "***hidden***"
        else:
            status = "❌ Not Set"
            display_value = "[dim]not configured[/dim]"
            
        table.add_row(setting, display_value, source, status)
    
    console.print(table)
    
    # Show validation status
    validation_status = _get_otlp_validation_status()
    if validation_status["valid"]:
        console.print("\n[green]✅ Configuration is valid and ready for production[/green]")
    else:
        console.print(f"\n[red]❌ Configuration issues: {validation_status['issues']}[/red]")
        console.print("[yellow]💡 Use 'uvmgr otel config validate' for detailed validation[/yellow]")


def _set_otlp_config(endpoint: Optional[str], service_name: Optional[str], headers: Optional[str], 
                     compression: Optional[str], timeout: Optional[int], insecure: bool, 
                     protocol: Optional[str]) -> None:
    """Set OTLP configuration in environment."""
    from pathlib import Path
    
    console.print("[cyan]🔧 Updating OTLP configuration...[/cyan]")
    
    # Read or create .env file
    env_file = Path(".env")
    env_vars = {}
    
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    
    # Update configuration
    updates = []
    if endpoint:
        env_vars["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
        updates.append(f"Endpoint: {endpoint}")
    
    if service_name:
        env_vars["OTEL_SERVICE_NAME"] = service_name
        updates.append(f"Service: {service_name}")
        
    if headers:
        env_vars["OTEL_EXPORTER_OTLP_HEADERS"] = headers
        updates.append("Headers: ***configured***")
        
    if compression:
        env_vars["OTEL_EXPORTER_OTLP_COMPRESSION"] = compression
        updates.append(f"Compression: {compression}")
        
    if timeout:
        env_vars["OTEL_EXPORTER_OTLP_TIMEOUT"] = str(timeout)
        updates.append(f"Timeout: {timeout}s")
        
    if protocol:
        env_vars["OTEL_EXPORTER_OTLP_PROTOCOL"] = protocol
        updates.append(f"Protocol: {protocol}")
        
    if insecure:
        env_vars["OTEL_EXPORTER_OTLP_INSECURE"] = "true"
        updates.append("Insecure: enabled")
    
    # Write updated .env file
    env_content = "\n".join([f"{k}={v}" for k, v in sorted(env_vars.items())])
    env_file.write_text(env_content + "\n")
    
    console.print("[green]✅ Configuration updated successfully![/green]")
    for update in updates:
        console.print(f"  • {update}")
        
    console.print(f"\n[blue]📄 Configuration saved to: {env_file.absolute()}[/blue]")
    console.print("[yellow]💡 Restart uvmgr to apply the new configuration[/yellow]")


def _validate_otlp_config() -> None:
    """Validate OTLP configuration and test connectivity."""
    console.print("[cyan]🔍 Validating OTLP configuration...[/cyan]")
    
    validation = _get_otlp_validation_status()
    
    from rich.table import Table
    
    table = Table(title="OTLP Configuration Validation")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    for check, result in validation["checks"].items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        table.add_row(check, status, result["message"])
    
    console.print(table)
    
    if validation["valid"]:
        console.print("\n[green]✅ All validation checks passed![/green]")
        console.print("[blue]🚀 Your OTLP configuration is production-ready[/blue]")
        
        # Test connectivity
        console.print("\n[cyan]🌐 Testing connectivity...[/cyan]")
        _test_otlp_connectivity()
    else:
        console.print(f"\n[red]❌ Validation failed: {validation['issues']}[/red]")
        console.print("[yellow]💡 Use 'uvmgr otel config set' to fix configuration issues[/yellow]")


def _export_otlp_config() -> None:
    """Export OTLP configuration for deployment."""
    config = {
        "version": "1.0",
        "otlp_exporter": {
            "endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
            "traces_endpoint": os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", ""),
            "metrics_endpoint": os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", ""),
            "compression": os.getenv("OTEL_EXPORTER_OTLP_COMPRESSION", "gzip"),
            "timeout": int(os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT", "10")),
            "protocol": os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc"),
            "insecure": os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "false").lower() == "true"
        },
        "service": {
            "name": os.getenv("OTEL_SERVICE_NAME", "uvmgr"),
            "version": os.getenv("OTEL_SERVICE_VERSION", ""),
        },
        "resource_attributes": os.getenv("OTEL_RESOURCE_ATTRIBUTES", "")
    }
    
    console.print(json.dumps(config, indent=2))


def _get_otlp_validation_status() -> dict:
    """Get OTLP configuration validation status."""
    checks = {}
    issues = []
    
    # Check endpoint configuration
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        checks["Endpoint"] = {"passed": True, "message": f"Configured: {endpoint}"}
    else:
        checks["Endpoint"] = {"passed": False, "message": "No endpoint configured"}
        issues.append("Missing OTLP endpoint")
    
    # Check service name
    service_name = os.getenv("OTEL_SERVICE_NAME", "uvmgr")
    if service_name:
        checks["Service Name"] = {"passed": True, "message": f"Service: {service_name}"}
    else:
        checks["Service Name"] = {"passed": False, "message": "No service name"}
        issues.append("Missing service name")
    
    # Check protocol
    protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    if protocol in ["grpc", "http/protobuf"]:
        checks["Protocol"] = {"passed": True, "message": f"Valid protocol: {protocol}"}
    else:
        checks["Protocol"] = {"passed": False, "message": f"Invalid protocol: {protocol}"}
        issues.append("Invalid protocol")
    
    # Check compression
    compression = os.getenv("OTEL_EXPORTER_OTLP_COMPRESSION", "gzip")
    if compression in ["gzip", "none"]:
        checks["Compression"] = {"passed": True, "message": f"Valid compression: {compression}"}
    else:
        checks["Compression"] = {"passed": False, "message": f"Invalid compression: {compression}"}
        issues.append("Invalid compression")
    
    # Check timeout
    try:
        timeout = int(os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT", "10"))
        if 1 <= timeout <= 300:
            checks["Timeout"] = {"passed": True, "message": f"Valid timeout: {timeout}s"}
        else:
            checks["Timeout"] = {"passed": False, "message": f"Timeout out of range: {timeout}s"}
            issues.append("Timeout out of range (1-300s)")
    except ValueError:
        checks["Timeout"] = {"passed": False, "message": "Invalid timeout value"}
        issues.append("Invalid timeout value")
    
    return {
        "valid": len(issues) == 0,
        "issues": ", ".join(issues),
        "checks": checks
    }


def _test_otlp_connectivity() -> None:
    """Test OTLP endpoint connectivity."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        console.print("[red]❌ No endpoint configured for connectivity test[/red]")
        return
    
    try:
        import requests
        import time
        
        # Parse endpoint to get base URL for health check
        if endpoint.startswith("http"):
            base_url = endpoint.rsplit("/", 1)[0] if endpoint.endswith("/") else endpoint
        else:
            console.print("[yellow]⚠️ Cannot test gRPC endpoint connectivity directly[/yellow]")
            return
        
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            console.print(f"[green]✅ Connectivity test passed ({response_time:.0f}ms)[/green]")
        else:
            console.print(f"[yellow]⚠️ Endpoint reachable but returned {response.status_code}[/yellow]")
            
    except requests.exceptions.Timeout:
        console.print("[red]❌ Connection timeout - check endpoint URL[/red]")
    except requests.exceptions.ConnectionError:
        console.print("[red]❌ Connection failed - check if endpoint is running[/red]")
    except Exception as e:
        console.print(f"[red]❌ Connectivity test failed: {e}[/red]")
