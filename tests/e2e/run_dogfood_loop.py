#!/usr/bin/env python3
"""Run the complete uvmgr dogfooding test loop.

This script uses uvmgr to test itself in a self-referential loop.
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()


class DogfoodRunner:
    """Runner for dogfooding test loop."""

    def __init__(self, verbose: bool = False):
        """Initialize runner."""
        self.verbose = verbose
        self.results: dict[str, tuple[bool, float, str]] = {}
        self.start_time = time.time()

    def run_command(self, *args: str, cwd: Path = None) -> tuple[bool, str, str]:
        """Run a uvmgr command and return success, stdout, stderr."""
        cmd = ["uvmgr"] + list(args)

        if self.verbose:
            console.print(f"[cyan]Running:[/cyan] {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or Path.cwd(),
                capture_output=True,
                text=True,
                timeout=120, check=False  # 2 minute timeout
            )
            success = result.returncode == 0

            if self.verbose and not success:
                console.print(f"[red]Failed:[/red] {result.stderr}")

            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def test_self_help(self) -> bool:
        """Test uvmgr help command."""
        console.print("\n[bold blue]Test 1: uvmgr --help[/bold blue]")
        start = time.time()

        success, stdout, _ = self.run_command("--help")
        duration = time.time() - start

        if success and "Usage: uvmgr" in stdout:
            console.print("[green]✓[/green] Help command works")
            self.results["help"] = (True, duration, "Help displayed correctly")
            return True
        console.print("[red]✗[/red] Help command failed")
        self.results["help"] = (False, duration, "Help not displayed")
        return False

    def test_self_version(self) -> bool:
        """Test uvmgr version command."""
        console.print("\n[bold blue]Test 2: uvmgr --version[/bold blue]")
        start = time.time()

        success, stdout, _ = self.run_command("--version")
        duration = time.time() - start

        if success and ("uvmgr" in stdout or "version" in stdout.lower()):
            console.print("[green]✓[/green] Version command works")
            self.results["version"] = (True, duration, "Version displayed")
            return True
        console.print("[red]✗[/red] Version command failed")
        self.results["version"] = (False, duration, "Version not displayed")
        return False

    def test_self_tests(self) -> bool:
        """Test running uvmgr's own test suite."""
        console.print("\n[bold blue]Test 3: uvmgr tests run (self-test)[/bold blue]")
        start = time.time()

        # Run a simple test file
        success, stdout, stderr = self.run_command(
            "tests", "run", "tests/test_import.py", "--tb=short"
        )
        duration = time.time() - start

        if success and "passed" in stdout:
            console.print("[green]✓[/green] Self-tests pass")
            self.results["self_test"] = (True, duration, "Tests passed")
            return True
        console.print("[red]✗[/red] Self-tests failed")
        self.results["self_test"] = (False, duration, f"Tests failed: {stderr}")
        return False

    def test_project_cycle(self) -> bool:
        """Test full project development cycle."""
        console.print("\n[bold blue]Test 4: Full project cycle[/bold blue]")
        start = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()

            # Create pyproject.toml
            pyproject = project / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "dogfood-test"
