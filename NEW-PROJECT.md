# Creating a New Typer CLI Project

This guide explains how to create a new Typer-based CLI project following the structure and best practices of uvmgr.

## Project Structure Overview

```
mycli/
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Container definition
├── pyproject.toml         # Project metadata and dependencies
├── README.md             # Project documentation
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── .copier-answers.yml   # Copier template answers
├── src/
│   └── mycli/            # Main package
│       ├── __init__.py
│       ├── cli.py        # Root CLI application
│       ├── cli_utils.py  # CLI utility functions
│       ├── main.py       # Entry point
│       ├── __main__.py   # Python -m entry point
│       ├── logging_config.py # Logging setup
│       ├── commands/     # Command modules
│       │   ├── __init__.py
│       │   └── [command].py
│       ├── core/         # Core utilities
│       │   ├── __init__.py
│       │   ├── shell.py
│       │   ├── telemetry.py
│       │   ├── config.py
│       │   ├── fs.py
│       │   ├── process.py
│       │   ├── venv.py
│       │   ├── paths.py
│       │   ├── cache.py
│       │   ├── concurrency.py
│       │   ├── history.py
│       │   ├── lint.py
│       │   └── clipboard.py
│       ├── ops/          # Business logic
│       │   ├── __init__.py
│       │   └── [operation].py
│       └── runtime/      # Runtime implementations
│           ├── __init__.py
│           └── [runtime].py
├── tests/                # Test suite
│   ├── __init__.py
│   ├── e2e/             # End-to-end tests
│   └── test_*.py
├── docs/                # Documentation
├── reports/             # Test reports and coverage
├── examples/            # Example usage
└── catalog/             # Data catalogs
```

## Step 1: Project Setup

1. Create a new project using Copier (recommended) or manually:

```bash
# Using Copier (recommended)
uvmgr new mycli

# Or manually
mkdir mycli && cd mycli
```

2. Initialize the project with `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"

[project]
name = "mycli"
version = "0.1.0"
description = "My CLI Application"
readme = "README.md"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
requires-python = ">=3.12,<4.0"
dependencies = [
    "typer>=0.15.1",
    "rich>=14.0.0",
    "click>=8.0.0",
    "pytest>=8.3.5",
    "ruff>=0.11.11",
]

[project.scripts]
mycli = "mycli.cli:app"

[project.urls]
homepage = "https://github.com/yourusername/mycli"
source = "https://github.com/yourusername/mycli"
documentation = "https://github.com/yourusername/mycli"

[dependency-groups]
dev = [
    "commitizen>=4.3.0",
    "coverage[toml]>=7.6.10",
    "mypy>=1.14.1",
    "pdoc>=15.0.1",
    "pre-commit>=4.0.1",
    "pytest>=8.3.4",
    "pytest-mock>=3.14.0",
    "pytest-xdist>=3.6.1",
]

[tool.ruff]
fix = true
line-length = 100
src = ["src", "tests"]
target-version = "py312"

[tool.ruff.lint]
select = [
    "A", "ASYNC", "B", "C4", "C90", "D", "DTZ", "E", "F", "FLY", "FURB",
    "I", "ISC", "LOG", "N", "NPY", "PERF", "PGH", "PIE", "PL", "PT", "Q",
    "RET", "RUF", "RSE", "SIM", "TID", "UP", "W", "YTT",
]
ignore = ["D203", "D213", "E501", "PGH002", "PGH003", "RET504", "S101", "S307"]

[tool.mypy]
junit_xml = "reports/mypy.xml"
ignore_missing_imports = true
pretty = true
show_column_numbers = true
show_error_codes = true
show_error_context = true
warn_unreachable = true

[tool.pytest.ini_options]
addopts = "--color=yes --doctest-modules --exitfirst --failed-first --verbosity=2 --junitxml=reports/pytest.xml"
testpaths = ["src", "tests"]
xfail_strict = true

[tool.coverage.run]
branch = true
command_line = "--module pytest"
data_file = "reports/.coverage"
source = ["src"]

[tool.coverage.report]
precision = 1
show_missing = true
skip_covered = true

[tool.coverage.xml]
output = "reports/coverage.xml"
```

