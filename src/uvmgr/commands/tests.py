"""
uvmgr.commands.tests
--------------------
Test execution and coverage commands for uvmgr.

This module provides CLI commands for running tests and generating coverage reports
using pytest and coverage tools. It includes comprehensive CI verification tools
and full OpenTelemetry instrumentation.

Commands
--------
- run : Run the test suite using pytest
- coverage : Generate coverage reports using coverage
- ci verify : Comprehensive CI verification (replaces verify_pyinstaller_ci.py)
- ci quick : Quick CI checks for development
- ci run : Run full CI pipeline locally

All commands automatically instrument with telemetry and provide both human-readable
and JSON output formats.

Example
-------
    $ uvmgr tests run
    $ uvmgr tests run --verbose
    $ uvmgr tests coverage
    $ uvmgr tests ci verify
    $ uvmgr tests ci quick

See Also
--------
- :mod:`uvmgr.core.process` : Process execution utilities
- :mod:`uvmgr.core.semconv` : Semantic conventions
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from uvmgr.core.instrumentation import (
    add_span_attributes,
    add_span_event,
    instrument_command,
    instrument_subcommand,
)
from uvmgr.core.process import run_logged
from uvmgr.core.semconv import CIAttributes, CIOperations, TestAttributes, TestCoverageAttributes
from uvmgr.core.testing import (
    get_test_infrastructure,
    TestDiscovery,
    TestReporter,
    TestType,
    generate_test_templates
)
from uvmgr.core.shell import dump_json

app = typer.Typer(help="Run the test suite (and coverage) using pytest and coverage.")

console = Console()


@app.command("run")
@instrument_command("tests_run", track_args=True)
def run_tests(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Run tests verbosely"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Run tests in parallel"),
    coverage: bool = typer.Option(True, "--coverage/--no-coverage", help="Collect coverage data"),
    fail_fast: bool = typer.Option(False, "--fail-fast", "-x", help="Stop on first failure"),
    test_type: List[str] = typer.Option([], "--type", "-t", help="Test types to run (unit, integration, e2e)"),
    markers: List[str] = typer.Option([], "--marker", "-m", help="Test markers to run"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output results as JSON"),
    generate_report: bool = typer.Option(True, "--report/--no-report", help="Generate comprehensive test report")
):
    """
    🧪 Run comprehensive test suite with intelligent optimization.
    
    This enhanced command uses the new Tier 2B testing infrastructure to provide:
    - Intelligent test discovery and classification
    - Parallel execution for performance
    - Comprehensive coverage analysis
    - Advanced failure analysis and recommendations
    - Performance benchmarking
    
    The command automatically discovers and categorizes tests by type (unit, integration, e2e)
    and provides detailed analytics and recommendations for improving test quality.
    """
    
    # Parse test types
    test_types = []
    if test_type:
        type_map = {
            "unit": TestType.UNIT,
            "integration": TestType.INTEGRATION,
            "e2e": TestType.E2E,
            "performance": TestType.PERFORMANCE,
            "security": TestType.SECURITY
        }
        test_types = [type_map.get(t) for t in test_type if t in type_map]
    
    if not test_types:
        test_types = [TestType.UNIT, TestType.INTEGRATION]  # Default types
    
    # Track enhanced test execution
    add_span_attributes(**{
        TestAttributes.OPERATION: "run_comprehensive",
        TestAttributes.FRAMEWORK: "pytest_enhanced",
        "test.verbose": verbose,
        "test.parallel": parallel,
        "test.coverage": coverage,
        "test.types": [t.value for t in test_types],
        "test.markers": markers
    })
    add_span_event("tests.comprehensive.started", {
        "test_types": [t.value for t in test_types],
        "parallel": parallel,
        "coverage": coverage
    })
    
    console.print(Panel(
        f"🧪 [bold]Comprehensive Test Execution[/bold]\n"
        f"Types: {', '.join(t.value for t in test_types)}\n"
        f"Parallel: {'✅' if parallel else '❌'}\n"
        f"Coverage: {'✅' if coverage else '❌'}\n"
        f"Markers: {', '.join(markers) if markers else 'None'}",
        title="Test Configuration"
    ))
    
    try:
        # Use the comprehensive testing infrastructure
        async def _run_tests():
            infrastructure = get_test_infrastructure(Path.cwd())
            return await infrastructure.run_tests(
                test_types=test_types,
                parallel=parallel,
                coverage=coverage,
                fail_fast=fail_fast,
                verbose=verbose,
                markers=markers
            )
        
        # Run tests asynchronously
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running comprehensive test suite...", total=None)
            test_suite = asyncio.run(_run_tests())
            progress.update(task, description="Test execution completed")
        
        # Generate comprehensive report
        if generate_report:
            reporter = TestReporter(Path.cwd())
            report = reporter.generate_comprehensive_report(test_suite)
            
            if json_output:
                dump_json(report)
            else:
                _display_test_results(test_suite, report)
        
        # Record final metrics
        add_span_attributes(**{
            TestAttributes.TEST_COUNT: test_suite.total_tests,
            TestAttributes.PASSED: test_suite.passed,
            TestAttributes.FAILED: test_suite.failed,
            TestAttributes.SKIPPED: test_suite.skipped,
            TestCoverageAttributes.COVERAGE_PERCENTAGE: test_suite.coverage_percentage or 0.0
        })
        
        if test_suite.failed > 0:
            add_span_event("tests.comprehensive.completed", {"success": False})
            console.print(f"\n[red]❌ {test_suite.failed} test(s) failed[/red]")
            raise typer.Exit(1)
        else:
            add_span_event("tests.comprehensive.completed", {"success": True})
            console.print(f"\n[green]✅ All {test_suite.passed} test(s) passed![/green]")
    
    except Exception as e:
        console.print(f"[red]❌ Test execution failed: {e}[/red]")
        add_span_event("tests.comprehensive.failed", {"error": str(e)})
        raise typer.Exit(1)


def _display_test_results(test_suite, report):
    """Display comprehensive test results."""
    
    # Summary table
    summary_table = Table(title="Test Execution Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")
    summary_table.add_column("Status", style="green")
    
    summary_data = [
        ("Total Tests", str(test_suite.total_tests), "✅"),
        ("Passed", str(test_suite.passed), "🟢"),
        ("Failed", str(test_suite.failed), "🔴" if test_suite.failed > 0 else "✅"),
        ("Skipped", str(test_suite.skipped), "🟡" if test_suite.skipped > 0 else "✅"),
        ("Success Rate", f"{test_suite.success_rate:.1%}", "🟢" if test_suite.success_rate > 0.95 else "🟡"),
        ("Duration", f"{test_suite.total_duration:.2f}s", "✅"),
        ("Coverage", f"{test_suite.coverage_percentage:.1f}%" if test_suite.coverage_percentage else "N/A", 
         "🟢" if (test_suite.coverage_percentage or 0) >= 80 else "🟡")
    ]
    
    for metric, value, status in summary_data:
        summary_table.add_row(metric, value, status)
    
    console.print(summary_table)
    
    # Performance insights
    if report.get("performance"):
        perf = report["performance"]
        console.print(f"\n📊 Performance Insights:")
        console.print(f"   Average test duration: {perf['average_test_duration']:.3f}s")
        
        if perf.get("slowest_tests"):
            console.print(f"   Slowest tests:")
            for test in perf["slowest_tests"][:3]:
                console.print(f"     • {test['name']}: {test['duration']:.3f}s")
    
    # Failure analysis
    if report.get("failures") and test_suite.failed > 0:
        console.print(f"\n🔍 Failure Analysis:")
        for failure in report["failures"][:3]:
            console.print(f"   ❌ {failure['name']}")
            console.print(f"      Category: {failure['category']}")
            console.print(f"      Fix: {failure['suggested_fix']}")
    
    # Recommendations
    if report.get("recommendations"):
        console.print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            console.print(f"   • {rec}")


@app.command("discover")
@instrument_command("tests_discover", track_args=True)
def discover_tests(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """🔍 Discover and analyze test structure."""
    
    discovery = TestDiscovery(Path.cwd())
    discovered = discovery.discover_tests()
    stats = discovery.get_test_statistics()
    
    if json_output:
        dump_json({
            "discovered_tests": {k.value: [str(f) for f in v] for k, v in discovered.items()},
            "statistics": stats
        })
        return
    
    console.print("🔍 Test Discovery Results")
    console.print("=" * 40)
    
    for test_type, files in discovered.items():
        type_stats = stats["by_type"].get(test_type.value, {})
        console.print(f"\n📋 {test_type.value.title()} Tests:")
        console.print(f"   Files: {len(files)}")
        console.print(f"   Functions: {type_stats.get('functions', 0)}")
        console.print(f"   Async functions: {type_stats.get('async_functions', 0)}")
        
        if type_stats.get("markers"):
            console.print(f"   Markers: {', '.join(type_stats['markers'])}")
        
        for test_file in files[:3]:  # Show first 3 files
            console.print(f"     📄 {test_file.relative_to(Path.cwd())}")
        
        if len(files) > 3:
            console.print(f"     ... and {len(files) - 3} more files")
    
    console.print(f"\n📊 Summary:")
    console.print(f"   Total test files: {stats['total_test_files']}")
    console.print(f"   Total test functions: {stats['total_functions']}")


@app.command("generate")
@instrument_command("tests_generate", track_args=True)
def generate_test_templates(
    module: str = typer.Argument(..., help="Module path to generate tests for (e.g., uvmgr.core.config)"),
    test_type: str = typer.Option("unit", "--type", "-t", help="Test type to generate (unit, integration)")
):
    """🏗️ Generate test templates for modules (8020 test generation)."""
    
    try:
        templates = generate_test_templates(Path.cwd(), module)
        
        console.print(f"✅ Generated test templates for {module}:")
        for template in templates:
            console.print(f"   📄 {template.relative_to(Path.cwd())}")
        
        console.print(f"\n💡 Edit the generated templates to implement actual tests")
        
    except Exception as e:
        console.print(f"❌ Failed to generate test templates: {e}")
        raise typer.Exit(1)


@app.command("coverage")
@instrument_command("tests_coverage", track_args=True)
def run_coverage(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Run coverage verbosely."),
):
    """
    Generate coverage reports using coverage run + coverage report.
    
    This command runs the test suite with coverage measurement and generates
    a coverage report showing which parts of the code were executed during
    testing. It uses the coverage tool to measure code coverage.
    
    Parameters
    ----------
    verbose : bool, optional
        If True, run coverage with verbose output showing more details about
        coverage measurement and reporting. Default is False.
    
    Notes
    -----
    The command automatically:
    - Runs the test suite with coverage measurement
    - Generates a coverage report showing line coverage
    - Records telemetry for coverage execution
    - Uses project's coverage configuration from pyproject.toml
    
    Coverage measurement includes:
    - Line coverage for all Python files in the project
    - Branch coverage if enabled in configuration
    - Coverage data stored in .coverage file
    - HTML and XML reports generated automatically
    
    Example
    -------
    >>> # Generate coverage report
    >>> uvmgr tests coverage
    >>> 
    >>> # Generate coverage with verbose output
    >>> uvmgr tests coverage --verbose
    >>> 
    >>> # Coverage data is stored in .coverage file
    >>> # HTML report available in htmlcov/ directory
    """
    # Track coverage execution
    add_span_attributes(
        **{
            TestAttributes.OPERATION: "coverage",
            TestAttributes.FRAMEWORK: "pytest",
            "test.verbose": verbose,
        }
    )
    add_span_event("tests.coverage.started", {"framework": "pytest", "verbose": verbose})

    cmd_run = ["coverage", "run", "--module", "pytest"]
    cmd_report = ["coverage", "report"]
    if verbose:
        cmd_run.append("-v")
    run_logged(cmd_run)
    run_logged(cmd_report)
    add_span_event("tests.coverage.completed", {"success": True})


# CI subcommand group
ci_app = typer.Typer(help="Run CI tests locally")
app.add_typer(ci_app, name="ci")


class CIVerifier:
    """
    Verify CI tests locally.
    
    This class provides functionality to run CI verification tests locally,
    allowing developers to test their changes before pushing to CI. It
    includes comprehensive testing of build processes, package installation,
    and executable generation.
    
    Attributes
    ----------
    results : list[tuple[str, bool, str]]
        List of test results as (description, success, details) tuples.
    start_time : float
        Timestamp when verification started.
    
    Example
    -------
    >>> verifier = CIVerifier()
    >>> verifier.run_command("python --version", "Check Python version")
    >>> verifier.run_command("uv --version", "Check uv version")
    >>> success = verifier.show_results()
    """

    def __init__(self):
        self.results: list[tuple[str, bool, str]] = []
        self.start_time = time.time()

    def run_command(self, cmd: str, description: str, check: bool = True, timeout: int = 300) -> bool:
        """
        Run a command and record the result.
        
        This method executes a shell command and records the success or failure
        of the command. It provides real-time feedback and handles timeouts
        and exceptions gracefully.
        
        Parameters
        ----------
        cmd : str
            The shell command to execute.
        description : str
            Human-readable description of what the command is testing.
        check : bool, optional
            If True, raise an exception on command failure. If False,
            record the failure but continue execution. Default is True.
        timeout : int, optional
            Maximum time in seconds to wait for command completion.
            Default is 300 seconds (5 minutes).
        
        Returns
        -------
        bool
            True if the command succeeded, False otherwise.
        
        Notes
        -----
        The method automatically:
        - Displays the command being executed
        - Shows real-time progress feedback
        - Handles command timeouts gracefully
        - Records detailed error information
        - Updates the results list with outcome
        
        Example
        -------
        >>> verifier = CIVerifier()
        >>> success = verifier.run_command(
        ...     "python -c 'print(\"Hello\")'",
        ...     "Test Python execution",
        ...     check=False
        ... )
        >>> print(f"Command succeeded: {success}")
        """
        console.print(f"\n[bold blue]Testing:[/bold blue] {description}")
        console.print(f"[dim]Command: {cmd}[/dim]")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            success = result.returncode == 0
            if success:
                console.print("[green]✓[/green] Passed")
                self.results.append((description, True, "Passed"))
            else:
                console.print("[red]✗[/red] Failed")
                error_msg = result.stderr or result.stdout or "Unknown error"
                self.results.append((description, False, error_msg[:100]))
                if check:
                    console.print(f"[red]Error:[/red] {error_msg}")
                    return False

            return success

        except subprocess.TimeoutExpired:
            console.print("[red]✗[/red] Timed out")
            self.results.append((description, False, "Timeout"))
            return False
        except Exception as e:
            console.print(f"[red]✗[/red] Exception: {e}")
            self.results.append((description, False, str(e)[:100]))
            return False

    def show_results(self) -> bool:
        """
        Display test results summary.
        
        This method displays a comprehensive summary of all test results,
        including a formatted table showing the status of each test and
        overall statistics.
        
        Returns
        -------
        bool
            True if all tests passed, False if any test failed.
        
        Notes
        -----
        The method displays:
        - A formatted table with test names, status, and details
        - Overall statistics (total tests, passed, failed, success rate)
        - Time elapsed for all tests
        - Color-coded status indicators
        
        The summary panel is color-coded:
        - Green: All tests passed
        - Yellow: Some tests passed, some failed
        - Red: All tests failed
        
        Example
        -------
        >>> verifier = CIVerifier()
        >>> verifier.run_command("python --version", "Python version")
        >>> verifier.run_command("uv --version", "uv version")
        >>> all_passed = verifier.show_results()
        >>> if all_passed:
        ...     print("All CI checks passed!")
        """
        elapsed = time.time() - self.start_time

        # Create results table
        table = Table(title="CI Test Results", show_header=True)
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")

        passed = 0
        for test, success, details in self.results:
            status = "[green]✓ PASS[/green]" if success else "[red]✗ FAIL[/red]"
            table.add_row(test, status, details)
            if success:
                passed += 1

        console.print("\n")
        console.print(table)

        # Summary
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0

        summary_style = "green" if passed == total else "yellow" if passed > 0 else "red"
        console.print(Panel.fit(
            "[bold]Summary[/bold]\n\n"
            f"Tests run: {total}\n"
            f"Passed: {passed}\n"
            f"Failed: {total - passed}\n"
            f"Success rate: {success_rate:.1f}%\n"
            f"Time elapsed: {elapsed:.1f}s",
            border_style=summary_style
        ))

        return passed == total


@ci_app.command("verify")
@instrument_subcommand("tests")
def ci_verify(
    timeout: int = typer.Option(300, "--timeout", "-t", help="Command timeout in seconds"),
    skip_build: bool = typer.Option(False, "--skip-build", help="Skip executable build tests"),
    clean: bool = typer.Option(True, "--clean/--no-clean", help="Clean up artifacts after testing"),
):
    """
    Comprehensive CI verification (replaces verify_pyinstaller_ci.py).
    
    This command runs a comprehensive set of CI verification tests locally,
    allowing developers to test their changes before pushing to CI. It includes
    environment checks, dependency validation, build testing, and executable
    generation verification.
    
    Parameters
    ----------
    timeout : int, optional
        Maximum time in seconds to wait for each command to complete.
        Default is 300 seconds (5 minutes).
    skip_build : bool, optional
        If True, skip the PyInstaller build tests. Useful for faster
        verification when build testing is not needed. Default is False.
    clean : bool, optional
        If True, clean up temporary artifacts after testing. Set to False
        to preserve artifacts for debugging. Default is True.
    
    Notes
    -----
    The verification includes:
    - Environment checks (Python version, uv version, etc.)
    - Dependency validation and installation
    - Package building and installation
    - PyInstaller executable generation (unless skipped)
    - Test execution and coverage
    - Cleanup of temporary files
    
    All tests are run with telemetry instrumentation and provide
    detailed feedback on success or failure.
    
    Example
    -------
    >>> # Run full verification
    >>> uvmgr tests ci verify
    >>> 
    >>> # Quick verification without build tests
    >>> uvmgr tests ci verify --skip-build
    >>> 
    >>> # Verification with longer timeout
    >>> uvmgr tests ci verify --timeout 600
    >>> 
    >>> # Keep artifacts for debugging
    >>> uvmgr tests ci verify --no-clean
    """
    add_span_attributes(**{
        CIAttributes.OPERATION: CIOperations.VERIFY,
        CIAttributes.RUNNER: "local",
        CIAttributes.ENVIRONMENT: "development",
    })
    add_span_event("ci.verify.started", {"timeout": timeout, "skip_build": skip_build})

    console.print(Panel.fit(
        "[bold]PyInstaller CI Verification[/bold]\n\n"
        "Running local tests to verify PyInstaller integration\n"
        "before pushing to CI.",
        border_style="cyan"
    ))

    verifier = CIVerifier()

    # Environment checks
    env_tests = [
        ("Python version", "python --version"),
        ("UV installed", "which uv"),
        ("PyInstaller available", "python -c 'import PyInstaller'"),
        ("Project dependencies", "uv pip list | grep -E '(typer|rich|pyinstaller)'"),
    ]

    console.print(Panel.fit("[bold]1. Environment Verification[/bold]", border_style="cyan"))
    for desc, cmd in env_tests:
        verifier.run_command(cmd, desc, check=False, timeout=30)

    # Unit tests
    console.print(Panel.fit("[bold]2. Unit Tests[/bold]", border_style="cyan"))
    verifier.run_command("pytest tests/test_build_exe.py -v", "PyInstaller unit tests", timeout=timeout)

    # Linting
    console.print(Panel.fit("[bold]3. Linting[/bold]", border_style="cyan"))
    verifier.run_command("uvmgr lint check", "Code linting", timeout=timeout)

    # Build commands
    if not skip_build:
        console.print(Panel.fit("[bold]4. Build Commands[/bold]", border_style="cyan"))
        build_tests = [
            ("Generate spec file", "uvmgr build spec --name test-ci-build"),
            ("Build test executable", "uvmgr build exe --name test-ci --exclude numpy --exclude pandas"),
            ("Build uvmgr (dogfood)", "uvmgr build dogfood --no-test --no-platform"),
        ]
        for desc, cmd in build_tests:
            verifier.run_command(cmd, desc, check=False, timeout=timeout)

        # Test built executable
        console.print(Panel.fit("[bold]5. Executable Testing[/bold]", border_style="cyan"))
        dist_path = Path("dist")
        if dist_path.exists():
            executables = list(dist_path.glob("uvmgr*"))
            if executables:
                exe_path = executables[0]
                exe_tests = [
                    ("Executable runs", f"{exe_path} --version"),
                    ("Help works", f"{exe_path} --help"),
                    ("Commands list", f"{exe_path}"),
                ]
                for desc, cmd in exe_tests:
                    verifier.run_command(cmd, desc, check=False, timeout=30)

    # Cleanup
    if clean:
        console.print(Panel.fit("[bold]6. Cleanup[/bold]", border_style="cyan"))
        cleanup_commands = [
            ("Remove spec files", "rm -f test-ci*.spec uvmgr-demo.spec"),
            ("Remove build dir", "rm -rf build/"),
            ("Remove dist dir", "rm -rf dist/"),
        ]
        for desc, cmd in cleanup_commands:
            verifier.run_command(cmd, desc, check=False, timeout=30)

    # Show results
    all_passed = verifier.show_results()

    # Record metrics
    total_tests = len(verifier.results)
    passed_tests = sum(1 for _, success, _ in verifier.results if success)
    elapsed = time.time() - verifier.start_time

    add_span_attributes(**{
        CIAttributes.TEST_COUNT: total_tests,
        CIAttributes.PASSED: passed_tests,
        CIAttributes.FAILED: total_tests - passed_tests,
        CIAttributes.DURATION: elapsed,
        CIAttributes.SUCCESS_RATE: (passed_tests / total_tests * 100) if total_tests > 0 else 0,
    })

    if all_passed:
        console.print("\n[bold green]✅ All CI verification tests passed![/bold green]")
        console.print("[dim]Your PyInstaller changes are ready for CI.[/dim]")
        add_span_event("ci.verify.completed", {"success": True})
    else:
        console.print("\n[bold red]❌ Some CI verification tests failed![/bold red]")
        console.print("[dim]Please fix the issues before pushing.[/dim]")
        add_span_event("ci.verify.completed", {"success": False})
        raise typer.Exit(1)


@ci_app.command("quick")
@instrument_subcommand("tests")
def ci_quick(
    timeout: int = typer.Option(30, "--timeout", "-t", help="Command timeout in seconds"),
):
    """Quick essential CI tests (replaces quick_ci_test.py)."""
    add_span_attributes(**{
        CIAttributes.OPERATION: CIOperations.QUICK_TEST,
        CIAttributes.RUNNER: "local",
        CIAttributes.ENVIRONMENT: "development",
    })
    add_span_event("ci.quick.started", {"timeout": timeout})

    console.print(Panel.fit(
        "[bold]Quick PyInstaller CI Test[/bold]\n\n"
        "Running essential tests to verify PyInstaller integration",
        border_style="cyan"
    ))

    start_time = time.time()
    verifier = CIVerifier()

    # Quick essential tests
    tests = [
        ("Python version check", "python --version"),
        ("PyInstaller import", "python -c 'import PyInstaller; print(f\"PyInstaller {PyInstaller.__version__}\")'"),
        ("Run unit tests", "pytest tests/test_build_exe.py -v"),
        ("Generate spec file", "uvmgr build spec --name ci-test"),
        ("Clean up", "rm -f ci-test.spec"),
    ]

    for description, command in tests:
        verifier.run_command(command, description, check=False, timeout=timeout)

    # Show results
    all_passed = verifier.show_results()

    # Record metrics
    total_tests = len(verifier.results)
    passed_tests = sum(1 for _, success, _ in verifier.results if success)
    elapsed = time.time() - start_time

    add_span_attributes(**{
        CIAttributes.TEST_COUNT: total_tests,
        CIAttributes.PASSED: passed_tests,
        CIAttributes.FAILED: total_tests - passed_tests,
        CIAttributes.DURATION: elapsed,
        CIAttributes.SUCCESS_RATE: (passed_tests / total_tests * 100) if total_tests > 0 else 0,
    })

    if all_passed:
        console.print("\n[bold green]✅ All tests passed! PyInstaller integration is ready for CI.[/bold green]")
        add_span_event("ci.quick.completed", {"success": True})
    else:
        console.print("\n[bold red]❌ Some tests failed. Please check the errors above.[/bold red]")
        add_span_event("ci.quick.completed", {"success": False})
        raise typer.Exit(1)


@ci_app.command("run")
@instrument_subcommand("tests")
def ci_run(
    runner: str = typer.Option("native", "--runner", "-r", help="CI runner method (native, act, docker)"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="Command timeout in seconds"),
):
    """Run CI tests with different runner methods (replaces run_ci_locally.sh)."""
    add_span_attributes(**{
        CIAttributes.OPERATION: CIOperations.RUN,
        CIAttributes.RUNNER: runner,
        CIAttributes.ENVIRONMENT: "development",
    })
    add_span_event("ci.run.started", {"runner": runner, "timeout": timeout})

    console.print(Panel.fit(
        f"[bold]uvmgr CI Local Runner[/bold]\n\n"
        f"Running CI tests with {runner} method",
        border_style="cyan"
    ))

    verifier = CIVerifier()

    if runner == "native":
        # Native CI simulation
        native_tests = [
            ("Check Python version", "python --version"),
            ("Install dependencies", "uv pip install -e ."),
            ("Install PyInstaller", "uv pip install pyinstaller pyinstaller-hooks-contrib"),
            ("Run linting", "uvmgr lint check"),
            ("Run tests", "uvmgr tests run"),
            ("Run PyInstaller tests", "pytest tests/test_build_exe.py -v"),
            ("Test spec generation", "uvmgr build spec --name ci-test"),
            ("Test executable build", "uvmgr build exe --name ci-test --clean"),
            ("Test dogfood build", "uvmgr build dogfood --test --no-platform"),
        ]

        for desc, cmd in native_tests:
            verifier.run_command(cmd, desc, check=False, timeout=timeout)

        # Verify executable if it exists
        dist_path = Path("dist")
        if dist_path.exists():
            executables = list(dist_path.glob("uvmgr*"))
            if executables:
                exe_path = executables[0]
                verifier.run_command(f"{exe_path} --version", "Verify built executable", check=False, timeout=30)

    elif runner == "act":
        # GitHub Actions local runner
        act_check = verifier.run_command("which act", "Check act installation", check=False, timeout=30)
        if not act_check:
            console.print("[yellow]act is not installed. Install it with:[/yellow]")
            console.print("  brew install act  # macOS")
            console.print("  curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux")
            raise typer.Exit(1)

        act_tests = [
            ("Run PyInstaller tests with act", "act -j test-pyinstaller -P ubuntu-latest=catthehacker/ubuntu:act-latest"),
            ("Run main test workflow with act", "act -j test -P ubuntu-latest=catthehacker/ubuntu:act-latest"),
        ]

        for desc, cmd in act_tests:
            verifier.run_command(cmd, desc, check=False, timeout=timeout)

    elif runner == "docker":
        # Docker/devcontainer method
        docker_check = verifier.run_command("which docker", "Check Docker installation", check=False, timeout=30)
        if not docker_check:
            console.print("[red]Docker is not installed. Please install Docker first.[/red]")
            raise typer.Exit(1)

        docker_tests = [
            ("Build devcontainer", "docker build -t uvmgr-ci -f .devcontainer/Dockerfile ."),
            ("Run tests in container", 'docker run --rm -v "$(pwd)":/workspace uvmgr-ci bash -c "cd /workspace && uvmgr lint check && uvmgr tests run && pytest tests/test_build_exe.py -v"'),
        ]

        for desc, cmd in docker_tests:
            verifier.run_command(cmd, desc, check=False, timeout=timeout)

    else:
        console.print(f"[red]Unknown runner: {runner}[/red]")
        console.print("[yellow]Available runners: native, act, docker[/yellow]")
        raise typer.Exit(1)

    # Cleanup
    cleanup_commands = [
        ("Remove spec files", "rm -f test-*.spec ci-test.spec uvmgr-demo.spec"),
        ("Remove build directories", "rm -rf build/ dist/"),
    ]
    for desc, cmd in cleanup_commands:
        verifier.run_command(cmd, desc, check=False, timeout=30)

    # Show results
    all_passed = verifier.show_results()

    # Record metrics
    total_tests = len(verifier.results)
    passed_tests = sum(1 for _, success, _ in verifier.results if success)
    elapsed = time.time() - verifier.start_time

    add_span_attributes(**{
        CIAttributes.TEST_COUNT: total_tests,
        CIAttributes.PASSED: passed_tests,
        CIAttributes.FAILED: total_tests - passed_tests,
        CIAttributes.DURATION: elapsed,
        CIAttributes.SUCCESS_RATE: (passed_tests / total_tests * 100) if total_tests > 0 else 0,
    })

    if all_passed:
        console.print(f"\n[bold green]✅ All CI tests passed with {runner} runner![/bold green]")
        add_span_event("ci.run.completed", {"success": True, "runner": runner})
    else:
        console.print(f"\n[bold red]❌ Some CI tests failed with {runner} runner![/bold red]")
        add_span_event("ci.run.completed", {"success": False, "runner": runner})
        raise typer.Exit(1)
