"""E2E test configuration and fixtures for uvmgr dogfooding tests."""
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from rich.console import Console

console = Console()


@pytest.fixture
def temp_project() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()

        # Create basic project structure
        (project_path / "src").mkdir()
        (project_path / "tests").mkdir()

        # Create minimal pyproject.toml
        pyproject = project_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
description = "Test project for uvmgr e2e tests"
requires-python = ">=3.8"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

        yield project_path

        # Cleanup is automatic with tempfile


@pytest.fixture
def uvmgr_runner(monkeypatch):
    """Fixture for running uvmgr commands in tests."""
    def run(*args: str, cwd: Path | None = None, check: bool = True, **kwargs) -> subprocess.CompletedProcess:
        """Run uvmgr command with arguments."""
        cmd = ["uvmgr"] + list(args)

        console.print(f"[blue]Running:[/blue] {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            **kwargs
        )

        if check and result.returncode != 0:
            console.print(f"[red]Command failed:[/red] {result.stderr}")
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        return result

    return run


@pytest.fixture
def sample_python_module() -> str:
    """Sample Python module content for testing."""
    return '''"""Sample module for testing."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value: int) -> int:
        """Add to result."""
        self.result += value
        return self.result
'''


@pytest.fixture
def sample_test_module() -> str:
    """Sample test module content."""
    return '''"""Tests for sample module."""
import pytest
from sample import add, multiply, Calculator


def test_add():
    """Test addition."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_multiply():
    """Test multiplication."""
    assert multiply(2, 3) == 6
    assert multiply(-2, 3) == -6


class TestCalculator:
    """Test calculator class."""
    
    def test_init(self):
        """Test initialization."""
        calc = Calculator()
        assert calc.result == 0
    
    def test_add(self):
        """Test add method."""
        calc = Calculator()
        assert calc.add(5) == 5
        assert calc.add(3) == 8
'''


@contextmanager
def timer():
    """Context manager for timing operations."""
    class Timer:
        def __init__(self):
            self.elapsed = 0.0

    t = Timer()
    start = time.perf_counter()

    try:
        yield t
    finally:
        t.elapsed = time.perf_counter() - start


def assert_project_structure(project_path: Path) -> None:
    """Assert that project has expected structure."""
    assert project_path.exists()
    assert (project_path / "pyproject.toml").exists()
    assert (project_path / "src").is_dir()
    assert (project_path / "tests").is_dir()


def assert_venv_exists(project_path: Path) -> None:
    """Assert that virtual environment exists."""
    venv_path = project_path / ".venv"
    assert venv_path.exists()
    assert (venv_path / "bin" / "python").exists() or (venv_path / "Scripts" / "python.exe").exists()


def assert_build_artifacts(project_path: Path) -> None:
    """Assert that build artifacts exist."""
    dist_path = project_path / "dist"
    assert dist_path.exists()

    # Check for wheel file
    wheels = list(dist_path.glob("*.whl"))
    assert len(wheels) > 0, "No wheel files found in dist/"


def create_sample_module(project_path: Path, module_content: str, test_content: str) -> None:
    """Create sample Python module and test in project."""
    # Create module
    module_path = project_path / "src" / "sample.py"
    module_path.write_text(module_content)

    # Create test
    test_path = project_path / "tests" / "test_sample.py"
    test_path.write_text(test_content)

    # Create __init__.py files
    (project_path / "src" / "__init__.py").touch()
    (project_path / "tests" / "__init__.py").touch()


@pytest.fixture
def mock_telemetry():
    """Mock telemetry for testing."""
    traces = []

    class MockTelemetry:
        def capture_trace(self, name: str, attributes: dict[str, Any]):
            traces.append({"name": name, "attributes": attributes})

        def get_traces(self):
            return traces

        def clear(self):
            traces.clear()

    return MockTelemetry()


def assert_command_success(result: subprocess.CompletedProcess) -> None:
    """Assert that command completed successfully."""
    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"


def assert_output_contains(result: subprocess.CompletedProcess, text: str) -> None:
    """Assert that command output contains text."""
    combined = result.stdout + result.stderr
    assert text in combined, f"Expected '{text}' in output, got: {combined}"


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch, tmp_path):
    """Isolate test environment from user's system."""
    # Use temporary home directory
    test_home = tmp_path / "home"
    test_home.mkdir()
    monkeypatch.setenv("HOME", str(test_home))

    # Use temporary cache
    test_cache = tmp_path / "cache"
    test_cache.mkdir()
    monkeypatch.setenv("UVMGR_CACHE_DIR", str(test_cache))

    # Disable any system config
    monkeypatch.setenv("UVMGR_NO_CONFIG", "1")

    # Ensure clean uv cache
    monkeypatch.setenv("UV_CACHE_DIR", str(tmp_path / "uv_cache"))
