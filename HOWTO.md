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
5.  [Observability & Telemetry](#5-observability--telemetry)
    *   [OpenTelemetry Integration](#51-opentelemetry-integration)
    *   [Weaver Semantic Conventions](#52-weaver-semantic-conventions)
6.  [Code Quality](#6-code-quality)
    *   [Linting and Formatting](#61-linting-and-formatting)
    *   [Development Server](#62-development-server)
7.  [AI Integration](#7-ai-integration)
    *   [MCP Server](#71-mcp-server)
8.  [A Note on Deprecated Commands](#8-a-note-on-deprecated-commands)

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
Run business process automation workflows using SpiffWorkflow.

```bash
# Run a BPMN workflow file
uvmgr agent run workflow.bpmn

# Run with custom variables
uvmgr agent run workflow.bpmn --var "input_file=data.csv" --var "output_dir=results"
```

#### Task Scheduling (`ap-scheduler`)
Schedule recurring tasks using APScheduler.

```bash
# Start the scheduler daemon
uvmgr ap-scheduler start

# Add a scheduled task
uvmgr ap-scheduler add "daily_backup" "0 2 * * *" "backup_script.py"

# List scheduled tasks
uvmgr ap-scheduler list

# Remove a scheduled task
uvmgr ap-scheduler remove "daily_backup"
```

### 4.3. Cache Management (`uvmgr cache`)

Manage the `uv` cache to free up disk space or troubleshoot issues.

```bash
# Show cache statistics
uvmgr cache info

# Clear the entire cache
uvmgr cache clear

# Remove specific packages from cache
uvmgr cache remove "requests" "pandas"
```

## 5. Observability & Telemetry

### 5.1. OpenTelemetry Integration (`uvmgr otel`)

`uvmgr` includes comprehensive OpenTelemetry integration for observability, tracing, and metrics collection.

#### Quick Start
```bash
# Start OTEL infrastructure
docker-compose -f docker-compose.otel.yml up -d

# Run commands with automatic telemetry
uvmgr deps add requests
uvmgr tests run

# View traces in Jaeger (http://localhost:16686)
# View metrics in Prometheus (http://localhost:9090)
```

#### Telemetry Coverage Analysis
```bash
# Analyze telemetry coverage across the codebase
uvmgr otel coverage

# Check coverage with custom threshold
uvmgr otel coverage --threshold 90

# Analyze specific layer
uvmgr otel coverage --layer Command

# Show detailed function analysis
uvmgr otel coverage --detailed
```

#### Validation and Testing
```bash
# Run comprehensive OTEL validation
uvmgr otel validate --comprehensive

# Test telemetry functionality
uvmgr otel test --iterations 10

# Export validation results
uvmgr otel validate --export --output validation.json
```

#### Semantic Conventions
```bash
# Validate semantic conventions
uvmgr otel semconv --validate

# Generate code from conventions
uvmgr otel semconv --generate
```

#### Status and Demo
```bash
# Check OTEL status
uvmgr otel status

# Run OTEL demo features
uvmgr otel demo

# Export telemetry data
uvmgr otel export --format json --output telemetry.json
```

### 5.2. Weaver Semantic Conventions (`uvmgr weaver`)

Manage OpenTelemetry semantic conventions using the official Weaver tool.

#### Installation
```bash
# Install Weaver
uvmgr weaver install

# Install specific version
uvmgr weaver install --version v0.1.0

# Force reinstall
uvmgr weaver install --force
```

#### Registry Management
```bash
# Validate semantic convention registry
uvmgr weaver check

# Check with future validation rules
uvmgr weaver check --future

# Apply custom policy
uvmgr weaver check --policy security-policy.rego
```

#### Code Generation
```bash
# Generate Python constants
uvmgr weaver generate python --output src/telemetry/

# Generate documentation
uvmgr weaver generate markdown --output docs/semconv/

# Generate with custom config
uvmgr weaver generate python --config weaver.yaml
```

#### Registry Operations
```bash
# Resolve references and inheritance
uvmgr weaver resolve --format json --output resolved.json

# Search for attributes or metrics
uvmgr weaver search "package" --type attribute

# Show registry statistics
uvmgr weaver stats

# Compare registries
uvmgr weaver diff old-registry/ new-registry/ --output changes.json
```

#### Documentation
```bash
# Generate comprehensive documentation
uvmgr weaver docs --output ./docs/telemetry/ --format markdown

# Check Weaver version
uvmgr weaver version
```

## 6. Code Quality

### 6.1. Linting and Formatting (`uvmgr lint`)

Run code quality checks and formatting using Ruff.

#### Linting
```bash
# Check code for violations
uvmgr lint check

# Check specific path
uvmgr lint check src/

# Auto-fix violations
uvmgr lint check --fix

# Show what would be fixed
uvmgr lint check --show-fixes
```

#### Formatting
```bash
# Format code
uvmgr lint format

# Format specific path
uvmgr lint format src/

# Check formatting without changes
uvmgr lint format --check
```

#### Auto-fix All Issues
```bash
# Fix all auto-fixable issues (linting + formatting)
uvmgr lint fix

# Fix specific path
uvmgr lint fix src/
```

### 6.2. Development Server (`uvmgr serve`)

Start a development server for your application.

```bash
# Start development server
uvmgr serve

# Start with custom host and port
uvmgr serve --host 0.0.0.0 --port 8080

# Start with reload enabled
uvmgr serve --reload
```

## 7. AI Integration

### 7.1. MCP Server (`uvmgr mcp`)

Start a Model Context Protocol (MCP) server for AI assistant integration.

#### Quick Start
```bash
# Start MCP server with stdio transport (for Claude Desktop)
uvmgr mcp serve

# Start SSE server for web clients
uvmgr mcp serve --transport sse --port 3000

# Start HTTP server with authentication
uvmgr mcp serve --transport http --auth-token mytoken
```

#### Transport Options
- **stdio**: Direct communication through standard I/O (best for Claude Desktop)
- **sse**: Server-Sent Events for real-time streaming (good for web clients)
- **http**: RESTful HTTP endpoints for traditional API access

#### Claude Desktop Integration
1. Open Claude Desktop settings
2. Go to 'Developer' > 'Edit Config'
3. Add to the 'mcpServers' section:
   ```json
   "uvmgr": {
     "command": "python3.12",
     "args": ["-m", "uvmgr", "mcp", "serve"]
   }
   ```

#### Web Interface Integration
For Claude.ai web interface:
1. Click 'Add integration' in settings
2. Integration name: uvmgr
3. Integration URL: `http://localhost:8000/sse` (for SSE) or `http://localhost:8000/mcp` (for HTTP)

## 8. A Note on Deprecated Commands

Some commands have been deprecated in favor of more specific alternatives:

- `uvmgr run` → Use `uvmgr exec` for script execution
- `uvmgr install` → Use `uvmgr deps add` for dependency management
- `uvmgr uninstall` → Use `uvmgr deps remove` for dependency removal

These changes provide better organization and more intuitive command names.

---

For more detailed information about specific features, see the documentation in the `docs/` directory:

- [Weaver Command Suite](docs/weaver-command-suite.md) - Complete Weaver documentation
- [OpenTelemetry Integration](docs/otel-integration.md) - OTEL setup and usage guide
- [MCP Documentation](docs/mcp/) - Model Context Protocol guides