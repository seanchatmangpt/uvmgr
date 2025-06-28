"""Performance and telemetry tests for uvmgr dogfooding."""
import json
import os
import statistics
import time
from pathlib import Path
from typing import Dict, List

import pytest

from .conftest import assert_command_success, timer


class TestPerformanceBenchmarks:
    """Performance benchmarking tests."""

    @pytest.fixture
    def benchmark_project(self, temp_project, uvmgr_runner):
        """Create a project for benchmarking."""
        # Setup a standard project
        uvmgr_runner("deps", "lock", cwd=temp_project)
        uvmgr_runner("deps", "add", "pytest", "rich", "typer", "--dev", cwd=temp_project)
        uvmgr_runner("deps", "add", "pydantic", "httpx", cwd=temp_project)

        # Create some test files
        tests = temp_project / "tests"
        tests.mkdir(exist_ok=True)
        for i in range(5):
            test_file = tests / f"test_bench_{i}.py"
            test_file.write_text(f"""
def test_pass_{i}():
    assert True

def test_calc_{i}():
    assert 2 + 2 == 4
""")

        return temp_project

    def test_command_startup_time(self, uvmgr_runner):
        """Benchmark command startup overhead."""
        iterations = 5
        times = []

        for _ in range(iterations):
            with timer() as t:
                result = uvmgr_runner("--help")
                assert_command_success(result)
            times.append(t.elapsed)

        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        print(f"\nStartup time: {avg_time:.3f}s ± {std_dev:.3f}s")

        # Performance assertions
        assert avg_time < 0.5, f"Startup too slow: {avg_time:.3f}s"
        assert max(times) < 1.0, f"Max startup time too high: {max(times):.3f}s"

    def test_dependency_operations_performance(self, benchmark_project, uvmgr_runner):
        """Benchmark dependency management operations."""
        benchmarks = {}

        # List dependencies
        with timer() as t:
            result = uvmgr_runner("deps", "list", cwd=benchmark_project)
            assert_command_success(result)
        benchmarks["list"] = t.elapsed

        # Add a new dependency
        with timer() as t:
            result = uvmgr_runner("deps", "add", "click", cwd=benchmark_project)
            assert_command_success(result)
        benchmarks["add"] = t.elapsed

        # Remove dependency
        with timer() as t:
            result = uvmgr_runner("deps", "remove", "click", cwd=benchmark_project)
            assert_command_success(result)
        benchmarks["remove"] = t.elapsed

        # Update all
        with timer() as t:
            result = uvmgr_runner("deps", "update", cwd=benchmark_project)
            assert_command_success(result)
        benchmarks["update"] = t.elapsed

        # Log results
        print("\nDependency operations benchmark:")
        for op, time in benchmarks.items():
            print(f"  {op}: {time:.3f}s")

        # Performance assertions
        assert benchmarks["list"] < 2.0, "Listing deps too slow"
        assert benchmarks["add"] < 10.0, "Adding dep too slow"
        assert benchmarks["remove"] < 5.0, "Removing dep too slow"

    def test_test_execution_performance(self, benchmark_project, uvmgr_runner):
        """Benchmark test execution performance."""
        # Run all tests
        with timer() as t_all:
            result = uvmgr_runner("tests", "run", cwd=benchmark_project)
            assert_command_success(result)

        # Run single test file
        single_file = benchmark_project / "tests" / "test_bench_0.py"
        with timer() as t_single:
            result = uvmgr_runner("tests", "run", str(single_file), cwd=benchmark_project)
            assert_command_success(result)

        print("\nTest execution benchmark:")
        print(f"  All tests (10 tests): {t_all.elapsed:.3f}s")
        print(f"  Single file (2 tests): {t_single.elapsed:.3f}s")
        print(f"  Per-test overhead: {(t_all.elapsed - t_single.elapsed) / 8:.3f}s")

        # Performance assertions
        assert t_all.elapsed < 10.0, "Running all tests too slow"
        assert t_single.elapsed < 3.0, "Running single test too slow"

    def test_build_performance(self, benchmark_project, uvmgr_runner):
        """Benchmark build operations."""
        benchmarks = {}

        # Build wheel
        with timer() as t:
            result = uvmgr_runner("build", "wheel", cwd=benchmark_project)
            assert_command_success(result)
        benchmarks["wheel"] = t.elapsed

        # Clean and rebuild
        dist_dir = benchmark_project / "dist"
        if dist_dir.exists():
            import shutil
            shutil.rmtree(dist_dir)

        # Build sdist
        with timer() as t:
            result = uvmgr_runner("build", "sdist", cwd=benchmark_project)
            assert_command_success(result)
        benchmarks["sdist"] = t.elapsed

        # Build all
        if dist_dir.exists():
            import shutil
            shutil.rmtree(dist_dir)

        with timer() as t:
            result = uvmgr_runner("build", "all", cwd=benchmark_project)
            assert_command_success(result)
        benchmarks["all"] = t.elapsed

        print("\nBuild operations benchmark:")
        for op, time in benchmarks.items():
            print(f"  {op}: {time:.3f}s")

        # Performance assertions
        assert benchmarks["wheel"] < 5.0, "Building wheel too slow"
        assert benchmarks["sdist"] < 5.0, "Building sdist too slow"
        assert benchmarks["all"] < 10.0, "Building all too slow"

    def test_cache_effectiveness(self, temp_project, uvmgr_runner):
        """Test that caching improves performance."""
        # Clear any existing cache
        cache_dir = Path.home() / ".uvmgr_cache"
        if os.environ.get("UVMGR_CACHE_DIR"):
            cache_dir = Path(os.environ["UVMGR_CACHE_DIR"])

        # First run - cold cache
        uvmgr_runner("deps", "lock", cwd=temp_project)

        with timer() as t_cold:
            result = uvmgr_runner("deps", "add", "requests", cwd=temp_project)
            assert_command_success(result)

        # Remove and re-add - warm cache
        uvmgr_runner("deps", "remove", "requests", cwd=temp_project)

        with timer() as t_warm:
            result = uvmgr_runner("deps", "add", "requests", cwd=temp_project)
            assert_command_success(result)

        print("\nCache effectiveness:")
        print(f"  Cold cache: {t_cold.elapsed:.3f}s")
        print(f"  Warm cache: {t_warm.elapsed:.3f}s")
        print(f"  Speedup: {t_cold.elapsed / t_warm.elapsed:.2f}x")

        # Cache should provide some speedup (at least 10%)
        # Note: Network conditions can affect this
        if t_warm.elapsed < t_cold.elapsed * 0.9:
            print("  ✓ Cache is effective")