## Step 2: Core Structure

### 1. Root CLI (`src/mycli/cli.py`)

```python
"""
mycli.cli
=========

Root Typer application.

• Sets up logging once (plain `logging` + optional OpenTelemetry)
• Adds a global `--json / -j` flag
• Dynamically mounts every sub-command package found in **mycli.commands**
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

import typer

from mycli.core.shell import colour, dump_json
from mycli.logging_config import setup_logging
from mycli.cli_utils import handle_cli_exception

# ──────────────────────────────────────────────────────────────────────────────
#  Logging bootstrap (idempotent)
# ──────────────────────────────────────────────────────────────────────────────
setup_logging()

# ──────────────────────────────────────────────────────────────────────────────
#  Root Typer application
# ──────────────────────────────────────────────────────────────────────────────
app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    help="**mycli** – Your CLI description.",
    context_settings={"allow_extra_args": True},
)

# Record JSON preference in ctx.meta so sub-commands can honour it -------------
def _json_cb(ctx: typer.Context, value: bool):
    if value:
        ctx.meta["json"] = True

@app.callback()
def _root(
    ctx: typer.Context,
    json_: bool = typer.Option(
        False,
        "--json",
        "-j",
        callback=_json_cb,
        is_eager=True,
        help="Print machine-readable JSON and exit",
    ),
):
    """Callback only sets the JSON flag – no other side-effects."""

# ──────────────────────────────────────────────────────────────────────────────
#  Mount every sub-command defined in *mycli.commands*
# ──────────────────────────────────────────────────────────────────────────────
commands_pkg = importlib.import_module("mycli.commands")

for verb in commands_pkg.__all__:
    mod = importlib.import_module(f"mycli.commands.{verb}")

    # Expect exactly one typer.Typer object in the module's globals ------------
    sub_app = next(
        (obj for obj in mod.__dict__.values() if isinstance(obj, typer.Typer)),
        None,
    )
    if sub_app is None:  # Fail fast during development
        raise ImportError(f"`{verb}` has no Typer sub-app")

    # Mount under the same name (convert _ to - for nicer CLI UX) --------------
    app.add_typer(sub_app, name=verb.replace("_", "-"))

if __name__ == "__main__":
    import sys
    debug = "--debug" in sys.argv
    try:
        # ... main CLI logic ...
        pass
    except Exception as e:
        handle_cli_exception(e, debug=debug)
```

### 2. CLI Utilities (`src/mycli/cli_utils.py`)

```python
"""
mycli.cli_utils
==============

CLI utility functions for error handling and common operations.
"""

import sys
from typing import Any

import typer

def handle_cli_exception(exc: Exception, debug: bool = False) -> None:
    """Handle CLI exceptions with appropriate error reporting."""
    if debug:
        raise exc
    else:
        typer.echo(f"Error: {exc}", err=True)
        sys.exit(1)
```

### 3. Logging Configuration (`src/mycli/logging_config.py`)

```python
"""
mycli.logging_config
===================

Logging configuration setup.
"""

import logging
from typing import Optional

def setup_logging(level: str = "INFO", otel: Optional[bool] = None) -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
```

### 4. Main Entry Point (`src/mycli/main.py`)

```python
"""
mycli.main
==========

Main entry point for the application.
"""

import sys
from pathlib import Path

from mycli.cli import app

def main() -> None:
    """Main entry point."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    app()

if __name__ == "__main__":
    main()
```

### 5. Module Entry Point (`src/mycli/__main__.py`)

```python
"""
mycli.__main__
==============

Entry point for `python -m mycli`.
"""

from mycli.main import main

if __name__ == "__main__":
    main()
```

## Step 3: Command Structure

### 1. Commands Package (`src/mycli/commands/__init__.py`)

