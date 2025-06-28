# Code Quality Guide

`uvmgr` provides comprehensive code quality tools to help maintain high standards across your Python projects. This guide covers linting, formatting, and development server features.

## Overview

The code quality tools in `uvmgr` are built around **Ruff**, a fast Python linter and formatter written in Rust. These tools help you:

- Maintain consistent code style
- Catch potential bugs and issues
- Ensure code follows best practices
- Automatically fix common problems
- Streamline the development workflow

## Quick Start

### Basic Code Quality Workflow

```bash
# Check code for issues
uvmgr lint check

# Format code automatically
uvmgr lint format

# Fix all auto-fixable issues
uvmgr lint fix
```

### Development Server

```bash
# Start development server
uvmgr serve

# Start with custom configuration
uvmgr serve --host 0.0.0.0 --port 8080 --reload
```

## Linting (`uvmgr lint check`)

The linting command checks your code for style violations, potential bugs, and best practice issues.

### Basic Usage

```bash
# Check current directory
uvmgr lint check

# Check specific path
uvmgr lint check src/

# Check specific file
uvmgr lint check src/myapp/main.py
```

### Auto-fixing Issues

```bash
# Fix auto-fixable violations
uvmgr lint check --fix

# Show what would be fixed without making changes
uvmgr lint check --show-fixes
```

### Examples

```bash
# Check and fix issues in source code
uvmgr lint check src/ --fix

# Check tests directory
uvmgr lint check tests/

# Show detailed output
uvmgr lint check -v
```

### Common Ruff Rules

Ruff includes rules from multiple linters:

#### Style (PEP 8)
- `E501`: Line too long
- `E302`: Expected 2 blank lines
- `E303`: Too many blank lines

#### Import Organization
- `I001`: Import sorting
- `I002`: Missing required imports
- `I003`: Unused imports

#### Error Detection
- `F401`: Unused imports
- `F841`: Unused variables
- `F821`: Undefined names

#### Best Practices
- `B006`: Do not use mutable data structures for argument defaults
- `B008`: Do not perform function calls in argument defaults
- `B011`: Do not call assert False since Python with -O removes these calls

## Formatting (`uvmgr lint format`)

The formatting command automatically formats your code according to PEP 8 and other style guidelines.

### Basic Usage

```bash
# Format current directory
uvmgr lint format

# Format specific path
uvmgr lint format src/

# Format specific file
uvmgr lint format src/myapp/main.py
```

### Check Mode

```bash
# Check if files are formatted without making changes
uvmgr lint format --check

# Exit with error if files need formatting
uvmgr lint format --check && echo "All files formatted"
```

### Examples

```bash
# Format all Python files
uvmgr lint format

# Check formatting in CI
uvmgr lint format --check

# Format specific directories
uvmgr lint format src/ tests/ examples/
```

## Auto-fix All Issues (`uvmgr lint fix`)

The `fix` command combines formatting and linting with auto-fixing to resolve all automatically fixable issues.

### Usage

```bash
# Fix all issues in current directory
uvmgr lint fix

# Fix issues in specific path
uvmgr lint fix src/

# Fix issues in multiple paths
uvmgr lint fix src/ tests/
```

### What It Does

1. **Formats code** using Ruff formatter
2. **Fixes linting issues** that can be automatically resolved
3. **Reports remaining issues** that require manual attention

### Examples

```bash
# Fix all issues before committing
uvmgr lint fix

# Fix issues in specific modules
uvmgr lint fix src/myapp/ src/utils/

# Fix and check remaining issues
uvmgr lint fix && uvmgr lint check
```

## Development Server (`uvmgr serve`)

The development server provides a convenient way to run your application during development.

### Basic Usage

```bash
# Start server with default settings
uvmgr serve

# Start with custom host and port
uvmgr serve --host 0.0.0.0 --port 8080

# Start with auto-reload
uvmgr serve --reload
```

### Configuration Options

```bash
# Custom host (default: 127.0.0.1)
uvmgr serve --host 0.0.0.0

# Custom port (default: 8000)
uvmgr serve --port 8080

# Enable auto-reload on file changes
uvmgr serve --reload

# Custom reload directories
uvmgr serve --reload --reload-dir src/ --reload-dir templates/
```

### Examples

```bash
# Development with auto-reload
uvmgr serve --reload --port 3000

# Production-like settings
uvmgr serve --host 0.0.0.0 --port 80

# Custom configuration
uvmgr serve --host 127.0.0.1 --port 5000 --reload
```

## Configuration

### Ruff Configuration

Ruff configuration is typically defined in `pyproject.toml`:

