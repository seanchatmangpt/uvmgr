# uvmgr: Unified Python Workflow Engine Guide

## Overview

uvmgr is a powerful unified Python workflow engine powered by `uv`, designed to streamline Python project development, testing, and deployment. This guide covers best practices for using uvmgr's features to create and manage Python projects end-to-end.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Creation](#project-creation)
3. [Project Lifecycle](#project-lifecycle)
4. [Development Workflow](#development-workflow)
5. [Quality Assurance](#quality-assurance)
6. [Building and Releasing](#building-and-releasing)
7. [Advanced Features](#advanced-features)

## Getting Started

### Installation

```bash
# Install uvmgr
pip install uvmgr

# Verify installation
uvmgr --version
```

## Project Creation

### Creating a New Project

uvmgr uses [Substrate](https://github.com/superlinear-ai/substrate) as its default template for creating new Python projects. Substrate provides a modern, standardized project structure with best practices for Python development.

```bash
# Create a new project using the default Substrate template
uvmgr new my-project

# Create a project with a custom template
uvmgr new my-project --template https://github.com/user/custom-template

# Interactive mode with all configuration options
uvmgr new my-project --interactive
```

### Project Configuration

During project creation, you'll be prompted to configure:

1. **Basic Information**
   - Project name (converted to kebab-case)
   - Package name (converted to snake_case)
   - Project description
   - Author information
   - License selection

2. **Development Tools**
   - Pre-commit hooks for code quality
   - Conventional commits for versioning
   - GPG commit signing
   - CI/CD platform (GitHub/GitLab)
   - Test coverage tools

3. **Environment Setup**
   - Python version
   - Development container configuration
   - VS Code settings
   - Git hooks

### Project Structure

The created project will have this structure:

```
my-project/
├── .devcontainer/          # Dev container configuration
├── .github/               # GitHub workflows
├── src/
│   └── my_project/       # Package source
├── tests/                # Test suite
├── .pre-commit-config.yaml
├── pyproject.toml        # Project metadata and dependencies
├── README.md
└── CHANGELOG.md
```

### Template Features

The Substrate template includes:

1. **Development Environment**
   - Dev container support
   - VS Code integration
   - Pre-configured linting and formatting
   - Git hooks setup
   - Virtual environment management with uv

2. **Quality Assurance**
   - Ruff for fast Python linting
   - MyPy for static type checking
   - Pre-commit hooks
   - Test coverage with Coverage.py

3. **CI/CD Pipeline**
   - GitHub Actions or GitLab CI/CD
   - Automated testing
   - Code quality checks
   - Release management

4. **Documentation**
   - README.md template
   - CHANGELOG.md
   - API documentation setup
   - Development guides

### Custom Templates

You can use custom Copier templates by providing a URL:

```bash
# Use a custom template
uvmgr new my-project --template https://github.com/user/custom-template

# Pin template version
uvmgr new my-project --template https://github.com/user/custom-template@v1.0.0
```

### Environment Management

```bash
# Open a Python REPL in your project environment
uvmgr shell

# Execute a Python script in the project environment
uvmgr exec script.py

# Run arbitrary tools in the project environment
uvmgr tool <tool-name>
```

## Project Lifecycle

### Dependency Management

```bash
# Add new dependencies
uvmgr deps add requests pandas

# Upgrade dependencies
uvmgr deps upgrade

# Remove dependencies
uvmgr deps remove unused-package

# Manage package indexes
uvmgr index add https://custom.pypi.org/simple
```

### Cache Management

```bash
# Manage uv cache
uvmgr cache clean
uvmgr cache list
```

## Development Workflow

### Development Tasks

```bash
# Run all development tasks (lint, test, serve)
uvmgr dev

# Individual tasks
uvmgr lint    # Run Ruff + MyPy + Pre-commit
uvmgr test    # Run coverage + pytest
uvmgr serve   # Start FastAPI dev server
```

### Code Quality

The `lint` command runs multiple quality checks:
- Ruff for fast Python linting
- MyPy for static type checking
- Pre-commit hooks for git commit validation

## Quality Assurance

### Testing

```bash
# Run tests with coverage
uvmgr test

# Run specific test files
uvmgr test tests/test_specific.py

# Generate coverage reports
uvmgr test --coverage
```

### AI-Assisted Development

```bash
# Use local or remote Language Models for development
uvmgr ai <prompt>

# Common use cases:
uvmgr ai "Review this code for security issues"
uvmgr ai "Generate test cases for this function"
```

## Building and Releasing

### Building Packages

```bash
# Build wheel and sdist
uvmgr build

# Build specific formats
uvmgr build --wheel-only
uvmgr build --sdist-only
```

### Release Management

```bash
# Prepare a new release
uvmgr release

# The release command uses Commitizen to:
# - Bump version numbers
# - Generate changelog
# - Create git tags
# - Prepare release notes
```

## Advanced Features

### Workflow Automation

```bash
# Execute BPMN workflows
uvmgr agent run workflow.bpmn

# Schedule tasks using APScheduler
uvmgr ap-scheduler add "task_name" "cron_expression"
```

### Remote Execution

```bash
# Execute commands on remote systems
uvmgr remote run <command>

# Note: Remote execution features are under development
```

## Best Practices

1. **Project Structure**
   - Use `uvmgr new` to create standardized project layouts
   - Follow the template's directory structure
   - Keep dependencies in `pyproject.toml`

2. **Development Workflow**
   - Run `uvmgr dev` before committing changes
   - Use `uvmgr lint` to maintain code quality
   - Leverage `uvmgr ai` for code reviews and improvements

3. **Dependency Management**
   - Use `uvmgr deps` for all package operations
   - Keep dependencies up to date with `uvmgr deps upgrade`
   - Use `uvmgr cache` to manage package caches

4. **Testing and Quality**
   - Write tests for all new features
   - Maintain high test coverage
   - Use `uvmgr test` regularly during development

5. **Release Process**
   - Use `uvmgr release` for version management
   - Follow semantic versioning
   - Keep changelog up to date

## Tips and Tricks

- Use `--json` flag for machine-readable output:
  ```bash
  uvmgr --json <command>
  ```

- Combine commands for efficient workflows:
  ```bash
  uvmgr deps add new-package && uvmgr dev
  ```

- Use the shell for interactive development:
  ```bash
  uvmgr shell
  ```

## Troubleshooting

Common issues and solutions:

1. **Cache Issues**
   ```bash
   uvmgr cache clean
   ```

2. **Dependency Conflicts**
   ```bash
   uvmgr deps upgrade --latest
   ```

3. **Test Failures**
   ```bash
   uvmgr test --verbose
   ```

## Contributing

To contribute to uvmgr:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `uvmgr dev` to verify
5. Submit a pull request

## License

[Add appropriate license information]

---

For more detailed information about specific commands, use:
```bash
uvmgr <command> --help
``` 