```python
"""
mycli.commands
=============

Package marker + lazy loader for every Typer sub-app.

Nothing here is imported by end-users directly; the root CLI (`mycli.cli`)
resolves sub-modules via ``importlib.import_module`` on demand.  This file:

1. Documents which command modules exist.
2. Provides *auto-completion* / IDE discovery through ``__all__``.
3. Implements a `__getattr__` lazy loader so
   ``from mycli.commands import example`` Just-Works™ without importing
   heavy optional dependencies at start-up.

Add new verb modules to **__all__** when you create them.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final, List

__all__: Final[List[str]] = [
    "example",
    "build",
    "test",
    # Add more commands here
]

_PACKAGE_PREFIX = __name__ + "."

def __getattr__(name: str) -> ModuleType:
    """
    Lazy-import sub-modules so we don't pay the cost (or trigger missing
    extras) unless the command group is actually used.
    """
    if name not in __all__:
        raise AttributeError(name)
    module = importlib.import_module(_PACKAGE_PREFIX + name)
    setattr(sys.modules[__name__], name, module)
    return module
```

### 2. Example Command (`src/mycli/commands/example.py`)

```python
"""
mycli.commands.example
=====================

Example command implementation.
"""

import typer
from rich.console import Console

from mycli.ops.example import ExampleOperation
from mycli.core.shell import maybe_json

app = typer.Typer(help="Example command description.")
console = Console()

@app.command()
def run(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Name to greet"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Run the example command."""
    op = ExampleOperation()
    result = op.execute(name=name, verbose=verbose)
    
    # Handle JSON output
    maybe_json(ctx, result)
    
    # Rich console output
    console.print(f"[green]Hello, {name}![/green]")
```

### 3. Build Command (`src/mycli/commands/build.py`)

```python
"""
mycli.commands.build
===================

Build command implementation.
"""

import typer
from rich.console import Console

from mycli.ops.build import BuildOperation
from mycli.core.shell import maybe_json

app = typer.Typer(help="Build operations.")
console = Console()

@app.command()
def project(
    ctx: typer.Context,
    target: str = typer.Option("wheel", "--target", "-t", help="Build target"),
    clean: bool = typer.Option(False, "--clean", help="Clean before building"),
):
    """Build the project."""
    op = BuildOperation()
    result = op.build_project(target=target, clean=clean)
    
    maybe_json(ctx, result)
    console.print(f"[green]Built {target} successfully![/green]")
```

## Step 4: Core Utilities

### 1. Shell Utilities (`src/mycli/core/shell.py`)

```python
"""
mycli.core.shell
===============

Shell and output utilities.
"""

import json
import sys
from typing import Any, Dict

import typer

def colour(text: str, color: str = "green") -> str:
    """Add color to text."""
    return f"[{color}]{text}[/{color}]"

def dump_json(data: Any) -> None:
    """Dump data as JSON to stdout."""
    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")

def maybe_json(ctx: typer.Context, data: Dict[str, Any]) -> None:
    """Output data as JSON if --json flag is set."""
    if ctx.meta.get("json"):
        dump_json(data)
        raise typer.Exit()
```

### 2. File System Utilities (`src/mycli/core/fs.py`)

```python
"""
mycli.core.fs
============

File system utilities.
"""

import shutil
from pathlib import Path
from typing import Optional

def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def safe_remove(path: Path) -> None:
    """Safely remove a file or directory."""
    if path.exists():
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)

def find_files(pattern: str, root: Optional[Path] = None) -> list[Path]:
    """Find files matching pattern."""
    if root is None:
        root = Path.cwd()
    return list(root.glob(pattern))
```

### 3. Process Utilities (`src/mycli/core/process.py`)

```python
"""
mycli.core.process
=================

Process execution utilities.
"""

import subprocess
from pathlib import Path
from typing import List, Optional

def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture_output,
        check=check,
        text=True,
    )
```

## Step 5: Operations Layer

### 1. Example Operation (`src/mycli/ops/example.py`)

```python
"""
mycli.ops.example
================

Business logic for the example command.
"""

from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class ExampleOperation:
    """Example operation implementation."""
    
    def execute(self, name: str, verbose: bool = False) -> Dict[str, Any]:
        """Execute the example operation."""
        # Implement business logic here
        return {
            "status": "success",
            "message": f"Hello, {name}!",
            "verbose": verbose,
        }
```

### 2. Build Operation (`src/mycli/ops/build.py`)