```toml
[tool.ruff]
# Enable auto-fixing
fix = true

# Line length
line-length = 100

# Target Python version
target-version = "py312"

# Source directories
src = ["src", "tests"]

[tool.ruff.format]
# Docstring code formatting
docstring-code-format = true

[tool.ruff.lint]
# Select rules to enable
select = [
    "A",      # flake8-builtins
    "ASYNC",  # flake8-async
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "D",      # pydocstyle
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "W",      # pycodestyle warnings
]

# Ignore specific rules
ignore = [
    "D203",   # 1 blank line required before class docstring
    "D213",   # Multi-line docstring summary should start at the second line
    "E501",   # Line too long
]

# Unfixable rules
unfixable = ["F401", "F841"]
```

### Pre-commit Integration

Add Ruff to your pre-commit configuration:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### VS Code Integration

Configure VS Code to use Ruff:

```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  }
}
```

## Best Practices

### Workflow Integration

1. **Pre-commit**: Run linting and formatting before commits
2. **CI/CD**: Include code quality checks in your pipeline
3. **IDE**: Configure your editor to use Ruff
4. **Regular checks**: Run `uvmgr lint fix` regularly

### Example Workflow

```bash
# 1. Make changes to your code
vim src/myapp/main.py

# 2. Fix any issues automatically
uvmgr lint fix

# 3. Check for remaining issues
uvmgr lint check

# 4. Run tests
uvmgr tests run

# 5. Commit changes
git add .
git commit -m "Add new feature"
```

### CI/CD Integration

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install uvmgr
        run: pip install uvmgr
      
      - name: Check code quality
        run: uvmgr lint check --check
      
      - name: Check formatting
        run: uvmgr lint format --check
      
      - name: Run tests
        run: uvmgr tests run
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# If you get import errors, ensure dependencies are installed
uvmgr deps sync

# Or install Ruff directly
pip install ruff
```

#### Configuration Issues
```bash
# Check Ruff configuration
ruff check --show-config

# Validate pyproject.toml
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
```

#### Performance Issues
```bash
# Use Ruff's cache
ruff check --cache-dir .ruff_cache

# Exclude large directories
ruff check --exclude vendor/ --exclude node_modules/
```

### Getting Help

```bash
# Show Ruff help
ruff --help

# Show specific command help
ruff check --help
ruff format --help

# Show rule documentation
ruff rule E501
```

## Advanced Features

### Custom Rules

Create custom rules in `pyproject.toml`:

```toml
[tool.ruff.lint.rules]
# Customize rule settings
"E501" = { line-length = 120 }
"B006" = false  # Disable rule
```

### Ignore Files

Create `.ruff.toml` for project-specific ignores:

```toml
# .ruff.toml
[tool.ruff]
ignore = ["E501", "W503"]

[tool.ruff.lint]
ignore = ["src/legacy/"]
```

### Per-file Configuration

Use inline comments to ignore specific lines:

```python
# ruff: noqa: E501
very_long_line = "this line is intentionally long and should not be flagged by the linter"

# ruff: noqa
def legacy_function():  # This entire function is ignored
    pass
```

## Integration with Other Tools

### Poetry Integration

```toml
# pyproject.toml
[tool.poetry.scripts]
lint = "uvmgr.cli:app"
format = "uvmgr.cli:app"

[tool.poetry.group.dev.dependencies]
ruff = "^0.1.0"
```

### Makefile Integration

```makefile
# Makefile
.PHONY: lint format fix test

lint:
	uvmgr lint check

format:
	uvmgr lint format

fix:
	uvmgr lint fix

test:
	uvmgr tests run

quality: fix lint test
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.12-slim

RUN pip install uvmgr

WORKDIR /app
COPY . .

# Run code quality checks
RUN uvmgr lint fix
RUN uvmgr lint check

# Start development server
CMD ["uvmgr", "serve", "--host", "0.0.0.0"]
```

## Performance Tips

### Optimize for Speed

```bash
# Use Ruff's cache
ruff check --cache-dir .ruff_cache

# Exclude unnecessary directories
ruff check --exclude .git --exclude .venv --exclude node_modules/

# Use parallel processing
ruff check --jobs 4
```

### Large Codebases

```bash
# Check only changed files
ruff check --diff

# Use file-based caching
ruff check --cache-dir .ruff_cache

# Exclude generated files
ruff check --exclude "*/generated/*" --exclude "*/build/*"
```

## Migration from Other Tools

### From Black + isort + flake8

```bash
# Replace multiple tools with Ruff
# Before:
black .
isort .
flake8 .

# After:
uvmgr lint fix
```

### From pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

This comprehensive code quality guide should help you maintain high standards across your Python projects using `uvmgr`'s integrated tools. 