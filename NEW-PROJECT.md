# Creating a New Typer CLI Project

This guide explains how to create a new Typer-based CLI project following the structure and best practices of uvmgr.

## Project Structure Overview

```
mycli/
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Container definition
├── pyproject.toml         # Project metadata and dependencies
├── README.md             # Project documentation
├── src/
│   └── mycli/            # Main package
│       ├── __init__.py
│       ├── cli.py        # Root CLI application
│       ├── commands/     # Command modules
│       │   ├── __init__.py
│       │   └── [command].py
│       ├── core/         # Core utilities
│       │   ├── __init__.py
│       │   └── [utility].py
│       ├── ops/          # Business logic
│       │   ├── __init__.py
│       │   └── [operation].py
│       └── runtime/      # Runtime implementations
│           ├── __init__.py
│           └── [runtime].py
└── tests/                # Test suite
    ├── __init__.py
    └── test_*.py
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
[project]
name = "mycli"
version = "0.1.0"
description = "My CLI Application"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "click>=8.0.0",
]
requires-python = ">=3.9"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py39"

[tool.mypy]
python_version = "3.9"
strict = true
```

## Step 2: Core Structure

### 1. Root CLI (`src/mycli/cli.py`)

```python
"""
mycli.cli
=========

Root Typer application with global options and command mounting.
"""

from __future__ import annotations

import importlib
from typing import Any

import typer

from mycli.core.telemetry import setup_logging

# Setup logging
setup_logging("INFO")

# Root application
app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    help="**mycli** – Your CLI description.",
)

# Global options
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
    """Global callback for shared options."""

# Mount commands
commands_pkg = importlib.import_module("mycli.commands")

for verb in commands_pkg.__all__:
    mod = importlib.import_module(f"mycli.commands.{verb}")
    sub_app = next(
        (obj for obj in mod.__dict__.values() if isinstance(obj, typer.Typer)),
        None,
    )
    if sub_app is None:
        raise ImportError(f"`{verb}` has no Typer sub-app")
    app.add_typer(sub_app, name=verb.replace("_", "-"))
```

### 2. Command Module (`src/mycli/commands/example.py`)

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

### 3. Operation Module (`src/mycli/ops/example.py`)

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

### 4. Core Utilities (`src/mycli/core/telemetry.py`)

```python
"""
mycli.core.telemetry
===================

Logging and telemetry setup.
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

## Step 3: Testing Structure

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

def test_example_command(cli_runner: CliRunner):
    """Test the example command."""
    result = cli_runner.invoke(app, ["run", "World"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.stdout

def test_example_command_json(cli_runner: CliRunner):
    """Test the example command with JSON output."""
    result = cli_runner.invoke(app, ["run", "World", "--json"])
    assert result.exit_code == 0
    assert '"status": "success"' in result.stdout
```

## Step 4: Development Tools

1. Add development dependencies to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "--cov=mycli --cov-report=xml:reports/coverage.xml"

[tool.ruff]
select = ["E", "F", "B", "I"]
ignore = []

[tool.mypy]
plugins = ["pydantic.mypy"]
```

2. Add pre-commit configuration (`.pre-commit-config.yaml`):

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

## Step 5: Container Support

### 1. Dockerfile

```dockerfile
FROM python:3.9-slim

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

2. **Error Handling**
   - Use custom exceptions for business logic
   - Implement graceful error handling in commands
   - Provide meaningful error messages

3. **Testing**
   - Write tests for all commands
   - Use fixtures for common setup
   - Test both success and error cases
   - Include integration tests

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Add appropriate license information] 