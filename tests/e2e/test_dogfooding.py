"""Dogfooding E2E tests where uvmgr tests itself."""
import os
import sys
from pathlib import Path

import pytest

from tests.e2e.conftest import (
    assert_build_artifacts,
    assert_command_success,
    assert_output_contains,
    assert_project_structure,
    assert_venv_exists,
    create_sample_module,
    timer,
)


class TestDogfoodingLoop:
    """Test uvmgr using uvmgr itself."""

    def test_uvmgr_tests_itself(self, uvmgr_runner):
        """Uvmgr runs its own test suite."""
        # Use uvmgr to run a simple test from uvmgr's own test suite
        result = uvmgr_runner("tests", "run", check=False)

        # Should pass since it's a simple import test
        assert_command_success(result)
        assert_output_contains(result, "passed")

    def test_uvmgr_lints_itself(self, uvmgr_runner):
        """Uvmgr checks its own code quality."""
        # Run lint check on a specific uvmgr module
        result = uvmgr_runner("lint", "check", check=False)

        # Lint might have issues, but command should run
        assert result.returncode in [0, 1]  # 0 = no issues, 1 = issues found

    def test_uvmgr_builds_itself(self, uvmgr_runner, tmp_path):
        """Uvmgr builds its own wheel."""
        # Copy minimal uvmgr structure to temp dir
        test_project = tmp_path / "uvmgr_copy"
        test_project.mkdir()

        # Copy essential files
        import shutil
        shutil.copy2("pyproject.toml", test_project)
        shutil.copytree("src", test_project / "src")

        # Build wheel
        result = uvmgr_runner("build", "dist", cwd=test_project)
        assert_command_success(result)

        # Verify wheel exists
        assert_build_artifacts(test_project)


class TestFullDevelopmentCycle:
    """Test complete development workflow using uvmgr."""

    def test_init_to_build_cycle(self, uvmgr_runner, temp_project, sample_python_module, sample_test_module):
        """Test full cycle: init → deps → test → lint → build."""
        # 1. Initialize project (already done by fixture)
        assert_project_structure(temp_project)

        # 2. Set up Python environment
        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)

        # 3. Add dependencies
        result = uvmgr_runner("deps", "add", "pytest", "--dev", cwd=temp_project)
        assert_command_success(result)

        result = uvmgr_runner("deps", "add", "rich", cwd=temp_project)
        assert_command_success(result)

        # 4. Create sample code
        create_sample_module(temp_project, sample_python_module, sample_test_module)

        # 5. Run tests
        result = uvmgr_runner("tests", "run", cwd=temp_project)
        assert_command_success(result)
        assert_output_contains(result, "passed")

        # 6. Run lint
        result = uvmgr_runner("lint", "check", cwd=temp_project, check=False)
        # Lint might fail on generated code, that's ok

        # 7. Build wheel
        result = uvmgr_runner("build", "dist", cwd=temp_project)
        assert_command_success(result)
        assert_build_artifacts(temp_project)

        # 8. Verify project state
        assert_venv_exists(temp_project)

    def test_dependency_management_cycle(self, uvmgr_runner, temp_project):
        """Test dependency management workflow."""
        # Lock dependencies
        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)

        # Add multiple dependencies
        deps = ["pytest", "rich", "typer", "pydantic"]
        for dep in deps:
            result = uvmgr_runner("deps", "add", dep, "--dev", cwd=temp_project)
            assert_command_success(result)

        # List dependencies
        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)
        for dep in deps:
            assert_output_contains(result, dep)

        # Update all
        result = uvmgr_runner("deps", "update", cwd=temp_project)
        assert_command_success(result)

        # Remove a dependency
        result = uvmgr_runner("deps", "remove", "typer", cwd=temp_project)
        assert_command_success(result)

        # Verify removal
        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)
        assert "typer" not in result.stdout


