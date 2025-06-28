# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and other AI agents when working with code in this repository.

## Project Overview

uvmgr is a unified Python workflow engine that wraps around `uv` (a fast Python package manager) to streamline the entire Python development lifecycle. It provides a clean CLI interface with a three-layer architecture: Commands → Operations → Runtime.

### System Architecture Insights
- **Unified Workflow Engine**: Integrates package management, testing, building, AI assistance, and observability
- **External System Integration**: Seamlessly connects to uv, PyPI, Git, Docker, OpenTelemetry, and AI services
- **MCP Protocol Support**: Enables AI agents to interact with uvmgr programmatically
- **Comprehensive Telemetry**: Built-in OpenTelemetry instrumentation for all operations
- **Weaver Forge Integration**: Automated code generation and instrumentation capabilities
- **Advanced Search System**: AST-based code search, dependency analysis, and semantic understanding
- **External Project Testing**: Validate uvmgr capabilities on any Python project with OTEL verification

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
# Analyze command layer (20+ CLI commands including search)
# Inspect operations layer (business logic)
# Monitor runtime layer (subprocess execution)
# Review core infrastructure (cache, config, telemetry)
```

## Advanced Search Capabilities

uvmgr provides sophisticated search functionality that goes beyond simple text matching:

### Code Search with AST Parsing
```bash
# Find function definitions with complexity analysis
uvmgr search code "async def.*upload" --type function --complexity-min 3

# Search for classes with inheritance patterns
uvmgr search code "class.*Model" --include-docs --show-context 5

# Find imports with usage tracking
uvmgr search code "import requests" --type import --show-usage
```

### Dependency Analysis
```bash
# Find vulnerable packages
uvmgr search deps "*" --show-vulnerabilities --format json

# Track package usage across codebase
uvmgr search deps "requests" --show-usage --include-transitive

# Identify unused dependencies
uvmgr search deps "*" --unused-only --format csv
```

### Semantic Search with AI
```bash
# Natural language code discovery
uvmgr search semantic "authentication middleware patterns"

# Find similar code patterns
uvmgr search semantic "error handling best practices" --explain

# Search across documentation
uvmgr search semantic "installation guide" --scope docs
```

### Multi-faceted Search
```bash
# Search everything at once
uvmgr search all "database" --include-logs --format json

# Targeted multi-search
uvmgr search all "security" --no-logs --max-per-type 10
```

## External Project Testing & Verification

uvmgr can test its capabilities on any Python project with comprehensive OTEL verification:

### OTEL Verification Principles
**TRUST ONLY OTEL TRACES - NO HARDCODED VALUES**
- Every claim about uvmgr's capabilities is verified through actual telemetry data
- Performance benchmarks are measured, not assumed
- All lifecycle phases are instrumented and validated

### External Testing Framework
```bash
# Test uvmgr on any project
cd external-project-testing/
bash auto-install-uvmgr.sh /path/to/python/project

# Run comprehensive OTEL verification
python otel-instrumented-runner.py

# Test Substrate template integration
bash test-substrate-integration.sh ./substrate-test

# View real-time verification dashboard
open http://localhost:3000  # Grafana dashboards
```

### Verified Capabilities
- ✅ **Auto-install works on any Python project** (< 120s, config files created)
- ✅ **Substrate template integration** (7-phase workflow validation)
- ✅ **Complete lifecycle coverage** (8 phases with 80%+ success rate)
- ✅ **Performance benchmarks met** (startup < 500ms, operations within SLA)
- ✅ **Full observability** (comprehensive telemetry collection)

## Project Initialization & Templates

### Creating New Projects
```bash
# Basic project
uvmgr new my-project

# Substrate-inspired project with all modern features
uvmgr new substrate my-substrate-project --substrate

# FastAPI project
uvmgr new my-api --template fastapi

