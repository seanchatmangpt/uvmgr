# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

uvmgr is a unified Python workflow engine that wraps around `uv` (a fast Python package manager) to streamline the entire Python development lifecycle. It provides a clean CLI interface with a three-layer architecture: Commands → Operations → Runtime.

## Key Development Commands

### Running Tests
```bash
# Run all tests with coverage
poe test

# Run tests using uvmgr
uvmgr tests run
uvmgr tests run --verbose

# Run tests with coverage report
uvmgr tests coverage

# Run a specific test file
pytest tests/test_cli.py

# Run a specific test function
pytest tests/test_cli.py::test_help
```

### Linting and Code Quality
```bash
# Run all linters and formatters
poe lint

# Run linting with uvmgr
uvmgr lint check
uvmgr lint fix
```

### Documentation
```bash
# Generate API documentation
poe docs
poe docs --docformat google --output-directory api-docs
```

### Building and Releasing
```bash
# Build Python distributions
uvmgr build dist
uvmgr build dist --upload  # Build and upload to PyPI

# Build standalone executable with PyInstaller
uvmgr build exe
uvmgr build exe --name myapp
uvmgr build exe --onedir  # Build as directory instead of single file
uvmgr build exe --debug  # Debug build issues

# Generate PyInstaller spec file for customization
uvmgr build spec
uvmgr build spec --name myapp --onefile

# Build uvmgr itself as executable (eat own dog food)
uvmgr build dogfood
uvmgr build dogfood --test  # Test the built executable
uvmgr build dogfood --version --platform  # Include version and platform in name

# Bump version (uses commitizen)
uvmgr release version patch
uvmgr release version minor
uvmgr release version major
```

## Architecture Overview

### Directory Structure
- `src/uvmgr/commands/` - CLI command implementations using Typer
- `src/uvmgr/ops/` - Business logic layer (pure functions, no side effects)
- `src/uvmgr/runtime/` - Runtime execution layer (subprocess calls, file I/O)
- `src/uvmgr/core/` - Core utilities (cache, config, shell, telemetry)
- `src/uvmgr/mcp/` - Model Context Protocol server for AI integration

### Key Design Patterns
1. **Command Pattern**: Each CLI command is a separate module in `commands/`
2. **Three-Layer Architecture**: Commands call ops, ops call runtime
3. **Dependency Injection**: Core utilities injected where needed
4. **Async Support**: Many operations support async execution

## Important Development Rules

From .cursorrules:
- **NEVER** run `uv`, `pytest`, `python`, `python3`, or `coverage` directly
- Always use `uvmgr` for package management operations
- Do not edit `pyproject.toml` file directly

## Testing Guidelines

- Tests are located in `tests/` directory
- Use pytest-mock for mocking subprocess calls
- Coverage reports are generated in `reports/` directory
- Tests should follow the pattern: `test_<module>.py`
- Use fixtures from `tests/fixtures/` for test data

## Adding New Commands

1. Create a new module in `src/uvmgr/commands/`
2. Define a Typer app instance
3. Implement command functions with proper type hints
4. The CLI loader will automatically discover and add your command

Example:
```python
# src/uvmgr/commands/mycommand.py
import typer
from ..ops.mycommand import my_operation

app = typer.Typer()

@app.command()
def do_something(arg: str = typer.Argument(..., help="Description")):
    """Command description."""
    result = my_operation(arg)
    typer.echo(result)
```

## Configuration

- User config: `~/.config/uvmgr/env.toml`
- Cache directory: `~/.uvmgr_cache/`
- Virtual environments: `.venv/` in project root

## MCP Server

To work with MCP features:
```bash
# Install MCP dependencies
pip install 'uvmgr[mcp]'

# Start MCP server
uvmgr serve start
```

## Common Development Tasks

### Adding Dependencies
```bash
# Add a production dependency
uvmgr deps add <package>

# Add a development dependency
uvmgr deps add <package> --dev

# Update dependencies
uvmgr deps update
```

### Working with AI Features
```bash
# Get AI assistance
uvmgr ai assist "Describe what you need"

# Fix test failures with AI
uvmgr ai fix-tests

# Plan implementation
uvmgr ai plan "Feature description"
```

## Pre-commit Hooks

The project uses extensive pre-commit hooks. They run automatically on commit but can be run manually:
```bash
# Run on all files
poe lint

# Install/update hooks
pre-commit install
pre-commit autoupdate
```

## Type Checking

MyPy is configured for static type checking:
```bash
# Type check the codebase
mypy src/

# Type check with pretty output (configured in pyproject.toml)
mypy
```

## Key Dependencies

- **CLI**: typer, rich (for enhanced terminal output)
- **Testing**: pytest, pytest-mock, coverage
- **AI**: dspy, fastmcp, ember-ai
- **Web**: fastapi
- **Workflow**: spiffworkflow, apscheduler
- **Telemetry**: opentelemetry-sdk
- **Packaging**: pyinstaller, pyinstaller-hooks-contrib

## Error Handling

- Use `typer.Exit(code=1)` for CLI errors
- Provide helpful error messages with `rich.console.Console().print("[red]Error: ...[/red]")`
- Runtime errors should bubble up with clear messages
- Use proper logging with the configured telemetry system

## Performance Considerations

- The project emphasizes speed by using `uv` underneath
- Cache operations are used extensively (`~/.uvmgr_cache/`)
- Subprocess calls are made with proper error handling
- Async operations are preferred for I/O-bound tasks

## PyInstaller Integration

uvmgr can package itself and other Python applications as standalone executables:

### Building Executables
- `uvmgr build exe` - Build a single-file executable
- `uvmgr build exe --onedir` - Build as a directory bundle
- `uvmgr build exe --spec custom.spec` - Use a custom spec file
- `uvmgr build dogfood` - Build uvmgr itself as an executable

### Spec File Generation
- `uvmgr build spec` - Generate a customizable PyInstaller spec file
- Spec files include all necessary hidden imports for uvmgr
- Supports custom icons, exclusions, and data files

### Hidden Imports
The build system automatically includes common uvmgr dependencies:
- All uvmgr command modules
- Core dependencies (typer, rich, fastapi, etc.)
- AI libraries (dspy, ember-ai)
- Workflow engines (spiffworkflow, apscheduler)

### Testing Built Executables
- The `dogfood` command includes a `--test` flag to verify the executable
- Tests include version check, help display, and command listing
- Ensures the standalone executable functions correctly