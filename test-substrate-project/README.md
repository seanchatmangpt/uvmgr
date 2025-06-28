# test-substrate-project

A Python project created with uvmgr, inspired by modern development practices.

## Features

- 🚀 Substrate-inspired project structure
- ⚡ FastAPI web framework
- 🖥️ Typer CLI interface
- 📦 Modern dependency management with uv
- 🧪 Testing with pytest
- 🔍 Linting with Ruff
- 📊 Type checking with MyPy

## Installation

```bash
# Install in development mode
uv pip install -e .

# Install with dependencies
uv pip install -e ".[dev]"
```

## Usage

### Command Line Interface

```bash
# Show version
python -m test_substrate_project version

# Say hello
python -m test_substrate_project hello --name "World"
```

### Web API

```bash
# Start development server
uvicorn test_substrate_project.api:app --reload

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### Development Tasks

This project uses `poethepoet` for task automation:

```bash
# Run tests
poe test

# Run linting
poe lint

# Format code
poe format

# Type checking
poe type-check

# Run all checks
poe all-checks
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov

# Lint code
ruff check .

# Format code
ruff format .

# Type checking
mypy src
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
