Of course. Here is a completely rewritten `HOWTO.md` file, drafted from scratch to be accurate, comprehensive, and logically structured based on the provided source code.

---

# uvmgr: A Comprehensive User Guide

Welcome to the comprehensive user guide for `uvmgr`. This document provides in-depth information and practical examples for every feature, serving as a complete reference for the tool.

For a brief overview, please see the [README.md](README.md).

## Table of Contents

1.  [Core Concepts](#1-core-concepts)
2.  [Installation](#2-installation)
3.  [The Project Lifecycle](#3-the-project-lifecycle)
    *   [Project Creation](#31-project-creation)
    *   [Dependency Management](#32-dependency-management)
    *   [Development Environment](#33-development-environment)
    *   [Quality Assurance](#34-quality-assurance)
    *   [Building and Releasing](#35-building-and-releasing)
4.  [Advanced Features](#4-advanced-features)
    *   [AI-Assisted Development](#41-ai-assisted-development)
    *   [Automation and Scheduling](#42-automation-and-scheduling)
    *   [Cache Management](#43-cache-management)
5.  [A Note on Deprecated Commands](#5-a-note-on-deprecated-commands)

## 1. Core Concepts

### The uvmgr Architecture

`uvmgr` is designed with a clean, three-layer architecture:
*   **Commands (`src/uvmgr/commands`):** Defines the CLI interface that you interact with (using Typer).
*   **Operations (`src/uvmgr/ops`):** Contains the core orchestration logic, written in pure Python.
*   **Runtime (`src/uvmgr/runtime`):** The layer that performs side-effects, like running subprocesses (`uv`, `pytest`) or making network calls.

### JSON Output

All commands support a global `--json` or `-j` flag. When used, `uvmgr` will output machine-readable JSON instead of human-readable text, which is ideal for scripting and integration with other tools.

```bash
uvmgr --json deps list
```

## 2. Installation

If you haven't already, install `uvmgr` using `pip`:
```bash
pip install uvmgr
```

## 3. The Project Lifecycle

This guide walks you through the typical lifecycle of a Python project using `uvmgr`.

### 3.1. Project Creation (`uvmgr new`)

The `new` command scaffolds a new Python project. It sets up a standard directory structure and basic configuration files.

```bash
# Create a standard library project with a Typer CLI
uvmgr new my-new-library

# Create a project with a FastAPI skeleton included
uvmgr new my-web-api --fastapi
```
*(Note: The project creation logic is currently a stub and will be fully implemented in a future version.)*

### 3.2. Dependency Management (`uvmgr deps` & `uvmgr index`)

#### Managing Dependencies (`deps`)
Use the `deps` command group to manage your project's dependencies via `uv`.

```bash
# Add a runtime dependency to your project
uvmgr deps add "requests" "pandas"

# Add a development-only dependency
uvmgr deps add "pytest" --dev

# Remove a dependency
uvmgr deps remove "pandas"

# Upgrade all dependencies to the latest versions allowed by pyproject.toml
uvmgr deps upgrade --all

# List all packages in the virtual environment
uvmgr deps list
```

#### Managing Package Indexes (`index`)
If you need to use a private or alternative PyPI index, you can manage it with the `index` command.

```bash
# Add a custom index URL
uvmgr index add https://my.private.pypi/simple

# List all configured custom indexes
uvmgr index list
```

### 3.3. Development Environment (`uvmgr exec`, `uvmgr shell`, `uvmgr tool`)

#### Executing Scripts (`exec`)
The `exec` command runs a Python script within the project's managed virtual environment, ensuring it has access to all installed dependencies.

```bash
# Run a script
uvmgr exec scripts/my_script.py

# Run a script and pass arguments to it
uvmgr exec scripts/my_script.py --input data.csv --output results.csv

# Run a script with temporary dependencies without installing them permanently
uvmgr exec --with numpy --with matplotlib scripts/plot.py

# Pipe a script into uvmgr from stdin
echo 'import sys; print(sys.version)' | uvmgr exec -
```

#### Interactive Shell (`shell`)
For interactive work and debugging, open a Python REPL directly in the project's environment. It will automatically use IPython if available.

```bash
uvmgr shell open
```

#### Running Tools (`tool`)
The `tool` command allows you to install and run command-line tools in an isolated environment managed by `uv`, keeping your project's dependencies clean.

```bash
# Install a tool like black
uvmgr tool install black

# Run the installed tool
uvmgr tool run black . --check

# Print the directory where tools are installed
uvmgr tool dir
```

### 3.4. Quality Assurance (`uvmgr tests`)

The `tests` command group is your interface for running the project's test suite.

```bash
# Run the test suite with pytest
uvmgr tests run

# Run tests with verbose output
uvmgr tests run -v

# Run tests and generate a code coverage report
uvmgr tests coverage
```

### 3.5. Building and Releasing (`uvmgr build` & `uvmgr release`)

#### Building Packages (`build`)
When you are ready to package your project, the `build` command creates `sdist` and `wheel` files.

```bash
# Build packages into the dist/ directory
uvmgr build dist

# Build and immediately upload to PyPI using Twine
uvmgr build dist --upload
```

#### Release Management (`release`)
`uvmgr` uses [Commitizen](https://commitizen-tools.github.io/commitizen/) to manage versions and changelogs based on your commit history.

```bash
# Automatically bump the version, update CHANGELOG.md, and create a git tag
uvmgr release bump

# Print the generated changelog to the console
uvmgr release changelog
```

## 4. Advanced Features

### 4.1. AI-Assisted Development (`uvmgr ai`)

Leverage local or remote language models to enhance your workflow. By default, it uses `ollama/phi3:medium-128k`.

```bash
# Ask the AI to explain a concept or review code
uvmgr ai ask "What are the pros and cons of using asyncio?"

# Generate a markdown plan for a new feature and save it to a file
uvmgr ai plan "Implement a Redis cache layer" --out PLAN.md

# Automatically attempt to generate a patch for failing tests
uvmgr ai fix-tests --patch "fix.patch"

# List available local Ollama models
uvmgr ai ollama list

# Delete a local Ollama model
uvmgr ai ollama delete llama3
```

### 4.2. Automation and Scheduling (`uvmgr agent` & `uvmgr ap-scheduler`)

#### BPMN Workflows (`agent`)
Run business process workflows defined in `.bpmn` files.

```bash
uvmgr agent run my_workflow.bpmn
```

#### Scheduled Tasks (`ap-scheduler`)
Schedule commands to run at specific intervals or on a cron schedule.

```bash
# Schedule a command to run every 10 minutes
uvmgr ap-scheduler add --every 600 "backup-job" "python scripts/backup.py"

# Schedule a command to run at midnight every day
uvmgr ap-scheduler add --cron "0 0 * * *" "cleanup-job" "rm -rf /tmp/cache"

# List all scheduled jobs
uvmgr ap-scheduler list

# Remove a job
uvmgr ap-scheduler remove "backup-job"

# Start the scheduler in the foreground
uvmgr ap-scheduler run
```

### 4.3. Cache Management (`uvmgr cache`)

Manage the `uv` package cache.

```bash
# Show the location of the uv cache directory
uvmgr cache dir

# Prune (clean) the cache to remove unused packages
uvmgr cache prune
```