# Project with specific features
uvmgr new my-app --github-actions --pre-commit --dev-containers
```

### Substrate Features
When using `--substrate` or `--template substrate`:
- **DevContainers**: Containerized development environment
- **GitHub Actions**: CI/CD pipelines pre-configured
- **Pre-commit Hooks**: Code quality enforcement
- **Conventional Commits**: Standardized commit messages
- **Semantic Versioning**: Automated version management
- **OTEL Integration**: Built-in observability

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

## Best Practices for AI Agents

When working with uvmgr codebase as an AI agent:

### Code Understanding
1. **Use Search First**: Always use `uvmgr search` commands to understand code structure
   ```bash
   # Find relevant code before making changes
   uvmgr search code "function_name" --include-docs
   uvmgr search semantic "feature description"
   ```

2. **Verify Through OTEL**: Don't assume performance or behavior - verify through telemetry
   ```bash
   uvmgr otel validate
   # Check actual execution traces and metrics
   ```

3. **Follow Three-Layer Architecture**: Respect the Commands → Ops → Runtime separation
   - Commands: CLI interface and validation
   - Operations: Pure business logic
   - Runtime: Side effects and I/O

### Agent Workflow Patterns

#### 1. Discovery → Analysis → Implementation → Verification
```bash
# Step 1: Discovery - Find relevant code
uvmgr search semantic "authentication system"
uvmgr search code "class.*Auth" --type class

# Step 2: Analysis - Understand dependencies
uvmgr search deps "auth-library" --show-usage
uvmgr search all "login" --max-per-type 5

# Step 3: Implementation - Make changes with context
# (Make code changes based on discovery)

# Step 4: Verification - Validate through OTEL
uvmgr otel validate
python external-project-testing/otel-instrumented-runner.py
```

#### 2. Multi-Agent Coordination Pattern
```bash
# Agent 1: Code Analysis
uvmgr search code "def.*" --complexity-min 10 --format json > complex_functions.json

# Agent 2: Dependency Analysis  
uvmgr search deps "*" --show-vulnerabilities --format json > vulnerabilities.json

# Agent 3: Performance Analysis
uvmgr otel demo
# Analyze telemetry data for bottlenecks

# Coordinator: Aggregate findings and create action plan
uvmgr ai plan "Refactor complex functions with security vulnerabilities"
```

#### 3. External Project Validation Pattern
```bash
# Never assume uvmgr works - always verify on real projects
cd external-project-testing/

# Test minimal Python project
bash auto-install-uvmgr.sh /tmp/test-project
python otel-claim-verification.py --project /tmp/test-project

# Test complex project (e.g., FastAPI app)
bash test-substrate-integration.sh ./substrate-test --full-validation

# Monitor real-time metrics
open http://localhost:3000  # Grafana dashboards
open http://localhost:16686  # Jaeger traces
```

### Search Strategy Optimization

#### 1. Hierarchical Search Pattern
```bash
# Start broad, then narrow
uvmgr search all "pattern" --max-per-type 5  # Overview
uvmgr search code "pattern" --type function   # Specific type
uvmgr search code "pattern" --complexity-min 5 # Quality filter
```

#### 2. Context-Aware Search
```bash
# Build context before making changes
uvmgr search files "test_*.py" --name "test_auth*"  # Find related tests
uvmgr search code "import.*auth" --type import      # Find usage patterns
uvmgr search logs "auth" --level error --since 24h  # Recent issues
```

#### 3. Semantic Search for Concepts
```bash
# Use natural language for complex patterns
uvmgr search semantic "error handling patterns in async functions"
uvmgr search semantic "database connection pooling best practices"
uvmgr search semantic "secure password storage implementation"
```

### Verification Patterns

#### 1. Pre-Change Verification
```bash
# Before making changes, establish baseline
uvmgr tests run --coverage > baseline_coverage.txt
uvmgr otel validate > baseline_telemetry.json
uvmgr search deps "*" --format json > baseline_deps.json
```

#### 2. Post-Change Verification
```bash
# After changes, compare against baseline
uvmgr tests run --coverage
# Compare coverage percentages

uvmgr otel validate
# Check for performance regressions

uvmgr search deps "*" --unused-only
# Ensure no broken dependencies
```

#### 3. OTEL-Based Failure Detection
```bash
# Monitor for failures in real-time
python external-project-testing/otel-failure-detector.py --threshold 0.95

