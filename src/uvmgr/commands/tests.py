"""
Typer sub-app: uvmgr tests …

This module implements a command (run) and a subcommand (coverage) to run the test suite and generate coverage reports.
"""

from __future__ import annotations

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

from uvmgr.core.instrumentation import instrument_command, instrument_subcommand, add_span_attributes, add_span_event
from uvmgr.core.semconv import TestAttributes, CIAttributes, CIOperations
from uvmgr.core.process import run_logged
from .. import main as cli_root

tests_app = typer.Typer(help="Run the test suite (and coverage) using pytest and coverage.")

# Mount the sub-app under the name 'tests' (so that 'uvmgr tests' works)
cli_root.app.add_typer(tests_app, name="tests")

console = Console()


@tests_app.command("run")
@instrument_command("tests_run", track_args=True)
def run_tests(verbose: bool = typer.Option(False, "--verbose", "-v", help="Run tests verbosely.")):
    """Run the test suite using pytest."""
    # Track test execution
    add_span_attributes(
        **{
            TestAttributes.OPERATION: "run",
            TestAttributes.FRAMEWORK: "pytest",
            "test.verbose": verbose,
        }
    )
    add_span_event("tests.run.started", {"framework": "pytest", "verbose": verbose})
    
    cmd = ["pytest"]
    if verbose:
        cmd.append("-v")
    run_logged(cmd)
    add_span_event("tests.run.completed", {"success": True})


@tests_app.command("coverage")
@instrument_command("tests_coverage", track_args=True)
def run_coverage(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Run coverage verbosely."),
):
    """Generate coverage reports using coverage run + coverage report."""
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
tests_app.add_typer(ci_app, name="ci")


class CIVerifier:
    """Verify CI tests locally."""

    def __init__(self):
        self.results: list[tuple[str, bool, str]] = []
        self.start_time = time.time()

    def run_command(self, cmd: str, description: str, check: bool = True, timeout: int = 300) -> bool:
        """Run a command and record the result."""
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
        """Display test results summary."""
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
            f"[bold]Summary[/bold]\n\n"
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
    """Comprehensive CI verification (replaces verify_pyinstaller_ci.py)."""
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