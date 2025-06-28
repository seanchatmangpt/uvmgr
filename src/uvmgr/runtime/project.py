"""
uvmgr.runtime.project
=====================

Runtime layer for project creation with Substrate-inspired templates.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from textwrap import dedent

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import span


def create_project(
    name: str,
    *,
    template: str = "basic",
    substrate: bool = False,
    fastapi: bool = False,
    typer_cli: bool = True,
    dev_containers: bool = False,
    github_actions: bool = False,
    pre_commit: bool = False,
    conventional_commits: bool = False,
    semantic_versioning: bool = False,
) -> dict:
    """
    Create a new Python project with specified features.
    
    Args:
        name: Project name and directory
        template: Project template type 
        substrate: Enable Substrate-inspired features
        fastapi: Include FastAPI skeleton
        typer_cli: Include Typer CLI skeleton
        dev_containers: Include DevContainer configuration
        github_actions: Include GitHub Actions CI/CD
        pre_commit: Include pre-commit hooks
        conventional_commits: Enable conventional commits
        semantic_versioning: Enable semantic versioning
        
    Returns:
        Dictionary with creation results
    """
    with span("runtime.project.create", project_name=name):
        start_time = time.time()
        project_dir = Path(name)
        
        add_span_event("project.creation.directories.starting", {
            "project_dir": str(project_dir),
            "template": template
        })
        
        # Create project directory structure
        if project_dir.exists():
            raise FileExistsError(f"Directory '{name}' already exists")
            
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard Python project structure
        dirs_to_create = [
            project_dir / "src" / name.replace("-", "_"),
            project_dir / "tests",
            project_dir / "docs",
        ]
        
        if dev_containers:
            dirs_to_create.append(project_dir / ".devcontainer")
            
        if github_actions:
            dirs_to_create.append(project_dir / ".github" / "workflows")
            
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        files_created = 0
        
        # Create pyproject.toml with Substrate-inspired configuration
        pyproject_content = _generate_pyproject_toml(
            name, substrate, fastapi, typer_cli, pre_commit, 
            conventional_commits, semantic_versioning
        )
        (project_dir / "pyproject.toml").write_text(pyproject_content)
        files_created += 1
        
        # Create main package module
        package_name = name.replace("-", "_")
        package_dir = project_dir / "src" / package_name
        
        init_content = f'"""Main package for {name}."""\n__version__ = "0.1.0"\n'
        (package_dir / "__init__.py").write_text(init_content)
        files_created += 1
        
        # Create CLI module if requested
        if typer_cli:
            cli_content = _generate_cli_module(package_name)
            (package_dir / "cli.py").write_text(cli_content)
            files_created += 1
            
        # Create FastAPI module if requested
        if fastapi:
            api_content = _generate_fastapi_module(package_name)
            (package_dir / "api.py").write_text(api_content)
            files_created += 1
            
        # Create basic test
        test_content = _generate_test_module(package_name)
        (project_dir / "tests" / "test_basic.py").write_text(test_content)
        files_created += 1
        
        # Create README with Substrate-inspired content
        readme_content = _generate_readme(name, substrate, fastapi, typer_cli)
        (project_dir / "README.md").write_text(readme_content)
        files_created += 1
        
        # Create DevContainer configuration if requested
        if dev_containers:
            devcontainer_content = _generate_devcontainer_config(name)
            (project_dir / ".devcontainer" / "devcontainer.json").write_text(devcontainer_content)
            files_created += 1
            
        # Create GitHub Actions if requested
        if github_actions:
            workflow_content = _generate_github_workflow(name, substrate)
            (project_dir / ".github" / "workflows" / "ci.yml").write_text(workflow_content)
            files_created += 1
            
        # Create pre-commit configuration if requested
        if pre_commit:
            precommit_content = _generate_precommit_config()
            (project_dir / ".pre-commit-config.yaml").write_text(precommit_content)
            files_created += 1
            
        # Create additional Substrate-inspired files
        if substrate:
            # Add Taskfile for task automation
            taskfile_content = _generate_taskfile(name)
            (project_dir / "Taskfile.yml").write_text(taskfile_content)
            files_created += 1
            
            # Add .gitignore
            gitignore_content = _generate_gitignore()
            (project_dir / ".gitignore").write_text(gitignore_content)
            files_created += 1
            
        duration = time.time() - start_time
        
        add_span_attributes(**{
            "project.files_created": files_created,
            "project.creation_duration": duration,
        })
        
        add_span_event("project.creation.completed", {
            "project_dir": str(project_dir),
            "files_created": files_created,
            "duration": duration,
        })
        
        return {
            "path": str(project_dir.absolute()),
            "files_created": files_created,
            "duration": duration,
        }


def _generate_pyproject_toml(
    name: str, substrate: bool, fastapi: bool, typer_cli: bool,
    pre_commit: bool, conventional_commits: bool, semantic_versioning: bool
) -> str:
    """Generate pyproject.toml with Substrate-inspired configuration."""
    
    dependencies = []
    if fastapi:
        dependencies.extend(["fastapi", "uvicorn[standard]"])
    if typer_cli:
        dependencies.append("typer[all]")
        
    dev_dependencies = [
        "pytest",
        "pytest-cov", 
        "ruff",
        "mypy",
    ]
    
    if substrate:
        dev_dependencies.extend([
            "poethepoet",  # Task runner like in Substrate
            "commitizen",  # For conventional commits
            "pre-commit",  # Pre-commit hooks
        ])
        
    pyproject = f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "A Python project created with uvmgr"
readme = "README.md"
requires-python = ">=3.10"
authors = [
    {{name = "Developer", email = "dev@example.com"}},
]
dependencies = {dependencies}

[project.optional-dependencies]
dev = {dev_dependencies}

[project.urls]
Homepage = "https://github.com/example/{name}"
Repository = "https://github.com/example/{name}.git"
Issues = "https://github.com/example/{name}/issues"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "YTT", "S", "BLE", "FBT", "B", "A", "COM", "C4", "DTZ", "T10", "DJ", "EM", "EXE", "FA", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SLOT", "SIM", "TID", "TCH", "INT", "ARG", "PTH", "TD", "FIX", "ERA", "PD", "PGH", "PL", "TRY", "FLY", "NPY", "AIR", "PERF", "FURB", "LOG", "RUF"]
ignore = ["E501", "S101", "D"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing --cov-report=html"
"""

    if substrate and conventional_commits:
        pyproject += """
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
tag_format = "v$version"
version_files = ["pyproject.toml:version"]
"""

    if substrate:
        pyproject += f"""
[tool.poe.tasks]
test = "pytest"
lint = "ruff check ."
format = "ruff format ."
type-check = "mypy src"
all-checks = ["lint", "format", "type-check", "test"]

[tool.poe.tasks.serve]
help = "Run the development server"
"""
        if fastapi:
            pyproject += f'cmd = "uvicorn {name.replace("-", "_")}.api:app --reload"\n'
        else:
            pyproject += 'cmd = "python -m src"\n'

    return pyproject


