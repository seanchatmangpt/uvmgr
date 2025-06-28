# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

uvmgr is a unified Python workflow engine that wraps around `uv` (a fast Python package manager) to streamline the entire Python development lifecycle. It provides a clean CLI interface with a three-layer architecture: Commands → Operations → Runtime.

### System Architecture Insights
- **Unified Workflow Engine**: Integrates package management, testing, building, AI assistance, and observability
- **External System Integration**: Seamlessly connects to uv, PyPI, Git, Docker, OpenTelemetry, and AI services
- **MCP Protocol Support**: Enables AI agents to interact with uvmgr programmatically
- **Comprehensive Telemetry**: Built-in OpenTelemetry instrumentation for all operations
- **Weaver Forge Integration**: Automated code generation and instrumentation capabilities

## Project Introspection & Visualization

uvmgr provides comprehensive project introspection capabilities through architectural diagrams and telemetry:

### Architectural Visualization
```bash
# Generate system architecture diagrams (C4 Context/Container)
# View three-layer architecture flow: Commands → Ops → Runtime
# Understand component relationships and external integrations
# Analyze AI/MCP integration patterns
```

### System Observability
```bash
# OpenTelemetry instrumentation and tracing
uvmgr otel validate
uvmgr otel demo

# Real-time metrics and performance monitoring
# Comprehensive telemetry for all command executions
# Integration with Prometheus and OTEL Collector
```

### Component Analysis
```bash
# Analyze command layer (17+ CLI commands)
# Inspect operations layer (business logic)
# Monitor runtime layer (subprocess execution)
# Review core infrastructure (cache, config, telemetry)
```

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
5. **Observer Pattern**: Telemetry system instruments all operations
6. **Strategy Pattern**: Multiple execution strategies (local, remote, containerized)
7. **Factory Pattern**: Dynamic command loading and registration
8. **Decorator Pattern**: Weaver Forge instrumentation and code generation

### Execution Flow Architecture
```
User Input → CLI Parser → Command Router
    ↓
Commands Layer (Validation, Auth, Telemetry Start)
    ↓
Operations Layer (Business Logic, Data Processing)
    ↓
Runtime Layer (Process Execution, File/Network Operations)
    ↓
Core Infrastructure (Cache, Config, Metrics, Paths)
```

### Integration Ecosystem
- **Package Management**: uv, PyPI integration
- **Version Control**: Git operations and workflow automation
- **Containerization**: Docker build and deployment
- **AI Services**: OpenAI, Groq API integration via DSPy
- **Observability**: OpenTelemetry, Prometheus, metrics export
- **Code Generation**: Weaver Forge templating and instrumentation

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

## MCP Server & AI Integration

uvmgr includes a comprehensive Model Context Protocol (MCP) server for AI agent integration:

### MCP Server Features
```bash
# Install MCP dependencies
pip install 'uvmgr[mcp]'

# Start MCP server
uvmgr serve start
uvmgr serve status

# Available MCP tools for AI agents:
# - ai: AI assistance and automation
# - build: PyInstaller and distribution building
# - deps: Package dependency management
# - exec: Command execution and subprocess management
# - files: File system operations
# - project: Project structure and configuration
# - test: Testing and coverage operations
```

### AI Agent Capabilities
- **Programmatic Access**: AI agents can execute all uvmgr commands via MCP
- **Context Awareness**: Agents receive project structure and configuration context
- **Automated Workflows**: Complex multi-step operations through agent coordination
- **Real-time Feedback**: Telemetry and logging integration for agent observability

### Supported AI Frameworks
- **DSPy**: Advanced AI pipeline construction and optimization
- **FastMCP**: High-performance MCP server implementation
- **Ember-AI**: AI workflow automation and orchestration

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

### Agent Coordination & Workflows
```bash
# SpiffWorkflow integration for complex automation
uvmgr agent coordinate
uvmgr agent swarm

# APScheduler for task scheduling
uvmgr ap-scheduler start
uvmgr ap-scheduler status

# Remote execution capabilities
uvmgr remote execute
```

### Observability & Telemetry
```bash
# OpenTelemetry validation and testing
uvmgr otel validate
uvmgr otel demo

# Weaver semantic convention validation
uvmgr weaver validate
uvmgr weaver generate

# Comprehensive system instrumentation
# Automatic span creation for all operations
# Metrics collection and export
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

## Key Dependencies & Technology Stack

### Core Infrastructure
- **CLI Framework**: typer (command structure), rich (enhanced terminal output)
- **Async Runtime**: asyncio, aiofiles (high-performance I/O)
- **Configuration**: TOML-based config management
- **Caching**: Advanced caching system with cleanup automation

### Development & Testing
- **Testing**: pytest, pytest-mock, coverage (comprehensive test suite)
- **Code Quality**: ruff, mypy, black (linting and formatting)
- **Documentation**: pdoc (API documentation generation)

### AI & Automation
- **AI Frameworks**: dspy (AI pipelines), ember-ai (workflow automation)
- **MCP Integration**: fastmcp (Model Context Protocol server)
- **Agent Coordination**: Multi-agent workflow orchestration

### Workflow & Orchestration
- **Process Automation**: spiffworkflow (BPMN workflow engine)
- **Task Scheduling**: apscheduler (cron-like scheduling)
- **Remote Execution**: Distributed command execution

### Observability & Telemetry
- **Instrumentation**: opentelemetry-sdk (comprehensive tracing)
- **Metrics**: Prometheus integration, custom metrics collection
- **Semantic Conventions**: Weaver-based OTEL semantic conventions

### Build & Distribution
- **Packaging**: pyinstaller, pyinstaller-hooks-contrib (executable building)
- **Container**: Docker integration for containerized builds
- **Package Management**: uv (fast Python package manager)

### Web & API
- **Web Framework**: fastapi (for MCP server and web interfaces)
- **HTTP Client**: Advanced HTTP client for external API integration

## Error Handling

- Use `typer.Exit(code=1)` for CLI errors
- Provide helpful error messages with `rich.console.Console().print("[red]Error: ...[/red]")`
- Runtime errors should bubble up with clear messages
- Use proper logging with the configured telemetry system

## Performance Considerations

### Speed Optimizations
- **uv Integration**: Leverages uv's Rust-based performance for package operations
- **Extensive Caching**: Intelligent caching system (`~/.uvmgr_cache/`) with automatic cleanup
- **Async Architecture**: Preferred async operations for I/O-bound tasks
- **Parallel Execution**: Concurrent command execution where applicable

### Resource Management
- **Memory Efficiency**: Careful subprocess management and resource cleanup
- **Disk Usage**: Automatic cache management and temporary file cleanup
- **Network Optimization**: Efficient package downloads and API calls

### Monitoring & Profiling
- **Built-in Telemetry**: OpenTelemetry instrumentation for performance monitoring
- **Execution Tracing**: Detailed spans for command execution analysis
- **Metrics Collection**: Performance metrics export to Prometheus
- **Error Tracking**: Comprehensive error handling and reporting

### Scalability Features
- **Remote Execution**: Distribute heavy operations across multiple systems
- **Agent Coordination**: Scale complex workflows through agent orchestration
- **Containerized Builds**: Isolated build environments for consistent performance

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