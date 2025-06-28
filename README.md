# uvmgr

[![PyPI Version](https://img.shields.io/pypi/v/uvmgr.svg)](https://pypi.org/project/uvmgr/)
[![License](https://img.shields.io/pypi/l/uvmgr.svg)](https://github.com/seanchatmangpt/uvmgr/blob/main/LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/seanchatmangpt/uvmgr/ci.yml)](https://github.com/seanchatmangpt/uvmgr/actions)

**`uvmgr`** is a unified Python workflow engine powered by `uv`. It provides a single, consistent command-line interface to streamline the entire development lifecycle—from project creation to release, with advanced observability and AI integration capabilities.

### Key Features

*   **Project Scaffolding:** Create modern Python projects from templates.
*   **Dependency Management:** A simple, powerful wrapper around `uv` for managing packages.
*   **Testing & Coverage:** Run your test suite with `pytest` and generate coverage reports.
*   **Builds & Releases:** Build packages and manage versions with Commitizen.
*   **AI-Assisted Development:** Leverage language models to review code, generate plans, and fix tests.
*   **Environment Interaction:** Execute scripts and tools directly within the project's virtual environment.
*   **Workflow Automation:** Run BPMN workflows or schedule recurring tasks.
*   **OpenTelemetry Integration:** Built-in observability with tracing, metrics, and semantic conventions.
*   **Code Quality:** Linting and formatting with Ruff integration.
*   **MCP Server:** Model Context Protocol server for AI assistant integration.
*   **Weaver Integration:** OpenTelemetry semantic convention management.

### Installation

```bash
pip install uvmgr
```

### Getting Started: A Quick Tour

Experience the unified workflow in just a few commands:

1.  **Create a new project with a FastAPI skeleton:**
    ```bash
    uvmgr new my-awesome-project --fastapi
    ```

2.  **Navigate into your new project:**
    ```bash
    cd my-awesome-project
    ```

3.  **Add a new dependency:** `uv` will automatically find and update your `pyproject.toml`.
    ```bash
    uvmgr deps add "requests"
    ```

4.  **Run the test suite:**
    ```bash
    uvmgr tests run
    ```

5.  **Build your package:**
    ```bash
    uvmgr build dist
    ```

### Command Overview

`uvmgr` organizes its functionality into intuitive command groups.

#### Core Development
*   `uvmgr new`:         Create a new Python project.
*   `uvmgr deps`:        Manage project dependencies.
*   `uvmgr tests`:       Run the test suite with `pytest`.
*   `uvmgr build`:       Build `sdist` and `wheel` packages.
*   `uvmgr release`:     Manage project versions and changelogs.
*   `uvmgr exec`:        Execute Python scripts in the project environment.
*   `uvmgr shell`:       Open an interactive REPL in the project environment.
*   `uvmgr tool`:        Install and run command-line tools.

#### Code Quality & Development
*   `uvmgr lint`:        Run Ruff linter and formatter.
*   `uvmgr serve`:       Start development server.

#### AI & Automation
*   `uvmgr ai`:          Interact with language models.
*   `uvmgr agent`:       Run BPMN automation workflows.
*   `uvmgr ap-scheduler`:  Schedule recurring tasks.
*   `uvmgr mcp`:         Start MCP server for AI assistant integration.

#### Observability & Telemetry
*   `uvmgr otel`:        OpenTelemetry validation and management.
*   `uvmgr weaver`:      OpenTelemetry Weaver semantic convention tools.

#### Utilities
*   `uvmgr cache`:       Manage the `uv` cache.
*   `uvmgr index`:       Manage package indexes.

**For a complete reference with detailed examples for every command, please see our [Comprehensive User Guide](HOWTO.md).**

### Quick Examples

#### OpenTelemetry Observability
```bash
# Start OTEL infrastructure
docker-compose -f docker-compose.otel.yml up -d

# Run commands with automatic telemetry
uvmgr deps add requests
uvmgr tests run

# View traces in Jaeger (http://localhost:16686)
# View metrics in Prometheus (http://localhost:9090)
```

#### Code Quality
```bash
# Lint and format code
uvmgr lint check
uvmgr lint format

# Auto-fix issues
uvmgr lint fix
```

#### AI Integration
```bash
# Start MCP server for Claude Desktop
uvmgr mcp serve

# Ask AI for help
uvmgr ai ask "How do I optimize this function?"
```

#### Semantic Conventions
```bash
# Install Weaver
uvmgr weaver install

# Validate semantic conventions
uvmgr weaver check

# Generate code from conventions
uvmgr weaver generate python
```

### Contributing

Contributions are welcome! To get started with development:

1.  Fork the repository.
2.  Clone your fork and navigate into the directory.
3.  Set up the development environment:
    ```bash
    uv sync --all-extras
    ```
4.  Install the pre-commit hooks:
    ```bash
    pre-commit install
    ```
5.  Make your changes, run tests, and submit a pull request.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.