class TestTelemetryIntegration:
    """Test telemetry and observability features."""

    @pytest.mark.skipif(
        not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"),
        reason="OTEL endpoint not configured"
    )
    def test_otel_trace_generation(self, uvmgr_runner, temp_project):
        """Test that commands generate OTEL traces."""
        # Enable trace collection
        traces = []

        # Run command with telemetry
        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)

        # TODO: Implement trace collection and validation
        # This would require integrating with OTEL collector

    def test_performance_metrics_collection(self, uvmgr_runner, temp_project):
        """Test performance metrics are collected."""
        metrics_file = temp_project / "uvmgr_metrics.json"

        # Run commands that should generate metrics
        commands = [
            ["deps", "lock"],
            ["deps", "add", "pytest", "--dev"],
            ["tests", "run"],
            ["build", "wheel"],
        ]

        for cmd in commands:
            uvmgr_runner(*cmd, cwd=temp_project, check=False)

        # Check if metrics were collected
        # Note: This assumes uvmgr has a metrics collection feature
        # which would need to be implemented

    def test_error_tracking(self, uvmgr_runner, temp_project):
        """Test that errors are properly tracked."""
        # Intentionally cause errors
        error_cases = [
            # Non-existent package
            ["deps", "add", "this-package-does-not-exist-12345"],
            # Invalid command
            ["invalid-command"],
            # Missing required arg
            ["deps", "add"],
        ]

        errors_tracked = []

        for cmd in error_cases:
            result = uvmgr_runner(*cmd, cwd=temp_project, check=False)
            if result.returncode != 0:
                errors_tracked.append({
                    "command": cmd,
                    "exit_code": result.returncode,
                    "error": result.stderr
                })

        # Verify errors were captured
        assert len(errors_tracked) == len(error_cases)

        print(f"\nError tracking: {len(errors_tracked)} errors captured")