def _generate_cli_module(package_name: str) -> str:
    """Generate Typer CLI module."""
    return dedent(f"""
    '''Command-line interface for {package_name}.'''
    
    import typer
    from rich.console import Console
    
    from . import __version__
    
    app = typer.Typer(help="Command-line interface for {package_name}")
    console = Console()
    
    
    @app.command()
    def version():
        '''Show version information.'''
        console.print(f"{{__version__}}")
        
        
    @app.command()
    def hello(name: str = "World"):
        '''Say hello to someone.'''
        console.print(f"Hello {{name}}!")
        
        
    def main():
        '''Entry point for the CLI.'''
        app()
        
        
    if __name__ == "__main__":
        main()
    """).strip()


def _generate_fastapi_module(package_name: str) -> str:
    """Generate FastAPI module."""
    return dedent(f"""
    '''FastAPI application for {package_name}.'''
    
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    from . import __version__
    
    app = FastAPI(
        title="{package_name}",
        description="API for {package_name}",
        version=__version__,
    )
    
    
    @app.get("/")
    async def root():
        '''Root endpoint.'''
        return {{"message": "Hello from {package_name}!", "version": __version__}}
        
        
    @app.get("/health")
    async def health():
        '''Health check endpoint.'''
        return JSONResponse(
            status_code=200,
            content={{"status": "healthy", "version": __version__}}
        )
    """).strip()


def _generate_test_module(package_name: str) -> str:
    """Generate basic test module."""
    return dedent(f"""
    '''Basic tests for {package_name}.'''
    
    import pytest
    
    from {package_name} import __version__
    
    
    def test_version():
        '''Test version is defined.'''
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0
        
        
    def test_import():
        '''Test package can be imported.'''
        import {package_name}
        assert {package_name} is not None
    """).strip()


def _generate_readme(name: str, substrate: bool, fastapi: bool, typer_cli: bool) -> str:
    """Generate README with Substrate-inspired content."""
    
    readme = f"""# {name}

A Python project created with uvmgr, inspired by modern development practices.

## Features

"""
    
    features = []
    if substrate:
        features.append("🚀 Substrate-inspired project structure")
    if fastapi:
        features.append("⚡ FastAPI web framework")
    if typer_cli:
        features.append("🖥️ Typer CLI interface")
        
    features.extend([
        "📦 Modern dependency management with uv",
        "🧪 Testing with pytest",
        "🔍 Linting with Ruff",
        "📊 Type checking with MyPy",
    ])
    
    for feature in features:
        readme += f"- {feature}\n"
        
    readme += f"""
## Installation

```bash
# Install in development mode
uv pip install -e .

# Install with dependencies
uv pip install -e ".[dev]"
```

## Usage
"""

    if typer_cli:
        readme += f"""
### Command Line Interface

```bash
# Show version
python -m {name.replace('-', '_')} version

# Say hello
python -m {name.replace('-', '_')} hello --name "World"
```
"""

    if fastapi:
        readme += f"""
### Web API

```bash
# Start development server
uvicorn {name.replace('-', '_')}.api:app --reload

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```
"""

    if substrate:
        readme += """
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
"""

    readme += """
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
"""

    return readme