```python
"""
mycli.ops.build
==============

Build operation business logic.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from mycli.core.process import run_command

@dataclass
class BuildOperation:
    """Build operation implementation."""
    
    def build_project(self, target: str = "wheel", clean: bool = False) -> Dict[str, Any]:
        """Build the project."""
        # Implement build logic here
        if clean:
            # Clean build artifacts
            pass
        
        # Run build command
        result = run_command(["python", "-m", "build", "--wheel"])
        
        return {
            "status": "success",
            "target": target,
            "output": result.stdout,
        }
```

## Step 6: Runtime Layer

### 1. Runtime Base (`src/mycli/runtime/__init__.py`)

```python
"""
mycli.runtime
============

Runtime implementations for different execution contexts.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class Runtime(ABC):
    """Base runtime class."""
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the runtime."""
        pass

class LocalRuntime(Runtime):
    """Local execution runtime."""
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute locally."""
        return {"runtime": "local", "status": "success"}
```

## Step 7: Testing Structure

### 1. Test Configuration (`tests/conftest.py`)

```python
"""
Test configuration and fixtures.
"""

import pytest
from typer.testing import CliRunner

@pytest.fixture
def cli_runner():
    """Create a Typer CLI runner for testing."""
    return CliRunner()

@pytest.fixture
def mock_operation(monkeypatch):
    """Mock the example operation."""
    def mock_execute(*args, **kwargs):
        return {"status": "success", "message": "Mocked response"}
    
    monkeypatch.setattr("mycli.ops.example.ExampleOperation.execute", mock_execute)
```

### 2. Command Tests (`tests/test_example.py`)

```python
"""
Tests for the example command.
"""

import pytest
from typer.testing import CliRunner

from mycli.cli import app

def test_example_command(cli_runner: CliRunner):
    """Test the example command."""
    result = cli_runner.invoke(app, ["example", "run", "World"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.stdout

def test_example_command_json(cli_runner: CliRunner):
    """Test the example command with JSON output."""
    result = cli_runner.invoke(app, ["example", "run", "World", "--json"])
    assert result.exit_code == 0
    assert '"status": "success"' in result.stdout
```

## Step 8: Development Tools

### 1. Pre-commit Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
    -   id: ruff
        args: [--fix]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
    -   id: mypy
        additional_dependencies: [types-all]
```

### 2. Copier Template Answers (`.copier-answers.yml`)

```yaml
# Answers to Copier template questions
project_name: mycli
project_description: My CLI Application
author_name: Your Name
author_email: your.email@example.com
python_version: "3.12"
```

## Step 9: Container Support

### 1. Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python package
COPY . .
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["mycli"]
```

### 2. Docker Compose

```yaml
version: '3.8'

services:
  mycli:
    build: .
    volumes:
      - .:/app
    environment:
      - PYTHONPATH=/app
```

## Best Practices

1. **Command Organization**
   - Keep commands modular and focused
   - Use the `commands/` directory for CLI definitions
   - Implement business logic in `ops/`
   - Place shared utilities in `core/`
   - Use `runtime/` for execution context implementations

2. **Error Handling**
   - Use custom exceptions for business logic
   - Implement graceful error handling in commands
   - Provide meaningful error messages
   - Use the `handle_cli_exception` utility

3. **Testing**
   - Write tests for all commands
   - Use fixtures for common setup
   - Test both success and error cases
   - Include integration tests in `tests/e2e/`

4. **Documentation**
   - Document all commands and options
   - Include examples in docstrings
   - Keep README.md up to date
   - Use type hints consistently

5. **Development Workflow**
   - Use pre-commit hooks
   - Run tests before committing
   - Keep dependencies up to date
   - Follow semantic versioning
   - Use `uvmgr` for package management

6. **Project Structure**
   - Follow the established directory structure
   - Use lazy loading for commands
   - Implement proper logging
   - Support JSON output mode
   - Use Rich for beautiful CLI output

## Usage Example

```bash
# Install the package
pip install -e .

# Run the CLI
mycli --help
mycli example run World
mycli example run World --json

# Development
pre-commit install
pytest
ruff check .
mypy .
```

## Next Steps

1. Add more commands following the same pattern
2. Implement additional core utilities as needed
3. Add CI/CD pipeline configuration
4. Create comprehensive documentation
5. Add more test coverage
6. Implement runtime-specific features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Add appropriate license information] 