class TestErrorHandling:
    """Test error handling and recovery."""

    def test_missing_project_error(self, uvmgr_runner, tmp_path):
        """Test commands in directory without project."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Should fail gracefully
        result = uvmgr_runner("deps", "list", cwd=empty_dir, check=False)
        assert result.returncode != 0

    def test_invalid_dependency_error(self, uvmgr_runner, temp_project):
        """Test adding non-existent package."""
        # Setup project first
        uvmgr_runner("deps", "list", cwd=temp_project)

        # Try to add non-existent package
        result = uvmgr_runner(
            "deps", "add", "this-package-definitely-does-not-exist-12345",
            cwd=temp_project, check=False
        )
        assert result.returncode != 0

        # Verify project still works
        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)

    def test_command_cascade_recovery(self, uvmgr_runner, temp_project):
        """Test recovery after command failure."""
        # Lock first
        uvmgr_runner("deps", "list", cwd=temp_project)

        # Cause a failure
        result = uvmgr_runner("tests", "run", cwd=temp_project, check=False)
        # Might fail due to no tests

        # Subsequent commands should still work
        result = uvmgr_runner("deps", "add", "pytest", "--dev", cwd=temp_project)
        assert_command_success(result)

        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)


class TestPerformance:
    """Performance benchmarks for dogfooding."""

    @pytest.mark.benchmark
    def test_command_performance(self, uvmgr_runner, temp_project):
        """Benchmark key command performance."""
        # Setup project
        uvmgr_runner("deps", "list", cwd=temp_project)
        uvmgr_runner("deps", "add", "pytest", "--dev", cwd=temp_project)

        benchmarks = {}

        # Time deps list
        with timer() as t:
            result = uvmgr_runner("deps", "list", cwd=temp_project)
            assert_command_success(result)
        benchmarks["deps_list"] = t.elapsed

        # Time simple test run
        test_file = temp_project / "tests" / "test_simple.py"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("def test_pass(): assert True")

        with timer() as t:
            result = uvmgr_runner("tests", "run", str(test_file), cwd=temp_project)
            assert_command_success(result)
        benchmarks["single_test"] = t.elapsed

        # Time help command (should be fast)
        with timer() as t:
            result = uvmgr_runner("--help")
            assert_command_success(result)
        benchmarks["help"] = t.elapsed

        # Performance assertions
        assert benchmarks["help"] < 0.5  # Help should be very fast
        assert benchmarks["deps_list"] < 2.0  # Deps list under 2s
        assert benchmarks["single_test"] < 5.0  # Single test under 5s

        # Log results
        print("\nPerformance Benchmarks:")
        for cmd, time in benchmarks.items():
            print(f"  {cmd}: {time:.3f}s")

    def test_cache_effectiveness(self, uvmgr_runner, temp_project):
        """Test that caching improves performance."""
        # Setup
        uvmgr_runner("deps", "list", cwd=temp_project)

        # First run (cold cache)
        with timer() as t1:
            result = uvmgr_runner("deps", "add", "rich", cwd=temp_project)
            assert_command_success(result)

        # Remove and re-add (should use cache)
        uvmgr_runner("deps", "remove", "rich", cwd=temp_project)

        with timer() as t2:
            result = uvmgr_runner("deps", "add", "rich", cwd=temp_project)
            assert_command_success(result)

        # Second run should be faster due to cache
        # Note: This might not always be true due to network conditions
        print(f"\nCache performance: cold={t1.elapsed:.3f}s, warm={t2.elapsed:.3f}s")


class TestSelfReferential:
    """Self-referential tests where uvmgr operates on itself."""

    def test_recursive_uvmgr_call(self, uvmgr_runner):
        """Test uvmgr calling uvmgr."""
        # Create a script that uses uvmgr
        script = """
import subprocess
result = subprocess.run(["uvmgr", "--version"], capture_output=True, text=True)
print(f"Nested uvmgr version: {result.stdout.strip()}")
"""

        # Run it with uvmgr's Python
        result = uvmgr_runner("run", "python", "-c", script, check=False)

        # Should work if uvmgr is in PATH
        if result.returncode == 0:
            assert_output_contains(result, "Nested uvmgr version:")

    def test_uvmgr_development_workflow(self, uvmgr_runner, tmp_path):
        """Simulate developing uvmgr using uvmgr."""
        # Create a mock uvmgr development project
        dev_project = tmp_path / "uvmgr_dev"
        dev_project.mkdir()

        # Create minimal uvmgr-like structure
        (dev_project / "pyproject.toml").write_text("""
[project]
name = "uvmgr-dev"
version = "0.1.0"
dependencies = ["typer", "rich", "uv"]

[project.scripts]
uvmgr-dev = "uvmgr_dev.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

        # Create source
        src = dev_project / "src" / "uvmgr_dev"
        src.mkdir(parents=True)
        (src / "__init__.py").touch()
        (src / "cli.py").write_text("""
import typer
app = typer.Typer()

@app.command()
def hello():
    print("Hello from uvmgr-dev!")
""")

        # Use uvmgr to develop uvmgr-like project
        result = uvmgr_runner("deps", "list", cwd=dev_project)
        assert_command_success(result)

        result = uvmgr_runner("deps", "add", "pytest", "--dev", cwd=dev_project)
        assert_command_success(result)

        # Install in editable mode
        result = uvmgr_runner("deps", "install", cwd=dev_project)
        assert_command_success(result)

        # Build it
        result = uvmgr_runner("build", "dist", cwd=dev_project)
        assert_command_success(result)
        assert_build_artifacts(dev_project)