# Automated incident response
uvmgr otel monitor --alert-on-failure --webhook https://your-webhook.com

# Integrated monitoring with auto-remediation
python external-project-testing/otel-monitor-integration.py --mode monitor
# Dashboard available at http://localhost:8080
```

### OTEL Failure Detection System

uvmgr includes a comprehensive failure detection and incident response system:

#### Automated Detection Patterns
- **High Error Rate**: Monitors error rates against thresholds
- **Performance Degradation**: Detects operations running slower than baseline
- **Dependency Failures**: Tracks external service health
- **Resource Exhaustion**: Identifies memory and connection issues
- **Cascading Failures**: Detects failure spread across components

#### Auto-Remediation Capabilities
```bash
# Automated remediation for common issues:
# - Cache clearing for memory issues
# - Service restarts for persistent errors
# - Connection pool resets
# - Timeout adjustments
# - Performance optimization
```

#### Real-time Monitoring Dashboard
- Web interface at `http://localhost:8080`
- Active incident tracking
- SLA violation monitoring
- Remediation history
- WebSocket updates for real-time data

### Troubleshooting Guide for Agents

#### Common Issues and Solutions

1. **Search Returns No Results**
   ```bash
   # Check if files exist
   uvmgr search files "*" --path /target/path
   
   # Try broader patterns
   uvmgr search code ".*pattern.*" --type all
   
   # Use semantic search
   uvmgr search semantic "describe what you're looking for"
   ```

2. **Performance Degradation**
   ```bash
   # Profile with OTEL
   uvmgr otel demo --profile
   
   # Check cache status
   uvmgr cache size
   
   # Disable parallel processing for debugging
   uvmgr search code "pattern" --no-parallel
   ```

3. **Dependency Conflicts**
   ```bash
   # Full dependency analysis
   uvmgr deps tree
   uvmgr deps check
   
   # Find conflicting versions
   uvmgr search deps "*" --show-versions --format json | jq '.conflicts'
   ```

4. **Test Failures**
   ```bash
   # AI-assisted debugging
   uvmgr ai fix-tests
   
   # Isolated test run
   uvmgr tests run --verbose --no-coverage
   
   # Check test dependencies
   uvmgr search deps "*pytest*" --show-usage
   ```

### Multi-Agent Collaboration

#### Agent Roles and Responsibilities

1. **Discovery Agent**: Uses search commands to map codebase
2. **Analysis Agent**: Evaluates code quality and dependencies
3. **Implementation Agent**: Makes code changes based on analysis
4. **Verification Agent**: Validates changes through OTEL
5. **Coordinator Agent**: Orchestrates workflow and decisions

#### Communication Patterns
```bash
# Agents share context through structured data
uvmgr search all "pattern" --format json > shared_context.json

# Use MCP for inter-agent communication
uvmgr mcp execute tool_name --input shared_context.json

# Coordinate through workflow engine
uvmgr agent coordinate --workflow multi_agent_refactor.bpmn
```

### Development Workflow
1. **Test on External Projects**: Validate changes work outside uvmgr's file tree
   ```bash
   cd external-project-testing/
   python test-lifecycle.py --project minimal
   ```

2. **Use Parallel Search**: Leverage parallel processing for large codebases
   ```bash
   uvmgr search all "pattern" --parallel
   ```

3. **Check Dependencies**: Always verify dependency impacts
   ```bash
   uvmgr search deps "package" --show-usage
   ```

### Performance Validation
1. **Measure, Don't Guess**: Use OTEL metrics for performance claims
2. **Cache Appropriately**: Use search cache for repeated operations
3. **Profile with Telemetry**: Check span durations in Jaeger
4. **Set Performance SLAs**: Define and monitor performance objectives
   ```bash
   # Example: Search should complete within 5 seconds
   uvmgr otel monitor --sla "search_duration < 5s"
   ```

## Error Handling

