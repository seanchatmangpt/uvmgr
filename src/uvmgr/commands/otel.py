"""
Typer sub-app: uvmgr otel …

Commands for OpenTelemetry validation and management.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from uvmgr.core.instrumentation import instrument_command
from uvmgr.core.semconv import CliAttributes, PackageAttributes
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import get_current_span, metric_counter, span

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
    else:
        console.print(f"\n[green]Coverage {overall_coverage:.1f}% meets threshold {threshold}%[/green]")


@app.command("validate")
@instrument_command("otel_validate")
def validate(
    endpoint: str = typer.Option(
        os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        "--endpoint",
        "-e",
        help="OTEL collector endpoint"
    ),
    timeout: int = typer.Option(5, "--timeout", "-t", help="Connection timeout in seconds"),
):
    """Validate OTEL configuration and connectivity."""
    console.print("[bold]OpenTelemetry Configuration Validation[/bold]\n")

    validation_results = []

    # Check if OTEL SDK is installed
    try:
        import opentelemetry
        from opentelemetry import trace
        validation_results.append(("OTEL SDK installed", True, f"Version: {opentelemetry.__version__}"))
    except ImportError:
        validation_results.append(("OTEL SDK installed", False, "Run: uvmgr deps add opentelemetry-sdk"))

    # Check environment variables
    env_vars = {
        "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
        "OTEL_SERVICE_NAME": os.environ.get("OTEL_SERVICE_NAME", "uvmgr"),
        "OTEL_TRACES_EXPORTER": os.environ.get("OTEL_TRACES_EXPORTER", "otlp"),
        "OTEL_METRICS_EXPORTER": os.environ.get("OTEL_METRICS_EXPORTER", "otlp"),
    }

    for var, value in env_vars.items():
        if value:
            validation_results.append((f"Env: {var}", True, value))
        else:
            validation_results.append((f"Env: {var}", False, "Not set"))

    # Test collector connectivity
    import urllib.error
    import urllib.request

    # Try gRPC health check
    health_url = endpoint.replace("4317", "13133") + "/health"
    health_url = health_url.replace("http://", "").replace("https://", "")
    health_url = f"http://{health_url}"

    try:
        with urllib.request.urlopen(health_url, timeout=timeout) as response:
            if response.status == 200:
                validation_results.append(("Collector health check", True, "Connected"))
            else:
                validation_results.append(("Collector health check", False, f"Status: {response.status}"))
    except Exception as e:
        validation_results.append(("Collector health check", False, str(e)))

    # Display results
    table = Table(title="Validation Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    all_passed = True
    for check, passed, details in validation_results:
        status = "✓ Pass" if passed else "✗ Fail"
        style = "green" if passed else "red"
        table.add_row(check, f"[{style}]{status}[/{style}]", details)
        if not passed:
            all_passed = False

    console.print(table)

    if all_passed:
        console.print("\n[green]✓ All validation checks passed![/green]")
    else:
        console.print("\n[red]✗ Some validation checks failed.[/red]")
        raise typer.Exit(1)


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
        import opentelemetry
        console.print(f"  [green]✓[/green] OpenTelemetry SDK v{opentelemetry.__version__}")
    except ImportError:
        console.print("  [yellow]![/yellow] OpenTelemetry SDK not installed (telemetry disabled)")

    # Show semantic conventions
    console.print("\n[bold]Semantic Conventions:[/bold]")
    try:
        from uvmgr.core import semconv
        conv_modules = [
            "CliAttributes", "PackageAttributes", "BuildAttributes",
            "TestAttributes", "AiAttributes", "McpAttributes"
        ]
        for module in conv_modules:
            if hasattr(semconv, module):
                console.print(f"  [green]✓[/green] {module}")
    except ImportError:
        console.print("  [red]✗[/red] Semantic conventions not found")


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