version = "0.1.0"
requires-python = ">=3.8"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

            # Initialize project
            success, _, _ = self.run_command("deps", "lock", cwd=project)
            if not success:
                self.results["project_cycle"] = (False, time.time() - start, "Failed to lock deps")
                return False

            # Add dependency
            success, _, _ = self.run_command("deps", "add", "rich", cwd=project)
            if not success:
                self.results["project_cycle"] = (False, time.time() - start, "Failed to add dep")
                return False

            # List dependencies
            success, stdout, _ = self.run_command("deps", "list", cwd=project)
            if not success or "rich" not in stdout:
                self.results["project_cycle"] = (False, time.time() - start, "Dep not listed")
                return False

            # Build wheel
            success, _, _ = self.run_command("build", "wheel", cwd=project)
            duration = time.time() - start

            if success and (project / "dist").exists():
                console.print("[green]✓[/green] Project cycle completed")
                self.results["project_cycle"] = (True, duration, "Full cycle successful")
                return True
            console.print("[red]✗[/red] Project cycle failed")
            self.results["project_cycle"] = (False, duration, "Build failed")
            return False

    def test_recursive_call(self) -> bool:
        """Test uvmgr calling uvmgr recursively."""
        console.print("\n[bold blue]Test 5: Recursive uvmgr call[/bold blue]")
        start = time.time()

        # Create a script that calls uvmgr
        script = """
import subprocess
result = subprocess.run(["uvmgr", "--version"], capture_output=True, text=True)
print(f"Inner call: {result.returncode}")
exit(result.returncode)
"""

        # Run the script with uvmgr's Python
        success, stdout, _ = self.run_command("run", "python", "-c", script)
        duration = time.time() - start

        if success and "Inner call: 0" in stdout:
            console.print("[green]✓[/green] Recursive call works")
            self.results["recursive"] = (True, duration, "Recursive call successful")
            return True
        console.print("[red]✗[/red] Recursive call failed")
        self.results["recursive"] = (False, duration, "Recursive call failed")
        return False

    def test_performance(self) -> bool:
        """Test command performance benchmarks."""
        console.print("\n[bold blue]Test 6: Performance benchmarks[/bold blue]")

        benchmarks = {}

        # Benchmark help (should be < 0.5s)
        start = time.time()
        success, _, _ = self.run_command("--help")
        help_time = time.time() - start
        benchmarks["help"] = help_time

        # Benchmark deps list in temp project
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "perf_test"
            project.mkdir()

            # Minimal pyproject.toml
            (project / "pyproject.toml").write_text("""
[project]
name = "perf-test"
version = "0.1.0"
dependencies = ["rich"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

            # Lock first
            self.run_command("deps", "lock", cwd=project)

            # Benchmark deps list
            start = time.time()
            success, _, _ = self.run_command("deps", "list", cwd=project)
            list_time = time.time() - start
            benchmarks["deps_list"] = list_time

        # Check performance
        help_ok = benchmarks["help"] < 1.0  # Help under 1s
        list_ok = benchmarks["deps_list"] < 3.0  # List under 3s

        if help_ok and list_ok:
            console.print("[green]✓[/green] Performance acceptable")
            console.print(f"  Help: {benchmarks['help']:.3f}s")
            console.print(f"  Deps list: {benchmarks['deps_list']:.3f}s")
            self.results["performance"] = (True, 0, f"Help={help_time:.3f}s, List={list_time:.3f}s")
            return True
        console.print("[red]✗[/red] Performance issues detected")
        self.results["performance"] = (False, 0, "Performance below threshold")
        return False

    def generate_report(self) -> None:
        """Generate final test report."""
        console.print("\n[bold yellow]Dogfooding Test Report[/bold yellow]")
        console.print("=" * 50)

        # Summary table
        table = Table(title="Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Details", style="white")

        total_passed = 0
        for test_name, (passed, duration, details) in self.results.items():
            status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
            table.add_row(test_name, status, f"{duration:.3f}s", details)
            if passed:
                total_passed += 1

        console.print(table)

        # Overall summary
        total_tests = len(self.results)
        total_time = time.time() - self.start_time
        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        console.print(f"\nTotal Tests: {total_tests}")
        console.print(f"Passed: {total_passed}")
        console.print(f"Failed: {total_tests - total_passed}")
        console.print(f"Pass Rate: {pass_rate:.1f}%")
        console.print(f"Total Time: {total_time:.2f}s")

        # Save JSON report
        report_file = Path("dogfood_report.json")
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_tests - total_passed,
            "pass_rate": pass_rate,
            "total_time": total_time,
            "results": {
                name: {
                    "passed": passed,
                    "duration": duration,
                    "details": details
                }
                for name, (passed, duration, details) in self.results.items()
            }
        }

        report_file.write_text(json.dumps(report_data, indent=2))
        console.print(f"\nDetailed report saved to: {report_file}")

    def run(self) -> int:
        """Run all dogfooding tests."""
        console.print("[bold cyan]Starting uvmgr Dogfooding Test Loop[/bold cyan]")
        console.print("Testing uvmgr using uvmgr itself...\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Running tests...", total=6)

            # Run all tests
            tests = [
                ("Testing help command...", self.test_self_help),
                ("Testing version command...", self.test_self_version),
                ("Running self-tests...", self.test_self_tests),
                ("Testing project cycle...", self.test_project_cycle),
                ("Testing recursive calls...", self.test_recursive_call),
                ("Running benchmarks...", self.test_performance),
            ]

            for description, test_func in tests:
                progress.update(task, description=description)
                test_func()
                progress.advance(task)

        # Generate report
        self.generate_report()

        # Return exit code based on results
        all_passed = all(passed for passed, _, _ in self.results.values())
        return 0 if all_passed else 1


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run uvmgr dogfooding test loop")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    runner = DogfoodRunner(verbose=args.verbose)
    sys.exit(runner.run())


if __name__ == "__main__":
    main()
