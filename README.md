# uvmgr

[![PyPI Version](https://img.shields.io/pypi/v/uvmgr.svg)](https://pypi.org/project/uvmgr/)
[![License](https://img.shields.io/pypi/l/uvmgr.svg)](https://github.com/seanchatmangpt/uvmgr/blob/main/LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/seanchatmangpt/uvmgr/ci.yml)](https://github.com/seanchatmangpt/uvmgr/actions)

**`uvmgr`** is a unified Python workflow engine powered by `uv`. It provides a single, consistent command-line interface to streamline the entire development lifecycle—from project creation to release.

### Key Features

*   **Project Scaffolding:** Create modern Python projects from templates.
*   **Dependency Management:** A simple, powerful wrapper around `uv` for managing packages.
*   **Testing & Coverage:** Run your test suite with `pytest` and generate coverage reports.
*   **Builds & Releases:** Build packages and manage versions with Commitizen.
*   **AI-Assisted Development:** Leverage language models to review code, generate plans, and fix tests.
*   **Environment Interaction:** Execute scripts and tools directly within the project's virtual environment.
*   **Workflow Automation:** Run BPMN workflows or schedule recurring tasks.

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

*   `uvmgr new`:         Create a new Python project.
*   `uvmgr deps`:        Manage project dependencies.
*   `uvmgr tests`:       Run the test suite with `pytest`.
*   `uvmgr build`:       Build `sdist` and `wheel` packages.
*   `uvmgr release`:     Manage project versions and changelogs.
*   `uvmgr exec`:        Execute Python scripts in the project environment.
*   `uvmgr shell`:       Open an interactive REPL in the project environment.
*   `uvmgr tool`:        Install and run command-line tools.
*   `uvmgr ai`:          Interact with language models.
*   `uvmgr cache`:       Manage the `uv` cache.
*   `uvmgr agent`:       Run BPMN automation workflows.
*   `uvmgr ap-scheduler`:  Schedule recurring tasks.

**For a complete reference with detailed examples for every command, please see our [Comprehensive User Guide](HOWTO.md).**

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