def _generate_devcontainer_config(name: str) -> str:
    """Generate DevContainer configuration."""
    return dedent(f"""
    {{
        "name": "{name} Development",
        "image": "mcr.microsoft.com/devcontainers/python:3.11",
        "features": {{
            "ghcr.io/devcontainers/features/github-cli:1": {{}},
            "ghcr.io/devcontainers/features/docker-in-docker:2": {{}}
        }},
        "customizations": {{
            "vscode": {{
                "extensions": [
                    "ms-python.python",
                    "ms-python.black-formatter",
                    "charliermarsh.ruff",
                    "ms-python.mypy-type-checker",
                    "GitHub.copilot"
                ],
                "settings": {{
                    "python.defaultInterpreterPath": "/usr/local/bin/python",
                    "python.formatting.provider": "black",
                    "python.linting.enabled": true,
                    "python.linting.ruffEnabled": true
                }}
            }}
        }},
        "postCreateCommand": "pip install -e '.[dev]'",
        "remoteUser": "vscode"
    }}
    """).strip()


def _generate_github_workflow(name: str, substrate: bool) -> str:
    """Generate GitHub Actions workflow."""
    
    workflow = f"""name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}
        
    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "${{{{ github.workspace }}}}/.local/bin" >> $GITHUB_PATH
        
    - name: Install dependencies
      run: uv pip install -e ".[dev]" --system
      
    - name: Lint with Ruff
      run: ruff check .
      
    - name: Type check with MyPy
      run: mypy src
      
    - name: Test with pytest
      run: pytest --cov --cov-report=xml
      
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
"""

    if substrate:
        workflow += """
  release:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
        token: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
        
    - name: Install dependencies
      run: |
        pip install commitizen
        
    - name: Bump version and create changelog
      run: |
        cz bump --changelog
        git push --follow-tags
"""

    return workflow


def _generate_precommit_config() -> str:
    """Generate pre-commit configuration."""
    return dedent("""
    repos:
      - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.4.0
        hooks:
          - id: trailing-whitespace
          - id: end-of-file-fixer
          - id: check-yaml
          - id: check-added-large-files
          - id: check-merge-conflict
          
      - repo: https://github.com/astral-sh/ruff-pre-commit
        rev: v0.1.6
        hooks:
          - id: ruff
            args: [--fix, --exit-non-zero-on-fix]
          - id: ruff-format
          
      - repo: https://github.com/pre-commit/mirrors-mypy
        rev: v1.7.1
        hooks:
          - id: mypy
            additional_dependencies: [types-requests]
    """).strip()


def _generate_taskfile(name: str) -> str:
    """Generate Taskfile for task automation."""
    return dedent(f"""
    version: '3'
    
    tasks:
      install:
        desc: Install dependencies
        cmds:
          - uv pip install -e ".[dev]"
          
      test:
        desc: Run tests
        cmds:
          - pytest
          
      test-cov:
        desc: Run tests with coverage
        cmds:
          - pytest --cov --cov-report=html
          
      lint:
        desc: Lint code
        cmds:
          - ruff check .
          
      format:
        desc: Format code
        cmds:
          - ruff format .
          
      type-check:
        desc: Type check
        cmds:
          - mypy src
          
      all-checks:
        desc: Run all checks
        deps: [lint, format, type-check, test]
        
      clean:
        desc: Clean build artifacts
        cmds:
          - rm -rf build/ dist/ *.egg-info/
          - rm -rf .pytest_cache/ .coverage htmlcov/
          
      build:
        desc: Build package
        cmds:
          - python -m build
    """).strip()


def _generate_gitignore() -> str:
    """Generate comprehensive .gitignore."""
    return dedent("""
    # Byte-compiled / optimized / DLL files
    __pycache__/
    *.py[cod]
    *$py.class
    
    # C extensions
    *.so
    
    # Distribution / packaging
    .Python
    build/
    develop-eggs/
    dist/
    downloads/
    eggs/
    .eggs/
    lib/
    lib64/
    parts/
    sdist/
    var/
    wheels/
    share/python-wheels/
    *.egg-info/
    .installed.cfg
    *.egg
    MANIFEST
    
    # PyInstaller
    *.manifest
    *.spec
    
    # Installer logs
    pip-log.txt
    pip-delete-this-directory.txt
    
    # Unit test / coverage reports
    htmlcov/
    .tox/
    .nox/
    .coverage
    .coverage.*
    .cache
    nosetests.xml
    coverage.xml
    *.cover
    *.py,cover
    .hypothesis/
    .pytest_cache/
    cover/
    
    # Virtual environments
    .env
    .venv
    env/
    venv/
    ENV/
    env.bak/
    venv.bak/
    
    # IDEs
    .vscode/
    .idea/
    *.swp
    *.swo
    *~
    
    # OS
    .DS_Store
    .DS_Store?
    ._*
    .Spotlight-V100
    .Trashes
    ehthumbs.db
    Thumbs.db
    
    # Project specific
    *.log
    .env.local
    .env.*.local
    """).strip()