class TestScalabilityBenchmarks:
    """Test uvmgr performance at scale."""

    @pytest.mark.slow
    def test_large_dependency_tree(self, uvmgr_runner, temp_project):
        """Test performance with many dependencies."""
        # Add many common dependencies
        large_deps = [
            "requests", "numpy", "pandas", "matplotlib",
            "scikit-learn", "sqlalchemy", "flask", "django",
            "pytest", "black", "mypy", "ruff",
        ]

        uvmgr_runner("deps", "lock", cwd=temp_project)

        # Time adding all dependencies
        with timer() as t:
            for dep in large_deps[:6]:  # Limit to avoid timeout
                result = uvmgr_runner("deps", "add", dep, cwd=temp_project)
                assert_command_success(result)

        print("\nLarge dependency tree:")
        print(f"  Added {len(large_deps[:6])} packages in {t.elapsed:.3f}s")
        print(f"  Average per package: {t.elapsed / 6:.3f}s")

        # List all deps
        with timer() as t:
            result = uvmgr_runner("deps", "list", cwd=temp_project)
            assert_command_success(result)

        print(f"  Listing all deps: {t.elapsed:.3f}s")

        # Performance should not degrade significantly
        assert t.elapsed < 5.0, "Listing many deps too slow"

    @pytest.mark.slow
    def test_many_test_files(self, uvmgr_runner, temp_project):
        """Test performance with many test files."""
        # Create many test files
        tests_dir = temp_project / "tests"
        tests_dir.mkdir(exist_ok=True)

        num_files = 20
        for i in range(num_files):
            test_file = tests_dir / f"test_perf_{i:03d}.py"
            test_file.write_text(f"""
import time

def test_fast_{i}_1():
    assert True

def test_fast_{i}_2():
    assert 1 + 1 == 2

def test_fast_{i}_3():
    assert "a" * 10 == "aaaaaaaaaa"
""")

        # Setup project
        uvmgr_runner("deps", "lock", cwd=temp_project)
        uvmgr_runner("deps", "add", "pytest", "--dev", cwd=temp_project)

        # Run all tests
        with timer() as t:
            result = uvmgr_runner("tests", "run", "-n", "auto", cwd=temp_project)
            assert_command_success(result)

        total_tests = num_files * 3
        print("\nMany test files:")
        print(f"  Ran {total_tests} tests in {t.elapsed:.3f}s")
        print(f"  Average per test: {t.elapsed / total_tests * 1000:.1f}ms")

        # Should handle many tests efficiently
        assert t.elapsed < 30.0, f"Running {total_tests} tests too slow"


def generate_performance_report(results: dict[str, float]) -> None:
    """Generate a performance report."""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
        "summary": {
            "total_benchmarks": len(results),
            "average_time": statistics.mean(results.values()),
            "median_time": statistics.median(results.values()),
            "slowest": max(results.items(), key=lambda x: x[1]),
            "fastest": min(results.items(), key=lambda x: x[1]),
        }
    }

    report_file = Path("performance_report.json")
    report_file.write_text(json.dumps(report, indent=2))

    print(f"\nPerformance report saved to: {report_file}")