- Use `typer.Exit(code=1)` for CLI errors
- Provide helpful error messages with `rich.console.Console().print("[red]Error: ...[/red]")`
- Runtime errors should bubble up with clear messages
- Use proper logging with the configured telemetry system
- All errors are traced through OpenTelemetry spans
- Search operations handle malformed files gracefully

## Performance Considerations

### Speed Optimizations
- **uv Integration**: Leverages uv's Rust-based performance for package operations
- **Extensive Caching**: Intelligent caching system (`~/.uvmgr_cache/`) with automatic cleanup
- **Async Architecture**: Preferred async operations for I/O-bound tasks
- **Parallel Execution**: Concurrent command execution where applicable
- **AST Caching**: Parsed Python ASTs cached for repeated searches
- **Search Indexing**: Pre-built indexes for fast file and content discovery

### Search Performance
- **Parallel File Processing**: Multi-threaded search across large codebases
- **Smart Result Limiting**: Stream results to avoid memory overload
- **Incremental Indexing**: Only re-index changed files
- **Memory-Efficient Streaming**: Process large files without full loading
- **Cached Dependency Graphs**: Avoid re-parsing import trees

### OTEL-Verified Benchmarks
All performance claims verified through actual telemetry:
- **Command Startup**: < 500ms (measured via `uvmgr_command_duration_seconds`)
- **Dependency List**: < 2s for typical projects
- **Search Operations**: < 5s for codebases with 10K+ files
- **Test Overhead**: < 50% compared to direct pytest
- **Cache Hit Rate**: > 80% for repeated operations

### Resource Management
- **Memory Efficiency**: Careful subprocess management and resource cleanup
- **Disk Usage**: Automatic cache management and temporary file cleanup
- **Network Optimization**: Efficient package downloads and API calls
- **Search Cache**: LRU eviction for search results

### Monitoring & Profiling
- **Built-in Telemetry**: OpenTelemetry instrumentation for performance monitoring
- **Execution Tracing**: Detailed spans for command execution analysis
- **Metrics Collection**: Performance metrics export to Prometheus
- **Error Tracking**: Comprehensive error handling and reporting
- **Real-time Dashboards**: Grafana dashboards for performance visualization

### Scalability Features
- **Remote Execution**: Distribute heavy operations across multiple systems
- **Agent Coordination**: Scale complex workflows through agent orchestration
- **Containerized Builds**: Isolated build environments for consistent performance
- **Distributed Search**: Shard large search operations across workers

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

## Custom Claude Commands

uvmgr includes custom commands for Claude Code to enhance AI-assisted development workflows. These commands are located in `.claude/commands/` and provide specialized automation:

### Available Commands

#### `/project:analyze-uvmgr [component] [depth=deep]`
Deep analysis of uvmgr components with multi-perspective insights:
- Architecture compliance checking
- Telemetry coverage analysis
- Code quality metrics
- Performance profiling
- Test coverage gaps

#### `/project:test-workflow [component] [coverage-threshold=80]`
Automated test workflow with AI assistance:
- Pre-test dependency validation
- Coverage baseline and gap analysis
- AI-assisted test fixing
- Test generation for coverage improvement
- Performance optimization

#### `/project:search-optimize [query] [scope=all]`
Optimize search across uvmgr's advanced search system:
- Multi-strategy search execution
- AST-based code analysis
- Dependency tracking
- Semantic understanding
- Performance metrics

#### `/project:migrate-project [path] [features=auto]`
Migrate existing projects to uvmgr/Substrate:
- Auto-detect current project structure
- Convert dependency management
- Add Substrate features incrementally
- OTEL integration
- Safety backups and rollback

### Command Development
Custom commands follow the agent-guides pattern:
- Markdown format in `.claude/commands/`
- Multi-phase execution approach
- Integration with uvmgr CLI
- WebSearch capability when needed
- Anti-repetition mechanisms

### Best Practices
1. Use commands for complex multi-step workflows
2. Leverage uvmgr's telemetry for validation
3. Combine multiple commands for comprehensive analysis
4. Export results in appropriate formats (JSON, Markdown)
5. Cache results for repeated operations