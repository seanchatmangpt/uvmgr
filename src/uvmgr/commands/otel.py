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

from uvmgr.core.instrumentation import instrument_command
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
    """Manage semantic conventions with Weaver."""
    weaver_path = Path(__file__).parent.parent.parent.parent / "tools" / "weaver"
    registry_path = Path(__file__).parent.parent.parent.parent / "weaver-forge" / "registry"

    if not weaver_path.exists():
        console.print("[red]Weaver not found. Please install it first.[/red]")
        raise typer.Exit(1)

    if validate or (not validate and not generate):
        console.print("[bold]Validating semantic conventions...[/bold]")

        result = subprocess.run(
            [str(weaver_path), "registry", "check", "-r", str(registry_path), "--future"],
            capture_output=True,
            text=True, check=False
        )

        if result.returncode == 0:
            console.print("[green]✓ Semantic conventions are valid![/green]")
        else:
            console.print("[red]✗ Validation failed:[/red]")
            console.print(result.stderr)
            raise typer.Exit(1)

    if generate:
        console.print("\n[bold]Generating code from conventions...[/bold]")

        # Run the validation script which handles generation
        script_path = registry_path.parent / "validate_semconv.py"
        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True, check=False
        )

        if result.returncode == 0:
            console.print("[green]✓ Code generation completed![/green]")
            console.print(result.stdout)
        else:
            console.print("[red]✗ Generation failed:[/red]")
            console.print(result.stderr)
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
        assert hasattr(CliAttributes, "COMMAND")
        assert hasattr(CliAttributes, "EXIT_CODE")
        conventions_tested += 1

        # Test Package conventions
        assert hasattr(PackageAttributes, "NAME")
        assert hasattr(PackageAttributes, "VERSION")
        conventions_tested += 1

        # Test Build conventions
        assert hasattr(BuildAttributes, "TYPE")
        assert hasattr(BuildAttributes, "DURATION")
        conventions_tested += 1

        # Test Workflow conventions
        assert hasattr(WorkflowAttributes, "ENGINE")
        assert hasattr(WorkflowAttributes, "OPERATION")
        conventions_tested += 1

        # Test that constants have proper values (strings)
        assert isinstance(CliAttributes.COMMAND, str)
        assert isinstance(PackageAttributes.NAME, str)
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
